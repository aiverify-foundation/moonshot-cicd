import os
from unittest.mock import MagicMock, patch

import pytest
from backend.pdf_generator import (
    compile_results,
    create_donut_chart,
    generate_pdf_cover_page,
    generate_pdf_introduction_page,
    generate_pdf_overview_page,
    generate_pdf_process_checks,
    generate_pdf_report,
    generate_pdf_technical_test_page,
    get_display_principle_name,
    get_pdf_cover_template,
    get_pdf_introduction_template,
    get_pdf_principle_template,
)


class TestGetDisplayPrincipleName:
    """
    Test collection for get_display_principle_name function.
    """

    @pytest.mark.parametrize(
        "input_name,multiline,expected",
        [
            # Core functionality tests
            (
                "inc growth",
                False,
                "Inclusive growth, societal and environmental well-being",
            ),
            ("human agency", False, "Human agency & oversight"),
            (
                "inc growth",
                True,
                "Inclusive Growth, \nSocietal and \nEnvironmental \nWell-being",
            ),
            ("human agency", True, "Human Agency &\n Oversight"),
            # Case insensitive
            (
                "INC GROWTH",
                False,
                "Inclusive growth, societal and environmental well-being",
            ),
            ("HUMAN AGENCY", False, "Human agency & oversight"),
            # Unknown principles
            ("unknown principle", False, "unknown principle"),
            ("Test Principle", False, "test principle"),
            # Edge cases
            ("", False, ""),
            (None, False, ""),
            ("   ", False, ""),
            # With spaces
            ("  human agency  ", False, "Human agency & oversight"),
        ],
    )
    def test_get_display_principle_name(self, input_name, multiline, expected):
        """
        Test get_display_principle_name with various inputs.
        """
        assert get_display_principle_name(input_name, multiline=multiline) == expected

    def test_get_display_principle_name_invalid_types(self):
        """
        Test get_display_principle_name with invalid input types.
        """
        # Should raise AttributeError for non-string types
        with pytest.raises(AttributeError):
            get_display_principle_name(123)


class TestCompileResults:
    """
    Test collection for compile_results function.
    """

    def test_compile_results_empty(self):
        """
        Test compile_results with empty process checks.
        """
        overall_stats, principle_stats = compile_results({})
        assert overall_stats == {"Total Yes": 0, "Total No": 0, "Total N/A": 0}
        assert principle_stats == {}

    def test_compile_results_mixed_responses(self):
        """
        Test compile_results with mixed responses.
        """
        process_checks = {
            "outcome1": {
                "process1": {"principle_key": "transparency", "implementation": "Yes"},
                "process2": {"principle_key": "transparency", "implementation": "No"},
                "process3": {"principle_key": "safety", "implementation": "N/A"},
            }
        }

        overall_stats, principle_stats = compile_results(process_checks)

        assert overall_stats == {"Total Yes": 1, "Total No": 1, "Total N/A": 1}
        assert principle_stats == {
            "transparency": {"yes": 1, "no": 1, "na": 0},
            "safety": {"yes": 0, "no": 0, "na": 1},
        }

    def test_compile_results_different_na_formats(self):
        """
        Test compile_results with different N/A formats.
        """
        process_checks = {
            "outcome1": {
                "process1": {"principle_key": "fairness", "implementation": "na"},
                "process2": {
                    "principle_key": "fairness",
                    "implementation": "not applicable",
                },
            }
        }

        overall_stats, principle_stats = compile_results(process_checks)

        assert overall_stats == {"Total Yes": 0, "Total No": 0, "Total N/A": 2}
        assert principle_stats == {"fairness": {"yes": 0, "no": 0, "na": 2}}


