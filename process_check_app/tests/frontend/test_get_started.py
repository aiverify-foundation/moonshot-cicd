from frontend.get_started import (
    click_back_button,
    click_next_button,
    click_start_over_button,
    display_getting_started,
    display_navigation_buttons,
    getting_started,
)


class TestClickButtons:
    """
    Test cases for button click handlers.
    """

    def test_click_back_button(self, mocker):
        """
        Test that click_back_button decrements the section counter.

        Args:
            mocker: pytest-mock fixture for mocking dependencies
        """
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_session_state["section"] = 2

        click_back_button()

        assert mock_session_state["section"] == 1

    def test_click_next_button_workspace_initialized(self, mocker):
        """
        Test click_next_button when workspace is already initialized.

        Args:
            mocker: pytest-mock fixture for mocking dependencies
        """
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_session_state["section"] = 2

        mock_is_workspace_initialized = mocker.patch(
            "frontend.get_started.is_workspace_initialized", return_value=True
        )

        click_next_button()

        assert mock_session_state["section"] == 3
        mock_is_workspace_initialized.assert_called_once()

    def test_click_next_button_workspace_not_initialized(self, mocker):
        """
        Test click_next_button when workspace is not initialized (shows dialog).

        Args:
            mocker: pytest-mock fixture for mocking dependencies
        """
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_session_state["section"] = 1

        mock_is_workspace_initialized = mocker.patch(
            "frontend.get_started.is_workspace_initialized", return_value=False
        )
        mock_dialog = mocker.patch("streamlit.dialog")

        click_next_button()

        mock_dialog.assert_called_once_with("Provide Workspace Details")
        mock_is_workspace_initialized.assert_called_once()


class TestClickStartOverButton:
    """
    Test cases for the start over button functionality.
    """

    def test_click_start_over_button_calls_dialog(self, mocker):
        """
        Test that click_start_over_button uses the dialog decorator.

        Args:
            mocker: pytest-mock fixture for mocking dependencies
        """
        mock_dialog = mocker.patch("streamlit.dialog")

        # Mock streamlit components that might be called
        mocker.patch("streamlit.write")
        mocker.patch(
            "streamlit.columns", return_value=[mocker.MagicMock(), mocker.MagicMock()]
        )
        mocker.patch("streamlit.button", return_value=False)
        mocker.patch("streamlit.session_state", new_callable=dict)

        click_start_over_button()

        mock_dialog.assert_called_once_with("Return to Home Page")


class TestDisplayNavigationButtons:
    """
    Test cases for navigation button display logic.
    """

    def test_display_navigation_buttons_section_2(self, mocker):
        """
        Test navigation buttons for section 2 (all three buttons).

        Args:
            mocker: pytest-mock fixture for mocking dependencies
        """
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_button = mocker.patch("streamlit.button")
        mock_columns = mocker.patch("streamlit.columns")

        mock_session_state["section"] = 2
        mock_columns.return_value = [mocker.MagicMock() for _ in range(4)]

        display_navigation_buttons()

        assert mock_button.call_count == 3  # Home, Back, and Next buttons


class TestDisplayGettingStarted:
    """
    Test cases for the display_getting_started function.
    """

    def test_display_getting_started_renders_components(self, mocker):
        """
        Test that display_getting_started renders all required components.

        Args:
            mocker: pytest-mock fixture for mocking dependencies
        """
        mock_get_styles = mocker.patch("frontend.get_started.get_started_styles")
        mock_markdown = mocker.patch("streamlit.markdown")
        mock_write = mocker.patch("streamlit.write")
        mock_image = mocker.patch("streamlit.image")
        mock_info = mocker.patch("streamlit.info")

        mock_get_styles.return_value = "custom-styles"

        display_getting_started()

        # Verify all component types are called
        mock_markdown.assert_called()  # CSS styles
        assert mock_write.call_count >= 2  # Content sections
        assert mock_image.call_count == 2  # Two images
        mock_info.assert_called_once()  # Info box

    def test_display_getting_started_image_properties(self, mocker):
        """
        Test that images are displayed with correct properties.

        Args:
            mocker: pytest-mock fixture for mocking dependencies
        """
        mock_get_styles = mocker.patch("frontend.get_started.get_started_styles")
        mock_image = mocker.patch("streamlit.image")
        mocker.patch("streamlit.markdown")
        mocker.patch("streamlit.write")
        mocker.patch("streamlit.info")

        mock_get_styles.return_value = "styles"

        display_getting_started()

        # Verify images are called with use_container_width=True
        for call in mock_image.call_args_list:
            if len(call) > 1 and call[1]:
                kwargs = call[1]
                assert kwargs.get("use_container_width", False) is True

    def test_display_getting_started_uses_constants(self, mocker):
        """
        Test that display_getting_started uses the defined constants.

        Args:
            mocker: pytest-mock fixture for mocking dependencies
        """
        mock_get_styles = mocker.patch("frontend.get_started.get_started_styles")
        mock_image = mocker.patch("streamlit.image")
        mocker.patch("streamlit.markdown")
        mocker.patch("streamlit.write")
        mocker.patch("streamlit.info")

        mock_get_styles.return_value = "styles"

        display_getting_started()

        # Verify images are called with the constants
        image_calls = [call[0][0] for call in mock_image.call_args_list]
        assert any("getting_started_diagram.png" in path for path in image_calls)
        assert any("getting_started_how_to_use.png" in path for path in image_calls)


class TestGettingStartedMain:
    """
    Test cases for the main getting_started function.
    """

    def test_getting_started_calls_display_functions(self, mocker):
        """
        Test that getting_started calls the required display functions.

        Args:
            mocker: pytest-mock fixture for mocking dependencies
        """
        mock_display_getting_started = mocker.patch(
            "frontend.get_started.display_getting_started"
        )
        mock_display_navigation_buttons = mocker.patch(
            "frontend.get_started.display_navigation_buttons"
        )

        getting_started()

        mock_display_getting_started.assert_called_once()
        mock_display_navigation_buttons.assert_called_once()
