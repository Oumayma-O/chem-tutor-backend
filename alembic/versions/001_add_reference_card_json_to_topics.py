"""add reference_card_json to topics

Revision ID: 001
Revises:
Create Date: 2026-03-03

NOTE: The 'topics' table was renamed to 'lessons' in the current schema.
The column 'reference_card_json' already exists on the 'lessons' model
via create_all. This migration is kept as a no-op for alembic history.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
