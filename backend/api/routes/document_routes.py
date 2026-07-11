from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
import mimetypes
from urllib.parse import quote
from fastapi.responses import FileResponse
from schemas.document import (
    UploadResponse,
    DocumentResponse,
    DeleteResponse,
)

from sqlalchemy.orm import Session

from database.dependencies import get_db

from repositories.document_repository import DocumentRepository
from models.extraction import Extraction
from services.upload_service import UploadService
from schemas.enums import DocumentCategory
router = APIRouter(
    prefix="/documents",
    tags=["Medical Documents"],
)


# -----------------------
# Upload Document
# -----------------------

@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=200,
)
async def upload_document(
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
    "processed_files": processed_files
}


# -----------------------
# Get All Documents
# -----------------------

from typing import List

@router.get(
    "",
    response_model=List[DocumentResponse],
)
def get_documents(
    db: Session = Depends(get_db),
):

    return DocumentRepository.get_all(db)


# -----------------------
# Get Single Document
# -----------------------

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
):

    document = DocumentRepository.get_by_id(
        db,
        document_id,
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document


@router.get(
    "/{document_id}/file",
)
def get_document_file(
    document_id: int,
    db: Session = Depends(get_db),
):

    document = DocumentRepository.get_by_id(
        db,
        document_id,
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    media_type = mimetypes.guess_type(document.original_filename)[0] or "application/octet-stream"
    safe_filename = quote(document.original_filename)

    return FileResponse(
        document.storage_path,
        media_type=media_type,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{safe_filename}",
        },
    )


@router.get(
    "/{document_id}/extraction",
)
def get_document_extraction(
    document_id: int,
    db: Session = Depends(get_db),
):

    extraction = (
        db.query(Extraction)
        .filter(Extraction.document_id == document_id)
        .first()
    )

    if not extraction:

        raise HTTPException(
            status_code=404,
            detail="Extraction not found",
        )

    return {
        "document_id": document_id,
        "extraction_id": extraction.id,
        "extracted_data": extraction.extracted_json,
    }


# -----------------------
# Delete Document
# -----------------------

@router.delete(
    "/{document_id}",
    response_model=DeleteResponse,
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):

    document = DocumentRepository.delete(
        db,
        document_id,
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return {
        "message": "Document Deleted"
    }
