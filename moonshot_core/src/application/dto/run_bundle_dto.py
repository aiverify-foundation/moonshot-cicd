from pydantic import BaseModel


class RunBundleRequestDTO(BaseModel):
    """
    RunBundleRequestDTO represents the data transfer object for bundle execution request.
    
    This DTO contains only the essential data fields for transferring bundle execution
    request information between different layers of the application, without complex logic.

    Attributes:
        bundle_name (str): The name of the bundle to execute.
        connector (str): The connector identifier to use for the bundle.
    """

    class Config:
        arbitrary_types_allowed = True

    # The name of the bundle to execute
    bundle_name: str

    # The connector identifier to use for the bundle
    connector: str


class RunBundleResponseDTO(BaseModel):
    """
    RunBundleResponseDTO represents the data transfer object for bundle execution response.
    
    This DTO contains only the essential data fields for transferring bundle execution
    response information between different layers of the application, without complex logic.

    Attributes:
        bundle_name (str): The name of the bundle that was executed.
        message (str): A message describing the result of the bundle execution.
    """

    class Config:
        arbitrary_types_allowed = True

    # The name of the bundle that was executed
    bundle_name: str

    # A message describing the result of the bundle execution
    message: str
