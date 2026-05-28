"""add_benchmark_related_tables_and_aivf_run_tables

Revision ID: 87a4885183af
Revises: 2bf4af1172bc
Create Date: 2026-02-12 10:15:11.720319

Benchmark test/dataset/metric/bundle tables + AIVF product tables
(benchmark_run, run_test_status, run_test_prompt, run_test_bundle,
llm_provider_endpoint_config, custom_app, custom_app_config).
benchmark_run references llm_provider_model_config for saved model configuration.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87a4885183af'
down_revision: Union[str, Sequence[str], None] = '2bf4af1172bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable foreign key constraints for SQLite
    op.execute("PRAGMA foreign_keys = ON")

    # Create benchmark_test_dataset table (referenced by benchmark_test and benchmark_test_dataset_prompt)
    op.create_table(
        "benchmark_test_dataset",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("system_name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("license", sa.String(), nullable=True),
        sa.Column("reference", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version", "system_name", name="uq_benchmark_test_dataset_system_name_version"),
    )

    # Create benchmark_test_dataset_prompt table
    op.create_table(
        "benchmark_test_dataset_prompt",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("benchmark_test_dataset_id", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.String(), nullable=False),
        sa.Column("target", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["benchmark_test_dataset_id"],
            ["benchmark_test_dataset.id"],
        ),
    )

    # Create benchmark_test_metric table (referenced by benchmark_test.metric_id)
    op.create_table(
        "benchmark_test_metric",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create benchmark_test table
    op.create_table(
        "benchmark_test",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("system_name", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),  # 'scan' or 'benchmark'
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("metric_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("create_dt", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["dataset_id"], ["benchmark_test_dataset.id"]),
        sa.ForeignKeyConstraint(["metric_id"], ["benchmark_test_metric.id"]),
        sa.UniqueConstraint("version", "system_name", name="uq_benchmark_test_version_system_name"),
    )

    # Create benchmark_test_bundle table
    op.create_table(
        "benchmark_test_bundle",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("system_name", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("visible", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("create_dt", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version", "system_name", name="uq_benchmark_test_bundle_version_system_name"),
    )

    # Create benchmark_test_bundle_grouping junction table (many-to-many: bundle <-> test)
    op.create_table(
        "benchmark_test_bundle_grouping",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("test_bundle_id", sa.Integer(), nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["test_bundle_id"], ["benchmark_test_bundle.id"]),
        sa.ForeignKeyConstraint(["test_id"], ["benchmark_test.id"]),
        sa.UniqueConstraint("test_bundle_id", "test_id", name="uq_benchmark_test_bundle_grouping_bundle_test"),
    )

    # ---- AIVF product: benchmark run, endpoint config, custom app ----
    op.create_table(
        "llm_provider_endpoint_config",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("llm_provider_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["llm_provider_id"], ["llm_provider.id"]),
    )
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
    op.create_table(
        "benchmark_run",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("endpoint_type", sa.String(), nullable=False),  # LLM_Provider, Custom_App
        sa.Column("llm_provider_id", sa.Integer(), nullable=True),
        sa.Column("llm_provider_model_id", sa.Integer(), nullable=True),
        sa.Column("llm_provider_model_config_id", sa.Integer(), nullable=True),
        sa.Column("custom_app_id", sa.Integer(), nullable=True),
        sa.Column("custom_app_config_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_benchmark_run_name"),
        sa.ForeignKeyConstraint(["llm_provider_id"], ["llm_provider.id"]),
        sa.ForeignKeyConstraint(["llm_provider_model_id"], ["llm_provider_model.id"]),
        sa.ForeignKeyConstraint(
            ["llm_provider_model_config_id"],
            ["llm_provider_model_config.id"],
            name="fk_benchmark_run_llm_provider_model_config_id",
        ),
        sa.ForeignKeyConstraint(["custom_app_id"], ["custom_app.id"]),
        sa.ForeignKeyConstraint(["custom_app_config_id"], ["custom_app_config.id"]),
    )
    op.create_table(
        "benchmark_run_test_status",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),  # not_started, in_progress, completed, pause, skipped
        sa.Column("start_dt", sa.DateTime(), nullable=True),
        sa.Column("end_dt", sa.DateTime(), nullable=True),
        sa.Column("connector_pre_prompt", sa.String(), nullable=True),
        sa.Column("connector_post_prompt", sa.String(), nullable=True),
        sa.Column("system_prompt", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "test_id", name="uq_benchmark_run_test_status_run_test"),
        sa.ForeignKeyConstraint(["run_id"], ["benchmark_run.id"]),
        sa.ForeignKeyConstraint(["test_id"], ["benchmark_test.id"]),
    )
    op.create_table(
        "benchmark_run_test_prompt",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("run_test_id", sa.Integer(), nullable=False),
        sa.Column("prompt_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("prompt_additional_info", sa.String(), nullable=True),
        sa.Column("target", sa.String(), nullable=False),
        sa.Column("prediction_result", sa.String(), nullable=True),
        sa.Column("prediction_context", sa.String(), nullable=True),
        sa.Column("evaluation_prompt", sa.String(), nullable=True),
        sa.Column("evaluation_prediction_result", sa.String(), nullable=True),
        sa.Column("evaluation_accuracy", sa.Float(), nullable=True),
        sa.Column("user_evaluation", sa.Integer(), nullable=True),
        sa.Column("user_notes", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_test_id", "prompt_id", name="uq_benchmark_run_test_prompt_run_test_prompt"),
        sa.ForeignKeyConstraint(["run_test_id"], ["benchmark_run_test_status.id"]),
        sa.ForeignKeyConstraint(["prompt_id"], ["benchmark_test_dataset_prompt.id"]),
    )
    op.create_table(
        "benchmark_run_test_bundle",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("test_bundle_id", sa.Integer(), nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id", "test_bundle_id", "test_id",
            name="uq_benchmark_run_test_bundle_run_bundle_test",
        ),
        sa.ForeignKeyConstraint(["run_id"], ["benchmark_run.id"]),
        sa.ForeignKeyConstraint(["test_bundle_id"], ["benchmark_test_bundle.id"]),
        sa.ForeignKeyConstraint(["test_id"], ["benchmark_test.id"]),
    )


def downgrade() -> None:
    """Downgrade schema (drop AIVF tables first, then benchmark tables)."""
    op.drop_table("benchmark_run_test_bundle")
    op.drop_table("benchmark_run_test_prompt")
    op.drop_table("benchmark_run_test_status")
    op.drop_table("benchmark_run")
    op.drop_table("custom_app_config")
    op.drop_table("custom_app")
    op.drop_table("llm_provider_endpoint_config")
    op.drop_table("benchmark_test_bundle_grouping")
    op.drop_table("benchmark_test_bundle")
    op.drop_table("benchmark_test")
    op.drop_table("benchmark_test_metric")
    op.drop_table("benchmark_test_dataset_prompt")
    op.drop_table("benchmark_test_dataset")
