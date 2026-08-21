"""DTOs for registering an LLM provider API key (write-only; no secret in responses)."""

from pydantic import BaseModel, Field


class SetLlmProviderApiKeyRequestDTO(BaseModel):
    """Request body for POST /api/providers/{provider_id}/api-key."""

    api_key: str = Field(..., min_length=1)


class SetLlmProviderApiKeyResponseDTO(BaseModel):
    """Success response; never includes the API key or ciphertext."""

    message: str
