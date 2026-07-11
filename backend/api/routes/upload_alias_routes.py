from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from database.dependencies import get_db
from schemas.document import UploadResponse
from schemas.enums import DocumentCategory
from services.upload_service import UploadService


router = APIRouter(tags=["Medical Documents"])


@router.post("/upload", response_model=UploadResponse, status_code=200)
async def upload_document_alias(
    file: UploadFile = File(...),
    document_category: DocumentCategory = Form(...),
    db: Session = Depends(get_db),
):
    document, processed_files = await UploadService.upload_document(
        db=db,
        upload_file=file,
        document_category=document_category,
    )
    return {
        "message": "Upload Successful",
        "document_id": document.id,
        "filename": document.original_filename,
        "status": document.status,
        "processed_files": processed_files,
    }
