from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy import Float
from sqlalchemy import DateTime
from sqlalchemy import func

from sqlalchemy.orm import relationship

from database.base import Base


class RunMetadata(Base):

    __tablename__ = "run_metadata"

    id = Column(Integer, primary_key=True)

    document_id = Column(
        Integer,
        ForeignKey("medical_documents.id")
    )

    model_name = Column(String)

    model_version = Column(String)

    runtime = Column(String)

    prompt_version = Column(String)

    latency = Column(Float)

    processing_time = Column(Float)

    document_category = Column(String)

    file_type = Column(String)

    errors = Column(String)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    document = relationship(
        "MedicalDocument",
        back_populates="metadata_run"
    )
