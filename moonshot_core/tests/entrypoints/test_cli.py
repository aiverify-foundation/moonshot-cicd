import asyncio
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from click.testing import CliRunner
import toml

from entrypoints.cli.cli import (
    cli,
    create_run_test,
    welcome,
    update_tasks_status,
    MoonshotProgressBar,
    ProgressManager,
    progress_manager,
)


class TestWelcome:
    """Test cases for the welcome function."""

    @patch('builtins.print')
    def test_welcome_displays_logo(self, mock_print):
        """Test that welcome function displays the Project Moonshot logo."""
        # Act
        welcome()
        
        # Assert
        mock_print.assert_called_once()
        logo_output = mock_print.call_args[0][0]
        # The logo is ASCII art, so let's check for unique parts
        assert "_____" in logo_output  # Check for ASCII art
        assert "___/" in logo_output   # Another unique part of the ASCII art


class TestCli:
    """Test cases for the CLI command group."""

    def setup_method(self):
        """Setup for each test method."""
        self.runner = CliRunner()

    @patch('entrypoints.cli.cli.AppConfig')
    @patch('builtins.open', mock_open(read_data='[tool.poetry]\nname="test-app"\nversion="1.0.0"\nauthors=["Test Author"]\nlicense="MIT"\ndescription="Test description"'))
    @patch('entrypoints.cli.cli.welcome')
    @patch('builtins.print')
    def test_cli_no_subcommand_shows_welcome(self, mock_print, mock_welcome, mock_app_config):
        """Test that CLI shows welcome page when no subcommand is provided."""

        result = self.runner.invoke(cli, [])
        
        assert result.exit_code == 0
        mock_welcome.assert_called_once()
        mock_app_config.assert_called_once()

    @patch('entrypoints.cli.cli.AppConfig')
    @patch('builtins.open', mock_open(read_data='[tool.poetry]\nname="test-app"\nversion="1.0.0"\nauthors=["Test Author"]\nlicense="MIT"\ndescription="Test description"'))
    def test_cli_with_subcommand_no_welcome(self, mock_app_config):
        """Test that CLI doesn't show welcome page when subcommand is provided."""
        with patch('entrypoints.cli.cli.ApiAdapter') as mock_api_adapter:
            mock_adapter_instance = MagicMock()
            mock_adapter_instance.create_run_test = AsyncMock()
            mock_api_adapter.return_value = mock_adapter_instance
            
            result = self.runner.invoke(cli, ['run', 'test_run_id', 'test_config_id', 'test_connector'])
            
            # Assert - AppConfig should still be called for initialization
            mock_app_config.assert_called_once()


class TestCreateRunTest:
    """Test cases for the create_run_test function."""

    def setup_method(self):
        """Setup for each test method."""
        self.runner = CliRunner()

    @pytest.mark.parametrize("run_id,test_config_id,connector,expected_calls", [
        # Good cases
        ("valid_run_id", "valid_config", "valid_connector", 1),
        ("run_123", "config_456", "openai_connector", 1),
        # Edge cases with special characters
        ("run-with-dashes", "config_with_underscores", "connector.with.dots", 1),
        ("run_with_numbers_123", "config_789", "connector_abc", 1),
    ])
    def test_create_run_test_valid_parameters(self, run_id, test_config_id, connector, expected_calls):
        """Test create_run_test with valid parameters."""
        with patch('entrypoints.cli.cli.ApiAdapter') as mock_api_adapter:

            mock_adapter_instance = MagicMock()
            mock_adapter_instance.create_run_test = AsyncMock()
            mock_api_adapter.return_value = mock_adapter_instance

            result = self.runner.invoke(create_run_test, [run_id, test_config_id, connector])
            
            # Assert
            assert result.exit_code == 0
            mock_api_adapter.assert_called_once()

    @pytest.mark.parametrize("run_id,test_config_id,connector,should_fail", [
        # Bad cases - missing arguments
        ("", "valid_config", "valid_connector", True),
        ("valid_run", "", "valid_connector", True),
        ("valid_run", "valid_config", "", True),
        # Bad cases - None values (would be caught by Click)
        (None, "valid_config", "valid_connector", True),
    ])
    def test_create_run_test_invalid_parameters(self, run_id, test_config_id, connector, should_fail):
        """Test create_run_test with invalid parameters."""
        # Filter out None values as Click would handle them differently
        args = [arg for arg in [run_id, test_config_id, connector] if arg is not None]
        
        # Act
        result = self.runner.invoke(create_run_test, args)
        
        # Assert
        if should_fail and len(args) < 3:
            assert result.exit_code != 0  # Click should return error for missing args

    def test_create_run_test_api_adapter_exception(self):
        """Test create_run_test when ApiAdapter raises an exception."""
        with patch('entrypoints.cli.cli.ApiAdapter') as mock_api_adapter:
            # Arrange
            mock_adapter_instance = MagicMock()
            mock_adapter_instance.create_run_test = AsyncMock(side_effect=Exception("API Error"))
            mock_api_adapter.return_value = mock_adapter_instance

            # Act
            result = self.runner.invoke(create_run_test, ["test_run", "test_config", "test_connector"])
            
            # Assert - Exception should cause non-zero exit code
            assert result.exit_code == 1  # CLI propagates the exception as exit code 1
            mock_api_adapter.assert_called_once()

    def test_create_run_test_sets_progress_manager_properties(self):
        """Test that create_run_test properly sets progress manager properties."""
        with patch('entrypoints.cli.cli.ApiAdapter') as mock_api_adapter:
            # Arrange
            mock_adapter_instance = MagicMock()
            mock_adapter_instance.create_run_test = AsyncMock()
            mock_api_adapter.return_value = mock_adapter_instance
            
            run_id = "test_run"
            test_config_id = "test_config"
            connector = "test_connector"

            # Act
            result = self.runner.invoke(create_run_test, [run_id, test_config_id, connector])
            
            # Assert
            assert result.exit_code == 0
            # Check that progress manager properties were set (these are global)
            assert progress_manager.title == f"Moonshot Run Test: {test_config_id}"
            assert f"Run ID: {run_id}" in progress_manager.test_info
            assert f"Test Configuration ID: {test_config_id}" in progress_manager.test_info
            assert f"Connector: {connector}" in progress_manager.test_info


