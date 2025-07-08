from unittest.mock import Mock, mock_open, patch

import pytest
from backend.cards_component.cards_component import create_component


class TestCardsComponent:
    """Test collection for cards component functions."""

    @pytest.fixture
    def mock_components(self, mocker):
        """Mock streamlit components."""
        mock_component = Mock()
        mock_declare_component = mocker.patch(
            "backend.cards_component.cards_component.components.declare_component",
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
        "principles_names,principles_data,current_index,key,expected_params",
        [
            # Basic test case
            (
                ["Principle 1", "Principle 2", "Principle 3"],
                {
                    "principle_1": {"total_checks": 10, "answered_checks": 5},
                    "principle_2": {"total_checks": 8, "answered_checks": 8},
                    "principle_3": {"total_checks": 12, "answered_checks": 0},
                },
                0,
                "cards_component",
                {
                    "principles_names": ["Principle 1", "Principle 2", "Principle 3"],
                    "principles_data": {
                        "principle_1": {"total_checks": 10, "answered_checks": 5},
                        "principle_2": {"total_checks": 8, "answered_checks": 8},
                        "principle_3": {"total_checks": 12, "answered_checks": 0},
                    },
                    "current_index": 0,
                    "key": "cards_component",
                },
            ),
            # Empty data test case
            (
                [],
                {},
                0,
                "empty_cards",
                {
                    "principles_names": [],
                    "principles_data": {},
                    "current_index": 0,
                    "key": "empty_cards",
                },
            ),
            # Single principle test case
            (
                ["Single Principle"],
                {"single": {"total_checks": 5, "answered_checks": 3}},
                0,
                "single_cards",
                {
                    "principles_names": ["Single Principle"],
                    "principles_data": {
                        "single": {"total_checks": 5, "answered_checks": 3}
                    },
                    "current_index": 0,
                    "key": "single_cards",
                },
            ),
            # Non-zero current index test case
            (
                ["Principle A", "Principle B"],
                {
                    "principle_a": {"total_checks": 6, "answered_checks": 6},
                    "principle_b": {"total_checks": 4, "answered_checks": 2},
                },
                1,
                "custom_key",
                {
                    "principles_names": ["Principle A", "Principle B"],
                    "principles_data": {
                        "principle_a": {"total_checks": 6, "answered_checks": 6},
                        "principle_b": {"total_checks": 4, "answered_checks": 2},
                    },
                    "current_index": 1,
                    "key": "custom_key",
                },
            ),
            # Unicode test case
            (
                ["Principle 测试", "Principle 🚀"],
                {
                    "principle_unicode": {"total_checks": 3, "answered_checks": 1},
                    "principle_emoji": {"total_checks": 7, "answered_checks": 7},
                },
                0,
                "unicode_cards",
                {
                    "principles_names": ["Principle 测试", "Principle 🚀"],
                    "principles_data": {
                        "principle_unicode": {"total_checks": 3, "answered_checks": 1},
                        "principle_emoji": {"total_checks": 7, "answered_checks": 7},
                    },
                    "current_index": 0,
                    "key": "unicode_cards",
                },
            ),
        ],
    )
    def test_create_component_success(
        self,
        mock_components,
        mock_os_path,
        principles_names,
        principles_data,
        current_index,
        key,
        expected_params,
    ):
        """Test successful creation of cards component with various inputs."""
        mock_component, mock_declare_component = mock_components

        # Mock file operations
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            result = create_component(
                principles_names, principles_data, current_index, key
            )

        # Verify component was declared correctly
        mock_declare_component.assert_called_once_with(
            "cards_component", path="/test/path"
        )

        # Verify component was called with correct parameters
        mock_component.assert_called_once_with(**expected_params)

        # Verify result is the component return value
        assert result == mock_component.return_value

        # Verify file operations
        mock_file.assert_called_once_with("/test/path/index.html", "w")
        mock_file().write.assert_called_once()

    @pytest.mark.parametrize(
        "principles_names,principles_data,current_index,key,expected_error",
        [
            # Invalid principles_names
            (None, {}, 0, "test", TypeError),
            (123, {}, 0, "test", TypeError),
            ("not a list", {}, 0, "test", TypeError),
            # Invalid principles_data
            ([], None, 0, "test", TypeError),
            ([], 123, 0, "test", TypeError),
            ([], "not a dict", 0, "test", TypeError),
            # Invalid current_index
            ([], {}, None, "test", TypeError),
            ([], {}, "not an int", "test", TypeError),
            ([], {}, -1, "test", ValueError),  # Assuming negative index is invalid
            # Invalid key
            ([], {}, 0, None, TypeError),
            ([], {}, 0, 123, TypeError),
        ],
    )
    def test_create_component_invalid_inputs(
        self,
        mock_components,
        mock_os_path,
        principles_names,
        principles_data,
        current_index,
        key,
        expected_error,
    ):
        """Test that invalid input types raise appropriate errors."""
        mock_component, mock_declare_component = mock_components

        with pytest.raises(expected_error):
            create_component(principles_names, principles_data, current_index, key)

    def test_create_component_file_exists_same_content(
        self, mock_components, mock_os_path
    ):
        """Test when HTML file exists with same content - should not write file."""
        mock_component, mock_declare_component = mock_components
        mock_dirname, mock_join, mock_exists = mock_os_path

        # Mock os.path.exists to return True (file exists)
        mock_exists.return_value = True

        # Mock file operations - simulate existing file with same content
        # Read the actual HTML content from the test file to match exactly
        with open("process_check_app/tests/assets/cards_component.html", "r") as f:
            actual_html_content = f.read()

        mock_file = mock_open(read_data=actual_html_content)
        with patch("builtins.open", mock_file):
            result = create_component(
                ["Principle 1", "Principle 2"],
                {"principle_1": {"total_checks": 5, "answered_checks": 3}},
                0,
                "cards_component",
            )

        # Verify component was declared correctly
        mock_declare_component.assert_called_once_with(
            "cards_component", path="/test/path"
        )

        # Verify component was called with correct parameters
        mock_component.assert_called_once_with(
            principles_names=["Principle 1", "Principle 2"],
            principles_data={"principle_1": {"total_checks": 5, "answered_checks": 3}},
            current_index=0,
            key="cards_component",
        )

        # Verify result is the component return value
        assert result == mock_component.return_value

        # Verify file operations - should only read existing file, not write (since content is same)
        assert mock_file.call_count == 1

        # Verify no write operation occurred since content was identical
        mock_file().read.assert_called_once()
        mock_file().write.assert_not_called()

    def test_create_component_file_exists_different_content(
        self, mock_components, mock_os_path
    ):
        """Test when HTML file exists with different content - should write file."""
        mock_component, mock_declare_component = mock_components
        mock_dirname, mock_join, mock_exists = mock_os_path

        # Mock os.path.exists to return True (file exists)
        mock_exists.return_value = True

        # Mock file operations - simulate existing file with different content
        # Read the actual HTML content from the test file and modify it to be different
        with open("process_check_app/tests/assets/cards_component.html", "r") as f:
            actual_html_content = f.read()

        # Create different content by modifying the actual HTML
        different_html_content = actual_html_content.replace(
            "vertical-card", "different-card-class"
        )

        mock_file = mock_open(read_data=different_html_content)
        with patch("builtins.open", mock_file):
            result = create_component(
                ["Principle 1", "Principle 2"],
                {"principle_1": {"total_checks": 5, "answered_checks": 3}},
                0,
                "cards_component",
            )

        # Verify component was declared correctly
        mock_declare_component.assert_called_once_with(
            "cards_component", path="/test/path"
        )

        # Verify component was called with correct parameters
        mock_component.assert_called_once_with(
            principles_names=["Principle 1", "Principle 2"],
            principles_data={"principle_1": {"total_checks": 5, "answered_checks": 3}},
            current_index=0,
            key="cards_component",
        )

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

    def test_create_component_default_parameters(self, mock_components, mock_os_path):
        """Test create_component with default parameters."""
        mock_component, mock_declare_component = mock_components

        # Mock file operations
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            result = create_component(
                ["Test Principle"], {"test": {"total_checks": 1, "answered_checks": 0}}
            )

        # Verify component was declared correctly
        mock_declare_component.assert_called_once_with(
            "cards_component", path="/test/path"
        )

        # Verify component was called with default parameters
        mock_component.assert_called_once_with(
            principles_names=["Test Principle"],
            principles_data={"test": {"total_checks": 1, "answered_checks": 0}},
            current_index=0,  # Default value
            key="cards_component",  # Default value
        )

        # Verify result is the component return value
        assert result == mock_component.return_value
