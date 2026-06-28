"""initial schema - users, uploads, recordings, transcripts, commitments, commitment_events

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-20

"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

commitment_status_enum = sa.Enum(
    "detected", "confirmed", "active", "modified",
    "blocked", "fulfilled", "missed", "cancelled",
    name="commitmentstatus",
)

file_type_enum = sa.Enum("audio", "transcript", name="filetype")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("email", sa.String, nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "uploads",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("file_name", sa.String, nullable=False),
        sa.Column("file_type", file_type_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "recordings",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("upload_id", sa.Integer, sa.ForeignKey("uploads.id"), nullable=False),
        sa.Column("audio_path", sa.String, nullable=False),
        sa.Column("duration", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "transcripts",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("upload_id", sa.Integer, sa.ForeignKey("uploads.id"), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "commitments",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("owner", sa.String, nullable=False),
        sa.Column("action", sa.String, nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", commitment_status_enum, nullable=False, server_default="detected"),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("source_transcript_id", sa.Integer, sa.ForeignKey("transcripts.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "commitment_events",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("commitment_id", sa.Integer, sa.ForeignKey("commitments.id"), nullable=False),
        sa.Column("event_type", sa.String, nullable=False),
        sa.Column("event_data", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("commitment_events")
    op.drop_table("commitments")
    op.drop_table("transcripts")
    op.drop_table("recordings")
    op.drop_table("uploads")
    op.drop_table("users")
    commitment_status_enum.drop(op.get_bind(), checkfirst=True)
    file_type_enum.drop(op.get_bind(), checkfirst=True)