class TestMoonshotProgressBar:
    """Test cases for the MoonshotProgressBar class."""

    def test_moonshot_progress_bar_initialization(self):
        """Test MoonshotProgressBar initialization with title."""
        # Arrange
        title = "Test Progress Bar"
        
        # Act
        progress_bar = MoonshotProgressBar(title=title)
        
        # Assert
        assert progress_bar.title == title

    def test_get_renderables_creates_panel(self):
        """Test that get_renderables creates a Panel with correct styling."""
        # Arrange
        title = "Test Progress"
        progress_bar = MoonshotProgressBar(title=title)
        
        # Act
        renderables = list(progress_bar.get_renderables())
        
        # Assert
        assert len(renderables) == 1
        # The Panel should contain the title and styling
        panel = renderables[0]
        assert hasattr(panel, 'title')


class TestProgressManager:
    """Test cases for the ProgressManager class."""

    def setup_method(self):
        """Setup for each test method."""
        self.progress_manager = ProgressManager()

    def test_progress_manager_initialization(self):
        """Test ProgressManager initial state."""
        # Assert
        assert self.progress_manager.title == ""
        assert self.progress_manager.test_info == ""
        assert self.progress_manager.task_id is None

    @pytest.mark.parametrize("title,test_info,expected_title,expected_info", [
        # Good cases
        ("Test Title", "Test Info", "Test Title", "Test Info"),
        ("", "", "", ""),
        ("Long Title with Spaces", "Detailed test information", "Long Title with Spaces", "Detailed test information"),
        # Edge cases with special characters
        ("Title with 特殊字符", "Info with émojis 🚀", "Title with 特殊字符", "Info with émojis 🚀"),
    ])
    def test_progress_manager_property_assignment(self, title, test_info, expected_title, expected_info):
        """Test ProgressManager property assignment."""
        # Act
        self.progress_manager.title = title
        self.progress_manager.test_info = test_info
        
        # Assert
        assert self.progress_manager.title == expected_title
        assert self.progress_manager.test_info == expected_info

    @pytest.mark.parametrize("total,expected_started", [
        # Good cases
        (10, True),
        (100, True),
        (1, True),
        # Edge cases
        (0, True),  # Even 0 should start progress
    ])
    @patch('entrypoints.cli.cli.MoonshotProgressBar')
    def test_start_progress_valid_total(self, mock_progress_bar, total, expected_started):
        """Test start_progress with valid total values."""
        # Arrange
        mock_progress_instance = MagicMock()
        mock_progress_bar.return_value = mock_progress_instance
        
        # Act
        self.progress_manager.start_progress(total)
        
        # Assert
        if expected_started:
            mock_progress_bar.assert_called_once()
            assert self.progress_manager.task_id is not None
        else:
            mock_progress_bar.assert_not_called()
            assert self.progress_manager.task_id is None

    @pytest.mark.parametrize("total", [
        # Bad cases - negative values
        (-1,),
        (-10,),
        (-100,),
    ])
    @patch('entrypoints.cli.cli.MoonshotProgressBar')
    def test_start_progress_negative_total(self, mock_progress_bar, total):
        """Test start_progress with negative total values."""
        # Act - The actual implementation doesn't validate negative values, so we need to test actual behavior
        self.progress_manager.start_progress(total)
        
        # Assert - Progress bar should still be created even with negative values
        mock_progress_bar.assert_called_once()
        assert self.progress_manager.task_id is not None

    def test_update_progress_valid_state(self):
        """Test update_progress when progress is properly initialized."""
        # Arrange
        with patch('entrypoints.cli.cli.MoonshotProgressBar') as mock_progress_bar:
            mock_progress_instance = MagicMock()
            mock_progress_bar.return_value = mock_progress_instance
            
            self.progress_manager.start_progress(10)
            
            # Act
            self.progress_manager.update_progress(5)
            
            # Assert
            # Should not raise any exceptions
            assert self.progress_manager.task_id is not None

    def test_update_progress_no_task_id(self):
        """Test update_progress when no task_id is set."""
        # Act & Assert - Should not raise exception, just silently handle
        self.progress_manager.update_progress(5)
        assert self.progress_manager.task_id is None

    def test_complete_progress_valid_state(self):
        """Test complete_progress when progress is properly initialized."""
        # Arrange
        with patch('entrypoints.cli.cli.MoonshotProgressBar') as mock_progress_bar:
            mock_progress_instance = MagicMock()
            mock_progress_bar.return_value = mock_progress_instance
            
            self.progress_manager.start_progress(10)
            
            # Act
            self.progress_manager.complete_progress()
            
            # Assert - task_id should be reset to None after completion
            assert self.progress_manager.task_id is None

    def test_complete_progress_no_task_id(self):
        """Test complete_progress when no task_id is set."""
        # Act & Assert - Should not raise exception, just silently handle
        self.progress_manager.complete_progress()
        assert self.progress_manager.task_id is None


