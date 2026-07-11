from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy import DateTime
from sqlalchemy import JSON
from sqlalchemy import func

from sqlalchemy.orm import relationship

from database.base import Base


class Review(Base):

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)

    document_id = Column(
        Integer,
        ForeignKey("medical_documents.id")
    )

    reviewer_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    status = Column(String)

    reviewer_notes = Column(String)

    reviewed_data = Column(JSON)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    document = relationship(
        "MedicalDocument",
        back_populates="review"
    )

    reviewer = relationship(
        "User",
        back_populates="reviews"
    )
