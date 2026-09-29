"""add autocomplete_suggestions

Revision ID: 6d4e0f2a3b45
Revises: 5c3d9e1f2a34
Create Date: 2026-09-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6d4e0f2a3b45"
down_revision: Union[str, Sequence[str], None] = "5c3d9e1f2a34"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """A new table only, so the running release is unaffected."""
    op.create_table(
        "autocomplete_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("model_version", sa.String(200), nullable=False),
        sa.Column("note_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("completion", sa.Text(), nullable=False),
        sa.Column("suggestion", sa.Text(), nullable=False),
        sa.Column("tokens", postgresql.JSONB(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=True),
        sa.Column("accepted_chars", sa.Integer(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_autocomplete_suggestions_note_id", "autocomplete_suggestions", ["note_id"])
    op.create_index("ix_autocomplete_suggestions_outcome", "autocomplete_suggestions", ["outcome"])


def downgrade() -> None:
    op.drop_index("ix_autocomplete_suggestions_outcome", table_name="autocomplete_suggestions")
    op.drop_index("ix_autocomplete_suggestions_note_id", table_name="autocomplete_suggestions")
    op.drop_table("autocomplete_suggestions")
