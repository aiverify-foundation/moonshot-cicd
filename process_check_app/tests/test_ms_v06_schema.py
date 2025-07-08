import pytest
from backend.schema.ms_v06_schema import extract_06_report_info


class TestExtract06ReportInfo:
    """
    Test suite for extract_06_report_info function that validates the extraction and processing of test results from
    Moonshot v0.6 structure with valid input data.
    """

    @pytest.mark.parametrize(
        "input_data,expected_output",
        [
            # Test case 1: Validates processing of successful cookbooks with complete evaluation summaries
            # Verifies handling of multiple recipes with different evaluation metrics
            (
                {
                    "metadata": {
                        "id": "run_123",
                        "status": "completed",
                        "cookbooks": ["cookbook_1", "cookbook_2"],
                        "endpoints": ["gpt-4", "claude-3"],
                    },
                    "results": {
                        "cookbooks": [
                            {
                                "id": "cookbook_1",
                                "recipes": [
                                    {
                                        "id": "recipe_1",
                                        "evaluation_summary": [
                                            {
                                                "model_id": "gpt-4",
                                                "num_of_prompts": 100,
                                                "avg_grade_value": 0.95,
                                                "grade": "A",
                                            }
                                        ],
                                    },
                                    {
                                        "id": "recipe_2",
                                        "evaluation_summary": [
                                            {
                                                "model_id": "claude-3",
                                                "num_of_prompts": 50,
                                                "avg_grade_value": 0.88,
                                                "grade": "B",
                                            }
                                        ],
                                    },
                                ],
                                "overall_evaluation_summary": [],
                            }
                        ]
                    },
                },
                {
                    "status": "completed",
                    "total_tests": {"test_success": 2, "test_fail": 0, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [
                        {
                            "test_name": "recipe_1",
                            "id": "recipe_1",
                            "summary": {"avg_grade_value": 0.95, "grade": "A"},
                        },
                        {
                            "test_name": "recipe_2",
                            "id": "recipe_2",
                            "summary": {"avg_grade_value": 0.88, "grade": "B"},
                        },
                    ],
                },
            ),
            # Test case 2: Validates processing of cookbooks without evaluation summaries
            # Verifies that recipes without summaries are counted as failures
            (
                {
                    "metadata": {
                        "id": "run_124",
                        "status": "completed",
                        "cookbooks": ["cookbook_3"],
                        "endpoints": ["gpt-4"],
                    },
                    "results": {
                        "cookbooks": [
                            {
                                "id": "cookbook_3",
                                "recipes": [
                                    {
                                        "id": "recipe_3",
                                        # No evaluation_summary
                                    },
                                    {
                                        "id": "recipe_4",
                                        "evaluation_summary": [],  # Empty evaluation_summary
                                    },
                                ],
                                "overall_evaluation_summary": [],
                            }
                        ]
                    },
                },
                {
                    "status": "completed",
                    "total_tests": {"test_success": 0, "test_fail": 2, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [],
                },
            ),
            # Test case 3: Validates handling of mixed cookbook results
            # Tests combination of successful and failed recipes
            (
                {
                    "metadata": {
                        "id": "run_789",
                        "status": "partial",
                        "cookbooks": ["mixed_cookbook"],
                        "endpoints": ["gpt-3.5", "llama-2"],
                    },
                    "results": {
                        "cookbooks": [
                            {
                                "id": "mixed_cookbook",
                                "recipes": [
                                    {
                                        "id": "successful_recipe",
                                        "evaluation_summary": [
                                            {
                                                "model_id": "gpt-3.5",
                                                "num_of_prompts": 75,
                                                "avg_grade_value": 0.82,
                                                "grade": "B",
                                            }
                                        ],
                                    },
                                    {
                                        "id": "failed_recipe",
                                        # No evaluation_summary
                                    },
                                    {
                                        "id": "incomplete_recipe",
                                        "evaluation_summary": [],
                                    },
                                ],
                                "overall_evaluation_summary": [],
                            }
                        ]
                    },
                },
                {
                    "status": "partial",
                    "total_tests": {"test_success": 1, "test_fail": 2, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [
                        {
                            "test_name": "successful_recipe",
                            "id": "successful_recipe",
                            "summary": {"avg_grade_value": 0.82, "grade": "B"},
                        },
                    ],
                },
            ),
            # Test case 4: Validates handling of empty cookbooks
            # Tests valid case with no recipes
            (
                {
                    "metadata": {
                        "id": "run_empty",
                        "status": "incomplete",
                        "cookbooks": [],
                        "endpoints": [],
                    },
                    "results": {"cookbooks": []},
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
                    "metadata": {
                        "status": "completed",
                    },
                    "results": {
                        "cookbooks": [
                            {
                                "id": "default_cookbook",
                                "recipes": [
                                    {
                                        "id": "default_recipe",
                                        "evaluation_summary": [
                                            {
                                                "model_id": "unknown",
                                                "num_of_prompts": 10,
                                                "avg_grade_value": 0.75,
                                                "grade": "C",
                                            }
                                        ],
                                    }
                                ],
                                "overall_evaluation_summary": [],
                            }
                        ]
                    },
                },
                {
                    "status": "completed",
                    "total_tests": {"test_success": 1, "test_fail": 0, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [
                        {
                            "test_name": "default_recipe",
                            "id": "default_recipe",
                            "summary": {"avg_grade_value": 0.75, "grade": "C"},
                        },
                    ],
                },
            ),
            # Test case 6: Validates handling of recipes without id field
            # Tests default recipe name assignment when id is missing
            (
                {
                    "metadata": {"status": "completed"},
                    "results": {
                        "cookbooks": [
                            {
                                "id": "unnamed_cookbook",
                                "recipes": [
                                    {
                                        # No id field
                                        "evaluation_summary": [
                                            {
                                                "model_id": "test-model",
                                                "num_of_prompts": 25,
                                                "avg_grade_value": 0.90,
                                                "grade": "A-",
                                            }
                                        ],
                                    }
                                ],
                                "overall_evaluation_summary": [],
                            }
                        ]
                    },
                },
                {
                    "status": "completed",
                    "total_tests": {"test_success": 1, "test_fail": 0, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [
                        {
                            "test_name": "Unnamed Recipe",
                            "id": None,
                            "summary": {"avg_grade_value": 0.9, "grade": "A-"},
                        },
                    ],
                },
            ),
            # Test case 7: Validates rounding of avg_grade_value
            # Tests that avg_grade_value is properly rounded to 2 decimal places
            (
                {
                    "metadata": {"status": "completed"},
                    "results": {
                        "cookbooks": [
                            {
                                "id": "rounding_cookbook",
                                "recipes": [
                                    {
                                        "id": "rounding_recipe",
                                        "evaluation_summary": [
                                            {
                                                "model_id": "test-model",
                                                "num_of_prompts": 33,
                                                "avg_grade_value": 0.876543,  # Should round to 0.88
                                                "grade": "B+",
                                            }
                                        ],
                                    }
                                ],
                                "overall_evaluation_summary": [],
                            }
                        ]
                    },
                },
                {
                    "status": "completed",
                    "total_tests": {"test_success": 1, "test_fail": 0, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [
                        {
                            "test_name": "rounding_recipe",
                            "id": "rounding_recipe",
                            "summary": {"avg_grade_value": 0.88, "grade": "B+"},
                        },
                    ],
                },
            ),
            # Test case 8: Validates handling of duplicate recipe names
            # Tests that duplicate recipe names are handled correctly (only first occurrence processed)
            (
                {
                    "metadata": {"status": "completed"},
                    "results": {
                        "cookbooks": [
                            {
                                "id": "duplicate_cookbook",
                                "recipes": [
                                    {
                                        "id": "duplicate_recipe",
                                        "evaluation_summary": [
                                            {
                                                "model_id": "first-model",
                                                "num_of_prompts": 20,
                                                "avg_grade_value": 0.85,
                                                "grade": "B",
                                            }
                                        ],
                                    },
                                    {
                                        "id": "duplicate_recipe",  # Same name as above
                                        "evaluation_summary": [
                                            {
                                                "model_id": "second-model",
                                                "num_of_prompts": 30,
                                                "avg_grade_value": 0.95,
                                                "grade": "A",
                                            }
                                        ],
                                    },
                                ],
                                "overall_evaluation_summary": [],
                            }
                        ]
                    },
                },
                {
                    "status": "completed",
                    "total_tests": {
                        "test_success": 1,
                        "test_fail": 0,
                        "test_skip": 0,
                    },  # Second one skipped due to duplicate
                    "evaluation_summaries_and_metadata": [
                        {
                            "test_name": "duplicate_recipe",
                            "id": "duplicate_recipe",
                            "summary": {
                                "avg_grade_value": 0.85,
                                "grade": "B",
                            },  # Only first occurrence
                        },
                    ],
                },
            ),
            # Test case 9: Validates handling of multiple cookbooks with mixed results
            # Tests processing multiple cookbooks with different recipe outcomes
            (
                {
                    "metadata": {
                        "id": "run_multi",
                        "status": "completed",
                        "cookbooks": ["cookbook_a", "cookbook_b"],
                        "endpoints": ["model-1", "model-2"],
                    },
                    "results": {
                        "cookbooks": [
                            {
                                "id": "cookbook_a",
                                "recipes": [
                                    {
                                        "id": "recipe_a1",
                                        "evaluation_summary": [
                                            {
                                                "model_id": "model-1",
                                                "num_of_prompts": 40,
                                                "avg_grade_value": 0.92,
                                                "grade": "A-",
                                            }
                                        ],
                                    }
                                ],
                                "overall_evaluation_summary": [],
                            },
                            {
                                "id": "cookbook_b",
                                "recipes": [
                                    {
                                        "id": "recipe_b1",
                                        "evaluation_summary": [
                                            {
                                                "model_id": "model-2",
                                                "num_of_prompts": 60,
                                                "avg_grade_value": 0.78,
                                                "grade": "C+",
                                            }
                                        ],
                                    },
                                    {
                                        "id": "recipe_b2",
                                        # No evaluation_summary
                                    },
                                ],
                                "overall_evaluation_summary": [],
                            },
                        ]
                    },
                },
                {
                    "status": "completed",
                    "total_tests": {"test_success": 2, "test_fail": 1, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [
                        {
                            "test_name": "recipe_a1",
                            "id": "recipe_a1",
                            "summary": {"avg_grade_value": 0.92, "grade": "A-"},
                        },
                        {
                            "test_name": "recipe_b1",
                            "id": "recipe_b1",
                            "summary": {"avg_grade_value": 0.78, "grade": "C+"},
                        },
                    ],
                },
            ),
            # Test case 10: Validates minimal valid structure
            # Tests minimal but valid report structure
            (
                {
                    "metadata": {"status": "completed"},
                    "results": {"cookbooks": []},
                },
                {
                    "status": "completed",
                    "total_tests": {"test_success": 0, "test_fail": 0, "test_skip": 0},
                    "evaluation_summaries_and_metadata": [],
                },
            ),
        ],
    )
    def test_extract_06_report_info_valid_cases(self, input_data, expected_output):
        """Test extract_06_report_info with various valid input scenarios.

        Tests the extract_06_report_info function's ability to correctly process and validate
        Moonshot v0.6 report structures across different scenarios. The test cases cover:

        1. Complete cookbook results with evaluation summaries
        2. Cookbooks without evaluation summaries (counted as failures)
        3. Mixed success/failure cases with partial completion
        4. Empty cookbooks and minimal data structures
        5. Default value handling for missing optional fields
        6. Recipes without ID fields (default naming)
        7. Proper rounding of grade values
        8. Duplicate recipe name handling (first occurrence only)
        9. Multiple cookbook processing with mixed results
        10. Minimal valid report structure

        Parameters:
            input_data (dict): Test input data simulating various Moonshot v0.6 report structures
            expected_output (dict): Expected processed output containing test results and summaries

        The function verifies that the extract_06_report_info function correctly:
        - Processes evaluation summaries
        - Counts test successes, failures, and skips
        - Handles missing or incomplete data
        - Maintains data integrity and expected output format
        """
        result = extract_06_report_info(input_data)
        assert result == expected_output

    @pytest.mark.parametrize(
        "input_data,expected_test_counts",
        [
            # Boundary case: Single recipe with evaluation summary
            # Tests handling of minimal successful recipe case with evaluation summary
            (
                {
                    "metadata": {"status": "completed"},
                    "results": {
                        "cookbooks": [
                            {
                                "id": "single_cookbook",
                                "recipes": [
                                    {
                                        "id": "single_recipe",
                                        "evaluation_summary": [
                                            {
                                                "model_id": "test-model",
                                                "num_of_prompts": 50,
                                                "avg_grade_value": 0.95,
                                                "grade": "A",
                                            }
                                        ],
                                    }
                                ],
                                "overall_evaluation_summary": [],
                            }
                        ]
                    },
                },
                {"test_success": 1, "test_fail": 0, "test_skip": 0},
            ),
            # Boundary case: Single recipe without evaluation summary
            # Tests handling of minimal failing recipe case with missing evaluation summary
            (
                {
                    "metadata": {"status": "completed"},
                    "results": {
                        "cookbooks": [
                            {
                                "id": "single_cookbook",
                                "recipes": [
                                    {
                                        "id": "single_recipe",
                                        # No evaluation_summary
                                    }
                                ],
                                "overall_evaluation_summary": [],
                            }
                        ]
                    },
                },
                {"test_success": 0, "test_fail": 1, "test_skip": 0},
            ),
            # Boundary case: Many recipes (stress test)
            # Tests processing of large number of mixed pass/fail results
            # Even numbered recipes have evaluation summaries (pass)
            # Odd numbered recipes have no summaries (fail)
            (
                {
                    "metadata": {"status": "completed"},
                    "results": {
                        "cookbooks": [
                            {
                                "id": "stress_cookbook",
                                "recipes": [
                                    {
                                        "id": f"recipe_{i}",
                                        "evaluation_summary": (
                                            [
                                                {
                                                    "model_id": "stress-model",
                                                    "num_of_prompts": 10,
                                                    "avg_grade_value": 0.8,
                                                    "grade": "B",
                                                }
                                            ]
                                            if i % 2 == 0
                                            else []
                                        ),
                                    }
                                    for i in range(100)
                                ],
                                "overall_evaluation_summary": [],
                            }
                        ]
                    },
                },
                {"test_success": 50, "test_fail": 50, "test_skip": 0},
            ),
        ],
    )
    def test_extract_06_report_info_boundary_cases(
        self, input_data, expected_test_counts
    ):
        """Test extract_06_report_info with boundary conditions.

        This test function validates the behavior of extract_06_report_info at boundary conditions:
        - Minimal case with single successful recipe
        - Minimal case with single failing recipe
        - Stress test with large number of mixed pass/fail results

        Args:
            input_data: Test input data representing boundary test cases
            expected_test_counts: Expected counts of test successes, failures and skips
        """
        # Process input data through function
        result = extract_06_report_info(input_data)
        print(result)

        # Verify test counts match expected
        print(result["total_tests"])
        assert result["total_tests"] == expected_test_counts

        # Verify status is completed since we have test results
        print(result["status"])
        assert result["status"] == "completed"

    def test_extract_06_report_info_return_type_structure(self):
        """Test that the function returns the correct data structure types.

        This test verifies that extract_06_report_info returns data with the expected
        type structure, including:
        - Top level dictionary with correct key types
        - Nested total_tests dictionary with integer counts
        - List of evaluation summaries with required fields

        The test uses a minimal valid input to check the structural integrity of the output,
        ensuring type safety throughout the returned data structure.
        """
        # Create minimal test data with required fields
        test_data = {
            "metadata": {"status": "completed"},
            "results": {
                "cookbooks": [
                    {
                        "id": "type_test_cookbook",
                        "recipes": [
                            {
                                "id": "type_test_recipe",
                                "evaluation_summary": [
                                    {
                                        "model_id": "test-model",
                                        "num_of_prompts": 25,
                                        "avg_grade_value": 0.9,
                                        "grade": "A-",
                                    }
                                ],
                            }
                        ],
                        "overall_evaluation_summary": [],
                    }
                ]
            },
        }

        # Process test data through the function
        result = extract_06_report_info(test_data)

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
            assert "summary" in summary, "Summary missing required summary field"
