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
    Add LLM provider, API key, model, model config, and endpoint config parameters tables.
    """
    # Drop columns that reference custom_app / custom_app_config (SQLite-friendly batch)
    with op.batch_alter_table("benchmark_run", schema=None) as batch_op:
        batch_op.drop_column("custom_app_config_id")
        batch_op.drop_column("custom_app_id")
    op.drop_table("custom_app_config")
    op.drop_table("custom_app")

    # ---- LLM provider and config tables (per ERD) ----
    op.create_table(
        "llm_provider",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("system_name", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("system_name", "version", name="uq_llm_provider_system_name_version"),
    )
    op.create_table(
        "llm_provider_api_key",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("llm_provider_id", sa.Integer(), nullable=False),
        sa.Column("encrypted_key", sa.String(), nullable=False),
        sa.Column("salt", sa.String(), nullable=False),
        sa.Column("nonce", sa.String(), nullable=False),
        sa.Column("authentication_tag", sa.String(), nullable=False),
        sa.Column("create_dt", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("last_used_dt", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["llm_provider_id"], ["llm_provider.id"]),
    )
    op.create_table(
        "llm_provider_model",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("llm_provider_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("create_dt", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["llm_provider_id"], ["llm_provider.id"]),
        sa.UniqueConstraint("llm_provider_id", "name", name="uq_llm_provider_model_provider_name"),
    )
    op.create_table(
        "llm_provider_model_config",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("model_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("updated_dt", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("last_used_dt", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["model_id"], ["llm_provider_model.id"]),
        sa.UniqueConstraint("model_id", "name", name="uq_llm_provider_model_config_model_name"),
    )
    op.create_table(
        "llm_provider_endpoint_config_parameters",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("config_id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["config_id"], ["llm_provider_model_config.id"]),
        sa.UniqueConstraint("config_id", "key", name="uq_llm_provider_endpoint_config_parameters_config_key"),
    )


def downgrade() -> None:
    """Drop LLM provider/config tables; restore custom_app and custom_app_config and FK columns on benchmark_run."""
    op.drop_table("llm_provider_endpoint_config_parameters")
    op.drop_table("llm_provider_model_config")
    op.drop_table("llm_provider_model")
    op.drop_table("llm_provider_api_key")
    op.drop_table("llm_provider")
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
