import pytest
from backend.schema.ms_ga_schema import extract_ga_report_info


class TestExtractGaReportInfo:
    """
    Test suite for extract_ga_report_info function that validates the extraction and processing
    of test results from Moonshot GA structure with valid input data.
    """

    @pytest.mark.parametrize(
        "input_data,expected_output",
        [
            # Test case 1: Validates processing of successful tests with complete evaluation summaries
            # Verifies handling of multiple test cases with different models and evaluation metrics
            (
                {
                    "run_metadata": {
                        "run_id": "123",
                        "test_id": "456",
                        "start_time": "2021-01-01 12:00:00",
                        "end_time": "2021-01-01 12:00:00",
                        "duration": 100,
                    },
                    "run_results": [
                        {
                            "metadata": {
                                "test_name": "test_1",
                                "connector": {"model": "gpt-4"},
                            },
                            "results": {
                                "evaluation_summary": {"accuracy": 0.95, "total": 100}
                            },
                        },
                        {
                            "metadata": {
                                "test_name": "test_2",
                                "connector": {"model": "claude-3"},
                            },
                            "results": {
                                "evaluation_summary": {"accuracy": 0.88, "total": 50}
                            },
                        },
                    ],
                },
                {
                    "status": "completed",
                    "total_tests": {"test_success": 2, "test_fail": 0, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [
                        {
                            "test_name": "test_1",
                            "id": "test_1",
                            "model_id": "gpt-4",
                            "summary": {"accuracy": 0.95, "total": 100},
                        },
                        {
                            "test_name": "test_2",
                            "id": "test_2",
                            "model_id": "claude-3",
                            "summary": {"accuracy": 0.88, "total": 50},
                        },
                    ],
                },
            ),
            # Test case 2: Validates processing of tests without evaluation summaries
            # Verifies that tests without summaries are counted as failures
            (
                {
                    "run_metadata": {
                        "run_id": "124",
                        "test_id": "457",
                        "start_time": "2021-01-01 13:00:00",
                        "end_time": "2021-01-01 13:00:00",
                        "duration": 100,
                    },
                    "run_results": [
                        {
                            "metadata": {
                                "test_name": "test_3",
                                "connector": {"model": "gpt-4"},
                            },
                            "results": {
                                # No evaluation_summary
                            },
                        },
                        {
                            "metadata": {
                                "test_name": "test_4",
                                "connector": {"model": "claude-3"},
                            },
                            "results": {
                                "evaluation_summary": {}  # Empty evaluation_summary
                            },
                        },
                    ],
                },
                {
                    "status": "completed",
                    "total_tests": {"test_success": 0, "test_fail": 2, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [
                        {
                            "test_name": "test_3",
                            "id": "test_3",
                            "model_id": "gpt-4",
                            "summary": {},
                        },
                        {
                            "test_name": "test_4",
                            "id": "test_4",
                            "model_id": "claude-3",
                            "summary": {},
                        },
                    ],
                },
            ),
            # Test case 3: Validates handling of mixed test results
            # Tests combination of successful and failed tests
            (
                {
                    "run_metadata": {
                        "run_id": "789",
                        "test_id": "101",
                        "start_time": "2021-02-01 10:00:00",
                        "end_time": "2021-02-01 11:00:00",
                        "duration": 3600,
                    },
                    "run_results": [
                        {
                            "metadata": {
                                "test_name": "successful_test",
                                "connector": {"model": "gpt-3.5"},
                            },
                            "results": {"evaluation_summary": {"score": 85}},
                        },
                        {
                            "metadata": {
                                "test_name": "failed_test",
                                "connector": {"model": "llama-2"},
                            },
                            "results": {"evaluation_summary": {}},
                        },
                        {
                            "metadata": {
                                "test_name": "incomplete_test",
                                "connector": {"model": "mistral"},
                            },
                            "results": {},
                        },
                    ],
                },
                {
                    "status": "completed",
                    "total_tests": {"test_success": 1, "test_fail": 2, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [
                        {
                            "test_name": "successful_test",
                            "id": "successful_test",
                            "model_id": "gpt-3.5",
                            "summary": {"score": 85},
                        },
                        {
                            "test_name": "failed_test",
                            "id": "failed_test",
                            "model_id": "llama-2",
                            "summary": {},
                        },
                        {
                            "test_name": "incomplete_test",
                            "id": "incomplete_test",
                            "model_id": "mistral",
                            "summary": {},
                        },
                    ],
                },
            ),
            # Test case 4: Validates handling of empty run results
            # Tests valid case with no test results
            (
                {
                    "run_metadata": {
                        "run_id": "empty",
                        "test_id": "empty",
                        "start_time": "2021-03-01 09:00:00",
                        "end_time": "2021-03-01 09:00:00",
                        "duration": 0,
                    },
                    "run_results": [],
                },
                {
                    "status": "incomplete",
                    "total_tests": {"test_success": 0, "test_fail": 0, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [],
                },
            ),
            # Test case 5: Validates default value handling for missing optional metadata fields
            # Tests that default values are correctly applied when optional fields are missing
            (
                {
                    "run_results": [
                        {
                            "metadata": {},
                            "results": {"evaluation_summary": {"pass": True}},
                        },
                        {
                            "results": {"evaluation_summary": {"pass": False}},
                        },
                    ]
                },
                {
                    "status": "completed",
                    "total_tests": {"test_success": 2, "test_fail": 0, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [
                        {
                            "test_name": "Unnamed Test",
                            "id": "Unnamed Test",
                            "model_id": "Unknown Model",
                            "summary": {"pass": True},
                        },
                        {
                            "test_name": "Unnamed Test",
                            "id": "Unnamed Test",
                            "model_id": "Unknown Model",
                            "summary": {"pass": False},
                        },
                    ],
                },
            ),
            # Test case 6: Validates handling of tests without test_name field
            # Tests default test name assignment when test_name is missing
            (
                {
                    "run_results": [
                        {
                            "metadata": {"connector": {"model": "test-model"}},
                            "results": {"evaluation_summary": {"metric": 0.9}},
                        }
                    ]
                },
                {
                    "status": "completed",
                    "total_tests": {"test_success": 1, "test_fail": 0, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [
                        {
                            "test_name": "Unnamed Test",
                            "id": "Unnamed Test",
                            "model_id": "test-model",
                            "summary": {"metric": 0.9},
                        },
                    ],
                },
            ),
            # Test case 7: Validates handling of missing connector field
            # Tests default model ID assignment when connector info is missing
            (
                {
                    "run_results": [
                        {
                            "metadata": {"test_name": "test_without_connector"},
                            "results": {"evaluation_summary": {"result": "success"}},
                        }
                    ]
                },
                {
                    "status": "completed",
                    "total_tests": {"test_success": 1, "test_fail": 0, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [
                        {
                            "test_name": "test_without_connector",
                            "id": "test_without_connector",
                            "model_id": "Unknown Model",
                            "summary": {"result": "success"},
                        }
                    ],
                },
            ),
            # Test case 8: Validates handling of complex evaluation summaries
            # Tests processing of evaluation summaries with nested data structures
            (
                {
                    "run_results": [
                        {
                            "metadata": {
                                "test_name": "complex_test",
                                "connector": {"model": "advanced-model"},
                            },
                            "results": {
                                "evaluation_summary": {
                                    "accuracy": 0.92,
                                    "metrics": {"precision": 0.89, "recall": 0.94},
                                    "total_prompts": 150,
                                }
                            },
                        }
                    ]
                },
                {
                    "status": "completed",
                    "total_tests": {"test_success": 1, "test_fail": 0, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [
                        {
                            "test_name": "complex_test",
                            "id": "complex_test",
                            "model_id": "advanced-model",
                            "summary": {
                                "accuracy": 0.92,
                                "metrics": {"precision": 0.89, "recall": 0.94},
                                "total_prompts": 150,
                            },
                        },
                    ],
                },
            ),
            # Test case 9: Validates handling of multiple tests with mixed results
            # Tests processing multiple tests with different evaluation outcomes
            (
                {
                    "run_metadata": {
                        "run_id": "run_multi",
                        "test_id": "test_multi",
                        "start_time": "2021-05-01 10:00:00",
                        "end_time": "2021-05-01 12:00:00",
                        "duration": 7200,
                    },
                    "run_results": [
                        {
                            "metadata": {
                                "test_name": "test_a",
                                "connector": {"model": "model-1"},
                            },
                            "results": {"evaluation_summary": {"score": 88.5}},
                        },
                        {
                            "metadata": {
                                "test_name": "test_b",
                                "connector": {"model": "model-2"},
                            },
                            "results": {"evaluation_summary": {"score": 75.2}},
                        },
                        {
                            "metadata": {
                                "test_name": "test_c",
                                "connector": {"model": "model-3"},
                            },
                            "results": {},  # No evaluation_summary
                        },
                    ],
                },
                {
                    "status": "completed",
                    "total_tests": {"test_success": 2, "test_fail": 1, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [
                        {
                            "test_name": "test_a",
                            "id": "test_a",
                            "model_id": "model-1",
                            "summary": {"score": 88.5},
                        },
                        {
                            "test_name": "test_b",
                            "id": "test_b",
                            "model_id": "model-2",
                            "summary": {"score": 75.2},
                        },
                        {
                            "test_name": "test_c",
                            "id": "test_c",
                            "model_id": "model-3",
                            "summary": {},
                        },
                    ],
                },
            ),
            # Test case 10: Validates minimal valid structure
            # Tests minimal but valid report structure
            (
                {"run_results": []},
                {
                    "status": "incomplete",
                    "total_tests": {"test_success": 0, "test_fail": 0, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [],
                },
            ),
        ],
    )
    def test_extract_ga_report_info_valid_cases(self, input_data, expected_output):
        """Test extract_ga_report_info with various valid input scenarios.

        Tests the extract_ga_report_info function's ability to correctly process and validate
        Moonshot GA report structures across different scenarios. The test cases cover:

        1. Complete test results with evaluation summaries
        2. Tests without evaluation summaries (counted as failures)
        3. Mixed success/failure cases
        4. Empty run results and minimal data structures
        5. Default value handling for missing optional fields
        6. Tests without test_name fields (default naming)
        7. Missing connector field handling
        8. Complex evaluation summaries with nested data
        9. Multiple tests processing with mixed results
        10. Minimal valid report structure

        Parameters:
            input_data (dict): Test input data simulating various Moonshot GA report structures
            expected_output (dict): Expected processed output containing test results and summaries

        The function verifies that the extract_ga_report_info function correctly:
        - Processes evaluation summaries
        - Counts test successes, failures, and skips
        - Handles missing or incomplete data
        - Maintains data integrity and expected output format
        """
        result = extract_ga_report_info(input_data)
        assert result == expected_output

    @pytest.mark.parametrize(
        "input_data,expected_test_counts",
        [
            # Boundary case: Single test with summary
            # Tests handling of minimal successful test case with evaluation summary
            (
                {
                    "run_results": [
                        {
                            "metadata": {
                                "test_name": "single_test",
                                "connector": {"model": "test-model"},
                            },
                            "results": {"evaluation_summary": {"score": 100}},
                        }
                    ]
                },
                {"test_success": 1, "test_fail": 0, "test_skip": 0},
            ),
            # Boundary case: Single test without summary
            # Tests handling of minimal failing test case with missing evaluation summary
            (
                {
                    "run_results": [
                        {
                            "metadata": {
                                "test_name": "single_test",
                                "connector": {"model": "test-model"},
                            },
                            "results": {},
                        }
                    ]
                },
                {"test_success": 0, "test_fail": 1, "test_skip": 0},
            ),
            # Boundary case: Many tests (stress test)
            # Tests processing of large number of mixed pass/fail results
            # Even numbered tests have evaluation summaries (pass)
            # Odd numbered tests have no summaries (fail)
            (
                {
                    "run_results": [
                        {
                            "metadata": {
                                "test_name": f"test_{i}",
                                "connector": {"model": "model"},
                            },
                            "results": {
                                "evaluation_summary": {"id": i} if i % 2 == 0 else {}
                            },
                        }
                        for i in range(100)
                    ]
                },
                {"test_success": 50, "test_fail": 50, "test_skip": 0},
            ),
        ],
    )
    def test_extract_ga_report_info_boundary_cases(
        self, input_data, expected_test_counts
    ):
        """Test extract_ga_report_info with boundary conditions.

        This test function validates the behavior of extract_ga_report_info at boundary conditions:
        - Minimal case with single successful test
        - Minimal case with single failing test
        - Stress test with large number of mixed pass/fail results

        Args:
            input_data: Test input data representing boundary test cases
            expected_test_counts: Expected counts of test successes, failures and skips
        """
        # Process input data through function
        result = extract_ga_report_info(input_data)

        # Verify test counts match expected
        assert result["total_tests"] == expected_test_counts

        # Verify status is completed since we have test results
        assert result["status"] == "completed"

        # Verify number of summary entries matches total test count
        assert len(result["evaluation_summaries_and_metadata"]) == sum(
            expected_test_counts.values()
        )

    def test_extract_ga_report_info_return_type_structure(self):
        """Test that the function returns the correct data structure types.

        This test verifies that extract_ga_report_info returns data with the expected
        type structure, including:
        - Top level dictionary with correct key types
        - Nested total_tests dictionary with integer counts
        - List of evaluation summaries with required fields

        The test uses a minimal valid input to check the structural integrity of the output,
        ensuring type safety throughout the returned data structure.
        """
        # Create minimal test data with required fields
        test_data = {
            "run_results": [
                {
                    "metadata": {
                        "test_name": "type_test",
                        "connector": {"model": "test-model"},
                    },
                    "results": {"evaluation_summary": {"metric": 0.9}},
                }
            ]
        }

        # Process test data through the function
        result = extract_ga_report_info(test_data)

        # Verify top-level return structure has correct types
        assert isinstance(result, dict), "Return value must be a dictionary"
        assert isinstance(result["status"], str), "Status must be a string"
        assert isinstance(
            result["total_tests"], dict
        ), "Total tests must be a dictionary"
        assert isinstance(
            result["evaluation_summaries_and_metadata"], list
        ), "Summaries must be a list"

        # Verify total_tests contains integer counters
        total_tests = result["total_tests"]
        assert isinstance(
            total_tests["test_success"], int
        ), "Success count must be an integer"
        assert isinstance(
            total_tests["test_fail"], int
        ), "Fail count must be an integer"
        assert isinstance(
            total_tests["test_skip"], int
        ), "Skip count must be an integer"

        # Verify evaluation summary dictionary structure and required fields
        if result["evaluation_summaries_and_metadata"]:
            summary = result["evaluation_summaries_and_metadata"][0]
            assert isinstance(summary, dict), "Each summary must be a dictionary"
            assert "test_name" in summary, "Summary missing required test_name field"
            assert "id" in summary, "Summary missing required id field"
            assert "model_id" in summary, "Summary missing required model_id field"
            assert "summary" in summary, "Summary missing required summary field"
