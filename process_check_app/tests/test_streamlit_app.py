import http.server
from unittest.mock import MagicMock

import pytest
from streamlit_app import (
    apply_custom_css,
    display_current_section,
    display_sections_bar,
    main,
    set_custom_width_layout,
    start_http_server,
)


class TestApplyCustomCSS:
    """
    Test cases for apply_custom_css function.
    """

    def test_apply_custom_css_calls_markdown(self, mocker):
        """
        Test that apply_custom_css calls st.markdown with CSS styles.
        """
        mock_markdown = mocker.patch("streamlit.markdown")

        apply_custom_css()

        # Should call markdown 3 times: header hide, footer hide, and custom styles
        assert mock_markdown.call_count == 3

    def test_apply_custom_css_hides_header(self, mocker):
        """
        Test that apply_custom_css hides the Streamlit header.
        """
        mock_markdown = mocker.patch("streamlit.markdown")

        apply_custom_css()

        # Check that header hiding CSS is applied
        hide_header_call = mock_markdown.call_args_list[0]
        assert "header {visibility: hidden;}" in hide_header_call[0][0]
        assert hide_header_call[1]["unsafe_allow_html"] is True

    def test_apply_custom_css_hides_footer(self, mocker):
        """
        Test that apply_custom_css hides the Streamlit footer and menu.
        """
        mock_markdown = mocker.patch("streamlit.markdown")

        apply_custom_css()

        # Check that footer hiding CSS is applied
        hide_footer_call = mock_markdown.call_args_list[1]
        assert "#MainMenu {visibility: hidden;}" in hide_footer_call[0][0]
        assert "footer {visibility: hidden;}" in hide_footer_call[0][0]
        assert hide_footer_call[1]["unsafe_allow_html"] is True

    def test_apply_custom_css_applies_custom_styles(self, mocker):
        """
        Test that apply_custom_css applies custom container and section styles.
        """
        mock_markdown = mocker.patch("streamlit.markdown")

        apply_custom_css()

        # Check that custom styles are applied
        custom_styles_call = mock_markdown.call_args_list[2]
        custom_css = custom_styles_call[0][0]

        assert ".container" in custom_css
        assert ".section" in custom_css
        assert ".box" in custom_css
        assert ".line" in custom_css
        assert ".label" in custom_css
        assert custom_styles_call[1]["unsafe_allow_html"] is True


class TestDisplaySectionsBar:
    """
    Test cases for display_sections_bar function.
    """

    def test_display_sections_bar_section_0_no_display(self, mocker):
        """
        Test that sections bar is not displayed when section is 0.
        """
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_markdown = mocker.patch("streamlit.markdown")

        mocker.patch.dict("streamlit.session_state", {"section": 0})

        display_sections_bar()

        # Should not call markdown when section is 0
        mock_markdown.assert_not_called()

    def test_display_sections_bar_section_none_no_display(self, mocker):
        """
        Test that sections bar is not displayed when section is None.
        """
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_markdown = mocker.patch("streamlit.markdown")

        display_sections_bar()

        # Should not call markdown when section is None/not set
        mock_markdown.assert_not_called()

    def test_display_sections_bar_section_1_displays(self, mocker):
        """
        Test that sections bar is displayed when section is 1.
        """
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_markdown = mocker.patch("streamlit.markdown")

        mocker.patch.dict("streamlit.session_state", {"section": 1})

        display_sections_bar()

        # Should call markdown once when section >= 1
        mock_markdown.assert_called_once()

        # Check that the HTML contains sections
        html_content = mock_markdown.call_args[0][0]
        assert "Welcome" in html_content
        assert "Getting Started" in html_content
        assert "Complete Process Checks" in html_content
        assert "Upload Technical Tests Results" in html_content
        assert "Generate Report" in html_content

    def test_display_sections_bar_active_section_highlighting(self, mocker):
        """
        Test that the current section is highlighted as active.
        """
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_markdown = mocker.patch("streamlit.markdown")

        mocker.patch.dict("streamlit.session_state", {"section": 3})

        display_sections_bar()

        html_content = mock_markdown.call_args[0][0]

        # Section 3 should be active, sections 1-3 should be active, 4-5 should be inactive
        assert 'class="box active">3</div>' in html_content
        assert 'class="box inactive">4</div>' in html_content
        assert 'class="box inactive">5</div>' in html_content
        # Check that active/inactive classes are properly applied
        assert "active" in html_content
        assert "inactive" in html_content

    def test_display_sections_bar_completed_lines(self, mocker):
        """
        Test that completed sections have completed line styling.
        """
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_markdown = mocker.patch("streamlit.markdown")

        mocker.patch.dict("streamlit.session_state", {"section": 4})

        display_sections_bar()

        html_content = mock_markdown.call_args[0][0]

        # Lines should be marked as completed for sections less than current
        assert 'class="line completed"' in html_content
        assert "completed" in html_content
        # Section 4 should be active and previous sections should be completed
        assert 'class="box active">4</div>' in html_content
        assert 'class="label completed">Welcome</div>' in html_content


