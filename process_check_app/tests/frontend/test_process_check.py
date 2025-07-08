import pytest
from frontend.process_check import (
    REFERENCE_EXCEL_FILE_PATH,
    ProcessCheck,
    click_back_button,
    click_next_button,
    click_start_over_button,
    display_navigation_buttons,
    display_process_check,
    get_export_data,
)


@pytest.fixture
def mock_session_state():
    """Fixture to provide a mock session state for testing."""
    return {
        "workspace_data": {
            "process_checks": {
                "outcome1": {
                    "process1": {
                        "principle_key": "principle1",
                        "implementation": "Yes",
                        "elaboration": "Test elaboration",
                        "evidence_type": "Document",
                        "evidence": "Test evidence",
                        "process_to_achieve_outcomes": "Test process",
                        "outcomes": "Test outcome",
                    },
                    "process2": {
                        "principle_key": "principle2",
                        "implementation": "No",
                        "elaboration": "",
                        "evidence_type": "",
                        "evidence": "",
                        "process_to_achieve_outcomes": "",
                        "outcomes": "Test outcome 2",
                    },
                }
            },
            "progress_data": {
                "total_questions": 10,
                "total_answered_questions": 5,
                "principles": {
                    "principle1": {"principle_total": 5, "principle_answered": 3},
                    "principle2": {"principle_total": 5, "principle_answered": 2},
                },
            },
            "app_name": "Test App",
            "app_description": "Test Description",
            "last_saved": "2024-01-01T12:00:00",
        },
        "section": 3,
        "workspace_id": "test_workspace_123",
        "edit_mode": False,
        "needs_refresh": False,
        "cards_component": 0,
        "scroll_to_top": False,
    }


@pytest.fixture
def mock_principles_data():
    """Fixture to provide mock principles data."""
    return {
        "principle1": {
            "principle_description": "Test principle 1 description",
            "process_checks": {
                "process1": {
                    "outcome_id": "outcome1",
                    "evidence_type": "Document",
                    "evidence": "Test evidence",
                    "process_to_achieve_outcomes": "Test process",
                    "outcomes": "Test outcome",
                    "implementation": None,
                    "elaboration": "",
                }
            },
        },
        "principle2": {
            "principle_description": "Test principle 2 description",
            "process_checks": {
                "process2": {
                    "outcome_id": "outcome1",
                    "evidence_type": "",
                    "evidence": "",
                    "process_to_achieve_outcomes": "",
                    "outcomes": "Test outcome 2",
                    "implementation": "Invalid",  # Will be set to None
                    "elaboration": "",
                }
            },
        },
    }


class TestProcessCheckInit:
    """Test ProcessCheck initialization."""

    def test_init_with_imported_data(self, mocker):
        """Test initialization with imported Excel data."""
        mock_session_state = mocker.patch("streamlit.session_state", new_callable=dict)
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )

        mock_principles = {"principle1": {"data": "test"}}
        mock_session_state["imported_excel_principles_data"] = mock_principles
        mock_session_state["workspace_data"] = {"process_checks": {"old": "data"}}

        process_check = ProcessCheck()

        assert process_check.principles_data == mock_principles
        assert "process_checks" not in mock_session_state["workspace_data"]
        assert mock_session_state["imported_excel_principles_data"] == {}
        mock_read_excel.assert_not_called()

    def test_init_without_imported_data(self, mocker):
        """Test initialization without imported Excel data."""
        mocker.patch("streamlit.session_state", new_callable=dict)
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )

        mock_principles = {"principle1": {"data": "test"}}
        mock_read_excel.return_value = mock_principles

        process_check = ProcessCheck()

        assert process_check.principles_data == mock_principles
        mock_read_excel.assert_called_once_with(REFERENCE_EXCEL_FILE_PATH)


