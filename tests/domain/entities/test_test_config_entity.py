import pytest
from pydantic import ValidationError

from src.domain.entities.test_config_entity import TestConfigEntity
from domain.services.enums.test_types import TestTypes


class TestTestConfigEntity:
    """Test class for TestConfigEntity"""

    def test_minimal_initialization_benchmark(self):
        """Test TestConfigEntity with minimal required parameters for benchmark"""
        # Arrange
        name = "benchmark_test"
        test_type = TestTypes.BENCHMARK
        metric = {"name": "accuracy", "threshold": 0.8}

        # Act
        entity = TestConfigEntity(
            name=name,
            type=test_type,
            metric=metric
        )

        # Assert
        assert entity.name == name
        assert entity.type == test_type
        assert entity.metric == metric
        assert entity.attack_module is None  # Default value
        assert entity.dataset == ""  # Default value
        assert entity.prompt == ""  # Default value

    def test_minimal_initialization_scan(self):
        """Test TestConfigEntity with minimal required parameters for scan"""
        # Arrange
        name = "scan_test"
        test_type = TestTypes.SCAN
        metric = {"name": "safety_score", "threshold": 0.9}
        attack_module = {"name": "jailbreak", "params": {"iterations": 10}}

        # Act
        entity = TestConfigEntity(
            name=name,
            type=test_type,
            metric=metric,
            attack_module=attack_module
        )

        # Assert
        assert entity.name == name
        assert entity.type == test_type
        assert entity.metric == metric
        assert entity.attack_module == attack_module
        assert entity.dataset == ""  # Default value
        assert entity.prompt == ""  # Default value

    def test_full_initialization(self):
        """Test TestConfigEntity with all parameters provided"""
        # Arrange
        name = "comprehensive_test"
        test_type = TestTypes.SCAN
        attack_module = {"name": "prompt_injection", "params": {"temperature": 0.7, "max_tokens": 100}}
        dataset = "security_dataset"
        metric = {"name": "harmfulness", "threshold": 0.5, "weights": {"toxicity": 0.6, "bias": 0.4}}
        prompt = "Test the model's response to adversarial inputs"

        # Act
        entity = TestConfigEntity(
            name=name,
            type=test_type,
            attack_module=attack_module,
            dataset=dataset,
            metric=metric,
            prompt=prompt
        )

        # Assert
        assert entity.name == name
        assert entity.type == test_type
        assert entity.attack_module == attack_module
        assert entity.dataset == dataset
        assert entity.metric == metric
        assert entity.prompt == prompt

    @pytest.mark.parametrize("name,test_type,attack_module,dataset,metric,prompt,description", [
        # Good case 1: Complete benchmark configuration
        (
            "accuracy_benchmark",
            TestTypes.BENCHMARK,
            None,
            "math_qa_dataset",
            {"name": "accuracy", "threshold": 0.85, "evaluation_method": "exact_match"},
            "",
            "Complete benchmark test configuration"
        ),
        # Good case 2: Complete scan configuration
        (
            "security_scan",
            TestTypes.SCAN,
            {"name": "adversarial_attack", "params": {"iterations": 20, "temperature": 0.8}},
            "security_prompts",
            {"name": "safety_score", "threshold": 0.9, "categories": ["harmful", "biased"]},
            "Evaluate model safety against adversarial prompts",
            "Complete scan test configuration"
        ),
        # Bad case 1: Missing required name field - this should fail
        # Note: We can't actually test missing required fields with parametrize easily
        # as it would cause instantiation to fail before the test runs
        # Bad case 2: Invalid test type - this should fail
        # Note: Similar issue with enum validation
    ])
    def test_valid_configurations(self, name, test_type, attack_module, dataset, metric, prompt, description):
        """Test TestConfigEntity with various valid configurations"""
        # Act
        entity = TestConfigEntity(
            name=name,
            type=test_type,
            attack_module=attack_module,
            dataset=dataset,
            metric=metric,
            prompt=prompt
        )

        # Assert
        assert entity.name == name
        assert entity.type == test_type
        assert entity.attack_module == attack_module
        assert entity.dataset == dataset
        assert entity.metric == metric
        assert entity.prompt == prompt

    @pytest.mark.parametrize("invalid_data,expected_error_type,description", [
        # Bad case 1: Missing required name field
        (
            {
                "type": TestTypes.BENCHMARK,
                "metric": {"name": "accuracy"}
            },
            ValidationError,
            "Missing required name field should raise ValidationError"
        ),
        # Bad case 2: Missing required type field
        (
            {
                "name": "test_config",
                "metric": {"name": "accuracy"}
            },
            ValidationError,
            "Missing required type field should raise ValidationError"
        ),
        # Bad case 3: Missing required metric field
        (
            {
                "name": "test_config",
                "type": TestTypes.BENCHMARK
            },
            ValidationError,
            "Missing required metric field should raise ValidationError"
        ),
        # Bad case 4: Invalid type value
        (
            {
                "name": "test_config",
                "type": "invalid_type",
                "metric": {"name": "accuracy"}
            },
            ValidationError,
            "Invalid type value should raise ValidationError"
        ),
    ])
    def test_invalid_configurations(self, invalid_data, expected_error_type, description):
        """Test TestConfigEntity with invalid configurations"""
        # Act & Assert
        with pytest.raises(expected_error_type):
            TestConfigEntity(**invalid_data)

    @pytest.mark.parametrize("name", [
        # Good cases - various valid name types
        "simple_test",
        "test_with_underscores",
        "TestWithCamelCase",
        "test-with-hyphens",
        "test.with.dots",
        "test123",
        "123test",
        "test with spaces",
        "test_with_unicode_测试",
        "very_long_test_name_" * 10,
    ])
    def test_valid_name_variations(self, name):
        """Test TestConfigEntity with various valid name formats"""
        # Act
        entity = TestConfigEntity(
            name=name,
            type=TestTypes.BENCHMARK,
            metric={"name": "test_metric"}
        )

        # Assert
        assert entity.name == name

    @pytest.mark.parametrize("name,expected_error", [
        # Bad cases - invalid name types
        (123, "Input should be a valid string"),
        ([], "Input should be a valid string"),
        ({}, "Input should be a valid string"),
        (True, "Input should be a valid string"),
        (None, "Input should be a valid string"),
        (3.14, "Input should be a valid string"),
    ])
    def test_invalid_name_types(self, name, expected_error):
        """Test TestConfigEntity with invalid name types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestConfigEntity(
                name=name,
                type=TestTypes.BENCHMARK,
                metric={"name": "test_metric"}
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("test_type", [
        # Good cases - valid TestTypes enum values
        TestTypes.BENCHMARK,
        TestTypes.SCAN,
    ])
    def test_valid_type_variations(self, test_type):
        """Test TestConfigEntity with valid test types"""
        # Act
        entity = TestConfigEntity(
            name="test_config",
            type=test_type,
            metric={"name": "test_metric"}
        )

        # Assert
        assert entity.type == test_type

    @pytest.mark.parametrize("test_type,expected_error", [
        # Bad cases - invalid test types
        ("invalid_type", "Input should be 'benchmark' or 'scan'"),
        (123, "Input should be 'benchmark' or 'scan'"),
        ([], "Input should be 'benchmark' or 'scan'"),
        ({}, "Input should be 'benchmark' or 'scan'"),
        (True, "Input should be 'benchmark' or 'scan'"),
        (None, "Input should be 'benchmark' or 'scan'"),
    ])
    def test_invalid_type_values(self, test_type, expected_error):
        """Test TestConfigEntity with invalid test types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestConfigEntity(
                name="test_config",
                type=test_type,
                metric={"name": "test_metric"}
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("attack_module", [
        # Good cases - various valid attack_module formats
        None,  # Default value
        {"name": "simple_attack"},
        {"name": "complex_attack", "params": {"temperature": 0.7}},
        {"name": "advanced_attack", "params": {"iterations": 10, "threshold": 0.5, "strategies": ["A", "B"]}},
        {"name": "nested_attack", "params": {"config": {"nested": {"value": 42}}}},
        {"name": "unicode_attack_攻击", "params": {"参数": "值"}},
    ])
    def test_valid_attack_module_variations(self, attack_module):
        """Test TestConfigEntity with various valid attack_module formats"""
        # Act
        entity = TestConfigEntity(
            name="test_config",
            type=TestTypes.SCAN,
            metric={"name": "test_metric"},
            attack_module=attack_module
        )

        # Assert
        assert entity.attack_module == attack_module

    @pytest.mark.parametrize("attack_module,expected_error", [
        # Bad cases - invalid attack_module types
        ("string", "Input should be a valid dictionary"),
        (123, "Input should be a valid dictionary"),
        ([], "Input should be a valid dictionary"),
        (True, "Input should be a valid dictionary"),
        (3.14, "Input should be a valid dictionary"),
    ])
    def test_invalid_attack_module_types(self, attack_module, expected_error):
        """Test TestConfigEntity with invalid attack_module types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestConfigEntity(
                name="test_config",
                type=TestTypes.SCAN,
                metric={"name": "test_metric"},
                attack_module=attack_module
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("dataset", [
        # Good cases - various valid dataset formats
        "",  # Default value
        "simple_dataset",
        "dataset_with_underscores",
        "DatasetWithCamelCase",
        "dataset-with-hyphens",
        "dataset.with.dots",
        "dataset123",
        "123dataset",
        "dataset with spaces",
        "unicode_dataset_数据集",
        "path/to/dataset.json",
        "very_long_dataset_name_" * 10,
    ])
    def test_valid_dataset_variations(self, dataset):
        """Test TestConfigEntity with various valid dataset formats"""
        # Act
        entity = TestConfigEntity(
            name="test_config",
            type=TestTypes.BENCHMARK,
            metric={"name": "test_metric"},
            dataset=dataset
        )

        # Assert
        assert entity.dataset == dataset

    @pytest.mark.parametrize("dataset,expected_error", [
        # Bad cases - invalid dataset types
        (123, "Input should be a valid string"),
        ([], "Input should be a valid string"),
        ({}, "Input should be a valid string"),
        (True, "Input should be a valid string"),
        (None, "Input should be a valid string"),
        (3.14, "Input should be a valid string"),
    ])
    def test_invalid_dataset_types(self, dataset, expected_error):
        """Test TestConfigEntity with invalid dataset types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestConfigEntity(
                name="test_config",
                type=TestTypes.BENCHMARK,
                metric={"name": "test_metric"},
                dataset=dataset
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("metric", [
        # Good cases - various valid metric formats
        {"name": "simple_metric"},
        {"name": "accuracy", "threshold": 0.8},
        {"name": "complex_metric", "threshold": 0.9, "weights": {"precision": 0.5, "recall": 0.5}},
        {"name": "nested_metric", "config": {"nested": {"parameters": {"value": 42}}}},
        {"name": "unicode_metric_你好世界", "描述": "你好世界"},
        {"name": "comprehensive_metric", "threshold": 0.85, "categories": ["A", "B"], "weights": [0.6, 0.4]},
    ])
    def test_valid_metric_variations(self, metric):
        """Test TestConfigEntity with various valid metric formats"""
        # Act
        entity = TestConfigEntity(
            name="test_config",
            type=TestTypes.BENCHMARK,
            metric=metric
        )

        # Assert
        assert entity.metric == metric

    @pytest.mark.parametrize("metric,expected_error", [
        # Bad cases - invalid metric types
        ("string", "Input should be a valid dictionary"),
        (123, "Input should be a valid dictionary"),
        ([], "Input should be a valid dictionary"),
        (True, "Input should be a valid dictionary"),
        (None, "Input should be a valid dictionary"),
        (3.14, "Input should be a valid dictionary"),
    ])
    def test_invalid_metric_types(self, metric, expected_error):
        """Test TestConfigEntity with invalid metric types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestConfigEntity(
                name="test_config",
                type=TestTypes.BENCHMARK,
                metric=metric
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("prompt", [
        # Good cases - various valid prompt formats
        "",  # Default value
        "Simple prompt",
        "Multi-line\nprompt\nwith\nbreaks",
        "Prompt with special chars: !@#$%^&*()",
        "Unicode prompt: 你好世界",
        "Very long prompt " * 100,
        "JSON-like prompt: {\"instruction\": \"test\", \"context\": \"evaluation\"}",
        "Template prompt: Please evaluate the following based on criteria:\n1. Accuracy\n2. Relevance",
        "Prompt with citations: According to research (Smith, 2023), AI systems should...",
    ])
    def test_valid_prompt_variations(self, prompt):
        """Test TestConfigEntity with various valid prompt formats"""
        # Act
        entity = TestConfigEntity(
            name="test_config",
            type=TestTypes.SCAN,
            metric={"name": "test_metric"},
            prompt=prompt
        )

        # Assert
        assert entity.prompt == prompt

    @pytest.mark.parametrize("prompt,expected_error", [
        # Bad cases - invalid prompt types
        (123, "Input should be a valid string"),
        ([], "Input should be a valid string"),
        ({}, "Input should be a valid string"),
        (True, "Input should be a valid string"),
        (None, "Input should be a valid string"),
        (3.14, "Input should be a valid string"),
    ])
    def test_invalid_prompt_types(self, prompt, expected_error):
        """Test TestConfigEntity with invalid prompt types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TestConfigEntity(
                name="test_config",
                type=TestTypes.SCAN,
                metric={"name": "test_metric"},
                prompt=prompt
            )
        assert expected_error in str(exc_info.value)

    def test_entity_serialization(self):
        """Test TestConfigEntity serialization to dictionary"""
        # Arrange
        entity = TestConfigEntity(
            name="serialization_test",
            type=TestTypes.SCAN,
            attack_module={"name": "test_attack", "params": {"iterations": 5}},
            dataset="test_dataset",
            metric={"name": "test_metric", "threshold": 0.8},
            prompt="Test prompt for serialization"
        )

        # Act
        serialized = entity.model_dump()

        # Assert
        expected = {
            "name": "serialization_test",
            "type": TestTypes.SCAN,
            "attack_module": {"name": "test_attack", "params": {"iterations": 5}},
            "dataset": "test_dataset",
            "metric": {"name": "test_metric", "threshold": 0.8},
            "prompt": "Test prompt for serialization"
        }
        assert serialized == expected

    def test_entity_json_serialization(self):
        """Test TestConfigEntity JSON serialization"""
        # Arrange
        entity = TestConfigEntity(
            name="json_test",
            type=TestTypes.BENCHMARK,
            dataset="json_dataset",
            metric={"name": "json_metric", "threshold": 0.9}
        )

        # Act
        json_str = entity.model_dump_json()

        # Assert
        assert isinstance(json_str, str)
        assert "json_test" in json_str
        assert "benchmark" in json_str
        assert "json_dataset" in json_str
        assert "json_metric" in json_str

    def test_entity_from_dict(self):
        """Test TestConfigEntity creation from dictionary"""
        # Arrange
        data = {
            "name": "from_dict_test",
            "type": "scan",
            "attack_module": {"name": "dict_attack", "params": {"param1": "value1"}},
            "dataset": "dict_dataset",
            "metric": {"name": "dict_metric", "threshold": 0.75},
            "prompt": "Test prompt from dict"
        }

        # Act
        entity = TestConfigEntity(**data)

        # Assert
        assert entity.name == "from_dict_test"
        assert entity.type == TestTypes.SCAN
        assert entity.attack_module == {"name": "dict_attack", "params": {"param1": "value1"}}
        assert entity.dataset == "dict_dataset"
        assert entity.metric == {"name": "dict_metric", "threshold": 0.75}
        assert entity.prompt == "Test prompt from dict"

    def test_inheritance_from_basemodel(self):
        """Test that TestConfigEntity inherits from BaseModel"""
        # Arrange & Act
        entity = TestConfigEntity(
            name="inheritance_test",
            type=TestTypes.BENCHMARK,
            metric={"name": "test_metric"}
        )

        # Assert
        from pydantic import BaseModel
        assert isinstance(entity, BaseModel)

    def test_arbitrary_types_allowed_config(self):
        """Test that arbitrary_types_allowed is configured"""
        # Act
        config = TestConfigEntity.model_config

        # Assert
        assert config.get('arbitrary_types_allowed') is True

    @pytest.mark.parametrize("field_name,new_value", [
        ("name", "updated_name"),
        ("type", TestTypes.SCAN),
        ("attack_module", {"name": "updated_attack", "params": {"new_param": "new_value"}}),
        ("dataset", "updated_dataset"),
        ("metric", {"name": "updated_metric", "threshold": 0.95}),
        ("prompt", "Updated prompt text"),
    ])
    def test_field_assignment_after_initialization(self, field_name, new_value):
        """Test field assignment after entity initialization"""
        # Arrange
        entity = TestConfigEntity(
            name="original_name",
            type=TestTypes.BENCHMARK,
            metric={"name": "original_metric"}
        )

        # Act
        setattr(entity, field_name, new_value)

        # Assert
        assert getattr(entity, field_name) == new_value

    def test_real_world_benchmark_scenario(self):
        """Test TestConfigEntity with realistic benchmark scenario"""
        # Arrange & Act
        entity = TestConfigEntity(
            name="math_qa_evaluation",
            type=TestTypes.BENCHMARK,
            dataset="grade_school_math",
            metric={
                "name": "accuracy",
                "threshold": 0.85,
                "evaluation_method": "exact_match",
                "case_sensitive": False
            }
        )

        # Assert
        assert entity.name == "math_qa_evaluation"
        assert entity.type == TestTypes.BENCHMARK
        assert entity.dataset == "grade_school_math"
        assert entity.metric["name"] == "accuracy"
        assert entity.metric["threshold"] == 0.85
        assert entity.attack_module is None
        assert entity.prompt == ""

    def test_real_world_scan_scenario(self):
        """Test TestConfigEntity with realistic scan scenario"""
        # Arrange & Act
        entity = TestConfigEntity(
            name="jailbreak_safety_test",
            type=TestTypes.SCAN,
            attack_module={
                "name": "jailbreak_attack",
                "params": {
                    "iterations": 50,
                    "temperature": 0.8,
                    "strategies": ["role_play", "hypothetical", "prefix_injection"]
                }
            },
            dataset="safety_prompts",
            metric={
                "name": "harmfulness_score",
                "threshold": 0.1,
                "categories": ["violence", "hate_speech", "self_harm", "illegal_activity"]
            },
            prompt="Test the model's resistance to jailbreak attempts"
        )

        # Assert
        assert entity.name == "jailbreak_safety_test"
        assert entity.type == TestTypes.SCAN
        assert entity.attack_module["name"] == "jailbreak_attack"
        assert entity.attack_module["params"]["iterations"] == 50
        assert entity.dataset == "safety_prompts"
        assert entity.metric["name"] == "harmfulness_score"
        assert entity.prompt == "Test the model's resistance to jailbreak attempts"

    def test_default_values(self):
        """Test TestConfigEntity default values"""
        # Arrange & Act
        entity = TestConfigEntity(
            name="defaults_test",
            type=TestTypes.BENCHMARK,
            metric={"name": "test_metric"}
        )

        # Assert
        assert entity.attack_module is None
        assert entity.dataset == ""
        assert entity.prompt == ""

    def test_empty_and_none_values(self):
        """Test TestConfigEntity with empty and None values where allowed"""
        # Arrange & Act
        entity = TestConfigEntity(
            name="empty_test",
            type=TestTypes.SCAN,
            attack_module=None,
            dataset="",
            metric={"name": "empty_metric"},
            prompt=""
        )

        # Assert
        assert entity.name == "empty_test"
        assert entity.type == TestTypes.SCAN
        assert entity.attack_module is None
        assert entity.dataset == ""
        assert entity.metric == {"name": "empty_metric"}
        assert entity.prompt == ""

    @pytest.mark.parametrize("name,test_type,attack_module,dataset,metric,prompt,description", [
        # Edge case 1: Minimal benchmark
        (
            "min_benchmark",
            TestTypes.BENCHMARK,
            None,
            "",
            {"name": "min_metric"},
            "",
            "Minimal benchmark configuration"
        ),
        # Edge case 2: Maximal scan
        (
            "max_scan_" * 20,  # Long name
            TestTypes.SCAN,
            {
                "name": "complex_attack_module",
                "params": {
                    "iterations": 1000,
                    "temperature": 0.95,
                    "strategies": ["strategy_" + str(i) for i in range(20)],
                    "nested_config": {
                        "deep": {"deeper": {"deepest": "value"}}
                    }
                }
            },
            "very_large_dataset_name_" * 10,
            {
                "name": "comprehensive_metric",
                "threshold": 0.001,
                "weights": {f"category_{i}": 1.0/50 for i in range(50)},
                "evaluation_methods": ["method_" + str(i) for i in range(10)]
            },
            "Very long prompt text " * 100,
            "Maximal scan configuration with large data structures"
        ),
    ])
    def test_edge_case_combinations(self, name, test_type, attack_module, dataset, metric, prompt, description):
        """Test TestConfigEntity with edge case combinations"""
        # Act
        entity = TestConfigEntity(
            name=name,
            type=test_type,
            attack_module=attack_module,
            dataset=dataset,
            metric=metric,
            prompt=prompt
        )

        # Assert
        assert entity.name == name
        assert entity.type == test_type
        assert entity.attack_module == attack_module
        assert entity.dataset == dataset
        assert entity.metric == metric
        assert entity.prompt == prompt 