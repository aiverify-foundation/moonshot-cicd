from typing import Any

from pydantic import BaseModel


class AppConfigEntity(BaseModel):
    """
    AppConfigEntity represents the application configuration loaded from a YAML file.

    Attributes:
        common (dict[str, Any]): Common configuration settings such as max_concurrency, max_calls_per_minute,
        and max_attempts.
        connectors_configurations (list[dict[str, Any]]): Configuration settings for various connectors.
        metrics (list[dict[str, Any]]): Configuration settings for different metrics.
        attack_modules (list[dict[str, Any]]): Configuration settings for different attack modules.
    """

    class Config:
        arbitrary_types_allowed = True

    # Common configuration settings with default values
    common: dict[str, Any] = {
        "max_concurrency": 5,
        "max_calls_per_minute": 60,
        "max_attempts": 3,
    }

    # List of connector configurations
    connectors_configurations: list[dict[str, Any]] = []

    # List of metric configurations
    metrics: list[dict[str, Any]] = []

    # List of attack module configurations
    attack_modules: list[dict[str, Any]] = []
