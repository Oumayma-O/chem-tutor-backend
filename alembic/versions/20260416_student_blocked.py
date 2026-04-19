"""Add classroom_students.is_blocked for teacher student management.

Revision ID: 20260416_student_blocked
Revises: 20260415_uniqueness_constraints
Create Date: 2026-04-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260416_student_blocked"
down_revision: Union[str, None] = "20260415_uniqueness_constraints"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "classroom_students",
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("classroom_students", "is_blocked")
