import csv
import io
import json
from typing import Any

from sqlalchemy.orm import Session

from models.export_history import ExportHistory
from models.medical_document import MedicalDocument


class ExportService:
    @staticmethod
    def reviewed_records(db: Session) -> list[dict[str, Any]]:
        documents = (
            db.query(MedicalDocument)
            .join(MedicalDocument.review)
            .filter(MedicalDocument.review.has())
            .order_by(MedicalDocument.created_at.desc())
            .all()
        )
        return [ExportService._serialize_document(document) for document in documents]

    @staticmethod
    def document_record(db: Session, document_id: int) -> dict[str, Any] | None:
        document = (
            db.query(MedicalDocument)
            .filter(MedicalDocument.id == document_id)
            .first()
        )
        if not document:
            return None
        return ExportService._serialize_document(document)

    @staticmethod
    def json_export(db: Session, document_id: int | None = None):
        if document_id is not None:
            record = ExportService.document_record(db, document_id)
            if record is None:
                return None
            ExportService._record_export(db, "json", 1)
            return record

        records = ExportService.reviewed_records(db)
        ExportService._record_export(db, "json", len(records))
        return records

    @staticmethod
    def csv_export(db: Session, document_id: int | None = None) -> str | None:
        if document_id is not None:
            record = ExportService.document_record(db, document_id)
            if record is None:
                return None
            records = [record]
        else:
            records = ExportService.reviewed_records(db)

        ExportService._record_export(db, "csv", len(records))

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "document_id",
                "document_category",
                "file_type",
                "original_filename",
                "review_status",
                "reviewer_notes",
                "extracted_data",
                "metadata",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow({
                "document_id": record["document_id"],
                "document_category": record["document_category"],
                "file_type": record["file_type"],
                "original_filename": record["original_filename"],
                "review_status": record["review"]["status"] if record["review"] else None,
                "reviewer_notes": record["review"]["reviewer_notes"] if record["review"] else None,
                "extracted_data": json.dumps(record["review"]["reviewed_data"] if record["review"] else record["extracted_data"]),
                "metadata": json.dumps(record["metadata"]),
            })
        return output.getvalue()

    @staticmethod
    def _serialize_document(document: MedicalDocument) -> dict[str, Any]:
        return {
            "document_id": document.id,
            "document_category": document.document_category,
            "file_type": document.file_type,
            "original_filename": document.original_filename,
            "stored_filename": document.stored_filename,
            "storage_path": document.storage_path,
            "status": document.status,
            "extracted_data": document.extraction.extracted_json if document.extraction else None,
            "review": {
                "status": document.review.status,
                "reviewer_notes": document.review.reviewer_notes,
                "reviewed_data": document.review.reviewed_data,
            } if document.review else None,
            "metadata": {
                "model_name": document.metadata_run.model_name,
                "model_version": document.metadata_run.model_version,
                "runtime": document.metadata_run.runtime,
                "prompt_version": document.metadata_run.prompt_version,
                "latency": document.metadata_run.latency,
                "processing_time": document.metadata_run.processing_time,
                "errors": document.metadata_run.errors,
            } if document.metadata_run else None,
        }

    @staticmethod
    def _record_export(db: Session, export_type: str, document_count: int):
        db.add(ExportHistory(
            export_type=export_type,
            exported_by="system",
            document_count=document_count,
        ))
        db.commit()
