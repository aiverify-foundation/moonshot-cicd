"""add_benchmark_run_test_prompt_metric_reasoning_table

Revision ID: 95403bb4e4d0
Revises: 6427a353f25f
Create Date: 2026-10-22 10:40:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "95403bb4e4d0"
down_revision: Union[str, Sequence[str], None] = "6427a353f25f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("PRAGMA foreign_keys = ON")

    op.create_table(
        "benchmark_run_test_prompt_metric_reasoning",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("benchmark_run_test_prompt_id", sa.Integer(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column(
            "create_dt", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["benchmark_run_test_prompt_id"],
            ["benchmark_run_test_prompt.id"],
        ),
    )
    op.create_index(
        "ix_benchmark_run_test_prompt_metric_reasoning_prompt_id",
        "benchmark_run_test_prompt_metric_reasoning",
        ["benchmark_run_test_prompt_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_benchmark_run_test_prompt_metric_reasoning_prompt_id",
        table_name="benchmark_run_test_prompt_metric_reasoning",
    )
    op.drop_table("benchmark_run_test_prompt_metric_reasoning")
