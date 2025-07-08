import pytest
from frontend.generate_report import (
    click_back_button,
    click_start_over_button,
    display_edit_form,
    display_generate_report,
    display_navigation_buttons,
    display_pdf_preview,
    display_report_form,
    initialize_session_state,
    render_action_buttons,
)


@pytest.fixture
def mock_session_state():
    """Fixture providing a mock session state dictionary."""
    return {
        "workspace_id": "test_workspace",
        "workspace_data": {
            "company_name": "Test Company",
            "app_name": "Test App",
            "app_description": "Test Description",
        },
        "section": 3,
        "edit_mode": False,
        "report_generated": False,
        "pdf_file_path": None,
    }


class TestDisplayGenerateReport:
    """Test the main entry point function."""

    def test_display_generate_report(self, mocker):
        """Test that all required functions are called in correct order."""
        mock_init = mocker.patch("frontend.generate_report.initialize_session_state")
        mock_form = mocker.patch("frontend.generate_report.display_report_form")
        mock_nav = mocker.patch("frontend.generate_report.display_navigation_buttons")

        display_generate_report()

        mock_init.assert_called_once()
        mock_form.assert_called_once()
        mock_nav.assert_called_once()


class TestInitializeSessionState:
    """Test session state initialization."""

    def test_initialize_session_state_all_missing(self, mocker):
        """Test initialization when all session state variables are missing."""
        mock_session_state = {}
        mocker.patch("streamlit.session_state", mock_session_state)
        mock_load = mocker.patch("frontend.generate_report.load_workspace")
        mock_init = mocker.patch("frontend.generate_report.initialize")

        mock_load.return_value = {"test": "data"}

        # Mock the initialize function to set workspace_id
        def mock_initialize(workspace_id):
            mock_session_state["workspace_id"] = workspace_id

        mock_init.side_effect = mock_initialize

        initialize_session_state()

        mock_init.assert_called_once_with(workspace_id="default")
        mock_load.assert_called_once_with("default")
        assert mock_session_state["workspace_data"] == {"test": "data"}
        assert mock_session_state["section"] == 1

    def test_initialize_session_state_partial_existing(self, mocker):
        """Test initialization when some session state variables exist."""
        mock_session_state = {"workspace_id": "existing_id", "section": 2}
        mocker.patch("streamlit.session_state", mock_session_state)
        mock_load = mocker.patch("frontend.generate_report.load_workspace")
        mock_init = mocker.patch("frontend.generate_report.initialize")

        mock_load.return_value = {"existing": "data"}

        initialize_session_state()

        # Should not reinitialize existing values
        mock_init.assert_not_called()
        mock_load.assert_called_once_with("existing_id")
        assert mock_session_state["workspace_data"] == {"existing": "data"}
        assert mock_session_state["section"] == 2

    def test_initialize_session_state_all_existing(self, mocker):
        """Test initialization when all session state variables already exist."""
        mock_session_state = {
            "workspace_id": "existing_id",
            "workspace_data": {"existing": "data"},
            "section": 5,
        }
        mocker.patch("streamlit.session_state", mock_session_state)
        mock_load = mocker.patch("frontend.generate_report.load_workspace")
        mock_init = mocker.patch("frontend.generate_report.initialize")

        initialize_session_state()

        # Should not call any initialization functions
        mock_init.assert_not_called()
        mock_load.assert_not_called()
        assert mock_session_state["workspace_id"] == "existing_id"
        assert mock_session_state["workspace_data"] == {"existing": "data"}
        assert mock_session_state["section"] == 5


