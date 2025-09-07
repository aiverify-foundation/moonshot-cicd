import pytest
from typing import Any
from pydantic import ValidationError

from domain.entities.connector_entity import ConnectorEntity


class TestConnectorEntity:
    """Test class for ConnectorEntity"""

    def test_minimal_initialization(self):
        """Test ConnectorEntity with minimal required parameters"""
        # Arrange
        connector_adapter = "openai_adapter"
        model = "gpt-4o"

        # Act
        entity = ConnectorEntity(
            connector_adapter=connector_adapter,
            model=model
        )

        # Assert
        assert entity.connector_adapter == connector_adapter
        assert entity.model == model
        assert entity.model_endpoint == ""  # Default value
        assert entity.params == {}  # Default value
        assert entity.connector_pre_prompt == ""  # Default value
        assert entity.connector_post_prompt == ""  # Default value
        assert entity.system_prompt == ""  # Default value

    def test_full_initialization(self):
        """Test ConnectorEntity with all parameters provided"""
        # Arrange
        connector_adapter = "openai_adapter"
        model = "gpt-4o"
        model_endpoint = "https://api.openai.com/v1/chat/completions"
        params = {"temperature": 0.7, "max_tokens": 150, "timeout": 30}
        connector_pre_prompt = "Pre-prompt context"
        connector_post_prompt = "Post-prompt instructions"
        system_prompt = "You are a helpful assistant"

        # Act
        entity = ConnectorEntity(
            connector_adapter=connector_adapter,
            model=model,
            model_endpoint=model_endpoint,
            params=params,
            connector_pre_prompt=connector_pre_prompt,
            connector_post_prompt=connector_post_prompt,
            system_prompt=system_prompt
        )

        # Assert
        assert entity.connector_adapter == connector_adapter
        assert entity.model == model
        assert entity.model_endpoint == model_endpoint
        assert entity.params == params
        assert entity.connector_pre_prompt == connector_pre_prompt
        assert entity.connector_post_prompt == connector_post_prompt
        assert entity.system_prompt == system_prompt

    @pytest.mark.parametrize("connector_adapter,model", [
        # Good cases - various valid combinations
        ("openai_adapter", "gpt-4o"),
        ("azure_adapter", "gpt-4o-mini"),
        ("aws_bedrock_adapter", "anthropic.claude-3-haiku-20240307-v1:0"),
        ("aws_sagemaker_adapter", "llama-2-7b"),
        ("langchain_openai_chatopenai_adapter", "gpt-3.5-turbo"),
        ("custom_adapter", "custom-model-v1"),
        ("huggingface_adapter", "meta-llama/Llama-2-7b-chat-hf"),
        ("ollama_adapter", "llama2:7b"),
    ])
    def test_initialization_with_valid_required_parameters(self, connector_adapter, model):
        """Test ConnectorEntity initialization with various valid required parameter combinations"""
        # Act
        entity = ConnectorEntity(
            connector_adapter=connector_adapter,
            model=model
        )

        # Assert
        assert entity.connector_adapter == connector_adapter
        assert entity.model == model

    @pytest.mark.parametrize("connector_adapter,expected_error", [
        # Bad cases - invalid connector_adapter types
        (None, "Input should be a valid string"),
        (123, "Input should be a valid string"),
        ([], "Input should be a valid string"),
        ({}, "Input should be a valid string"),
        (True, "Input should be a valid string"),
        (0.5, "Input should be a valid string"),
    ])
    def test_invalid_connector_adapter_types(self, connector_adapter, expected_error):
        """Test ConnectorEntity with invalid connector_adapter types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ConnectorEntity(
                connector_adapter=connector_adapter,
                model="gpt-4o"
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("model,expected_error", [
        # Bad cases - invalid model types
        (None, "Input should be a valid string"),
        (123, "Input should be a valid string"),
        ([], "Input should be a valid string"),
        ({}, "Input should be a valid string"),
        (True, "Input should be a valid string"),
        (0.5, "Input should be a valid string"),
    ])
    def test_invalid_model_types(self, model, expected_error):
        """Test ConnectorEntity with invalid model types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ConnectorEntity(
                connector_adapter="openai_adapter",
                model=model
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("model_endpoint", [
        # Good cases - various valid endpoint URLs and empty string
        "",  # Default empty string
        "https://api.openai.com/v1/chat/completions",
        "https://myorg.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2023-07-01-preview",
        "https://bedrock-runtime.us-east-1.amazonaws.com/model/anthropic.claude-3-haiku-20240307-v1:0/invoke",
        "http://localhost:8080/v1/completions",
        "https://api.anthropic.com/v1/messages",
        "custom://internal-service/model-endpoint",
        "ws://websocket-endpoint.com/stream",
    ])
    def test_valid_model_endpoint_values(self, model_endpoint):
        """Test ConnectorEntity with various valid model_endpoint values"""
        # Act
        entity = ConnectorEntity(
            connector_adapter="test_adapter",
            model="test_model",
            model_endpoint=model_endpoint
        )

        # Assert
        assert entity.model_endpoint == model_endpoint

    @pytest.mark.parametrize("model_endpoint,expected_error", [
        # Bad cases - invalid model_endpoint types
        (123, "Input should be a valid string"),
        ([], "Input should be a valid string"),
        ({}, "Input should be a valid string"),
        (True, "Input should be a valid string"),
        (0.5, "Input should be a valid string"),
        (None, "Input should be a valid string"),
    ])
    def test_invalid_model_endpoint_types(self, model_endpoint, expected_error):
        """Test ConnectorEntity with invalid model_endpoint types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ConnectorEntity(
                connector_adapter="test_adapter",
                model="test_model",
                model_endpoint=model_endpoint
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("params", [
        # Good cases - various valid parameter dictionaries
        {},  # Default empty dict
        {"temperature": 0.7},
        {"temperature": 0.5, "max_tokens": 100},
        {"timeout": 300, "retries": 3, "temperature": 0.9},
        {"session": {"region_name": "us-east-1", "aws_access_key_id": "key"}},
        {"nested": {"config": {"deep": {"value": 123}}}},
        {"complex": {"list": [1, 2, 3], "dict": {"a": "b"}, "bool": True}},
        {"api_key": "api_key_sample", "organization": "org-abcdef"},
    ])
    def test_valid_params_values(self, params):
        """Test ConnectorEntity with various valid params dictionary values"""
        # Act
        entity = ConnectorEntity(
            connector_adapter="test_adapter",
            model="test_model",
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
        (0.5, "Input should be a valid dictionary"),
        (None, "Input should be a valid dictionary"),
    ])
    def test_invalid_params_types(self, params, expected_error):
        """Test ConnectorEntity with invalid params types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ConnectorEntity(
                connector_adapter="test_adapter",
                model="test_model",
                params=params
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("connector_pre_prompt", [
        # Good cases - various valid pre-prompt strings
        "",  # Default empty string
        "Please analyze the following:",
        "Context: You are an expert in machine learning.\nTask:",
        "Multi-line\npre-prompt\nwith\nbreaks",
        "Pre-prompt with special chars: !@#$%^&*()",
        "Unicode pre-prompt: 你好世界",
        "Very long pre-prompt " * 50,  # Long string
        "JSON-like: {\"instruction\": \"analyze\", \"format\": \"detailed\"}",
    ])
    def test_valid_connector_pre_prompt_values(self, connector_pre_prompt):
        """Test ConnectorEntity with various valid connector_pre_prompt values"""
        # Act
        entity = ConnectorEntity(
            connector_adapter="test_adapter",
            model="test_model",
            connector_pre_prompt=connector_pre_prompt
        )

        # Assert
        assert entity.connector_pre_prompt == connector_pre_prompt

    @pytest.mark.parametrize("connector_pre_prompt,expected_error", [
        # Bad cases - invalid connector_pre_prompt types
        (123, "Input should be a valid string"),
        ([], "Input should be a valid string"),
        ({}, "Input should be a valid string"),
        (True, "Input should be a valid string"),
        (0.5, "Input should be a valid string"),
        (None, "Input should be a valid string"),
    ])
    def test_invalid_connector_pre_prompt_types(self, connector_pre_prompt, expected_error):
        """Test ConnectorEntity with invalid connector_pre_prompt types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ConnectorEntity(
                connector_adapter="test_adapter",
                model="test_model",
                connector_pre_prompt=connector_pre_prompt
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("connector_post_prompt", [
        # Good cases - various valid post-prompt strings
        "",  # Default empty string
        "Please provide a detailed explanation.",
        "Format your response as JSON.",
        "Multi-line\npost-prompt\nwith\ninstructions",
        "Post-prompt with special chars: !@#$%^&*()",
        "Unicode post-prompt: 안녕하세요",
        "Very long post-prompt " * 50,  # Long string
        "Template: Please respond in the following format:\n1. Summary\n2. Details\n3. Conclusion",
    ])
    def test_valid_connector_post_prompt_values(self, connector_post_prompt):
        """Test ConnectorEntity with various valid connector_post_prompt values"""
        # Act
        entity = ConnectorEntity(
            connector_adapter="test_adapter",
            model="test_model",
            connector_post_prompt=connector_post_prompt
        )

        # Assert
        assert entity.connector_post_prompt == connector_post_prompt

    @pytest.mark.parametrize("connector_post_prompt,expected_error", [
        # Bad cases - invalid connector_post_prompt types
        (123, "Input should be a valid string"),
        ([], "Input should be a valid string"),
        ({}, "Input should be a valid string"),
        (True, "Input should be a valid string"),
        (0.5, "Input should be a valid string"),
        (None, "Input should be a valid string"),
    ])
    def test_invalid_connector_post_prompt_types(self, connector_post_prompt, expected_error):
        """Test ConnectorEntity with invalid connector_post_prompt types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ConnectorEntity(
                connector_adapter="test_adapter",
                model="test_model",
                connector_post_prompt=connector_post_prompt
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("system_prompt", [
        # Good cases - various valid system prompt strings
        "",  # Default empty string
        "You are a helpful assistant.",
        "You are an expert Python developer.",
        "Multi-line\nsystem\nprompt\nwith\ndetailed\ninstructions",
        "System prompt with special chars: !@#$%^&*()",
        "Unicode system prompt: こんにちは",
        "Very long system prompt " * 50,  # Long string
        "Complex instructions: You are an AI assistant specialized in code review. " +
        "Please provide constructive feedback, suggest improvements, and identify potential issues.",
    ])
    def test_valid_system_prompt_values(self, system_prompt):
        """Test ConnectorEntity with various valid system_prompt values"""
        # Act
        entity = ConnectorEntity(
            connector_adapter="test_adapter",
            model="test_model",
            system_prompt=system_prompt
        )

        # Assert
        assert entity.system_prompt == system_prompt

    @pytest.mark.parametrize("system_prompt,expected_error", [
        # Bad cases - invalid system_prompt types
        (123, "Input should be a valid string"),
        ([], "Input should be a valid string"),
        ({}, "Input should be a valid string"),
        (True, "Input should be a valid string"),
        (0.5, "Input should be a valid string"),
        (None, "Input should be a valid string"),
    ])
    def test_invalid_system_prompt_types(self, system_prompt, expected_error):
        """Test ConnectorEntity with invalid system_prompt types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ConnectorEntity(
                connector_adapter="test_adapter",
                model="test_model",
                system_prompt=system_prompt
            )
        assert expected_error in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test ConnectorEntity initialization with missing required fields"""
        # Test missing connector_adapter
        with pytest.raises(ValidationError) as exc_info:
            ConnectorEntity(model="gpt-4o")
        assert "Field required" in str(exc_info.value)
        assert "connector_adapter" in str(exc_info.value)

        # Test missing model
        with pytest.raises(ValidationError) as exc_info:
            ConnectorEntity(connector_adapter="openai_adapter")
        assert "Field required" in str(exc_info.value)
        assert "model" in str(exc_info.value)

        # Test missing both required fields
        with pytest.raises(ValidationError) as exc_info:
            ConnectorEntity()
        assert "Field required" in str(exc_info.value)

    def test_entity_serialization(self):
        """Test ConnectorEntity serialization to dictionary"""
        # Arrange
        entity = ConnectorEntity(
            connector_adapter="openai_adapter",
            model="gpt-4o",
            model_endpoint="https://api.openai.com/v1/chat/completions",
            params={"temperature": 0.7, "max_tokens": 150},
            connector_pre_prompt="Analyze the following:",
            connector_post_prompt="Provide detailed response.",
            system_prompt="You are a helpful assistant."
        )

        # Act
        entity_dict = entity.model_dump()

        # Assert
        expected_keys = [
            "connector_adapter", "model", "model_endpoint", "params",
            "connector_pre_prompt", "connector_post_prompt", "system_prompt"
        ]
        assert all(key in entity_dict for key in expected_keys)
        assert entity_dict["connector_adapter"] == "openai_adapter"
        assert entity_dict["model"] == "gpt-4o"
        assert entity_dict["model_endpoint"] == "https://api.openai.com/v1/chat/completions"
        assert entity_dict["params"] == {"temperature": 0.7, "max_tokens": 150}

    def test_entity_json_serialization(self):
        """Test ConnectorEntity JSON serialization"""
        # Arrange
        entity = ConnectorEntity(
            connector_adapter="azure_adapter",
            model="gpt-4o-mini",
            params={"api_version": "2023-07-01-preview"}
        )

        # Act
        json_str = entity.model_dump_json()

        # Assert
        assert isinstance(json_str, str)
        assert "azure_adapter" in json_str
        assert "gpt-4o-mini" in json_str
        assert "api_version" in json_str

    def test_entity_from_dict(self):
        """Test ConnectorEntity creation from dictionary"""
        # Arrange
        entity_data = {
            "connector_adapter": "aws_bedrock_adapter",
            "model": "anthropic.claude-3-haiku-20240307-v1:0",
            "model_endpoint": "https://bedrock-runtime.us-east-1.amazonaws.com/",
            "params": {"timeout": 300, "region": "us-east-1"},
            "connector_pre_prompt": "Context setup",
            "connector_post_prompt": "Response format",
            "system_prompt": "You are Claude, an AI assistant."
        }

        # Act
        entity = ConnectorEntity(**entity_data)

        # Assert
        assert entity.connector_adapter == entity_data["connector_adapter"]
        assert entity.model == entity_data["model"]
        assert entity.model_endpoint == entity_data["model_endpoint"]
        assert entity.params == entity_data["params"]
        assert entity.connector_pre_prompt == entity_data["connector_pre_prompt"]
        assert entity.connector_post_prompt == entity_data["connector_post_prompt"]
        assert entity.system_prompt == entity_data["system_prompt"]

    def test_inheritance_from_basemodel(self):
        """Test that ConnectorEntity properly inherits from BaseModel"""
        # Act
        entity = ConnectorEntity(
            connector_adapter="test_adapter",
            model="test_model"
        )

        # Assert
        assert hasattr(entity, 'model_dump')
        assert hasattr(entity, 'model_dump_json')
        assert hasattr(entity, 'model_validate')
        assert entity.__class__.__bases__[0].__name__ == 'BaseModel'

    def test_arbitrary_types_allowed_config(self):
        """Test that arbitrary_types_allowed is properly configured"""
        # Assert
        assert ConnectorEntity.model_config.get('arbitrary_types_allowed') is True

    @pytest.mark.parametrize("field_name,new_value", [
        ("connector_adapter", "new_adapter"),
        ("model", "new_model"),
        ("model_endpoint", "https://new-endpoint.com/api"),
        ("params", {"new_param": "new_value", "updated": True}),
        ("connector_pre_prompt", "Updated pre-prompt text"),
        ("connector_post_prompt", "Updated post-prompt text"),
        ("system_prompt", "Updated system prompt"),
    ])
    def test_field_assignment_after_initialization(self, field_name, new_value):
        """Test field assignment after ConnectorEntity initialization"""
        # Arrange
        entity = ConnectorEntity(
            connector_adapter="original_adapter",
            model="original_model"
        )

        # Act
        setattr(entity, field_name, new_value)

        # Assert
        assert getattr(entity, field_name) == new_value

    def test_complex_nested_params_structure(self):
        """Test ConnectorEntity with complex nested params structure"""
        # Arrange
        complex_params = {
            "authentication": {
                "type": "oauth2",
                "credentials": {
                    "client_id": "client123",
                    "client_secret": "secret456"
                },
                "scopes": ["read", "write", "admin"]
            },
            "model_config": {
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 0.9,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1
            },
            "session_config": {
                "timeout": 300,
                "retries": 3,
                "backoff_factor": 2.0,
                "headers": {
                    "User-Agent": "ConnectorEntity/1.0",
                    "Accept": "application/json"
                }
            },
            "advanced": {
                "streaming": True,
                "parallel_calls": 5,
                "cache_responses": False,
                "logging": {
                    "level": "INFO",
                    "format": "json",
                    "destinations": ["console", "file"]
                }
            }
        }

        # Act
        entity = ConnectorEntity(
            connector_adapter="complex_adapter",
            model="complex_model",
            params=complex_params
        )

        # Assert
        assert entity.params == complex_params
        assert entity.params["authentication"]["type"] == "oauth2"
        assert entity.params["model_config"]["temperature"] == 0.7
        assert entity.params["session_config"]["timeout"] == 300
        assert entity.params["advanced"]["streaming"] is True

    @pytest.mark.parametrize("connector_adapter,model,endpoint,params", [
        # Edge cases - boundary conditions
        ("", "", "", {}),  # All minimal values
        ("a", "b", "c", {"k": "v"}),  # Single character strings
        ("very_long_adapter_name_" * 10, "very_long_model_name_" * 10, 
         "https://very-long-endpoint-url.com/" + "path/" * 20, 
         {"very_long_param_name_" * 5: "very_long_param_value_" * 10}),  # Very long strings
    ])
    def test_edge_case_string_lengths(self, connector_adapter, model, endpoint, params):
        """Test ConnectorEntity with edge case string lengths"""
        # Act
        entity = ConnectorEntity(
            connector_adapter=connector_adapter,
            model=model,
            model_endpoint=endpoint,
            params=params
        )

        # Assert
        assert entity.connector_adapter == connector_adapter
        assert entity.model == model
        assert entity.model_endpoint == endpoint
        assert entity.params == params

    def test_real_world_configurations(self):
        """Test ConnectorEntity with real-world configuration examples"""
        # Test OpenAI configuration
        openai_entity = ConnectorEntity(
            connector_adapter="openai_adapter",
            model="gpt-4o",
            model_endpoint="https://api.openai.com/v1/chat/completions",
            params={
                "api_key": "api_key_sample",
                "organization": "org-...",
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 1.0,
                "frequency_penalty": 0,
                "presence_penalty": 0
            },
            system_prompt="You are a helpful assistant that provides accurate and concise responses."
        )

        # Test AWS Bedrock configuration
        bedrock_entity = ConnectorEntity(
            connector_adapter="aws_bedrock_adapter",
            model="anthropic.claude-3-haiku-20240307-v1:0",
            params={
                "timeout": 300,
                "region_name": "us-east-1",
                "aws_access_key_id": "AKIA...",
                "aws_secret_access_key": "...",
                "max_tokens": 1000,
                "temperature": 0.5
            },
            connector_pre_prompt="Human: ",
            connector_post_prompt="\n\nAssistant:",
            system_prompt="You are Claude, an AI assistant created by Anthropic."
        )

        # Test Azure OpenAI configuration
        azure_entity = ConnectorEntity(
            connector_adapter="azure_openai_adapter",
            model="gpt-4",
            model_endpoint="https://myorg.openai.azure.com/openai/deployments/gpt-4/chat/completions",
            params={
                "api_key": "...",
                "api_version": "2023-07-01-preview",
                "deployment_name": "gpt-4",
                "temperature": 0.3,
                "max_tokens": 1500
            }
        )

        # Assert all configurations are valid
        assert openai_entity.connector_adapter == "openai_adapter"
        assert bedrock_entity.model == "anthropic.claude-3-haiku-20240307-v1:0"
        assert azure_entity.params["api_version"] == "2023-07-01-preview" 