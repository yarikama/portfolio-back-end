"""contact messages: name and subject without length limits

Revision ID: a1c2e3f4b5d6
Revises: 9b7c3d5e6f78
Create Date: 2026-10-02

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1c2e3f4b5d6"
down_revision: str | Sequence[str] | None = "9b7c3d5e6f78"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    VARCHAR(n) to TEXT is binary-compatible in PostgreSQL: no table rewrite,
    and the running release keeps working with it.
    """
    for column, length in (("name", 100), ("subject", 200)):
        op.alter_column(
            "contact_messages",
            column,
            type_=sa.Text(),
            existing_type=sa.String(length),
            existing_nullable=False,
        )


def downgrade() -> None:
    # Longer values are cut to fit.
    for column, length in (("name", 100), ("subject", 200)):
        op.alter_column(
            "contact_messages",
            column,
            type_=sa.String(length),
            existing_type=sa.Text(),
            existing_nullable=False,
            postgresql_using=f"left({column}, {length})",
        )
