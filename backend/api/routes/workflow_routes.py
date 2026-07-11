import json

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from database.dependencies import get_db
from schemas.workflow import (
    ExtractRequest,
    ExtractResponse,
    MetadataResponse,
    ReviewResponse,
    ReviewUpdate,
)
from services.export_service import ExportService
from services.extraction_service import ExtractionService
from services.metadata_service import MetadataService
from services.review_service import ReviewService


router = APIRouter(tags=["Workflow"])


@router.post("/extract", response_model=ExtractResponse)
def extract_document(payload: ExtractRequest, db: Session = Depends(get_db)):
    try:
        extraction, metadata = ExtractionService.extract(db, payload.document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return {
        "document_id": payload.document_id,
        "extraction_id": extraction.id,
        "status": "processed",
        "extracted_data": extraction.extracted_json,
        "metadata_id": metadata.id if metadata else None,
    }


@router.put("/review/{document_id}", response_model=ReviewResponse)
def update_review(
    document_id: int,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
):
    try:
        return ReviewService.upsert_review(db, document_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/review/{document_id}", response_model=ReviewResponse)
def get_review(document_id: int, db: Session = Depends(get_db)):
    review = ReviewService.get_review(db, document_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@router.get("/metadata/{document_id}", response_model=MetadataResponse)
def get_metadata(document_id: int, db: Session = Depends(get_db)):
    metadata = MetadataService.get_by_document_id(db, document_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")
    return metadata


@router.get("/export/json")
def export_json(document_id: int | None = None, db: Session = Depends(get_db)):
    records = ExportService.json_export(db, document_id)
    if records is None:
        raise HTTPException(status_code=404, detail="Document not found")

    content = {
        "format": "json",
        "document_id": document_id,
        "records": records,
    }
    filename = (
        f"medical_document_{document_id}.json"
        if document_id is not None
        else "medical_documents.json"
    )
    return Response(
        content=json.dumps(content, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/csv")
def export_csv(document_id: int | None = None, db: Session = Depends(get_db)):
    content = ExportService.csv_export(db, document_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Document not found")

    filename = (
        f"medical_document_{document_id}.csv"
        if document_id is not None
        else "medical_documents.csv"
    )
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
