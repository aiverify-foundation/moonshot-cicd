import pytest
from unittest.mock import patch, MagicMock
from domain.services.enums.module_types import ModuleTypes
from domain.services.loader.module_loader import ModuleLoader
from domain.services.loader.loader_types.attack_module_loader import (
    AttackModuleLoader,
)
from domain.services.loader.loader_types.connector_loader import ConnectorLoader
from domain.services.loader.loader_types.metric_loader import MetricLoader
from domain.services.loader.loader_types.prompt_processor_loader import (
    PromptProcessorLoader,
)

@pytest.mark.parametrize("module_name, file_type, expected_loader, expected_exception", [
    ('refusal_adapter', ModuleTypes.METRIC, MetricLoader, None),
    ('openai_adapter', ModuleTypes.CONNECTOR, ConnectorLoader, None),
    ('asyncio_prompt_processor_adapter', ModuleTypes.PROMPT_PROCESSOR, PromptProcessorLoader, None),
    ('hallucination', ModuleTypes.ATTACK_MODULE, AttackModuleLoader, None),
    ('unknown_module', 'UNKNOWN_TYPE', None, Exception),  # Test case for unknown module type
])
@patch('domain.services.loader.file_loader.StorageProviderFactory.get_adapter')
def test_module_loader_load(mock_get_adapter, module_name, file_type, expected_loader, expected_exception):
    # Mock the storage adapter
    mock_storage_adapter = MagicMock()
    mock_get_adapter.return_value = mock_storage_adapter

    if expected_exception:
        with pytest.raises(expected_exception):
            ModuleLoader.load(module_name, file_type)
    else:
        # Mock the loader
        mock_loader_instance = MagicMock()
        with patch.object(expected_loader, 'load', return_value=mock_loader_instance) as mock_load:
            # Test loading the file
            result = ModuleLoader.load(module_name, file_type)
            mock_load.assert_called_once_with(module_name)
            assert result == mock_loader_instance