from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import func
from sqlalchemy import Integer

from database.base import Base


class ExportHistory(Base):

    __tablename__ = "export_history"

    id = Column(Integer, primary_key=True)

    export_type = Column(String)

    exported_by = Column(String)

    document_count = Column(Integer)

    exported_at = Column(
        DateTime,
        server_default=func.now()
    )
