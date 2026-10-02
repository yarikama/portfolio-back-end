"""add admin_todos

Revision ID: c6e7f8a9b0c1
Revises: b3d4f5a6c7e8
Create Date: 2026-10-02

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c6e7f8a9b0c1"
down_revision: str | Sequence[str] | None = "b3d4f5a6c7e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """A new table only, so the running release is unaffected."""
    op.create_table(
        "admin_todos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("href", sa.Text(), nullable=True),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("daily_key", sa.String(32), nullable=True),
        sa.Column("done_on", sa.Date(), nullable=True),
        sa.Column("removed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_admin_todos_day", "admin_todos", ["day"])
    op.create_index(
        "uq_admin_todos_daily_day",
        "admin_todos",
        ["daily_key", "day"],
        unique=True,
        postgresql_where=sa.text("daily_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_table("admin_todos")
