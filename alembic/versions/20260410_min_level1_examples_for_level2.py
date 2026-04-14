"""Add classrooms.min_level1_examples_for_level2.

Revision ID: 20260410_min_l1_l2
Revises: 20260409_max_reveals
Create Date: 2026-04-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260410_min_l1_l2"
down_revision: Union[str, None] = "20260409_max_reveals"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "classrooms",
        sa.Column(
            "min_level1_examples_for_level2",
            sa.Integer(),
            nullable=False,
            server_default="2",
        ),
    )


def downgrade() -> None:
    op.drop_column("classrooms", "min_level1_examples_for_level2")
