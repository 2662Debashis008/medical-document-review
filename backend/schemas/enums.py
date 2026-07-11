from enum import Enum


class DocumentCategory(str, Enum):
    PRESCRIPTION = "prescription"
    XRAY = "xray"
    LAB_REPORT = "lab_report"


class FileType(str, Enum):
    IMAGE = "image"
    PDF = "pdf"
    TEXT = "text"


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    REVIEWED = "reviewed"
    FAILED = "failed"