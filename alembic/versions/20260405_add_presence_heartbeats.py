"""Add presence_heartbeats for live session polling.

Revision ID: 20260405_presence
Revises: 0258e0f4835d
Create Date: 2026-04-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260405_presence"
down_revision: Union[str, None] = "0258e0f4835d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "presence_heartbeats",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("classroom_id", sa.UUID(), nullable=False),
        sa.Column("step_id", sa.String(length=120), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "classroom_id"),
    )
    op.create_index(
        "ix_presence_classroom_seen",
        "presence_heartbeats",
        ["classroom_id", "last_seen_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_presence_classroom_seen", table_name="presence_heartbeats")
    op.drop_table("presence_heartbeats")
