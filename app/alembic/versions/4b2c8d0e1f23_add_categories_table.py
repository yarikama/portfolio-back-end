"""add categories table and category_id to projects

Revision ID: 4b2c8d0e1f23
Revises: 3a91f5925050
Create Date: 2026-01-23

"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4b2c8d0e1f23'
down_revision: Union[str, Sequence[str], None] = '3a91f5925050'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Predefined category UUIDs for consistent migration
ENGINEERING_UUID = '11111111-1111-1111-1111-111111111111'
ML_UUID = '22222222-2222-2222-2222-222222222222'


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_categories_name'), 'categories', ['name'], unique=True)

    # 2. Insert default categories
    op.execute(f"""
        INSERT INTO categories (id, name, label, description, "order", created_at, updated_at)
        VALUES
            ('{ENGINEERING_UUID}', 'engineering', 'Engineering', 'Software engineering projects', 0, NOW(), NOW()),
            ('{ML_UUID}', 'ml', 'ML/AI', 'Machine learning and AI projects', 1, NOW(), NOW())
    """)

    # 3. Add category_id column to projects (nullable initially)
    op.add_column('projects', sa.Column('category_id', sa.UUID(), nullable=True))

    # 4. Migrate existing data: set category_id based on current category string
    op.execute(f"""
        UPDATE projects
        SET category_id = '{ENGINEERING_UUID}'
        WHERE category = 'engineering'
    """)
    op.execute(f"""
        UPDATE projects
        SET category_id = '{ML_UUID}'
        WHERE category = 'ml'
    """)

    # 5. Handle any projects with unknown categories (assign to engineering by default)
    op.execute(f"""
        UPDATE projects
        SET category_id = '{ENGINEERING_UUID}'
        WHERE category_id IS NULL
    """)

    # 6. Make category_id NOT NULL
    op.alter_column('projects', 'category_id', nullable=False)

    # 7. Add foreign key constraint
    op.create_foreign_key(
        'fk_projects_category_id',
        'projects', 'categories',
        ['category_id'], ['id']
    )

    # 8. Make old category column nullable (keep for backward compatibility)
    op.alter_column('projects', 'category', nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Ensure category column has values from category_id
    op.execute(f"""
        UPDATE projects p
        SET category = c.name
        FROM categories c
        WHERE p.category_id = c.id
    """)

    # 2. Make category NOT NULL again
    op.alter_column('projects', 'category', nullable=False)

    # 3. Drop foreign key
    op.drop_constraint('fk_projects_category_id', 'projects', type_='foreignkey')

    # 4. Drop category_id column
    op.drop_column('projects', 'category_id')

    # 5. Drop categories table
    op.drop_index(op.f('ix_categories_name'), table_name='categories')
    op.drop_table('categories')
