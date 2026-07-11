from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

STORAGE_DIR = BASE_DIR / "storage"

# =====================================================
# Original Uploaded Files
# =====================================================

PRESCRIPTION_IMAGE_DIR = STORAGE_DIR / "prescriptions" / "images"
PRESCRIPTION_PDF_DIR = STORAGE_DIR / "prescriptions" / "pdf"
PRESCRIPTION_TEXT_DIR = STORAGE_DIR / "prescriptions" / "text"

XRAY_IMAGE_DIR = STORAGE_DIR / "xrays" / "images"
XRAY_REPORT_PDF_DIR = STORAGE_DIR / "xrays" / "reports_pdf"
XRAY_REPORT_TEXT_DIR = STORAGE_DIR / "xrays" / "reports_text"

LAB_REPORT_IMAGE_DIR = STORAGE_DIR / "lab_reports" / "images"
LAB_REPORT_PDF_DIR = STORAGE_DIR / "lab_reports" / "pdf"
LAB_REPORT_TEXT_DIR = STORAGE_DIR / "lab_reports" / "text"

# =====================================================
# Processed Files
# =====================================================

PROCESSED_PRESCRIPTION_IMAGE_DIR = (
    STORAGE_DIR / "processed" / "prescriptions" / "images"
)

PROCESSED_PRESCRIPTION_PDF_DIR = (
    STORAGE_DIR / "processed" / "prescriptions" / "pdf"
)

PROCESSED_PRESCRIPTION_TEXT_DIR = (
    STORAGE_DIR / "processed" / "prescriptions" / "text"
)

PROCESSED_XRAY_IMAGE_DIR = (
    STORAGE_DIR / "processed" / "xrays" / "images"
)

PROCESSED_XRAY_REPORT_PDF_DIR = (
    STORAGE_DIR / "processed" / "xrays" / "reports_pdf"
)

PROCESSED_XRAY_REPORT_TEXT_DIR = (
    STORAGE_DIR / "processed" / "xrays" / "reports_text"
)

PROCESSED_LAB_REPORT_IMAGE_DIR = (
    STORAGE_DIR / "processed" / "lab_reports" / "images"
)

PROCESSED_LAB_REPORT_PDF_DIR = (
    STORAGE_DIR / "processed" / "lab_reports" / "pdf"
)

PROCESSED_LAB_REPORT_TEXT_DIR = (
    STORAGE_DIR / "processed" / "lab_reports" / "text"
)

# =====================================================
# All Storage Directories
# =====================================================

ALL_STORAGE_DIRS = [

    PRESCRIPTION_IMAGE_DIR,
    PRESCRIPTION_PDF_DIR,
    PRESCRIPTION_TEXT_DIR,

    XRAY_IMAGE_DIR,
    XRAY_REPORT_PDF_DIR,
    XRAY_REPORT_TEXT_DIR,

    LAB_REPORT_IMAGE_DIR,
    LAB_REPORT_PDF_DIR,
    LAB_REPORT_TEXT_DIR,

    PROCESSED_PRESCRIPTION_IMAGE_DIR,
    PROCESSED_PRESCRIPTION_PDF_DIR,
    PROCESSED_PRESCRIPTION_TEXT_DIR,

    PROCESSED_XRAY_IMAGE_DIR,
    PROCESSED_XRAY_REPORT_PDF_DIR,
    PROCESSED_XRAY_REPORT_TEXT_DIR,

    PROCESSED_LAB_REPORT_IMAGE_DIR,
    PROCESSED_LAB_REPORT_PDF_DIR,
    PROCESSED_LAB_REPORT_TEXT_DIR,
]

# =====================================================
# Storage Mapping
# =====================================================

STORAGE_PATHS = {

    "prescription": {
        "image": PRESCRIPTION_IMAGE_DIR,
        "pdf": PRESCRIPTION_PDF_DIR,
        "text": PRESCRIPTION_TEXT_DIR,
    },

    "xray": {
        "image": XRAY_IMAGE_DIR,
        "pdf": XRAY_REPORT_PDF_DIR,
        "text": XRAY_REPORT_TEXT_DIR,
    },

    "lab_report": {
        "image": LAB_REPORT_IMAGE_DIR,
        "pdf": LAB_REPORT_PDF_DIR,
        "text": LAB_REPORT_TEXT_DIR,
    }

}
