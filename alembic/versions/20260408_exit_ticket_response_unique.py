"""Unique (exit_ticket_id, student_id) on exit_ticket_responses.

Revision ID: 20260408_et_resp_unique
Revises: 20260407_answer_reveal
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260408_et_resp_unique"
down_revision: Union[str, None] = "20260407_answer_reveal"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_exit_ticket_responses_ticket_student",
        "exit_ticket_responses",
        ["exit_ticket_id", "student_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_exit_ticket_responses_ticket_student",
        "exit_ticket_responses",
        type_="unique",
    )
