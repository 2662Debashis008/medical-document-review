from pathlib import Path

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

DOCUMENT_CATEGORIES = {
    "prescription",
    "xray",
    "lab_report",
}

FILE_TYPES = {
    "image",
    "pdf",
    "text",
}

EXTENSION_TO_FILE_TYPE = {
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".pdf": "pdf",
    ".txt": "text",
}

ALLOWED_EXTENSIONS = set(EXTENSION_TO_FILE_TYPE.keys())

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf",
    "text/plain",
}