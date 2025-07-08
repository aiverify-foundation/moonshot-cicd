import pytest
from pydantic import ValidationError

from domain.entities.attack_module_config_entity import AttackModuleConfigEntity
from domain.entities.connector_entity import ConnectorEntity


class TestAttackModuleConfigEntity:
    """Test class for AttackModuleConfigEntity"""

    def test_minimal_initialization(self):
        """Test AttackModuleConfigEntity with minimal required parameters"""
        # Arrange
        name = "test_attack_module"
        connector_configs = {
            "primary": ConnectorEntity(
                connector_adapter="openai_adapter",
                model="gpt-4"
            )
        }

        # Act
        entity = AttackModuleConfigEntity(
            name=name,
            connector_configurations=connector_configs
        )

        # Assert
        assert entity.name == name
        assert entity.connector_configurations == connector_configs
        assert entity.params == {}  # Default value

    def test_full_initialization(self):
        """Test AttackModuleConfigEntity with all parameters provided"""
        # Arrange
        name = "comprehensive_attack_module"
        connector_configs = {
            "primary": ConnectorEntity(
                connector_adapter="openai_adapter",
                model="gpt-4",
                model_endpoint="https://api.openai.com/v1",
                params={"temperature": 0.7, "max_tokens": 1000},
                connector_pre_prompt="Pre-prompt text",
                connector_post_prompt="Post-prompt text",
                system_prompt="System prompt text"
            ),
            "secondary": ConnectorEntity(
                connector_adapter="azure_adapter",
                model="gpt-3.5-turbo"
            )
        }
        params = {
            "threshold": 0.8,
            "iterations": 5,
            "strict_mode": True,
            "timeout": 30
        }

        # Act
        entity = AttackModuleConfigEntity(
            name=name,
            connector_configurations=connector_configs,
            params=params
        )

        # Assert
        assert entity.name == name
        assert entity.connector_configurations == connector_configs
        assert entity.params == params

    @pytest.mark.parametrize("name", [
        # Good cases - various valid name strings
        "simple_name",
        "attack-module-with-hyphens",
        "AttackModule123",
        "module_with_underscores",
        "UPPERCASE_MODULE",
        "Mixed_Case_Module",
        "module.with.dots",
        "a",  # Single character
        "very_long_attack_module_name_with_many_characters_and_descriptive_text",
        "unicode_module_名",
        "module with spaces",
        "module!@#$%^&*()",  # Special characters
    ])
    def test_valid_name_variations(self, name):
        """Test AttackModuleConfigEntity with various valid name strings"""
        # Arrange
        connector_configs = {
            "test": ConnectorEntity(
                connector_adapter="test_adapter",
                model="test_model"
            )
        }

        # Act
        entity = AttackModuleConfigEntity(
            name=name,
            connector_configurations=connector_configs
        )

        # Assert
        assert entity.name == name

    @pytest.mark.parametrize("connector_configs", [
        # Good cases - various connector configuration structures
        {
            "single": ConnectorEntity(
                connector_adapter="openai_adapter",
                model="gpt-4"
            )
        },
        {
            "primary": ConnectorEntity(
                connector_adapter="openai_adapter",
                model="gpt-4",
                params={"temperature": 0.5}
            ),
            "backup": ConnectorEntity(
                connector_adapter="azure_adapter",
                model="gpt-3.5-turbo"
            )
        },
        {
            "llm1": ConnectorEntity(
                connector_adapter="openai_adapter",
                model="gpt-4",
                model_endpoint="https://api.openai.com/v1",
                params={"temperature": 0.7, "max_tokens": 2000},
                system_prompt="You are a helpful assistant"
            ),
            "llm2": ConnectorEntity(
                connector_adapter="anthropic_adapter",
                model="claude-3",
                params={"max_tokens": 1500}
            ),
            "llm3": ConnectorEntity(
                connector_adapter="bedrock_adapter",
                model="titan-text"
            )
        },
    ])
    def test_connector_configurations_variations(self, connector_configs):
        """Test AttackModuleConfigEntity with various connector configuration structures"""
        # Act
        entity = AttackModuleConfigEntity(
            name="test_module",
            connector_configurations=connector_configs
        )

        # Assert
        assert entity.connector_configurations == connector_configs
        assert len(entity.connector_configurations) == len(connector_configs)
        for key, _ in connector_configs.items():
            assert key in entity.connector_configurations
            assert isinstance(entity.connector_configurations[key], ConnectorEntity)

    @pytest.mark.parametrize("params", [
        # Good cases - various parameter dictionary structures
        {},  # Empty dict
        {"simple": "value"},
        {"threshold": 0.8, "iterations": 10},
        {"complex": {"nested": {"deep": {"value": 42}}}},
        {
            "model_params": {
                "temperature": 0.7,
                "max_tokens": 1000,
                "top_p": 0.9
            },
            "attack_params": {
                "strategy": "jailbreak",
                "severity": "high",
                "targets": ["prompt_injection", "data_leakage"]
            },
            "flags": {
                "strict_mode": True,
                "verbose": False,
                "debug": True
            }
        },
        {"list_param": [1, 2, 3, "string", {"nested": "object"}]},
        {"mixed_types": {"int": 42, "float": 3.14, "bool": True, "null": None}},
    ])
    def test_params_field_variations(self, params):
        """Test AttackModuleConfigEntity with various params dictionary structures"""
        # Arrange
        connector_configs = {
            "test": ConnectorEntity(
                connector_adapter="test_adapter",
                model="test_model"
            )
        }

        # Act
        entity = AttackModuleConfigEntity(
            name="test_module",
            connector_configurations=connector_configs,
            params=params
        )

        # Assert
        assert entity.params == params

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
        """Test AttackModuleConfigEntity with invalid name types"""
        # Arrange
        connector_configs = {
            "test": ConnectorEntity(
                connector_adapter="test_adapter",
                model="test_model"
            )
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AttackModuleConfigEntity(
                name=name,
                connector_configurations=connector_configs
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("connector_configs,expected_error", [
        # Bad cases - invalid connector_configurations types
        (None, "Input should be a valid dictionary"),
        ("string", "Input should be a valid dictionary"),
        (123, "Input should be a valid dictionary"),
        ([], "Input should be a valid dictionary"),
        (True, "Input should be a valid dictionary"),
    ])
    def test_invalid_connector_configurations_types(self, connector_configs, expected_error):
        """Test AttackModuleConfigEntity with invalid connector_configurations types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AttackModuleConfigEntity(
                name="test_module",
                connector_configurations=connector_configs
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("params,expected_error", [
        # Bad cases - invalid params types
        ("string", "Input should be a valid dictionary"),
        (123, "Input should be a valid dictionary"),
        ([], "Input should be a valid dictionary"),
        (True, "Input should be a valid dictionary"),
        (None, "Input should be a valid dictionary"),
    ])
    def test_invalid_params_types(self, params, expected_error):
        """Test AttackModuleConfigEntity with invalid params types"""
        # Arrange
        connector_configs = {
            "test": ConnectorEntity(
                connector_adapter="test_adapter",
                model="test_model"
            )
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AttackModuleConfigEntity(
                name="test_module",
                connector_configurations=connector_configs,
                params=params
            )
        assert expected_error in str(exc_info.value)

    def test_invalid_connector_entity_in_configurations(self):
        """Test AttackModuleConfigEntity with invalid ConnectorEntity objects"""
        # Act & Assert - Invalid connector object
        with pytest.raises(ValidationError) as exc_info:
            AttackModuleConfigEntity(
                name="test_module",
                connector_configurations={
                    "invalid": "not_a_connector_entity"
                }
            )
        assert "Input should be a valid dictionary or instance of ConnectorEntity" in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test AttackModuleConfigEntity with missing required fields"""
        # Test missing name
        with pytest.raises(ValidationError) as exc_info:
            AttackModuleConfigEntity(
                connector_configurations={
                    "test": ConnectorEntity(
                        connector_adapter="test_adapter",
                        model="test_model"
                    )
                }
            )
        assert "Field required" in str(exc_info.value)

        # Test missing connector_configurations
        with pytest.raises(ValidationError) as exc_info:
            AttackModuleConfigEntity(
                name="test_module"
            )
        assert "Field required" in str(exc_info.value)

    def test_empty_connector_configurations(self):
        """Test AttackModuleConfigEntity with empty connector configurations"""
        # Act
        entity = AttackModuleConfigEntity(
            name="test_module",
            connector_configurations={}
        )

        # Assert
        assert entity.connector_configurations == {}
        assert len(entity.connector_configurations) == 0

    def test_entity_serialization(self):
        """Test AttackModuleConfigEntity serialization to dictionary"""
        # Arrange
        connector_configs = {
            "primary": ConnectorEntity(
                connector_adapter="openai_adapter",
                model="gpt-4",
                params={"temperature": 0.7}
            )
        }
        params = {"threshold": 0.8, "iterations": 5}

        entity = AttackModuleConfigEntity(
            name="serialization_test",
            connector_configurations=connector_configs,
            params=params
        )

        # Act
        entity_dict = entity.model_dump()

        # Assert
        expected_keys = ["name", "connector_configurations", "params"]
        assert all(key in entity_dict for key in expected_keys)
        assert entity_dict["name"] == "serialization_test"
        assert entity_dict["params"] == params
        assert "primary" in entity_dict["connector_configurations"]
        assert entity_dict["connector_configurations"]["primary"]["connector_adapter"] == "openai_adapter"

    def test_entity_json_serialization(self):
        """Test AttackModuleConfigEntity JSON serialization"""
        # Arrange
        connector_configs = {
            "json_test": ConnectorEntity(
                connector_adapter="json_adapter",
                model="json_model",
                system_prompt="JSON test prompt"
            )
        }
        
        entity = AttackModuleConfigEntity(
            name="json_serialization_test",
            connector_configurations=connector_configs,
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
        """Test AttackModuleConfigEntity creation from dictionary"""
        # Arrange
        entity_dict = {
            "name": "dict_test_module",
            "connector_configurations": {
                "dict_connector": {
                    "connector_adapter": "dict_adapter",
                    "model": "dict_model",
                    "model_endpoint": "",
                    "params": {},
                    "connector_pre_prompt": "",
                    "connector_post_prompt": "",
                    "system_prompt": ""
                }
            },
            "params": {"dict_param": "dict_value"}
        }

        # Act
        entity = AttackModuleConfigEntity(**entity_dict)

        # Assert
        assert entity.name == "dict_test_module"
        assert "dict_connector" in entity.connector_configurations
        assert isinstance(entity.connector_configurations["dict_connector"], ConnectorEntity)
        assert entity.connector_configurations["dict_connector"].connector_adapter == "dict_adapter"
        assert entity.params == {"dict_param": "dict_value"}

    def test_inheritance_from_basemodel(self):
        """Test that AttackModuleConfigEntity inherits from BaseModel"""
        # Arrange
        entity = AttackModuleConfigEntity(
            name="inheritance_test",
            connector_configurations={
                "test": ConnectorEntity(
                    connector_adapter="test_adapter",
                    model="test_model"
                )
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
        # This is verified by the fact that ConnectorEntity objects can be stored
        # Arrange
        connector = ConnectorEntity(
            connector_adapter="custom_adapter",
            model="custom_model"
        )

        # Act
        entity = AttackModuleConfigEntity(
            name="config_test",
            connector_configurations={"custom": connector}
        )

        # Assert
        assert entity.connector_configurations["custom"] == connector
        assert isinstance(entity.connector_configurations["custom"], ConnectorEntity)

    @pytest.mark.parametrize("field_name,new_value", [
        ("name", "updated_module_name"),
        ("params", {"updated": "params", "new_threshold": 0.9}),
    ])
    def test_field_assignment_after_initialization(self, field_name, new_value):
        """Test field assignment after entity initialization"""
        # Arrange
        entity = AttackModuleConfigEntity(
            name="original_name",
            connector_configurations={
                "original": ConnectorEntity(
                    connector_adapter="original_adapter",
                    model="original_model"
                )
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
        entity = AttackModuleConfigEntity(
            name="test_name",
            connector_configurations={
                "original": ConnectorEntity(
                    connector_adapter="original_adapter",
                    model="original_model"
                )
            }
        )

        new_configs = {
            "new_connector": ConnectorEntity(
                connector_adapter="new_adapter",
                model="new_model",
                params={"new": "param"}
            )
        }

        # Act
        entity.connector_configurations = new_configs

        # Assert
        assert entity.connector_configurations == new_configs
        assert "new_connector" in entity.connector_configurations
        assert "original" not in entity.connector_configurations

    def test_complex_nested_params_structure(self):
        """Test AttackModuleConfigEntity with complex nested params structure"""
        # Arrange
        complex_params = {
            "attack_strategy": {
                "primary": {
                    "type": "jailbreak",
                    "severity": "high",
                    "templates": [
                        {"id": 1, "name": "template1", "content": "content1"},
                        {"id": 2, "name": "template2", "content": "content2"}
                    ],
                    "config": {
                        "iterations": 10,
                        "threshold": 0.8,
                        "timeout": 30,
                        "flags": {"strict": True, "verbose": False}
                    }
                },
                "fallback": {
                    "type": "prompt_injection",
                    "severity": "medium"
                }
            },
            "model_settings": {
                "temperature": 0.7,
                "max_tokens": 2000,
                "top_p": 0.9,
                "frequency_penalty": 0.1
            },
            "metadata": {
                "version": "2.1.0",
                "author": "test_author",
                "created_at": "2024-01-01T00:00:00Z",
                "tags": ["security", "testing", "jailbreak"]
            }
        }

        connector_configs = {
            "primary": ConnectorEntity(
                connector_adapter="complex_adapter",
                model="complex_model"
            )
        }

        # Act
        entity = AttackModuleConfigEntity(
            name="complex_attack_module",
            connector_configurations=connector_configs,
            params=complex_params
        )

        # Assert
        assert entity.params == complex_params
        assert entity.params["attack_strategy"]["primary"]["config"]["iterations"] == 10
        assert entity.params["metadata"]["tags"] == ["security", "testing", "jailbreak"]

    @pytest.mark.parametrize("name,connector_count,param_keys", [
        # Edge cases - boundary conditions
        ("", 0, []),  # Empty name, no connectors, no params
        ("a", 1, ["k"]),  # Single character name, one connector, one param
        ("very_long_module_name_with_extensive_descriptive_text", 3, 
         ["very_long_parameter_name_with_descriptive_text", "another_param", "third_param"]),
    ])
    def test_edge_case_combinations(self, name, connector_count, param_keys):
        """Test AttackModuleConfigEntity with edge case combinations"""
        # Arrange
        connector_configs = {}
        for i in range(connector_count):
            connector_configs[f"connector_{i}"] = ConnectorEntity(
                connector_adapter=f"adapter_{i}",
                model=f"model_{i}"
            )

        params = {key: f"value_{key}" for key in param_keys}

        # Act
        entity = AttackModuleConfigEntity(
            name=name,
            connector_configurations=connector_configs,
            params=params
        )

        # Assert
        assert entity.name == name
        assert len(entity.connector_configurations) == connector_count
        assert entity.params == params

    def test_multiple_connector_types_in_configuration(self):
        """Test AttackModuleConfigEntity with multiple different connector types"""
        # Arrange
        connector_configs = {
            "openai_primary": ConnectorEntity(
                connector_adapter="openai_adapter",
                model="gpt-4",
                model_endpoint="https://api.openai.com/v1",
                params={"temperature": 0.7, "max_tokens": 2000},
                system_prompt="You are a helpful AI assistant"
            ),
            "azure_backup": ConnectorEntity(
                connector_adapter="azure_openai_adapter",
                model="gpt-35-turbo",
                model_endpoint="https://myazure.openai.azure.com/",
                params={"temperature": 0.5, "max_tokens": 1500},
                connector_pre_prompt="[SYSTEM]",
                connector_post_prompt="[/SYSTEM]"
            ),
            "anthropic_fallback": ConnectorEntity(
                connector_adapter="anthropic_adapter",
                model="claude-3-sonnet",
                params={"max_tokens": 1000, "temperature": 0.3}
            ),
            "local_model": ConnectorEntity(
                connector_adapter="local_adapter",
                model="llama-2-7b",
                model_endpoint="http://localhost:8080/v1",
                params={"context_length": 4096}
            )
        }

        # Act
        entity = AttackModuleConfigEntity(
            name="multi_connector_module",
            connector_configurations=connector_configs,
            params={"strategy": "multi_model_attack", "priority": "high"}
        )

        # Assert
        assert len(entity.connector_configurations) == 4
        assert all(isinstance(conn, ConnectorEntity) for conn in entity.connector_configurations.values())
        assert entity.connector_configurations["openai_primary"].model == "gpt-4"
        assert entity.connector_configurations["azure_backup"].model == "gpt-35-turbo"
        assert entity.connector_configurations["anthropic_fallback"].model == "claude-3-sonnet"
        assert entity.connector_configurations["local_model"].model == "llama-2-7b" 