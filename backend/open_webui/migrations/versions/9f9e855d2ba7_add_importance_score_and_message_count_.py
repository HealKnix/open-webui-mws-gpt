"""Add importance_score and message_count to chat_summary

Revision ID: 9f9e855d2ba7
Revises: 1c35c5c6e3b1
Create Date: 2026-04-11 18:04:07.242564

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = '9f9e855d2ba7'
down_revision: Union[str, None] = '1c35c5c6e3b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add importance_score column
    op.add_column('chat_summary', sa.Column('importance_score', sa.Float(), nullable=True, server_default='0.5'))
    # Add message_count column
    op.add_column('chat_summary', sa.Column('message_count', sa.BigInteger(), nullable=True, server_default='0'))


def downgrade() -> None:
    # Drop message_count column
    op.drop_column('chat_summary', 'message_count')
    # Drop importance_score column
    op.drop_column('chat_summary', 'importance_score')
