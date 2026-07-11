from sqlalchemy.orm import Session

from models.run_metadata import RunMetadata


class MetadataService:
    @staticmethod
    def get_by_document_id(db: Session, document_id: int):
        return (
            db.query(RunMetadata)
            .filter(RunMetadata.document_id == document_id)
            .first()
        )
