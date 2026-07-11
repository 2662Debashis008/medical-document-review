from config.storage import *

folders = [

    PROCESSED_PRESCRIPTION_IMAGE_DIR,
    PROCESSED_PRESCRIPTION_PDF_DIR,
    PROCESSED_XRAY_IMAGE_DIR,
    PROCESSED_XRAY_REPORT_PDF_DIR,
]

print("\nProcessed Storage\n")

for folder in folders:

    print(folder)
    print("Exists :", folder.exists())
    print("-" * 50)