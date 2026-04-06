"""Add classrooms.calculator_enabled boolean column.

Revision ID: 20260405_calc_enabled
Revises: 20260405_live_sess
Create Date: 2026-04-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260405_calc_enabled"
down_revision: Union[str, None] = "20260405_live_sess"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "classrooms",
        sa.Column("calculator_enabled", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_column("classrooms", "calculator_enabled")
