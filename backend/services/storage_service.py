from pathlib import Path

import aiofiles
from fastapi import UploadFile

from config.storage import STORAGE_PATHS
from utils.uuid_generator import generate_uuid_filename


class StorageService:

    @staticmethod
    async def save_file(
        upload_file: UploadFile,
        document_category: str,
        file_type: str,
    ):

        storage_directory = STORAGE_PATHS[document_category][file_type]

        Path(storage_directory).mkdir(
            parents=True,
            exist_ok=True
        )

        extension = Path(upload_file.filename).suffix.lower()

        stored_filename = generate_uuid_filename(extension)

        file_path = storage_directory / stored_filename

        async with aiofiles.open(file_path, "wb") as out_file:

            content = await upload_file.read()

            await out_file.write(content)

        await upload_file.seek(0)

        return {

            "original_filename": upload_file.filename,

            "stored_filename": stored_filename,

            "storage_path": str(file_path),

            "document_category": document_category,

            "file_type": file_type,

            "file_size": len(content)

        }