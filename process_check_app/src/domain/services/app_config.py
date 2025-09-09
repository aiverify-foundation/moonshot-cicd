from __future__ import annotations

import os
from typing import Any, Optional

from domain.entities.app_config_entity import AppConfigEntity
from domain.entities.attack_module_config_entity import AttackModuleConfigEntity
from domain.entities.connector_entity import ConnectorEntity
from domain.entities.metric_config_entity import MetricConfigEntity
from domain.services.logger import configure_logger

# Configure the logger for this module
logger = configure_logger(__name__)


class AppConfig:
    """
    Handles the app's configuration loaded from YAML files using a singleton pattern.

    This class ensures that only one instance of the configuration exists throughout
    the app's lifecycle. It provides methods to access different configuration sections
    such as common settings, connector settings, metric settings, and attack module settings.
    """

    CONFIG_PATH_ENV_VAR = "MS_CONFIG_PATH"
    TEST_CONFIG_PATH_ENV_VAR = "MS_TEST_CONFIG_PATH"
    DEFAULT_CONFIG_PATH = "moonshot_config.yaml"

    DEFAULT_DATA_PATH = "data"
    DEFAULT_TEST_CONFIGS_FILE = "tests.yaml"
    DEFAULT_DATASETS_PATH = f"{DEFAULT_DATA_PATH}/datasets"
    DEFAULT_ATTACK_MODULES_PATH = f"{DEFAULT_DATA_PATH}/attack_modules"
    DEFAULT_RESULTS_PATH = f"{DEFAULT_DATA_PATH}/results"
    DEFAULT_TEST_CONFIGS_PATH = f"{DEFAULT_DATA_PATH}/test_configs"
    DEFAULT_ADAPTERS_PATH = "src/adapters"
    DEFAULT_TEMP_PATH = "src/temp"

    LOG_CONFIG_LOADED = (
        "[AppConfig] Successfully loaded configuration from {config_path}"
    )
    LOG_NO_CONFIG_FILE = (
        "[AppConfig] No configuration file found. Using default settings."
    )
    LOG_ERROR_LOADING_CONFIG = "[AppConfig] Error loading configuration: {error}"
    LOG_ERROR_LOADING_CONNECTOR_CONFIG = (
        "[AppConfig] Error loading connector configuration: {error}"
    )
    LOG_ERROR_LOADING_METRIC_CONFIG = (
        "[AppConfig] Error loading metric configuration: {error}"
    )
    LOG_ERROR_LOADING_AM_CONFIG = (
        "[AppConfig] Error loading attack_module configuration: {error}"
    )
    FILE_NOT_FOUND_ERROR = "[AppConfig] File not found: {file_name}"

    _instance: Optional[AppConfig] = None
    _config: Optional[AppConfigEntity] = None

    def __new__(cls) -> AppConfig:
        """
        Create a new instance of AppConfig if one does not already exist.

        Returns:
            AppConfig: The singleton instance of AppConfig.
        """
        # Ensure only one instance of AppConfig exists (singleton pattern)
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """
        Load the configuration file and initialize the AppConfig instance.

        This method attempts to read the configuration from a YAML file specified
        by the 'MS_CONFIG_PATH' environment variable or defaults to 'moonshot_config.yaml'.
        It deserializes the content into an AppConfigEntity object. If the file is not
        found or an error occurs, it initializes with default settings.
        """
        config_path = os.getenv(self.CONFIG_PATH_ENV_VAR, self.DEFAULT_CONFIG_PATH)
        try:
            from domain.services.enums.file_types import FileTypes
            from domain.services.loader.file_loader import FileLoader

            # Load the configuration file
            self._config = FileLoader.load(config_path, FileTypes.CONFIG)
            logger.info(self.LOG_CONFIG_LOADED.format(config_path=config_path))

        except FileNotFoundError:
            logger.error(self.FILE_NOT_FOUND_ERROR.format(file_name=config_path))
            raise
        except Exception as e:
            logger.error(self.LOG_ERROR_LOADING_CONFIG.format(error=e))
            # Initialize with default settings in case of an error
            self._config = AppConfigEntity()

    @property
    def config(self) -> Optional[AppConfigEntity]:
        """
        Access the current configuration entity.

        Returns:
            Optional[AppConfigEntity]: The current configuration entity or None if not initialized.
        """
        return self._config

    def get_common_config(self, common_config_name: str) -> Any:
        """
        Retrieve a value from the common configuration section.

        Args:
            common_config_name (str): The name of the common configuration to retrieve.

        Returns:
            Any: The value of the specified common configuration or an empty dictionary if not found.
        """
        if self._config and self._config.common:
            return self._config.common.get(common_config_name, {})
        return {}

    def get_connector_config(
        self, connector_config_name: str
    ) -> Optional[ConnectorEntity]:
        """
        Retrieve the configuration for a specific connector.

        Args:
            connector_config_name (str): The name of the connector configuration to retrieve.

        Returns:
            ConnectorEntity: The configuration entity for the specified connector, or None if not found.
        """
        if self._config and self._config.connectors_configurations:
            # Find the connector configuration by name
            connector_config = next(
                (
                    config
                    for config in self._config.connectors_configurations
                    if config["name"] == connector_config_name
                ),
                None,
            )
            if connector_config:
                try:
                    # Combine parameters from the list into a single dictionary
                    params_list = connector_config.get("params", [])
                    combined_params = {}
                    if isinstance(params_list, list):
                        for param in params_list:
                            combined_params.update(param)
                    else:
                        combined_params = params_list

                    # Return a ConnectorEntity initialized with the configuration data
                    return ConnectorEntity(
                        connector_adapter=connector_config.get("connector_adapter", ""),
                        model=connector_config.get("model", ""),
                        model_endpoint=connector_config.get("model_endpoint", ""),
                        params=combined_params,
                        connector_pre_prompt=connector_config.get(
                            "connector_pre_prompt", ""
                        ),
                        connector_post_prompt=connector_config.get(
                            "connector_post_prompt", ""
                        ),
                        system_prompt=connector_config.get("system_prompt", ""),
                    )
                except Exception as e:
                    logger.error(
                        self.LOG_ERROR_LOADING_CONNECTOR_CONFIG.format(error=e)
                    )
                    raise
        return None

    def get_metric_config(self, metric_name: str) -> Optional[MetricConfigEntity]:
        """
        Retrieve configuration for a specific metric.

        This function searches for a metric configuration by its name within the loaded configuration.
        If found, it extracts the first connector configuration and initializes a MetricConfigEntity
        with it.

        Args:
            metric_name (str): The name of the metric configuration to retrieve.

        Returns:
            MetricConfigEntity: The configuration entity for the specified metric, or None if not found.
        """
        if self._config and self._config.metrics:
            # Find the metric configuration by name
            metric_config = next(
                (
                    config
                    for config in self._config.metrics
                    if config["name"] == metric_name
                ),
                None,
            )
            if metric_config:
                try:
                    # Extract the first connector configuration
                    connector_config = metric_config.get(
                        "connector_configurations", [{}]
                    )
                    # Prepare the params if they exist
                    params = metric_config.get("params", {})

                    connector_entity = ConnectorEntity(**connector_config)
                    # Return a MetricConfigEntity initialized with the configuration data
                    return MetricConfigEntity(
                        name=metric_config.get("name", ""),
                        connector_configurations=connector_entity,
                        params=params,
                    )
                except Exception as e:
                    logger.error(self.LOG_ERROR_LOADING_METRIC_CONFIG.format(error=e))
                    raise
        return None

    def get_attack_module_config(
        self, attack_module_name: str
    ) -> Optional[AttackModuleConfigEntity]:
        """
        Retrieve configuration for a specific attack module.

        This function searches for an attack module configuration by its name within the loaded configuration.
        If found, it extracts the first connector configuration and initializes an AttackModuleConfigEntity
        with it.

        Args:
            attack_module_name (str): The name of the attack module configuration to retrieve.

        Returns:
            AttackModuleConfigEntity: The configuration entity for the specified attack module, or None if not found.
        """

        if self._config and self._config.attack_modules:
            # Find the attack module configuration by name
            attack_module_config = next(
                (
                    config
                    for config in self._config.attack_modules
                    if config["name"] == attack_module_name
                ),
                None,
            )
            if attack_module_config:
                try:
                    # Extract the list of connector configurations
                    connector_configs = attack_module_config.get(
                        "connector_configurations", []
                    )

                    # Transform each configuration into a ConnectorEntity
                    connector_entities = {
                        key: ConnectorEntity(name=key, **value)
                        for key, value in connector_configs.items()
                    }

                    # Return an AttackModuleConfigEntity initialized with the configuration data
                    return AttackModuleConfigEntity(
                        name=attack_module_config.get("name", ""),
                        connector_configurations=connector_entities,
                    )
                except Exception as e:
                    logger.error(self.LOG_ERROR_LOADING_AM_CONFIG.format(error=e))
                    raise
        return None

    def get_test_config_file_path(self) -> str:
        """
        Retrieve the file path for the test configuration.

        This method checks the environment variable 'MS_TEST_CONFIG_PATH' to determine
        the path of the test configuration file. If the environment variable is not set,
        it defaults to the predefined path specified by 'DEFAULT_TEST_CONFIGS_FILE'.

        Returns:
            str: The file path for the test configuration.
        """
        test_config_filepath = os.getenv(
            self.TEST_CONFIG_PATH_ENV_VAR, self.DEFAULT_TEST_CONFIGS_FILE
        )
        return test_config_filepath
