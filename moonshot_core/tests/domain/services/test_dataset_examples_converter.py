"""Unit tests for dataset_examples_converter (prompt <-> input, target <-> target)."""

import pytest

from domain.entities.benchmark_test_dataset_entity import BenchmarkTestDatasetEntity
from domain.entities.benchmark_test_dataset_prompt_entity import (
    BenchmarkTestDatasetPromptEntity,
)
from domain.services.dataset_examples_converter import (
    benchmark_entity_to_examples_dict,
    examples_dict_to_benchmark_entity,
    examples_to_prompts,
    prompts_to_examples,
)


class TestExamplesToPrompts:
    """Tests for examples_to_prompts (dict -> prompt entities)."""

    def test_empty_list(self):
        assert examples_to_prompts([]) == []
        assert examples_to_prompts(None) == []

    def test_one_item(self):
        data = [{"input": "q1", "target": "a1"}]
        result = examples_to_prompts(data)
        assert len(result) == 1
        assert result[0].prompt == "q1"
        assert result[0].target == "a1"
        assert result[0].id is None
        assert result[0].benchmark_test_dataset_id is None

    def test_many_items(self):
        data = [
            {"input": "q1", "target": "a1"},
            {"input": "q2", "target": "a2"},
        ]
        result = examples_to_prompts(data)
        assert len(result) == 2
        assert result[0].prompt == "q1" and result[0].target == "a1"
        assert result[1].prompt == "q2" and result[1].target == "a2"

    def test_output_fallback_for_target(self):
        data = [{"input": "q", "output": "a"}]
        result = examples_to_prompts(data)
        assert len(result) == 1
        assert result[0].prompt == "q"
        assert result[0].target == "a"

    def test_missing_keys_default_empty(self):
        data = [{}]
        result = examples_to_prompts(data)
        assert len(result) == 1
        assert result[0].prompt == ""
        assert result[0].target == ""


class TestPromptsToExamples:
    """Tests for prompts_to_examples (prompt entities -> dict)."""

    def test_empty_list(self):
        assert prompts_to_examples([]) == []
        assert prompts_to_examples(None) == []

    def test_one_item(self):
        prompts = [BenchmarkTestDatasetPromptEntity(prompt="q1", target="a1")]
        result = prompts_to_examples(prompts)
        assert result == [{"input": "q1", "target": "a1"}]

    def test_many_items(self):
        prompts = [
            BenchmarkTestDatasetPromptEntity(prompt="q1", target="a1"),
            BenchmarkTestDatasetPromptEntity(prompt="q2", target="a2"),
        ]
        result = prompts_to_examples(prompts)
        assert result == [
            {"input": "q1", "target": "a1"},
            {"input": "q2", "target": "a2"},
        ]


class TestRoundTrip:
    """Round-trip: prompts_to_examples(examples_to_prompts(data)) == data for input/target dicts."""

    def test_round_trip_single(self):
        data = [{"input": "q", "target": "a"}]
        assert prompts_to_examples(examples_to_prompts(data)) == data

    def test_round_trip_multiple(self):
        data = [
            {"input": "q1", "target": "a1"},
            {"input": "q2", "target": "a2"},
        ]
        assert prompts_to_examples(examples_to_prompts(data)) == data


class TestFullDatasetConversion:
    """Tests for examples_dict_to_benchmark_entity and benchmark_entity_to_examples_dict."""

    def test_examples_dict_to_benchmark_entity(self):
        examples = [{"input": "q1", "target": "a1"}]
        entity = examples_dict_to_benchmark_entity("my_dataset", examples, version=2)
        assert entity.system_name == "my_dataset"
        assert entity.version == 2
        assert len(entity.prompts) == 1
        assert entity.prompts[0].prompt == "q1" and entity.prompts[0].target == "a1"

    def test_benchmark_entity_to_examples_dict(self):
        entity = BenchmarkTestDatasetEntity(
            version=1,
            system_name="x",
            prompts=[
                BenchmarkTestDatasetPromptEntity(prompt="q", target="a"),
            ],
        )
        assert benchmark_entity_to_examples_dict(entity) == [{"input": "q", "target": "a"}]
