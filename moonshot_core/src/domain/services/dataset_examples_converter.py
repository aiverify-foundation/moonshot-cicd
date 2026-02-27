"""
Central conversion between examples-dictionary format and BenchmarkTestDatasetEntity.

Mapping rule:
  - prompt (entity) <-> "input" (dict)
  - target (entity) <-> "target" (dict)

Examples dict format: [{"input": str, "target": str}, ...]
Used in JSON files, DatasetEntity.examples, and DTOs.
"""

from typing import Any

from domain.entities.benchmark_test_dataset_entity import BenchmarkTestDatasetEntity
from domain.entities.benchmark_test_dataset_prompt_entity import (
    BenchmarkTestDatasetPromptEntity,
)


def examples_to_prompts(
    examples: list[dict[str, Any]],
) -> list[BenchmarkTestDatasetPromptEntity]:
    """
    Convert examples dict list to list of BenchmarkTestDatasetPromptEntity.

    Mapping: d["input"] -> prompt, d["target"] -> target.
    Supports d["output"] as fallback for target if "target" is missing.
    id and benchmark_test_dataset_id are left None.
    None values are coerced to ""; other types are coerced to str.
    """
    result: list[BenchmarkTestDatasetPromptEntity] = []
    for d in examples or []:
        raw_prompt = d.get("input", "")
        raw_target = d.get("target", "") or d.get("output", "")
        prompt = "" if raw_prompt is None else str(raw_prompt)
        target = "" if raw_target is None else str(raw_target)
        result.append(
            BenchmarkTestDatasetPromptEntity(
                prompt=prompt,
                target=target,
            )
        )
    return result


def prompts_to_examples(
    prompts: list[BenchmarkTestDatasetPromptEntity],
) -> list[dict[str, str]]:
    """
    Convert list of BenchmarkTestDatasetPromptEntity to examples dict list.

    Mapping: p.prompt -> "input", p.target -> "target".
    """
    return [{"input": p.prompt, "target": p.target} for p in prompts or []]


def examples_dict_to_benchmark_entity(
    system_name: str,
    examples: list[dict[str, Any]],
    *,
    version: int = 1,
    description: str | None = None,
    license: str | None = None,
    reference: str | None = None,
) -> BenchmarkTestDatasetEntity:
    """
    Build BenchmarkTestDatasetEntity from system_name and examples dict list.

    Uses examples_to_prompts for the prompts field.
    """
    prompts = examples_to_prompts(examples)
    return BenchmarkTestDatasetEntity(
        version=version,
        system_name=system_name,
        description=description,
        license=license,
        reference=reference,
        prompts=prompts,
    )


def benchmark_entity_to_examples_dict(entity: BenchmarkTestDatasetEntity) -> list[dict[str, str]]:
    """
    Convert BenchmarkTestDatasetEntity to examples dict list.

    Returns prompts_to_examples(entity.prompts).
    """
    return prompts_to_examples(entity.prompts)
