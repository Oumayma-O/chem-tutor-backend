"""exit_ticket_lesson_id

Revision ID: 20260406_et_lesson_id
Revises: c4732611e81f
Create Date: 2026-04-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260406_et_lesson_id'
down_revision: Union[str, None] = 'c4732611e81f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('exit_tickets', sa.Column('lesson_id', sa.String(200), nullable=True))
    op.create_index(op.f('ix_exit_tickets_lesson_id'), 'exit_tickets', ['lesson_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_exit_tickets_lesson_id'), table_name='exit_tickets')
    op.drop_column('exit_tickets', 'lesson_id')
