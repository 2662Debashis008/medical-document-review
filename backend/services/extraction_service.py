import time
import copy
from pathlib import Path
from typing import Any

import fitz
from sqlalchemy.orm import Session

from models.extraction import Extraction
from models.medication import Medication
from models.run_metadata import RunMetadata
from config.settings import settings
from parsers.ai_response_parser import AIResponseParser
from providers.medgemma_provider import MedGemmaProvider
from repositories.document_repository import DocumentRepository
from services.preprocessing_service import PreprocessingService
from services.prompt_service import PromptService


class ExtractionService:
    @staticmethod
    def extract(db: Session, document_id: int) -> tuple[Extraction, RunMetadata]:
        document = DocumentRepository.get_by_id(db, document_id)
        if not document:
            raise ValueError("Document not found")

        started = time.perf_counter()
        metadata = None
        error_message = None
        document.status = "processing"
        db.commit()

        try:
            processed = PreprocessingService.preprocess(
                document.storage_path,
                document.document_category,
                document.file_type,
            )
            text_content = ExtractionService._read_text_content(
                document.storage_path,
                document.file_type,
            )
            prompt_file_type = ExtractionService._prompt_file_type(
                document.document_category,
                document.file_type,
                text_content,
            )
            prompt, prompt_version = PromptService.load_prompt(
                document.document_category,
                prompt_file_type,
            )
            extracted_json, provider_metadata = ExtractionService._extract_with_provider(
                prompt,
                processed["processed_files"],
                text_content,
                document.document_category,
                prompt_file_type,
                document.file_type,
            )
            extraction = ExtractionService._upsert_extraction(
                db,
                document_id,
                extracted_json,
            )
            ExtractionService._replace_medications(
                db,
                extraction,
                ExtractionService._prescription_medications(extracted_json),
            )
            document.status = "processed"
            metadata = ExtractionService._upsert_metadata(
                db,
                document,
                prompt_version,
                provider_metadata,
                time.perf_counter() - started,
                None,
            )
            db.commit()
            db.refresh(extraction)
            db.refresh(metadata)
            return extraction, metadata
        except Exception as exc:
            db.rollback()
            error_message = str(exc)
            document = DocumentRepository.get_by_id(db, document_id)
            if document:
                document.status = "failed"
                metadata = ExtractionService._upsert_metadata(
                    db,
                    document,
                    PromptService.PROMPT_VERSION,
                    {"latency": None, "model": None},
                    time.perf_counter() - started,
                    error_message,
                )
                db.commit()
            raise

    @staticmethod
    def _read_text_content(storage_path: str, file_type: str) -> str | None:
        path = Path(storage_path)
        if file_type == "text":
            return path.read_text(encoding="utf-8", errors="ignore")
        if file_type == "pdf":
            return ExtractionService._extract_pdf_text(path)
        return None

    @staticmethod
    def _extract_pdf_text(path: Path) -> str | None:
        text_parts: list[str] = []
        with fitz.open(path) as document:
            for page_number, page in enumerate(document, start=1):
                page_text = page.get_text("text").strip()
                if page_text:
                    text_parts.append(f"[Page {page_number}]\n{page_text}")
        text = "\n\n".join(text_parts).strip()
        return text or None

    @staticmethod
    def _prompt_file_type(
        document_category: str,
        file_type: str,
        text_content: str | None,
    ) -> str:
        if document_category == "xray" and file_type == "pdf" and not text_content:
            return "image"
        return file_type

    @staticmethod
    def _extract_with_provider(
        prompt: str,
        processed_files: list[str],
        text_content: str | None,
        document_category: str,
        file_type: str,
        source_file_type: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        provider = MedGemmaProvider()

        if document_category == "prescription" and file_type == "pdf":
            return ExtractionService._extract_prescription_pdf_pages(
                provider,
                prompt,
                processed_files,
            )
        if document_category == "lab_report" and file_type == "pdf":
            return ExtractionService._extract_lab_report_pdf_pages(
                provider,
                prompt,
                processed_files,
            )
        if (
            document_category == "xray"
            and source_file_type == "pdf"
            and processed_files
        ):
            return ExtractionService._extract_xray_image_pages(
                provider,
                prompt,
                processed_files,
                ExtractionService._pdf_text_by_page(text_content),
            )
        if document_category == "xray" and file_type == "image" and len(processed_files) > 1:
            return ExtractionService._extract_xray_image_pages(
                provider,
                prompt,
                processed_files,
            )

        try:
            raw_response, provider_metadata = provider.infer(
                prompt=prompt,
                input_paths=processed_files,
                text_content=text_content,
            )
            return (
                AIResponseParser.validate(raw_response, document_category, file_type),
                provider_metadata,
            )
        except Exception:
            if (
                document_category == "xray"
                and file_type == "pdf"
                and len(processed_files) > 1
            ):
                return ExtractionService._extract_xray_image_pages(
                    provider,
                    prompt,
                    processed_files,
                )
            raise

    @staticmethod
    def _extract_xray_image_pages(
        provider: MedGemmaProvider,
        prompt: str,
        processed_files: list[str],
        page_texts: dict[int, str] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        page_results = []
        total_latency = 0.0
        metadata: dict[str, Any] = {}

        for page_number, processed_file in enumerate(processed_files, start=1):
            page_prompt = (
                f"{prompt}\n\nThis is page {page_number} of an X-ray image PDF. "
                "Analyze only the image visible on this page. If this page belongs to the same "
                "patient, doctor/facility, and study as another page, keep those identity fields consistent."
            )
            page_text = (page_texts or {}).get(page_number)
            raw_response, page_metadata = provider.infer(
                prompt=page_prompt,
                input_paths=[processed_file],
                text_content=page_text,
            )
            metadata = page_metadata
            total_latency += page_metadata.get("latency") or 0
            page_results.append(AIResponseParser.validate(raw_response, "xray", "image"))

        metadata["latency"] = total_latency or metadata.get("latency")
        metadata["pages_processed"] = len(processed_files)
        return ExtractionService._merge_xray_image_pages(page_results), metadata

    @staticmethod
    def _merge_xray_image_pages(page_results: list[dict[str, Any]]) -> dict[str, Any]:
        if page_results and page_results[0].get("schema_version") == "xray_v2.0":
            return {
                "xrays": [
                    ExtractionService._merge_xray_v2_pages(group)
                    for group in ExtractionService._group_xray_v2_pages(page_results)
                ]
            }

        merged: dict[str, Any] = {
            "body_part": None,
            "findings": [],
            "observations": [],
            "possible_abnormalities": [],
            "confidence": None,
            "uncertainty_notes": [],
        }
        confidences: list[float] = []

        for page_number, result in enumerate(page_results, start=1):
            if not merged["body_part"] and result.get("body_part"):
                merged["body_part"] = result.get("body_part")
            if result.get("confidence") is not None:
                confidences.append(result["confidence"])
            for field in ("findings", "observations", "possible_abnormalities"):
                ExtractionService._extend_unique(
                    merged[field],
                    result.get(field) or [],
                    page_number,
                )
            ExtractionService._extend_unique(
                merged["uncertainty_notes"],
                result.get("uncertainty_notes") or [],
                page_number,
            )

        if confidences:
            merged["confidence"] = sum(confidences) / len(confidences)
        return {"xrays": [merged]}

    @staticmethod
    def _extend_unique(target: list[str], values: list[str], page_number: int):
        for value in values:
            if not value:
                continue
            text = value.strip()
            if text not in target:
                target.append(text)

    @staticmethod
    def _extract_prescription_pdf_pages(
        provider: MedGemmaProvider,
        prompt: str,
        processed_files: list[str],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        page_prescriptions = []
        total_latency = 0.0
        metadata: dict[str, Any] = {}

        for page_number, processed_file in enumerate(processed_files, start=1):
            page_prompt = (
                f"{prompt}\n\nThis is page {page_number} of a prescription PDF. "
                "Extract only the prescription visible on this page."
            )
            raw_response, page_metadata = provider.infer(
                prompt=page_prompt,
                input_paths=[processed_file],
                text_content=None,
            )
            metadata = page_metadata
            total_latency += page_metadata.get("latency") or 0
            parsed = AIResponseParser.validate(
                raw_response,
                "prescription",
                "image",
            )
            if parsed.get("schema_version") == "v2.0":
                page_prescriptions.append(parsed)
            else:
                prescriptions = parsed.get("prescriptions") or []
                if prescriptions:
                    page_prescriptions.append(prescriptions[0])

        metadata["latency"] = total_latency or metadata.get("latency")
        metadata["pages_processed"] = len(processed_files)
        if page_prescriptions and page_prescriptions[0].get("schema_version") == "v2.0":
            return {
                "prescriptions": [
                    ExtractionService._merge_prescription_v2_pages(group)
                    for group in ExtractionService._group_prescription_v2_pages(page_prescriptions)
                ]
            }, metadata

        return {"prescriptions": ExtractionService._merge_prescriptions(page_prescriptions)}, metadata

    @staticmethod
    def _pdf_text_by_page(text_content: str | None) -> dict[int, str]:
        if not text_content:
            return {}

        page_texts: dict[int, str] = {}
        current_page: int | None = None
        current_lines: list[str] = []

        for line in text_content.splitlines():
            stripped = line.strip()
            if stripped.startswith("[Page ") and stripped.endswith("]"):
                if current_page is not None:
                    page_texts[current_page] = "\n".join(current_lines).strip()
                try:
                    current_page = int(stripped.removeprefix("[Page ").removesuffix("]"))
                except ValueError:
                    current_page = None
                current_lines = []
            else:
                current_lines.append(line)

        if current_page is not None:
            page_texts[current_page] = "\n".join(current_lines).strip()
        return {page: text for page, text in page_texts.items() if text}

    @staticmethod
    def _group_prescription_v2_pages(
        prescriptions: list[dict[str, Any]]
    ) -> list[list[dict[str, Any]]]:
        groups: list[list[dict[str, Any]]] = []
        for prescription in prescriptions:
            target = None
            for group in groups:
                if ExtractionService._same_prescription_v2_identity(group[0], prescription):
                    target = group
                    break
            if target is None:
                target = groups[-1] if groups and ExtractionService._is_prescription_v2_continuation(prescription) else None
            if target is None:
                groups.append([prescription])
            else:
                target.append(prescription)
        return groups

    @staticmethod
    def _same_prescription_v2_identity(first: dict[str, Any], second: dict[str, Any]) -> bool:
        first_patient = as_nested_text(first, "patient", "name")
        second_patient = as_nested_text(second, "patient", "name")
        first_doctor = as_nested_text(first, "document_facility", "consultant", "name")
        second_doctor = as_nested_text(second, "document_facility", "consultant", "name")
        first_date = as_nested_text(first, "document_facility", "datetime_on_doc")
        second_date = as_nested_text(second, "document_facility", "datetime_on_doc")

        if first_patient and second_patient and first_patient != second_patient:
            return False
        if first_doctor and second_doctor and first_doctor != second_doctor:
            return False
        if first_date and second_date and first_date != second_date:
            return False
        return bool(first_patient and second_patient) or bool(first_doctor and second_doctor)

    @staticmethod
    def _is_prescription_v2_continuation(prescription: dict[str, Any]) -> bool:
        return not (
            as_nested_text(prescription, "patient", "name")
            or as_nested_text(prescription, "document_facility", "consultant", "name")
        )

    @staticmethod
    def _merge_prescription_v2_pages(
        prescriptions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        merged = copy.deepcopy(prescriptions[0])
        list_fields = [
            "history_presenting_complaints_facts",
            "investigations_facts",
            "medications_facts",
            "uncertain_or_illegible_segments",
        ]
        for field in list_fields:
            merged[field] = []

        for page_number, prescription in enumerate(prescriptions, start=1):
            ExtractionService._merge_missing_values(merged, prescription)
            for field in list_fields:
                for value in prescription.get(field) or []:
                    item = ExtractionService._with_page_context(value, page_number)
                    if item not in merged[field]:
                        merged[field].append(item)

            for field in ("working_diagnoses", "rationale", "red_flags"):
                target = merged.setdefault("interpretation_inferences", {}).setdefault(field, [])
                for value in (
                    prescription.get("interpretation_inferences", {}).get(field) or []
                ):
                    item = value.strip()
                    if item not in target:
                        target.append(item)

            excerpts = merged.setdefault("provenance", {}).setdefault(
                "key_verbatim_excerpts", []
            )
            for value in prescription.get("provenance", {}).get("key_verbatim_excerpts") or []:
                item = value.strip()
                if item not in excerpts:
                    excerpts.append(item)

        return merged

    @staticmethod
    def _merge_xray_v2_pages(page_results: list[dict[str, Any]]) -> dict[str, Any]:
        merged = copy.deepcopy(page_results[0])
        for field in ("findings_facts", "impression", "uncertain_or_illegible_segments"):
            merged[field] = []
        visual_parts = []

        for page_number, result in enumerate(page_results, start=1):
            ExtractionService._merge_missing_values(merged, result)
            for field in ("findings_facts", "impression", "uncertain_or_illegible_segments"):
                for value in result.get(field) or []:
                    item = ExtractionService._with_page_context(value, page_number)
                    if item not in merged[field]:
                        merged[field].append(item)

            visual = result.get("visual_understanding")
            if visual:
                visual_parts.append(visual.strip())

            recommendations = merged.setdefault("advice_plan_facts", {}).setdefault(
                "recommendations", []
            )
            for value in result.get("advice_plan_facts", {}).get("recommendations") or []:
                item = value.strip()
                if item not in recommendations:
                    recommendations.append(item)

        if visual_parts:
            merged["visual_understanding"] = "\n".join(visual_parts)
        return merged

    @staticmethod
    def _group_xray_v2_pages(page_results: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        groups: list[list[dict[str, Any]]] = []
        for result in page_results:
            target = None
            for group in groups:
                if ExtractionService._same_xray_v2_identity(group[0], result):
                    target = group
                    break
            if target is None:
                target = groups[-1] if groups and ExtractionService._is_xray_v2_continuation(result) else None
            if target is None:
                groups.append([result])
            else:
                target.append(result)
        return groups

    @staticmethod
    def _same_xray_v2_identity(first: dict[str, Any], second: dict[str, Any]) -> bool:
        comparable_paths = [
            ("patient", "name"),
            ("document_facility", "consultant", "name"),
            ("document_facility", "datetime_on_doc"),
            ("xray_study", "exam_date"),
            ("xray_study", "body_part"),
        ]
        shared = 0
        for path in comparable_paths:
            first_value = as_nested_text(first, *path)
            second_value = as_nested_text(second, *path)
            if first_value and second_value:
                if first_value != second_value:
                    return False
                shared += 1
        return shared > 0

    @staticmethod
    def _is_xray_v2_continuation(result: dict[str, Any]) -> bool:
        return not (
            as_nested_text(result, "patient", "name")
            or as_nested_text(result, "document_facility", "consultant", "name")
            or as_nested_text(result, "xray_study", "exam_date")
        )

    @staticmethod
    def _merge_missing_values(target: dict[str, Any], source: dict[str, Any]):
        if target is source:
            return
        for key, value in source.items():
            if isinstance(value, list):
                continue
            if value in (None, "", [], {}):
                continue
            current = target.get(key)
            if isinstance(current, dict) and isinstance(value, dict):
                ExtractionService._merge_missing_values(current, value)
            elif current in (None, "", [], {}):
                target[key] = value

    @staticmethod
    def _with_page_context(value: Any, page_number: int) -> Any:
        if isinstance(value, dict):
            item = dict(value)
            item.setdefault("page", page_number)
            return item
        return value

    @staticmethod
    def _merge_prescriptions(
        prescriptions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []

        for prescription in prescriptions:
            target = ExtractionService._find_matching_prescription(
                merged,
                prescription,
            )
            if target is None:
                merged.append({**prescription, "medications": []})
                target = merged[-1]

            for field in ("patient_name", "doctor_name", "date"):
                if not target.get(field) and prescription.get(field):
                    target[field] = prescription.get(field)
            target["medications"].extend(prescription.get("medications") or [])
            notes = target.setdefault("uncertainty_notes", [])
            for note in prescription.get("uncertainty_notes") or []:
                if note and note not in notes:
                    notes.append(note)

        return merged

    @staticmethod
    def _find_matching_prescription(
        merged: list[dict[str, Any]],
        prescription: dict[str, Any],
    ) -> dict[str, Any] | None:
        for candidate in merged:
            if ExtractionService._same_prescription_identity(candidate, prescription):
                return candidate
        return None

    @staticmethod
    def _same_prescription_identity(
        first: dict[str, Any],
        second: dict[str, Any],
    ) -> bool:
        fields = ("patient_name", "doctor_name", "date")
        shared = set()

        for field in fields:
            first_value = ExtractionService._normalize_key_value(first.get(field))
            second_value = ExtractionService._normalize_key_value(second.get(field))
            if first_value and second_value:
                if first_value != second_value:
                    return False
                shared.add(field)

        return "patient_name" in shared or {"doctor_name", "date"}.issubset(shared)

    @staticmethod
    def _normalize_key_value(value: Any) -> str:
        return " ".join(str(value or "").lower().split())

    @staticmethod
    def _prescription_medications(extracted_json: dict[str, Any]) -> list[dict[str, Any]]:
        if extracted_json.get("schema_version") == "v2.0":
            return extracted_json.get("medications_facts") or []

        medications = []
        for prescription in extracted_json.get("prescriptions", []):
            if prescription.get("schema_version") == "v2.0":
                medications.extend(prescription.get("medications_facts") or [])
            else:
                medications.extend(prescription.get("medications") or [])
        return medications

    @staticmethod
    def _upsert_extraction(
        db: Session,
        document_id: int,
        extracted_json: dict[str, Any],
    ) -> Extraction:
        extraction = (
            db.query(Extraction)
            .filter(Extraction.document_id == document_id)
            .first()
        )
        if extraction:
            extraction.extracted_json = extracted_json
        else:
            extraction = Extraction(
                document_id=document_id,
                extracted_json=extracted_json,
            )
            db.add(extraction)
            db.flush()
        return extraction

    @staticmethod
    def _replace_medications(
        db: Session,
        extraction: Extraction,
        medications: list[dict[str, Any]],
    ):
        db.query(Medication).filter(
            Medication.extraction_id == extraction.id
        ).delete()

        for medication in medications:
            drug = medication.get("drug") if isinstance(medication.get("drug"), dict) else {}
            dose = medication.get("dose") if isinstance(medication.get("dose"), dict) else {}
            
            strength = drug.get("strength")
            amount = medication.get("dosage") or dose.get("amount")
            if strength and amount and str(strength).lower().strip() != str(amount).lower().strip():
                dosage_val = f"{strength} ({amount})"
            else:
                dosage_val = strength or amount

            db.add(Medication(
                extraction_id=extraction.id,
                medication_name=medication.get("medication_name") or drug.get("name"),
                dosage=dosage_val,
                unit=medication.get("unit") or dose.get("unit"),
                frequency=medication.get("frequency"),
                route=medication.get("route"),
                duration=medication.get("duration"),
                instructions=medication.get("instructions") or medication.get("timing"),
                uncertainty_notes=medication.get("uncertainty_notes"),
            ))

    @staticmethod
    def _extract_lab_report_pdf_pages(
        provider: MedGemmaProvider,
        prompt: str,
        processed_files: list[str],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        page_results = []
        total_latency = 0.0
        metadata: dict[str, Any] = {}

        for page_number, processed_file in enumerate(processed_files, start=1):
            page_prompt = (
                f"{prompt}\n\nThis is page {page_number} of a laboratory report PDF. "
                "Extract only the test results visible on this page."
            )
            raw_response, page_metadata = provider.infer(
                prompt=page_prompt,
                input_paths=[processed_file],
                text_content=None,
            )
            metadata = page_metadata
            total_latency += page_metadata.get("latency") or 0.0
            parsed = AIResponseParser.validate(
                raw_response,
                "lab_report",
                "image",
            )
            page_results.append(parsed)

        metadata["latency"] = total_latency or metadata.get("latency")
        metadata["pages_processed"] = len(processed_files)
        return ExtractionService._merge_lab_report_pages(page_results), metadata

    @staticmethod
    def _merge_lab_report_pages(page_results: list[dict[str, Any]]) -> dict[str, Any]:
        if not page_results:
            return {}
        merged = copy.deepcopy(page_results[0])
        merged["panels"] = []

        panel_map: dict[str, dict[str, Any]] = {}

        for page_number, result in enumerate(page_results, start=1):
            ExtractionService._merge_missing_values(merged, result)
            for panel in result.get("panels") or []:
                panel_name = panel.get("panel_name") or "General Pathology"
                panel_name_clean = panel_name.strip()
                
                if panel_name_clean not in panel_map:
                    panel_map[panel_name_clean] = {
                        "panel_name": panel_name,
                        "tests": []
                    }
                
                for test in panel.get("tests") or []:
                    if test not in panel_map[panel_name_clean]["tests"]:
                        panel_map[panel_name_clean]["tests"].append(test)

        merged["panels"] = list(panel_map.values())
        return merged

    @staticmethod
    def _upsert_metadata(
        db: Session,
        document,
        prompt_version: str,
        provider_metadata: dict[str, Any],
        processing_time: float,
        errors: str | None,
    ) -> RunMetadata:
        metadata = (
            db.query(RunMetadata)
            .filter(RunMetadata.document_id == document.id)
            .first()
        )
        if not metadata:
            metadata = RunMetadata(document_id=document.id)
            db.add(metadata)

        metadata.model_name = provider_metadata.get("model") or settings.MODEL_NAME
        metadata.model_version = provider_metadata.get("model_version")
        metadata.runtime = "ollama"
        metadata.prompt_version = prompt_version
        metadata.latency = provider_metadata.get("latency")
        metadata.processing_time = processing_time
        metadata.document_category = document.document_category
        metadata.file_type = document.file_type
        metadata.errors = errors
        return metadata


def as_nested_text(data: dict[str, Any], *path: str) -> str:
    value: Any = data
    for key in path:
        if not isinstance(value, dict):
            return ""
        value = value.get(key)
    return ExtractionService._normalize_key_value(value)
