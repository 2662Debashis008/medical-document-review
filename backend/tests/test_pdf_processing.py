from services.pdf_processing_service import PDFProcessingService


INPUT_PDF = (
    "storage/original/prescriptions/pdf/sample.pdf"
)

OUTPUT_FOLDER = (
    "storage/processed/prescriptions/pdf"
)


if __name__ == "__main__":

    images = PDFProcessingService.convert_pdf_to_images(
        INPUT_PDF,
        OUTPUT_FOLDER,
    )

    print()

    print("Generated Images")

    for image in images:
        print(image)