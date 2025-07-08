import pytest
from backend.principle_calculator import (
    accountability_principle,
    data_governance_principle,
    explainability_principle,
    fairness_principle,
    human_agency_principle,
    inc_growth_principle,
    process_principle,
    reproducibility_principle,
    robustness_principle,
    safety_principle,
    security_principle,
    transparency_principle,
)


class TestProcessPrinciple:
    """
    Test collection for process_principle function.
    """

    @pytest.mark.parametrize(
        "principle_name,principle_number,expected_key",
        [
            ("transparency", "1", "transparency"),
            ("safety", "4", "safety"),
            ("human agency", "10", "human agency"),
            ("inc growth", "11", "inc growth"),
        ],
    )
    def test_process_principle_basic(
        self, principle_name, principle_number, expected_key
    ):
        """
        Test basic process_principle functionality.
        """
        data = {
            "process_checks": {
                "outcome1": {
                    "process1": {
                        "principle_key": f"{principle_number}. {principle_name.title()}",
                        "implementation": "Yes",
                    }
                }
            }
        }

        result = process_principle(data, principle_name, principle_number)

        assert expected_key in result
        assert "yes" in result[expected_key]
        assert "no" in result[expected_key]
        assert "na" in result[expected_key]
        assert "all_yes" in result[expected_key]

    def test_process_principle_all_yes(self):
        """
        Test process_principle with all Yes implementations.
        """
        data = {
            "process_checks": {
                "outcome1": {
                    "process1": {
                        "principle_key": "1. Transparency",
                        "implementation": "Yes",
                    },
                    "process2": {
                        "principle_key": "1. Transparency",
                        "implementation": "Yes",
                    },
                }
            }
        }

        result = process_principle(data, "transparency", "1")

        assert result["transparency"]["yes"] == 2
        assert result["transparency"]["no"] == 0
        assert result["transparency"]["na"] == 0
        assert result["transparency"]["all_yes"] is True

    def test_process_principle_mixed_implementations(self):
        """
        Test process_principle with mixed implementations.
        """
        data = {
            "process_checks": {
                "outcome1": {
                    "process1": {
                        "principle_key": "4. Safety",
                        "implementation": "Yes",
                    },
                    "process2": {
                        "principle_key": "4. Safety",
                        "implementation": "No",
                        "process_to_achieve_outcomes": "Test process for No",
                        "elaboration": "Test justification for No",
                    },
                    "process3": {
                        "principle_key": "4. Safety",
                        "implementation": "N/A",
                        "process_to_achieve_outcomes": "Test process for N/A",
                        "elaboration": "Test justification for N/A",
                    },
                }
            }
        }

        result = process_principle(data, "safety", "4")

        assert result["safety"]["yes"] == 1
        assert result["safety"]["no"] == 1
        assert result["safety"]["na"] == 1
        assert result["safety"]["all_yes"] is False


