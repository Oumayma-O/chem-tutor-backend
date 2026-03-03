"""add reference_card_json to topics

Revision ID: 001
Revises:
Create Date: 2026-03-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "topics",
        sa.Column("reference_card_json", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("topics", "reference_card_json")
