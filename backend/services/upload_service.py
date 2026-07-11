from sqlalchemy.orm import Session
from fastapi import UploadFile

from repositories.document_repository import DocumentRepository

from services.file_validator import FileValidator
from services.storage_service import StorageService
from services.preprocessing_service import PreprocessingService

from config.logger import logger


class UploadService:

    @staticmethod
    async def upload_document(
        db: Session,
        upload_file: UploadFile,
        document_category: str,
    ):

        logger.info("Starting upload process")

        try:

            # -----------------------------------
            # Validate uploaded file
            # -----------------------------------

            validation = await FileValidator.validate(
                upload_file,
                document_category,
            )

            logger.info("File validation completed")

            # -----------------------------------
            # Store original uploaded file
            # -----------------------------------

            storage = await StorageService.save_file(
                upload_file,
                document_category,
                validation["file_type"],
            )

            logger.info("Original file stored successfully")

            # -----------------------------------
            # Preprocess file
            # -----------------------------------

            processed_data = PreprocessingService.preprocess(

                input_path=storage["storage_path"],

                document_category=document_category,

                file_type=validation["file_type"],

            )

            logger.info("Preprocessing completed")

            # -----------------------------------
            # Save document metadata in SQLite
            # -----------------------------------

            document_data = {

                "document_category": document_category,

                "file_type": validation["file_type"],

                "original_filename": storage["original_filename"],

                "stored_filename": storage["stored_filename"],

                "storage_path": storage["storage_path"],

                "status": "uploaded",

            }

            document = DocumentRepository.create(
                db,
                document_data,
            )

            logger.info(
                f"Document saved in database. ID={document.id}"
            )

            # -----------------------------------
            # Return response
            # -----------------------------------

            return document, processed_data["processed_files"]

        except Exception as e:

            logger.exception(e)

            raise