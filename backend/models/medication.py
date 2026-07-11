from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import ForeignKey

from sqlalchemy.orm import relationship

from database.base import Base


class Medication(Base):

    __tablename__ = "medications"

    id = Column(Integer, primary_key=True)

    extraction_id = Column(
        Integer,
        ForeignKey("extractions.id")
    )

    medication_name = Column(String)

    dosage = Column(String)

    unit = Column(String)

    frequency = Column(String)

    route = Column(String)

    duration = Column(String)

    instructions = Column(String)

    uncertainty_notes = Column(String)

    extraction = relationship(
        "Extraction",
        back_populates="medications"
    )