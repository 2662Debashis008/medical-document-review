import json
import re
from typing import Any

from schemas.workflow import (
    FlexibleExtraction,
    PrescriptionExtraction,
    PrescriptionListExtraction,
    XrayImageExtraction,
    XrayReportExtraction,
    LabReportExtraction,
)


class AIResponseParser:
    @staticmethod
    def parse_json(raw_text: str) -> dict[str, Any]:
        text = raw_text.strip()
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                except json.JSONDecodeError:
                    parsed = AIResponseParser._repair_and_parse_json(text)
            else:
                parsed = AIResponseParser._repair_and_parse_json(text)

        if not isinstance(parsed, dict):
            raise ValueError("AI response JSON must be an object")

        return parsed

    @staticmethod
    def _repair_and_parse_json(text: str) -> dict[str, Any]:
        match = re.search(r"\{.*", text, flags=re.DOTALL)
        if not match:
            raise ValueError("AI response did not contain JSON")
        snippet = match.group(0)

        in_string = False
        escape = False
        stack = []
        fixed_chars = []

        for char in snippet:
            if escape:
                escape = False
                fixed_chars.append(char)
                continue
            if char == "\\":
                escape = True
                fixed_chars.append(char)
                continue
            if char == '"':
                in_string = not in_string
                fixed_chars.append(char)
                continue
            if not in_string:
                if char in "{[":
                    stack.append(char)
                elif char == "}":
                    if stack and stack[-1] == "{":
                        stack.pop()
                elif char == "]":
                    if stack and stack[-1] == "[":
                        stack.pop()
            fixed_chars.append(char)

        if in_string:
            fixed_chars.append('"')

        candidate = "".join(fixed_chars).rstrip()
        candidate = re.sub(r",\s*$", "", candidate)

        while stack:
            top = stack.pop()
            if top == "{":
                candidate += "}"
            elif top == "[":
                candidate += "]"

        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        raise ValueError(f"Could not parse AI JSON response: {text[:150]}")

    @classmethod
    def validate(cls, raw_text: str, document_category: str, file_type: str) -> dict[str, Any]:
        parsed = cls.parse_json(raw_text)

        if document_category == "prescription":
            return cls.validate_prescription(parsed)

        if document_category == "lab_report":
            return cls.validate_lab_report(parsed)

        if cls._looks_like_xray_v2(parsed):
            return cls._normalize_xray_v2(parsed)

        confidence = parsed.get("confidence")

        if isinstance(confidence, str):
            confidence = confidence.lower().strip()

            mapping = {
                "high": 0.95,
                "medium": 0.70,
                "low": 0.40,
            }

            parsed["confidence"] = mapping.get(confidence, 0.50)

        # -----------------------------
        # Normalize uncertainty_notes
        # -----------------------------
        notes = parsed.get("uncertainty_notes")

        if isinstance(notes, str):
            parsed["uncertainty_notes"] = [notes]

        elif notes is None:
            parsed["uncertainty_notes"] = []

        # -----------------------------
        # Validate
        # -----------------------------
        if file_type == "image":
            return XrayImageExtraction.model_validate(parsed).model_dump()

        return XrayReportExtraction.model_validate(parsed).model_dump()

    @classmethod
    def validate_prescription(cls, parsed: dict[str, Any]) -> dict[str, Any]:
        if cls._looks_like_prescription_v2(parsed):
            return cls._normalize_prescription_v2(parsed)

        if "prescriptions" not in parsed:
            parsed = {"prescriptions": [parsed]}

        prescriptions = parsed.get("prescriptions")
        if not isinstance(prescriptions, list):
            raise ValueError("Prescription response must contain a prescriptions list")

        normalized = []
        for prescription in prescriptions:
            if not isinstance(prescription, dict):
                continue
            normalized.append(cls._normalize_prescription(prescription))

        return PrescriptionListExtraction.model_validate(
            {"prescriptions": normalized}
        ).model_dump()

    @staticmethod
    def _normalize_prescription(prescription: dict[str, Any]) -> dict[str, Any]:
        prescription = dict(prescription)
        if prescription.get("uncertainty_notes") is None:
            prescription["uncertainty_notes"] = []

        medications = prescription.get("medications") or []
        if not isinstance(medications, list):
            medications = []

        normalized_medications = []
        for medication in medications:
            if not isinstance(medication, dict):
                continue
            medication = dict(medication)
            if "drug" in medication and not medication.get("medication_name"):
                medication["medication_name"] = medication.pop("drug")
            normalized_medications.append(medication)

        prescription["medications"] = normalized_medications
        return PrescriptionExtraction.model_validate(prescription).model_dump()

    @staticmethod
    def _looks_like_prescription_v2(parsed: dict[str, Any]) -> bool:
        return (
            parsed.get("schema_version") == "v2.0"
            or "document_facility" in parsed
            or "medications_facts" in parsed
        )

    @staticmethod
    def _normalize_prescription_v2(parsed: dict[str, Any]) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "schema_version": "v2.0",
            "document_facility": {
                "facility": "",
                "department": "",
                "consultant": {"name": "", "degrees": "", "reg_no": ""},
                "location": "",
                "datetime_on_doc": "",
                "source_type": "",
                "file_name": "",
            },
            "patient": {
                "name": "",
                "age": "",
                "sex": "",
                "dob": "",
                "address": "",
                "mobile": "",
                "id_or_uhid": "",
            },
            "vitals_anthropometry": {
                "height": "",
                "weight": "",
                "bp": "",
                "pulse": "",
                "spo2": "",
                "temperature": "",
                "notes": "",
            },
            "history_presenting_complaints_facts": [],
            "examination_facts": {
                "general": "",
                "systemic": "",
                "abdomen_rs_cvs_cns": "",
                "scores_scales": "",
            },
            "investigations_facts": [],
            "medications_facts": [],
            "advice_plan_facts": {
                "diet_lifestyle": "",
                "follow_up": "",
                "referrals_or_admission": "",
                "special_instructions": "",
            },
            "interpretation_inferences": {
                "working_diagnoses": [],
                "rationale": [],
                "red_flags": [],
            },
            "uncertain_or_illegible_segments": [],
            "provenance": {"key_verbatim_excerpts": []},
            "admin": {"warnings": [], "extractor": "azure-openai"},
        }
        normalized = AIResponseParser._deep_merge(defaults, parsed)
        normalized["history_presenting_complaints_facts"] = AIResponseParser._list_or_empty(
            normalized.get("history_presenting_complaints_facts")
        )
        normalized["investigations_facts"] = AIResponseParser._list_or_empty(
            normalized.get("investigations_facts")
        )
        normalized["medications_facts"] = AIResponseParser._list_or_empty(
            normalized.get("medications_facts")
        )
        normalized["uncertain_or_illegible_segments"] = AIResponseParser._list_or_empty(
            normalized.get("uncertain_or_illegible_segments")
        )
        return FlexibleExtraction.model_validate(normalized).model_dump()

    @staticmethod
    def _looks_like_xray_v2(parsed: dict[str, Any]) -> bool:
        return (
            parsed.get("schema_version") == "xray_v2.0"
            or "xray_study" in parsed
            or "visual_understanding" in parsed
            or "findings_facts" in parsed
        )

    @staticmethod
    def _normalize_xray_v2(parsed: dict[str, Any]) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "schema_version": "xray_v2.0",
            "document_facility": {
                "facility": "",
                "department": "",
                "consultant": {"name": "", "degrees": "", "reg_no": ""},
                "location": "",
                "datetime_on_doc": "",
                "source_type": "",
                "file_name": "",
            },
            "patient": {
                "name": "",
                "age": "",
                "sex": "",
                "dob": "",
                "id_or_uhid": "",
            },
            "xray_study": {
                "study_type": "",
                "body_part": "",
                "view": "",
                "laterality": "",
                "exam_date": "",
            },
            "clinical_context": {"history": "", "indication": ""},
            "image_quality": {
                "positioning": "",
                "exposure": "",
                "artifacts": "",
                "limitations": "",
            },
            "findings_facts": [],
            "impression": [],
            "advice_plan_facts": {
                "recommendations": [],
                "follow_up": "",
                "special_instructions": "",
            },
            "visual_understanding": "",
            "interpretation_inferences": {"possible_abnormalities": [], "rationale": []},
            "uncertain_or_illegible_segments": [],
            "provenance": {"key_verbatim_excerpts": []},
            "admin": {"warnings": [], "extractor": "azure-openai"},
        }
        normalized = AIResponseParser._deep_merge(defaults, parsed)
        for key in ("findings_facts", "impression", "uncertain_or_illegible_segments"):
            normalized[key] = AIResponseParser._list_or_empty(normalized.get(key))
        normalized["advice_plan_facts"]["recommendations"] = AIResponseParser._list_or_empty(
            normalized.get("advice_plan_facts", {}).get("recommendations")
        )
        return FlexibleExtraction.model_validate(normalized).model_dump()

    @classmethod
    def validate_lab_report(cls, parsed: dict[str, Any]) -> dict[str, Any]:
        defaults: dict[str, Any] = {
            "schema_version": "lab_v1.0",
            "laboratory": {
                "name": "",
                "referred_by": "",
                "datetime_on_doc": "",
            },
            "patient": {
                "name": "",
                "age": "",
                "sex": "",
            },
            "report_date": "",
            "panels": [],
        }

        # Pre-process raw string structures to avoid validation crashes
        if "laboratory" in parsed and isinstance(parsed["laboratory"], str):
            parsed["laboratory"] = {"name": parsed["laboratory"]}
        if "patient" in parsed and isinstance(parsed["patient"], str):
            parsed["patient"] = {"name": parsed["patient"]}

        normalized = cls._deep_merge(defaults, parsed)
        raw_panels = cls._list_or_empty(normalized.get("panels"))
        cleaned_panels = []
        for panel in raw_panels:
            if isinstance(panel, str):
                cleaned_panels.append({
                    "panel_name": panel,
                    "tests": []
                })
            elif isinstance(panel, dict):
                raw_tests = cls._list_or_empty(panel.get("tests"))
                cleaned_tests = []
                for test in raw_tests:
                    if isinstance(test, str):
                        cleaned_tests.append({
                            "test_name": test,
                            "result": "",
                            "unit": "",
                            "reference_range": "",
                            "flag": ""
                        })
                    elif isinstance(test, dict):
                        cleaned_tests.append(test)
                panel["tests"] = cleaned_tests
                cleaned_panels.append(panel)
        normalized["panels"] = cleaned_panels

        return LabReportExtraction.model_validate(normalized).model_dump()

    @staticmethod
    def _deep_merge(defaults: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
        merged = dict(defaults)
        for key, value in values.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = AIResponseParser._deep_merge(merged[key], value)
            elif value is not None:
                merged[key] = value
        return merged

    @staticmethod
    def _list_or_empty(value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]
