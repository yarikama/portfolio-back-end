"""add cover_image to projects

Revision ID: 5c3d9e1f2a34
Revises: 4b2c8d0e1f23
Create Date: 2026-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c3d9e1f2a34'
down_revision: Union[str, Sequence[str], None] = '4b2c8d0e1f23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add cover_image column to projects table."""
    op.add_column('projects', sa.Column('cover_image', sa.String(500), nullable=True))


def downgrade() -> None:
    """Remove cover_image column from projects table."""
    op.drop_column('projects', 'cover_image')