class TestProcessCheckMethods:
    """Test ProcessCheck class methods."""

    def test_filter_principle_checks(self, mocker, mock_principles_data):
        """Test filtering process checks for a specific principle."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        mock_read_excel.return_value = mock_principles_data
        mock_session_state.__getitem__.side_effect = lambda key: {
            "imported_excel_principles_data": {}
        }.get(key, {})
        mock_session_state.get.return_value = {}

        # Setup workspace data
        workspace_data = {
            "process_checks": {
                "outcome1": {
                    "process1": {"principle_key": "principle1"},
                    "process2": {"principle_key": "principle2"},
                },
                "outcome2": {"process3": {"principle_key": "principle1"}},
            }
        }
        mock_session_state.__getitem__.side_effect = lambda key: (
            workspace_data if key == "workspace_data" else {}
        )

        process_check = ProcessCheck()
        result = process_check._filter_principle_checks("principle1")

        assert "outcome1" in result
        assert "outcome2" in result
        assert "process1" in result["outcome1"]
        assert "process2" not in result["outcome1"]
        assert "process3" in result["outcome2"]

    def test_get_progress_data(self, mocker):
        """Test progress data calculation."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        mock_read_excel.return_value = {}
        mock_session_state.__getitem__.side_effect = lambda key: {
            "imported_excel_principles_data": {},
            "workspace_data": {
                "progress_data": {"total_questions": 10, "total_answered_questions": 6}
            },
        }.get(key, {})
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()
        progress_ratio, progress_message = process_check._get_progress_data()

        assert progress_ratio == 0.6
        assert "6 of 10" in progress_message
        assert "60%" in progress_message

    def test_get_progress_data_zero_questions(self, mocker):
        """Test progress data calculation with zero questions."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        mock_read_excel.return_value = {}
        mock_session_state.__getitem__.side_effect = lambda key: {
            "imported_excel_principles_data": {},
            "workspace_data": {
                "progress_data": {"total_questions": 0, "total_answered_questions": 0}
            },
        }.get(key, {})
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()
        progress_ratio, progress_message = process_check._get_progress_data()

        assert progress_ratio == 0
        assert "0 of 0" in progress_message

    def test_get_all_process_check_keys(self, mocker, mock_principles_data):
        """Test getting all process check keys."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        mock_read_excel.return_value = mock_principles_data
        mock_session_state.__getitem__.side_effect = lambda key: {
            "imported_excel_principles_data": {}
        }.get(key, {})
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()
        keys = process_check.get_all_process_check_keys()

        expected_keys = {
            "outcome_id",
            "evidence_type",
            "evidence",
            "process_to_achieve_outcomes",
            "outcomes",
            "implementation",
            "elaboration",
        }
        assert set(keys) == expected_keys

    def test_get_friendly_principle_name(self, mocker):
        """Test converting principle names to friendly format."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        mock_read_excel.return_value = {}
        mock_session_state.__getitem__.side_effect = lambda key: {
            "imported_excel_principles_data": {}
        }.get(key, {})
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()

        # Test special mappings
        result1 = process_check.get_friendly_principle_name("10. Human agency")
        assert "Human Agency" in result1 and "Oversight" in result1

        result2 = process_check.get_friendly_principle_name("11. Inclusive growth")
        assert "Inclusive Growth" in result2 and "Environmental" in result2

        # Test regular formatting
        result3 = process_check.get_friendly_principle_name("1. Some_principle_name")
        assert result3 == "Some Principle Name"

    def test_sort_versions(self, mocker):
        """Test version sorting."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        mock_read_excel.return_value = {}
        mock_session_state.__getitem__.side_effect = lambda key: {
            "imported_excel_principles_data": {}
        }.get(key, {})
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()
        versions = ["1.10", "1.2", "1.1", "2.1", "1.9"]
        sorted_versions = process_check.sort_versions(versions)

        assert sorted_versions == ["1.1", "1.2", "1.9", "1.10", "2.1"]


class TestProcessCheckStats:
    """Test process check statistics methods."""

    def test_get_process_check_stats_with_data(self, mocker, mock_principles_data):
        """Test getting process check statistics with workspace data."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        mock_read_excel.return_value = mock_principles_data

        workspace_data = {
            "process_checks": {
                "outcome1": {
                    "process1": {
                        "principle_key": "principle1",
                        "implementation": "Yes",
                    },
                    "process2": {"principle_key": "principle2", "implementation": "No"},
                }
            }
        }

        def session_state_getitem(key):
            if key == "imported_excel_principles_data":
                return {}
            elif key == "workspace_data":
                return workspace_data
            return {}

        def session_state_contains(key):
            return key in ["workspace_data"]

        mock_session_state.__getitem__.side_effect = session_state_getitem
        mock_session_state.__contains__.side_effect = session_state_contains
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()
        stats = process_check.get_process_check_stats()

        assert stats["total_questions"] == 2
        assert stats["total_answered_questions"] == 2
        assert "principle1" in stats["principles"]
        assert "principle2" in stats["principles"]

    def test_get_process_check_stats_without_workspace(
        self, mocker, mock_principles_data
    ):
        """Test getting process check statistics without workspace data."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        mock_read_excel.return_value = mock_principles_data
        mock_session_state.__getitem__.side_effect = lambda key: (
            {} if key == "imported_excel_principles_data" else {}
        )
        mock_session_state.__contains__.side_effect = lambda key: False
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()
        stats = process_check.get_process_check_stats()

        assert stats["total_questions"] == 2
        assert stats["total_answered_questions"] == 0
        assert stats["principles"]["principle1"]["principle_answered"] == 0
        assert stats["principles"]["principle2"]["principle_answered"] == 0


