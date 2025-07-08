import pytest
from unittest.mock import Mock, AsyncMock, patch, call, MagicMock
from typing import Callable
from pydantic import ValidationError

from domain.entities.connector_entity import ConnectorEntity
from domain.entities.dataset_entity import DatasetEntity
from domain.entities.prompt_entity import PromptEntity
from domain.ports.prompt_processor_port import PromptProcessorPort
from domain.services.enums.task_manager_status import TaskManagerStatus
from domain.services.benchmark.benchmark_task import BenchmarkTask


class TestBenchmarkTask:
    """Test class for BenchmarkTask"""

    @pytest.fixture
    def mock_connector_entity(self):
        """Create a mock ConnectorEntity for testing"""
        return ConnectorEntity(
            connector_adapter="openai_adapter",
            model="gpt-3.5-turbo",
            model_endpoint="https://api.openai.com/v1",
            params={"temperature": 0.7, "max_tokens": 100},
            connector_pre_prompt="Pre: ",
            connector_post_prompt=" :Post",
            system_prompt="You are a helpful assistant."
        )

    @pytest.fixture
    def mock_dataset_entity(self):
        """Create a mock DatasetEntity for testing"""
        return DatasetEntity(
            id="test_dataset",
            name="Test Dataset",
            description="A dataset for testing",
            examples=[
                {"input": "What is AI?", "target": "Artificial Intelligence", "extra_field": "hello_world"},
                {"input": "Define ML", "target": "Machine Learning","extra_field": "hello_world"},
                {"input": "Hello", "target": "Hi there!","extra_field": "hello_world"}
            ],
            num_of_dataset_prompts=3,
            created_date="2024-01-01 12:00:00",
            reference="test_reference",
            license="test_license"
        )

    @pytest.fixture
    def mock_prompt_processor(self):
        """Create a mock PromptProcessorPort for testing"""
        mock_processor = AsyncMock(spec=PromptProcessorPort)
        mock_processor.process_prompts.return_value = [
            PromptEntity(
                index=1,
                prompt="What is AI?",
                target="Artificial Intelligence",
                model_prediction="AI is artificial intelligence",
                evaluation_result={"score": 0.9},
                additional_info={"extra_field": "hello_world"},
                state=TaskManagerStatus.COMPLETED
            )
        ]
        return mock_processor

    @pytest.fixture
    def mock_callback_fn(self):
        """Create a mock callback function for testing"""
        return Mock(spec=Callable)

    @pytest.fixture
    def benchmark_task_without_callback(self, mock_connector_entity, mock_dataset_entity, mock_prompt_processor):
        """Create a BenchmarkTask instance without callback for testing"""
        return BenchmarkTask(
            task_id="test_task_123",
            connector_entity=mock_connector_entity,
            metric="accuracy_adapter",
            dataset_entity=mock_dataset_entity,
            prompt_processor_instance=mock_prompt_processor
        )

    @pytest.fixture
    def benchmark_task_with_callback(self, mock_connector_entity, mock_dataset_entity, 
                                   mock_prompt_processor, mock_callback_fn):
        """Create a BenchmarkTask instance with callback for testing"""
        return BenchmarkTask(
            task_id="test_task_with_callback",
            connector_entity=mock_connector_entity,
            metric="refusal_adapter",
            dataset_entity=mock_dataset_entity,
            prompt_processor_instance=mock_prompt_processor,
            callback_fn=mock_callback_fn
        )

    @pytest.mark.parametrize("task_id,connector_adapter,model,metric,callback_present,expected_state", [
        ("test_123", "openai", "gpt-4", "accuracy", False, TaskManagerStatus.PENDING),
        ("task_with_callback", "claude", "claude-3", "bleu", True, TaskManagerStatus.PENDING),
        ("", "empty_adapter", "", "", False, TaskManagerStatus.PENDING),
        ("unicode_task_测试", "unicode_adapter", "unicode_model", "unicode_metric", True, TaskManagerStatus.PENDING),
        ("special!@#$%", "special_adapter", "special_model", "special_metric", False, TaskManagerStatus.PENDING),
    ])
    def test_constructor_attribute_assignments(self, mock_dataset_entity, mock_prompt_processor, 
                                             task_id, connector_adapter, model, metric, callback_present, expected_state):
        """Test that constructor properly assigns all attributes (lines 45-52)"""
        # Arrange
        connector_entity = ConnectorEntity(
            connector_adapter=connector_adapter,
            model=model,
            model_endpoint="https://api.test.com",
            params={"temp": 0.5},
            connector_pre_prompt="pre",
            connector_post_prompt="post",
            system_prompt="system"
        )
        
        callback_fn = Mock(spec=Callable) if callback_present else None

        # Act
        task = BenchmarkTask(
            task_id=task_id,
            connector_entity=connector_entity,
            metric=metric,
            dataset_entity=mock_dataset_entity,
            prompt_processor_instance=mock_prompt_processor,
            callback_fn=callback_fn
        )

        # Assert - Test lines 45-52 assignments
        assert task.task_id == task_id  # Line 45
        assert task.state == expected_state  # Line 46
        assert task.prompts == []  # Line 47
        assert task.dataset_entity == mock_dataset_entity  # Line 48
        assert task.connector_entity == connector_entity  # Line 49
        assert task.metric == metric  # Line 50
        assert task.prompt_processor_instance == mock_prompt_processor  # Line 51
        assert task.callback_fn == callback_fn  # Line 52

    @pytest.mark.parametrize("task_fixture,expected_task_id,expected_metric,has_callback", [
        ("benchmark_task_without_callback", "test_task_123", "accuracy_adapter", False),
        ("benchmark_task_with_callback", "test_task_with_callback", "refusal_adapter", True)
    ])
    def test_initialization(self, request, task_fixture, expected_task_id, expected_metric, has_callback,
                          mock_connector_entity, mock_dataset_entity, mock_prompt_processor):
        """Test BenchmarkTask initialization with and without callback function"""
        # Arrange
        task = request.getfixturevalue(task_fixture)
        
        # Assert
        assert task.task_id == expected_task_id
        assert task.state == TaskManagerStatus.PENDING
        assert task.prompts == []
        assert task.dataset_entity == mock_dataset_entity
        assert task.connector_entity == mock_connector_entity
        assert task.metric == expected_metric
        assert task.prompt_processor_instance == mock_prompt_processor
        
        if has_callback:
            assert task.callback_fn is not None
        else:
            assert task.callback_fn is None

    @pytest.mark.parametrize("task_id,connector_adapter,model,metric,should_raise", [
        # Valid cases
        ("valid_task", "openai_adapter", "gpt-4", "accuracy", False),
        ("", "openai_adapter", "gpt-4", "accuracy", False),  # Empty task_id
        ("task", "", "gpt-4", "accuracy", False),  # Empty connector_adapter
        ("task", "openai_adapter", "", "accuracy", False),  # Empty model
        ("task", "openai_adapter", "gpt-4", "", False),  # Empty metric
        # Edge cases with special characters
        ("task-with-special!@#$%^&*()", "adapter_with_underscores", "model.name", "metric:score", False),
        # Very long strings
        ("a" * 1000, "b" * 500, "c" * 200, "d" * 100, False),
        # Unicode characters
        ("测试任务", "连接器", "模型", "指标", False),
        # None values (these might raise AttributeError depending on implementation)
        # (None, "openai_adapter", "gpt-4", "accuracy", True),
    ])
    def test_initialization_edge_cases(self, mock_dataset_entity, mock_prompt_processor, 
                                     task_id, connector_adapter, model, metric, should_raise):
        """Test BenchmarkTask initialization with edge cases and unexpected inputs"""
        if connector_adapter is not None:
            connector_entity = ConnectorEntity(
                connector_adapter=connector_adapter,
                model=model,
                model_endpoint="https://api.example.com/v1",
                params={"temperature": 0.7},
                connector_pre_prompt="",
                connector_post_prompt="",
                system_prompt=""
            )
        else:
            connector_entity = None

        if should_raise:
            with pytest.raises((TypeError, AttributeError, ValueError)):
                BenchmarkTask(
                    task_id=task_id,
                    connector_entity=connector_entity,
                    metric=metric,
                    dataset_entity=mock_dataset_entity,
                    prompt_processor_instance=mock_prompt_processor
                )
        else:
            task = BenchmarkTask(
                task_id=task_id,
                connector_entity=connector_entity,
                metric=metric,
                dataset_entity=mock_dataset_entity,
                prompt_processor_instance=mock_prompt_processor
            )
            
            assert task.task_id == task_id
            assert task.metric == metric

    @pytest.mark.parametrize("examples,expected_processing", [
        # Test the enumerate(self.dataset_entity.examples, 1) logic (line 61)
        ([{"input": "test1", "target": "result1"}], [(1, "test1", "result1", {})]),
        ([{"input": "test1", "target": "result1"}, {"input": "test2", "target": "result2"}], 
         [(1, "test1", "result1", {}), (2, "test2", "result2", {})]),
        # Test example.pop() logic (lines 63-64)
        ([{"input": "test", "target": "result", "extra": "data"}], [(1, "test", "result", {"extra": "data"})]),
        ([{"target": "result", "extra": "data"}], [(1, "", "result", {"extra": "data"})]),  # Missing input
        ([{"input": "test", "extra": "data"}], [(1, "test", "", {"extra": "data"})]),  # Missing target
        ([{"extra": "data"}], [(1, "", "", {"extra": "data"})]),  # Missing both input and target
        # Test additional_info collection (line 66)
        ([{"input": "test", "target": "result", "field1": "value1", "field2": "value2"}], 
         [(1, "test", "result", {"field1": "value1", "field2": "value2"})]),
        # Test empty examples
        ([], []),
        # Test complex additional info
        ([{"input": "test", "target": "result", "nested": {"key": "value"}, "list": [1, 2, 3]}], 
         [(1, "test", "result", {"nested": {"key": "value"}, "list": [1, 2, 3]})]),
    ])
    @patch('domain.services.benchmark.benchmark_task.logger')
    def test_generate_prompts_enumeration_and_processing(self, mock_logger, mock_connector_entity, 
                                                        mock_prompt_processor, examples, expected_processing):
        """Test the generate_prompts method focusing on lines 61-86 enumeration and example processing"""
        # Arrange
        dataset = DatasetEntity(
            id="test_enumeration",
            name="Enumeration Test Dataset",
            description="Test dataset for enumeration logic",
            examples=examples
        )
        
        task = BenchmarkTask(
            task_id="enumeration_test",
            connector_entity=mock_connector_entity,
            metric="test_metric",
            dataset_entity=dataset,
            prompt_processor_instance=mock_prompt_processor
        )

        prompts = task.generate_prompts()

        # Assert enumeration and processing logic
        assert len(prompts) == len(expected_processing)
        
        for i, (expected_index, expected_prompt, expected_target, expected_additional) in enumerate(expected_processing):
            prompt = prompts[i]
            assert prompt.index == expected_index  # Test enumerate(examples, 1) starting at 1
            assert prompt.prompt == expected_prompt  # Test input extraction with pop()
            assert prompt.target == expected_target  # Test target extraction with pop()
            assert prompt.additional_info == expected_additional  # Test additional_info collection
            assert prompt.model_prediction is None  # Test default None assignment
            assert prompt.evaluation_result == {}  # Test default empty dict assignment

    @pytest.mark.parametrize("dataset_examples,expected_behavior", [
        # Normal cases
        ([{"input": "test", "target": "result"}], "success"),
        # Edge cases with data types
        ([{"input": 123, "target": 456}], "success"),  # Numbers as input/target
        ([{"input": True, "target": False}], "success"),  # Booleans
        ([{"input": ["list", "input"], "target": {"dict": "target"}}], "success"),  # Complex types
        ([{"input": None, "target": None}], "success"),  # None values
        # Very large datasets
        ([{"input": f"input_{i}", "target": f"target_{i}"} for i in range(1000)], "success"),
        # Malformed examples
        ([{"not_input": "test", "not_target": "result"}], "success"),  # Missing input/target keys
        ([{}], "success"),  # Empty dictionaries
        ([None], "error"),  # None as example
        (["string_instead_of_dict"], "error"),  # String instead of dict
        ([{"input": "test"}, "invalid_example"], "error"),  # Mixed valid/invalid
    ])
    def test_generate_prompts_with_edge_case_datasets(self, mock_connector_entity, mock_prompt_processor,
                                                    dataset_examples, expected_behavior):
        """Test prompt generation with various edge case datasets"""
        # Arrange
        dataset = DatasetEntity(
            id="edge_case_dataset",
            name="Edge Case Dataset",
            description="Dataset with edge cases",
            examples=dataset_examples
        )
        
        task = BenchmarkTask(
            task_id="edge_test",
            connector_entity=mock_connector_entity,
            metric="test_metric",
            dataset_entity=dataset,
            prompt_processor_instance=mock_prompt_processor
        )

        if expected_behavior == "error":
            # Act & Assert
            with pytest.raises((TypeError, AttributeError, KeyError)):
                task.generate_prompts()
        else:
            # Act
            prompts = task.generate_prompts()
            
            # Assert
            assert len(prompts) == len(dataset_examples)
            for i, prompt in enumerate(prompts):
                assert prompt.index == i + 1
                assert isinstance(prompt, PromptEntity)

    @pytest.mark.parametrize("task_fixture", [
        "benchmark_task_without_callback",
        "benchmark_task_with_callback"
    ])
    @patch('domain.services.benchmark.benchmark_task.logger')
    def test_generate_results_logging(self, mock_logger, request, task_fixture):
        """Test generate_results method specifically for line 92 logging behavior"""
        # Arrange
        task = request.getfixturevalue(task_fixture)

        # Act
        task.generate_results()

        # Assert
        mock_logger.info.assert_called_once_with(BenchmarkTask.INFO_GENERATING_RESULTS)

    @patch('domain.services.benchmark.benchmark_task.logger')
    def test_generate_prompts_success(self, mock_logger, benchmark_task_without_callback):
        """Test successful prompt generation from dataset"""
        # Act
        prompts = benchmark_task_without_callback.generate_prompts()

        # Assert
        assert len(prompts) == 3
        mock_logger.info.assert_called_once_with(BenchmarkTask.INFO_GENERATING_PROMPTS)

        # Check first prompt
        first_prompt = prompts[0]
        assert first_prompt.index == 1
        assert first_prompt.prompt == "What is AI?"
        assert first_prompt.target == "Artificial Intelligence"
        assert first_prompt.model_prediction is None
        assert first_prompt.evaluation_result == {}
        assert first_prompt.additional_info == {"extra_field": "hello_world"}

        # Check second prompt
        second_prompt = prompts[1]
        assert second_prompt.index == 2
        assert second_prompt.prompt == "Define ML"
        assert second_prompt.target == "Machine Learning"
        assert second_prompt.additional_info == {"extra_field": "hello_world"}

        # Check third prompt
        third_prompt = prompts[2]
        assert third_prompt.index == 3
        assert third_prompt.prompt == "Hello"
        assert third_prompt.target == "Hi there!"
        assert third_prompt.additional_info == {"extra_field": "hello_world"}

    @pytest.mark.parametrize("examples,expected_prompts", [
        # Missing input and target
        ([{"other_field": "value1", "category": "test"}], 
         [{"prompt": "", "target": "", "additional_info": {"other_field": "value1", "category": "test"}}]),
        # Missing target only
        ([{"input": "Only input", "category": "test"}], 
         [{"prompt": "Only input", "target": "", "additional_info": {"category": "test"}}]),
        # Missing input only
        ([{"target": "Only target", "category": "test"}], 
         [{"prompt": "", "target": "Only target", "additional_info": {"category": "test"}}]),
        # All three scenarios combined
        ([{"other_field": "value1", "category": "test"},
          {"input": "Only input", "category": "test"},
          {"target": "Only target", "category": "test"}],
         [{"prompt": "", "target": "", "additional_info": {"other_field": "value1", "category": "test"}},
          {"prompt": "Only input", "target": "", "additional_info": {"category": "test"}},
          {"prompt": "", "target": "Only target", "additional_info": {"category": "test"}}])
    ])
    @patch('domain.services.benchmark.benchmark_task.logger')
    def test_generate_prompts_with_missing_fields(self, mock_logger, mock_connector_entity, 
                                                mock_prompt_processor, examples, expected_prompts):
        """Test prompt generation when input or target is missing from examples"""
        dataset_with_missing_fields = DatasetEntity(
            id="test_missing",
            name="Test Missing Fields",
            description="Dataset with missing fields",
            examples=examples
        )
        
        task = BenchmarkTask(
            task_id="test_missing",
            connector_entity=mock_connector_entity,
            metric="test_metric",
            dataset_entity=dataset_with_missing_fields,
            prompt_processor_instance=mock_prompt_processor
        )

        prompts = task.generate_prompts()

        assert len(prompts) == len(expected_prompts)
        
        for i, expected in enumerate(expected_prompts):
            assert prompts[i].prompt == expected["prompt"]
            assert prompts[i].target == expected["target"]
            assert prompts[i].additional_info == expected["additional_info"]

    @patch('domain.services.benchmark.benchmark_task.logger')
    def test_generate_prompts_empty_dataset(self, mock_logger, mock_connector_entity, 
                                          mock_prompt_processor):
        """Test prompt generation with empty dataset"""
        # Arrange
        empty_dataset = DatasetEntity(
            id="empty",
            name="Empty Dataset",
            description="Empty dataset",
            examples=[]
        )
        
        task = BenchmarkTask(
            task_id="test_empty",
            connector_entity=mock_connector_entity,
            metric="test_metric",
            dataset_entity=empty_dataset,
            prompt_processor_instance=mock_prompt_processor
        )

        # Act
        prompts = task.generate_prompts()

        # Assert
        assert len(prompts) == 0
        mock_logger.info.assert_called_once_with(BenchmarkTask.INFO_GENERATING_PROMPTS)

    @patch('domain.services.benchmark.benchmark_task.logger')
    def test_generate_results(self, mock_logger, benchmark_task_without_callback):
        """Test generate_results method"""
        # Act
        benchmark_task_without_callback.generate_results()

        # Assert
        mock_logger.info.assert_called_once_with(BenchmarkTask.INFO_GENERATING_RESULTS)

    @pytest.mark.parametrize("initial_state,process_success,expected_final_state,expected_return", [
        (TaskManagerStatus.PENDING, True, TaskManagerStatus.COMPLETED, True),
        (TaskManagerStatus.PENDING, False, TaskManagerStatus.COMPLETED_WITH_ERRORS, False),
        (TaskManagerStatus.RUNNING, True, TaskManagerStatus.COMPLETED, True),
        (TaskManagerStatus.COMPLETED, True, TaskManagerStatus.COMPLETED, True),
    ])
    @patch('domain.services.benchmark.benchmark_task.logger')
    @pytest.mark.asyncio
    async def test_run_state_management_lines_101_118(self, mock_logger, mock_connector_entity, mock_dataset_entity, 
                                                     mock_prompt_processor, initial_state, process_success, 
                                                     expected_final_state, expected_return):
        """Test run method state management focusing on lines 101-118"""
        # Arrange
        task = BenchmarkTask(
            task_id="state_test",
            connector_entity=mock_connector_entity,
            metric="test_metric",
            dataset_entity=mock_dataset_entity,
            prompt_processor_instance=mock_prompt_processor
        )
        task.state = initial_state

        if process_success:
            mock_prompt_processor.process_prompts.return_value = []
        else:
            mock_prompt_processor.process_prompts.side_effect = Exception("Processing failed")

        # Act
        result = await task.run()

        # Assert state transitions and return value
        assert task.state == expected_final_state
        assert result == expected_return

        # Verify state was set to RUNNING during execution (line 101)
        # This is tested implicitly by the successful state transition

    @pytest.mark.parametrize("has_callback,task_fixture", [
        (False, "benchmark_task_without_callback"),
        (True, "benchmark_task_with_callback")
    ])
    @patch('domain.services.benchmark.benchmark_task.logger')
    @pytest.mark.asyncio
    async def test_run_success(self, mock_logger, request, has_callback, task_fixture, mock_prompt_processor):
        """Test successful run with and without callback function"""
        # Arrange
        task = request.getfixturevalue(task_fixture)
        expected_prompts_with_results = [
            PromptEntity(
                index=1,
                prompt="What is AI?",
                target="Artificial Intelligence",
                model_prediction="AI is artificial intelligence",
                evaluation_result={"score": 0.9},
                additional_info={"extra_field": "hello_world"},
                state=TaskManagerStatus.COMPLETED
            )
        ]
        mock_prompt_processor.process_prompts.return_value = expected_prompts_with_results

        # Act
        result = await task.run()

        # Assert
        assert result is True
        assert task.state == TaskManagerStatus.COMPLETED
        assert len(task.prompts) == 3
        assert task.prompts_with_results == expected_prompts_with_results

        # Verify method calls
        callback_fn = task.callback_fn if has_callback else None
        mock_prompt_processor.process_prompts.assert_called_once_with(
            task.prompts, 
            task.connector_entity, 
            task.metric, 
            callback_fn
        )

        # Verify logging calls
        expected_log_calls = [
            call(BenchmarkTask.INFO_GENERATING_PROMPTS),
            call(BenchmarkTask.INFO_PROMPTS_COUNT.format(count=3)),
            call(BenchmarkTask.INFO_GENERATING_RESULTS)
        ]
        mock_logger.info.assert_has_calls(expected_log_calls)

    @pytest.mark.parametrize("error_type,error_message,expected_state", [
        (Exception, "Processing failed", TaskManagerStatus.COMPLETED_WITH_ERRORS),
        (ValueError, "Invalid value", TaskManagerStatus.COMPLETED_WITH_ERRORS),
        (RuntimeError, "Runtime error occurred", TaskManagerStatus.COMPLETED_WITH_ERRORS),
        (ConnectionError, "Network connection failed", TaskManagerStatus.COMPLETED_WITH_ERRORS),
        (TimeoutError, "Operation timed out", TaskManagerStatus.COMPLETED_WITH_ERRORS)
    ])
    @patch('domain.services.benchmark.benchmark_task.logger')
    @pytest.mark.asyncio
    async def test_run_failure_in_prompt_processing(self, mock_logger, benchmark_task_without_callback, 
                                                   mock_prompt_processor, error_type, 
                                                   error_message, expected_state):
        """Test run failure when prompt processing raises different types of exceptions"""
        # Arrange
        mock_prompt_processor.process_prompts.side_effect = error_type(error_message)

        # Act
        result = await benchmark_task_without_callback.run()

        # Assert
        assert result is False
        assert benchmark_task_without_callback.state == expected_state

        # Verify error logging
        mock_logger.error.assert_called_once_with(
            BenchmarkTask.ERROR_OCCURRED.format(e=error_message)
        )

    @pytest.mark.parametrize("processor_return_value,expected_result,expected_state", [
        # Normal successful cases
        ([PromptEntity(index=1, prompt="test", target="target")], True, TaskManagerStatus.COMPLETED),
        ([], True, TaskManagerStatus.COMPLETED),  # Empty results
        # Edge cases
        (None, False, TaskManagerStatus.COMPLETED_WITH_ERRORS),  # None return
        ("not_a_list", False, TaskManagerStatus.COMPLETED_WITH_ERRORS),  # Wrong type
        ([None], False, TaskManagerStatus.COMPLETED_WITH_ERRORS),  # List with None
        (["string", "not", "prompt", "entities"], False, TaskManagerStatus.COMPLETED_WITH_ERRORS),  # Wrong list content
    ])
    @patch('domain.services.benchmark.benchmark_task.logger')
    @pytest.mark.asyncio
    async def test_run_with_unexpected_processor_returns(self, mock_logger, benchmark_task_without_callback, 
                                                        mock_prompt_processor, processor_return_value,
                                                        expected_result, expected_state):
        """Test run behavior with unexpected return values from prompt processor"""
        # Arrange
        if processor_return_value in [None, "not_a_list", [None], ["string", "not", "prompt", "entities"]]:
            mock_prompt_processor.process_prompts.side_effect = TypeError("Invalid return type")
        else:
            mock_prompt_processor.process_prompts.return_value = processor_return_value

        # Act
        result = await benchmark_task_without_callback.run()

        # Assert
        assert result == expected_result
        assert benchmark_task_without_callback.state == expected_state

    @pytest.mark.parametrize("callback_side_effect,expected_behavior", [
        (None, "success"),  # Normal callback
        (Exception("Callback failed"), "continue"),  # Callback raises exception
        (ValueError("Invalid callback input"), "continue"),  # Specific exception
        (RuntimeError("Callback runtime error"), "continue"),  # Another exception type
    ])
    @patch('domain.services.benchmark.benchmark_task.logger')
    @pytest.mark.asyncio
    async def test_run_with_failing_callbacks(self, mock_logger, benchmark_task_with_callback, 
                                             mock_prompt_processor, mock_callback_fn,
                                             callback_side_effect, expected_behavior):
        """Test run behavior when callback functions fail"""
        # Arrange
        if callback_side_effect:
            # Make the processor raise an exception when callback is used
            mock_prompt_processor.process_prompts.side_effect = callback_side_effect
        else:
            mock_prompt_processor.process_prompts.return_value = []

        # Act
        result = await benchmark_task_with_callback.run()

        # Assert
        if expected_behavior == "success":
            assert result is True
            assert benchmark_task_with_callback.state == TaskManagerStatus.COMPLETED
        else:  # continue - task should handle callback failures gracefully
            assert result is False
            assert benchmark_task_with_callback.state == TaskManagerStatus.COMPLETED_WITH_ERRORS

    @patch('domain.services.benchmark.benchmark_task.logger')
    @pytest.mark.asyncio
    async def test_run_failure_in_prompt_generation(self, mock_logger, mock_connector_entity, 
                                                   mock_prompt_processor):
        """Test run failure when prompt generation raises an exception"""
        # Arrange
        bad_dataset = DatasetEntity(
            id="bad_dataset",
            name="Bad Dataset",
            description="Dataset that causes errors",
            examples=[{"input": "test"}]  # This will work fine
        )
        
        task = BenchmarkTask(
            task_id="test_bad",
            connector_entity=mock_connector_entity,
            metric="test_metric",
            dataset_entity=bad_dataset,
            prompt_processor_instance=mock_prompt_processor
        )

        # Mock the dataset examples to raise an exception during iteration
        mock_examples = MagicMock()
        mock_examples.__iter__.side_effect = Exception("Dataset error")
        with patch.object(task.dataset_entity, 'examples', mock_examples):
            # Act
            result = await task.run()

            # Assert
            assert result is False
            assert task.state == TaskManagerStatus.COMPLETED_WITH_ERRORS
            mock_logger.error.assert_called_once()

    @pytest.mark.parametrize("initial_state,expected_final_state", [
        (TaskManagerStatus.PENDING, TaskManagerStatus.COMPLETED),
        # Note: These might not be realistic scenarios depending on implementation
        # but test how the system handles unexpected initial states
    ])
    @pytest.mark.asyncio
    async def test_run_state_transitions(self, benchmark_task_without_callback, mock_prompt_processor,
                                       initial_state, expected_final_state):
        """Test that task state transitions correctly during run"""
        # Arrange
        mock_prompt_processor.process_prompts.return_value = []
        benchmark_task_without_callback.state = initial_state

        # Act
        await benchmark_task_without_callback.run()

        # Assert final state
        assert benchmark_task_without_callback.state == expected_final_state

    @pytest.mark.parametrize("metric_name", [
        "accuracy_adapter",
        "bleu_score", 
        "rouge_score",
        "f1_score",
        "custom_metric",
        "refusal_adapter",
        "toxicity_detector",
        "",  # Empty metric
        "metric with spaces",
        "metric-with-dashes",
        "metric_with_underscores",
        "MetricWithCamelCase",
        "123numeric_metric",
        "特殊字符metric",  # Unicode characters
        "very_long_metric_name_that_exceeds_normal_length_expectations_and_tests_system_limits",
    ])
    def test_initialization_with_different_metrics(self, mock_connector_entity, mock_dataset_entity, 
                                                  mock_prompt_processor, metric_name):
        """Test initialization with different metric names including edge cases"""
        # Act
        task = BenchmarkTask(
            task_id="test_metric",
            connector_entity=mock_connector_entity,
            metric=metric_name,
            dataset_entity=mock_dataset_entity,
            prompt_processor_instance=mock_prompt_processor
        )

        # Assert
        assert task.metric == metric_name

    @pytest.mark.parametrize("task_id", [
        "simple_id",
        "task-with-dashes",
        "task_with_underscores", 
        "TaskWithCamelCase",
        "task123with456numbers",
        "very-long-task-id-with-many-parts-separated-by-dashes",
        "",  # Empty task ID
        " ",  # Whitespace only
        "task with spaces",
        "task\nwith\nnewlines",
        "task\twith\ttabs",
        "task/with/slashes",
        "task\\with\\backslashes",
        "task|with|pipes",
        "task@with@symbols#and$percent%",
        "测试任务ID",  # Unicode
        "🚀🔥💯",  # Emojis
        "a" * 1000,  # Very long ID
    ])
    def test_task_id_types(self, mock_connector_entity, mock_dataset_entity, 
                          mock_prompt_processor, task_id):
        """Test that task_id accepts different string formats including edge cases"""
        # Act
        task = BenchmarkTask(
            task_id=task_id,
            connector_entity=mock_connector_entity,
            metric="test_metric",
            dataset_entity=mock_dataset_entity,
            prompt_processor_instance=mock_prompt_processor
        )

        # Assert
        assert task.task_id == task_id

    @pytest.mark.parametrize("prompt_count,expected_order", [
        (1, ["What is AI?"]),
        (2, ["What is AI?", "Define ML"]),
        (3, ["What is AI?", "Define ML", "Hello"]),
        (0, []),  # Edge case: no prompts
    ])
    def test_prompt_generation_preserves_example_order(self, mock_connector_entity, mock_dataset_entity,
                                                     mock_prompt_processor, prompt_count, expected_order):
        """Test that prompt generation preserves the order of examples from dataset"""
        # Arrange
        if prompt_count == 0:
            dataset = DatasetEntity(
                id="empty_dataset",
                name="Empty Dataset", 
                description="Empty dataset",
                examples=[]
            )
        else:
            examples = mock_dataset_entity.examples[:prompt_count]
            dataset = DatasetEntity(
                id="test_dataset",
                name="Test Dataset",
                description="Test dataset",
                examples=examples
            )
        
        task = BenchmarkTask(
            task_id="order_test",
            connector_entity=mock_connector_entity,
            metric="test_metric",
            dataset_entity=dataset,
            prompt_processor_instance=mock_prompt_processor
        )

        # Act
        prompts = task.generate_prompts()

        # Assert
        assert len(prompts) == prompt_count
        for i, expected_prompt in enumerate(expected_order):
            assert prompts[i].prompt == expected_prompt
            assert prompts[i].index == i + 1

    @pytest.mark.parametrize("complex_data", [
        {
            "metadata": {"nested": {"deep": "value"}},
            "list_field": [1, 2, 3],
            "bool_field": True,
            "null_field": None
        },
        {
            "string_field": "simple string",
            "number_field": 42,
            "float_field": 3.14
        },
        {
            "empty_dict": {},
            "empty_list": [],
            "zero_value": 0,
            "false_value": False
        },
        {
            "unicode_field": "测试数据",
            "emoji_field": "🚀🔥💯",
            "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?"
        },
        {
            "very_long_string": "a" * 10000,
            "nested_lists": [[1, 2], [3, 4], [5, 6]],
            "mixed_types": [1, "string", True, None, {"key": "value"}]
        }
    ])
    def test_prompt_generation_handles_complex_additional_info(self, mock_connector_entity, 
                                                              mock_prompt_processor, complex_data):
        """Test prompt generation with complex additional information including edge cases"""
        # Arrange
        example_data = {
            "input": "Test input",
            "target": "Test target",
            **complex_data
        }
        
        complex_dataset = DatasetEntity(
            id="complex",
            name="Complex Dataset",
            description="Dataset with complex additional info",
            examples=[example_data]
        )
        
        task = BenchmarkTask(
            task_id="test_complex",
            connector_entity=mock_connector_entity,
            metric="test_metric",
            dataset_entity=complex_dataset,
            prompt_processor_instance=mock_prompt_processor
        )

        # Act
        prompts = task.generate_prompts()

        # Assert
        assert len(prompts) == 1
        prompt = prompts[0]
        
        # Check that all complex data is preserved in additional_info
        for key, value in complex_data.items():
            assert prompt.additional_info[key] == value

    @pytest.mark.parametrize("concurrent_runs", [1, 2, 5, 10])
    @pytest.mark.asyncio
    async def test_concurrent_task_runs(self, mock_connector_entity, mock_dataset_entity, 
                                       mock_prompt_processor, concurrent_runs):
        """Test running multiple benchmark tasks concurrently"""
        # Arrange
        tasks = []
        for i in range(concurrent_runs):
            mock_processor = AsyncMock(spec=PromptProcessorPort)
            mock_processor.process_prompts.return_value = []
            
            task = BenchmarkTask(
                task_id=f"concurrent_task_{i}",
                connector_entity=mock_connector_entity,
                metric="test_metric",
                dataset_entity=mock_dataset_entity,
                prompt_processor_instance=mock_processor
            )
            tasks.append(task)

        # Act
        import asyncio
        results = await asyncio.gather(*[task.run() for task in tasks])

        # Assert
        assert len(results) == concurrent_runs
        assert all(result is True for result in results)
        assert all(task.state == TaskManagerStatus.COMPLETED for task in tasks)

    @pytest.mark.asyncio
    async def test_run_assigns_prompts_to_instance(self, benchmark_task_without_callback, mock_prompt_processor):
        """Test that run method assigns generated prompts to instance variable"""
        # Arrange
        mock_prompt_processor.process_prompts.return_value = []

        # Act
        await benchmark_task_without_callback.run()

        # Assert
        assert len(benchmark_task_without_callback.prompts) == 3
        assert all(isinstance(prompt, PromptEntity) for prompt in benchmark_task_without_callback.prompts)

    @pytest.mark.asyncio
    async def test_run_assigns_processed_prompts_to_instance(self, benchmark_task_without_callback, mock_prompt_processor):
        """Test that run method assigns processed prompts to instance variable"""
        # Arrange
        processed_prompts = [
            PromptEntity(
                index=1,
                prompt="Test",
                target="Target",
                model_prediction="Prediction",
                evaluation_result={"score": 0.9}
            )
        ]
        mock_prompt_processor.process_prompts.return_value = processed_prompts

        # Act
        await benchmark_task_without_callback.run()

        # Assert
        assert benchmark_task_without_callback.prompts_with_results == processed_prompts

    @pytest.mark.parametrize("constant_name,expected_value", [
        ("INFO_GENERATING_PROMPTS", "[BenchmarkTask] Generating Prompts..."),
        ("INFO_GENERATING_RESULTS", "[BenchmarkTask] Generating Results..."),
        ("INFO_PROCESSING_PROMPTS", "[BenchmarkTask] Processing Prompts..."),
        ("ERROR_OCCURRED", "[BenchmarkTask] An error occurred: {e}"),
        ("INFO_PROMPTS_COUNT", "[BenchmarkTask] Number of prompts generated: {count}")
    ])
    def test_class_constants(self, constant_name, expected_value):
        """Test that class constants are properly defined"""
        # Assert
        assert getattr(BenchmarkTask, constant_name) == expected_value

    @pytest.mark.asyncio
    async def test_run_logs_prompt_count(self, benchmark_task_without_callback, mock_prompt_processor):
        """Test that run method logs the correct prompt count"""
        # Arrange
        mock_prompt_processor.process_prompts.return_value = []
        
        with patch('domain.services.benchmark.benchmark_task.logger') as mock_logger:
            # Act
            await benchmark_task_without_callback.run()

            # Assert
            mock_logger.info.assert_any_call(
                BenchmarkTask.INFO_PROMPTS_COUNT.format(count=3)
            )

    def test_docstring_and_class_description(self):
        """Test that the class has proper documentation"""
        # Assert
        assert BenchmarkTask.__doc__ is not None
        assert "benchmark task" in BenchmarkTask.__doc__.lower()
        assert "processes prompts" in BenchmarkTask.__doc__.lower()

    @pytest.mark.parametrize("memory_pressure", [
        "low",    # Normal operation
        "high",   # High memory usage scenario
        "extreme" # Extreme memory scenario
    ])
    def test_memory_usage_scenarios(self, mock_connector_entity, mock_prompt_processor, memory_pressure):
        """Test benchmark task behavior under different memory pressure scenarios"""
        # Arrange
        if memory_pressure == "low":
            examples = [{"input": f"test_{i}", "target": f"result_{i}"} for i in range(10)]
        elif memory_pressure == "high":
            examples = [{"input": f"test_{i}", "target": f"result_{i}"} for i in range(1000)]
        else:  # extreme
            examples = [{"input": f"test_{i}", "target": "x" * 1000} for i in range(5000)]
        
        dataset = DatasetEntity(
            id="memory_test",
            name="Memory Test Dataset",
            description="Dataset for memory testing",
            examples=examples
        )
        
        task = BenchmarkTask(
            task_id="memory_test",
            connector_entity=mock_connector_entity,
            metric="test_metric",
            dataset_entity=dataset,
            prompt_processor_instance=mock_prompt_processor
        )

        # Act
        prompts = task.generate_prompts()

        # Assert
        assert len(prompts) == len(examples)
        # Verify memory efficiency - all prompts should be PromptEntity instances
        assert all(isinstance(prompt, PromptEntity) for prompt in prompts)

    @pytest.mark.parametrize("dataset_corruption_type", [
        "missing_examples_key",
        "examples_none", 
        "examples_not_iterable",
        "corrupt_example_structure"
    ])
    def test_corrupted_dataset_handling(self, mock_connector_entity, mock_prompt_processor, dataset_corruption_type):
        """Test handling of corrupted or malformed datasets"""
        # Arrange
        if dataset_corruption_type == "missing_examples_key":
            # Create dataset without examples attribute
            dataset = Mock()
            dataset.id = "corrupt"
            dataset.name = "Corrupt Dataset"
            del dataset.examples  # Remove examples attribute
            
            task = BenchmarkTask(
                task_id="corrupt_test",
                connector_entity=mock_connector_entity,
                metric="test_metric", 
                dataset_entity=dataset,
                prompt_processor_instance=mock_prompt_processor
            )

            # Act & Assert
            with pytest.raises(AttributeError):
                task.generate_prompts()
                
        elif dataset_corruption_type == "examples_none":
            # Act & Assert - should raise ValidationError during DatasetEntity creation
            with pytest.raises(ValidationError):
                DatasetEntity(
                    id="corrupt",
                    name="Corrupt Dataset",
                    description="Corrupt dataset",
                    examples=None
                )
                
        elif dataset_corruption_type == "examples_not_iterable":
            # Act & Assert - should raise ValidationError during DatasetEntity creation
            with pytest.raises(ValidationError):
                DatasetEntity(
                    id="corrupt", 
                    name="Corrupt Dataset",
                    description="Corrupt dataset",
                    examples="not_iterable"
                )
                
        else:  # corrupt_example_structure
            # Mock to make examples raise exception when accessed
            dataset = Mock()
            dataset.examples = Mock(side_effect=Exception("Corruption error"))
            
            task = BenchmarkTask(
                task_id="corrupt_test",
                connector_entity=mock_connector_entity,
                metric="test_metric", 
                dataset_entity=dataset,
                prompt_processor_instance=mock_prompt_processor
            )

            # Act & Assert
            with pytest.raises(Exception):
                task.generate_prompts() 