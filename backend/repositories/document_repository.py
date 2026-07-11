from sqlalchemy.orm import Session

from models.medical_document import MedicalDocument


class DocumentRepository:

    @staticmethod
    def create(db: Session, data: dict):

        document = MedicalDocument(**data)

        db.add(document)
        db.commit()
        db.refresh(document)

        return document

    @staticmethod
    def get_all(db: Session):

        return (
            db.query(MedicalDocument)
            .order_by(MedicalDocument.created_at.desc())
            .all()
        )

    @staticmethod
    def get_by_id(db: Session, document_id: int):

        return (
            db.query(MedicalDocument)
            .filter(MedicalDocument.id == document_id)
            .first()
        )

    @staticmethod
    def delete(db: Session, document_id: int):

        document = DocumentRepository.get_by_id(
            db,
            document_id,
        )

        if not document:
            return None

        db.delete(document)
        db.commit()

        return document