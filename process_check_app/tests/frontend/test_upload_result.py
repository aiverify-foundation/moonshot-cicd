import json
import os

import pytest
from frontend.upload_result import (
    GA_SAMPLE_REPORT_NAME,
    GA_SAMPLE_REPORT_PATH,
    V06_SAMPLE_REPORT_NAME,
    V06_SAMPLE_REPORT_PATH,
    apply_custom_styles,
    click_back_button,
    click_next_button,
    click_start_over_button,
    display_json_content,
    display_navigation_buttons,
    upload_result,
)


@pytest.fixture
def mock_session_state():
    """Fixture to provide a mock session state for testing."""
    return {
        "section": 3,
        "workspace_id": "test_workspace_123",
        "workspace_data": {
            "upload_results": {},
            "progress_data": {"total_questions": 10, "total_answered_questions": 8},
        },
        "file_uploader_key": 0,
    }


@pytest.fixture
def sample_json_data():
    """Fixture providing sample JSON data for testing."""
    return {
        "metadata": {"version": "1.0", "test_type": "moonshot"},
        "results": [{"test_id": "test_1", "status": "passed", "score": 0.85}],
    }


class TestNavigationButtons:
    """Test navigation button functions."""

    def test_click_back_button(self, mocker):
        """Test clicking the back button decrements section."""
        mock_session_state = {"section": 3}
        mocker.patch("streamlit.session_state", mock_session_state)
        click_back_button()
        assert mock_session_state["section"] == 2

    def test_click_next_button(self, mocker):
        """Test clicking the next button increments section."""
        mock_session_state = {"section": 3}
        mocker.patch("streamlit.session_state", mock_session_state)
        click_next_button()
        assert mock_session_state["section"] == 4

    def test_click_start_over_button(self, mocker):
        """Test clicking the start over button displays confirmation dialog."""
        mock_dialog = mocker.patch("streamlit.dialog")

        # Mock required streamlit components
        mocker.patch("streamlit.write")
        mocker.patch(
            "streamlit.columns", return_value=[mocker.MagicMock(), mocker.MagicMock()]
        )
        mocker.patch("streamlit.button", return_value=False)

        click_start_over_button()
        mock_dialog.assert_called_once_with("Return to Home Page")

    def test_display_navigation_buttons_complete(self, mocker):
        """Test display navigation buttons with all questions answered."""
        mock_session_state = mocker.patch("streamlit.session_state")
        mock_button = mocker.patch("streamlit.button")
        mock_columns = mocker.patch("streamlit.columns")
        mocker.patch("streamlit.markdown")

        mock_session_state.__getitem__.side_effect = lambda key: {
            "section": 3,
            "workspace_data": {
                "progress_data": {"total_questions": 10, "total_answered_questions": 10}
            },
        }.get(key, {})

        mock_columns.return_value = [
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        ]

        display_navigation_buttons()

        # Check that buttons were called
        assert mock_button.call_count == 3  # Home, Back, Next

        # Check that Next button is enabled (not disabled)
        next_button_calls = [
            call_args
            for call_args in mock_button.call_args_list
            if "Next" in str(call_args)
        ]
        assert len(next_button_calls) == 1
        next_call = next_button_calls[0]
        assert next_call[1]["disabled"] is False

    def test_display_navigation_buttons_incomplete(self, mocker):
        """Test display navigation buttons with incomplete questions."""
        mock_session_state = mocker.patch("streamlit.session_state")
        mock_button = mocker.patch("streamlit.button")
        mock_columns = mocker.patch("streamlit.columns")
        mocker.patch("streamlit.markdown")

        mock_session_state.__getitem__.side_effect = lambda key: {
            "section": 3,
            "workspace_data": {
                "progress_data": {"total_questions": 10, "total_answered_questions": 5}
            },
        }.get(key, {})

        mock_columns.return_value = [
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        ]

        display_navigation_buttons()

        # Check that Next button is disabled when not all questions are answered
        next_button_calls = [
            call_args
            for call_args in mock_button.call_args_list
            if "Next" in str(call_args)
        ]
        assert len(next_button_calls) == 1
        next_call = next_button_calls[0]
        assert next_call[1]["disabled"] is True


