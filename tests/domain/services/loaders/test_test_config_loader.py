import pytest
from unittest.mock import patch, MagicMock
from domain.services.loader.loader_types.test_config_loader import TestConfigLoader
from domain.entities.test_config_entity import TestConfigEntity
from domain.ports.storage_provider_port import StorageProviderPort
from domain.services.enums.test_types import TestTypes

@pytest.mark.parametrize("file_name, file_content, expected_entities, expected_exception", [
    (
        'valid_test_config.yaml',
        """
        test_key:
          - name: hallucination
            type: scan
            attack_module:
              name: hallucination
              params:
                max_prompts: 2
                use_case: |
                    This is a gaming chatbot. It will answer the top-selling games in US and Asia. It will give advice on what is the best
                    game to play based on the user preference.
                qns_type: MCQ
            metric:
              name: refusal_adapter
        """,
        {'test_key': [TestConfigEntity(
            name='hallucination',
            type='scan',  # Assuming 'scan' is a valid type in your TestTypes enum or similar construct
            attack_module={
                'name': 'hallucination',
                'params': {
                    'max_prompts': 2,
                    'use_case': "This is a gaming chatbot. It will answer the top-selling games in US and Asia. It will give advice on what is the best game to play based on the user preference.",
                    'qns_type': 'MCQ'
                }
            },
            dataset='',  # Assuming dataset is optional or not used in this context
            metric={'name': 'refusal_adapter'},
            prompt=''  # Assuming prompt is optional or not used in this context
        )]},
        None
    ),
    (
        'non_existent_file.yaml',
        None,
        None,
        FileNotFoundError
    ),
    (
        'invalid_content.yaml',
        "invalid content",
        None,
        Exception
    ),
])
@patch('domain.services.loader.factory.file_format_factory.FileFormatFactory.get_adapter')
def test_test_config_loader_load(mock_get_adapter, file_name, file_content, expected_entities, expected_exception):
    # Mock the storage adapter
    mock_storage_adapter = MagicMock(spec=StorageProviderPort)
    mock_storage_adapter.exists.return_value = file_content is not None
    mock_storage_adapter.read_file.return_value = file_content

    # Initialize the TestConfigLoader with the mock storage adapter
    loader = TestConfigLoader(mock_storage_adapter)

    if expected_exception:
        with pytest.raises(expected_exception):
            loader.load(file_name)
    else:
        # Mock the file format adapter
        mock_file_format_adapter = MagicMock()
        mock_file_format_adapter.deserialize.return_value = {
            "test_key": [
                {
                    "name": "hallucination",
                    "type": "scan",
                    "attack_module": {
                        "name": "hallucination",
                        "params": {
                            "max_prompts": 2,
                            "use_case": "This is a gaming chatbot. It will answer the top-selling games in US and Asia. It will give advice on what is the best game to play based on the user preference.",
                            "qns_type": "MCQ"
                        }
                    },
                    "metric": {
                        "name": "refusal_adapter"
                    }
                }
            ]
        }
        mock_get_adapter.return_value = mock_file_format_adapter

        # Test loading the file
        result = loader.load(file_name)
        assert result == expected_entities