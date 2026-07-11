from sqlalchemy import inspect, text

from database.base import Base
from database.session import engine

# Import all models
from models.user import User
from models.medical_document import MedicalDocument
from models.extraction import Extraction
from models.medication import Medication
from models.review import Review
from models.run_metadata import RunMetadata
from models.export_history import ExportHistory


def init_db():
    Base.metadata.create_all(bind=engine)


def ensure_schema():
    init_db()

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    def add_column_if_missing(table_name: str, column_name: str, ddl: str):
        if table_name not in tables:
            return
        existing_columns = {
            column["name"] for column in inspector.get_columns(table_name)
        }
        if column_name not in existing_columns:
            with engine.begin() as connection:
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))

    add_column_if_missing("run_metadata", "processing_time", "processing_time FLOAT")
    add_column_if_missing("run_metadata", "document_category", "document_category VARCHAR")
    add_column_if_missing("run_metadata", "file_type", "file_type VARCHAR")
    add_column_if_missing("run_metadata", "errors", "errors VARCHAR")
    add_column_if_missing("run_metadata", "created_at", "created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
    add_column_if_missing("reviews", "reviewed_data", "reviewed_data JSON")
    add_column_if_missing("reviews", "created_at", "created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
    add_column_if_missing("reviews", "updated_at", "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
    add_column_if_missing("extractions", "created_at", "created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
    add_column_if_missing("export_history", "document_count", "document_count INTEGER")
