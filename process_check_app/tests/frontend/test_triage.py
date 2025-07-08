from frontend.triage import (
    apply_custom_styles,
    display_continue_button,
    display_header,
    display_logo,
    display_new_process_button,
    triage,
)


# Create a mock version of the dialog-decorated function for testing
def mock_resume_workspace_dialog(available_workspaces):
    """Mock version of resume_workspace_dialog without the @st.dialog decorator for testing."""
    # Import here to avoid circular imports
    import streamlit as st
    from backend.workspace import initialize, load_workspace
    from streamlit.logger import get_logger

    logger = get_logger(__name__)

    # Display page content
    st.markdown(
        """
        We have saved your progress, so you can pick up right where you left off.

        You can review your previous answers and make any changes.
        """
    )

    # Extract workspace IDs for the selectbox
    available_ids = [workspace["workspace_id"] for workspace in available_workspaces]

    # Option to select from available IDs
    selected_id = st.selectbox(
        "Select your previous workspace",
        options=available_ids,
        index=None,
        placeholder="Dropdown to select Workspace ID",
    )

    st.write("")  # Add spacing

    # Create buttons for user actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "Resume",
            type="primary",
            use_container_width=True,
            disabled=not selected_id,
        ):
            if selected_id:
                # Load the full workspace data
                workspace_data = load_workspace(selected_id)
                if workspace_data is None:
                    st.error(
                        f"Could not load workspace data for ID: {selected_id}. Please select a different workspace."
                    )
                    return  # Prevent continuation if workspace data is None
                elif not workspace_data:  # Check if workspace_data is empty
                    logger.warning(
                        f"Workspace data for ID: {selected_id} is empty. You can still continue."
                    )
                # Update the session state with the selected ID and data
                initialize(selected_id, workspace_data)
                st.session_state["needs_resume"] = True
                st.session_state["section"] = 3
                st.rerun()

    with col2:
        if st.button("Cancel", type="secondary", use_container_width=True):
            st.rerun()


class TestApplyCustomStyles:
    """Test suite for apply_custom_styles function."""

    def test_apply_custom_styles(self, mocker):
        """Test that custom CSS styles are applied correctly."""
        mock_markdown = mocker.patch("streamlit.markdown")

        apply_custom_styles()

        # Verify markdown was called once with CSS content
        mock_markdown.assert_called_once()
        call_args = mock_markdown.call_args[0][0]

        # Verify key CSS elements are present
        assert "<style>" in call_args
        assert "font-family" in call_args
        assert ".stApp" in call_args
        assert ".main-header" in call_args
        assert ".stButton" in call_args
        assert "unsafe_allow_html=True" in str(mock_markdown.call_args)


class TestDisplayContinueButton:
    """Test suite for display_continue_button function."""

    def test_display_continue_button_with_workspaces(self, mocker):
        """Test continue button when workspaces are available."""
        # Setup
        available_workspaces = [
            {"workspace_id": "ws1", "data": "test1"},
            {"workspace_id": "ws2", "data": "test2"},
        ]

        # Mock streamlit components
        mock_columns = mocker.patch("streamlit.columns")
        mock_button = mocker.patch("streamlit.button")
        mock_markdown = mocker.patch("streamlit.markdown")
        mock_dialog = mocker.patch("frontend.triage.resume_workspace_dialog")

        # Mock columns
        col1, col2, col3 = mocker.MagicMock(), mocker.MagicMock(), mocker.MagicMock()
        mock_columns.return_value = [col1, col2, col3]

        # Mock button click
        mock_button.return_value = True

        display_continue_button(available_workspaces)

        # Verify divider was displayed
        mock_markdown.assert_called_once()
        divider_call = mock_markdown.call_args[0][0]
        assert "custom-divider" in divider_call
        assert "Or" in divider_call

        # Verify columns layout
        mock_columns.assert_called_once_with([1, 2, 1])

        # Verify button was created and enabled
        mock_button.assert_called_once_with(
            "Continue Where You Left Off",
            type="secondary",
            use_container_width=True,
            disabled=False,
        )

        # Verify dialog was called
        mock_dialog.assert_called_once_with(available_workspaces)

    def test_display_continue_button_no_workspaces(self, mocker):
        """Test continue button when no workspaces are available."""
        # Setup
        available_workspaces = []

        # Mock streamlit components
        mock_columns = mocker.patch("streamlit.columns")
        mock_button = mocker.patch("streamlit.button")
        mocker.patch("streamlit.markdown")

        # Mock columns
        col1, col2, col3 = mocker.MagicMock(), mocker.MagicMock(), mocker.MagicMock()
        mock_columns.return_value = [col1, col2, col3]

        # Mock button not clicked
        mock_button.return_value = False

        display_continue_button(available_workspaces)

        # Verify button was created but disabled
        mock_button.assert_called_once_with(
            "Continue Where You Left Off",
            type="secondary",
            use_container_width=True,
            disabled=True,
        )

    def test_display_continue_button_not_clicked(self, mocker):
        """Test continue button when button is not clicked."""
        available_workspaces = [{"workspace_id": "ws1"}]

        # Mock streamlit components
        mock_columns = mocker.patch("streamlit.columns")
        mock_button = mocker.patch("streamlit.button")
        mocker.patch("streamlit.markdown")
        mock_dialog = mocker.patch("frontend.triage.resume_workspace_dialog")

        # Mock columns
        col1, col2, col3 = mocker.MagicMock(), mocker.MagicMock(), mocker.MagicMock()
        mock_columns.return_value = [col1, col2, col3]

        # Mock button not clicked
        mock_button.return_value = False

        display_continue_button(available_workspaces)

        # Dialog should not be called
        mock_dialog.assert_not_called()


