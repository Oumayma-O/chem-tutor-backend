"""Add classrooms.max_answer_reveals_per_lesson.

Revision ID: 20260409_max_reveals
Revises: 20260408_et_resp_unique
Create Date: 2026-04-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260409_max_reveals"
down_revision: Union[str, None] = "20260408_et_resp_unique"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "classrooms",
        sa.Column(
            "max_answer_reveals_per_lesson",
            sa.Integer(),
            nullable=False,
            server_default="6",
        ),
    )


def downgrade() -> None:
    op.drop_column("classrooms", "max_answer_reveals_per_lesson")
