"""SQLAlchemy ORM models for database tables."""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class LLMProviderModel(Base):
    """
    SQLAlchemy model for the llm_provider table.
    
    This model represents an LLM provider in the database.
    """
    __tablename__ = "llm_provider"
    __table_args__ = (
        UniqueConstraint("system_name", "version", name="uq_llm_provider_system_name_version"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    system_name = Column(String, nullable=False)
    version = Column(Integer, nullable=False, server_default=text("0"), default=0)

    def __repr__(self) -> str:
        return (
            f"<LLMProviderModel(id={self.id}, name='{self.name}', "
            f"system_name='{self.system_name}', version={self.version})>"
        )


class LLMProviderModelModel(Base):
    """
    SQLAlchemy model for the llm_provider_model table.

    Stores model names under an LLM provider (referenced by benchmark_run.llm_provider_model_id).
    """
    __tablename__ = "llm_provider_model"

    id = Column(Integer, primary_key=True, autoincrement=True)
    llm_provider_id = Column(Integer, ForeignKey("llm_provider.id"), nullable=False)
    name = Column(String, nullable=False)
    create_dt = Column(DateTime, nullable=False, server_default=func.now())

    def __repr__(self) -> str:
        return f"<LLMProviderModelModel(id={self.id}, name='{self.name}')>"


class LLMProviderModelConfigModel(Base):
    """
    SQLAlchemy model for the llm_provider_model_config table.

    Named configuration for an llm_provider_model row (key/value parameters live in
    llm_provider_model_config_parameters).
    """

    __tablename__ = "llm_provider_model_config"
    __table_args__ = (
        UniqueConstraint("model_id", "name", name="uq_llm_provider_model_config_model_name"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(Integer, ForeignKey("llm_provider_model.id"), nullable=True)
    name = Column(String, nullable=False)
    updated_dt = Column(DateTime, nullable=False, server_default=func.now())
    last_used_dt = Column(DateTime, nullable=True)

    benchmark_runs = relationship(
        "BenchmarkRunModel",
        back_populates="llm_provider_model_config",
    )

    def __repr__(self) -> str:
        return f"<LLMProviderModelConfigModel(id={self.id}, name='{self.name}', model_id={self.model_id})>"


class LLMProviderModelConfigParametersModel(Base):
    """
    SQLAlchemy model for the llm_provider_model_config_parameters table.

    Key/value pairs attached to an llm_provider_model_config row.
    """

    __tablename__ = "llm_provider_model_config_parameters"
    __table_args__ = (
        UniqueConstraint(
            "config_id",
            "key",
            name="uq_llm_provider_model_config_parameters_config_key",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(Integer, ForeignKey("llm_provider_model_config.id"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<LLMProviderModelConfigParametersModel(id={self.id}, "
            f"config_id={self.config_id}, key='{self.key}')>"
        )


# Backwards-compatible alias (deprecated): use LLMProviderModelConfigParametersModel
LLMProviderEndpointConfigParametersModel = LLMProviderModelConfigParametersModel


class LLMProviderApiKeyModel(Base):
    """
    SQLAlchemy model for the llm_provider_api_key table.

    Stores one encrypted API key per llm_provider row (enforced in application code).
    """

    __tablename__ = "llm_provider_api_key"

    id = Column(Integer, primary_key=True, autoincrement=True)
    llm_provider_id = Column(Integer, ForeignKey("llm_provider.id"), nullable=False)
    encrypted_key = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    nonce = Column(String, nullable=False)
    authentication_tag = Column(String, nullable=False)
    # DB column is created_dt (2bf4af1172bc); cd225c9 create_dt only applies if that revision completes.
    create_dt = Column("created_dt", DateTime, nullable=False, server_default=func.now())
    last_used_dt = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<LLMProviderApiKeyModel(id={self.id}, llm_provider_id={self.llm_provider_id})>"


# ---------------------------------------------------------------------------
# Benchmark-related models
# ---------------------------------------------------------------------------


class BenchmarkTestDatasetModel(Base):
    """
    SQLAlchemy model for the benchmark_test_dataset table.

    Stores information about datasets used for benchmarking.
    """
    __tablename__ = "benchmark_test_dataset"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(Integer, nullable=False)
    system_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    license = Column(String, nullable=True)
    reference = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "system_name", "version",
            name="uq_benchmark_test_dataset_system_name_version",
        ),
    )

    # Relationships
    prompts = relationship("BenchmarkTestDatasetPromptModel", back_populates="dataset")
    benchmark_tests = relationship("BenchmarkTestModel", back_populates="dataset")

    def __repr__(self) -> str:
        return f"<BenchmarkTestDatasetModel(id={self.id}, system_name='{self.system_name}', version={self.version})>"


class BenchmarkTestDatasetPromptModel(Base):
    """
    SQLAlchemy model for the benchmark_test_dataset_prompt table.

    Stores individual prompts and target outputs for a benchmark dataset.
    """
    __tablename__ = "benchmark_test_dataset_prompt"

    id = Column(Integer, primary_key=True, autoincrement=True)
    benchmark_test_dataset_id = Column(
        Integer,
        ForeignKey("benchmark_test_dataset.id"),
        nullable=False,
    )
    prompt = Column(String, nullable=False)
    target = Column(String, nullable=False)

    # Relationships
    dataset = relationship("BenchmarkTestDatasetModel", back_populates="prompts")
    run_test_prompts = relationship(
        "BenchmarkRunTestPromptModel",
        back_populates="prompt",
    )

    def __repr__(self) -> str:
        return f"<BenchmarkTestDatasetPromptModel(id={self.id}, dataset_id={self.benchmark_test_dataset_id})>"


class BenchmarkTestMetricModel(Base):
    """
    SQLAlchemy model for the benchmark_test_metric table.

    Represents a metric used to evaluate benchmark test results.
    """
    __tablename__ = "benchmark_test_metric"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)

    # Relationships
    benchmark_tests = relationship("BenchmarkTestModel", back_populates="metric")

    def __repr__(self) -> str:
        return f"<BenchmarkTestMetricModel(id={self.id}, name='{self.name}')>"


class BenchmarkTestModel(Base):
    """
    SQLAlchemy model for the benchmark_test table.

    Represents an individual benchmark test or scan.
    """
    __tablename__ = "benchmark_test"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(Integer, nullable=False)
    system_name = Column(String, nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'scan' or 'benchmark'
    dataset_id = Column(
        Integer,
        ForeignKey("benchmark_test_dataset.id"),
        nullable=False,
    )
    metric_id = Column(
        Integer,
        ForeignKey("benchmark_test_metric.id"),
        nullable=False,
    )
    description = Column(Text, nullable=True)
    create_dt = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("version", "system_name", name="uq_benchmark_test_version_system_name"),
    )

    # Relationships
    dataset = relationship("BenchmarkTestDatasetModel", back_populates="benchmark_tests")
    metric = relationship("BenchmarkTestMetricModel", back_populates="benchmark_tests")
    bundle_groupings = relationship(
        "BenchmarkTestBundleGroupingModel",
        back_populates="test",
    )
    run_test_statuses = relationship(
        "BenchmarkRunTestStatusModel",
        back_populates="test",
    )
    run_test_bundles = relationship(
        "BenchmarkRunTestBundleModel",
        back_populates="test",
    )

    def __repr__(self) -> str:
        return f"<BenchmarkTestModel(id={self.id}, name='{self.name}', type='{self.type}')>"


class BenchmarkTestBundleModel(Base):
    """
    SQLAlchemy model for the benchmark_test_bundle table.

    Represents a collection or bundle of benchmark tests.
    """
    __tablename__ = "benchmark_test_bundle"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(Integer, nullable=False)
    system_name = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=False)
    visible = Column(Boolean, nullable=False, server_default=text("1"), default=True)
    create_dt = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "version",
            "system_name",
            name="uq_benchmark_test_bundle_version_system_name",
        ),
    )

    # Relationships
    test_groupings = relationship(
        "BenchmarkTestBundleGroupingModel",
        back_populates="test_bundle",
    )
    run_test_bundles = relationship(
        "BenchmarkRunTestBundleModel",
        back_populates="test_bundle",
    )

    def __repr__(self) -> str:
        return f"<BenchmarkTestBundleModel(id={self.id}, name='{self.name}')>"


class BenchmarkTestBundleGroupingModel(Base):
    """
    SQLAlchemy model for the benchmark_test_bundle_grouping table.

    Junction table linking benchmark_test_bundle and benchmark_test (many-to-many).
    """
    __tablename__ = "benchmark_test_bundle_grouping"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_bundle_id = Column(
        Integer,
        ForeignKey("benchmark_test_bundle.id"),
        nullable=False,
    )
    test_id = Column(
        Integer,
        ForeignKey("benchmark_test.id"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "test_bundle_id",
            "test_id",
            name="uq_benchmark_test_bundle_grouping_bundle_test",
        ),
    )

    # Relationships
    test_bundle = relationship("BenchmarkTestBundleModel", back_populates="test_groupings")
    test = relationship("BenchmarkTestModel", back_populates="bundle_groupings")

    def __repr__(self) -> str:
        return f"<BenchmarkTestBundleGroupingModel(id={self.id}, bundle_id={self.test_bundle_id}, test_id={self.test_id})>"


# ---------------------------------------------------------------------------
# Custom app models
# ---------------------------------------------------------------------------


class CustomAppModel(Base):
    """SQLAlchemy model for the custom_app table."""

    __tablename__ = "custom_app"
    __table_args__ = (UniqueConstraint("name", name="uq_custom_app_name"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    configs = relationship("CustomAppConfigModel", back_populates="custom_app")

    def __repr__(self) -> str:
        return f"<CustomAppModel(id={self.id}, name='{self.name}')>"


class CustomAppConfigModel(Base):
    """SQLAlchemy model for the custom_app_config table."""

    __tablename__ = "custom_app_config"
    __table_args__ = (
        UniqueConstraint(
            "custom_app_id",
            "name",
            name="uq_custom_app_config_custom_app_id_name",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    custom_app_id = Column(Integer, ForeignKey("custom_app.id"), nullable=False)
    name = Column(String, nullable=False)
    update_dt = Column(DateTime, nullable=False, server_default=func.now())

    custom_app = relationship("CustomAppModel", back_populates="configs")
    parameters = relationship("CustomAppConfigParametersModel", back_populates="config")
    secrets = relationship("CustomAppConfigSecretsModel", back_populates="config")
    benchmark_runs = relationship("BenchmarkRunModel", back_populates="custom_app_config")

    def __repr__(self) -> str:
        return (
            f"<CustomAppConfigModel(id={self.id}, name='{self.name}', "
            f"custom_app_id={self.custom_app_id})>"
        )


class CustomAppConfigParametersModel(Base):
    """SQLAlchemy model for the custom_app_config_parameters table."""

    __tablename__ = "custom_app_config_parameters"
    __table_args__ = (
        UniqueConstraint(
            "config_id",
            "key",
            name="uq_custom_app_config_parameters_config_key",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(Integer, ForeignKey("custom_app_config.id"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)

    config = relationship("CustomAppConfigModel", back_populates="parameters")

    def __repr__(self) -> str:
        return (
            f"<CustomAppConfigParametersModel(id={self.id}, "
            f"config_id={self.config_id}, key='{self.key}')>"
        )


class CustomAppConfigSecretsModel(Base):
    """SQLAlchemy model for the custom_app_config_secrets table."""

    __tablename__ = "custom_app_config_secrets"
    __table_args__ = (
        UniqueConstraint(
            "config_id",
            "key",
            name="uq_custom_app_config_secrets_config_key",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(Integer, ForeignKey("custom_app_config.id"), nullable=False)
    key = Column(String, nullable=False)
    encrypted_secret = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    nonce = Column(String, nullable=False)
    authentication_tag = Column(String, nullable=False)

    config = relationship("CustomAppConfigModel", back_populates="secrets")

    def __repr__(self) -> str:
        return (
            f"<CustomAppConfigSecretsModel(id={self.id}, "
            f"config_id={self.config_id}, key='{self.key}')>"
        )


# ---------------------------------------------------------------------------
# AIVF product: benchmark run, endpoint config
# ---------------------------------------------------------------------------


class LLMProviderEndpointConfigModel(Base):
    """
    SQLAlchemy model for the llm_provider_endpoint_config table.

    Endpoint configuration for an LLM provider (referenced by benchmark_run).
    """
    __tablename__ = "llm_provider_endpoint_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    llm_provider_id = Column(Integer, ForeignKey("llm_provider.id"), nullable=True)
    name = Column(String, nullable=False)

    # Relationships
    llm_provider = relationship("LLMProviderModel", backref="endpoint_configs")

    def __repr__(self) -> str:
        return f"<LLMProviderEndpointConfigModel(id={self.id}, name='{self.name}')>"


class BenchmarkRunModel(Base):
    """
    SQLAlchemy model for the benchmark_run table.

    A single benchmark run (LLM provider endpoint).
    """
    __tablename__ = "benchmark_run"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    start_time = Column(DateTime, nullable=False, server_default=func.now())
    end_time = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)
    endpoint_type = Column(String, nullable=False)  # LLM_Provider, Custom_App
    llm_provider_id = Column(Integer, ForeignKey("llm_provider.id"), nullable=True)
    llm_provider_model_id = Column(Integer, ForeignKey("llm_provider_model.id"), nullable=True)
    llm_provider_model_config_id = Column(
        Integer,
        ForeignKey("llm_provider_model_config.id"),
        nullable=True,
    )
    custom_app_id = Column(Integer, ForeignKey("custom_app.id"), nullable=True)
    custom_app_config_id = Column(Integer, ForeignKey("custom_app_config.id"), nullable=True)

    # Relationships
    llm_provider = relationship("LLMProviderModel", backref="benchmark_runs")
    llm_provider_model_config = relationship(
        "LLMProviderModelConfigModel",
        back_populates="benchmark_runs",
    )
    custom_app = relationship("CustomAppModel", backref="benchmark_runs")
    custom_app_config = relationship(
        "CustomAppConfigModel",
        back_populates="benchmark_runs",
    )
    run_test_statuses = relationship(
        "BenchmarkRunTestStatusModel",
        back_populates="run",
    )
    run_test_bundles = relationship(
        "BenchmarkRunTestBundleModel",
        back_populates="run",
    )

    def __repr__(self) -> str:
        return f"<BenchmarkRunModel(id={self.id}, name='{self.name}', status='{self.status}')>"


class BenchmarkRunTestStatusModel(Base):
    """
    SQLAlchemy model for the benchmark_run_test_status table.

    Status of a single test within a benchmark run (not_started, in_progress, completed, pause, skipped).
    """
    __tablename__ = "benchmark_run_test_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("benchmark_run.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("benchmark_test.id"), nullable=False)
    status = Column(String, nullable=False)
    start_dt = Column(DateTime, nullable=True)
    end_dt = Column(DateTime, nullable=True)
    connector_pre_prompt = Column(String, nullable=True)
    connector_post_prompt = Column(String, nullable=True)
    system_prompt = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("run_id", "test_id", name="uq_benchmark_run_test_status_run_test"),
    )

    # Relationships
    run = relationship("BenchmarkRunModel", back_populates="run_test_statuses")
    test = relationship("BenchmarkTestModel", back_populates="run_test_statuses")
    run_test_prompts = relationship(
        "BenchmarkRunTestPromptModel",
        back_populates="run_test_status",
    )

    def __repr__(self) -> str:
        return f"<BenchmarkRunTestStatusModel(id={self.id}, run_id={self.run_id}, test_id={self.test_id})>"


class BenchmarkRunTestPromptModel(Base):
    """
    SQLAlchemy model for the benchmark_run_test_prompt table.

    Per-prompt result within a run-test (target, prediction, evaluation, user_notes).
    """
    __tablename__ = "benchmark_run_test_prompt"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_test_id = Column(Integer, ForeignKey("benchmark_run_test_status.id"), nullable=False)
    prompt_id = Column(Integer, ForeignKey("benchmark_test_dataset_prompt.id"), nullable=False)
    status = Column(String, nullable=False)
    prompt_additional_info = Column(String, nullable=True)
    target = Column(String, nullable=False)
    prediction_result = Column(String, nullable=True)
    prediction_context = Column(String, nullable=True)
    evaluation_prompt = Column(String, nullable=True)
    evaluation_prediction_result = Column(String, nullable=True)
    evaluation_accuracy = Column(Float, nullable=True)
    user_evaluation = Column(Integer, nullable=True)
    user_notes = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "run_test_id",
            "prompt_id",
            name="uq_benchmark_run_test_prompt_run_test_prompt",
        ),
    )

    # Relationships
    run_test_status = relationship("BenchmarkRunTestStatusModel", back_populates="run_test_prompts")
    prompt = relationship("BenchmarkTestDatasetPromptModel", back_populates="run_test_prompts")

    def __repr__(self) -> str:
        return f"<BenchmarkRunTestPromptModel(id={self.id}, run_test_id={self.run_test_id}, prompt_id={self.prompt_id})>"


class BenchmarkRunTestBundleModel(Base):
    """
    SQLAlchemy model for the benchmark_run_test_bundle table.

    Links a benchmark run to (test_bundle_id, test_id) for which tests/bundles are in the run.
    """
    __tablename__ = "benchmark_run_test_bundle"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("benchmark_run.id"), nullable=False)
    test_bundle_id = Column(Integer, ForeignKey("benchmark_test_bundle.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("benchmark_test.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "test_bundle_id",
            "test_id",
            name="uq_benchmark_run_test_bundle_run_bundle_test",
        ),
    )

    # Relationships
    run = relationship("BenchmarkRunModel", back_populates="run_test_bundles")
    test_bundle = relationship("BenchmarkTestBundleModel", back_populates="run_test_bundles")
    test = relationship("BenchmarkTestModel", back_populates="run_test_bundles")

    def __repr__(self) -> str:
        return f"<BenchmarkRunTestBundleModel(id={self.id}, run_id={self.run_id})>"


class MoonshotConfigModel(Base):
    """
    SQLAlchemy model for the moonshot_config table.

    Stores application configuration as key-value pairs.
    """
    __tablename__ = "moonshot_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, nullable=False, unique=True)
    value = Column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<MoonshotConfigModel(id={self.id}, key='{self.key}')>"