class TestDisplayHeader:
    """Test suite for display_header function."""

    def test_display_header(self, mocker):
        """Test that header is displayed with correct content."""
        mock_markdown = mocker.patch("streamlit.markdown")

        display_header()

        mock_markdown.assert_called_once_with(
            '<h1 class="main-header">Welcome to Process Checks for Generative AI</h1>',
            unsafe_allow_html=True,
        )


class TestDisplayLogo:
    """Test suite for display_logo function."""

    def test_display_logo(self, mocker):
        """Test that logo is displayed correctly."""
        mock_columns = mocker.patch("streamlit.columns")
        mock_image = mocker.patch("streamlit.image")

        # Mock columns
        col1, col2, col3 = mocker.MagicMock(), mocker.MagicMock(), mocker.MagicMock()
        mock_columns.return_value = [col1, col2, col3]

        display_logo()

        # Verify column layout
        mock_columns.assert_called_once_with([1, 2, 1])

        # Verify image is displayed
        mock_image.assert_called_once_with("assets/images/aiverify_logo.png", width=700)


class TestDisplayNewProcessButton:
    """Test suite for display_new_process_button function."""

    def test_display_new_process_button_clicked(self, mocker):
        """Test new process button when clicked."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_rerun = mocker.patch("streamlit.rerun")
        mock_columns = mocker.patch("streamlit.columns")
        mock_button = mocker.patch("streamlit.button")

        # Mock columns
        col1, col2, col3 = mocker.MagicMock(), mocker.MagicMock(), mocker.MagicMock()
        mock_columns.return_value = [col1, col2, col3]

        # Mock button click
        mock_button.return_value = True

        display_new_process_button()

        # Verify column layout
        mock_columns.assert_called_once_with([1, 2, 1])

        # Verify button was created
        mock_button.assert_called_once_with(
            "Start New Process Checks", type="primary", use_container_width=True
        )

        # Verify session state was updated
        assert mock_session_state["section"] == 1
        mock_rerun.assert_called_once()

    def test_display_new_process_button_not_clicked(self, mocker):
        """Test new process button when not clicked."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_rerun = mocker.patch("streamlit.rerun")
        mock_columns = mocker.patch("streamlit.columns")
        mock_button = mocker.patch("streamlit.button")

        # Mock columns
        col1, col2, col3 = mocker.MagicMock(), mocker.MagicMock(), mocker.MagicMock()
        mock_columns.return_value = [col1, col2, col3]

        # Mock button not clicked
        mock_button.return_value = False

        display_new_process_button()

        # Verify session state was not modified
        assert "section" not in mock_session_state
        mock_rerun.assert_not_called()


