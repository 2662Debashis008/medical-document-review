from pathlib import Path
import shutil
import uuid

import fitz
from PIL import Image, ImageDraw

from services.preprocessing_service import PreprocessingService


def create_sample_image(path: Path):
    image = Image.new("RGB", (400, 220), "white")
    draw = ImageDraw.Draw(image)
    draw.text((30, 80), "Prescription Sample", fill="black")
    image.save(path)


def create_sample_pdf(path: Path):
    document = fitz.open()
    page = document.new_page(width=400, height=220)
    page.insert_text((40, 100), "Prescription PDF Sample")
    document.save(path)
    document.close()


BASE_DIR = Path(__file__).parent


def workspace_temp_dir() -> Path:
    path = BASE_DIR / ".tmp" / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_image():
    temp_dir = workspace_temp_dir()
    image = temp_dir / "sample.png"

    try:
        create_sample_image(image)

        result = PreprocessingService.preprocess(image)

        assert result["type"] == "image"
        assert Path(result["processed_files"][0]).exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_xray_image_is_preserved():
    temp_dir = workspace_temp_dir()
    image = temp_dir / "xray.jpg"

    try:
        create_sample_image(image)

        result = PreprocessingService.preprocess(image, "xray", "image")

        assert result["type"] == "image"
        processed = Path(result["processed_files"][0])
        assert processed.exists()
        assert processed.read_bytes() == image.read_bytes()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_pdf():
    temp_dir = workspace_temp_dir()
    pdf = temp_dir / "sample_prescription.pdf"

    try:
        create_sample_pdf(pdf)

        result = PreprocessingService.preprocess(pdf)

        assert result["type"] == "pdf"
        assert result["processed_files"]
        assert all(Path(path).exists() for path in result["processed_files"])
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_xray_pdf_pages_are_preserved_without_image_cleanup():
    temp_dir = workspace_temp_dir()
    pdf = temp_dir / "sample_xray.pdf"

    try:
        create_sample_pdf(pdf)

        result = PreprocessingService.preprocess(pdf, "xray", "pdf")

        assert result["type"] == "pdf"
        assert result["processed_files"]
        assert all("/raw/" in Path(path).as_posix() for path in result["processed_files"])
        assert all(Path(path).exists() for path in result["processed_files"])
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_lab_report_preprocessing():
    temp_dir = workspace_temp_dir()
    image = temp_dir / "lab.jpg"
    pdf = temp_dir / "lab.pdf"

    try:
        create_sample_image(image)
        result_img = PreprocessingService.preprocess(image, "lab_report", "image")
        assert result_img["type"] == "image"
        assert Path(result_img["processed_files"][0]).exists()

        create_sample_pdf(pdf)
        result_pdf = PreprocessingService.preprocess(pdf, "lab_report", "pdf")
        assert result_pdf["type"] == "pdf"
        assert result_pdf["processed_files"]
        assert all(Path(path).exists() for path in result_pdf["processed_files"])
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_image()
    test_pdf()