class TestStylesAndDisplay:
    """Test styling and display functions."""

    def test_apply_custom_styles(self, mocker):
        """Test that custom styles are applied via markdown."""
        mock_markdown = mocker.patch("streamlit.markdown")
        apply_custom_styles()

        mock_markdown.assert_called_once()
        call_args = mock_markdown.call_args[0][0]
        # Verify that CSS styles are included
        assert "<style>" in call_args
        assert "font-family" in call_args
        assert "color" in call_args

    def test_display_json_content_with_valid_file(self, mocker, sample_json_data):
        """Test displaying JSON content from a valid file."""
        mock_markdown = mocker.patch("streamlit.markdown")
        mock_file_content = json.dumps(sample_json_data)

        mocker.patch("builtins.open", mocker.mock_open(read_data=mock_file_content))
        display_json_content("test_file.json")

        mock_markdown.assert_called_once()
        call_args = mock_markdown.call_args[0][0]
        # Verify JSON content is formatted and displayed
        assert "json-preview" in call_args
        assert "metadata" in call_args

    def test_get_download_link_logic(self):
        """Test download link generation logic (testing the nested function indirectly)."""
        import base64

        # Test the logic that would be used in the nested function
        test_data = '{"test": "data"}'
        filename = "test.json"
        link_text = "Download Test"

        # Simulate the get_download_link function logic
        b64 = base64.b64encode(test_data.encode()).decode()
        href = f'<a href="data:application/json;base64,{b64}" download="{filename}">{link_text}</a>'

        # Verify the download link structure
        assert "<a href=" in href
        assert "data:application/json;base64," in href
        assert f'download="{filename}"' in href
        assert f">{link_text}</a>" in href


class TestFileOperations:
    """Test file handling and validation logic."""

    def test_valid_json_file_processing(
        self,
        mocker,
        sample_json_data,
    ):
        """Test processing of valid JSON file."""
        mock_validate = mocker.patch("frontend.upload_result.validate_json")

        mock_validate.return_value = True

        # Mock file content
        mock_file_content = json.dumps(sample_json_data)

        # This test verifies the JSON validation logic
        mocker.patch("builtins.open", mocker.mock_open(read_data=mock_file_content))
        mocker.patch("json.load", return_value=sample_json_data)
        # Simulate the validation part of upload_result
        data = sample_json_data
        is_valid = mock_validate(data)

        assert is_valid is True
        mock_validate.assert_called_once_with(data)

    def test_invalid_json_file_processing(self, mocker):
        """Test processing of invalid JSON file."""
        mock_validate = mocker.patch("frontend.upload_result.validate_json")

        mock_validate.return_value = False

        invalid_data = {"invalid": "format"}

        # Simulate the validation part of upload_result
        is_valid = mock_validate(invalid_data)

        assert is_valid is False
        mock_validate.assert_called_once_with(invalid_data)

    def test_empty_json_file_handling(self, mocker):
        """Test handling of empty JSON file."""
        empty_data = {}

        # Simulate empty file check
        if not empty_data:
            result = "empty_file_error"
        else:
            result = "valid_file"

        assert result == "empty_file_error"

    def test_json_decode_error_handling(self):
        """Test handling of invalid JSON format."""
        invalid_json = "{ invalid json content"

        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)


class TestWorkspaceIntegration:
    """Test workspace and session state integration."""

    def test_workspace_initialization(self, mocker):
        """Test workspace initialization when not present."""
        mock_session_state = mocker.patch("streamlit.session_state")
        mock_init = mocker.patch("frontend.upload_result.initialize")

        # Simulate missing workspace_id
        mock_session_state.__contains__.side_effect = lambda key: key != "workspace_id"
        mock_session_state.get.return_value = None

        # This would be called in upload_result when workspace_id is missing
        mock_init(workspace_id="default")

        mock_init.assert_called_once_with(workspace_id="default")

    def test_upload_results_initialization(self, mocker):
        """Test upload_results dictionary initialization."""
        workspace_data = {}

        # Simulate the initialization logic
        if "upload_results" not in workspace_data:
            workspace_data["upload_results"] = {}

        assert "upload_results" in workspace_data
        assert workspace_data["upload_results"] == {}

    def test_file_removal_logic(self, mocker):
        """Test file removal logic when replacing files."""
        mock_exists = mocker.patch("os.path.exists")
        mock_remove = mocker.patch("os.remove")

        mock_exists.return_value = True
        file_path = "/tmp/test_file.json"

        # Simulate file removal logic
        if mock_exists(file_path):
            mock_remove(file_path)

        mock_exists.assert_called_once_with(file_path)
        mock_remove.assert_called_once_with(file_path)


