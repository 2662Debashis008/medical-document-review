from pathlib import Path

import fitz


class PDFUtils:

    @staticmethod
    def open_pdf(pdf_path: str):

        return fitz.open(pdf_path)

    @staticmethod
    def convert_page_to_image(page, output_path: str):

        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

        Path(output_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        pix.save(output_path)

        return output_path