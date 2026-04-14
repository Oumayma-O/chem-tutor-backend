"""Add classrooms.allow_answer_reveal boolean.

Revision ID: 20260407_answer_reveal
Revises: 20260406_cls_sessions
Create Date: 2026-04-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260407_answer_reveal"
down_revision: Union[str, None] = "20260406_cls_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "classrooms",
        sa.Column("allow_answer_reveal", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_column("classrooms", "allow_answer_reveal")
