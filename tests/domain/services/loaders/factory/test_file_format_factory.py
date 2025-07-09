import pytest
from unittest.mock import Mock, patch, MagicMock, call
import os
from typing import Any

from domain.ports.file_format_port import FileFormatPort
from domain.services.loader.factory.file_format_factory import FileFormatFactory


class TestFileFormatFactory:
    """Test class for FileFormatFactory"""

    def setup_method(self):
        """Setup method to reset factory state before each test"""
        # Reset the factory state before each test
        FileFormatFactory._adapters = []
        FileFormatFactory._fallback_adapter = None

    @pytest.fixture
    def mock_json_adapter(self):
        """Create a mock JsonAdapter for testing"""
        class MockJsonAdapter(FileFormatPort):
            def __init__(self):
                pass
            
            @staticmethod
            def supports(path: str) -> bool:
                return path.endswith('.json')
            
            def serialize(self, data: Any) -> str | None:
                return '{"test": "data"}'
            
            def deserialize(self, content: str) -> Any:
                return {"test": "data"}
        
        MockJsonAdapter.__name__ = "JsonAdapter"
        return MockJsonAdapter

    @pytest.fixture
    def mock_yaml_adapter(self):
        """Create a mock YamlAdapter for testing"""
        class MockYamlAdapter(FileFormatPort):
            def __init__(self):
                pass
            
            @staticmethod
            def supports(path: str) -> bool:
                return path.endswith('.yaml') or path.endswith('.yml')
            
            def serialize(self, data: Any) -> str | None:
                return 'test: data'
            
            def deserialize(self, content: str) -> Any:
                return {"test": "data"}
        
        MockYamlAdapter.__name__ = "YamlAdapter"
        return MockYamlAdapter

    @pytest.fixture
    def mock_custom_adapter(self):
        """Create a mock custom adapter for testing"""
        class MockCustomAdapter(FileFormatPort):
            def __init__(self):
                pass
            
            @staticmethod
            def supports(path: str) -> bool:
                return path.endswith('.custom')
            
            def serialize(self, data: Any) -> str | None:
                return 'custom data'
            
            def deserialize(self, content: str) -> Any:
                return {"custom": "data"}
        
        MockCustomAdapter.__name__ = "CustomAdapter"
        return MockCustomAdapter

    @pytest.fixture
    def invalid_adapter(self):
        """Create an invalid adapter that doesn't inherit from FileFormatPort"""
        class InvalidAdapter:
            def __init__(self):
                pass
        
        InvalidAdapter.__name__ = "InvalidAdapter"
        return InvalidAdapter

    def test_class_attributes_initialization(self):
        """Test that class attributes are properly initialized"""
        # Assert
        assert FileFormatFactory._adapters == []
        assert FileFormatFactory._fallback_adapter_name == "JsonAdapter"
        assert FileFormatFactory._fallback_adapter is None

    def test_class_constants(self):
        """Test that class constants are properly defined"""
        # Assert
        assert hasattr(FileFormatFactory, 'INFO_REGISTER_ADAPTER')
        assert hasattr(FileFormatFactory, 'WARNING_NO_ADAPTER_FOUND')
        assert hasattr(FileFormatFactory, 'ERROR_NO_FALLBACK_ADAPTER')
        assert hasattr(FileFormatFactory, 'ERROR_INVALID_ADAPTER')
        assert hasattr(FileFormatFactory, 'INFO_DETECTED_ADAPTER')
        assert hasattr(FileFormatFactory, 'ERROR_DISCOVER_ADAPTER')
        assert hasattr(FileFormatFactory, 'INFO_SET_FALLBACK_ADAPTER')
        assert hasattr(FileFormatFactory, 'ERROR_GETTING_ADAPTER')
        assert hasattr(FileFormatFactory, 'ERROR_INITIAL_DISCOVERY')

    @patch('domain.services.loader.factory.file_format_factory.logger')
    def test_register_adapter_valid(self, mock_logger, mock_json_adapter):
        """Test registering a valid adapter"""
        # Act
        FileFormatFactory.register_adapter(mock_json_adapter)

        # Assert
        assert mock_json_adapter in FileFormatFactory._adapters
        mock_logger.info.assert_called_once_with(
            FileFormatFactory.INFO_REGISTER_ADAPTER.format(adapter_cls="JsonAdapter")
        )

    @patch('domain.services.loader.factory.file_format_factory.logger')
    def test_register_adapter_invalid(self, mock_logger, invalid_adapter):
        """Test registering an invalid adapter raises TypeError"""
        # Act & Assert
        with pytest.raises(TypeError) as exc_info:
            FileFormatFactory.register_adapter(invalid_adapter)
        
        assert FileFormatFactory.ERROR_INVALID_ADAPTER.format(
            adapter_cls="InvalidAdapter"
        ) in str(exc_info.value)
        assert invalid_adapter not in FileFormatFactory._adapters

    @pytest.mark.parametrize("adapter_count", [1, 2, 3, 3])
    def test_register_multiple_adapters(self, mock_json_adapter, mock_yaml_adapter, 
                                      mock_custom_adapter, adapter_count):
        """Test registering multiple adapters"""
        # Arrange
        adapters = [mock_json_adapter, mock_yaml_adapter, mock_custom_adapter]
        selected_adapters = adapters[:adapter_count]

        # Act
        for adapter in selected_adapters:
            FileFormatFactory.register_adapter(adapter)

        # Assert
        print(FileFormatFactory._adapters)
        assert len(FileFormatFactory._adapters) == adapter_count
        for adapter in selected_adapters:
            assert adapter in FileFormatFactory._adapters

    @patch('domain.services.loader.factory.file_format_factory.os.listdir')
    @patch('domain.services.loader.factory.file_format_factory.get_instance')
    @patch('domain.services.loader.factory.file_format_factory.AppConfig')
    @patch('domain.services.loader.factory.file_format_factory.logger')
    def test_discover_adapters_success(self, mock_logger, mock_app_config, 
                                     mock_get_instance, mock_listdir, mock_json_adapter):
        """Test successful adapter discovery"""
        # Arrange
        mock_app_config.DEFAULT_ADAPTERS_PATH = "/test/adapters"
        mock_listdir.return_value = ["json_adapter.py", "yaml_adapter.py", "__init__.py", "not_adapter.txt"]
        
        mock_instance = mock_json_adapter()
        mock_get_instance.return_value = mock_instance

        # Act
        FileFormatFactory.discover_adapters()

        # Assert
        assert mock_json_adapter in FileFormatFactory._adapters
        assert FileFormatFactory._fallback_adapter == mock_json_adapter
        
        expected_calls = [
            call("json_adapter", "/test/adapters/file_format/json_adapter.py"),
            call("yaml_adapter", "/test/adapters/file_format/yaml_adapter.py"),
            call("__init__", "/test/adapters/file_format/__init__.py")
        ]
        mock_get_instance.assert_has_calls(expected_calls, any_order=True)
        
        mock_logger.info.assert_any_call(
            FileFormatFactory.INFO_DETECTED_ADAPTER.format(adapter_cls="JsonAdapter")
        )
        mock_logger.info.assert_any_call(FileFormatFactory.INFO_SET_FALLBACK_ADAPTER)

    @patch('domain.services.loader.factory.file_format_factory.os.listdir')
    @patch('domain.services.loader.factory.file_format_factory.get_instance')
    @patch('domain.services.loader.factory.file_format_factory.AppConfig')
    @patch('domain.services.loader.factory.file_format_factory.logger')
    def test_discover_adapters_with_errors(self, mock_logger, mock_app_config, 
                                         mock_get_instance, mock_listdir):
        """Test adapter discovery with errors during instantiation"""
        # Arrange
        mock_app_config.DEFAULT_ADAPTERS_PATH = "/test/adapters"
        mock_listdir.return_value = ["error_adapter.py", "valid_adapter.py"]
        
        def get_instance_side_effect(module_name, path):
            if "error_adapter" in path:
                raise Exception("Failed to load module")
            return None
        
        mock_get_instance.side_effect = get_instance_side_effect

        # Act
        FileFormatFactory.discover_adapters()

        # Assert
        mock_logger.error.assert_called_with(
            FileFormatFactory.ERROR_DISCOVER_ADAPTER.format(error="Failed to load module")
        )

    @patch('domain.services.loader.factory.file_format_factory.os.listdir')
    @patch('domain.services.loader.factory.file_format_factory.AppConfig')
    def test_discover_adapters_empty_directory(self, mock_app_config, mock_listdir):
        """Test adapter discovery with empty directory"""
        # Arrange
        mock_app_config.DEFAULT_ADAPTERS_PATH = "/test/adapters"
        mock_listdir.return_value = []

        # Act
        FileFormatFactory.discover_adapters()

        # Assert
        assert len(FileFormatFactory._adapters) == 0

    @patch('domain.services.loader.factory.file_format_factory.os.listdir')
    @patch('domain.services.loader.factory.file_format_factory.AppConfig')
    def test_discover_adapters_no_python_files(self, mock_app_config, mock_listdir):
        """Test adapter discovery with no Python files"""
        # Arrange
        mock_app_config.DEFAULT_ADAPTERS_PATH = "/test/adapters"
        mock_listdir.return_value = ["readme.txt", "config.yaml", "data.json"]

        # Act
        FileFormatFactory.discover_adapters()

        # Assert
        assert len(FileFormatFactory._adapters) == 0

    @patch('domain.services.loader.factory.file_format_factory.os.listdir')
    @patch('domain.services.loader.factory.file_format_factory.get_instance')
    @patch('domain.services.loader.factory.file_format_factory.AppConfig')
    def test_discover_adapters_non_fileformat_instances(self, mock_app_config, 
                                                       mock_get_instance, mock_listdir):
        """Test discovery ignores instances that don't inherit from FileFormatPort"""
        # Arrange
        mock_app_config.DEFAULT_ADAPTERS_PATH = "/test/adapters"
        mock_listdir.return_value = ["non_adapter.py"]
        
        class NonFileFormatClass:
            pass
        
        mock_instance = NonFileFormatClass()
        mock_get_instance.return_value = mock_instance

        # Act
        FileFormatFactory.discover_adapters()

        # Assert
        assert len(FileFormatFactory._adapters) == 0

    @pytest.mark.parametrize("path,expected_adapter", [
        ("test.json", "JsonAdapter"),
        ("data.yaml", "YamlAdapter"), 
        ("config.yml", "YamlAdapter"),
        ("custom.custom", "CustomAdapter")
    ])
    def test_get_adapter_with_registered_adapters(self, path, expected_adapter,
                                                 mock_json_adapter, mock_yaml_adapter, 
                                                 mock_custom_adapter):
        """Test getting adapter for different file types"""
        # Arrange
        FileFormatFactory.register_adapter(mock_json_adapter)
        FileFormatFactory.register_adapter(mock_yaml_adapter)
        FileFormatFactory.register_adapter(mock_custom_adapter)
        FileFormatFactory._fallback_adapter = mock_json_adapter

        # Act
        adapter = FileFormatFactory.get_adapter(path)

        # Assert
        assert adapter.__class__.__name__ == expected_adapter

    @patch('domain.services.loader.factory.file_format_factory.logger')
    def test_get_adapter_fallback_to_json(self, mock_logger, mock_json_adapter):
        """Test falling back to JsonAdapter when no specific adapter supports the path"""
        # Arrange
        FileFormatFactory.register_adapter(mock_json_adapter)
        FileFormatFactory._fallback_adapter = mock_json_adapter
        path = "unsupported.xyz"

        # Act
        adapter = FileFormatFactory.get_adapter(path)

        # Assert
        assert adapter.__class__.__name__ == "JsonAdapter"
        mock_logger.warning.assert_called_once_with(
            FileFormatFactory.WARNING_NO_ADAPTER_FOUND.format(path=path)
        )

    @patch('domain.services.loader.factory.file_format_factory.logger')
    def test_get_adapter_no_fallback_raises_error(self, mock_logger):
        """Test that RuntimeError is raised when no fallback adapter is set"""
        # Arrange
        FileFormatFactory._adapters = []  # Clear adapters to prevent auto-discovery
        FileFormatFactory._fallback_adapter = None
        path = "test.unknown"

        # Mock discover_adapters to prevent it from setting a fallback adapter
        with patch.object(FileFormatFactory, 'discover_adapters'):
            # Act & Assert
            with pytest.raises(RuntimeError) as exc_info:
                FileFormatFactory.get_adapter(path)
            
            assert FileFormatFactory.ERROR_NO_FALLBACK_ADAPTER in str(exc_info.value)

    @patch('domain.services.loader.factory.file_format_factory.FileFormatFactory.discover_adapters')
    @patch('domain.services.loader.factory.file_format_factory.logger')
    def test_get_adapter_auto_discovery(self, mock_logger, mock_discover, mock_json_adapter):
        """Test that adapters are auto-discovered when _adapters is empty"""
        # Arrange
        FileFormatFactory._adapters = []
        FileFormatFactory._fallback_adapter = mock_json_adapter
        path = "test.json"

        def side_effect():
            FileFormatFactory._adapters = [mock_json_adapter]

        mock_discover.side_effect = side_effect

        # Act
        adapter = FileFormatFactory.get_adapter(path)

        # Assert
        mock_discover.assert_called_once()
        assert adapter.__class__.__name__ == "JsonAdapter"

    @patch('domain.services.loader.factory.file_format_factory.logger')
    def test_get_adapter_exception_handling(self, mock_logger, mock_json_adapter):
        """Test exception handling in get_adapter method"""
        # Arrange
        FileFormatFactory._adapters = [mock_json_adapter]
        FileFormatFactory._fallback_adapter = mock_json_adapter
        path = "test.json"

        # Mock the supports method to raise an exception
        with patch.object(mock_json_adapter, 'supports', side_effect=Exception("Adapter error")):
            # Act & Assert
            with pytest.raises(Exception):
                FileFormatFactory.get_adapter(path)
            
            mock_logger.error.assert_called_with(
                FileFormatFactory.ERROR_GETTING_ADAPTER.format(path=path, error="Adapter error")
            )

    @pytest.mark.parametrize("adapter_name,should_set_fallback", [
        ("JsonAdapter", True),
        ("YamlAdapter", False),
        ("CustomAdapter", False)
    ])
    @patch('domain.services.loader.factory.file_format_factory.os.listdir')
    @patch('domain.services.loader.factory.file_format_factory.get_instance')
    @patch('domain.services.loader.factory.file_format_factory.AppConfig')
    @patch('domain.services.loader.factory.file_format_factory.logger')
    def test_discover_sets_fallback_adapter(self, mock_logger, mock_app_config, 
                                          mock_get_instance, mock_listdir,
                                          adapter_name, should_set_fallback):
        """Test that fallback adapter is set correctly during discovery"""
        # Arrange
        mock_app_config.DEFAULT_ADAPTERS_PATH = "/test/adapters"
        mock_listdir.return_value = ["test_adapter.py"]

        class MockAdapter(FileFormatPort):
            def __init__(self):
                pass
            def supports(self, path: str) -> bool:
                return True
            def serialize(self, data: Any) -> str | None:
                return ""
            def deserialize(self, content: str) -> Any:
                return {}

        MockAdapter.__name__ = adapter_name
        mock_instance = MockAdapter()
        mock_get_instance.return_value = mock_instance

        # Act
        FileFormatFactory.discover_adapters()

        # Assert
        if should_set_fallback:
            assert FileFormatFactory._fallback_adapter == MockAdapter
            mock_logger.info.assert_any_call(FileFormatFactory.INFO_SET_FALLBACK_ADAPTER)
        else:
            assert FileFormatFactory._fallback_adapter is None

    def test_adapter_supports_method_called_correctly(self, mock_json_adapter, mock_yaml_adapter):
        """Test that the supports method is called correctly for each adapter"""
        # Arrange
        FileFormatFactory.register_adapter(mock_json_adapter)
        FileFormatFactory.register_adapter(mock_yaml_adapter)
        FileFormatFactory._fallback_adapter = mock_json_adapter
        path = "test.yaml"

        with patch.object(mock_json_adapter, 'supports', return_value=False) as mock_json_supports, \
             patch.object(mock_yaml_adapter, 'supports', return_value=True) as mock_yaml_supports:
            
            # Act
            adapter = FileFormatFactory.get_adapter(path)

            # Assert
            mock_json_supports.assert_called_once_with(path)
            mock_yaml_supports.assert_called_once_with(path)
            assert adapter.__class__.__name__ == "YamlAdapter"

    def test_adapter_without_supports_method(self, mock_json_adapter):
        """Test handling of adapters without supports method"""
        # Arrange
        class AdapterWithoutSupports(FileFormatPort):
            def __init__(self):
                pass
            def serialize(self, data: Any) -> str | None:
                return ""
            def deserialize(self, content: str) -> Any:
                return {}
        
        AdapterWithoutSupports.__name__ = "AdapterWithoutSupports"
        
        FileFormatFactory.register_adapter(AdapterWithoutSupports)
        FileFormatFactory.register_adapter(mock_json_adapter)
        FileFormatFactory._fallback_adapter = mock_json_adapter
        path = "test.json"

        # Act
        adapter = FileFormatFactory.get_adapter(path)

        # Assert - should fall back to JsonAdapter since AdapterWithoutSupports has no supports method
        assert adapter.__class__.__name__ == "JsonAdapter"

    @pytest.mark.parametrize("path", [
        "",  # Empty path
        "file_without_extension",  # No extension
        "file.with.multiple.dots.json",  # Multiple dots
        "/absolute/path/file.json",  # Absolute path
        "relative/path/file.yaml",  # Relative path
        "file with spaces.json",  # Spaces in filename
        "file-with-dashes.yaml",  # Dashes in filename
        "file_with_underscores.json",  # Underscores
        "UPPERCASE.JSON",  # Uppercase extension
        "mixed.Case.Json",  # Mixed case
        "unicode_测试.json",  # Unicode characters
        "🚀🔥💯.yaml",  # Emojis
        "very_long_filename_that_exceeds_normal_expectations.json",  # Very long filename
    ])
    def test_get_adapter_edge_case_paths(self, path, mock_json_adapter):
        """Test get_adapter with various edge case paths"""
        # Arrange
        FileFormatFactory.register_adapter(mock_json_adapter)
        FileFormatFactory._fallback_adapter = mock_json_adapter

        # Act
        adapter = FileFormatFactory.get_adapter(path)

        # Assert
        assert isinstance(adapter, FileFormatPort)
        # Should either find a supporting adapter or fall back to JsonAdapter
        assert adapter.__class__.__name__ == "JsonAdapter"

    @patch('domain.services.loader.factory.file_format_factory.os.listdir')
    @patch('domain.services.loader.factory.file_format_factory.AppConfig')
    @patch('domain.services.loader.factory.file_format_factory.logger')
    def test_discover_adapters_os_error(self, mock_logger, mock_app_config, mock_listdir):
        """Test discover_adapters handles OS errors gracefully"""
        # Arrange
        mock_app_config.DEFAULT_ADAPTERS_PATH = "/nonexistent/path"
        mock_listdir.side_effect = OSError("Directory not found")

        # Act & Assert
        with pytest.raises(OSError):
            FileFormatFactory.discover_adapters()

    def test_register_same_adapter_multiple_times(self, mock_json_adapter):
        """Test registering the same adapter multiple times"""
        # Arrange & Act
        FileFormatFactory.register_adapter(mock_json_adapter)
        FileFormatFactory.register_adapter(mock_json_adapter)
        FileFormatFactory.register_adapter(mock_json_adapter)

        # Assert
        assert FileFormatFactory._adapters.count(mock_json_adapter) == 3

    def test_get_adapter_returns_new_instance(self, mock_json_adapter):
        """Test that get_adapter returns a new instance each time"""
        # Arrange
        FileFormatFactory.register_adapter(mock_json_adapter)
        FileFormatFactory._fallback_adapter = mock_json_adapter
        path = "test.json"

        # Act
        adapter1 = FileFormatFactory.get_adapter(path)
        adapter2 = FileFormatFactory.get_adapter(path)

        # Assert
        assert adapter1 is not adapter2  # Different instances
        assert type(adapter1) == type(adapter2)  # Same type

    @patch('domain.services.loader.factory.file_format_factory.get_instance')
    @patch('domain.services.loader.factory.file_format_factory.os.listdir')
    @patch('domain.services.loader.factory.file_format_factory.AppConfig')
    def test_discover_adapters_get_instance_returns_none(self, mock_app_config, 
                                                        mock_listdir, mock_get_instance):
        """Test discover_adapters when get_instance returns None"""
        # Arrange
        mock_app_config.DEFAULT_ADAPTERS_PATH = "/test/adapters"
        mock_listdir.return_value = ["none_adapter.py"]
        mock_get_instance.return_value = None

        # Act
        FileFormatFactory.discover_adapters()

        # Assert
        assert len(FileFormatFactory._adapters) == 0

    @patch('domain.services.loader.factory.file_format_factory.logger')
    def test_get_adapter_supports_method_exception(self, mock_logger, mock_json_adapter):
        """Test handling when supports method raises an exception"""
        # Arrange
        FileFormatFactory.register_adapter(mock_json_adapter)
        FileFormatFactory._fallback_adapter = mock_json_adapter
        path = "test.json"

        # Mock supports to raise exception for the first call, work normally for fallback
        def supports_side_effect(path_arg):
            if supports_side_effect.call_count == 1:
                supports_side_effect.call_count += 1
                raise Exception("Supports method error")
            return True

        supports_side_effect.call_count = 1

        with patch.object(mock_json_adapter, 'supports', side_effect=supports_side_effect):
            # Act & Assert
            with pytest.raises(Exception):
                FileFormatFactory.get_adapter(path)

    def test_factory_state_isolation(self, mock_json_adapter, mock_yaml_adapter):
        """Test that factory state changes don't affect other tests"""
        # Arrange
        initial_adapters_count = len(FileFormatFactory._adapters)
        
        # Act
        FileFormatFactory.register_adapter(mock_json_adapter)
        FileFormatFactory.register_adapter(mock_yaml_adapter)
        
        # Verify state changed
        assert len(FileFormatFactory._adapters) == initial_adapters_count + 2
        
        # Reset state (simulating teardown)
        FileFormatFactory._adapters = []
        FileFormatFactory._fallback_adapter = None
        
        # Assert state is reset
        assert len(FileFormatFactory._adapters) == 0
        assert FileFormatFactory._fallback_adapter is None

    def test_docstring_and_class_description(self):
        """Test that the class has proper documentation"""
        # Assert
        assert FileFormatFactory.__doc__ is not None
        assert "factory" in FileFormatFactory.__doc__.lower()
        assert "adapter" in FileFormatFactory.__doc__.lower()

    @pytest.mark.parametrize("exception_type", [
        ValueError,
        RuntimeError, 
        TypeError,
        OSError,
        AttributeError,
        ImportError
    ])
    @patch('domain.services.loader.factory.file_format_factory.get_instance')
    @patch('domain.services.loader.factory.file_format_factory.os.listdir')
    @patch('domain.services.loader.factory.file_format_factory.AppConfig')
    @patch('domain.services.loader.factory.file_format_factory.logger')
    def test_discover_adapters_various_exceptions(self, mock_logger, mock_app_config, 
                                                 mock_listdir, mock_get_instance, exception_type):
        """Test discover_adapters handles various exception types"""
        # Arrange
        mock_app_config.DEFAULT_ADAPTERS_PATH = "/test/adapters"
        mock_listdir.return_value = ["error_adapter.py"]
        mock_get_instance.side_effect = exception_type("Test error")

        # Act
        FileFormatFactory.discover_adapters()

        # Assert
        mock_logger.error.assert_called_with(
            FileFormatFactory.ERROR_DISCOVER_ADAPTER.format(error="Test error")
        )

    def test_adapter_priority_order(self, mock_json_adapter, mock_yaml_adapter, mock_custom_adapter):
        """Test that adapters are checked in registration order"""
        # Arrange
        FileFormatFactory.register_adapter(mock_yaml_adapter)  # Register first
        FileFormatFactory.register_adapter(mock_json_adapter)  # Register second
        FileFormatFactory.register_adapter(mock_custom_adapter)  # Register third
        FileFormatFactory._fallback_adapter = mock_json_adapter

        # Create a file that could match multiple adapters
        # Mock both adapters to support the same path to test priority
        with patch.object(mock_yaml_adapter, 'supports', return_value=True), \
             patch.object(mock_json_adapter, 'supports', return_value=True), \
             patch.object(mock_custom_adapter, 'supports', return_value=True):
            
            # Act
            adapter = FileFormatFactory.get_adapter("test.json")

            # Assert - should return the first registered adapter that supports the path
            assert adapter.__class__.__name__ == "YamlAdapter"

    @patch('domain.services.loader.factory.file_format_factory.logger')
    def test_concurrent_adapter_registration(self, mock_logger, mock_json_adapter, mock_yaml_adapter):
        """Test thread safety of adapter registration (basic test)"""
        # This is a basic test - full thread safety testing would require more complex setup
        import threading
        
        def register_adapters():
            FileFormatFactory.register_adapter(mock_json_adapter)
            FileFormatFactory.register_adapter(mock_yaml_adapter)

        # Act
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=register_adapters)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Assert - all adapters should be registered (potentially multiple times)
        assert len(FileFormatFactory._adapters) == 6  # 3 threads * 2 adapters each 