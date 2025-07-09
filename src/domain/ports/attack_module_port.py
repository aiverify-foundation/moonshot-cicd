from abc import abstractmethod
from typing import Any

from domain.entities.attack_module_entity import AttackModuleEntity


class AttackModulePort:

    @abstractmethod
    def configure(
        self, attack_module_id: str, attack_module_entity: AttackModuleEntity
    ) -> None:
        """
        Configure the attack module with the given attack module ID and the AttackModuleEntity instance.

        Args:
            attack_module_id (str): The attack module ID.
            attack_module_entity (AttackModuleEntity): The attack module entity containing configuration details.
        """

    pass

    @abstractmethod
    def update_params(self, params: dict) -> None:
        """
        Update the parameters of the attack module.

        This method should be implemented to update the internal parameters
        of the attack module with the provided dictionary. The keys and values
        in the dictionary should correspond to the specific parameters that
        need to be updated.

        Args:
            params (dict): A dictionary containing parameter names as keys
                           and their new values as values.
        """
        pass

    @abstractmethod
    def execute(self) -> Any:
        """
        Execute the logic of the attack. This method serves as the entry point for the attack module.
        * Do not change the name of this function in the attack module.

        Returns:
            Any: The result of the attack execution.
        """
        pass