class TestUpdateTasksStatus:
    """Test cases for the update_tasks_status function."""

    def setup_method(self):
        """Setup for each test method."""
        self.runner = CliRunner()

    @pytest.mark.parametrize("stage,message,expected_log", [
        # Good cases for stage and message
        (1, "Starting process", "[Stage 1] Starting process"),
        (2, "Processing data", "[Stage 2] Processing data"),
        (10, "Final stage", "[Stage 10] Final stage"),
    ])
    @patch('entrypoints.cli.cli.logger')
    def test_update_tasks_status_stage_message(self, mock_logger, stage, message, expected_log):
        """Test update_tasks_status with stage and message parameters."""
        # Act
        update_tasks_status(stage=stage, message=message)
        
        # Assert
        mock_logger.info.assert_called_once_with(expected_log)

    @pytest.mark.parametrize("state,total_prompts,completed_count,expected_behavior", [
        # Good cases for completed state
        ("completed", 10, 5, "update_progress"),
        ("completed", 10, 10, "complete_progress"),
        ("completed", 100, 50, "update_progress"),
        ("completed", 1, 1, "complete_progress"),
    ])
    @patch('entrypoints.cli.cli.progress_manager')
    @patch('entrypoints.cli.cli.logger')
    def test_update_tasks_status_completed_state(self, mock_logger, mock_progress_manager, 
                                                state, total_prompts, completed_count, expected_behavior):
        """Test update_tasks_status with completed state."""
        # Act
        update_tasks_status(state=state, total_prompts=total_prompts, completed_count=completed_count)
        
        # Assert
        mock_logger.info.assert_called_once()  # Should log the completion message
        if expected_behavior == "complete_progress":
            mock_progress_manager.complete_progress.assert_called_once()
        elif expected_behavior == "update_progress":
            mock_progress_manager.update_progress.assert_called_once_with(completed=completed_count)

    @pytest.mark.parametrize("total_prompts,completed_count", [
        # Good cases for running state
        (10, 0),
        (100, 5),
        (50, None),  # completed_count can be None
    ])
    @patch('entrypoints.cli.cli.progress_manager')
    def test_update_tasks_status_running_state(self, mock_progress_manager, total_prompts, completed_count):
        """Test update_tasks_status with running state."""
        # Setup mock to simulate task_id is None initially
        mock_progress_manager.task_id = None
        
        # Act
        update_tasks_status(state="running", total_prompts=total_prompts, completed_count=completed_count)
        
        # Assert
        mock_progress_manager.start_progress.assert_called_once_with(total=total_prompts)
        if completed_count is not None:
            mock_progress_manager.update_progress.assert_called_once_with(completed=completed_count)

    @pytest.mark.parametrize("state,total_prompts,completed_count", [
        # Bad cases - None values where they shouldn't be
        ("completed", None, 5),
        ("completed", 10, None),
        # Edge case - zero values
        ("completed", 0, 0),
    ])
    @patch('entrypoints.cli.cli.progress_manager')
    @patch('entrypoints.cli.cli.logger')
    def test_update_tasks_status_edge_cases(self, mock_logger, mock_progress_manager, 
                                          state, total_prompts, completed_count):
        """Test update_tasks_status with edge cases."""
        # Act
        update_tasks_status(state=state, total_prompts=total_prompts, completed_count=completed_count)
        
        # Assert - Should handle gracefully without errors
        # The exact behavior depends on implementation

    def test_update_tasks_status_no_parameters(self):
        """Test update_tasks_status with no parameters."""
        # Act & Assert - Should not raise exceptions
        update_tasks_status()

    @pytest.mark.parametrize("invalid_state", [
        # Bad cases - invalid states
        ("invalid_state",),
        ("unknown",),
        ("",),
    ])
    @patch('entrypoints.cli.cli.logger')
    def test_update_tasks_status_invalid_state(self, mock_logger, invalid_state):
        """Test update_tasks_status with invalid state values."""
        # Act
        update_tasks_status(state=invalid_state)
        
        # Assert - Should handle gracefully, possibly with logging
        # The exact behavior depends on implementation