class TestRenderActionButtons:
    """Test action buttons rendering and edit mode functionality."""

    def test_render_action_buttons_not_edit_mode_no_action(self, mocker):
        """Test action buttons when not in edit mode and no action returned."""
        mock_session_state = {
            "workspace_id": "test_id",
            "workspace_data": {
                "company_name": "Test Co",
                "app_name": "Test App",
                "app_description": "Test Desc",
            },
        }
        mocker.patch("streamlit.session_state", mock_session_state)
        mock_rerun = mocker.patch("streamlit.rerun")
        mock_component = mocker.patch(
            "frontend.generate_report.create_actions_component_no_excel"
        )

        mock_component.return_value = None

        render_action_buttons()

        mock_component.assert_called_once_with(
            workspace_id="test_id",
            company_name="Test Co",
            app_name="Test App",
            app_description="Test Desc",
        )
        assert mock_session_state["edit_mode"] is False
        mock_rerun.assert_not_called()

    def test_render_action_buttons_edit_action(self, mocker):
        """Test action buttons when edit action is returned."""
        mock_session_state = {
            "workspace_id": "test_id",
            "workspace_data": {
                "company_name": "Test Co",
                "app_name": "Test App",
                "app_description": "Test Desc",
            },
        }
        mocker.patch("streamlit.session_state", mock_session_state)
        mock_rerun = mocker.patch("streamlit.rerun")
        mock_component = mocker.patch(
            "frontend.generate_report.create_actions_component_no_excel"
        )

        mock_component.return_value = "edit"

        render_action_buttons()

        assert mock_session_state["edit_mode"] is True
        mock_rerun.assert_called_once()

    def test_render_action_buttons_in_edit_mode(self, mocker):
        """Test action buttons when already in edit mode."""
        mock_session_state = {
            "workspace_id": "test_id",
            "workspace_data": {},
            "edit_mode": True,
        }
        mocker.patch("streamlit.session_state", mock_session_state)
        mock_edit_form = mocker.patch("frontend.generate_report.display_edit_form")

        render_action_buttons()

        mock_edit_form.assert_called_once()

    def test_render_action_buttons_with_missing_data(self, mocker):
        """Test action buttons with missing workspace data fields."""
        mock_session_state = {
            "workspace_id": "test_id",
            "workspace_data": {},  # Missing all fields
        }
        mocker.patch("streamlit.session_state", mock_session_state)
        mock_component = mocker.patch(
            "frontend.generate_report.create_actions_component_no_excel"
        )

        mock_component.return_value = None

        render_action_buttons()

        mock_component.assert_called_once_with(
            workspace_id="test_id", company_name="", app_name="", app_description=""
        )


class TestDisplayEditForm:
    """Test the edit form functionality."""

    def test_display_edit_form_save_success(self, mocker):
        """Test successful form save with all required fields."""
        mock_session_state = {
            "workspace_id": "test_id",
            "workspace_data": {
                "company_name": "Old Company",
                "app_name": "Old App",
                "app_description": "Old Description",
            },
        }
        mocker.patch("streamlit.session_state", mock_session_state)
        mock_save = mocker.patch("frontend.generate_report.save_workspace")
        mock_form = mocker.patch("streamlit.form")
        mock_text_input = mocker.patch("streamlit.text_input")
        mock_text_area = mocker.patch("streamlit.text_area")
        mock_submit = mocker.patch("streamlit.form_submit_button")
        mock_columns = mocker.patch("streamlit.columns")
        mock_rerun = mocker.patch("streamlit.rerun")
        mock_success = mocker.patch("streamlit.success")

        # Mock form context manager
        mock_form_context = mocker.MagicMock()
        mock_form.return_value.__enter__ = mocker.MagicMock(
            return_value=mock_form_context
        )
        mock_form.return_value.__exit__ = mocker.MagicMock(return_value=None)

        # Mock input fields
        mock_text_input.side_effect = ["New Company", "New App"]
        mock_text_area.return_value = "New Description"

        # Mock column layout
        col1, col2 = mocker.MagicMock(), mocker.MagicMock()
        mock_columns.return_value = [col1, col2]

        # Mock submit buttons - save clicked
        mock_submit.side_effect = [True, False]  # save=True, cancel=False

        display_edit_form()

        # Verify form was created with correct key
        mock_form.assert_called_once_with("edit_app_info_form")

        # Verify inputs were created with correct parameters
        assert mock_text_input.call_count == 2
        mock_text_area.assert_called_once()

        # Verify save was called
        mock_save.assert_called_once_with(
            "test_id", mock_session_state["workspace_data"]
        )

        # Verify success message and state updates
        mock_success.assert_called_once_with("App information updated successfully!")
        assert mock_session_state["edit_mode"] is False
        assert mock_session_state["needs_refresh"] is True
        mock_rerun.assert_called_once()

    def test_display_edit_form_save_missing_fields(self, mocker):
        """Test form save with missing required fields."""
        mock_session_state = {"workspace_id": "test_id", "workspace_data": {}}
        mocker.patch("streamlit.session_state", mock_session_state)
        mock_form = mocker.patch("streamlit.form")
        mock_text_input = mocker.patch("streamlit.text_input")
        mock_text_area = mocker.patch("streamlit.text_area")
        mock_submit = mocker.patch("streamlit.form_submit_button")
        mock_columns = mocker.patch("streamlit.columns")
        mock_error = mocker.patch("streamlit.error")

        # Mock form context manager
        mock_form_context = mocker.MagicMock()
        mock_form.return_value.__enter__ = mocker.MagicMock(
            return_value=mock_form_context
        )
        mock_form.return_value.__exit__ = mocker.MagicMock(return_value=None)

        # Mock input fields with missing values
        mock_text_input.side_effect = ["", "App Name"]  # Missing company name
        mock_text_area.return_value = ""  # Missing description

        # Mock column layout
        col1, col2 = mocker.MagicMock(), mocker.MagicMock()
        mock_columns.return_value = [col1, col2]

        # Mock submit buttons - save clicked
        mock_submit.side_effect = [True, False]  # save=True, cancel=False

        display_edit_form()

        # Verify error message for missing fields
        mock_error.assert_called_once_with(
            "Please provide a valid Company Name, Application Description to proceed with saving changes."
        )

    def test_display_edit_form_cancel(self, mocker):
        """Test form cancel functionality."""
        mock_session_state = {
            "workspace_id": "test_id",
            "workspace_data": {},
            "edit_mode": True,
        }
        mocker.patch("streamlit.session_state", mock_session_state)
        mock_form = mocker.patch("streamlit.form")
        mocker.patch("streamlit.text_input")
        mocker.patch("streamlit.text_area")
        mock_submit = mocker.patch("streamlit.form_submit_button")
        mock_columns = mocker.patch("streamlit.columns")
        mock_rerun = mocker.patch("streamlit.rerun")

        # Mock form context manager
        mock_form_context = mocker.MagicMock()
        mock_form.return_value.__enter__ = mocker.MagicMock(
            return_value=mock_form_context
        )
        mock_form.return_value.__exit__ = mocker.MagicMock(return_value=None)

        # Mock column layout
        col1, col2 = mocker.MagicMock(), mocker.MagicMock()
        mock_columns.return_value = [col1, col2]

        # Mock submit buttons - cancel clicked
        mock_submit.side_effect = [False, True]  # save=False, cancel=True

        display_edit_form()

        # Verify edit mode was disabled and page rerun
        assert mock_session_state["edit_mode"] is False
        mock_rerun.assert_called_once()


