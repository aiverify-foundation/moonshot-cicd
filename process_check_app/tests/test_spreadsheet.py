import pandas as pd
import pytest
from backend.spreadsheet import (
    carry_forward_merged_values,
    extract_principle_description,
    get_process_data,
    is_matching_process,
    is_valid_process_id,
    matches_ai_type_filter,
    parse_process_check_row,
    process_single_principle_sheet,
    read_principles_from_excel,
    stringify_dict_keys,
    update_merged_cell_values,
    update_row_values,
)


class TestSpreadsheet:
    """Test collection for spreadsheet functions."""

    # ===============================
    # extract_principle_description
    # ===============================
    @pytest.mark.parametrize(
        "test_input,expected",
        [
            ("This is the principle description", "This is the principle description"),
            ("", ""),
            (
                "Principle with special chars: !@#$%^&*()",
                "Principle with special chars: !@#$%^&*()",
            ),
            (123, "123"),
            (3.14159, "3.14159"),
            (True, "True"),
            (None, "None"),
        ],
    )
    def test_extract_principle_description_various_inputs(self, test_input, expected):
        """Test extracting principle description with various input types and values"""
        # Create a test DataFrame with the test input at position [1, 0]
        data = [
            ["Principle Title", "Other Column"],
            [test_input, "More data"],
            ["Additional info", "Even more data"],
        ]
        df = pd.DataFrame(data)

        result = extract_principle_description(df)

        assert result == expected
        assert isinstance(result, str)

    @pytest.mark.parametrize("invalid_input", [123, "not a dataframe", [1, 2, 3]])
    def test_extract_principle_description_invalid_input_types(self, invalid_input):
        """Test that the function handles invalid input types appropriately"""
        with pytest.raises(AttributeError):
            extract_principle_description(invalid_input)  # type: ignore

    # ===============================
    # is_valid_process_id
    # ===============================
    @pytest.mark.parametrize(
        "process_id,expected",
        [
            # Valid process IDs
            ("1.2.3", True),
            ("123.456.789", True),
            ("000.111.222", True),
            ("10.20.30", True),
            ("0.0.0", True),
            ("999.999.999", True),
            ("1.02.3", True),
            ("01.2.3", True),
            # Invalid process IDs
            ("1.2", False),  # too few sections
            ("1.2.3.4", False),  # too many sections
            ("abc.def.ghi", False),  # not digits
            ("1..3", False),  # missing section
            ("1.2.a", False),  # last not digit
            ("a.2.3", False),  # first not digit
            ("1.2.3a", False),  # last has letter
            ("1.2.3 ", False),  # trailing space
            (" 1.2.3", False),  # leading space
            ("1-2-3", False),  # wrong separator
            ("1,2,3", False),  # wrong separator
            ("1.2.3.4.5", False),  # too many sections
            ("", False),  # empty string
            (None, False),  # NoneType
            (123, False),  # integer
            (1.23, False),  # float
            (1.2, False),  # float
            (1.2e3, False),  # float
            (12.34, False),  # float
            (100.200, False),  # float
            (123.456, False),  # float
            ([], False),  # list
            ({}, False),  # dict
            (True, False),  # boolean
            (False, False),  # boolean
        ],
    )
    def test_is_valid_process_id(self, process_id, expected):
        """Test is_valid_process_id with various valid and invalid process IDs"""
        assert is_valid_process_id(process_id) is expected

    # ===============================
    # matches_ai_type_filter
    # ===============================
    @pytest.mark.parametrize(
        "type_of_ai,ai_type_filter,expected",
        [
            # Valid matches
            ("Generative AI", "Generative AI", True),
            ("Generative AI", "Generative", True),
            ("Machine Learning AI", "Machine Learning", True),
            # Non-matches
            ("Machine Learning", "Generative AI", False),
            ("Deep Learning", "Generative AI", False),
            # Edge cases
            ("", "Generative AI", False),
            ("Generative AI", "", True),
            ("", "", True),
        ],
    )
    def test_matches_ai_type_filter(self, type_of_ai, ai_type_filter, expected):
        """Test matches_ai_type_filter with various inputs"""
        result = matches_ai_type_filter(type_of_ai, ai_type_filter)
        assert result is expected

    @pytest.mark.parametrize("invalid_type", [None, 123, True, []])
    def test_matches_ai_type_filter_non_string_inputs(self, invalid_type):
        """Test matches_ai_type_filter with non-string type_of_ai values"""
        result = matches_ai_type_filter(invalid_type, "Generative AI")
        assert result is False

    # ===============================
    # parse_process_check_row
    # ===============================
    @pytest.mark.parametrize(
        "row_data,merged_cell_values,ai_type_filter,expected_result",
        [
            # Valid cases
            (
                {
                    "Inclusive growth, societal and environmental well-being": 11.1,
                    "Unnamed: 1": "Traditional and Generative AI",
                    "Unnamed: 2": "Ensure that the development of AI system is for the beneficial",
                    "Unnamed: 3": "11.1.1",
                    "Unnamed: 4": "Put in place a process to determine that the development",
                    "Unnamed: 5": "Internal documentation (e.g., procedure manual) / External correspondence",
                    "Unnamed: 6": "Documentary evidence of consideration",
                    "Unnamed: 7": None,
                    "Unnamed: 8": None,
                },
                {
                    "outcome_id": 11.1,
                    "type_of_ai": "Traditional and Generative AI",
                    "outcomes": "Ensure that the development of AI system is for the beneficial",
                    "process_to_achieve_outcomes": "Put in place a process to determine that the development",
                    "evidence_type": "Internal documentation (e.g., procedure manual) / External correspondence",
                    "evidence": "Documentary evidence of consideration",
                },
                "Generative AI",
                True,
            ),
            (
                {
                    "Inclusive growth, societal and environmental well-being": 11.1,
                    "Unnamed: 1": "Traditional and Generative AI",
                    "Unnamed: 2": "Ensure that the development of AI system is for the beneficial",
                    "Unnamed: 3": "4.7.1",
                    "Unnamed: 4": "Put in place a process to determine that the development",
                    "Unnamed: 5": "Internal documentation (e.g., procedure manual) / External correspondence",
                    "Unnamed: 6": "Documentary evidence of consideration",
                    "Unnamed: 7": None,
                    "Unnamed: 8": None,
                },
                {
                    "outcome_id": 11.1,
                    "type_of_ai": "Traditional and Generative AI",
                    "outcomes": "Ensure that the development of AI system is for the beneficial",
                    "process_to_achieve_outcomes": "Put in place a process to determine that the development",
                    "evidence_type": "Internal documentation (e.g., procedure manual) / External correspondence",
                    "evidence": "Documentary evidence of consideration",
                },
                "Generative AI",
                True,
            ),
            (
                {
                    "Inclusive growth, societal and environmental well-being": 11.1,
                    "Unnamed: 1": "Generative AI",
                    "Unnamed: 2": "Ensure that the development of AI system is for the beneficial",
                    "Unnamed: 3": "123.456.789",
                    "Unnamed: 4": "Put in place a process to determine that the development",
                    "Unnamed: 5": "Internal documentation (e.g., procedure manual) / External correspondence",
                    "Unnamed: 6": "Documentary evidence of consideration",
                    "Unnamed: 7": None,
                    "Unnamed: 8": None,
                },
                {
                    "outcome_id": 11.1,
                    "type_of_ai": "Generative AI",
                    "outcomes": "Ensure that the development of AI system is for the beneficial",
                    "process_to_achieve_outcomes": "Put in place a process to determine that the development",
                    "evidence_type": "Internal documentation (e.g., procedure manual) / External correspondence",
                    "evidence": "Documentary evidence of consideration",
                },
                "Generative AI",
                True,
            ),
            (
                {
                    "Inclusive growth, societal and environmental well-being": 11.1,
                    "Unnamed: 1": "Machine Learning AI",
                    "Unnamed: 2": "Ensure that the development of AI system is for the beneficial",
                    "Unnamed: 3": "1.2.3",
                    "Unnamed: 4": "Put in place a process to determine that the development",
                    "Unnamed: 5": "Internal documentation (e.g., procedure manual) / External correspondence",
                    "Unnamed: 6": "Documentary evidence of consideration",
                    "Unnamed: 7": None,
                    "Unnamed: 8": None,
                },
                {
                    "outcome_id": 11.1,
                    "type_of_ai": "Machine Learning AI",
                    "outcomes": "Ensure that the development of AI system is for the beneficial",
                    "process_to_achieve_outcomes": "Put in place a process to determine that the development",
                    "evidence_type": "Internal documentation (e.g., procedure manual) / External correspondence",
                    "evidence": "Documentary evidence of consideration",
                },
                "Machine Learning",
                True,
            ),
            # Invalid process id
            (
                {
                    "Inclusive growth, societal and environmental well-being": 11.1,
                    "Unnamed: 1": "Traditional and Generative AI",
                    "Unnamed: 2": "Ensure that the development of AI system is for the beneficial",
                    "Unnamed: 3": "invalid process id",
                    "Unnamed: 4": "Put in place a process to determine that the development",
                    "Unnamed: 5": "Internal documentation (e.g., procedure manual) / External correspondence",
                    "Unnamed: 6": "Documentary evidence of consideration",
                    "Unnamed: 7": None,
                    "Unnamed: 8": None,
                },
                {
                    "outcome_id": 11.1,
                    "type_of_ai": "Traditional and Generative AI",
                    "outcomes": "Ensure that the development of AI system is for the beneficial",
                    "process_to_achieve_outcomes": "Put in place a process to determine that the development",
                    "evidence_type": "Internal documentation (e.g., procedure manual) / External correspondence",
                    "evidence": "Documentary evidence of consideration",
                },
                "Generative AI",
                False,
            ),
            # Invalid matches ai type filter
            (
                {
                    "Inclusive growth, societal and environmental well-being": 11.1,
                    "Unnamed: 1": "Traditional and Generative AI",
                    "Unnamed: 2": "Ensure that the development of AI system is for the beneficial",
                    "Unnamed: 3": "11.1.1",
                    "Unnamed: 4": "Put in place a process to determine that the development",
                    "Unnamed: 5": "Internal documentation (e.g., procedure manual) / External correspondence",
                    "Unnamed: 6": "Documentary evidence of consideration",
                    "Unnamed: 7": None,
                    "Unnamed: 8": None,
                },
                {
                    "outcome_id": 11.1,
                    "type_of_ai": "Traditional and Generative AI",
                    "outcomes": "Ensure that the development of AI system is for the beneficial",
                    "process_to_achieve_outcomes": "Put in place a process to determine that the development",
                    "evidence_type": "Internal documentation (e.g., procedure manual) / External correspondence",
                    "evidence": "Documentary evidence of consideration",
                },
                "Invalid Process ID",
                False,
            ),
        ],
    )
    def test_parse_process_check_row_validation(
        self, row_data, merged_cell_values, ai_type_filter, expected_result
    ):
        """Test parse_process_check_row validation logic"""
        row = pd.Series(row_data)
        result = parse_process_check_row(row, merged_cell_values, ai_type_filter)
        if expected_result:
            assert result is not None
            assert result["type_of_ai"] == merged_cell_values["type_of_ai"]
            assert result["outcome_id"] == 11.1
            assert (
                result["outcomes"]
                == "Ensure that the development of AI system is for the beneficial"
            )
        else:
            assert result is None

    @pytest.mark.parametrize(
        "row_data,merged_cell_values,ai_type_filter",
        [
            # Invalid row - None
            (
                None,
                {
                    "outcome_id": 11.1,
                    "type_of_ai": "Traditional and Generative AI",
                    "outcomes": "Ensure that the development of AI system is for the beneficial",
                    "process_to_achieve_outcomes": "Put in place a process to determine that the development",
                    "evidence_type": "Internal documentation (e.g., procedure manual) / External correspondence",
                    "evidence": "Documentary evidence of consideration",
                },
                "Generative AI",
            ),
            # Invalid merged_cell_values - None
            (
                pd.Series(
                    {
                        "Inclusive growth, societal and environmental well-being": 11.1,
                        "Unnamed: 1": "Traditional and Generative AI",
                        "Unnamed: 2": "Ensure that the development of AI system is for the beneficial",
                        "Unnamed: 3": "11.1.1",
                        "Unnamed: 4": "Put in place a process to determine that the development",
                        "Unnamed: 5": "Internal documentation (e.g., procedure manual) / External correspondence",
                        "Unnamed: 6": "Documentary evidence of consideration",
                        "Unnamed: 7": None,
                        "Unnamed: 8": None,
                    }
                ),
                None,
                "Generative AI",
            ),
            # Invalid ai_type_filter - None
            (
                pd.Series(
                    {
                        "Inclusive growth, societal and environmental well-being": 11.1,
                        "Unnamed: 1": "Traditional and Generative AI",
                        "Unnamed: 2": "Ensure that the development of AI system is for the beneficial",
                        "Unnamed: 3": "11.1.1",
                        "Unnamed: 4": "Put in place a process to determine that the development",
                        "Unnamed: 5": "Internal documentation (e.g., procedure manual) / External correspondence",
                        "Unnamed: 6": "Documentary evidence of consideration",
                        "Unnamed: 7": None,
                        "Unnamed: 8": None,
                    }
                ),
                {
                    "outcome_id": 11.1,
                    "type_of_ai": "Traditional and Generative AI",
                    "outcomes": "Ensure that the development of AI system is for the beneficial",
                    "process_to_achieve_outcomes": "Put in place a process to determine that the development",
                    "evidence_type": "Internal documentation (e.g., procedure manual) / External correspondence",
                    "evidence": "Documentary evidence of consideration",
                },
                None,
            ),
            # Invalid ai_type_filter - not a string
            (
                pd.Series(
                    {
                        "Inclusive growth, societal and environmental well-being": 11.1,
                        "Unnamed: 1": "Traditional and Generative AI",
                        "Unnamed: 2": "Ensure that the development of AI system is for the beneficial",
                        "Unnamed: 3": "11.1.1",
                        "Unnamed: 4": "Put in place a process to determine that the development",
                        "Unnamed: 5": "Internal documentation (e.g., procedure manual) / External correspondence",
                        "Unnamed: 6": "Documentary evidence of consideration",
                        "Unnamed: 7": None,
                        "Unnamed: 8": None,
                    }
                ),
                {
                    "outcome_id": 11.1,
                    "type_of_ai": "Traditional and Generative AI",
                    "outcomes": "Ensure that the development of AI system is for the beneficial",
                    "process_to_achieve_outcomes": "Put in place a process to determine that the development",
                    "evidence_type": "Internal documentation (e.g., procedure manual) / External correspondence",
                    "evidence": "Documentary evidence of consideration",
                },
                [],
            ),
        ],
    )
    def test_parse_process_check_row_error(
        self, row_data, merged_cell_values, ai_type_filter
    ):
        """Test parse_process_check_row raises TypeError for invalid input types"""
        with pytest.raises(TypeError):
            parse_process_check_row(row_data, merged_cell_values, ai_type_filter)

    # ===============================
    # update_merged_cell_values
    # ===============================
    def test_update_merged_cell_values_normal_case(self):
        """Test update_merged_cell_values with normal input"""
        row_data = {
            "col0": "outcome_1",
            "col1": "Generative AI",
            "col2": "New outcome",
            "col3": None,
            "col4": "Process description",
            "col5": "Evidence type",
            "col6": "Evidence",
        }
        row = pd.Series(row_data)

        merged_cell_values = {
            "outcome_id": "old_outcome",
            "type_of_ai": "old_ai",
            "outcomes": "old_outcomes",
            "process_to_achieve_outcomes": "old_process",
            "evidence_type": "old_evidence_type",
            "evidence": "old_evidence",
        }

        result = update_merged_cell_values(row, merged_cell_values)

        # Should update non-NA values
        assert result["outcome_id"] == "outcome_1"
        assert result["type_of_ai"] == "Generative AI"
        assert result["outcomes"] == "New outcome"
        assert result["process_to_achieve_outcomes"] == "Process description"
        assert result["evidence_type"] == "Evidence type"
        assert result["evidence"] == "Evidence"

    def test_update_merged_cell_values_with_na_values(self):
        """Test update_merged_cell_values with NA values that should not update"""
        # Create row data with enough columns to match MERGED_CELL_COLUMNS indices (0,1,2,4,5,6)
        row_data = [None, pd.NA, "New outcome", None, None, "Evidence type", None]
        row = pd.Series(row_data)

        merged_cell_values = {
            "outcome_id": "old_outcome",
            "type_of_ai": "old_ai",
            "outcomes": "old_outcomes",
            "process_to_achieve_outcomes": "old_process",
            "evidence_type": "old_evidence_type",
            "evidence": "old_evidence",
        }

        result = update_merged_cell_values(row, merged_cell_values)

        # Should keep old values for NA entries
        assert result["outcome_id"] == "old_outcome"
        assert result["type_of_ai"] == "old_ai"
        assert result["outcomes"] == "New outcome"  # This one updates
        assert result["process_to_achieve_outcomes"] == "old_process"
        assert result["evidence_type"] == "Evidence type"  # This one updates
        assert result["evidence"] == "old_evidence"

    def test_update_merged_cell_values_empty_input(self):
        """Test update_merged_cell_values with empty merged_cell_values"""
        # Create row data with enough columns to match MERGED_CELL_COLUMNS indices (0,1,2,4,5,6)
        row_data = [None, None, None, None, None, None, None]
        row = pd.Series(row_data)
        merged_cell_values = {}

        result = update_merged_cell_values(row, merged_cell_values)

        assert result == {}

    # ===============================
    # stringify_dict_keys
    # ===============================
    @pytest.mark.parametrize(
        "input_dict,expected",
        [
            (
                {1: {"a": "value1"}, 2: {"b": "value2"}},
                {"1": {"a": "value1"}, "2": {"b": "value2"}},
            ),
            ({}, {}),
            (None, {}),
            ({True: {"x": 1}, False: {"y": 2}}, {"True": {"x": 1}, "False": {"y": 2}}),
        ],
    )
    def test_stringify_dict_keys(self, input_dict, expected):
        """Test stringify_dict_keys with various input types"""
        result = stringify_dict_keys(input_dict)
        assert result == expected

    # ===============================
    # get_process_data
    # ===============================
    @pytest.mark.parametrize(
        "current_values,updates,expected",
        [
            # Valid case
            (
                {"outcome_id": "O1", "process_id": "P1"},
                {"O1": {"P1": {"field1": "value1"}}},
                {"field1": "value1"},
            ),
            # Missing outcome_id
            ({"process_id": "P1"}, {"O1": {"P1": {"field1": "value1"}}}, None),
            # Missing process_id
            ({"outcome_id": "O1"}, {"O1": {"P1": {"field1": "value1"}}}, None),
            # Nonexistent keys
            (
                {"outcome_id": "O2", "process_id": "P2"},
                {"O1": {"P1": {"field1": "value1"}}},
                None,
            ),
            # Empty updates
            ({"outcome_id": "O1", "process_id": "P1"}, {}, None),
        ],
    )
    def test_get_process_data(self, current_values, updates, expected):
        """Test get_process_data with various scenarios"""
        result = get_process_data(current_values, updates)
        assert result == expected

    # ===============================
    # is_matching_process
    # ===============================
    @pytest.mark.parametrize(
        "process,sheet_name,current_values,expected",
        [
            # All fields match
            (
                {
                    "principle_key": "P1",
                    "outcomes": "Test outcome",
                    "process_to_achieve_outcomes": "Test process",
                    "evidence_type": "Test evidence type",
                    "evidence": "Test evidence",
                },
                "P1",
                {
                    "outcomes": "Test outcome",
                    "process_to_achieve_outcomes": "Test process",
                    "evidence_type": "Test evidence type",
                    "evidence": "Test evidence",
                },
                True,
            ),
            # Principle key mismatch
            (
                {
                    "principle_key": "P2",
                    "outcomes": "Test outcome",
                    "process_to_achieve_outcomes": "Test process",
                    "evidence_type": "Test evidence type",
                    "evidence": "Test evidence",
                },
                "P1",
                {
                    "outcomes": "Test outcome",
                    "process_to_achieve_outcomes": "Test process",
                    "evidence_type": "Test evidence type",
                    "evidence": "Test evidence",
                },
                False,
            ),
            # Outcomes mismatch
            (
                {
                    "principle_key": "P1",
                    "outcomes": "Different outcome",
                    "process_to_achieve_outcomes": "Test process",
                    "evidence_type": "Test evidence type",
                    "evidence": "Test evidence",
                },
                "P1",
                {
                    "outcomes": "Test outcome",
                    "process_to_achieve_outcomes": "Test process",
                    "evidence_type": "Test evidence type",
                    "evidence": "Test evidence",
                },
                False,
            ),
        ],
    )
    def test_is_matching_process(self, process, sheet_name, current_values, expected):
        """Test is_matching_process with various matching scenarios"""
        result = is_matching_process(process, sheet_name, current_values)
        assert result is expected

    # ===============================
    # carry_forward_merged_values
    # ===============================
    def test_carry_forward_merged_values_normal_case(self, mocker):
        """Test carry_forward_merged_values with normal input"""
        # Mock row with cell values
        mock_cells = [
            mocker.Mock(value="new_outcome"),
            mocker.Mock(value="new_ai"),
            mocker.Mock(value=None),
        ]
        row = mock_cells

        last_values = {
            "outcome_id": "old_outcome",
            "type_of_ai": "old_ai",
            "outcomes": "old_outcomes",
        }

        column_indices = {"outcome_id": 0, "type_of_ai": 1, "outcomes": 2}

        result = carry_forward_merged_values(row, last_values, column_indices)

        assert result["outcome_id"] == "new_outcome"
        assert result["type_of_ai"] == "new_ai"
        assert result["outcomes"] == "old_outcomes"  # None value, so keep old

    # ===============================
    # update_row_values
    # ===============================
    @pytest.mark.parametrize(
        "process,expected_elaboration,expected_implementation",
        [
            # Both fields present
            (
                {
                    "elaboration": "New elaboration",
                    "implementation": "New implementation",
                },
                "New elaboration",
                "New implementation",
            ),
            # Only elaboration
            ({"elaboration": "New elaboration"}, "New elaboration", None),
            # Only implementation
            ({"implementation": "New implementation"}, None, "New implementation"),
            # Empty process
            ({}, None, None),
        ],
    )
    def test_update_row_values(
        self, mocker, process, expected_elaboration, expected_implementation
    ):
        """Test update_row_values with various process configurations"""
        # Mock row cells
        mock_cells = [mocker.Mock() for _ in range(10)]
        row = mock_cells

        # Store original values
        original_elab_value = row[8].value
        original_impl_value = row[7].value

        column_indices = {"elaboration": 8, "implementation": 7}

        update_row_values(row, process, column_indices)

        # Check elaboration
        if expected_elaboration is not None:
            assert row[8].value == expected_elaboration
        else:
            assert row[8].value == original_elab_value

        # Check implementation
        if expected_implementation is not None:
            assert row[7].value == expected_implementation
        else:
            assert row[7].value == original_impl_value

    # ===============================
    # process_single_principle_sheet
    # ===============================
    def test_process_single_principle_sheet_valid_data(self):
        """Test process_single_principle_sheet with valid data"""
        # Create test DataFrame
        data = [
            ["Header", "Col1", "Col2", "Col3", "Col4", "Col5", "Col6", "Col7", "Col8"],
            [
                "Test principle description",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            ],
            [
                "O1",
                "Generative AI",
                "Test outcome",
                "1.2.3",
                "Test process",
                "Evidence type",
                "Evidence",
                "Implementation",
                "Elaboration",
            ],
        ]
        df = pd.DataFrame(data)

        result = process_single_principle_sheet(df, "P1")

        assert result is not None
        assert result["principle_description"] == "Test principle description"
        assert "process_checks" in result
        assert "1.2.3" in result["process_checks"]

    def test_process_single_principle_sheet_exception_handling(self, mocker):
        """Test process_single_principle_sheet handles exceptions properly"""
        # Create invalid DataFrame that will cause an exception
        df = None
        mock_logger = mocker.patch("backend.spreadsheet.logger")

        result = process_single_principle_sheet(df, "P1")

        assert result is None
        mock_logger.error.assert_called_once()

    # ===============================
    # read_principles_from_excel
    # ===============================
    def test_read_principles_from_excel_success(self, mocker):
        """Test read_principles_from_excel with successful processing"""
        mock_excel_data = mocker.Mock()
        mock_excel_file = mocker.patch("pandas.ExcelFile")
        mock_process_data = mocker.patch(
            "backend.spreadsheet.process_excel_principles_data"
        )

        mock_excel_file.return_value = mock_excel_data
        mock_process_data.return_value = {"P1": {"principle_description": "Test"}}

        result = read_principles_from_excel("test.xlsx")

        mock_excel_file.assert_called_once_with("test.xlsx")
        mock_process_data.assert_called_once_with(mock_excel_data)
        assert result == {"P1": {"principle_description": "Test"}}

    def test_read_principles_from_excel_exception(self, mocker):
        """Test read_principles_from_excel handles exceptions"""
        mock_excel_file = mocker.patch("pandas.ExcelFile")
        mock_logger = mocker.patch("backend.spreadsheet.logger")

        mock_excel_file.side_effect = Exception("File not found")

        result = read_principles_from_excel("nonexistent.xlsx")

        assert result == {}
        mock_logger.error.assert_called_once()