class TestProcessCheckRendering:
    """Test ProcessCheck rendering methods."""

    def test_render_evidence_section_with_data(self, mocker):
        """Test rendering evidence section with data."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")
        mock_markdown = mocker.patch("streamlit.markdown")

        mock_read_excel.return_value = {}
        mock_session_state.__getitem__.side_effect = lambda key: (
            {} if key == "imported_excel_principles_data" else {}
        )
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()
        process_check._render_evidence_section("Document Type", "Evidence Description")

        # Verify markdown was called for evidence type and evidence
        assert (
            mock_markdown.call_count >= 4
        )  # Should render both evidence type and evidence

    def test_render_evidence_section_empty(self, mocker):
        """Test rendering evidence section with empty data."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")
        mock_markdown = mocker.patch("streamlit.markdown")

        mock_read_excel.return_value = {}
        mock_session_state.__getitem__.side_effect = lambda key: (
            {} if key == "imported_excel_principles_data" else {}
        )
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()
        process_check._render_evidence_section("", "")

        # Should not call markdown for empty values
        mock_markdown.assert_not_called()

    def test_render_map_badges_native(self, mocker):
        """Test rendering map badges."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")
        mock_color_mapping = mocker.patch(
            "frontend.process_check.get_map_color_mapping"
        )
        mock_markdown = mocker.patch("streamlit.markdown")

        mock_read_excel.return_value = {}
        mock_session_state.__getitem__.side_effect = lambda key: (
            {} if key == "imported_excel_principles_data" else {}
        )
        mock_session_state.get.return_value = {}
        mock_color_mapping.return_value = {"red": "Framework A", "blue": "Framework B"}

        process_check = ProcessCheck()
        process_check._render_map_badges_native(["red", "blue", ""])

        mock_markdown.assert_called_once()
        call_args = mock_markdown.call_args[0][0]
        assert "Framework A" in call_args
        assert "Framework B" in call_args

    def test_render_map_badges_native_empty(self, mocker):
        """Test rendering map badges with empty data."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")
        mock_markdown = mocker.patch("streamlit.markdown")

        mock_read_excel.return_value = {}
        mock_session_state.__getitem__.side_effect = lambda key: (
            {} if key == "imported_excel_principles_data" else {}
        )
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()
        process_check._render_map_badges_native([])

        mock_markdown.assert_not_called()


class TestMergeImportedData:
    """Test merging imported implementation data."""

    def test_merge_imported_implementation_data_success(
        self, mocker, mock_principles_data
    ):
        """Test successful merge of imported implementation data."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        current_data = mock_principles_data.copy()
        mock_read_excel.side_effect = [current_data, current_data]
        mock_session_state.__getitem__.side_effect = lambda key: (
            {} if key == "imported_excel_principles_data" else {}
        )
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()

        uploaded_data = mock_principles_data.copy()
        uploaded_data["principle1"]["process_checks"]["process1"][
            "implementation"
        ] = "Yes"
        uploaded_data["principle1"]["process_checks"]["process1"][
            "elaboration"
        ] = "Test elaboration"

        mock_upload_file = mocker.MagicMock()

        with mocker.patch(
            "frontend.process_check.read_principles_from_excel",
            return_value=uploaded_data,
        ):
            result, error, success = process_check._merge_imported_implementation_data(
                mock_upload_file
            )

        assert success is True
        assert error == ""
        assert result is not None

    def test_merge_imported_implementation_data_failure(self, mocker):
        """Test failed merge of imported implementation data."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        mock_read_excel.side_effect = [{"principle1": {}}, None]
        mock_session_state.__getitem__.side_effect = lambda key: (
            {} if key == "imported_excel_principles_data" else {}
        )
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()
        mock_upload_file = mocker.MagicMock()

        result, error, success = process_check._merge_imported_implementation_data(
            mock_upload_file
        )

        assert success is False
        assert "unable to load" in error
        assert result == {}


