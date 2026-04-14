"""Add mcp_app table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-13 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from open_webui.migrations.util import get_existing_tables

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing_tables = set(get_existing_tables())

    if 'mcp_app' not in existing_tables:
        op.create_table(
            'mcp_app',
            sa.Column('id', sa.String(), nullable=False, primary_key=True),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('name', sa.Text(), nullable=False, unique=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('icon', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            # MCP Connection
            sa.Column('transport', sa.String(), nullable=False),
            sa.Column('url', sa.Text(), nullable=True),
            sa.Column('command', sa.Text(), nullable=True),
            sa.Column('args', sa.JSON(), nullable=True),
            sa.Column('env_encrypted', sa.Text(), nullable=True),
            sa.Column('auth_type', sa.String(), nullable=True),
            sa.Column('auth_config_encrypted', sa.Text(), nullable=True),
            # App Configuration
            sa.Column('tool_configs', sa.JSON(), nullable=True),
            sa.Column('skill_prompt', sa.Text(), nullable=True),
            sa.Column('widget_ids', sa.JSON(), nullable=True),
            # Access & Meta
            sa.Column('access_control', sa.JSON(), nullable=True),
            sa.Column('meta', sa.JSON(), nullable=True),
            sa.Column('updated_at', sa.BigInteger(), nullable=False),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
        )
        op.create_index('idx_mcp_app_user_id', 'mcp_app', ['user_id'])
        op.create_index('idx_mcp_app_updated_at', 'mcp_app', ['updated_at'])


def downgrade() -> None:
    op.drop_index('idx_mcp_app_updated_at', table_name='mcp_app')
    op.drop_index('idx_mcp_app_user_id', table_name='mcp_app')
    op.drop_table('mcp_app')