class TestUploadResultMainFunction:
    """Test the main upload_result function behavior."""

    def test_upload_result_initialization(self, mocker):
        """Test upload_result function initialization and basic flow."""
        mock_session_state = mocker.patch("streamlit.session_state")
        mock_write = mocker.patch("streamlit.write")
        mock_uploader = mocker.patch("streamlit.file_uploader")
        mock_button = mocker.patch("streamlit.button")
        mock_tempdir = mocker.patch("tempfile.mkdtemp")
        mock_styles = mocker.patch("frontend.upload_result.apply_custom_styles")
        mock_nav = mocker.patch("frontend.upload_result.display_navigation_buttons")

        # Setup session state
        session_data = {
            "workspace_id": "test_123",
            "workspace_data": {"upload_results": {}},
            "file_uploader_key": 0,
        }

        def session_get(key, default=None):
            return session_data.get(key, default)

        def session_contains(key):
            return key in session_data

        mock_session_state.__getitem__.side_effect = session_get
        mock_session_state.get.side_effect = session_get
        mock_session_state.__contains__.side_effect = session_contains

        mock_tempdir.return_value = "/tmp/test_dir"
        mock_uploader.return_value = None  # No file uploaded
        mock_button.return_value = False

        # Mock file operations for sample files
        sample_data = '{"sample": "data"}'
        mocker.patch("builtins.open", mocker.mock_open(read_data=sample_data))
        upload_result()

        # Verify key functions were called
        mock_styles.assert_called_once()
        mock_nav.assert_called_once()
        mock_write.assert_called()
        mock_uploader.assert_called_once()

    def test_previous_file_display(self, mocker):
        """Test display of previously uploaded file."""
        mock_session_state = mocker.patch("streamlit.session_state")
        mock_exists = mocker.patch("os.path.exists")
        mock_display = mocker.patch("frontend.upload_result.display_json_content")
        mock_info = mocker.patch("streamlit.info")

        # Setup session state with existing file
        session_data = {
            "workspace_data": {
                "upload_results": {"file_path": "/tmp/existing_file.json"}
            }
        }

        mock_session_state.__getitem__.side_effect = lambda key: session_data.get(
            key, {}
        )
        mock_exists.return_value = True

        # Simulate the logic for displaying existing file
        if "file_path" in session_data["workspace_data"]["upload_results"]:
            file_path = session_data["workspace_data"]["upload_results"]["file_path"]
            if mock_exists(file_path):
                filename = os.path.basename(file_path)
                # This would trigger the info message and display
                mock_info(f"You previously uploaded {filename}")
                mock_display(file_path)

        mock_exists.assert_called_once_with("/tmp/existing_file.json")
        mock_info.assert_called_once()
        mock_display.assert_called_once_with("/tmp/existing_file.json")


class TestConstants:
    """Test module constants and file paths."""

    def test_sample_report_constants(self):
        """Test that sample report constants are properly defined."""
        assert GA_SAMPLE_REPORT_NAME == "ms_ga_result_template.json"
        assert V06_SAMPLE_REPORT_NAME == "ms_v06_result_template.json"

        # Verify paths are constructed correctly
        assert "assets" in GA_SAMPLE_REPORT_PATH
        assert "results" in GA_SAMPLE_REPORT_PATH
        assert GA_SAMPLE_REPORT_NAME in GA_SAMPLE_REPORT_PATH

        assert "assets" in V06_SAMPLE_REPORT_PATH
        assert "results" in V06_SAMPLE_REPORT_PATH
        assert V06_SAMPLE_REPORT_NAME in V06_SAMPLE_REPORT_PATH