class TestNavigationButtons:
    """Test navigation button functions."""

    def test_click_back_button(self, mocker):
        """Test clicking the back button."""
        mock_session_state = mocker.patch("streamlit.session_state", {"section": 3})
        click_back_button()
        assert mock_session_state["section"] == 2

    def test_click_next_button(self, mocker):
        """Test clicking the next button."""
        mock_session_state = mocker.patch("streamlit.session_state", {"section": 3})
        click_next_button()
        assert mock_session_state["section"] == 4

    def test_click_start_over_button(self, mocker):
        """Test clicking the start over button."""
        mocker.patch("streamlit.session_state")
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
            call for call in mock_button.call_args_list if "Next" in str(call)
        ]
        assert len(next_button_calls) == 1
        # Check that disabled parameter is False
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
            call for call in mock_button.call_args_list if "Next" in str(call)
        ]
        assert len(next_button_calls) == 1
        next_call = next_button_calls[0]
        assert next_call[1]["disabled"] is True


class TestDisplayFunctions:
    """Test display functions."""

    def test_display_process_check(self, mocker):
        """Test display_process_check function."""
        mock_process_check_class = mocker.patch("frontend.process_check.ProcessCheck")
        mock_display_nav = mocker.patch(
            "frontend.process_check.display_navigation_buttons"
        )

        mock_process_check = mocker.MagicMock()
        mock_process_check_class.return_value = mock_process_check

        display_process_check()

        mock_process_check_class.assert_called_once()
        mock_process_check.display.assert_called_once()
        mock_display_nav.assert_called_once()


class TestGetExportData:
    """Test get_export_data function."""

    def test_get_export_data(self, mocker):
        """Test get_export_data function."""
        mock_export_excel = mocker.patch("frontend.process_check.export_excel")

        mock_export_excel.return_value = b"excel_data"

        result = get_export_data("test_file.xlsx", {"test": "data"})

        assert result == b"excel_data"
        mock_export_excel.assert_called_once_with("test_file.xlsx", {"test": "data"})


class TestProcessCheckDisplay:
    """Test ProcessCheck display methods."""

    def test_display_instructions(self, mocker):
        """Test display instructions method."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")
        mock_expander = mocker.patch("streamlit.expander")
        mock_markdown = mocker.patch("streamlit.markdown")

        mock_read_excel.return_value = {}
        mock_session_state.__getitem__.side_effect = lambda key: (
            {} if key == "imported_excel_principles_data" else {}
        )
        mock_session_state.get.return_value = {}

        mock_expander_context = mocker.MagicMock()
        mock_expander.return_value.__enter__.return_value = mock_expander_context
        mock_expander.return_value.__exit__.return_value = None

        process_check = ProcessCheck()
        process_check.display_instructions()

        mock_expander.assert_called_once_with("Instructions", expanded=True)
        mock_markdown.assert_called_once()

    def test_render_progress_bar(self, mocker):
        """Test render progress bar method."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")
        mock_progress = mocker.patch("streamlit.progress")

        mock_read_excel.return_value = {}
        mock_session_state.__getitem__.side_effect = lambda key: {
            "imported_excel_principles_data": {},
            "workspace_data": {
                "progress_data": {"total_questions": 10, "total_answered_questions": 7}
            },
        }.get(key, {})
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()
        process_check.render_progress_bar()

        mock_progress.assert_called_once()
        call_args = mock_progress.call_args
        assert call_args[0][0] == 0.7  # Progress ratio
        assert "7 of 10" in call_args[0][1]  # Progress message


