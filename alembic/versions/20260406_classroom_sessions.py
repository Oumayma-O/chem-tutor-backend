"""classroom_sessions

Revision ID: 20260406_cls_sessions
Revises: 20260406_et_lesson_id
Create Date: 2026-04-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260406_cls_sessions"
down_revision: Union[str, None] = "20260406_et_lesson_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "classroom_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "classroom_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("classrooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_type", sa.String(40), nullable=False, server_default="exit_ticket"),
        sa.Column(
            "exit_ticket_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("exit_tickets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("unit_id", sa.String(100), nullable=False),
        sa.Column("lesson_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("timed_practice_minutes", sa.Integer, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_classroom_sessions_classroom_id",
        "classroom_sessions",
        ["classroom_id"],
    )
    op.create_index(
        "ix_classroom_sessions_class_started",
        "classroom_sessions",
        ["classroom_id", "started_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_classroom_sessions_class_started", table_name="classroom_sessions")
    op.drop_index("ix_classroom_sessions_classroom_id", table_name="classroom_sessions")
    op.drop_table("classroom_sessions")
