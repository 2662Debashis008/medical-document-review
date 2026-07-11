from sqlalchemy.orm import Session

from models.review import Review
from repositories.document_repository import DocumentRepository
from schemas.workflow import ReviewUpdate


class ReviewService:
    @staticmethod
    def get_review(db: Session, document_id: int):
        return db.query(Review).filter(Review.document_id == document_id).first()

    @staticmethod
    def upsert_review(db: Session, document_id: int, payload: ReviewUpdate):
        document = DocumentRepository.get_by_id(db, document_id)
        if not document:
            raise ValueError("Document not found")

        review = ReviewService.get_review(db, document_id)
        if not review:
            review = Review(document_id=document_id)
            db.add(review)

        review.status = payload.status
        review.reviewer_notes = payload.reviewer_notes
        review.reviewed_data = payload.reviewed_data
        review.reviewer_id = payload.reviewer_id
        document.status = "reviewed" if payload.status == "approved" else payload.status

        db.commit()
        db.refresh(review)
        return review
