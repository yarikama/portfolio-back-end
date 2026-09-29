"""add accepted_tokens to autocomplete_suggestions

Revision ID: 8a6b2c4d5e67
Revises: 7e5f1a3b4c56
Create Date: 2026-09-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8a6b2c4d5e67"
down_revision: Union[str, Sequence[str], None] = "7e5f1a3b4c56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """A nullable column, so the running release is unaffected."""
    op.add_column(
        "autocomplete_suggestions",
        sa.Column("accepted_tokens", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("autocomplete_suggestions", "accepted_tokens")
