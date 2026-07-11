import uuid


def generate_uuid_filename(extension: str) -> str:
    return f"{uuid.uuid4()}{extension}"