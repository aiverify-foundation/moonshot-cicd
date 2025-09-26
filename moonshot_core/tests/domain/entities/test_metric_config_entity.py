import pytest
from pydantic import ValidationError

from src.domain.entities.metric_config_entity import MetricConfigEntity
from domain.entities.connector_entity import ConnectorEntity


class TestMetricConfigEntity:
    """Test class for MetricConfigEntity"""

    def test_minimal_initialization(self):
        """Test MetricConfigEntity with minimal required parameters"""
        # Arrange
        name = "test_metric"
        connector_config = {
            "connector_adapter": "openai_adapter",
            "model": "gpt-4"
        }

        # Act
        entity = MetricConfigEntity(
            name=name,
            connector_configurations=connector_config
        )

        # Assert
        assert entity.name == name
        assert isinstance(entity.connector_configurations, ConnectorEntity)
        assert entity.connector_configurations.connector_adapter == "openai_adapter"
        assert entity.connector_configurations.model == "gpt-4"
        assert entity.params == {}  # Default value

    def test_full_initialization(self):
        """Test MetricConfigEntity with all parameters provided"""
        # Arrange
        name = "comprehensive_metric"
        connector_config = {
            "connector_adapter": "azure_adapter",
            "model": "gpt-4o-mini",
            "model_endpoint": "https://api.azure.com/v1",
            "params": {"temperature": 0.5, "max_tokens": 500},
            "connector_pre_prompt": "Evaluate the following:",
            "connector_post_prompt": "Provide detailed assessment",
            "system_prompt": "You are a metric evaluation assistant."
        }
        params = {
            "threshold": 0.8,
            "weight": 0.7,
            "strict_mode": True,
            "evaluation_criteria": ["accuracy", "relevance", "coherence"]
        }

        # Act
        entity = MetricConfigEntity(
            name=name,
            connector_configurations=connector_config,
            params=params
        )

        # Assert
        assert entity.name == name
        assert isinstance(entity.connector_configurations, ConnectorEntity)
        assert entity.connector_configurations.connector_adapter == "azure_adapter"
        assert entity.connector_configurations.model == "gpt-4o-mini"
        assert entity.params == params

    @pytest.mark.parametrize("name", [
        # Good cases - various valid name strings
        "simple_metric",
        "metric-with-hyphens",
        "MetricName123",
        "metric_with_underscores",
        "UPPERCASE_METRIC",
        "Mixed_Case_Metric",
        "metric.with.dots",
        "m",  # Single character
        "very_long_metric_name_with_many_characters_and_descriptive_text",
        "unicode_metric_名前",
        "metric with spaces",
        "metric!@#$%^&*()",  # Special characters
        "accuracy",
        "faithfulness",
        "relevance",
        "coherence",
        "f1_score",
        "bleu_score",
        "rouge_score",
    ])
    def test_valid_name_variations(self, name):
        """Test MetricConfigEntity with various valid name strings"""
        # Arrange
        connector_config = {
            "connector_adapter": "test_adapter",
            "model": "test_model"
        }

        # Act
        entity = MetricConfigEntity(
            name=name,
            connector_configurations=connector_config
        )

        # Assert
        assert entity.name == name

    @pytest.mark.parametrize("name,expected_error", [
        # Bad cases - invalid name types
        (None, "Input should be a valid string"),
        (123, "Input should be a valid string"),
        ([], "Input should be a valid string"),
        ({}, "Input should be a valid string"),
        (True, "Input should be a valid string"),
        (3.14, "Input should be a valid string"),
    ])
    def test_invalid_name_types(self, name, expected_error):
        """Test MetricConfigEntity with invalid name types"""
        # Arrange
        connector_config = {
            "connector_adapter": "test_adapter",
            "model": "test_model"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            MetricConfigEntity(
                name=name,
                connector_configurations=connector_config
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("connector_config", [
        # Good cases - various valid connector configurations
        {
            "connector_adapter": "openai_adapter",
            "model": "gpt-4"
        },
        {
            "connector_adapter": "azure_adapter",
            "model": "gpt-4o-mini",
            "model_endpoint": "https://api.azure.com/v1",
            "params": {"temperature": 0.7}
        },
        {
            "connector_adapter": "aws_bedrock_adapter",
            "model": "anthropic.claude-3-haiku-20240307-v1:0",
            "system_prompt": "You are an evaluator"
        },
        {
            "connector_adapter": "langchain_openai_chatopenai_adapter",
            "model": "gpt-3.5-turbo",
            "connector_pre_prompt": "Context:",
            "connector_post_prompt": "Assessment:"
        },
    ])
    def test_valid_connector_configurations(self, connector_config):
        """Test MetricConfigEntity with various valid connector configurations"""
        # Act
        entity = MetricConfigEntity(
            name="test_metric",
            connector_configurations=connector_config
        )

        # Assert
        assert isinstance(entity.connector_configurations, ConnectorEntity)
        assert entity.connector_configurations.connector_adapter == connector_config["connector_adapter"]
        assert entity.connector_configurations.model == connector_config["model"]

    @pytest.mark.parametrize("connector_config,expected_error", [
        # Bad cases - invalid connector configuration types
        (None, "Input should be a valid dictionary"),
        ("string", "Input should be a valid dictionary"),
        (123, "Input should be a valid dictionary"),
        ([], "Input should be a valid dictionary"),
        (True, "Input should be a valid dictionary"),
    ])
    def test_invalid_connector_configurations_types(self, connector_config, expected_error):
        """Test MetricConfigEntity with invalid connector configuration types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            MetricConfigEntity(
                name="test_metric",
                connector_configurations=connector_config
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("params", [
        # Good cases - various valid params structures
        {},  # Empty dict
        {"threshold": 0.8},
        {"weight": 0.5, "threshold": 0.9},
        {"strict_mode": True, "timeout": 30},
        {"evaluation_criteria": ["accuracy", "relevance"]},
        {"nested": {"config": {"value": 42}}},
        {"mixed_types": {"string": "test", "number": 123, "boolean": True, "list": [1, 2, 3]}},
        {"large_config": {f"param_{i}": i for i in range(100)}},
        {"unicode_params": {"名前": "テスト", "説明": "パラメータ"}},
    ])
    def test_valid_params_variations(self, params):
        """Test MetricConfigEntity with various valid params structures"""
        # Arrange
        connector_config = {
            "connector_adapter": "test_adapter",
            "model": "test_model"
        }

        # Act
        entity = MetricConfigEntity(
            name="test_metric",
            connector_configurations=connector_config,
            params=params
        )

        # Assert
        assert entity.params == params

    @pytest.mark.parametrize("params,expected_error", [
        # Bad cases - invalid params types
        ("string", "Input should be a valid dictionary"),
        (123, "Input should be a valid dictionary"),
        ([], "Input should be a valid dictionary"),
        (True, "Input should be a valid dictionary"),
        (None, "Input should be a valid dictionary"),
    ])
    def test_invalid_params_types(self, params, expected_error):
        """Test MetricConfigEntity with invalid params types"""
        # Arrange
        connector_config = {
            "connector_adapter": "test_adapter",
            "model": "test_model"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            MetricConfigEntity(
                name="test_metric",
                connector_configurations=connector_config,
                params=params
            )
        assert expected_error in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test MetricConfigEntity with missing required fields"""
        # Test missing name
        with pytest.raises(ValidationError) as exc_info:
            MetricConfigEntity(
                connector_configurations={
                    "connector_adapter": "test_adapter",
                    "model": "test_model"
                }
            )
        assert "Field required" in str(exc_info.value)

        # Test missing connector_configurations
        with pytest.raises(ValidationError) as exc_info:
            MetricConfigEntity(
                name="test_metric"
            )
        assert "Field required" in str(exc_info.value)

    def test_entity_serialization(self):
        """Test MetricConfigEntity serialization to dictionary"""
        # Arrange
        connector_config = {
            "connector_adapter": "openai_adapter",
            "model": "gpt-4o",
            "params": {"temperature": 0.7}
        }
        params = {"threshold": 0.8, "weight": 0.5}

        entity = MetricConfigEntity(
            name="serialization_test",
            connector_configurations=connector_config,
            params=params
        )

        # Act
        entity_dict = entity.model_dump()

        # Assert
        expected_keys = ["name", "connector_configurations", "params"]
        assert all(key in entity_dict for key in expected_keys)
        assert entity_dict["name"] == "serialization_test"
        assert entity_dict["params"] == params
        assert entity_dict["connector_configurations"]["connector_adapter"] == "openai_adapter"
        assert entity_dict["connector_configurations"]["model"] == "gpt-4o"

    def test_entity_json_serialization(self):
        """Test MetricConfigEntity JSON serialization"""
        # Arrange
        connector_config = {
            "connector_adapter": "json_adapter",
            "model": "json_model",
            "system_prompt": "JSON test prompt"
        }
        
        entity = MetricConfigEntity(
            name="json_serialization_test",
            connector_configurations=connector_config,
            params={"json_param": "json_value"}
        )

        # Act
        json_str = entity.model_dump_json()

        # Assert
        assert isinstance(json_str, str)
        assert "json_serialization_test" in json_str
        assert "json_adapter" in json_str
        assert "json_param" in json_str

    def test_entity_from_dict(self):
        """Test MetricConfigEntity creation from dictionary"""
        # Arrange
        entity_dict = {
            "name": "dict_test_metric",
            "connector_configurations": {
                "connector_adapter": "dict_adapter",
                "model": "dict_model",
                "model_endpoint": "",
                "params": {},
                "connector_pre_prompt": "",
                "connector_post_prompt": "",
                "system_prompt": ""
            },
            "params": {"dict_param": "dict_value"}
        }

        # Act
        entity = MetricConfigEntity(**entity_dict)

        # Assert
        assert entity.name == "dict_test_metric"
        assert isinstance(entity.connector_configurations, ConnectorEntity)
        assert entity.connector_configurations.connector_adapter == "dict_adapter"
        assert entity.connector_configurations.model == "dict_model"
        assert entity.params == {"dict_param": "dict_value"}

    def test_inheritance_from_basemodel(self):
        """Test that MetricConfigEntity inherits from BaseModel"""
        # Arrange
        entity = MetricConfigEntity(
            name="inheritance_test",
            connector_configurations={
                "connector_adapter": "test_adapter",
                "model": "test_model"
            }
        )

        # Act & Assert
        from pydantic import BaseModel
        assert isinstance(entity, BaseModel)
        assert hasattr(entity, 'model_dump')
        assert hasattr(entity, 'model_dump_json')
        assert hasattr(entity, 'model_validate')

    def test_arbitrary_types_allowed_config(self):
        """Test that the Config allows arbitrary types"""
        # Act
        entity = MetricConfigEntity(
            name="config_test",
            connector_configurations={
                "connector_adapter": "custom_adapter",
                "model": "custom_model"
            }
        )

        # Assert
        assert isinstance(entity.connector_configurations, ConnectorEntity)
        assert hasattr(entity, 'Config')
        assert entity.Config.arbitrary_types_allowed is True

    @pytest.mark.parametrize("field_name,new_value", [
        ("name", "updated_metric_name"),
        ("params", {"updated": "params", "new_threshold": 0.9}),
    ])
    def test_field_assignment_after_initialization(self, field_name, new_value):
        """Test field assignment after entity initialization"""
        # Arrange
        entity = MetricConfigEntity(
            name="original_name",
            connector_configurations={
                "connector_adapter": "original_adapter",
                "model": "original_model"
            },
            params={"original": "params"}
        )

        # Act
        setattr(entity, field_name, new_value)

        # Assert
        assert getattr(entity, field_name) == new_value

    def test_connector_configurations_assignment_after_initialization(self):
        """Test connector_configurations assignment after initialization"""
        # Arrange
        entity = MetricConfigEntity(
            name="test_name",
            connector_configurations={
                "connector_adapter": "original_adapter",
                "model": "original_model"
            }
        )

        new_config = ConnectorEntity(
            connector_adapter="new_adapter",
            model="new_model",
            params={"new": "param"}
        )

        # Act
        entity.connector_configurations = new_config

        # Assert
        assert entity.connector_configurations == new_config
        assert entity.connector_configurations.connector_adapter == "new_adapter"
        assert entity.connector_configurations.model == "new_model"

    def test_complex_nested_params_structure(self):
        """Test MetricConfigEntity with complex nested params structure"""
        # Arrange
        complex_params = {
            "evaluation": {
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
        entity = MetricConfigEntity(
            name="complex_metric",
            connector_configurations={
                "connector_adapter": "complex_adapter",
                "model": "complex_model"
            },
            params=complex_params
        )

        # Assert
        assert entity.params == complex_params
        assert entity.params["evaluation"]["primary"]["parameters"]["threshold"] == 0.95
        assert entity.params["metadata"]["tags"] == ["accuracy", "performance", "robust"]

    @pytest.mark.parametrize("name,connector_adapter,model,params", [
        # Edge cases - boundary conditions
        ("", "adapter", "model", {}),  # Empty name
        ("metric", "", "model", {}),  # Empty adapter
        ("metric", "adapter", "", {}),  # Empty model
        ("a", "b", "c", {"d": "e"}),  # Single character strings
        ("very_long_metric_name_with_many_characters", 
         "very_long_adapter_name_with_descriptive_text",
         "very_long_model_name_with_version_numbers",
         {"very_long_param_name": "very_long_param_value"}),
    ])
    def test_edge_case_combinations(self, name, connector_adapter, model, params):
        """Test MetricConfigEntity with edge case combinations"""
        # Act
        entity = MetricConfigEntity(
            name=name,
            connector_configurations={
                "connector_adapter": connector_adapter,
                "model": model
            },
            params=params
        )

        # Assert
        assert entity.name == name
        assert entity.connector_configurations.connector_adapter == connector_adapter
        assert entity.connector_configurations.model == model
        assert entity.params == params

    def test_real_world_metric_configurations(self):
        """Test MetricConfigEntity with real-world metric configurations"""
        # Test accuracy metric
        accuracy_entity = MetricConfigEntity(
            name="accuracy",
            connector_configurations={
                "connector_adapter": "openai_adapter",
                "model": "gpt-4o",
                "system_prompt": "Evaluate the accuracy of the response"
            },
            params={"threshold": 0.8, "normalize": True}
        )

        # Test faithfulness metric
        faithfulness_entity = MetricConfigEntity(
            name="faithfulness",
            connector_configurations={
                "connector_adapter": "langchain_openai_chatopenai_adapter",
                "model": "gpt-4o-mini",
                "connector_pre_prompt": "Check if the response is faithful to the context:",
                "system_prompt": "You are a faithfulness evaluator"
            },
            params={"categorise_result": False, "strict_mode": True}
        )

        # Assert
        assert accuracy_entity.name == "accuracy"
        assert accuracy_entity.params["threshold"] == 0.8
        assert faithfulness_entity.name == "faithfulness"
        assert faithfulness_entity.params["categorise_result"] is False

    def test_metric_config_with_different_connector_types(self):
        """Test MetricConfigEntity with different types of connectors"""
        # Test with OpenAI connector
        openai_metric = MetricConfigEntity(
            name="openai_metric",
            connector_configurations={
                "connector_adapter": "openai_adapter",
                "model": "gpt-4",
                "params": {"temperature": 0.0, "max_tokens": 100}
            }
        )

        # Test with Azure connector
        azure_metric = MetricConfigEntity(
            name="azure_metric",
            connector_configurations={
                "connector_adapter": "azure_adapter",
                "model": "gpt-4o-mini",
                "model_endpoint": "https://myorg.openai.azure.com/",
                "params": {"api_version": "2023-07-01-preview"}
            }
        )

        # Test with AWS Bedrock connector
        bedrock_metric = MetricConfigEntity(
            name="bedrock_metric",
            connector_configurations={
                "connector_adapter": "aws_bedrock_adapter",
                "model": "anthropic.claude-3-haiku-20240307-v1:0",
                "model_endpoint": "https://bedrock-runtime.us-east-1.amazonaws.com/",
                "params": {"region": "us-east-1"}
            }
        )

        # Assert
        assert openai_metric.connector_configurations.connector_adapter == "openai_adapter"
        assert azure_metric.connector_configurations.connector_adapter == "azure_adapter"
        assert bedrock_metric.connector_configurations.connector_adapter == "aws_bedrock_adapter"

    def test_params_default_value(self):
        """Test that params defaults to empty dict when not provided"""
        # Act
        entity = MetricConfigEntity(
            name="default_params_test",
            connector_configurations={
                "connector_adapter": "test_adapter",
                "model": "test_model"
            }
        )

        # Assert
        assert entity.params == {}
        assert isinstance(entity.params, dict)

    def test_empty_string_fields(self):
        """Test MetricConfigEntity with empty string name"""
        # Act
        entity = MetricConfigEntity(
            name="",  # Empty name should be valid
            connector_configurations={
                "connector_adapter": "test_adapter",
                "model": "test_model"
            },
            params={}
        )

        # Assert
        assert entity.name == ""
        assert entity.params == {} 