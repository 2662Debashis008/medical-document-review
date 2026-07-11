class FileValidationException(Exception):
    """Base exception for file validation."""
    pass


class InvalidExtensionException(FileValidationException):
    pass


class InvalidMimeTypeException(FileValidationException):
    pass


class InvalidFileSizeException(FileValidationException):
    pass


class InvalidDocumentCategoryException(FileValidationException):
    pass


class InvalidFileTypeException(FileValidationException):
    pass