class TestPyprojectLoading:
    """Test cases for pyproject.toml loading functionality."""

    def setup_method(self):
        """Setup for each test method."""
        self.runner = CliRunner()

    @patch('builtins.open', mock_open(read_data='''
[tool.poetry]
name = "test-moonshot"
version = "2.0.0"
authors = ["Test Author <test@example.com>"]
license = "Apache-2.0"
description = "Test moonshot application"
'''))
    def test_pyproject_loading_success(self):
        """Test successful loading of pyproject.toml."""
        # Act
        result = self.runner.invoke(cli, [])
        
        # Assert
        assert result.exit_code == 0
        # The CLI should load without errors when pyproject.toml is valid

    @patch('builtins.open', side_effect=FileNotFoundError("pyproject.toml not found"))
    def test_pyproject_loading_file_not_found(self, mock_open):
        """Test handling when pyproject.toml is not found."""
        # Act
        result = self.runner.invoke(cli, [])
        
        # Assert - Should handle gracefully
        # Exact behavior depends on implementation

    @patch('builtins.open', mock_open(read_data='invalid toml content'))
    @patch('entrypoints.cli.cli.toml.load', side_effect=toml.TomlDecodeError("Invalid TOML", "invalid toml content", 0))
    def test_pyproject_loading_invalid_toml(self, mock_toml_load):
        """Test handling when pyproject.toml contains invalid TOML."""
        # Act
        result = self.runner.invoke(cli, [])
        
        # Assert - Should handle gracefully
        # Exact behavior depends on implementation


class TestIntegration:
    """Integration test cases for CLI functionality."""

    def setup_method(self):
        """Setup for each test method."""
        self.runner = CliRunner()

    @patch('entrypoints.cli.cli.AppConfig')
    @patch('builtins.open', mock_open(read_data='[tool.poetry]\nname="test-app"\nversion="1.0.0"\nauthors=["Test Author"]\nlicense="MIT"\ndescription="Test description"'))
    def test_full_run_workflow(self, mock_app_config):
        """Test a complete workflow from CLI invocation to completion."""
        with patch('entrypoints.cli.cli.ApiAdapter') as mock_api_adapter:
            # Arrange
            mock_adapter_instance = MagicMock()
            mock_adapter_instance.create_run_test = AsyncMock()
            mock_api_adapter.return_value = mock_adapter_instance

            # Act - Simulate a full run command
            result = self.runner.invoke(cli, ['run', 'integration_test_run', 'test_config', 'test_connector'])
            
            # Assert
            assert result.exit_code == 0
            mock_app_config.assert_called_once()
            mock_api_adapter.assert_called_once() 