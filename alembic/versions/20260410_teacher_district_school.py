"""Add users.district and users.school for teacher onboarding.

Revision ID: 20260410_teacher_onboard
Revises: 20260410_min_l1_l2
Create Date: 2026-04-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260410_teacher_onboard"
down_revision: Union[str, None] = "20260410_min_l1_l2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("district", sa.String(300), nullable=True))
    op.add_column("users", sa.Column("school", sa.String(300), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "school")
    op.drop_column("users", "district")
