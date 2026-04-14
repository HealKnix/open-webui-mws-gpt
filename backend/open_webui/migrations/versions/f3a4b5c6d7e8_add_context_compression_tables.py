"""Add context compression tables

Revision ID: f3a4b5c6d7e8
Revises: 9f9e855d2ba7
Create Date: 2026-04-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = 'f3a4b5c6d7e8'
down_revision: Union[str, None] = '9f9e855d2ba7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create chat_context_segment table
    op.create_table(
        'chat_context_segment',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('chat_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('parent_segment_id', sa.String(), nullable=True),
        sa.Column('from_message_id', sa.String(), nullable=False),
        sa.Column('to_message_id', sa.String(), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('summary_json', sa.Text(), nullable=False),  # JSON stored as text
        sa.Column('tool_digest_json', sa.Text(), nullable=True),  # JSON stored as text
        sa.Column('token_count_before', sa.Integer(), nullable=True, default=0),
        sa.Column('token_count_after', sa.Integer(), nullable=True, default=0),
        sa.Column('status', sa.String(), nullable=True, default='active'),
        sa.Column('version', sa.Integer(), nullable=True, default=1),
        sa.Column('created_at', sa.BigInteger(), nullable=False),
        sa.Column('expires_at', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for chat_context_segment
    op.create_index('idx_chat_context_segment_chat_created', 'chat_context_segment', ['chat_id', 'created_at'])
    op.create_index('idx_chat_context_segment_chat_status', 'chat_context_segment', ['chat_id', 'status'])
    op.create_index('idx_chat_context_segment_expires', 'chat_context_segment', ['expires_at'])
    op.create_index('idx_chat_context_segment_parent', 'chat_context_segment', ['parent_segment_id'])
    op.create_index('idx_chat_context_segment_user_id', 'chat_context_segment', ['user_id'])

    # Create chat_context_state table
    op.create_table(
        'chat_context_state',
        sa.Column('chat_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('last_compacted_message_id', sa.String(), nullable=True),
        sa.Column('active_segment_id', sa.String(), nullable=True),
        sa.Column('threshold_messages', sa.Integer(), nullable=True, default=20),
        sa.Column('keep_last_messages', sa.Integer(), nullable=True, default=5),
        sa.Column('threshold_tokens', sa.Integer(), nullable=True, default=4000),
        sa.Column('enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('include_tool_data', sa.Boolean(), nullable=True, default=True),
        sa.Column('max_segment_age_days', sa.Integer(), nullable=True, default=30),
        sa.Column('max_segments_per_chat', sa.Integer(), nullable=True, default=10),
        sa.Column('updated_at', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('chat_id'),
    )

    # Create indexes for chat_context_state
    op.create_index('idx_chat_context_state_user_id', 'chat_context_state', ['user_id'])
    op.create_index('idx_chat_context_state_enabled', 'chat_context_state', ['enabled'])


def downgrade() -> None:
    # Drop indexes for chat_context_state
    op.drop_index('idx_chat_context_state_enabled', table_name='chat_context_state')
    op.drop_index('idx_chat_context_state_user_id', table_name='chat_context_state')

    # Drop chat_context_state table
    op.drop_table('chat_context_state')

    # Drop indexes for chat_context_segment
    op.drop_index('idx_chat_context_segment_user_id', table_name='chat_context_segment')
    op.drop_index('idx_chat_context_segment_parent', table_name='chat_context_segment')
    op.drop_index('idx_chat_context_segment_expires', table_name='chat_context_segment')
    op.drop_index('idx_chat_context_segment_chat_status', table_name='chat_context_segment')
    op.drop_index('idx_chat_context_segment_chat_created', table_name='chat_context_segment')

    # Drop chat_context_segment table
    op.drop_table('chat_context_segment')
