"""Add user_session_activity table for teacher engagement tracking.

Revision ID: 20260410_user_session
Revises: 20260410_teacher_onboard
Create Date: 2026-04-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "20260410_user_session"
down_revision: Union[str, None] = "20260410_teacher_onboard"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_session_activity",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("login_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total_minutes_active", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("user_id", "session_date", name="uq_user_session_date"),
    )
    op.create_index("ix_user_session_user_date", "user_session_activity", ["user_id", "session_date"])


def downgrade() -> None:
    op.drop_index("ix_user_session_user_date", table_name="user_session_activity")
    op.drop_table("user_session_activity")
