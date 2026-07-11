from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import func

from sqlalchemy.orm import relationship

from database.base import Base


class MedicalDocument(Base):

    __tablename__ = "medical_documents"

    id = Column(Integer, primary_key=True, index=True)

    document_category = Column(String, nullable=False)

    file_type = Column(String, nullable=False)

    original_filename = Column(String, nullable=False)

    stored_filename = Column(String, nullable=False)

    storage_path = Column(String, nullable=False)

    status = Column(String, default="uploaded")

    created_at = Column(DateTime, server_default=func.now())

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    extraction = relationship(
        "Extraction",
        back_populates="document",
        uselist=False
    )

    review = relationship(
        "Review",
        back_populates="document",
        uselist=False
    )

    metadata_run = relationship(
        "RunMetadata",
        back_populates="document",
        uselist=False
    )

    @property
    def review_status(self):
        return self.review.status if self.review else None

    @property
    def extraction_error(self):
        return self.metadata_run.errors if self.metadata_run else None
