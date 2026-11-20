from abc import ABC, abstractmethod


class FeatureFlagPort(ABC):
    """
    Port for loading feature flags from any source (file, env, DynamoDB, etc.).
    """

    SOURCE_NAME: str

    @abstractmethod
    def load_flags(self) -> dict[str, bool]:
        """
        Return all flags from this source.

        Missing or unreadable sources should return an empty dict.
        """
        pass

    def is_enabled(self, name: str) -> bool:
        """
        Return whether the named flag is enabled.

        Adapters may override this for per-flag lookups (e.g. DynamoDB GetItem).
        """
        return bool(self.load_flags().get(name, False))