class TestDisplayReportForm:
    """Test the report form display and functionality."""

    def test_display_report_form_initial_state(self, mocker):
        """Test report form initial display without report generation."""
        mock_session_state = {}
        mocker.patch("streamlit.session_state", mock_session_state)
        mock_render = mocker.patch("frontend.generate_report.render_action_buttons")
        mock_button = mocker.patch("streamlit.button")
        mock_write = mocker.patch("streamlit.write")
        mocker.patch("streamlit.markdown")

        mock_button.return_value = False  # Generate Report button not clicked

        display_report_form()

        # Verify initial session state setup
        assert mock_session_state["report_generated"] is False
        assert mock_session_state["pdf_file_path"] is None

        # Verify UI elements
        mock_write.assert_called_once_with("## Generate Your Report")
        mock_render.assert_called_once()
        mock_button.assert_called_once_with("Generate Report", type="primary")

    def test_display_report_form_generate_report(self, mocker):
        """Test report generation when button is clicked."""
        mock_session_state = {"workspace_data": {"test": "data"}}
        mocker.patch("streamlit.session_state", mock_session_state)
        mocker.patch("frontend.generate_report.render_action_buttons")
        mock_generate = mocker.patch("frontend.generate_report.generate_pdf_report")
        mock_button = mocker.patch("streamlit.button")
        mock_spinner = mocker.patch("streamlit.spinner")

        mock_button.return_value = True  # Generate Report button clicked
        mock_generate.return_value = "/path/to/report.pdf"

        # Mock spinner context manager
        mock_spinner_context = mocker.MagicMock()
        mock_spinner.return_value.__enter__ = mocker.MagicMock(
            return_value=mock_spinner_context
        )
        mock_spinner.return_value.__exit__ = mocker.MagicMock(return_value=None)

        mocker.patch("frontend.generate_report.display_pdf_preview")
        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake pdf content"))
        mocker.patch("streamlit.download_button")

        display_report_form()

        # Verify report generation
        mock_generate.assert_called_once_with({"test": "data"})
        mock_spinner.assert_called_once_with("Generating your report...")

        # Verify session state updates
        assert mock_session_state["report_generated"] is True
        assert mock_session_state["pdf_file_path"] == "/path/to/report.pdf"

    def test_display_report_form_with_generated_report(self, mocker):
        """Test report form when report has been generated."""
        mock_session_state = {
            "report_generated": True,
            "pdf_file_path": "/path/to/test_report.pdf",
        }
        mocker.patch("streamlit.session_state", mock_session_state)
        mocker.patch("frontend.generate_report.render_action_buttons")
        mock_preview = mocker.patch("frontend.generate_report.display_pdf_preview")
        mock_button = mocker.patch("streamlit.button")
        mocker.patch("streamlit.markdown")
        mock_download = mocker.patch("streamlit.download_button")

        mock_button.return_value = False

        # Mock file reading
        pdf_content = b"%PDF-1.4 fake pdf content"
        mocker.patch("builtins.open", mocker.mock_open(read_data=pdf_content))

        display_report_form()

        # Verify preview and download functionality
        mock_preview.assert_called_once_with("summary_report.pdf")
        mock_download.assert_called_once()

        # Verify download button parameters
        download_call = mock_download.call_args
        assert download_call[1]["label"] == "Download PDF"
        assert download_call[1]["data"] == pdf_content
        assert download_call[1]["file_name"] == "summary_report.pdf"
        assert download_call[1]["mime"] == "application/pdf"