class TestDisplayCurrentSection:
    """
    Test cases for display_current_section function.
    """

    def test_display_current_section_triage(self, mocker):
        """
        Test that section 0 displays triage.
        """
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_triage = mocker.patch("streamlit_app.triage")

        mocker.patch.dict("streamlit.session_state", {"section": 0})

        display_current_section()

        mock_triage.assert_called_once()

    def test_display_current_section_welcome(self, mocker):
        """
        Test that section 1 displays welcome.
        """
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_welcome = mocker.patch("streamlit_app.welcome")

        mocker.patch.dict("streamlit.session_state", {"section": 1})

        display_current_section()

        mock_welcome.assert_called_once()

    def test_display_current_section_getting_started(self, mocker):
        """
        Test that section 2 displays getting started.
        """
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_getting_started = mocker.patch("streamlit_app.getting_started")

        mocker.patch.dict("streamlit.session_state", {"section": 2})

        display_current_section()

        mock_getting_started.assert_called_once()

    def test_display_current_section_process_check(self, mocker):
        """
        Test that section 3 displays process check.
        """
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_process_check = mocker.patch("streamlit_app.display_process_check")

        mocker.patch.dict("streamlit.session_state", {"section": 3})

        display_current_section()

        mock_process_check.assert_called_once()

    def test_display_current_section_upload_result(self, mocker):
        """
        Test that section 4 displays upload result.
        """
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_upload_result = mocker.patch("streamlit_app.upload_result")

        mocker.patch.dict("streamlit.session_state", {"section": 4})

        display_current_section()

        mock_upload_result.assert_called_once()

    def test_display_current_section_generate_report(self, mocker):
        """
        Test that section 5 displays generate report.
        """
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_generate_report = mocker.patch("streamlit_app.display_generate_report")

        mocker.patch.dict("streamlit.session_state", {"section": 5})

        display_current_section()

        mock_generate_report.assert_called_once()

    def test_display_current_section_no_section_set(self, mocker):
        """
        Test behavior when no section is set in session state.
        """
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_triage = mocker.patch("streamlit_app.triage")
        mock_welcome = mocker.patch("streamlit_app.welcome")
        mock_getting_started = mocker.patch("streamlit_app.getting_started")
        mock_process_check = mocker.patch("streamlit_app.display_process_check")
        mock_upload_result = mocker.patch("streamlit_app.upload_result")
        mock_generate_report = mocker.patch("streamlit_app.display_generate_report")

        # session_state.get("section") returns None when not set
        display_current_section()

        # None should not match any condition, so no functions should be called
        mock_triage.assert_not_called()
        mock_welcome.assert_not_called()
        mock_getting_started.assert_not_called()
        mock_process_check.assert_not_called()
        mock_upload_result.assert_not_called()
        mock_generate_report.assert_not_called()


class TestSetCustomWidthLayout:
    """
    Test cases for set_custom_width_layout function.
    """

    def test_set_custom_width_layout_page_config(self, mocker):
        """
        Test that set_custom_width_layout sets the page configuration.
        """
        mock_set_page_config = mocker.patch("streamlit.set_page_config")
        mocker.patch("streamlit.markdown")

        set_custom_width_layout()

        # Should call set_page_config with correct parameters
        mock_set_page_config.assert_called_once_with(
            page_title="AI Verify Process Checks Tool for Generative AI",
            layout="centered",
            page_icon="assets/images/favicon.jpg",
        )

    def test_set_custom_width_layout_custom_css(self, mocker):
        """
        Test that set_custom_width_layout applies custom CSS for container width.
        """
        mocker.patch("streamlit.set_page_config")
        mock_markdown = mocker.patch("streamlit.markdown")

        set_custom_width_layout()

        # Should call markdown with CSS for container width
        mock_markdown.assert_called_once()
        css_content = mock_markdown.call_args[0][0]

        assert ".block-container" in css_content
        assert "max-width: 1000px" in css_content
        assert mock_markdown.call_args[1]["unsafe_allow_html"] is True


class TestStartHttpServer:
    """
    Test cases for start_http_server function.
    """

    def test_start_http_server_creates_server(self, mocker):
        """
        Test that start_http_server creates a TCP server on port 8000.
        """
        mock_tcp_server = mocker.patch("socketserver.TCPServer")
        mock_server_instance = MagicMock()
        mock_tcp_server.return_value.__enter__.return_value = mock_server_instance

        start_http_server()

        # Should create TCP server on port 8000
        mock_tcp_server.assert_called_once()
        args = mock_tcp_server.call_args[0]
        assert args[0] == ("", 8000)
        assert args[1] == http.server.SimpleHTTPRequestHandler

        # Should call serve_forever
        mock_server_instance.serve_forever.assert_called_once()

    def test_start_http_server_prints_message(self, mocker, capsys):
        """
        Test that start_http_server prints serving message.
        """
        mock_tcp_server = mocker.patch("socketserver.TCPServer")
        mock_server_instance = MagicMock()
        mock_tcp_server.return_value.__enter__.return_value = mock_server_instance

        start_http_server()

        # Check that message is printed
        captured = capsys.readouterr()
        assert "Serving at port 8000" in captured.out


