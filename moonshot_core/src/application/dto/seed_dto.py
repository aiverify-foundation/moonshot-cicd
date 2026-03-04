from pydantic import BaseModel, ConfigDict


class SeedSharedConfigResponseDTO(BaseModel):
    """
    Response DTO for the seed-shared-config-if-changed API.

    Attributes:
        seeded: True if seeding was performed, False if skipped (file unchanged or not found).
        message: Short description of the result.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    seeded: bool
    message: str
