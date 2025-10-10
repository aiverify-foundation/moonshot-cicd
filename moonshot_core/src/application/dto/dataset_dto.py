from pydantic import BaseModel


class DatasetDTO(BaseModel):
    """
    DatasetDTO represents the data transfer object for dataset information.
    
    This DTO contains only the essential data fields for transferring dataset
    information between different layers of the application, without complex
    logic or generators.

    Attributes:
        id (str): Unique identifier for the dataset.
        name (str): Name of the dataset.
        description (str): Description of the dataset's contents and purpose.
        examples (list): List of examples from the dataset, where each example is a dictionary.
        num_of_dataset_prompts (int): The number of dataset prompts.
        created_date (str): The creation date and time of the dataset in ISO format without 'T'.
        reference (str): An optional string to store a reference link or identifier for the dataset.
        license (str): License information for the dataset.
    """

    class Config:
        arbitrary_types_allowed = True

    # Unique identifier for the dataset
    id: str

    # Name of the dataset
    name: str

    # Description of the dataset's contents and purpose
    description: str

    # List of examples from the dataset, where each example is a dictionary.
    examples: list

    # The number of dataset prompts
    num_of_dataset_prompts: int = 0

    # The creation date and time of the dataset in ISO format without 'T'.
    created_date: str = ""

    # An optional string to store a reference link or identifier for the dataset
    reference: str = ""

    # License information for the dataset. Defaults to an empty string if not provided.
    license: str = ""