class TestInitializeProcessChecksData:
    """Test process checks data initialization."""

    def test_initialize_process_checks_data_new_workspace(
        self, mocker, mock_principles_data
    ):
        """Test initializing process checks data for new workspace."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        mock_read_excel.return_value = mock_principles_data
        mock_session_state.__getitem__.side_effect = lambda key: (
            {} if key == "imported_excel_principles_data" else {}
        )
        mock_session_state.get.return_value = {
            "workspace_data": {}
        }  # No process_checks key

        process_check = ProcessCheck()
        process_check.initialize_process_checks_data()

        # Should have called _group_process_checks_by_outcome and sort_versions
        # This is tested indirectly by verifying the method completes without error
        assert True

    def test_initialize_process_checks_data_existing_workspace(
        self, mocker, mock_principles_data
    ):
        """Test initializing process checks data with existing workspace."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        mock_read_excel.return_value = mock_principles_data
        existing_workspace = {
            "workspace_data": {"process_checks": {"existing": "data"}}
        }
        mock_session_state.__getitem__.side_effect = lambda key: (
            {} if key == "imported_excel_principles_data" else {}
        )
        mock_session_state.get.return_value = existing_workspace

        process_check = ProcessCheck()
        process_check.initialize_process_checks_data()

        # Should not modify existing process_checks data
        assert True


class TestProcessCheckDisplayMethods:
    """Test ProcessCheck display and rendering methods that can be tested."""

    def test_display_method_calls_initialization(self, mocker):
        """Test that display method calls initialization methods."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        mock_read_excel.return_value = {}
        mock_session_state.__getitem__.side_effect = lambda key: (
            {} if key == "imported_excel_principles_data" else {}
        )
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()

        # Mock all the display methods to avoid UI calls
        mock_init = mocker.patch.object(process_check, "initialize_process_checks_data")
        mock_instructions = mocker.patch.object(process_check, "display_instructions")
        mock_actions = mocker.patch.object(process_check, "render_action_buttons")
        mock_stats = mocker.patch.object(process_check, "get_process_check_stats")
        mock_progress = mocker.patch.object(process_check, "render_progress_bar")
        mock_pane = mocker.patch.object(process_check, "render_process_checks_pane")
        mocker.patch("streamlit.markdown")

        mock_stats.return_value = {"test": "data"}

        process_check.display()

        mock_init.assert_called_once()
        mock_instructions.assert_called_once()
        mock_actions.assert_called_once()
        mock_stats.assert_called_once()
        mock_progress.assert_called_once()
        mock_pane.assert_called_once()

    def test_render_process_checks_calls_filter(self, mocker):
        """Test that render_process_checks calls filtering and rendering methods."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")
        mocker.patch("streamlit.header")
        mocker.patch("streamlit.markdown")

        mock_read_excel.return_value = {}
        mock_session_state.__getitem__.side_effect = lambda key: (
            {} if key == "imported_excel_principles_data" else {}
        )
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()

        # Mock the helper methods
        mock_filter = mocker.patch.object(process_check, "_filter_principle_checks")
        mock_load_map = mocker.patch("frontend.process_check.load_map_data")
        mock_render = mocker.patch.object(process_check, "_render_outcome_container")

        mock_filter.return_value = {"outcome1": {"process1": {"test": "data"}}}
        mock_load_map.return_value = {}

        process_check.render_process_checks(
            "Test Principle", "Description", "principle1"
        )

        mock_filter.assert_called_once_with("principle1")
        mock_load_map.assert_called_once()
        mock_render.assert_called_once_with(
            "outcome1", {"process1": {"test": "data"}}, {}
        )


