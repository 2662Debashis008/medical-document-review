"""Add workflow metadata fields

Revision ID: c6f8a4b2d9e1
Revises: b97fa0d3ac21
Create Date: 2026-06-28 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c6f8a4b2d9e1"
down_revision: Union[str, Sequence[str], None] = "b97fa0d3ac21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("run_metadata", sa.Column("processing_time", sa.Float(), nullable=True))
    op.add_column("run_metadata", sa.Column("document_category", sa.String(), nullable=True))
    op.add_column("run_metadata", sa.Column("file_type", sa.String(), nullable=True))
    op.add_column("run_metadata", sa.Column("errors", sa.String(), nullable=True))
    op.add_column("run_metadata", sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True))
    op.add_column("reviews", sa.Column("reviewed_data", sa.JSON(), nullable=True))
    op.add_column("reviews", sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True))
    op.add_column("reviews", sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True))
    op.add_column("extractions", sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True))
    op.add_column("export_history", sa.Column("document_count", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("export_history", "document_count")
    op.drop_column("extractions", "created_at")
    op.drop_column("reviews", "updated_at")
    op.drop_column("reviews", "created_at")
    op.drop_column("reviews", "reviewed_data")
    op.drop_column("run_metadata", "created_at")
    op.drop_column("run_metadata", "errors")
    op.drop_column("run_metadata", "file_type")
    op.drop_column("run_metadata", "document_category")
    op.drop_column("run_metadata", "processing_time")
