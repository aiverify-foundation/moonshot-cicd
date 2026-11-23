"""Curated allowlists for Bedrock Mantle web search connectors.

Model IDs follow AWS OpenAI-on-Bedrock docs. On ``bedrock-mantle``, use the
``openai.*`` foundation IDs (e.g. ``openai.gpt-5.5``). On ``bedrock-runtime``,
users often paste geo profiles (``us.openai.*`` / ``global.openai.*``).

Refs:
- https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-54.html
- https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-55.html
- https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-6-sol.html
"""

from __future__ import annotations

ALLOWED_REGIONS: frozenset[str] = frozenset(
    {
        "us-east-1",
        "us-east-2",
        "us-west-2",
    }
)

# Mantle IDs (preferred for our bedrock-mantle.{region}.api.aws/v1 client)
_MANTLE_GPT5_TIER = "openai.gpt-5.4"  # GPT-5.x on Bedrock; no bare ``openai.gpt-5`` ID
_MANTLE_GPT55 = "openai.gpt-5.5"
_MANTLE_GPT6 = (
    "openai.gpt-6-sol",
    "openai.gpt-6-luna",
    "openai.gpt-6-astra",
)

# Runtime cross-Region inference profile IDs (same models, different naming)
_RUNTIME_PROFILES = frozenset(
    {
        "us.openai.gpt-5.4",
        "global.openai.gpt-5.4",
        "us.openai.gpt-5.5",
        "global.openai.gpt-5.5",
        "us.openai.gpt-6-sol",
        "global.openai.gpt-6-sol",
        "us.openai.gpt-6-luna",
        "global.openai.gpt-6-luna",
        "us.openai.gpt-6-astra",
        "global.openai.gpt-6-astra",
    }
)

ALLOWED_MODEL_IDS: frozenset[str] = frozenset(
    {
        _MANTLE_GPT5_TIER,
        _MANTLE_GPT55,
        *_MANTLE_GPT6,
        *_RUNTIME_PROFILES,
    }
)


def is_allowed_region(region: str) -> bool:
    return region.strip() in ALLOWED_REGIONS


def is_allowed_model_id(model_id: str) -> bool:
    stripped = model_id.strip()
    if not stripped:
        return False
    if stripped in ALLOWED_MODEL_IDS:
        return True
    # Custom OpenAI-on-Bedrock IDs (Mantle or inference profiles)
    if stripped.startswith("openai.gpt-"):
        return True
    return stripped.startswith("us.openai.") or stripped.startswith("global.openai.")
