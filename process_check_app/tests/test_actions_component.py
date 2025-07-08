from unittest.mock import Mock, mock_open, patch

import pytest
from backend.actions_components.actions_component import (
    create_actions_component,
    create_actions_component_no_excel,
)


class TestActionsComponent:
    """Test collection for actions component functions."""

    @pytest.fixture
    def mock_components(self, mocker):
        """Mock streamlit components."""
        mock_component = Mock()
        mock_declare_component = mocker.patch(
            "backend.actions_components.actions_component.components.declare_component",
            return_value=mock_component,
        )
        return mock_component, mock_declare_component

    @pytest.fixture
    def mock_os_path(self, mocker):
        """Mock os.path functions."""
        mock_dirname = mocker.patch("os.path.dirname", return_value="/test/path")
        mock_join = mocker.patch("os.path.join", return_value="/test/path/index.html")
        mock_exists = mocker.patch("os.path.exists", return_value=False)
        return mock_dirname, mock_join, mock_exists

    @pytest.mark.parametrize(
        "function,args,expected_params",
        [
            # Regular component tests
            (
                create_actions_component,
                ("workspace_123", "Test App", "A test application"),
                {
                    "workspace_id": "workspace_123",
                    "app_name": "Test App",
                    "app_description": "A test application",
                    "key": "actions_component",
                },
            ),
            (
                create_actions_component,
                ("", "Empty App", ""),
                {
                    "workspace_id": "",
                    "app_name": "Empty App",
                    "app_description": "",
                    "key": "actions_component",
                },
            ),
            (
                create_actions_component,
                (
                    "special_chars_!@#",
                    "App with Special Chars",
                    "Description with émojis 🚀",
                ),
                {
                    "workspace_id": "special_chars_!@#",
                    "app_name": "App with Special Chars",
                    "app_description": "Description with émojis 🚀",
                    "key": "actions_component",
                },
            ),
            # No-excel component tests
            (
                create_actions_component_no_excel,
                ("workspace_456", "Test Company", "Test App", "A test application"),
                {
                    "workspace_id": "workspace_456",
                    "company_name": "Test Company",
                    "app_name": "Test App",
                    "app_description": "A test application",
                    "key": "actions_component",
                },
            ),
            (
                create_actions_component_no_excel,
                ("", "Empty Company", "Empty App", ""),
                {
                    "workspace_id": "",
                    "company_name": "Empty Company",
                    "app_name": "Empty App",
                    "app_description": "",
                    "key": "actions_component",
                },
            ),
            (
                create_actions_component_no_excel,
                (
                    "unicode_测试",
                    "Unicode Company 测试",
                    "Unicode App 测试",
                    "Unicode description 测试",
                ),
                {
                    "workspace_id": "unicode_测试",
                    "company_name": "Unicode Company 测试",
                    "app_name": "Unicode App 测试",
                    "app_description": "Unicode description 测试",
                    "key": "actions_component",
                },
            ),
        ],
    )
    def test_create_actions_component_success(
        self, mock_components, mock_os_path, function, args, expected_params
    ):
        """Test successful creation of actions components with various inputs."""
        mock_component, mock_declare_component = mock_components

        # Mock file operations
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            result = function(*args)

        # Verify component was declared correctly
        mock_declare_component.assert_called_once_with(
            "actions_component", path="/test/path"
        )

        # Verify component was called with correct parameters
        mock_component.assert_called_once_with(**expected_params)

        # Verify result is the component return value
        assert result == mock_component.return_value

        # Verify file operations
        mock_file.assert_called_once_with("/test/path/index.html", "w")
        mock_file().write.assert_called_once()

    @pytest.mark.parametrize(
        "function,args,expected_error",
        [
            # Invalid workspace_id
            (
                create_actions_component,
                (None, "Test App", "Test Description"),
                TypeError,
            ),
            (
                create_actions_component,
                (123, "Test App", "Test Description"),
                TypeError,
            ),
            (
                create_actions_component_no_excel,
                (None, "Test Company", "Test App", "Test Description"),
                TypeError,
            ),
            (
                create_actions_component_no_excel,
                (123, "Test Company", "Test App", "Test Description"),
                TypeError,
            ),
            # Invalid app_name
            (
                create_actions_component,
                ("workspace_id", None, "Test Description"),
                TypeError,
            ),
            (
                create_actions_component,
                ("workspace_id", 123, "Test Description"),
                TypeError,
            ),
            (
                create_actions_component_no_excel,
                ("workspace_id", "Test Company", None, "Test Description"),
                TypeError,
            ),
            (
                create_actions_component_no_excel,
                ("workspace_id", "Test Company", 123, "Test Description"),
                TypeError,
            ),
            # Invalid app_description
            (create_actions_component, ("workspace_id", "Test App", None), TypeError),
            (create_actions_component, ("workspace_id", "Test App", 123), TypeError),
            (
                create_actions_component_no_excel,
                ("workspace_id", "Test Company", "Test App", None),
                TypeError,
            ),
            (
                create_actions_component_no_excel,
                ("workspace_id", "Test Company", "Test App", 123),
                TypeError,
            ),
            # Invalid company_name (only for no-excel version)
            (
                create_actions_component_no_excel,
                ("workspace_id", None, "Test App", "Test Description"),
                TypeError,
            ),
            (
                create_actions_component_no_excel,
                ("workspace_id", 123, "Test App", "Test Description"),
                TypeError,
            ),
        ],
    )
    def test_create_actions_component_invalid_inputs(
        self, mock_components, mock_os_path, function, args, expected_error
    ):
        """Test that invalid input types raise appropriate errors."""
        mock_component, mock_declare_component = mock_components

        with pytest.raises(expected_error):
            function(*args)

    @pytest.mark.parametrize(
        "function,args,expected_params,html_file",
        [
            # Regular component test
            (
                create_actions_component,
                ("workspace_123", "Test App", "A test application"),
                {
                    "workspace_id": "workspace_123",
                    "app_name": "Test App",
                    "app_description": "A test application",
                    "key": "actions_component",
                },
                "process_check_app/tests/assets/actions_component.html",
            ),
            # No-excel component test
            (
                create_actions_component_no_excel,
                ("workspace_456", "Test Company", "Test App", "A test application"),
                {
                    "workspace_id": "workspace_456",
                    "company_name": "Test Company",
                    "app_name": "Test App",
                    "app_description": "A test application",
                    "key": "actions_component",
                },
                "process_check_app/tests/assets/actions_component_no_excel.html",
            ),
        ],
    )
    def test_create_actions_component_file_exists_same_content(
        self, mock_components, mock_os_path, function, args, expected_params, html_file
    ):
        """Test when HTML file exists with same content - should not write file."""
        mock_component, mock_declare_component = mock_components
        mock_dirname, mock_join, mock_exists = mock_os_path

        # Mock os.path.exists to return True (file exists)
        mock_exists.return_value = True

        # Mock file operations - simulate existing file with same content
        # Read the actual HTML content from the appropriate test file
        with open(html_file, "r") as f:
            actual_html_content = f.read()

        mock_file = mock_open(read_data=actual_html_content)
        with patch("builtins.open", mock_file):
            result = function(*args)

        # Verify component was declared correctly
        mock_declare_component.assert_called_once_with(
            "actions_component", path="/test/path"
        )

        # Verify component was called with correct parameters
        mock_component.assert_called_once_with(**expected_params)

        # Verify result is the component return value
        assert result == mock_component.return_value

        # Verify file operations - should only read existing file, not write (since content is same)
        assert mock_file.call_count == 1

        # Verify no write operation occurred since content was identical
        mock_file().read.assert_called_once()
        mock_file().write.assert_not_called()

    @pytest.mark.parametrize(
        "function,args,expected_params,html_file",
        [
            # Regular component test
            (
                create_actions_component,
                ("workspace_123", "Test App", "A test application"),
                {
                    "workspace_id": "workspace_123",
                    "app_name": "Test App",
                    "app_description": "A test application",
                    "key": "actions_component",
                },
                "process_check_app/tests/assets/actions_component.html",
            ),
            # No-excel component test
            (
                create_actions_component_no_excel,
                ("workspace_456", "Test Company", "Test App", "A test application"),
                {
                    "workspace_id": "workspace_456",
                    "company_name": "Test Company",
                    "app_name": "Test App",
                    "app_description": "A test application",
                    "key": "actions_component",
                },
                "process_check_app/tests/assets/actions_component_no_excel.html",
            ),
        ],
    )
    def test_create_actions_component_file_exists_different_content(
        self, mock_components, mock_os_path, function, args, expected_params, html_file
    ):
        """Test when HTML file exists with different content - should write file."""
        mock_component, mock_declare_component = mock_components
        mock_dirname, mock_join, mock_exists = mock_os_path

        # Mock os.path.exists to return True (file exists)
        mock_exists.return_value = True

        # Mock file operations - simulate existing file with different content
        # Read the actual HTML content from the appropriate test file and modify it to be different
        with open(html_file, "r") as f:
            actual_html_content = f.read()

        # Create different content by modifying the actual HTML
        different_html_content = actual_html_content.replace(
            "Application Name", "Different Application Name"
        )

        mock_file = mock_open(read_data=different_html_content)
        with patch("builtins.open", mock_file):
            result = function(*args)

        # Verify component was declared correctly
        mock_declare_component.assert_called_once_with(
            "actions_component", path="/test/path"
        )

        # Verify component was called with correct parameters
        mock_component.assert_called_once_with(**expected_params)

        # Verify result is the component return value
        assert result == mock_component.return_value

        # Verify file operations - should read existing file and write new content
        # First call: read existing file
        # Second call: write new file (since content is different)
        assert mock_file.call_count == 2
        mock_file.assert_any_call("/test/path/index.html", "r")
        mock_file.assert_any_call("/test/path/index.html", "w")
        mock_file().read.assert_called_once()
        mock_file().write.assert_called_once()

    def test_create_actions_component_default_parameters(
        self, mock_components, mock_os_path
    ):
        """Test create_actions_component with default parameters."""
        mock_component, mock_declare_component = mock_components

        # Mock file operations
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            result = create_actions_component(
                "test_workspace", "Test App", "A test application"
            )

        # Verify component was declared correctly
        mock_declare_component.assert_called_once_with(
            "actions_component", path="/test/path"
        )

        # Verify component was called with default parameters
        mock_component.assert_called_once_with(
            workspace_id="test_workspace",
            app_name="Test App",
            app_description="A test application",
            key="actions_component",  # Default value
        )

        # Verify result is the component return value
        assert result == mock_component.return_value