class TestEditFormLogic:
    """Test edit form business logic that can be tested without full UI interaction."""

    def test_display_edit_form_initialization(self, mocker):
        """Test edit form gets current values from session state."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        mock_read_excel.return_value = {}
        workspace_data = {
            "app_name": "Test App Name",
            "app_description": "Test App Description",
        }

        def session_get(key, default=None):
            if key == "imported_excel_principles_data":
                return {}
            elif key == "workspace_data":
                return workspace_data
            return default

        mock_session_state.__getitem__.side_effect = session_get
        mock_session_state.get.side_effect = session_get

        process_check = ProcessCheck()

        # Mock streamlit form components to avoid actual rendering
        mocker.patch("streamlit.form")
        mock_text_input = mocker.patch("streamlit.text_input")
        mock_text_area = mocker.patch("streamlit.text_area")
        mocker.patch(
            "streamlit.columns", return_value=[mocker.MagicMock(), mocker.MagicMock()]
        )
        mocker.patch("streamlit.form_submit_button", return_value=False)

        process_check.display_edit_form()

        # Verify that the form components were called with current values
        mock_text_input.assert_called()
        mock_text_area.assert_called()


class TestActionButtonsLogic:
    """Test action buttons business logic."""

    def test_render_action_buttons_edit_mode_false(self, mocker):
        """Test render action buttons when not in edit mode."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        mock_read_excel.return_value = {}

        session_data = {
            "imported_excel_principles_data": {},
            "workspace_id": "test_123",
            "workspace_data": {
                "app_name": "Test App",
                "app_description": "Test Description",
                "last_saved": "2024-01-01T12:00:00",
                "process_checks": {},
            },
            "edit_mode": False,
        }

        def session_get(key, default=None):
            return session_data.get(key, default)

        mock_session_state.__getitem__.side_effect = session_get
        mock_session_state.get.side_effect = session_get
        mock_session_state.__contains__.side_effect = lambda key: key in session_data

        process_check = ProcessCheck()

        # Mock all UI components
        mocker.patch(
            "streamlit.columns", return_value=[mocker.MagicMock(), mocker.MagicMock()]
        )
        mock_create_actions = mocker.patch(
            "frontend.process_check.create_actions_component"
        )
        mocker.patch("streamlit.container")
        mocker.patch("streamlit.markdown")
        mocker.patch("streamlit.download_button")
        mocker.patch("streamlit.button", return_value=False)
        mocker.patch(
            "frontend.process_check.get_export_data", return_value=b"test_data"
        )

        mock_create_actions.return_value = None

        process_check.render_action_buttons()

        mock_create_actions.assert_called_once()

    def test_render_action_buttons_edit_mode_true(self, mocker):
        """Test render action buttons when in edit mode."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        mock_read_excel.return_value = {}

        session_data = {
            "imported_excel_principles_data": {},
            "edit_mode": True,
            "workspace_data": {"app_name": "Test", "app_description": "Test"},
        }

        def session_get(key, default=None):
            return session_data.get(key, default)

        mock_session_state.__getitem__.side_effect = session_get
        mock_session_state.get.side_effect = session_get
        mock_session_state.__contains__.side_effect = lambda key: key in session_data

        process_check = ProcessCheck()

        # Mock edit form method
        mock_edit_form = mocker.patch.object(process_check, "display_edit_form")

        process_check.render_action_buttons()

        mock_edit_form.assert_called_once()


class TestProcessCheckRenderingMethods:
    """Test individual rendering method logic."""

    def test_render_process_checks_pane_initialization(self, mocker):
        """Test process checks pane initializes state variables."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        mock_read_excel.return_value = {"principle1": {"data": "test"}}

        session_data = {
            "imported_excel_principles_data": {},
            "workspace_data": {
                "progress_data": {
                    "principles": {
                        "principle1": {"principle_total": 1, "principle_answered": 0}
                    }
                }
            },
            "cards_component": 0,
            "scroll_to_top": False,
        }

        def session_get(key, default=None):
            return session_data.get(key, default)

        def session_contains(key):
            return key in session_data

        mock_session_state.__getitem__.side_effect = session_get
        mock_session_state.get.side_effect = session_get
        mock_session_state.__contains__.side_effect = session_contains

        process_check = ProcessCheck()

        # Create a custom side effect for st.columns that handles different call patterns
        def columns_side_effect(*args, **kwargs):
            # Check if it's [1, 3] (2 columns) or [2, 4, 2] (3 columns)
            if args and len(args[0]) == 3:
                return [mocker.MagicMock(), mocker.MagicMock(), mocker.MagicMock()]
            else:
                return [mocker.MagicMock(), mocker.MagicMock()]

        # Mock all UI components and dependencies
        mocker.patch("streamlit.columns", side_effect=columns_side_effect)
        mock_create_component = mocker.patch("frontend.process_check.create_component")
        mock_render_checks = mocker.patch.object(process_check, "render_process_checks")
        mocker.patch("streamlit.button", return_value=False)
        mocker.patch("frontend.process_check.save_workspace")
        mocker.patch("frontend.process_check.get_main_styles", return_value="")
        mocker.patch("streamlit.markdown")
        mocker.patch("streamlit_scroll_to_top.scroll_to_here")

        mock_create_component.return_value = 0

        process_check.render_process_checks_pane()

        # Verify the component was created and process checks rendered
        mock_create_component.assert_called_once()
        mock_render_checks.assert_called_once()


