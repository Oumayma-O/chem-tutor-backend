"""Uniqueness: teacher+class name (active), one admin per school.

Revision ID: 20260415_uniqueness
Revises: 20260415_et_resp_time
Create Date: 2026-04-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260415_uniqueness"
down_revision: Union[str, None] = "20260415_et_resp_time"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # A teacher cannot have two active classrooms with the same name (case-sensitive at DB level).
    op.create_index(
        "uq_classroom_teacher_name_active",
        "classrooms",
        ["teacher_id", "name"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )

    # Only one admin account may be assigned to each school.
    op.create_index(
        "uq_admin_school",
        "users",
        ["school"],
        unique=True,
        postgresql_where=sa.text("role = 'admin'"),
    )


def downgrade() -> None:
    op.drop_index("uq_admin_school", table_name="users")
    op.drop_index("uq_classroom_teacher_name_active", table_name="classrooms")