class TestIndividualPrinciples:
    """
    Test collection for individual principle functions.
    """

    @pytest.mark.parametrize(
        "principle_func,principle_key,description_key,wim_key,recommendation_key",
        [
            (
                transparency_principle,
                "1. Transparency",
                "transparency_description",
                "transparency_wim",
                "transparency_recommendation",
            ),
            (
                explainability_principle,
                "2. Explainability",
                "explainability_description",
                "explainability_wim",
                "explainability_recommendation",
            ),
            (
                reproducibility_principle,
                "3. Reproducibility",
                "reproducibility_description",
                "reproducibility_wim",
                "reproducibility_recommendation",
            ),
            (
                safety_principle,
                "4. Safety",
                "safety_description",
                "safety_wim",
                "safety_recommendation",
            ),
            (
                security_principle,
                "5. Security",
                "security_description",
                "security_wim",
                "security_recommendation",
            ),
            (
                robustness_principle,
                "6. Robustness",
                "robustness_description",
                "robustness_wim",
                "robustness_recommendation",
            ),
            (
                fairness_principle,
                "7. Fairness",
                "fairness_description",
                "fairness_wim",
                "fairness_recommendation",
            ),
            (
                data_governance_principle,
                "8. Data Governance",
                "data_governance_description",
                "data_governance_wim",
                "data_governance_recommendation",
            ),
            (
                accountability_principle,
                "9. Accountability",
                "accountability_description",
                "accountability_wim",
                "accountability_recommendation",
            ),
            (
                human_agency_principle,
                "10. Human agency",
                "human_agency_description",
                "human_agency_wim",
                "human_agency_recommendation",
            ),
            (
                inc_growth_principle,
                "11. Inclusive growth",
                "inc_growth_description",
                "inc_growth_wim",
                "inc_growth_recommendation",
            ),
        ],
    )
    def test_principle_all_yes(
        self,
        principle_func,
        principle_key,
        description_key,
        wim_key,
        recommendation_key,
    ):
        """
        Test principle functions with all Yes implementations.
        """
        data = {
            "process_checks": {
                "outcome1": {
                    "process1": {
                        "principle_key": principle_key,
                        "implementation": "Yes",
                    }
                }
            }
        }

        result = principle_func(data)

        assert description_key in result
        assert wim_key in result
        assert result[recommendation_key] == ""
        assert result["justifications"] is None

    @pytest.mark.parametrize(
        "principle_func,principle_key,description_key,wim_key,recommendation_key",
        [
            (
                transparency_principle,
                "1. Transparency",
                "transparency_description",
                "transparency_wim",
                "transparency_recommendation",
            ),
            (
                explainability_principle,
                "2. Explainability",
                "explainability_description",
                "explainability_wim",
                "explainability_recommendation",
            ),
            (
                reproducibility_principle,
                "3. Reproducibility",
                "reproducibility_description",
                "reproducibility_wim",
                "reproducibility_recommendation",
            ),
            (
                safety_principle,
                "4. Safety",
                "safety_description",
                "safety_wim",
                "safety_recommendation",
            ),
            (
                security_principle,
                "5. Security",
                "security_description",
                "security_wim",
                "security_recommendation",
            ),
            (
                robustness_principle,
                "6. Robustness",
                "robustness_description",
                "robustness_wim",
                "robustness_recommendation",
            ),
            (
                fairness_principle,
                "7. Fairness",
                "fairness_description",
                "fairness_wim",
                "fairness_recommendation",
            ),
            (
                data_governance_principle,
                "8. Data Governance",
                "data_governance_description",
                "data_governance_wim",
                "data_governance_recommendation",
            ),
            (
                accountability_principle,
                "9. Accountability",
                "accountability_description",
                "accountability_wim",
                "accountability_recommendation",
            ),
            (
                human_agency_principle,
                "10. Human agency",
                "human_agency_description",
                "human_agency_wim",
                "human_agency_recommendation",
            ),
            (
                inc_growth_principle,
                "11. Inclusive growth",
                "inc_growth_description",
                "inc_growth_wim",
                "inc_growth_recommendation",
            ),
        ],
    )
    def test_principle_with_no(
        self,
        principle_func,
        principle_key,
        description_key,
        wim_key,
        recommendation_key,
    ):
        """
        Test principle functions with No implementations.
        """
        data = {
            "process_checks": {
                "outcome1": {
                    "process1": {
                        "principle_key": principle_key,
                        "implementation": "No",
                        "process_to_achieve_outcomes": "Test process",
                        "elaboration": "Test justification",
                    }
                }
            }
        }

        result = principle_func(data)

        assert description_key in result
        assert wim_key in result
        assert result[recommendation_key] != ""
        assert len(result["process_to_achieve_outcomes"]) > 0
        assert len(result["justifications"]) > 0

    def test_safety_principle_special_questions(self):
        """
        Test safety principle with special question groups.
        """
        # Test safety question 1 group
        data = {
            "process_checks": {
                "outcome1": {
                    "4.8.1": {
                        "principle_key": "4. Safety",
                        "implementation": "No",
                        "process_to_achieve_outcomes": "Test process",
                        "elaboration": "Test justification",
                    }
                }
            }
        }

        result = safety_principle(data)

        # Should contain additional WIM text for content safety
        wim_text = " ".join(result["safety_wim"])
        assert "content safety" in wim_text or "misleading" in wim_text

    def test_reproducibility_principle_traceability(self):
        """
        Test reproducibility principle with traceability questions.
        """
        data = {
            "process_checks": {
                "outcome1": {
                    "3.1.1": {  # Traceability question
                        "principle_key": "3. Reproducibility",
                        "implementation": "No",
                        "process_to_achieve_outcomes": "Test process",
                        "elaboration": "Test justification",
                    }
                }
            }
        }

        result = reproducibility_principle(data)

        # Should contain traceability-specific WIM text
        wim_text = " ".join(result["reproducibility_wim"])
        assert "traceability" in wim_text or "audits" in wim_text

    def test_reproducibility_principle_reproducibility_questions(self):
        """
        Test reproducibility principle with reproducibility questions.
        """
        data = {
            "process_checks": {
                "outcome1": {
                    "3.5.1": {  # Reproducibility question
                        "principle_key": "3. Reproducibility",
                        "implementation": "No",
                        "process_to_achieve_outcomes": "Test process",
                        "elaboration": "Test justification",
                    }
                }
            }
        }

        result = reproducibility_principle(data)

        # Should contain reproducibility-specific WIM text
        wim_text = " ".join(result["reproducibility_wim"])
        assert "reproducibility" in wim_text or "debug" in wim_text


class TestEdgeCases:
    """
    Test collection for edge cases and error handling.
    """

    def test_process_principle_empty_data(self):
        """
        Test process_principle with empty data.
        """
        data = {"process_checks": {}}

        result = process_principle(data, "transparency", "1")

        assert "transparency" in result
        assert result["transparency"]["yes"] == 0
        assert result["transparency"]["no"] == 0
        assert result["transparency"]["na"] == 0

    def test_process_principle_missing_elaboration(self):
        """
        Test principle function with missing elaboration.
        """
        data = {
            "process_checks": {
                "outcome1": {
                    "process1": {
                        "principle_key": "1. Transparency",
                        "implementation": "No",
                        "process_to_achieve_outcomes": "Test process",
                        # Missing elaboration field
                    }
                }
            }
        }

        result = transparency_principle(data)

        # Should handle missing elaboration gracefully
        assert "transparency_description" in result
        assert result["justifications"] is None

    def test_explainability_principle_empty_elaboration(self):
        """
        Test explainability principle with empty elaboration.
        """
        data = {
            "process_checks": {
                "outcome1": {
                    "process1": {
                        "principle_key": "2. Explainability",
                        "implementation": "No",
                        "process_to_achieve_outcomes": "Test process",
                        "elaboration": "   ",  # Empty/whitespace elaboration
                    }
                }
            }
        }

        result = explainability_principle(data)

        assert "explainability_description" in result
        assert result["justifications"] is None

    def test_unknown_principle_function(self):
        """
        Test process_principle with unknown principle.
        """
        data = {
            "process_checks": {
                "outcome1": {
                    "process1": {
                        "principle_key": "99. Unknown",
                        "implementation": "Yes",
                    }
                }
            }
        }

        # Should not crash even if principle function doesn't exist
        result = process_principle(data, "unknown", "99")

        assert "unknown" in result
        assert result["unknown"]["yes"] == 1