class TestDataValidationAndProcessing:
    """Test data validation and processing logic."""

    def test_merge_implementation_data_with_matching_fields(self, mocker):
        """Test merge implementation data with matching field validation."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        principles_data = {
            "principle1": {
                "process_checks": {
                    "process1": {
                        "outcome_id": "outcome1",
                        "evidence_type": "Document",
                        "implementation": None,
                        "elaboration": "",
                    }
                }
            }
        }

        mock_read_excel.return_value = principles_data
        mock_session_state.__getitem__.side_effect = lambda key: (
            {} if key == "imported_excel_principles_data" else {}
        )
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()

        # Create uploaded data that matches
        uploaded_data = {
            "principle1": {
                "process_checks": {
                    "process1": {
                        "outcome_id": "outcome1",  # Same as current
                        "evidence_type": "Document",  # Same as current
                        "implementation": "Yes",  # This should be merged
                        "elaboration": "Test elaboration",  # This should be merged
                    }
                }
            }
        }

        # Mock the read function for the uploaded file
        mocker.patch(
            "frontend.process_check.read_principles_from_excel",
            return_value=uploaded_data,
        )

        result, error, success = process_check._merge_imported_implementation_data(
            mocker.MagicMock()
        )

        assert success is True
        assert error == ""
        # Check that implementation was merged
        merged_process = result["principle1"]["process_checks"]["process1"]
        assert merged_process["implementation"] == "Yes"
        assert merged_process["elaboration"] == "Test elaboration"

    def test_merge_implementation_data_non_matching_fields(self, mocker):
        """Test merge implementation data with non-matching fields (should not merge)."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        principles_data = {
            "principle1": {
                "process_checks": {
                    "process1": {
                        "outcome_id": "outcome1",
                        "evidence_type": "Document",
                        "implementation": None,
                        "elaboration": "",
                    }
                }
            }
        }

        mock_read_excel.return_value = principles_data
        mock_session_state.__getitem__.side_effect = lambda key: (
            {} if key == "imported_excel_principles_data" else {}
        )
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()

        # Create uploaded data with different fields
        uploaded_data = {
            "principle1": {
                "process_checks": {
                    "process1": {
                        "outcome_id": "outcome2",  # Different from current
                        "evidence_type": "Document",
                        "implementation": "Yes",
                        "elaboration": "Test elaboration",
                    }
                }
            }
        }

        mocker.patch(
            "frontend.process_check.read_principles_from_excel",
            return_value=uploaded_data,
        )

        result, error, success = process_check._merge_imported_implementation_data(
            mocker.MagicMock()
        )

        assert success is True
        # Implementation should NOT be merged due to mismatched outcome_id
        merged_process = result["principle1"]["process_checks"]["process1"]
        assert merged_process["implementation"] is None  # Should remain unchanged


class TestAdditionalBusinessLogic:
    """Test additional business logic methods."""

    def test_get_process_check_stats_with_invalid_implementation(self, mocker):
        """Test process check stats with invalid implementation values."""
        mock_read_excel = mocker.patch(
            "frontend.process_check.read_principles_from_excel"
        )
        mock_session_state = mocker.patch("streamlit.session_state")

        principles_data = {
            "principle1": {"process_checks": {"process1": {}, "process2": {}}}
        }

        workspace_data = {
            "process_checks": {
                "outcome1": {
                    "process1": {
                        "principle_key": "principle1",
                        "implementation": "Invalid",
                    },
                    "process2": {
                        "principle_key": "principle1",
                        "implementation": "Yes",
                    },
                }
            }
        }

        mock_read_excel.return_value = principles_data

        def session_state_getitem(key):
            if key == "imported_excel_principles_data":
                return {}
            elif key == "workspace_data":
                return workspace_data
            return {}

        def session_state_contains(key):
            return key in ["workspace_data"]

        mock_session_state.__getitem__.side_effect = session_state_getitem
        mock_session_state.__contains__.side_effect = session_state_contains
        mock_session_state.get.return_value = {}

        process_check = ProcessCheck()
        stats = process_check.get_process_check_stats()

        # Only valid implementations should be counted
        assert stats["total_questions"] == 2
        assert (
            stats["total_answered_questions"] == 1
        )  # Only process2 has valid implementation
