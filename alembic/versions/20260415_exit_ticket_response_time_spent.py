"""Add time_spent_s to exit_ticket_responses.

Revision ID: 20260415_et_resp_time
Revises: 20260410_teacher_onboard
Create Date: 2026-04-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260415_et_resp_time"
down_revision: Union[str, None] = "20260410_user_session"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exit_ticket_responses",
        sa.Column("time_spent_s", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("exit_ticket_responses", "time_spent_s")
