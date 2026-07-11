from pathlib import Path

import fitz

class PDFProcessingService:

    @staticmethod
    def convert_pdf_to_images(input_pdf_path: str, output_folder: str, dpi: int = 180):
        input_pdf_path = Path(input_pdf_path)
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)

        output_paths = []

        with fitz.open(input_pdf_path) as document:
            for page_number, page in enumerate(document, start=1):
                output_path = output_folder / f"{input_pdf_path.stem}_page_{page_number}.png"
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                pixmap.save(output_path)
                output_paths.append(str(output_path))

        if not output_paths:
            raise ValueError(f"PDF has no renderable pages: {input_pdf_path}")

        return output_paths