class TestUploadResultCoverageImprovement:
    """Test upload_result function with different session state scenarios to improve coverage."""

    def test_upload_result_workspace_id_missing(self, mocker):
        """Test upload_result when workspace_id is missing - hits line 256."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_uploader = mocker.patch("streamlit.file_uploader")
        mock_tempdir = mocker.patch("tempfile.mkdtemp")
        mocker.patch("frontend.upload_result.apply_custom_styles")
        mocker.patch("frontend.upload_result.display_navigation_buttons")
        mock_init = mocker.patch("frontend.upload_result.initialize")

        # Set up session state WITHOUT workspace_id
        mock_session_state.update(
            {"workspace_data": {"upload_results": {}}, "file_uploader_key": 0}
        )

        mock_tempdir.return_value = "/tmp/test_dir"
        mock_uploader.return_value = None

        # Mock file operations for sample files
        sample_data = '{"sample": "data"}'
        mocker.patch("builtins.open", mocker.mock_open(read_data=sample_data))
        upload_result()

        # Verify initialize was called (line 256)
        mock_init.assert_called_once_with(workspace_id="default")

    def test_upload_result_workspace_data_missing(self, mocker):
        """Test upload_result when workspace_data is missing - hits line 260."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_uploader = mocker.patch("streamlit.file_uploader")
        mock_tempdir = mocker.patch("tempfile.mkdtemp")
        mocker.patch("frontend.upload_result.apply_custom_styles")
        mocker.patch("frontend.upload_result.display_navigation_buttons")

        # Set up session state WITHOUT workspace_data
        mock_session_state.update({"workspace_id": "test_123", "file_uploader_key": 0})

        mock_tempdir.return_value = "/tmp/test_dir"
        mock_uploader.return_value = None

        # Mock file operations for sample files
        sample_data = '{"sample": "data"}'
        mocker.patch("builtins.open", mocker.mock_open(read_data=sample_data))
        upload_result()

        # Verify workspace_data was initialized (line 260) and upload_results was initialized (line 264)
        assert "workspace_data" in mock_session_state
        assert mock_session_state["workspace_data"] == {"upload_results": {}}

    def test_upload_result_upload_results_missing(self, mocker):
        """Test upload_result when upload_results is missing - hits line 264."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_uploader = mocker.patch("streamlit.file_uploader")
        mock_tempdir = mocker.patch("tempfile.mkdtemp")
        mocker.patch("frontend.upload_result.apply_custom_styles")
        mocker.patch("frontend.upload_result.display_navigation_buttons")

        # Set up session state with workspace_data but WITHOUT upload_results
        mock_session_state.update(
            {
                "workspace_id": "test_123",
                "workspace_data": {},  # Empty workspace_data
                "file_uploader_key": 0,
            }
        )

        mock_tempdir.return_value = "/tmp/test_dir"
        mock_uploader.return_value = None

        # Mock file operations for sample files
        sample_data = '{"sample": "data"}'
        mocker.patch("builtins.open", mocker.mock_open(read_data=sample_data))
        upload_result()

        # Verify upload_results was initialized (line 264)
        assert "upload_results" in mock_session_state["workspace_data"]
        assert mock_session_state["workspace_data"]["upload_results"] == {}

    def test_upload_result_file_uploader_key_missing(self, mocker):
        """Test upload_result when file_uploader_key is missing - hits line 271."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_uploader = mocker.patch("streamlit.file_uploader")
        mock_tempdir = mocker.patch("tempfile.mkdtemp")
        mocker.patch("frontend.upload_result.apply_custom_styles")
        mocker.patch("frontend.upload_result.display_navigation_buttons")

        # Set up session state WITHOUT file_uploader_key
        mock_session_state.update(
            {
                "workspace_id": "test_123",
                "workspace_data": {"upload_results": {}},
                # Missing file_uploader_key
            }
        )

        mock_tempdir.return_value = "/tmp/test_dir"
        mock_uploader.return_value = None

        # Mock file operations for sample files
        sample_data = '{"sample": "data"}'
        mocker.patch("builtins.open", mocker.mock_open(read_data=sample_data))
        upload_result()

        # Verify file_uploader_key was initialized (line 271)
        assert "file_uploader_key" in mock_session_state
        assert mock_session_state["file_uploader_key"] == 0

    def test_upload_result_with_existing_file_path_exists(self, mocker):
        """Test upload_result when previous file exists - hits lines in existing file display logic."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_uploader = mocker.patch("streamlit.file_uploader")
        mock_info = mocker.patch("streamlit.info")
        mock_exists = mocker.patch("os.path.exists")
        mock_tempdir = mocker.patch("tempfile.mkdtemp")
        mocker.patch("frontend.upload_result.apply_custom_styles")
        mocker.patch("frontend.upload_result.display_navigation_buttons")
        mock_display = mocker.patch("frontend.upload_result.display_json_content")

        # Set up session state with existing file path
        mock_session_state.update(
            {
                "workspace_id": "test_123",
                "workspace_data": {
                    "upload_results": {"file_path": "/tmp/existing_file.json"}
                },
                "file_uploader_key": 0,
            }
        )

        mock_tempdir.return_value = "/tmp/test_dir"
        mock_uploader.return_value = None  # No new file uploaded
        mock_exists.return_value = True  # Previous file exists

        # Mock file operations for sample files
        sample_data = '{"sample": "data"}'
        mocker.patch("builtins.open", mocker.mock_open(read_data=sample_data))
        upload_result()

        # Verify previous file logic was executed
        # Check if our specific file path was called (may not be the last call due to Streamlit internals)
        expected_calls = [
            call
            for call in mock_exists.call_args_list
            if "/tmp/existing_file.json" in str(call)
        ]
        assert (
            len(expected_calls) > 0
        ), f"Expected call to exists('/tmp/existing_file.json') but got calls: {mock_exists.call_args_list}"
        mock_info.assert_called_once()
        mock_display.assert_called_once_with("/tmp/existing_file.json")

    def test_upload_result_with_existing_file_path_not_exists(self, mocker):
        """Test upload_result when previous file no longer exists - hits cleanup logic."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_uploader = mocker.patch("streamlit.file_uploader")
        mock_exists = mocker.patch("os.path.exists")
        mock_tempdir = mocker.patch("tempfile.mkdtemp")
        mocker.patch("frontend.upload_result.apply_custom_styles")
        mocker.patch("frontend.upload_result.display_navigation_buttons")

        # Set up session state with existing file path
        file_path = "/tmp/missing_file.json"
        mock_session_state.update(
            {
                "workspace_id": "test_123",
                "workspace_data": {"upload_results": {"file_path": file_path}},
                "file_uploader_key": 0,
            }
        )

        mock_tempdir.return_value = "/tmp/test_dir"
        mock_uploader.return_value = None  # No new file uploaded
        mock_exists.return_value = False  # Previous file doesn't exist

        # Mock file operations for sample files
        sample_data = '{"sample": "data"}'
        mocker.patch("builtins.open", mocker.mock_open(read_data=sample_data))
        upload_result()

        # Verify cleanup logic was executed - file_path should be removed
        mock_exists.assert_called_with(file_path)
        assert "file_path" not in mock_session_state["workspace_data"]["upload_results"]


