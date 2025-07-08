import pytest
from typing import Callable
from unittest.mock import MagicMock
from pydantic import ValidationError

from domain.entities.attack_module_entity import AttackModuleEntity


class TestAttackModuleEntity:
    """Test class for AttackModuleEntity"""

    def test_minimal_initialization(self):
        """Test AttackModuleEntity with minimal required parameters"""
        # Arrange
        connector = "openai_adapter"
        metric = {"name": "accuracy", "threshold": 0.8}
        prompt_processor = "asyncio_prompt_processor_adapter"

        # Act
        entity = AttackModuleEntity(
            connector=connector,
            metric=metric,
            prompt_processor=prompt_processor
        )

        # Assert
        assert entity.connector == connector
        assert entity.metric == metric
        assert entity.prompt_processor == prompt_processor
        assert entity.prompt == ""  # Default value
        assert entity.dataset == ""  # Default value
        assert entity.callback_fn is None  # Default value

    def test_full_initialization(self):
        """Test AttackModuleEntity with all parameters provided"""
        # Arrange
        connector = "openai_adapter"
        metric = {"name": "refusal", "threshold": 0.9, "params": {"strict": True}}
        prompt = "Test prompt for attack module"
        dataset = "test_dataset.json"
        prompt_processor = "custom_prompt_processor"
        callback_fn = MagicMock()

        # Act
        entity = AttackModuleEntity(
            connector=connector,
            metric=metric,
            prompt=prompt,
            dataset=dataset,
            prompt_processor=prompt_processor,
            callback_fn=callback_fn
        )

        # Assert
        assert entity.connector == connector
        assert entity.metric == metric
        assert entity.prompt == prompt
        assert entity.dataset == dataset
        assert entity.prompt_processor == prompt_processor
        assert entity.callback_fn == callback_fn

    @pytest.mark.parametrize("connector,metric,prompt_processor", [
        # Good cases - various valid combinations
        ("openai_adapter", {"name": "accuracy_adapter"}, "asyncio_prompt_processor_adapter"),
        ("azure_adapter", {"name": "accuracy_adapter", "threshold": 0.85}, "asyncio_prompt_processor_adapter"),
        ("custom_adapter", {"name": "custom_adapter", "config": {"nested": "value"}}, "asyncio_prompt_processor_adapter"),
        ("bedrock_adapter", {"name": "refusal", "params": {"hello": "world"}}, "asyncio_prompt_processor_adapter"),
    ])
    def test_initialization_with_valid_parameters(self, connector, metric, prompt_processor):
        """Test AttackModuleEntity initialization with various valid parameter combinations"""
        # Act
        entity = AttackModuleEntity(
            connector=connector,
            metric=metric,
            prompt_processor=prompt_processor
        )

        # Assert
        assert entity.connector == connector
        assert entity.metric == metric
        assert entity.prompt_processor == prompt_processor

    @pytest.mark.parametrize("prompt,dataset", [
        # Good cases - various string values
        ("Simple test prompt", "dataset1.csv"),
        ("", ""),  # Empty strings are valid
        ("Multi-line\nprompt\nwith\nbreaks", "path/to/dataset.json"),
        ("Prompt with special chars: !@#$%^&*()", "dataset_with_underscores.txt"),
        ("Unicode prompt: 你好世界", "unicode_dataset_测试.json"),
    ])
    def test_optional_string_fields(self, prompt, dataset):
        """Test AttackModuleEntity with various optional string field values"""
        # Act
        entity = AttackModuleEntity(
            connector="test_connector",
            metric={"name": "test"},
            prompt=prompt,
            dataset=dataset,
            prompt_processor="test_processor"
        )

        # Assert
        assert entity.prompt == prompt
        assert entity.dataset == dataset

    @pytest.mark.parametrize("metric", [
        # Good cases - various metric dictionary structures
        {"name": "accuracy"},
        {"name": "f1_score", "threshold": 0.8},
        {"name": "custom", "params": {"key": "value"}},
        {"type": "complex", "config": {"nested": {"deep": {"value": 123}}}},
        {"name": "multi_param", "threshold": 0.9, "params": {"a": 1, "b": 2}, "flags": ["flag1", "flag2"]},
    ])
    def test_metric_field_variations(self, metric):
        """Test AttackModuleEntity with various metric dictionary structures"""
        # Act
        entity = AttackModuleEntity(
            connector="test_connector",
            metric=metric,
            prompt_processor="test_processor"
        )

        # Assert
        assert entity.metric == metric

    def test_callback_function_assignment(self):
        """Test AttackModuleEntity with callback function"""
        # Arrange
        def test_callback(result):
            return f"Processed: {result}"

        mock_callback = MagicMock(side_effect=test_callback)

        # Act
        entity = AttackModuleEntity(
            connector="test_connector",
            metric={"name": "test"},
            prompt_processor="test_processor",
            callback_fn=mock_callback
        )

        # Assert
        assert entity.callback_fn == mock_callback
        assert callable(entity.callback_fn)

        # Test callback execution
        result = entity.callback_fn("test_result")
        mock_callback.assert_called_once_with("test_result")
        assert result == "Processed: test_result"

    def test_lambda_callback_function(self):
        """Test AttackModuleEntity with lambda callback function"""
        # Arrange
        lambda_callback = lambda x: x.upper()

        # Act
        entity = AttackModuleEntity(
            connector="test_connector",
            metric={"name": "test"},
            prompt_processor="test_processor",
            callback_fn=lambda_callback
        )

        # Assert
        assert entity.callback_fn == lambda_callback
        assert entity.callback_fn("test") == "TEST"

    @pytest.mark.parametrize("connector,expected_error", [
        # Bad cases - invalid connector types
        (None, "Input should be a valid string"),
        (123, "Input should be a valid string"),
        ([], "Input should be a valid string"),
        ({}, "Input should be a valid string"),
        (True, "Input should be a valid string"),
    ])
    def test_invalid_connector_types(self, connector, expected_error):
        """Test AttackModuleEntity with invalid connector types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AttackModuleEntity(
                connector=connector,
                metric={"name": "test"},
                prompt_processor="test_processor"
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("metric,expected_error", [
        # Bad cases - invalid metric types
        (None, "Input should be a valid dictionary"),
        ("string", "Input should be a valid dictionary"),
        (123, "Input should be a valid dictionary"),
        ([], "Input should be a valid dictionary"),
        (True, "Input should be a valid dictionary"),
    ])
    def test_invalid_metric_types(self, metric, expected_error):
        """Test AttackModuleEntity with invalid metric types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AttackModuleEntity(
                connector="test_connector",
                metric=metric,
                prompt_processor="test_processor"
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("prompt_processor,expected_error", [
        # Bad cases - invalid prompt_processor types
        (None, "Input should be a valid string"),
        (123, "Input should be a valid string"),
        ([], "Input should be a valid string"),
        ({}, "Input should be a valid string"),
        (True, "Input should be a valid string"),
    ])
    def test_invalid_prompt_processor_types(self, prompt_processor, expected_error):
        """Test AttackModuleEntity with invalid prompt_processor types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AttackModuleEntity(
                connector="test_connector",
                metric={"name": "test"},
                prompt_processor=prompt_processor
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("prompt,expected_error", [
        # Bad cases - invalid prompt types
        (123, "Input should be a valid string"),
        ([], "Input should be a valid string"),
        ({}, "Input should be a valid string"),
        (True, "Input should be a valid string"),
    ])
    def test_invalid_prompt_types(self, prompt, expected_error):
        """Test AttackModuleEntity with invalid prompt types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AttackModuleEntity(
                connector="test_connector",
                metric={"name": "test"},
                prompt=prompt,
                prompt_processor="test_processor"
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("dataset,expected_error", [
        # Bad cases - invalid dataset types
        (123, "Input should be a valid string"),
        ([], "Input should be a valid string"),
        ({}, "Input should be a valid string"),
        (True, "Input should be a valid string"),
    ])
    def test_invalid_dataset_types(self, dataset, expected_error):
        """Test AttackModuleEntity with invalid dataset types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AttackModuleEntity(
                connector="test_connector",
                metric={"name": "test"},
                dataset=dataset,
                prompt_processor="test_processor"
            )
        assert expected_error in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test AttackModuleEntity with missing required fields"""
        # Test missing connector
        with pytest.raises(ValidationError) as exc_info:
            AttackModuleEntity(
                metric={"name": "test"},
                prompt_processor="test_processor"
            )
        assert "Field required" in str(exc_info.value)

        # Test missing metric
        with pytest.raises(ValidationError) as exc_info:
            AttackModuleEntity(
                connector="test_connector",
                prompt_processor="test_processor"
            )
        assert "Field required" in str(exc_info.value)

        # Test missing prompt_processor
        with pytest.raises(ValidationError) as exc_info:
            AttackModuleEntity(
                connector="test_connector",
                metric={"name": "test"}
            )
        assert "Field required" in str(exc_info.value)

    def test_entity_serialization(self):
        """Test AttackModuleEntity serialization to dictionary"""
        # Arrange
        entity = AttackModuleEntity(
            connector="test_connector",
            metric={"name": "accuracy", "threshold": 0.8},
            prompt="Test prompt",
            dataset="test_dataset.json",
            prompt_processor="test_processor"
        )

        # Act
        entity_dict = entity.model_dump()

        # Assert
        expected_keys = ["connector", "metric", "prompt", "dataset", "prompt_processor", "callback_fn"]
        assert all(key in entity_dict for key in expected_keys)
        assert entity_dict["connector"] == "test_connector"
        assert entity_dict["metric"] == {"name": "accuracy", "threshold": 0.8}
        assert entity_dict["prompt"] == "Test prompt"
        assert entity_dict["dataset"] == "test_dataset.json"
        assert entity_dict["prompt_processor"] == "test_processor"
        assert entity_dict["callback_fn"] is None

    def test_entity_json_serialization(self):
        """Test AttackModuleEntity JSON serialization"""
        # Arrange
        entity = AttackModuleEntity(
            connector="json_test_connector",
            metric={"name": "json_test", "params": {"nested": {"value": 42}}},
            prompt="JSON test prompt",
            dataset="json_test.json",
            prompt_processor="json_processor"
        )

        # Act
        json_str = entity.model_dump_json()

        # Assert
        assert isinstance(json_str, str)
        assert "json_test_connector" in json_str
        assert "json_test" in json_str
        assert "JSON test prompt" in json_str

    def test_entity_from_dict(self):
        """Test AttackModuleEntity creation from dictionary"""
        # Arrange
        entity_dict = {
            "connector": "dict_connector",
            "metric": {"name": "dict_metric", "threshold": 0.75},
            "prompt": "Dict prompt",
            "dataset": "dict_dataset.csv",
            "prompt_processor": "dict_processor",
            "callback_fn": None
        }

        # Act
        entity = AttackModuleEntity(**entity_dict)

        # Assert
        assert entity.connector == "dict_connector"
        assert entity.metric == {"name": "dict_metric", "threshold": 0.75}
        assert entity.prompt == "Dict prompt"
        assert entity.dataset == "dict_dataset.csv"
        assert entity.prompt_processor == "dict_processor"
        assert entity.callback_fn is None

    def test_inheritance_from_basemodel(self):
        """Test that AttackModuleEntity inherits from BaseModel"""
        # Arrange
        entity = AttackModuleEntity(
            connector="test",
            metric={"name": "test"},
            prompt_processor="test"
        )

        # Act & Assert
        from pydantic import BaseModel
        assert isinstance(entity, BaseModel)
        assert hasattr(entity, 'model_dump')
        assert hasattr(entity, 'model_dump_json')
        assert hasattr(entity, 'model_validate')

    def test_arbitrary_types_allowed_config(self):
        """Test that the Config allows arbitrary types (for callback functions)"""
        # Arrange
        class CustomCallable:
            def __call__(self, x):
                return f"Custom: {x}"

        custom_callback = CustomCallable()

        # Act
        entity = AttackModuleEntity(
            connector="test",
            metric={"name": "test"},
            prompt_processor="test",
            callback_fn=custom_callback
        )

        # Assert
        assert entity.callback_fn == custom_callback
        assert entity.callback_fn("test") == "Custom: test"

    @pytest.mark.parametrize("field_name,new_value", [
        ("connector", "new_connector"),
        ("metric", {"name": "new_metric", "updated": True}),
        ("prompt", "Updated prompt text"),
        ("dataset", "updated_dataset.json"),
        ("prompt_processor", "updated_processor"),
    ])
    def test_field_assignment_after_initialization(self, field_name, new_value):
        """Test field assignment after entity initialization"""
        # Arrange
        entity = AttackModuleEntity(
            connector="original",
            metric={"name": "original"},
            prompt_processor="original"
        )

        # Act
        setattr(entity, field_name, new_value)

        # Assert
        assert getattr(entity, field_name) == new_value

    def test_callback_fn_none_assignment(self):
        """Test explicit None assignment to callback_fn"""
        # Act
        entity = AttackModuleEntity(
            connector="test",
            metric={"name": "test"},
            prompt_processor="test",
            callback_fn=None
        )

        # Assert
        assert entity.callback_fn is None

    def test_complex_nested_metric_structure(self):
        """Test AttackModuleEntity with complex nested metric structure"""
        # Arrange
        complex_metric = {
            "name": "complex_metric",
            "config": {
                "primary": {
                    "algorithm": "advanced",
                    "parameters": {
                        "threshold": 0.95,
                        "weights": [0.1, 0.2, 0.7],
                        "flags": {"strict": True, "verbose": False}
                    }
                },
                "secondary": {
                    "fallback": "simple",
                    "timeout": 30
                }
            },
            "metadata": {
                "version": "2.1.0",
                "author": "test_author",
                "tags": ["accuracy", "performance", "robust"]
            }
        }

        # Act
        entity = AttackModuleEntity(
            connector="complex_connector",
            metric=complex_metric,
            prompt_processor="complex_processor"
        )

        # Assert
        assert entity.metric == complex_metric
        assert entity.metric["config"]["primary"]["parameters"]["threshold"] == 0.95
        assert entity.metric["metadata"]["tags"] == ["accuracy", "performance", "robust"]

    @pytest.mark.parametrize("connector,metric,prompt,dataset,processor", [
        # Edge cases - boundary conditions
        ("", {"name": ""}, "", "", ""),  # All empty strings
        ("a", {"k": "v"}, "p", "d", "pr"),  # Single character strings
        ("very_long_connector_name_with_many_characters", 
         {"very_long_metric_name": "with_very_long_value_that_spans_multiple_words"}, 
         "Very long prompt text that contains multiple sentences and various punctuation marks.",
         "very/long/path/to/dataset/file/with/multiple/directories.json",
         "very_long_prompt_processor_name_with_descriptive_text"),
    ])
    def test_edge_case_string_lengths(self, connector, metric, prompt, dataset, processor):
        """Test AttackModuleEntity with edge case string lengths"""
        # Act
        entity = AttackModuleEntity(
            connector=connector,
            metric=metric,
            prompt=prompt,
            dataset=dataset,
            prompt_processor=processor
        )

        # Assert
        assert entity.connector == connector
        assert entity.metric == metric
        assert entity.prompt == prompt
        assert entity.dataset == dataset
        assert entity.prompt_processor == processor

    def test_multiple_callback_function_types(self):
        """Test AttackModuleEntity with different types of callback functions"""
        # Test with regular function
        def regular_func(x):
            return x * 2

        entity1 = AttackModuleEntity(
            connector="test1",
            metric={"name": "test1"},
            prompt_processor="test1",
            callback_fn=regular_func
        )
        assert entity1.callback_fn(5) == 10

        # Test with lambda
        entity2 = AttackModuleEntity(
            connector="test2",
            metric={"name": "test2"},
            prompt_processor="test2",
            callback_fn=lambda x: str(x).upper()
        )
        assert entity2.callback_fn("hello") == "HELLO"

        # Test with method
        class TestClass:
            def method(self, x):
                return f"method_{x}"

        test_obj = TestClass()
        entity3 = AttackModuleEntity(
            connector="test3",
            metric={"name": "test3"},
            prompt_processor="test3",
            callback_fn=test_obj.method
        )
        assert entity3.callback_fn("test") == "method_test" 