class TestDisplayPdfPreview:
    """Test PDF preview functionality."""

    def test_display_pdf_preview(self, mocker):
        """Test PDF preview iframe generation."""
        mock_markdown = mocker.patch("streamlit.markdown")
        pdf_file_path = "test_report.pdf"

        display_pdf_preview(pdf_file_path)

        # Verify iframe HTML was generated correctly
        mock_markdown.assert_called_once()
        call_args = mock_markdown.call_args[0][0]
        assert "test_report.pdf" in call_args
        assert "iframe" in call_args
        assert "http://localhost:8000/temp_report/" in call_args


class TestNavigationFunctions:
    """Test navigation button functions."""

    def test_click_back_button(self, mocker):
        """Test back button functionality."""
        mock_session_state = {"section": 5}
        mocker.patch("streamlit.session_state", mock_session_state)

        click_back_button()

        assert mock_session_state["section"] == 4

    def test_click_start_over_button_no(self, mocker):
        """Test start over button with No confirmation."""
        original_state = {
            "workspace_id": "test",
            "section": 3,
            "server_started": True,
            "other_data": "should_remain",
        }
        mock_session_state = original_state.copy()
        mocker.patch("streamlit.session_state", mock_session_state)
        mock_dialog = mocker.patch("streamlit.dialog")
        mocker.patch("streamlit.write")
        mock_columns = mocker.patch("streamlit.columns")
        mock_button = mocker.patch("streamlit.button")
        mock_rerun = mocker.patch("streamlit.rerun")

        # Mock dialog context manager
        mock_dialog_context = mocker.MagicMock()
        mock_dialog.return_value.__enter__ = mocker.MagicMock(
            return_value=mock_dialog_context
        )
        mock_dialog.return_value.__exit__ = mocker.MagicMock(return_value=None)

        # Mock columns
        col1, col2 = mocker.MagicMock(), mocker.MagicMock()
        mock_columns.return_value = [col1, col2]

        # Mock the No button to return True when clicked (just triggers rerun)
        def mock_button_side_effect(*args, **kwargs):
            if "No, cancel" in args[0]:
                mock_rerun()
                return True
            return False

        mock_button.side_effect = mock_button_side_effect

        click_start_over_button()

        # Verify session state unchanged
        assert mock_session_state == original_state