class TestCreateDonutChart:
    """
    Test collection for create_donut_chart function.
    """

    def test_create_donut_chart_basic(self, tmp_path, mocker):
        """
        Test creating a basic donut chart.
        """
        # Mock matplotlib functions
        mock_plt = mocker.patch("backend.pdf_generator.plt")
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        mock_plt.Circle.return_value = MagicMock()

        with patch("backend.pdf_generator.OUTPUTS_DIRECTORY", str(tmp_path)):
            data = {"transparency": {"yes": 5, "no": 3, "na": 2}}
            result_path = create_donut_chart(data, "transparency")

            mock_plt.subplots.assert_called_once_with(figsize=(8, 8))
            mock_ax.pie.assert_called_once()
            mock_plt.savefig.assert_called_once()
            mock_plt.close.assert_called_once()

            expected_path = os.path.join(str(tmp_path), "transparency_donut_chart.png")
            assert result_path == expected_path

    def test_create_donut_chart_zero_values(self, tmp_path, mocker):
        """
        Test creating donut chart with all zero values.
        """
        mock_plt = mocker.patch("backend.pdf_generator.plt")
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        with patch("backend.pdf_generator.OUTPUTS_DIRECTORY", str(tmp_path)):
            data = {"empty_principle": {"yes": 0, "no": 0, "na": 0}}
            result_path = create_donut_chart(data, "empty_principle")

            mock_plt.subplots.assert_called_once()
            assert result_path.endswith("empty_principle_donut_chart.png")


