"""initial usage tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usage_daily",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("project", sa.String(length=512), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cache_creation_tokens", sa.Integer(), nullable=False),
        sa.Column("cache_read_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("total_cost", sa.Float(), nullable=False),
        sa.Column("models_json", sa.Text(), nullable=False),
        sa.Column("raw_json", sa.Text(), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "date", "project", "source", name="uq_usage_user_date_project_source"),
    )
    op.create_index(op.f("ix_usage_daily_date"), "usage_daily", ["date"], unique=False)
    op.create_index(op.f("ix_usage_daily_project"), "usage_daily", ["project"], unique=False)
    op.create_index(op.f("ix_usage_daily_source"), "usage_daily", ["source"], unique=False)
    op.create_index(op.f("ix_usage_daily_user_id"), "usage_daily", ["user_id"], unique=False)

    op.create_table(
        "usage_models",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("usage_id", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cache_creation_tokens", sa.Integer(), nullable=False),
        sa.Column("cache_read_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("total_cost", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["usage_id"], ["usage_daily.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usage_id", "model", name="uq_usage_model"),
    )
    op.create_index(op.f("ix_usage_models_model"), "usage_models", ["model"], unique=False)
    op.create_index(op.f("ix_usage_models_usage_id"), "usage_models", ["usage_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_usage_models_usage_id"), table_name="usage_models")
    op.drop_index(op.f("ix_usage_models_model"), table_name="usage_models")
    op.drop_table("usage_models")
    op.drop_index(op.f("ix_usage_daily_user_id"), table_name="usage_daily")
    op.drop_index(op.f("ix_usage_daily_source"), table_name="usage_daily")
    op.drop_index(op.f("ix_usage_daily_project"), table_name="usage_daily")
    op.drop_index(op.f("ix_usage_daily_date"), table_name="usage_daily")
    op.drop_table("usage_daily")

