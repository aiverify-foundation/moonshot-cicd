"""DTO for the structured error returned when a metric or connector adapter file is missing."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from domain.services.benchmark_extensions import AdapterNotFoundError

ADAPTER_NOT_FOUND_CODE = "adapter_not_found"

# Upper bound for walking an exception chain, so a cyclic chain cannot loop forever.
_MAX_CAUSE_DEPTH = 10


class AdapterNotFoundDetailDTO(BaseModel):
    """
    HTTP ``detail`` for a request that needs an adapter that is no longer on the server.

    It carries no file paths. The full message, with paths, stays in the server log.
    """

    code: Literal["adapter_not_found"] = Field(
        default=ADAPTER_NOT_FOUND_CODE, description="Machine-readable error code"
    )
    message: str = Field(..., description="Short message safe to show to a user")
    adapter_type: str = Field(..., description="Adapter kind, e.g. metric or connector")
    adapter_name: str = Field(..., description="Adapter module name")


def find_adapter_not_found(exc: BaseException) -> Optional[AdapterNotFoundError]:
    """Return *exc*, or the first ``AdapterNotFoundError`` in its ``__cause__`` chain."""
    current: Optional[BaseException] = exc
    for _ in range(_MAX_CAUSE_DEPTH):
        if current is None:
            return None
        if isinstance(current, AdapterNotFoundError):
            return current
        current = current.__cause__
    return None


def adapter_not_found_detail(exc: BaseException) -> Optional[dict[str, Any]]:
    """
    Return the structured HTTP ``detail`` when *exc* was caused by a missing adapter file.

    Returns ``None`` for any other error, so callers can fall back to ``str(exc)``.
    """
    error = find_adapter_not_found(exc)
    if error is None:
        return None
    adapter_type = error.module_type.name.lower() if error.module_type else "unknown"
    adapter_name = error.adapter_name or "unknown"
    return AdapterNotFoundDetailDTO(
        message=f"The {adapter_type} adapter '{adapter_name}' is not available on the server.",
        adapter_type=adapter_type,
        adapter_name=adapter_name,
    ).model_dump()
