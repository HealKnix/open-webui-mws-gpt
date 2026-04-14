"""Add widget table

Revision ID: c3d4e5f6a7b8
Revises: f3a4b5c6d7e8
Create Date: 2026-04-12 21:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from open_webui.migrations.util import get_existing_tables

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'f3a4b5c6d7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing_tables = set(get_existing_tables())

    if 'widget' not in existing_tables:
        op.create_table(
            'widget',
            sa.Column('id', sa.String(), nullable=False, primary_key=True),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('name', sa.Text(), nullable=False, unique=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('meta', sa.JSON(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('updated_at', sa.BigInteger(), nullable=False),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
        )
        op.create_index('idx_widget_user_id', 'widget', ['user_id'])
        op.create_index('idx_widget_updated_at', 'widget', ['updated_at'])


def downgrade() -> None:
    op.drop_index('idx_widget_updated_at', table_name='widget')
    op.drop_index('idx_widget_user_id', table_name='widget')
    op.drop_table('widget')
