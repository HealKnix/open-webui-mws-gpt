"""Add chat_summaries table

Revision ID: 20ec0241e978
Revises: b2c3d4e5f6a7
Create Date: 2026-04-11 02:39:16.271634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = '20ec0241e978'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create chat_summaries table
    op.create_table(
        'chat_summary',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('chat_id', sa.String(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('insights', sa.JSON(), nullable=True),
        sa.Column('importance_score', sa.Float(), nullable=True, default=0.5),
        sa.Column('message_count', sa.BigInteger(), nullable=True, default=0),
        sa.Column('created_at', sa.BigInteger(), nullable=True),
        sa.Column('updated_at', sa.BigInteger(), nullable=True),
        sa.Column('expires_at', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes
    op.create_index('idx_chat_summary_user_id', 'chat_summary', ['user_id'])
    op.create_index('idx_chat_summary_chat_id', 'chat_summary', ['chat_id'])
    op.create_index('idx_chat_summary_category', 'chat_summary', ['category'])
    op.create_index('idx_chat_summary_user_category', 'chat_summary', ['user_id', 'category'])
    op.create_index('idx_chat_summary_expires', 'chat_summary', ['expires_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_chat_summary_expires', table_name='chat_summary')
    op.drop_index('idx_chat_summary_user_category', table_name='chat_summary')
    op.drop_index('idx_chat_summary_category', table_name='chat_summary')
    op.drop_index('idx_chat_summary_chat_id', table_name='chat_summary')
    op.drop_index('idx_chat_summary_user_id', table_name='chat_summary')
    
    # Drop table
    op.drop_table('chat_summary')