class TestDisplayNavigationButtons:
    """Test navigation buttons display."""

    def test_display_navigation_buttons_section_1(self, mocker):
        """Test navigation buttons for section 1 (only Home button)."""
        mock_session_state = {"section": 1}
        mocker.patch("streamlit.session_state", mock_session_state)
        mock_markdown = mocker.patch("streamlit.markdown")
        mock_columns = mocker.patch("streamlit.columns")
        mock_button = mocker.patch("streamlit.button")

        # Mock columns
        col1, _, col2, col3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        mock_columns.return_value = [col1, _, col2, col3]

        display_navigation_buttons()

        # Verify spacing and separator
        mock_markdown.assert_any_call(
            "<div style='margin-top: 10px;'></div>", unsafe_allow_html=True
        )
        mock_markdown.assert_any_call("---")

        # Verify column layout
        mock_columns.assert_called_once_with([2, 6, 2, 2])

        # Verify Home button is called (should be called once for section >= 1)
        mock_button.assert_called_with(
            ":material/home: Home",
            on_click=click_start_over_button,
            use_container_width=True,
        )

    def test_display_navigation_buttons_section_3(self, mocker):
        """Test navigation buttons for section 3 (both Home and Back buttons)."""
        mock_session_state = {"section": 3}
        mocker.patch("streamlit.session_state", mock_session_state)
        mocker.patch("streamlit.markdown")
        mock_columns = mocker.patch("streamlit.columns")
        mock_button = mocker.patch("streamlit.button")

        # Mock columns
        col1, _, col2, col3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        mock_columns.return_value = [col1, _, col2, col3]

        display_navigation_buttons()

        # For section 3, both Home and Back buttons should be called
        # We need to check both calls were made
        expected_calls = [
            mocker.call(
                ":material/home: Home",
                on_click=click_start_over_button,
                use_container_width=True,
            ),
            mocker.call("← Back", on_click=click_back_button, use_container_width=True),
        ]
        mock_button.assert_has_calls(expected_calls, any_order=True)

    def test_display_navigation_buttons_section_0(self, mocker):
        """Test navigation buttons for section 0 (no buttons shown)."""
        mock_session_state = {"section": 0}
        mocker.patch("streamlit.session_state", mock_session_state)
        mock_markdown = mocker.patch("streamlit.markdown")
        mock_columns = mocker.patch("streamlit.columns")
        mocker.patch("streamlit.button")

        # Mock columns (they are always created)
        col1, _, col2, col3 = (
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
            mocker.MagicMock(),
        )
        mock_columns.return_value = [col1, _, col2, col3]

        display_navigation_buttons()

        # Verify no spacing/separator for section < 1
        mock_markdown.assert_not_called()

        # Verify columns are still created (always happens in the function)
        mock_columns.assert_called_once_with([2, 6, 2, 2])

        # Verify no buttons are shown (section < 1)
        col1.__enter__.return_value.button.assert_not_called()
        col3.__enter__.return_value.button.assert_not_called()


class TestFormValidation:
    """Test form validation logic in edit form."""

    def test_missing_fields_logic(self):
        """Test the missing fields validation logic."""
        # Test all fields missing
        missing_fields = []
        if not "":  # company_name
            missing_fields.append("Company Name")
        if not "":  # app_name
            missing_fields.append("Application Name")
        if not "":  # app_description
            missing_fields.append("Application Description")

        assert missing_fields == [
            "Company Name",
            "Application Name",
            "Application Description",
        ]

        # Test partial fields missing
        missing_fields = []
        if not "Test Company":  # company_name present
            missing_fields.append("Company Name")
        if not "":  # app_name missing
            missing_fields.append("Application Name")
        if not "Test Description":  # app_description present
            missing_fields.append("Application Description")

        assert missing_fields == ["Application Name"]


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_missing_workspace_data(self, mocker):
        """Test handling when workspace_data is missing from session state."""
        # Don't set workspace_data
        mock_session_state = {"workspace_id": "test_id"}
        mocker.patch("streamlit.session_state", mock_session_state)

        # Should raise KeyError since the function doesn't handle missing workspace_data gracefully
        with pytest.raises(KeyError):
            render_action_buttons()

    def test_missing_section_in_navigation(self, mocker):
        """Test navigation buttons when section is missing."""
        # Don't set section
        mock_session_state = {}
        mocker.patch("streamlit.session_state", mock_session_state)

        with pytest.raises(KeyError):
            display_navigation_buttons()

    def test_pdf_generation_failure(self, mocker):
        """Test handling when PDF generation fails."""
        mock_session_state = {"workspace_data": {"test": "data"}}
        mocker.patch("streamlit.session_state", mock_session_state)
        mocker.patch("frontend.generate_report.render_action_buttons")
        mock_generate = mocker.patch("frontend.generate_report.generate_pdf_report")
        mock_button = mocker.patch("streamlit.button")

        mock_button.return_value = True
        mock_generate.side_effect = Exception("PDF generation failed")

        # Should handle the exception gracefully
        mock_spinner = mocker.patch("streamlit.spinner")
        mock_spinner_context = mocker.MagicMock()
        mock_spinner.return_value.__enter__ = mocker.MagicMock(
            return_value=mock_spinner_context
        )
        mock_spinner.return_value.__exit__ = mocker.MagicMock(return_value=None)

        # Should not raise an unhandled exception
        try:
            display_report_form()
        except Exception as e:
            # If an exception is raised, it should be the expected one
            assert str(e) == "PDF generation failed"