class TestResumeWorkspaceDialog:
    """Test suite for resume_workspace_dialog function."""

    def test_resume_workspace_dialog_resume_success(self, mocker):
        """Test successful workspace resume."""
        # Setup
        available_workspaces = [{"workspace_id": "ws1"}, {"workspace_id": "ws2"}]

        # Mock streamlit components
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_rerun = mocker.patch("streamlit.rerun")
        mock_button = mocker.patch("streamlit.button")
        mock_columns = mocker.patch("streamlit.columns")
        mock_selectbox = mocker.patch("streamlit.selectbox")
        mocker.patch("streamlit.write")
        mocker.patch("streamlit.markdown")

        # Mock backend components
        mock_init = mocker.patch("backend.workspace.initialize")
        mock_load = mocker.patch("backend.workspace.load_workspace")

        mock_selectbox.return_value = "ws1"
        mock_load.return_value = {"test": "data"}

        # Mock columns
        col1, col2 = mocker.MagicMock(), mocker.MagicMock()
        mock_columns.return_value = [col1, col2]

        # Mock Resume button clicked
        mock_button.side_effect = [True, False]  # Resume=True, Cancel=False

        mock_resume_workspace_dialog(available_workspaces)

        # Verify selectbox was created with correct options
        mock_selectbox.assert_called_once_with(
            "Select your previous workspace",
            options=["ws1", "ws2"],
            index=None,
            placeholder="Dropdown to select Workspace ID",
        )

        # Verify workspace was loaded and initialized
        mock_load.assert_called_once_with("ws1")
        mock_init.assert_called_once_with("ws1", {"test": "data"})

        # Verify session state was updated
        assert mock_session_state["needs_resume"] is True
        assert mock_session_state["section"] == 3
        mock_rerun.assert_called_once()

    def test_resume_workspace_dialog_cancel(self, mocker):
        """Test workspace dialog cancellation."""
        available_workspaces = [{"workspace_id": "ws1"}]

        # Mock streamlit components
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_rerun = mocker.patch("streamlit.rerun")
        mock_button = mocker.patch("streamlit.button")
        mock_columns = mocker.patch("streamlit.columns")
        mock_selectbox = mocker.patch("streamlit.selectbox")
        mocker.patch("streamlit.write")
        mocker.patch("streamlit.markdown")

        mock_selectbox.return_value = "ws1"

        # Mock columns
        col1, col2 = mocker.MagicMock(), mocker.MagicMock()
        mock_columns.return_value = [col1, col2]

        # Mock Cancel button clicked
        mock_button.side_effect = [False, True]  # Resume=False, Cancel=True

        mock_resume_workspace_dialog(available_workspaces)

        # Verify rerun was called (for cancel)
        mock_rerun.assert_called_once()

    def test_resume_workspace_dialog_load_failure(self, mocker):
        """Test workspace resume when load_workspace returns None."""
        available_workspaces = [{"workspace_id": "ws1"}]

        # Mock streamlit components
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_error = mocker.patch("streamlit.error")
        mock_button = mocker.patch("streamlit.button")
        mock_columns = mocker.patch("streamlit.columns")
        mock_selectbox = mocker.patch("streamlit.selectbox")
        mocker.patch("streamlit.write")
        mocker.patch("streamlit.markdown")

        # Mock backend components
        mock_load = mocker.patch("backend.workspace.load_workspace")

        mock_selectbox.return_value = "ws1"
        mock_load.return_value = None  # Simulate load failure

        # Mock columns
        col1, col2 = mocker.MagicMock(), mocker.MagicMock()
        mock_columns.return_value = [col1, col2]

        # Mock Resume button clicked
        mock_button.side_effect = [True, False]

        mock_resume_workspace_dialog(available_workspaces)

        # Verify error was shown
        mock_error.assert_called_once()
        error_msg = mock_error.call_args[0][0]
        assert "Could not load workspace data for ID: ws1" in error_msg

    def test_resume_workspace_dialog_empty_workspace(self, mocker):
        """Test workspace resume when workspace data is empty."""
        available_workspaces = [{"workspace_id": "ws1"}]

        # Mock streamlit components
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mocker.patch("streamlit.rerun")
        mock_button = mocker.patch("streamlit.button")
        mock_columns = mocker.patch("streamlit.columns")
        mock_selectbox = mocker.patch("streamlit.selectbox")
        mocker.patch("streamlit.write")
        mocker.patch("streamlit.markdown")

        # Mock backend components
        mock_init = mocker.patch("backend.workspace.initialize")
        mock_load = mocker.patch("backend.workspace.load_workspace")
        mock_get_logger = mocker.patch("streamlit.logger.get_logger")

        mock_selectbox.return_value = "ws1"
        mock_load.return_value = {}  # Empty workspace data

        # Mock logger
        mock_logger = mocker.MagicMock()
        mock_get_logger.return_value = mock_logger

        # Mock columns
        col1, col2 = mocker.MagicMock(), mocker.MagicMock()
        mock_columns.return_value = [col1, col2]

        # Mock Resume button clicked
        mock_button.side_effect = [True, False]

        mock_resume_workspace_dialog(available_workspaces)

        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "Workspace data for ID: ws1 is empty" in warning_msg

        # Verify initialization still proceeded
        mock_init.assert_called_once_with("ws1", {})
        assert mock_session_state["needs_resume"] is True
        assert mock_session_state["section"] == 3

    def test_resume_workspace_dialog_no_selection(self, mocker):
        """Test resume button when no workspace is selected."""
        available_workspaces = [{"workspace_id": "ws1"}]

        # Mock streamlit components
        mock_button = mocker.patch("streamlit.button")
        mock_columns = mocker.patch("streamlit.columns")
        mock_selectbox = mocker.patch("streamlit.selectbox")
        mocker.patch("streamlit.write")
        mocker.patch("streamlit.markdown")

        mock_selectbox.return_value = None  # No selection

        # Mock columns
        col1, col2 = mocker.MagicMock(), mocker.MagicMock()
        mock_columns.return_value = [col1, col2]

        mock_resume_workspace_dialog(available_workspaces)

        # Verify Resume button is disabled when no selection
        # Check that the first button call (Resume button) has disabled=True
        button_calls = mock_button.call_args_list
        resume_button_call = button_calls[0]
        assert resume_button_call[1]["disabled"] is True


