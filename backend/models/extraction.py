from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy import JSON
from sqlalchemy import DateTime
from sqlalchemy import func

from sqlalchemy.orm import relationship

from database.base import Base


class Extraction(Base):

    __tablename__ = "extractions"

    id = Column(Integer, primary_key=True)

    document_id = Column(
        Integer,
        ForeignKey("medical_documents.id")
    )

    extracted_json = Column(JSON)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    document = relationship(
        "MedicalDocument",
        back_populates="extraction"
    )

    medications = relationship(
        "Medication",
        back_populates="extraction"
    )
