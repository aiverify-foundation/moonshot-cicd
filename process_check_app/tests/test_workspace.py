import json
from pathlib import Path

import pytest
from backend.workspace import (
    _load_workspace_file,
    ensure_outputs_directory_exists,
    get_available_workspaces,
    initialize,
    is_workspace_initialized,
    load_workspace,
    save_workspace,
    workspace_file_exists,
)


class TestWorkspace:
    """Test collection for workspace functions."""

    @pytest.mark.parametrize(
        "workspace_id,workspace_data,expected_workspace_id,expected_workspace_data",
        [
            # Test with default parameters (None values)
            (None, None, "", {}),
            # Test with custom workspace_id and workspace_data
            (
                "test_workspace_123",
                {"key1": "value1", "key2": "value2"},
                "test_workspace_123",
                {"key1": "value1", "key2": "value2"},
            ),
            # Test with None workspace_data (should default to empty dict)
            ("test_id", None, "test_id", {}),
            # Test with empty workspace_id
            ("", {"data": "test"}, "", {"data": "test"}),
            # Test with empty workspace_data dict
            ("workspace_456", {}, "workspace_456", {}),
            # Test with invalid input types
            (123, {"data": "test"}, "", {"data": "test"}),
            ([], {"data": "test"}, "", {"data": "test"}),
            ({"id": "test"}, {"data": "test"}, "", {"data": "test"}),
            # Test with invalid workspace_data types
            ("test_id", "not_a_dict", "test_id", {}),
            ("test_id", 123, "test_id", {}),
            ("test_id", ["list", "data"], "test_id", {}),
            # Test with very long workspace_id
            ("a" * 1000, {"data": "test"}, "a" * 1000, {"data": "test"}),
        ],
    )
    def test_initialize(
        self,
        mocker,
        workspace_id,
        workspace_data,
        expected_workspace_id,
        expected_workspace_data,
    ):
        """Test initialize with various parameter combinations."""
        # Mock streamlit session state
        mock_session_state = {}
        mocker.patch("backend.workspace.st.session_state", mock_session_state)

        # Mock ensure_outputs_directory_exists
        mock_ensure_dir = mocker.patch(
            "backend.workspace.ensure_outputs_directory_exists"
        )

        # Call initialize
        if workspace_id is None and workspace_data is None:
            initialize()
        elif workspace_data is None:
            initialize(workspace_id)
        else:
            initialize(workspace_id, workspace_data)

        # Verify ensure_outputs_directory_exists was called
        mock_ensure_dir.assert_called_once()

        # Verify session state was updated correctly
        assert (
            "workspace_id" in mock_session_state
        ), "workspace_id should be set in session state"
        assert (
            "workspace_data" in mock_session_state
        ), "workspace_data should be set in session state"
        assert (
            mock_session_state["workspace_id"] == expected_workspace_id
        ), f"Expected workspace_id {expected_workspace_id}, got {mock_session_state.get('workspace_id')}"
        assert (
            mock_session_state["workspace_data"] == expected_workspace_data
        ), f"Expected workspace_data {expected_workspace_data}, got {mock_session_state.get('workspace_data')}"

        # Additional validation to ensure session state was properly initialized
        assert (
            len(mock_session_state) == 2
        ), "Session state should contain exactly 2 keys"

        # Verify session state structure matches expectations
        for key in ["workspace_id", "workspace_data"]:
            assert (
                key in mock_session_state
            ), f"Key '{key}' should exist in session state"

    @pytest.mark.parametrize(
        "workspace_id,should_raise_exception",
        [
            ("workspace1", False),
            ("workspace2", False),
            ("test_workspace_123", False),
            ("", True),
            (None, True),
            (123, True),
            ([], True),
            (True, True),
            (42.5, True),
        ],
    )
    def test_workspace_file_exists(self, mocker, workspace_id, should_raise_exception):
        """Test workspace_file_exists with different workspace IDs."""
        # Mock Path.exists() method
        mock_path = mocker.patch("backend.workspace.OUTPUTS_DIRECTORY")
        mock_path.__truediv__.return_value.exists.return_value = True

        if should_raise_exception:
            # Test that ValueError is raised for invalid workspace_id
            with pytest.raises(
                ValueError, match="workspace_id must be a non-empty string"
            ):
                workspace_file_exists(workspace_id)
        else:
            # Call the function for valid workspace_id
            result = workspace_file_exists(workspace_id)

            # Verify the result
            assert isinstance(result, bool)

            # Verify the path was constructed correctly
            mock_path.__truediv__.assert_called_once_with(f"{workspace_id}.json")

    @pytest.mark.parametrize(
        "workspace_id,expected,should_raise_exception",
        [
            ("workspace1", True, False),
            ("", False, False),
            ("test_workspace_123", True, False),
            (None, False, True),
            (123, False, True),
            ([], False, True),
            (True, False, True),
            (42.5, False, True),
            ({}, False, True),
            (set(), False, True),
        ],
    )
    def test_is_workspace_initialized(
        self, mocker, workspace_id, expected, should_raise_exception
    ):
        """Test is_workspace_initialized with different session states."""
        # Mock streamlit session state
        mock_session_state = {"workspace_id": workspace_id}
        mocker.patch("backend.workspace.st.session_state", mock_session_state)

        if should_raise_exception:
            # Test that TypeError is raised for non-string workspace_id
            with pytest.raises(TypeError, match="workspace_id must be a string"):
                is_workspace_initialized()
        else:
            # Call the function for valid workspace_id types
            result = is_workspace_initialized()

            # Verify the result
            assert result == expected

    @pytest.mark.parametrize(
        "directory_exists,should_call_mkdir",
        [
            (False, True),  # Directory doesn't exist, should create it
            (True, False),  # Directory exists, should not create it
        ],
    )
    def test_ensure_outputs_directory_exists(
        self, mocker, directory_exists, should_call_mkdir
    ):
        """Test ensure_outputs_directory_exists with different directory states."""
        # Mock Path.exists to return the parameterized value
        mock_path = mocker.patch("backend.workspace.OUTPUTS_DIRECTORY")
        mock_path.exists.return_value = directory_exists

        # Mock mkdir method
        mock_mkdir = mocker.patch.object(mock_path, "mkdir")

        # Call the function
        ensure_outputs_directory_exists()

        # Verify exists was called
        mock_path.exists.assert_called_once()

        # Verify mkdir behavior based on parameters
        if should_call_mkdir:
            mock_mkdir.assert_called_once_with(parents=True)
        else:
            mock_mkdir.assert_not_called()

    @pytest.mark.parametrize(
        "mock_files,mock_load_results,expected_count,expected_workspace_ids",
        [
            # Test case 1: Successful retrieval of available workspaces
            (
                [
                    Path("workspace1.json"),
                    Path("workspace2.json"),
                    Path("workspace3.json"),
                ],
                [
                    {
                        "workspace_id": "workspace1",
                        "workspace_data": {"key1": "value1"},
                    },
                    {
                        "workspace_id": "workspace2",
                        "workspace_data": {"key2": "value2"},
                    },
                    {
                        "workspace_id": "workspace3",
                        "workspace_data": {"key3": "value3"},
                    },
                ],
                3,
                ["workspace1", "workspace2", "workspace3"],
            ),
            # Test case 2: Empty directory
            ([], [], 0, []),
            # Test case 3: Some workspace files fail to load
            (
                [
                    Path("workspace1.json"),
                    Path("workspace2.json"),
                    Path("workspace3.json"),
                ],
                [
                    {
                        "workspace_id": "workspace1",
                        "workspace_data": {"key1": "value1"},
                    },
                    None,  # Failed load
                    {
                        "workspace_id": "workspace3",
                        "workspace_data": {"key3": "value3"},
                    },
                ],
                2,
                ["workspace1", "workspace3"],
            ),
        ],
    )
    def test_get_available_workspaces(
        self,
        mocker,
        mock_files,
        mock_load_results,
        expected_count,
        expected_workspace_ids,
    ):
        """Test get_available_workspaces with different scenarios."""
        # Mock glob to return the parameterized files
        mock_path = mocker.patch("backend.workspace.OUTPUTS_DIRECTORY")
        mock_path.glob.return_value = mock_files

        # Mock _load_workspace_file to return parameterized results
        mock_load_workspace = mocker.patch("backend.workspace._load_workspace_file")
        mock_load_workspace.side_effect = mock_load_results

        # Call the function
        result = get_available_workspaces()

        # Verify the result count
        assert len(result) == expected_count

        # Verify workspace IDs if any results expected
        if expected_count > 0:
            actual_workspace_ids = [workspace["workspace_id"] for workspace in result]
            assert actual_workspace_ids == expected_workspace_ids
        else:
            assert result == []

        # Verify glob was called with correct pattern
        mock_path.glob.assert_called_once_with("*.json")

    @pytest.mark.parametrize(
        "workspace_id,file_exists,workspace_data,expected_result,expected_logger_call",
        [
            # Test case 1: Successful loading
            (
                "test_workspace",
                True,
                {"key1": "value1", "key2": "value2"},
                {"key1": "value1", "key2": "value2"},
                "info",
            ),
            # Test case 2: File doesn't exist
            ("nonexistent_workspace", False, None, None, "warning"),
            # Test case 3: File exists but JSON parsing fails
            ("error_workspace", True, "invalid_json", None, "error"),
            # Test case 4: Empty workspace data
            ("empty_workspace", True, {}, {}, "info"),
            # Test case 5: File exists but file read fails
            ("file_error_workspace", True, "file_error", None, "error"),
        ],
    )
    def test_load_workspace(
        self,
        mocker,
        workspace_id,
        file_exists,
        workspace_data,
        expected_result,
        expected_logger_call,
    ):
        """Test load_workspace with different scenarios."""
        # Mock file path and its exists method
        mock_path = mocker.patch("backend.workspace.OUTPUTS_DIRECTORY")
        mock_file_path = mocker.MagicMock()
        mock_file_path.exists.return_value = file_exists
        mock_path.__truediv__.return_value = mock_file_path

        # Mock logger
        mock_logger = mocker.patch("backend.workspace.logger")

        if file_exists:
            if workspace_data == "invalid_json":
                # Mock file operations to succeed but JSON parsing to fail
                mock_file = mocker.mock_open()
                mocker.patch("builtins.open", mock_file)
                mocker.patch(
                    "json.load", side_effect=json.JSONDecodeError("Invalid JSON", "", 0)
                )
            elif workspace_data == "file_error":
                # Mock file operations to fail
                mocker.patch(
                    "builtins.open", side_effect=FileNotFoundError("File not found")
                )
            else:
                # Mock successful file operations
                mock_file = mocker.mock_open()
                mocker.patch("builtins.open", mock_file)
                mocker.patch("json.load", return_value=workspace_data)

        # Call the function
        result = load_workspace(workspace_id)

        # Verify the result
        assert result == expected_result

        # Verify file path was constructed correctly
        mock_path.__truediv__.assert_called_once_with(f"{workspace_id}.json")

        # Verify file exists was checked
        mock_file_path.exists.assert_called_once()

        # Verify appropriate logger method was called
        if expected_logger_call == "info":
            mock_logger.info.assert_called_once()
        elif expected_logger_call == "warning":
            mock_logger.warning.assert_called_once()
        elif expected_logger_call == "error":
            mock_logger.error.assert_called_once()

    @pytest.mark.parametrize(
        "file_path,workspace_data,expected_result,description",
        [
            # Successful loading test cases
            (
                Path("workspace1.json"),
                {"key1": "value1", "key2": "value2"},
                {
                    "workspace_id": "workspace1",
                    "workspace_data": {"key1": "value1", "key2": "value2"},
                },
                "simple data",
            ),
            (
                Path("complex_workspace.json"),
                {
                    "nested": {"level1": {"level2": "value"}},
                    "list": [1, 2, 3],
                    "boolean": True,
                },
                {
                    "workspace_id": "complex_workspace",
                    "workspace_data": {
                        "nested": {"level1": {"level2": "value"}},
                        "list": [1, 2, 3],
                        "boolean": True,
                    },
                },
                "complex nested data",
            ),
            (
                Path("empty_workspace.json"),
                {},
                {"workspace_id": "empty_workspace", "workspace_data": {}},
                "empty data",
            ),
            (
                Path("null_workspace.json"),
                {"key1": None, "key2": "value"},
                {
                    "workspace_id": "null_workspace",
                    "workspace_data": {"key1": None, "key2": "value"},
                },
                "null values",
            ),
            (
                Path("workspace.with.dots.json"),
                {"data": "test"},
                {
                    "workspace_id": "workspace.with.dots",
                    "workspace_data": {"data": "test"},
                },
                "file with dots in name",
            ),
            (
                Path("large_workspace.json"),
                {
                    "large_list": list(range(100)),
                    "large_dict": {f"key_{i}": f"value_{i}" for i in range(10)},
                },
                {
                    "workspace_id": "large_workspace",
                    "workspace_data": {
                        "large_list": list(range(100)),
                        "large_dict": {f"key_{i}": f"value_{i}" for i in range(10)},
                    },
                },
                "large data structures",
            ),
        ],
    )
    def test_load_workspace_file_success(
        self, mocker, file_path, workspace_data, expected_result, description
    ):
        """Test successful loading of workspace files with various data types."""
        # Mock the Path.open method globally
        mock_file = mocker.mock_open()
        mocker.patch("pathlib.Path.open", mock_file)

        # Mock json.load to return the workspace data
        mock_json_load = mocker.patch("json.load", return_value=workspace_data)

        # Mock logger
        mock_logger = mocker.patch("backend.workspace.logger")

        # Call the function
        result = _load_workspace_file(file_path)

        # Verify the result
        assert result == expected_result, f"Failed test case: {description}"

        # Verify file operations
        mock_file.assert_called_once_with("r")

        # Verify json.load was called with the file object
        mock_json_load.assert_called_once_with(mock_file())

        # Verify no error was logged
        mock_logger.error.assert_not_called()

    def test_load_workspace_file_exception(self, mocker):
        """Test _load_workspace_file with file reading exception."""
        file_path = Path("error_workspace.json")

        # Mock the Path.open method to raise an exception
        mocker.patch(
            "pathlib.Path.open", side_effect=FileNotFoundError("File not found")
        )

        # Mock logger
        mock_logger = mocker.patch("backend.workspace.logger")

        # Call the function
        result = _load_workspace_file(file_path)

        # Verify the result is None
        assert result is None

        # Verify error was logged
        mock_logger.error.assert_called_once()
        error_message = mock_logger.error.call_args[0][0]
        assert "Error reading workspace file" in error_message
        assert file_path.name in error_message

    @pytest.mark.parametrize(
        "workspace_id,workspace_data,description",
        [
            ("workspace1", {"key1": "value1"}, "simple string data"),
            (
                "complex_workspace",
                {"nested": {"data": "value"}, "list": [1, 2, 3]},
                "complex nested data",
            ),
            ("empty_workspace", {}, "empty data"),
            (
                "numbers_workspace",
                {"int_val": 42, "float_val": 3.14, "negative": -10},
                "numeric data",
            ),
            (
                "boolean_workspace",
                {"true_val": True, "false_val": False},
                "boolean data",
            ),
            (
                "null_workspace",
                {"null_val": None, "empty_str": "", "zero": 0},
                "null and empty values",
            ),
            (
                "list_workspace",
                {"simple_list": [1, 2, 3], "mixed_list": ["a", 1, True, None]},
                "list data",
            ),
            (
                "special_chars_workspace",
                {
                    "unicode": "café résumé",
                    "emoji": ":rocket: :tada:",
                    "special": "!@#$%^&*()",
                },
                "special characters",
            ),
        ],
    )
    def test_save_workspace_success(
        self, mocker, workspace_id, workspace_data, description
    ):
        """Test successful saving of workspace data."""
        # Mock dependencies
        mock_ensure_dir = mocker.patch(
            "backend.workspace.ensure_outputs_directory_exists"
        )
        mock_path = mocker.patch("backend.workspace.OUTPUTS_DIRECTORY")
        mock_file_path = mocker.MagicMock()
        mock_path.__truediv__.return_value = mock_file_path

        # Mock the file_path.open method specifically
        mock_file = mocker.mock_open()
        mock_file_path.open = mock_file

        # Mock json.dump
        mock_json_dump = mocker.patch("json.dump")

        # Mock datetime
        mock_datetime = mocker.patch("backend.workspace.datetime")
        mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T12:00:00"

        # Mock logger
        mock_logger = mocker.patch("backend.workspace.logger")

        # Call the function
        result = save_workspace(workspace_id, workspace_data)

        # Verify success
        assert result is True, f"Failed test case: {description}"
        mock_ensure_dir.assert_called_once()
        mock_path.__truediv__.assert_called_once_with(f"{workspace_id}.json")
        mock_file.assert_called_once_with("w")

        # Verify data with timestamp
        expected_data = workspace_data.copy()
        expected_data["last_saved"] = "2023-01-01T12:00:00"
        mock_json_dump.assert_called_once_with(expected_data, mock_file(), indent=2)
        mock_logger.info.assert_called_once()

    @pytest.mark.parametrize(
        "workspace_id,workspace_data,exception_type,exception_message,description",
        [
            (
                "permission_workspace",
                {"key1": "value1"},
                PermissionError,
                "Permission denied",
                "file permission error",
            ),
            (
                "disk_full_workspace",
                {"key1": "value1"},
                OSError,
                "No space left on device",
                "disk space error",
            ),
            (
                "dir_error_workspace",
                {"key1": "value1"},
                OSError,
                "Directory creation failed",
                "directory creation error",
            ),
            (
                "file_locked_workspace",
                {"key1": "value1"},
                OSError,
                "File is locked",
                "file locked error",
            ),
        ],
    )
    def test_save_workspace_file_errors(
        self,
        mocker,
        workspace_id,
        workspace_data,
        exception_type,
        exception_message,
        description,
    ):
        """Test save_workspace with various file operation errors."""
        # Mock ensure_outputs_directory_exists to succeed
        mock_ensure_dir = mocker.patch(
            "backend.workspace.ensure_outputs_directory_exists"
        )

        # Mock the file path and its open method to raise an exception
        mock_path = mocker.patch("backend.workspace.OUTPUTS_DIRECTORY")
        mock_file_path = mocker.MagicMock()
        mock_path.__truediv__.return_value = mock_file_path
        mock_file_path.open.side_effect = exception_type(exception_message)

        mock_logger = mocker.patch("backend.workspace.logger")

        # Call the function
        result = save_workspace(workspace_id, workspace_data)

        # Verify failure
        assert result is False, f"Failed test case: {description}"
        mock_ensure_dir.assert_called_once()
        mock_file_path.open.assert_called_once_with("w")
        mock_logger.error.assert_called_once()

    @pytest.mark.parametrize(
        "workspace_id,workspace_data,non_serializable_value,description",
        [
            (
                "lambda_workspace",
                {"key1": "value1", "func": lambda x: x},
                lambda x: x,
                "lambda function",
            ),
            (
                "class_workspace",
                {"key1": "value1", "obj": object()},
                object(),
                "class instance",
            ),
            (
                "set_workspace",
                {"key1": "value1", "set_val": {1, 2, 3}},
                {1, 2, 3},
                "set data",
            ),
            (
                "bytes_workspace",
                {"key1": "value1", "bytes_val": b"binary"},
                b"binary",
                "bytes data",
            ),
        ],
    )
    def test_save_workspace_json_errors(
        self, mocker, workspace_id, workspace_data, non_serializable_value, description
    ):
        """Test save_workspace with various JSON serialization errors."""
        # Mock JSON serialization to fail
        mock_ensure_dir = mocker.patch(
            "backend.workspace.ensure_outputs_directory_exists"
        )
        mock_path = mocker.patch("backend.workspace.OUTPUTS_DIRECTORY")
        mock_file_path = mocker.MagicMock()
        mock_path.__truediv__.return_value = mock_file_path
        mock_file = mocker.mock_open()
        mocker.patch("pathlib.Path.open", mock_file)
        mocker.patch(
            "json.dump",
            side_effect=TypeError(
                f"Object of type {type(non_serializable_value).__name__} is not JSON serializable"
            ),
        )
        mock_logger = mocker.patch("backend.workspace.logger")

        # Call the function
        result = save_workspace(workspace_id, workspace_data)

        # Verify failure
        assert result is False, f"Failed test case: {description}"
        mock_ensure_dir.assert_called_once()
        mock_logger.error.assert_called_once()

    @pytest.mark.parametrize(
        "workspace_id,workspace_data,edge_case,description",
        [
            (
                123,
                {"key": 42, "number": 3.14, "bool": True},
                "numeric workspace ID",
                "numeric workspace ID",
            ),
            (
                True,
                {"key": 42, "number": 3.14, "bool": True},
                "boolean workspace ID",
                "boolean workspace ID",
            ),
            (
                None,
                {"key": 42, "number": 3.14, "bool": True},
                "None workspace ID",
                "None workspace ID",
            ),
            (
                3.14,
                {"key": 42, "number": 3.14, "bool": True},
                "float workspace ID",
                "float workspace ID",
            ),
            (
                [1, 2, 3],
                {"key": 42, "number": 3.14, "bool": True},
                "list workspace ID",
                "list workspace ID",
            ),
            (
                {"key": "value"},
                {"key": 42, "number": 3.14, "bool": True},
                "dict workspace ID",
                "dict workspace ID",
            ),
            ("workspace_id", 123, "numeric workspace_data", "numeric workspace_data"),
            ("workspace_id", True, "boolean workspace_data", "boolean workspace_data"),
            ("workspace_id", None, "None workspace_data", "None workspace_data"),
            ("workspace_id", 3.14, "float workspace_data", "float workspace_data"),
            ("workspace_id", [1, 2, 3], "list workspace_data", "list workspace_data"),
            (
                "workspace_id",
                "string_data",
                "string workspace_data",
                "string workspace_data",
            ),
        ],
    )
    def test_save_workspace_edge_cases(
        self, mocker, workspace_id, workspace_data, edge_case, description
    ):
        """Test save_workspace with edge cases for workspace IDs and data that should raise ValueError."""
        # Call the function and expect ValueError for invalid types
        with pytest.raises(ValueError):
            save_workspace(workspace_id, workspace_data)
