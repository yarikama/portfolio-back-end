"""add admin_seen

Revision ID: b3d4f5a6c7e8
Revises: a1c2e3f4b5d6
Create Date: 2026-10-02

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3d4f5a6c7e8"
down_revision: str | Sequence[str] | None = "a1c2e3f4b5d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """A new table only, so the running release is unaffected."""
    op.create_table(
        "admin_seen",
        sa.Column("email", sa.Text(), primary_key=True),
        sa.Column("page", sa.String(32), primary_key=True),
        sa.Column("seen_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("admin_seen")
