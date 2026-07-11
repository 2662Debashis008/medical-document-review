from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_serializer
from datetime import timezone

# ----------------------------
# Upload Response
# ----------------------------

class UploadResponse(BaseModel):
    message: str
    document_id: int
    filename: str
    status: str
    processed_files: list[str] = []


# ----------------------------
# Document Response
# ----------------------------

class DocumentResponse(BaseModel):
    id: int
    document_category: str
    file_type: str
    original_filename: str
    stored_filename: str
    storage_path: str
    status: str
    review_status: str | None = None
    extraction_error: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    model_config = ConfigDict(
        from_attributes=True
    )


# ----------------------------
# Delete Response
# ----------------------------

class DeleteResponse(BaseModel):
    message: str
