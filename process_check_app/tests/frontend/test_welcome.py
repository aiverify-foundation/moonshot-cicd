import pytest
from frontend.welcome import (
    click_back_button,
    click_next_button,
    click_start_over_button,
    display_navigation_buttons,
    welcome,
)


class TestClickButtons:
    """
    Test cases for button click handlers and navigation functions.
    """

    def test_click_next_button(self, mocker):
        """
        Test that click_next_button increments the section counter by 1.
        """
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_session_state["section"] = 1

        click_next_button()

        assert mock_session_state["section"] == 2

    def test_click_back_button(self, mocker):
        """
        Test that click_back_button decrements the section counter by 1.
        """
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_session_state["section"] = 2

        click_back_button()

        assert mock_session_state["section"] == 1


class TestClickStartOverButton:
    """
    Test cases for the start over button and dialog functionality.

    Note: The actual dialog content cannot be fully tested in unit tests
    due to the @st.dialog decorator creating nested execution contexts.
    """

    def test_click_start_over_button_calls_dialog(self, mocker):
        """
        Test that click_start_over_button uses the dialog decorator with correct title.
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

    def test_click_start_over_button_function_exists(self, mocker):
        """
        Test that the click_start_over_button function exists and is callable without errors.
        """
        # This is a basic test to ensure the function is properly defined
        assert callable(click_start_over_button)

        # Test that it doesn't raise an exception when called
        # (we mock streamlit to avoid actual UI operations)
        mocker.patch("streamlit.dialog")
        mocker.patch("streamlit.write")
        mocker.patch("streamlit.columns")
        mocker.patch("streamlit.button", return_value=False)
        mocker.patch("streamlit.session_state", new_callable=dict)

        try:
            click_start_over_button()
            # If we get here without exception, the test passes
            assert True
        except Exception as e:
            pytest.fail(f"click_start_over_button raised an exception: {e}")


class TestDisplayNavigationButtons:
    """
    Test cases for navigation button display logic and layout structure.
    """

    def test_display_navigation_buttons_section_1(self, mocker):
        """
        Test navigation buttons for section 1 display Home and Next buttons only.
        """
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_button = mocker.patch("streamlit.button")
        mock_markdown = mocker.patch("streamlit.markdown")
        mock_columns = mocker.patch("streamlit.columns")

        mock_session_state["section"] = 1
        mock_columns.return_value = [mocker.MagicMock() for _ in range(4)]

        display_navigation_buttons()

        # Should show divider and buttons
        mock_markdown.assert_called()
        assert mock_button.call_count == 2  # Home and Next buttons

    def test_display_navigation_buttons_margin_and_divider(self, mocker):
        """
        Test that margin and divider are displayed for sections >= 1.
        """
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_markdown = mocker.patch("streamlit.markdown")
        mock_columns = mocker.patch("streamlit.columns")
        mocker.patch("streamlit.button")

        mock_session_state["section"] = 1
        mock_columns.return_value = [mocker.MagicMock() for _ in range(4)]

        display_navigation_buttons()

        # Should call markdown for margin and divider
        assert mock_markdown.call_count >= 2

    def test_display_navigation_buttons_columns_structure(self, mocker):
        """
        Test that navigation buttons use the correct 4-column layout structure.
        """
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_columns = mocker.patch("streamlit.columns")
        mocker.patch("streamlit.button")

        mock_session_state["section"] = 1
        mock_columns.return_value = [mocker.MagicMock() for _ in range(4)]

        display_navigation_buttons()

        # Should create columns with specific layout
        mock_columns.assert_called_with([2, 6, 2, 2])


class TestWelcomeFunction:
    """
    Test cases for the main welcome function and its component rendering.
    """

    def test_welcome_function_renders_components(self, mocker):
        """
        Test that the main welcome function renders all required UI components.
        """
        mock_get_css = mocker.patch("frontend.welcome.get_welcome_custom_css")
        mock_get_mapping = mocker.patch("frontend.welcome.get_map_color_mapping")
        mock_markdown = mocker.patch("streamlit.markdown")
        mock_write = mocker.patch("streamlit.write")
        mock_image = mocker.patch("streamlit.image")
        mock_display_nav = mocker.patch("frontend.welcome.display_navigation_buttons")

        mock_get_css.return_value = "custom-css-styles"
        mock_get_mapping.return_value = {"blue": "NIST", "green": "ISO"}

        welcome()

        # Verify all component types are called
        mock_markdown.assert_called()  # CSS styles and framework badges
        assert mock_write.call_count >= 3  # Multiple content sections
        mock_image.assert_called_once()  # Welcome image
        mock_display_nav.assert_called_once()  # Navigation buttons

    def test_welcome_function_image_properties(self, mocker):
        """
        Test that the welcome image is displayed with correct path and properties.
        """
        mock_get_css = mocker.patch("frontend.welcome.get_welcome_custom_css")
        mock_get_mapping = mocker.patch("frontend.welcome.get_map_color_mapping")
        mock_image = mocker.patch("streamlit.image")
        mocker.patch("streamlit.markdown")
        mocker.patch("streamlit.write")
        mocker.patch("frontend.welcome.display_navigation_buttons")

        mock_get_css.return_value = "styles"
        mock_get_mapping.return_value = {}

        welcome()

        # Verify image is called with use_container_width=True
        mock_image.assert_called_once_with(
            "assets/images/welcome_image.png", use_container_width=True
        )


class TestEdgeCases:
    """
    Test cases for edge cases and boundary conditions in navigation logic.
    """

    def test_navigation_buttons_boundary_sections(self, mocker):
        """
        Test navigation button visibility at boundary section values (sections 4 and 6).
        """
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_button = mocker.patch("streamlit.button")
        mock_columns = mocker.patch("streamlit.columns")

        mock_columns.return_value = [mocker.MagicMock() for _ in range(4)]

        # Test section 4 (boundary for Next button)
        mock_session_state["section"] = 4
        display_navigation_buttons()

        # Should show Next button for section 4
        assert mock_button.call_count == 3  # Home, Back, and Next

        # Reset mocks
        mock_button.reset_mock()

        # Test section 6 (beyond normal range)
        mock_session_state["section"] = 6
        display_navigation_buttons()

        # Should not show Next button for section >= 5
        assert mock_button.call_count == 2  # Home and Back only