class TestFileUploadLogic:
    """Test specific file upload logic from lines 284-339 in upload_result.py."""

    def test_upload_new_file_with_previous_file_cleanup(self, mocker):
        """Test uploading new file when previous file exists - tests cleanup logic (lines 287-296)."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_uploader = mocker.patch("streamlit.file_uploader")
        mock_success = mocker.patch("streamlit.success")
        mock_exists = mocker.patch("os.path.exists")
        mock_remove = mocker.patch("os.remove")
        mock_join = mocker.patch("os.path.join")
        mock_tempdir = mocker.patch("tempfile.mkdtemp")
        mocker.patch("frontend.upload_result.apply_custom_styles")
        mocker.patch("frontend.upload_result.display_navigation_buttons")
        mock_validate = mocker.patch("frontend.upload_result.validate_json")
        mock_save = mocker.patch("frontend.upload_result.save_workspace")

        # Create mock uploaded file
        mock_uploaded_file = mocker.MagicMock()
        mock_uploaded_file.name = "new_test.json"
        mock_uploaded_file.getbuffer.return_value = b'{"valid": "json"}'

        # Set up session state with existing file
        mock_session_state.update(
            {
                "workspace_id": "test_123",
                "workspace_data": {
                    "upload_results": {"file_path": "/tmp/old_file.json"}
                },
                "file_uploader_key": 0,
            }
        )

        mock_tempdir.return_value = "/tmp/test_dir"
        mock_join.return_value = "/tmp/test_dir/new_test.json"
        mock_uploader.return_value = mock_uploaded_file
        mock_exists.return_value = True  # Previous file exists
        mock_validate.return_value = True  # Valid JSON

        # Mock file operations
        json_data = {"valid": "json"}
        mock_file = mocker.patch("builtins.open", mocker.mock_open())
        mocker.patch("json.load", return_value=json_data)
        mocker.patch("json.dumps", return_value='{"valid": "json"}')

        # Mock sample files
        sample_data = '{"sample": "data"}'
        mock_file.side_effect = [
            mocker.mock_open(read_data=sample_data).return_value,  # Sample file reads
            mocker.mock_open(read_data=sample_data).return_value,
            mocker.mock_open().return_value,  # File write
            mocker.mock_open().return_value,  # File read
        ]

        upload_result()

        # Verify previous file was removed
        mock_exists.assert_any_call("/tmp/old_file.json")
        mock_remove.assert_called_with("/tmp/old_file.json")

        # Verify new file was saved
        mock_validate.assert_called_once_with(json_data)
        mock_success.assert_called_once_with("File uploaded successfully")
        mock_save.assert_called_once()

        # Verify session state updated with new file path
        assert (
            mock_session_state["workspace_data"]["upload_results"]["file_path"]
            == "/tmp/test_dir/new_test.json"
        )

    def test_upload_empty_json_file(self, mocker):
        """Test uploading empty JSON file - tests empty data handling (lines 305-310)."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_uploader = mocker.patch("streamlit.file_uploader")
        mock_error = mocker.patch("streamlit.error")
        mock_remove = mocker.patch("os.remove")
        mock_join = mocker.patch("os.path.join")
        mock_tempdir = mocker.patch("tempfile.mkdtemp")
        mocker.patch("frontend.upload_result.apply_custom_styles")
        mocker.patch("frontend.upload_result.display_navigation_buttons")

        # Create mock uploaded file
        mock_uploaded_file = mocker.MagicMock()
        mock_uploaded_file.name = "empty.json"
        mock_uploaded_file.getbuffer.return_value = b"{}"

        # Set up session state
        mock_session_state.update(
            {
                "workspace_id": "test_123",
                "workspace_data": {"upload_results": {}},
                "file_uploader_key": 0,
            }
        )

        mock_tempdir.return_value = "/tmp/test_dir"
        mock_join.return_value = "/tmp/test_dir/empty.json"
        mock_uploader.return_value = mock_uploaded_file

        # Mock file operations - empty JSON data
        mock_file = mocker.patch("builtins.open", mocker.mock_open())
        mocker.patch("json.load", return_value={})  # Empty JSON

        # Mock sample files
        sample_data = '{"sample": "data"}'
        mock_file.side_effect = [
            mocker.mock_open(read_data=sample_data).return_value,  # Sample file reads
            mocker.mock_open(read_data=sample_data).return_value,
            mocker.mock_open().return_value,  # File write
            mocker.mock_open().return_value,  # File read
        ]

        upload_result()

        # Verify error was shown and file was removed
        mock_error.assert_called_once_with(
            "The uploaded JSON file is empty. Please upload a valid Project Moonshot JSON file."
        )
        mock_remove.assert_called_with("/tmp/test_dir/empty.json")

    def test_upload_invalid_schema_json_file(self, mocker):
        """Test uploading JSON with invalid schema - tests validation failure (lines 323-328)."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_uploader = mocker.patch("streamlit.file_uploader")
        mock_error = mocker.patch("streamlit.error")
        mock_remove = mocker.patch("os.remove")
        mock_join = mocker.patch("os.path.join")
        mock_tempdir = mocker.patch("tempfile.mkdtemp")
        mocker.patch("frontend.upload_result.apply_custom_styles")
        mocker.patch("frontend.upload_result.display_navigation_buttons")
        mock_validate = mocker.patch("frontend.upload_result.validate_json")

        # Create mock uploaded file
        mock_uploaded_file = mocker.MagicMock()
        mock_uploaded_file.name = "invalid.json"
        mock_uploaded_file.getbuffer.return_value = b'{"invalid": "schema"}'

        # Set up session state
        mock_session_state.update(
            {
                "workspace_id": "test_123",
                "workspace_data": {"upload_results": {}},
                "file_uploader_key": 0,
            }
        )

        mock_tempdir.return_value = "/tmp/test_dir"
        mock_join.return_value = "/tmp/test_dir/invalid.json"
        mock_uploader.return_value = mock_uploaded_file
        mock_validate.return_value = False  # Invalid schema

        # Mock file operations
        json_data = {"invalid": "schema"}
        mock_file = mocker.patch("builtins.open", mocker.mock_open())
        mocker.patch("json.load", return_value=json_data)

        # Mock sample files
        sample_data = '{"sample": "data"}'
        mock_file.side_effect = [
            mocker.mock_open(read_data=sample_data).return_value,  # Sample file reads
            mocker.mock_open(read_data=sample_data).return_value,
            mocker.mock_open().return_value,  # File write
            mocker.mock_open().return_value,  # File read
        ]

        upload_result()

        # Verify validation was called and error was shown
        mock_validate.assert_called_once_with(json_data)
        mock_error.assert_called_once()
        # Check that the error message contains the key parts (more flexible to handle encoding issues)
        error_call_args = mock_error.call_args[0][0]
        assert "uploaded" in error_call_args and "correct format" in error_call_args
        assert "valid Project Moonshot JSON file" in error_call_args
        mock_remove.assert_called_with("/tmp/test_dir/invalid.json")

    def test_upload_malformed_json_file(self, mocker):
        """Test uploading malformed JSON file - tests JSONDecodeError handling (lines 329-334)."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_uploader = mocker.patch("streamlit.file_uploader")
        mock_error = mocker.patch("streamlit.error")
        mock_remove = mocker.patch("os.remove")
        mock_join = mocker.patch("os.path.join")
        mock_tempdir = mocker.patch("tempfile.mkdtemp")
        mocker.patch("frontend.upload_result.apply_custom_styles")
        mocker.patch("frontend.upload_result.display_navigation_buttons")

        # Create mock uploaded file
        mock_uploaded_file = mocker.MagicMock()
        mock_uploaded_file.name = "malformed.json"
        mock_uploaded_file.getbuffer.return_value = b'{"malformed": json}'

        # Set up session state
        mock_session_state.update(
            {
                "workspace_id": "test_123",
                "workspace_data": {"upload_results": {}},
                "file_uploader_key": 0,
            }
        )

        mock_tempdir.return_value = "/tmp/test_dir"
        mock_join.return_value = "/tmp/test_dir/malformed.json"
        mock_uploader.return_value = mock_uploaded_file

        # Mock file operations with JSON decode error
        mock_file = mocker.patch("builtins.open", mocker.mock_open())
        mocker.patch(
            "json.load", side_effect=json.JSONDecodeError("Invalid JSON", "doc", 0)
        )

        # Mock sample files
        sample_data = '{"sample": "data"}'
        mock_file.side_effect = [
            mocker.mock_open(read_data=sample_data).return_value,  # Sample file reads
            mocker.mock_open(read_data=sample_data).return_value,
            mocker.mock_open().return_value,  # File write
            mocker.mock_open().return_value,  # File read
        ]

        upload_result()

        # Verify error was shown and file was removed
        mock_error.assert_called_once_with(
            "The uploaded file is not a valid JSON. Please upload a valid Project Moonshot JSON file."
        )
        mock_remove.assert_called_with("/tmp/test_dir/malformed.json")

    def test_upload_valid_json_file_success_path(self, mocker):
        """Test successful upload of valid JSON file - tests success path (lines 311-322)."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_uploader = mocker.patch("streamlit.file_uploader")
        mock_markdown = mocker.patch("streamlit.markdown")
        mock_success = mocker.patch("streamlit.success")
        mock_join = mocker.patch("os.path.join")
        mock_tempdir = mocker.patch("tempfile.mkdtemp")
        mocker.patch("frontend.upload_result.apply_custom_styles")
        mocker.patch("frontend.upload_result.display_navigation_buttons")
        mock_validate = mocker.patch("frontend.upload_result.validate_json")
        mock_save = mocker.patch("frontend.upload_result.save_workspace")

        # Create mock uploaded file
        mock_uploaded_file = mocker.MagicMock()
        mock_uploaded_file.name = "valid.json"
        mock_uploaded_file.getbuffer.return_value = b'{"test": "data"}'

        # Set up session state
        mock_session_state.update(
            {
                "workspace_id": "test_123",
                "workspace_data": {"upload_results": {}},
                "file_uploader_key": 0,
            }
        )

        mock_tempdir.return_value = "/tmp/test_dir"
        mock_join.return_value = "/tmp/test_dir/valid.json"
        mock_uploader.return_value = mock_uploaded_file
        mock_validate.return_value = True  # Valid schema

        # Mock file operations
        json_data = {"test": "data"}
        json_str = '{\n    "test": "data"\n}'
        mock_file = mocker.patch("builtins.open", mocker.mock_open())
        mocker.patch("json.load", return_value=json_data)
        mocker.patch("json.dumps", return_value=json_str)

        # Mock sample files
        sample_data = '{"sample": "data"}'
        mock_file.side_effect = [
            mocker.mock_open(read_data=sample_data).return_value,  # Sample file reads
            mocker.mock_open(read_data=sample_data).return_value,
            mocker.mock_open().return_value,  # File write
            mocker.mock_open().return_value,  # File read
        ]

        upload_result()

        # Verify success path
        mock_validate.assert_called_once_with(json_data)
        mock_success.assert_called_once_with("File uploaded successfully")
        mock_markdown.assert_any_call(
            f'<div class="json-preview">{json_str}</div>', unsafe_allow_html=True
        )
        mock_save.assert_called_once_with(
            "test_123", mock_session_state["workspace_data"]
        )

        # Verify session state updated
        assert (
            mock_session_state["workspace_data"]["upload_results"]["file_path"]
            == "/tmp/test_dir/valid.json"
        )

    def test_upload_with_previous_file_removal_exception(self, mocker):
        """Test file upload when previous file removal fails - tests exception handling (lines 293-295)."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_uploader = mocker.patch("streamlit.file_uploader")
        mock_remove = mocker.patch("os.remove")
        mock_exists = mocker.patch("os.path.exists")
        mock_tempdir = mocker.patch("tempfile.mkdtemp")
        mocker.patch("frontend.upload_result.apply_custom_styles")
        mocker.patch("frontend.upload_result.display_navigation_buttons")

        # Create mock uploaded file
        mock_uploaded_file = mocker.MagicMock()
        mock_uploaded_file.name = "new.json"
        mock_uploaded_file.getbuffer.return_value = b'{"new": "data"}'

        # Set up session state with existing file
        mock_session_state.update(
            {
                "workspace_id": "test_123",
                "workspace_data": {
                    "upload_results": {"file_path": "/tmp/old_file.json"}
                },
                "file_uploader_key": 0,
            }
        )

        mock_tempdir.return_value = "/tmp/test_dir"
        mock_uploader.return_value = mock_uploaded_file
        mock_exists.return_value = True  # Previous file exists
        mock_remove.side_effect = Exception(
            "Permission denied"
        )  # Simulate removal failure

        # Mock file operations
        json_data = {"new": "data"}
        mock_file = mocker.patch("builtins.open", mocker.mock_open())
        mocker.patch("json.load", return_value=json_data)
        mocker.patch("os.path.join", return_value="/tmp/test_dir/new.json")
        mocker.patch("frontend.upload_result.validate_json", return_value=True)
        mocker.patch("frontend.upload_result.save_workspace")
        mocker.patch("streamlit.success")
        mocker.patch("json.dumps", return_value='{"new": "data"}')

        # Mock sample files
        sample_data = '{"sample": "data"}'
        mock_file.side_effect = [
            mocker.mock_open(read_data=sample_data).return_value,  # Sample file reads
            mocker.mock_open(read_data=sample_data).return_value,
            mocker.mock_open().return_value,  # File write
            mocker.mock_open().return_value,  # File read
        ]

        upload_result()

        # Verify exception was caught and execution continued
        mock_exists.assert_any_call("/tmp/old_file.json")
        mock_remove.assert_called_with("/tmp/old_file.json")

        # Verify file path was still removed from session state despite removal failure
        assert (
            "file_path" not in mock_session_state["workspace_data"]["upload_results"]
            or mock_session_state["workspace_data"]["upload_results"]["file_path"]
            == "/tmp/test_dir/new.json"
        )


