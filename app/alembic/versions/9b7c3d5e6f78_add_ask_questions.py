"""add ask_questions

Revision ID: 9b7c3d5e6f78
Revises: 8a6b2c4d5e67
Create Date: 2026-10-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "9b7c3d5e6f78"
down_revision: str | Sequence[str] | None = "8a6b2c4d5e67"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """A new table only, so the running release is unaffected."""
    op.create_table(
        "ask_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("quote", sa.Text(), nullable=True),
        sa.Column("page", sa.String(200), nullable=True),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("citations", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("truncated", sa.Boolean(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("admin", sa.Boolean(), nullable=False),
        sa.Column("rating", sa.String(8), nullable=True),
    )
    op.create_index("ix_ask_questions_created_at", "ask_questions", ["created_at"])
    op.create_index("ix_ask_questions_rating", "ask_questions", ["rating"])


def downgrade() -> None:
    op.drop_index("ix_ask_questions_rating", table_name="ask_questions")
    op.drop_index("ix_ask_questions_created_at", table_name="ask_questions")
    op.drop_table("ask_questions")
