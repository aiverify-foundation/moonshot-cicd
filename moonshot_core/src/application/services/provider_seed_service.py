from typing import List, Optional

from application.ports.provider_repository import ProviderRepository
from adapters.connector.openai_adapter import OpenAIAdapter
from adapters.connector.together_adapter import TogetherAdapter
from adapters.driven.repository.sqlalchemy.llm_provider_adapter import LLMProviderAdapter
from domain.entities.provider_entity import ProviderEntity
from domain.services.logger import configure_logger


class ProviderSeedService:
    """
    Seed the llm_provider table from a hardcoded list of providers.

    Version rules per system_name:
    - If no row exists: insert hardcoded version.
    - If hardcoded_version > max_existing_version: insert new row.
    - Otherwise (equal or lower): skip.
    """

    def __init__(self, provider_repository: Optional[ProviderRepository] = None) -> None:
        self.logger = configure_logger(__name__)
        self.provider_repository: ProviderRepository = provider_repository or LLMProviderAdapter()

    def _get_adapter_provider_definitions(self) -> list[dict]:
        """
        Build provider definitions from connector adapter class metadata.
        """
        return [
            OpenAIAdapter.provider_seed_definition(),
            TogetherAdapter.provider_seed_definition(),
        ]

    def seed_hardcoded_providers(self) -> None:
        """Seed providers from adapter metadata with version-aware logic."""
        self.logger.info("Seeding hardcoded LLM providers")

        existing_providers: List[ProviderEntity] = self.provider_repository.list_providers()
        providers_by_system_name: dict[str, List[ProviderEntity]] = {}
        for provider in existing_providers:
            providers_by_system_name.setdefault(provider.system_name, []).append(provider)

        for cfg in self._get_adapter_provider_definitions():
            name = cfg["name"]
            system_name = cfg["system_name"]
            hardcoded_version = cfg["version"]

            existing_for_system = providers_by_system_name.get(system_name, [])
            if not existing_for_system:
                self.logger.info(
                    "No existing provider for %s; inserting version %s",
                    system_name,
                    hardcoded_version,
                )
                self.provider_repository.add_provider(
                    name=name,
                    system_name=system_name,
                    version=hardcoded_version,
                )
                # Refresh cache to include newly added provider
                new_entities = self.provider_repository.list_providers()
                providers_by_system_name[system_name] = [
                    p for p in new_entities if p.system_name == system_name
                ]
                continue

            max_existing_version = max(p.version for p in existing_for_system)

            if hardcoded_version > max_existing_version:
                self.logger.info(
                    "Found %s with max version %s; inserting newer version %s",
                    system_name,
                    max_existing_version,
                    hardcoded_version,
                )
                self.provider_repository.add_provider(
                    name=name,
                    system_name=system_name,
                    version=hardcoded_version,
                )
                # Refresh cache to include newly added provider
                new_entities = self.provider_repository.list_providers()
                providers_by_system_name[system_name] = [
                    p for p in new_entities if p.system_name == system_name
                ]
            else:
                self.logger.info(
                    "Skipping %s v%s (max existing version %s)",
                    system_name,
                    hardcoded_version,
                    max_existing_version,
                )

