from pathlib import Path
from utils.image_utils import ImageUtils


class ImageProcessingService:

    @staticmethod
    def process_image(input_path: str, output_path: str):

        image = ImageUtils.load_image(input_path)

        image = ImageUtils.resize(image)
        image = ImageUtils.grayscale(image)
        image = ImageUtils.remove_noise(image)
        image = ImageUtils.enhance_contrast(image)
        image = ImageUtils.deskew(image)

        ImageUtils.save_image(
            image=image,
            output_path=output_path,
        )

        return output_path