from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ExtractRequest(BaseModel):
    document_id: int


class ExtractResponse(BaseModel):
    document_id: int
    extraction_id: int
    status: str
    extracted_data: dict[str, Any]
    metadata_id: int | None = None


class ReviewUpdate(BaseModel):
    status: Literal["approved", "rejected", "needs_changes"]
    reviewer_notes: str | None = None
    reviewed_data: dict[str, Any] | None = None
    reviewer_id: int | None = None


class ReviewResponse(BaseModel):
    id: int
    document_id: int
    status: str
    reviewer_notes: str | None = None
    reviewed_data: dict[str, Any] | None = None
    reviewer_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, dt: datetime | None) -> str | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    model_config = ConfigDict(from_attributes=True)


class MetadataResponse(BaseModel):
    id: int
    document_id: int
    model_name: str | None = None
    model_version: str | None = None
    runtime: str | None = None
    prompt_version: str | None = None
    latency: float | None = None
    processing_time: float | None = None
    document_category: str | None = None
    file_type: str | None = None
    errors: str | None = None
    created_at: datetime | None = None

    @field_serializer("created_at")
    def serialize_datetime(self, dt: datetime | None) -> str | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------
# Prescription Extraction
# --------------------------------------------------

class MedicationItem(BaseModel):
    medication_name: str | None = None
    dosage: str | None = None
    unit: str | None = None
    frequency: str | None = None
    route: str | None = None
    duration: str | None = None
    instructions: str | None = None
    uncertainty_notes: str | None = None


class PrescriptionExtraction(BaseModel):
    patient_name: str | None = None
    doctor_name: str | None = None
    gender: str | None = None
    age: str | None = None
    date: str | None = None
    medications: list[MedicationItem] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)


class PrescriptionListExtraction(BaseModel):
    prescriptions: list[PrescriptionExtraction] = Field(default_factory=list)


# --------------------------------------------------
# X-Ray Image Extraction
# --------------------------------------------------

class XrayImageExtraction(BaseModel):
    body_part: str | None = None
    findings: list[str] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)
    possible_abnormalities: list[str] = Field(default_factory=list)

    # Accept numeric confidence (0.0 - 1.0)
    confidence: float | int | None = None

    uncertainty_notes: list[str] = Field(default_factory=list)


# --------------------------------------------------
# X-Ray Report Extraction
# --------------------------------------------------

class XrayReportExtraction(BaseModel):
    study_type: str | None = None
    findings: str | list[str] | None = None
    impression: str | list[str] | None = None
    recommendation: str | list[str] | None = None
    summary: str | None = None


# --------------------------------------------------
# Laboratory Report Extraction
# --------------------------------------------------

class LabTestItem(BaseModel):
    test_name: str | None = None
    result: str | None = None
    unit: str | None = None
    reference_range: str | None = None
    flag: str | None = None


class LabPanel(BaseModel):
    panel_name: str | None = None
    tests: list[LabTestItem] = Field(default_factory=list)


class LabReportExtraction(BaseModel):
    schema_version: Literal["lab_v1.0"] = "lab_v1.0"
    laboratory: dict[str, Any] = Field(default_factory=dict)
    patient: dict[str, Any] = Field(default_factory=dict)
    report_date: str | None = None
    panels: list[LabPanel] = Field(default_factory=list)


class FlexibleExtraction(BaseModel):
    model_config = ConfigDict(extra="allow")
