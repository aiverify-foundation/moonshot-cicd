"""remove_custom_app

Revision ID: cd225c9fcc5f
Revises: 87a4885183af
Create Date: 2026-02-19 15:49:12.196852

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd225c9fcc5f'
down_revision: Union[str, Sequence[str], None] = '87a4885183af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove custom_app and custom_app_config tables and their FK columns from benchmark_run.
    """
    # Drop columns that reference custom_app / custom_app_config (SQLite-friendly batch)
    with op.batch_alter_table("benchmark_run", schema=None) as batch_op:
        batch_op.drop_column("custom_app_config_id")
        batch_op.drop_column("custom_app_id")
    op.drop_table("custom_app_config")
    op.drop_table("custom_app")


def downgrade() -> None:
    """Restore custom_app and custom_app_config and FK columns on benchmark_run."""
    op.create_table(
        "custom_app",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "custom_app_config",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("custom_app_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["custom_app_id"], ["custom_app.id"]),
    )
    with op.batch_alter_table("benchmark_run", schema=None) as batch_op:
        batch_op.add_column(sa.Column("custom_app_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("custom_app_config_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_benchmark_run_custom_app_id_custom_app",
            "custom_app",
            ["custom_app_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_benchmark_run_custom_app_config_id_custom_app_config",
            "custom_app_config",
            ["custom_app_config_id"],
            ["id"],
        )
