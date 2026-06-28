"""add processing_status to uploads

Revision ID: 0002_add_processing_status
Revises: 0001_initial
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_add_processing_status"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "uploads",
        sa.Column(
            "processing_status",
            sa.String,
            nullable=False,
            server_default="pending",
        ),
    )


def downgrade() -> None:
    op.drop_column("uploads", "processing_status")
