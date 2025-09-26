from abc import ABC, abstractmethod
from typing import Any


class Loader(ABC):
    """
    Abstract base class for loaders.

    This class defines the interface for loading various types of modules or data.
    Subclasses should provide concrete implementations of the load method.
    """

    @abstractmethod
    def load(self, loader_name: str) -> Any:
        """
        Load a module or data by its name.

        Args:
            loader_name (str): The name of the module or data to load.

        Returns:
            Any: The loaded module or data.
        """
        pass
