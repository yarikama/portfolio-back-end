"""add min_token_prob to autocomplete_suggestions

Revision ID: 7e5f1a3b4c56
Revises: 6d4e0f2a3b45
Create Date: 2026-09-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7e5f1a3b4c56"
down_revision: Union[str, Sequence[str], None] = "6d4e0f2a3b45"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """A nullable column, so the running release is unaffected."""
    op.add_column(
        "autocomplete_suggestions",
        sa.Column("min_token_prob", sa.Float(), nullable=True),
    )
    # Every suggestion so far was shown with the original cut-off.
    op.execute("UPDATE autocomplete_suggestions SET min_token_prob = 0.5")


def downgrade() -> None:
    op.drop_column("autocomplete_suggestions", "min_token_prob")
