from abc import ABC, abstractmethod


class ApiPort(ABC):
    @abstractmethod
    def create_run_test(self, config_filename: str, connector: str) -> None:
        """
        Create a run test.

        Args:
            config_filename (str): The filename of the configuration file containing the test details.
            connector (str): The connector to be used for the run test.
        """
        pass
