"""add_benchmark_run_test_error_table

Revision ID: 6427a353f25f
Revises: 87a4885183af
Create Date: 2026-07-02 12:32:02.245892

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6427a353f25f'
down_revision: Union[str, Sequence[str], None] = '87a4885183af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("PRAGMA foreign_keys = ON")

    op.create_table(
        "benchmark_run_test_error",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("benchmark_run_test_prompt_id", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.String(), nullable=False),
        sa.Column("error_source", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["benchmark_run_test_prompt_id"],
            ["benchmark_run_test_prompt.id"],
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("benchmark_run_test_error")
