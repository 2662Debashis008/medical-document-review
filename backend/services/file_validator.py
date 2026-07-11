from pathlib import Path

from fastapi import UploadFile

from exceptions.file_exceptions import (
    InvalidDocumentCategoryException,
    InvalidExtensionException,
    InvalidFileSizeException,
    InvalidFileTypeException,
    InvalidMimeTypeException,
)

from utils.file_constants import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    DOCUMENT_CATEGORIES,
    EXTENSION_TO_FILE_TYPE,
    FILE_TYPES,
    MAX_FILE_SIZE,
)


class FileValidator:

    @staticmethod
    def validate_document_category(category: str):

        if category.lower() not in DOCUMENT_CATEGORIES:
            raise InvalidDocumentCategoryException(
                f"Unsupported category: {category}"
            )

    @staticmethod
    def validate_extension(filename: str):

        extension = Path(filename).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise InvalidExtensionException(
                f"Unsupported extension: {extension}"
            )

        return extension

    @staticmethod
    def validate_file_type(extension: str):

        file_type = EXTENSION_TO_FILE_TYPE.get(extension)

        if file_type not in FILE_TYPES:
            raise InvalidFileTypeException(
                f"Unsupported file type: {file_type}"
            )

        return file_type

    @staticmethod
    def validate_mime_type(upload_file: UploadFile):

        if upload_file.content_type not in ALLOWED_MIME_TYPES:
            raise InvalidMimeTypeException(
                f"Unsupported MIME Type: {upload_file.content_type}"
            )

    @staticmethod
    async def validate_file_size(upload_file: UploadFile):

        contents = await upload_file.read()

        size = len(contents)

        await upload_file.seek(0)

        if size > MAX_FILE_SIZE:
            raise InvalidFileSizeException(
                f"Maximum file size is {MAX_FILE_SIZE // (1024 * 1024)} MB"
            )

        return size

    @classmethod
    async def validate(
        cls,
        upload_file: UploadFile,
        document_category: str,
    ):

        cls.validate_document_category(document_category)

        extension = cls.validate_extension(upload_file.filename)

        file_type = cls.validate_file_type(extension)

        cls.validate_mime_type(upload_file)

        file_size = await cls.validate_file_size(upload_file)

        return {
            "extension": extension,
            "file_type": file_type,
            "file_size": file_size,
        }