class TestTriage:
    """Test suite for main triage function."""

    def test_triage_complete_flow(self, mocker):
        """Test the complete triage function flow."""
        # Setup
        mock_workspaces = [{"workspace_id": "ws1"}, {"workspace_id": "ws2"}]

        # Mock all the display functions
        mock_styles = mocker.patch("frontend.triage.apply_custom_styles")
        mock_logo = mocker.patch("frontend.triage.display_logo")
        mock_header = mocker.patch("frontend.triage.display_header")
        mock_write = mocker.patch("streamlit.write")
        mock_get_workspaces = mocker.patch("frontend.triage.get_available_workspaces")
        mock_new_button = mocker.patch("frontend.triage.display_new_process_button")
        mock_continue_button = mocker.patch("frontend.triage.display_continue_button")

        mock_get_workspaces.return_value = mock_workspaces

        triage()

        # Verify all components are called in correct order
        mock_styles.assert_called_once()
        mock_logo.assert_called_once()
        mock_header.assert_called_once()

        # Verify spacing is added (9 newlines)
        assert mock_write.call_count == 9
        for call_args in mock_write.call_args_list:
            assert call_args[0][0] == "\n"

        # Verify workspace data is retrieved
        mock_get_workspaces.assert_called_once()

        # Verify buttons are displayed with workspace data
        mock_new_button.assert_called_once()
        mock_continue_button.assert_called_once_with(mock_workspaces)

    def test_triage_no_workspaces(self, mocker):
        """Test triage function when no workspaces are available."""
        # Setup - no available workspaces
        mocker.patch("frontend.triage.apply_custom_styles")
        mocker.patch("frontend.triage.display_logo")
        mocker.patch("frontend.triage.display_header")
        mocker.patch("streamlit.write")
        mock_get_workspaces = mocker.patch("frontend.triage.get_available_workspaces")
        mocker.patch("frontend.triage.display_new_process_button")
        mock_continue_button = mocker.patch("frontend.triage.display_continue_button")

        mock_get_workspaces.return_value = []

        triage()

        # Verify continue button is still called but with empty list
        mock_continue_button.assert_called_once_with([])