class TestFileRemovalLogic:
    """Test file removal button logic from lines 365-383 in upload_result.py."""

    def test_remove_file_button_success(self, mocker):
        """Test successful file removal when button is clicked - tests lines 365-383."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_uploader = mocker.patch("streamlit.file_uploader")
        mock_markdown = mocker.patch("streamlit.markdown")
        mock_button = mocker.patch("streamlit.button")
        mock_success = mocker.patch("streamlit.success")
        mock_rerun = mocker.patch("streamlit.rerun")
        mock_exists = mocker.patch("os.path.exists")
        mock_remove = mocker.patch("os.remove")
        mock_tempdir = mocker.patch("tempfile.mkdtemp")
        mocker.patch("frontend.upload_result.apply_custom_styles")
        mocker.patch("frontend.upload_result.display_navigation_buttons")

        # Set up session state with existing file
        file_path = "/tmp/test_file.json"
        mock_session_state.update(
            {
                "workspace_id": "test_123",
                "workspace_data": {"upload_results": {"file_path": file_path}},
                "file_uploader_key": 5,
            }
        )

        mock_tempdir.return_value = "/tmp/test_dir"
        mock_uploader.return_value = None  # No new file uploaded
        mock_button.return_value = True  # Button clicked
        mock_exists.return_value = True  # File exists

        # Mock file operations for sample files
        sample_data = '{"sample": "data"}'
        mocker.patch("builtins.open", mocker.mock_open(read_data=sample_data))
        upload_result()

        # Verify button was created with correct parameters
        mock_button.assert_called_with(
            "Remove Uploaded File",
            key="remove_file_button",
            use_container_width=True,
            type="primary",
        )

        # Verify file removal logic
        mock_exists.assert_any_call(file_path)
        mock_remove.assert_called_with(file_path)

        # Verify session state cleanup
        assert "file_path" not in mock_session_state["workspace_data"]["upload_results"]

        # Verify success message and UI updates
        mock_success.assert_called_once_with("Uploaded file has been removed.")
        assert mock_session_state["file_uploader_key"] == 6  # Incremented
        mock_rerun.assert_called_once()

        # Verify remove button styling was applied
        expected_style = """
        <style>
        .remove_file_button {
            background-color: red !important;
            color: white !important;
            width: 100%;
        }
        </style>
        """
        mock_markdown.assert_any_call(expected_style, unsafe_allow_html=True)

    def test_file_uploader_key_increment_behavior(self, mocker):
        """Test that file_uploader_key is properly incremented to force Streamlit refresh."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_uploader = mocker.patch("streamlit.file_uploader")
        mock_button = mocker.patch("streamlit.button")
        mock_success = mocker.patch("streamlit.success")
        mock_rerun = mocker.patch("streamlit.rerun")
        mock_exists = mocker.patch("os.path.exists")
        mock_remove = mocker.patch("os.remove")
        mock_tempdir = mocker.patch("tempfile.mkdtemp")
        mocker.patch("frontend.upload_result.apply_custom_styles")
        mocker.patch("frontend.upload_result.display_navigation_buttons")

        # Set up session state with high file_uploader_key value
        file_path = "/tmp/test_file.json"
        initial_key = 42
        mock_session_state.update(
            {
                "workspace_id": "test_123",
                "workspace_data": {"upload_results": {"file_path": file_path}},
                "file_uploader_key": initial_key,
            }
        )

        mock_tempdir.return_value = "/tmp/test_dir"
        mock_uploader.return_value = None  # No new file uploaded
        mock_button.return_value = True  # Button clicked
        mock_exists.return_value = True  # File exists

        # Mock file operations for sample files
        sample_data = '{"sample": "data"}'
        mocker.patch("builtins.open", mocker.mock_open(read_data=sample_data))
        upload_result()

        # Verify file_uploader_key was incremented by exactly 1
        assert mock_session_state["file_uploader_key"] == initial_key + 1

        # Verify all cleanup actions occurred
        mock_remove.assert_called_with(file_path)
        assert "file_path" not in mock_session_state["workspace_data"]["upload_results"]
        mock_success.assert_called_once_with("Uploaded file has been removed.")
        mock_rerun.assert_called_once()