class TestMainFunction:
    """
    Test cases for the main function.
    """

    def test_main_initializes_session_state(self, mocker):
        """
        Test that main function initializes session state when not set.
        """
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_logger = mocker.patch("streamlit_app.logger")

        # Mock all the other functions that main calls
        mocker.patch("streamlit_app.set_custom_width_layout")
        mocker.patch("streamlit_app.apply_custom_css")
        mocker.patch("streamlit_app.display_sections_bar")
        mocker.patch("streamlit_app.display_current_section")
        mocker.patch("threading.Thread")

        main()

        # Should initialize section to 0
        assert mock_session_state["section"] == 0
        mock_logger.info.assert_called_with("Initializing the application.")

    def test_main_does_not_reinitialize_session_state(self, mocker):
        """
        Test that main function does not reinitialize session state when already set.
        """
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_logger = mocker.patch("streamlit_app.logger")

        # Set section already
        mock_session_state["section"] = 3

        # Mock all the other functions that main calls
        mocker.patch("streamlit_app.set_custom_width_layout")
        mocker.patch("streamlit_app.apply_custom_css")
        mocker.patch("streamlit_app.display_sections_bar")
        mocker.patch("streamlit_app.display_current_section")
        mocker.patch("threading.Thread")

        main()

        # Should not change existing section value
        assert mock_session_state["section"] == 3
        mock_logger.info.assert_not_called()

    def test_main_starts_http_server_once(self, mocker):
        """
        Test that main function starts HTTP server only once.
        """
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_thread = mocker.patch("threading.Thread")

        # Mock all the other functions that main calls
        mocker.patch("streamlit_app.set_custom_width_layout")
        mocker.patch("streamlit_app.apply_custom_css")
        mocker.patch("streamlit_app.display_sections_bar")
        mocker.patch("streamlit_app.display_current_section")

        main()

        # Should create and start a daemon thread
        mock_thread.assert_called_once()
        thread_args = mock_thread.call_args
        assert thread_args[1]["target"].__name__ == "start_http_server"

        # Thread should be set as daemon and started
        thread_instance = mock_thread.return_value
        assert thread_instance.daemon is True
        thread_instance.start.assert_called_once()

        # Should set server_started flag
        assert mock_session_state["server_started"] is True

    def test_main_does_not_restart_server(self, mocker):
        """
        Test that main function does not restart HTTP server when already started.
        """
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_thread = mocker.patch("threading.Thread")

        # Set server as already started
        mock_session_state["server_started"] = True

        # Mock all the other functions that main calls
        mocker.patch("streamlit_app.set_custom_width_layout")
        mocker.patch("streamlit_app.apply_custom_css")
        mocker.patch("streamlit_app.display_sections_bar")
        mocker.patch("streamlit_app.display_current_section")

        main()

        # Should not create new thread when server already started
        mock_thread.assert_not_called()

    def test_main_calls_all_functions(self, mocker):
        """
        Test that main function calls all required UI functions.
        """
        mocker.patch("streamlit.session_state", new_callable=dict)

        mock_set_layout = mocker.patch("streamlit_app.set_custom_width_layout")
        mock_apply_css = mocker.patch("streamlit_app.apply_custom_css")
        mock_display_bar = mocker.patch("streamlit_app.display_sections_bar")
        mock_display_section = mocker.patch("streamlit_app.display_current_section")
        mocker.patch("threading.Thread")

        main()

        # Should call all UI setup functions
        mock_set_layout.assert_called_once()
        mock_apply_css.assert_called_once()
        mock_display_bar.assert_called_once()
        mock_display_section.assert_called_once()


class TestEdgeCases:
    """
    Test cases for edge cases and boundary conditions.
    """

    def test_display_sections_bar_with_high_section_number(self, mocker):
        """
        Test sections bar behavior with section number higher than expected.
        """
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_markdown = mocker.patch("streamlit.markdown")

        mocker.patch.dict("streamlit.session_state", {"section": 10})

        display_sections_bar()

        # Should still display sections bar
        mock_markdown.assert_called_once()

    def test_display_current_section_with_invalid_section(self, mocker):
        """
        Test display_current_section with section number not in range 0-5.
        """
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_triage = mocker.patch("streamlit_app.triage")

        mocker.patch.dict("streamlit.session_state", {"section": 99})

        display_current_section()

        # Should not call any display function for invalid section
        mock_triage.assert_not_called()

    def test_main_with_thread_creation_error(self, mocker):
        """
        Test main function behavior when thread creation fails.
        """
        mocker.patch("streamlit.session_state", new_callable=dict)
        mocker.patch("threading.Thread", side_effect=Exception("Thread error"))

        # Mock all the other functions that main calls
        mocker.patch("streamlit_app.set_custom_width_layout")
        mocker.patch("streamlit_app.apply_custom_css")
        mocker.patch("streamlit_app.display_sections_bar")
        mocker.patch("streamlit_app.display_current_section")

        # Should raise exception when thread creation fails
        with pytest.raises(Exception, match="Thread error"):
            main()
