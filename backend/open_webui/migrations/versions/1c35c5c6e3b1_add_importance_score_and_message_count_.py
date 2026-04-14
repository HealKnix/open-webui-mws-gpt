"""Add importance_score and message_count to chat_summary

Revision ID: 1c35c5c6e3b1
Revises: 20ec0241e978
Create Date: 2026-04-11 03:11:51.510027

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = '1c35c5c6e3b1'
down_revision: Union[str, None] = '20ec0241e978'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
