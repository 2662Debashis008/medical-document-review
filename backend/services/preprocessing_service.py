from pathlib import Path
import shutil

from config.storage import (
    PROCESSED_PRESCRIPTION_IMAGE_DIR,
    PROCESSED_PRESCRIPTION_PDF_DIR,
    PROCESSED_PRESCRIPTION_TEXT_DIR,
    PROCESSED_XRAY_IMAGE_DIR,
    PROCESSED_XRAY_REPORT_PDF_DIR,
    PROCESSED_XRAY_REPORT_TEXT_DIR,
    PROCESSED_LAB_REPORT_IMAGE_DIR,
    PROCESSED_LAB_REPORT_PDF_DIR,
    PROCESSED_LAB_REPORT_TEXT_DIR,
)

from services.image_processing_service import ImageProcessingService
from services.pdf_processing_service import PDFProcessingService


class PreprocessingService:

    @staticmethod
    def preprocess(
        input_path: str,
        document_category: str = "prescription",
        file_type: str | None = None,
    ):

        input_path = Path(input_path)
        if file_type is None:
            if input_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                file_type = "image"
            elif input_path.suffix.lower() == ".pdf":
                file_type = "pdf"
            elif input_path.suffix.lower() == ".txt":
                file_type = "text"
            else:
                raise ValueError(f"Unsupported file type: {input_path.suffix.lower()}")

        # ---------------------------------
        # Decide processed output folder
        # ---------------------------------

        if document_category == "prescription":

            if file_type == "image":

                output_folder = PROCESSED_PRESCRIPTION_IMAGE_DIR
            elif file_type == "text":
                output_folder = PROCESSED_PRESCRIPTION_TEXT_DIR

            else:

                output_folder = PROCESSED_PRESCRIPTION_PDF_DIR

        elif document_category == "lab_report":

            if file_type == "image":

                output_folder = PROCESSED_LAB_REPORT_IMAGE_DIR
            elif file_type == "text":
                output_folder = PROCESSED_LAB_REPORT_TEXT_DIR

            else:

                output_folder = PROCESSED_LAB_REPORT_PDF_DIR

        else:

            if file_type == "image":

                output_folder = PROCESSED_XRAY_IMAGE_DIR
            elif file_type == "text":
                output_folder = PROCESSED_XRAY_REPORT_TEXT_DIR

            else:

                output_folder = PROCESSED_XRAY_REPORT_PDF_DIR

        output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        extension = input_path.suffix.lower()

        # =====================================================
        # IMAGE
        # =====================================================

        if extension in [".jpg", ".jpeg", ".png"]:

            output_path = output_folder / input_path.name

            if document_category == "xray":
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(input_path, output_path)
            else:
                ImageProcessingService.process_image(
                    str(input_path),
                    str(output_path),
                )

            return {

                "type": "image",

                "processed_files": [
                    str(output_path)
                ]

            }

        # =====================================================
        # PDF
        # =====================================================

        elif extension == ".pdf":
            pdf_output_folder = output_folder / input_path.stem
            raw_output_folder = pdf_output_folder / "raw"
            processed_output_folder = pdf_output_folder / "processed"

            pages = PDFProcessingService.convert_pdf_to_images(
                str(input_path),
                str(raw_output_folder),
            )

            processed_pages = []

            for page in pages:

                page = Path(page)

                if document_category == "xray":
                    processed_pages.append(str(page))
                    continue

                processed_page = processed_output_folder / page.name

                ImageProcessingService.process_image(
                    str(page),
                    str(processed_page),
                )

                processed_pages.append(
                    str(processed_page)
                )

            return {

                "type": "pdf",

                "processed_files": processed_pages

            }
        elif extension == ".txt":
            output_path = output_folder / input_path.name
            output_path.write_text(
                input_path.read_text(encoding="utf-8", errors="ignore"),
                encoding="utf-8",
            )

            return {
                "type": "text",
                "processed_files": [str(output_path)]
            }

        else:

            raise ValueError(
                f"Unsupported file type: {extension}"
            )
