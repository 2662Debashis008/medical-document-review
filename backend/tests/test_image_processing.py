from pathlib import Path

from services.image_processing_service import ImageProcessingService


INPUT_IMAGE = "storage/original/prescriptions/images/sample.jpg"

OUTPUT_IMAGE = (
    "storage/processed/prescriptions/images/sample_processed.jpg"
)


if __name__ == "__main__":

    Path("storage/processed/prescriptions/images").mkdir(
        parents=True,
        exist_ok=True,
    )

    output = ImageProcessingService.process_image(
        INPUT_IMAGE,
        OUTPUT_IMAGE,
    )

    print()

    print("Processed Image")

    print(output)