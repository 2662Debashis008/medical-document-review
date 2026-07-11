import cv2
import numpy as np
from pathlib import Path


class ImageUtils:

    @staticmethod
    def load_image(image_path: str):

        image = cv2.imread(image_path)

        if image is None:
            raise Exception(f"Unable to load image: {image_path}")

        return image

    @staticmethod
    def resize(image, width=1200):

        h, w = image.shape[:2]

        if w <= width:
            return image

        ratio = width / w

        new_height = int(h * ratio)

        return cv2.resize(
            image,
            (width, new_height),
            interpolation=cv2.INTER_AREA,
        )

    @staticmethod
    def grayscale(image):

        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def remove_noise(image):

        return cv2.fastNlMeansDenoising(
            image,
            None,
            10,
            7,
            21,
        )

    @staticmethod
    def enhance_contrast(image):

        clahe = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8),
        )

        return clahe.apply(image)

    @staticmethod
    def deskew(image):
        # Threshold the image (text is dark, background is light)
        # We invert it so text is white (255) and background is black (0)
        thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        
        # Find all coordinates of non-zero pixels (the text)
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) == 0:
            return image
            
        angle = cv2.minAreaRect(coords)[-1]
        
        # The angle returned is in range [-90, 0) or [0, 90) depending on OpenCV version
        # Adjust angle to get correct skew
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle
            
        # Only rotate if the skew is minor (e.g. within 20 degrees).
        # Wild angles suggest area estimation failed, so ignore them to prevent side-rotation.
        if abs(angle) > 20 or abs(angle) < 0.1:
            return image
            
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(
            image,
            matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

    @staticmethod
    def save_image(image, output_path: str):

        Path(output_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        cv2.imwrite(output_path, image)

        return output_path