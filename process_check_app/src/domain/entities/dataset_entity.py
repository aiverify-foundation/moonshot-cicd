from pydantic import BaseModel


class DatasetEntity(BaseModel):
    """
    DatasetEntity represents the structure and metadata of a dataset.

    Attributes:
        id (str): Unique identifier for the dataset.
        name (str): Name of the dataset.
        description (str): Description of the dataset's contents and purpose.
        examples (list): Generator of examples from the dataset, where each example is a dictionary.
        num_of_dataset_prompts (int): The number of dataset prompts, automatically calculated.
        created_date (str): The creation date and time of the dataset in ISO format without 'T'. Automatically generated
        reference (str): An optional string to store a reference link or identifier for the dataset.
        license (str): License information for the dataset. Defaults to an empty string if not provided.
    """

    class Config:
        arbitrary_types_allowed = True

    # Unique identifier for the dataset
    id: str

    # Name of the dataset
    name: str

    # Description of the dataset's contents and purpose
    description: str

    # Generator of examples from the dataset, where each example is a dictionary.
    examples: list

    # The number of dataset prompts, automatically calculated
    num_of_dataset_prompts: int = 0

    # The creation date and time of the dataset in ISO format without 'T'. Automatically generated.
    created_date: str = ""

    # An optional string to store a reference link or identifier for the dataset
    reference: str = ""

    # License information for the dataset. Defaults to an empty string if not provided.
    license: str = ""