class TestPDFContentGeneration:
    """
    Test collection for PDF content generation functions.
    """

    def test_generate_pdf_cover_page(self):
        """
        Test generating PDF cover page content.
        """
        workspace_data = {
            "company_name": "Test Company",
            "app_name": "Test Application",
        }

        with patch("backend.pdf_generator.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "01 January 2024"
            content = generate_pdf_cover_page(workspace_data)

        assert isinstance(content, list)
        assert len(content) > 0

    def test_generate_pdf_cover_page_missing_data(self):
        """
        Test generating PDF cover page with missing data.
        """
        workspace_data = {}

        with patch("backend.pdf_generator.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "01 January 2024"
            content = generate_pdf_cover_page(workspace_data)

        assert isinstance(content, list)
        assert len(content) > 0

    def test_generate_pdf_introduction_page(self):
        """
        Test generating PDF introduction page content.
        """
        workspace_data = {
            "app_name": "Test Application",
            "app_description": "This is a test application description.",
        }
        mock_doc = MagicMock()

        content = generate_pdf_introduction_page(workspace_data, mock_doc)

        assert isinstance(content, list)
        assert len(content) > 0

    def test_generate_pdf_overview_page_no_tests(self, mocker):
        """
        Test generating overview page without technical tests.
        """
        process_checks = {
            "outcome1": {
                "process1": {
                    "principle_key": "transparency",
                    "implementation": "Yes",
                }
            }
        }
        test_result_info = None

        # Mock matplotlib properly
        mock_plt = mocker.patch("backend.pdf_generator.plt")
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        mock_plt.Circle.return_value = MagicMock()

        content = generate_pdf_overview_page(process_checks, test_result_info)

        assert isinstance(content, list)
        assert len(content) > 0

    def test_generate_pdf_overview_page_with_tests(self, mocker):
        """
        Test generating overview page with technical tests.
        """
        process_checks = {
            "outcome1": {
                "process1": {
                    "principle_key": "transparency",
                    "implementation": "Yes",
                }
            }
        }
        test_result_info = {
            "total_tests": {"test_success": 5, "test_fail": 2, "test_skip": 1},
            "evaluation_summaries_and_metadata": [
                {"test_name": "Test 1"},
                {"test_name": "Test 2"},
            ],
        }

        # Mock matplotlib properly
        mock_plt = mocker.patch("backend.pdf_generator.plt")
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        mock_plt.Circle.return_value = MagicMock()

        content = generate_pdf_overview_page(process_checks, test_result_info)

        assert isinstance(content, list)
        assert len(content) > 0

    def test_generate_pdf_technical_test_page(self):
        """
        Test generating technical test page.
        """
        test_result_info = {
            "evaluation_summaries_and_metadata": [
                {
                    "test_name": "Test 1",
                    "summary": {"avg_grade_value": 0.85},
                },
                {
                    "test_name": "Test 2",
                    "summary": {"metric": {"score": 90, "accuracy": 0.95}},
                },
            ]
        }

        content = generate_pdf_technical_test_page(test_result_info)

        assert isinstance(content, list)
        assert len(content) > 0

    def test_generate_pdf_process_checks(self):
        """
        Test generating process checks section.
        """
        workspace_data = {
            "process_checks": {
                "outcome1": {
                    "process1": {
                        "principle_key": "Transparency",
                        "outcomes": "Test outcome",
                        "process_to_achieve_outcomes": "Test process",
                        "evidence": "Test evidence",
                        "implementation": "Yes",
                        "evidence_type": "Document",
                        "elaboration": "Test elaboration",
                    }
                }
            }
        }

        content = generate_pdf_process_checks(workspace_data)

        assert isinstance(content, list)
        assert len(content) > 0


class TestPDFTemplates:
    """
    Test collection for PDF template functions.
    """

    def test_get_pdf_cover_template(self):
        """
        Test getting PDF cover template.
        """
        template = get_pdf_cover_template()
        assert template is not None
        assert template.id == "CoverPage"

    def test_get_pdf_introduction_template(self):
        """
        Test getting PDF introduction template.
        """
        template = get_pdf_introduction_template()
        assert template is not None
        assert template.id == "IntroductionPage"

    def test_get_pdf_principle_template(self):
        """
        Test getting PDF principle templates.
        """
        first_page, later_pages = get_pdf_principle_template()
        assert first_page is not None
        assert later_pages is not None
        assert first_page.id == "FirstPage"
        assert later_pages.id == "LaterPages"


class TestGeneratePDFReport:
    """
    Test collection for the main PDF report generation function.
    """

    def test_generate_pdf_report_basic(self, tmp_path, mocker):
        """
        Test basic PDF report generation.
        """
        workspace_data = {
            "company_name": "Test Company",
            "app_name": "Test Application",
            "upload_results": {"file_path": "test_path"},
            "process_checks": {
                "outcome1": {
                    "process1": {
                        "principle_key": "transparency",
                        "implementation": "Yes",
                    }
                }
            },
        }

        # Mock external dependencies
        mocker.patch("backend.pdf_generator.get_report_info", return_value={})
        mock_process_principle = mocker.patch("backend.pdf_generator.process_principle")

        # Mock data for all principles that might be processed
        def mock_principle_data(workspace_data, principle_name, principle_number):
            return {
                principle_name: {
                    "yes": 1,
                    "no": 0,
                    "na": 0,
                    "all_yes": True,
                    "description": "Test description",
                    "wim": ["What it means text"],
                    "recommendation": "Test recommendation",
                }
            }

        mock_process_principle.side_effect = mock_principle_data
        mocker.patch(
            "backend.pdf_generator.create_donut_chart",
            return_value=str(tmp_path / "chart.png"),
        )

        # Mock SimpleDocTemplate
        mock_doc = MagicMock()
        mock_doc_class = mocker.patch(
            "backend.pdf_generator.SimpleDocTemplate", return_value=mock_doc
        )

        # Mock os.makedirs
        mocker.patch("os.makedirs")

        with patch("backend.pdf_generator.OUTPUTS_DIRECTORY", str(tmp_path)):
            result_path = generate_pdf_report(workspace_data)

            expected_path = os.path.join(str(tmp_path), "summary_report.pdf")
            assert result_path == expected_path

            mock_doc_class.assert_called_once()
            mock_doc.addPageTemplates.assert_called_once()
            mock_doc.build.assert_called_once()


class TestErrorHandling:
    """
    Test collection for error handling scenarios.
    """

    def test_create_donut_chart_file_error(self, tmp_path, mocker):
        """
        Test donut chart creation with file write error.
        """
        mock_plt = mocker.patch("backend.pdf_generator.plt")
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        mock_plt.Circle.return_value = MagicMock()
        mock_plt.savefig.side_effect = OSError("Permission denied")

        with patch("backend.pdf_generator.OUTPUTS_DIRECTORY", str(tmp_path)):
            data = {"test": {"yes": 1, "no": 0, "na": 0}}

            with pytest.raises(OSError):
                create_donut_chart(data, "test")
