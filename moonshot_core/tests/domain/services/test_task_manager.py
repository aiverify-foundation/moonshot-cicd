import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.domain.services.task_manager import TaskManager

from domain.services.enums.file_types import FileTypes
from domain.services.enums.module_types import ModuleTypes
from domain.services.enums.test_types import TestTypes
from domain.services.loader.file_loader import FileLoader
from domain.services.loader.module_loader import ModuleLoader

@pytest.mark.asyncio
async def test_run_benchmark():
    # Create a TaskManager instance
    task_manager = TaskManager()

    # Mock the dependencies
    mock_connector_entity = MagicMock()
    mock_dataset_entity = MagicMock()
    mock_prompt_processor_instance = AsyncMock()
    mock_prompt_processor_instance.process_prompts.return_value = ([], {})

    # Mock the methods in TaskManager
    with patch.object(task_manager, '_get_connector_config', return_value=mock_connector_entity), \
         patch.object(task_manager, '_load_module', side_effect=[mock_dataset_entity, (mock_prompt_processor_instance, "processor_id")]), \
         patch.object(task_manager, '_generate_prompts', return_value=[]), \
         patch.object(task_manager, '_serialize_results', return_value='{"mock": "result"}'), \
         patch.object(task_manager, '_store_results_to_local_path', return_value='/mock/path.json'), \
         patch.object(task_manager, '_convert_prompt_entities_to_dicts', return_value={}), \
         patch.object(task_manager, '_format_metadata', return_value={}):

        # Define test parameters
        run_id = "test_run_id"
        test_name = "test_benchmark"
        dataset = "test_dataset"
        metric = {}
        connector = "test_connector"
        prompt_processor = "test_prompt_processor"

        # Call the method
        result = await task_manager.run_benchmark(
            run_id=run_id,
            test_name=test_name,
            dataset=dataset,
            metric=metric,
            connector=connector,
            prompt_processor=prompt_processor,
            callback_fn=None,
            write_result=True
        )

        # Assertions
        assert result == '/mock/path.json'
        task_manager._get_connector_config.assert_called_once_with(connector)
        task_manager._load_module.assert_any_call(FileLoader, dataset, FileTypes.DATASET, task_manager.DATASET_LOADED_MSG, task_manager.ERROR_LOADING_DATASET)
        task_manager._load_module.assert_any_call(ModuleLoader, prompt_processor, ModuleTypes.PROMPT_PROCESSOR, task_manager.PROMPT_PROCESSOR_LOADED_MSG, task_manager.ERROR_LOADING_PROMPT_PROCESSOR)
        task_manager._generate_prompts.assert_called_once_with(mock_dataset_entity)
        mock_prompt_processor_instance.process_prompts.assert_called_once_with([], mock_connector_entity, metric, None)
        task_manager._serialize_results.assert_called_once()
        task_manager._store_results_to_local_path.assert_called_once_with(run_id, '{"mock": "result"}')

@pytest.mark.asyncio
async def test_run_benchmark_connector_config_none():
    """Test run_benchmark when connector config returns None"""
    task_manager = TaskManager()
    
    with patch.object(task_manager, '_get_connector_config', return_value=None):
        result = await task_manager.run_benchmark(
            run_id="test_id",
            test_name="test",
            dataset="dataset",
            metric={},
            connector="invalid_connector",
            prompt_processor="processor"
        )
        
        assert result == ""

@pytest.mark.asyncio
async def test_run_benchmark_dataset_loading_fails():
    """Test run_benchmark when dataset loading fails"""
    task_manager = TaskManager()
    
    mock_connector_entity = MagicMock()
    
    with patch.object(task_manager, '_get_connector_config', return_value=mock_connector_entity), \
         patch.object(task_manager, '_load_module', side_effect=[None, (MagicMock(), "processor_id")]):
        
        result = await task_manager.run_benchmark(
            run_id="test_id",
            test_name="test",
            dataset="invalid_dataset",
            metric={},
            connector="connector",
            prompt_processor="processor"
        )
        
        assert result == ""

@pytest.mark.asyncio
async def test_run_benchmark_prompt_processor_loading_fails():
    """Test run_benchmark when prompt processor loading fails"""
    task_manager = TaskManager()
    
    mock_connector_entity = MagicMock()
    mock_dataset_entity = MagicMock()
    
    with patch.object(task_manager, '_get_connector_config', return_value=mock_connector_entity), \
         patch.object(task_manager, '_load_module', side_effect=[mock_dataset_entity, None]):
        
        result = await task_manager.run_benchmark(
            run_id="test_id",
            test_name="test",
            dataset="dataset",
            metric={},
            connector="connector",
            prompt_processor="invalid_processor"
        )
        
        assert result == ""

@pytest.mark.asyncio
async def test_run_benchmark_serialization_fails():
    """Test run_benchmark when serialization fails"""
    task_manager = TaskManager()
    
    mock_connector_entity = MagicMock()
    mock_dataset_entity = MagicMock()
    mock_prompt_processor_instance = AsyncMock()
    mock_prompt_processor_instance.process_prompts.return_value = ([], {})
    
    with patch.object(task_manager, '_get_connector_config', return_value=mock_connector_entity), \
         patch.object(task_manager, '_load_module', side_effect=[mock_dataset_entity, (mock_prompt_processor_instance, "processor_id")]), \
         patch.object(task_manager, '_generate_prompts', return_value=[]), \
         patch.object(task_manager, '_serialize_results', return_value=None), \
         patch.object(task_manager, '_convert_prompt_entities_to_dicts', return_value={}), \
         patch.object(task_manager, '_format_metadata', return_value={}):
        
        result = await task_manager.run_benchmark(
            run_id="test_id",
            test_name="test",
            dataset="dataset",
            metric={},
            connector="connector",
            prompt_processor="processor"
        )
        
        assert result == ""

@pytest.mark.asyncio
async def test_run_benchmark_write_result_false():
    """Test run_benchmark with write_result=False"""
    task_manager = TaskManager()
    
    mock_connector_entity = MagicMock()
    mock_dataset_entity = MagicMock()
    mock_prompt_processor_instance = AsyncMock()
    mock_prompt_processor_instance.process_prompts.return_value = ([], {})
    
    with patch.object(task_manager, '_get_connector_config', return_value=mock_connector_entity), \
         patch.object(task_manager, '_load_module', side_effect=[mock_dataset_entity, (mock_prompt_processor_instance, "processor_id")]), \
         patch.object(task_manager, '_generate_prompts', return_value=[]), \
         patch.object(task_manager, '_serialize_results', return_value='{"serialized": "result"}'), \
         patch.object(task_manager, '_convert_prompt_entities_to_dicts', return_value={}), \
         patch.object(task_manager, '_format_metadata', return_value={}):
        
        result = await task_manager.run_benchmark(
            run_id="test_id",
            test_name="test",
            dataset="dataset",
            metric={},
            connector="connector",
            prompt_processor="processor",
            write_result=False
        )
        
        assert result == '{"serialized": "result"}'

@pytest.mark.asyncio
async def test_run_benchmark_exception_handling():
    """Test run_benchmark exception handling"""
    task_manager = TaskManager()
    
    with patch.object(task_manager, '_get_connector_config', side_effect=Exception("Test error")):
        
        with pytest.raises(Exception) as exc_info:
            await task_manager.run_benchmark(
                run_id="test_id",
                test_name="test",
                dataset="dataset",
                metric={},
                connector="connector",
                prompt_processor="processor"
            )
        
        assert str(exc_info.value) == "Test error"

@pytest.mark.asyncio
async def test_run_benchmark_with_callback():
    """Test run_benchmark with callback function"""
    task_manager = TaskManager()
    
    mock_connector_entity = MagicMock()
    mock_dataset_entity = MagicMock()
    mock_prompt_processor_instance = AsyncMock()
    mock_prompt_processor_instance.process_prompts.return_value = ([], {})
    
    callback_mock = MagicMock()
    
    with patch.object(task_manager, '_get_connector_config', return_value=mock_connector_entity), \
         patch.object(task_manager, '_load_module', side_effect=[mock_dataset_entity, (mock_prompt_processor_instance, "processor_id")]), \
         patch.object(task_manager, '_generate_prompts', return_value=[]), \
         patch.object(task_manager, '_serialize_results', return_value='{"mock": "result"}'), \
         patch.object(task_manager, '_store_results_to_local_path', return_value='/mock/path.json'), \
         patch.object(task_manager, '_convert_prompt_entities_to_dicts', return_value={}), \
         patch.object(task_manager, '_format_metadata', return_value={}):
        
        result = await task_manager.run_benchmark(
            run_id="test_id",
            test_name="test",
            dataset="dataset",
            metric={},
            connector="connector",
            prompt_processor="processor",
            callback_fn=callback_mock
        )
        
        # Verify callback was called at different stages
        assert callback_mock.call_count == 4
        callback_mock.assert_any_call(stage=0, message="Loading modules")
        callback_mock.assert_any_call(stage=1, message="Running benchmark")
        callback_mock.assert_any_call(stage=2, message="Formatting results")
        callback_mock.assert_any_call(stage=3, message="Writing results")

@pytest.mark.asyncio
async def test_run_scan():
    # Create a TaskManager instance
    task_manager = TaskManager()

    # Mock the dependencies
    mock_connector_entity = MagicMock()
    mock_attack_module_instance = AsyncMock()
    mock_attack_module_instance.execute.return_value = ([], {})
    mock_attack_module_instance.configure = MagicMock()
    mock_attack_module_instance.update_params = MagicMock()

    # Mock the methods in TaskManager
    with patch.object(task_manager, '_get_connector_config', return_value=mock_connector_entity), \
         patch.object(task_manager, '_load_module', return_value=(mock_attack_module_instance, "am_id")), \
         patch.object(task_manager, '_convert_prompt_entities_to_dicts', return_value={}), \
         patch.object(task_manager, '_serialize_results', return_value='{"mock": "result"}'), \
         patch.object(task_manager, '_store_results_to_local_path', return_value='/mock/path.json'):

        # Define test parameters
        run_id = "test_run_id"
        test_name = "test_scan"
        attack_module = {"name": "test_attack_module", "params": {}}
        metric = {}
        connector = "test_connector"

        # Call the method
        result = await task_manager.run_scan(
            run_id=run_id,
            test_name=test_name,
            attack_module=attack_module,
            metric=metric,
            connector=connector,
            dataset="",
            prompt="",
            prompt_processor="asyncio_prompt_processor_adapter",
            callback_fn=None,
            write_result=True
        )

        # Assertions
        assert result == '/mock/path.json'
        task_manager._get_connector_config.assert_called_once_with(connector)
        task_manager._load_module.assert_called_once_with(
            ModuleLoader,
            attack_module["name"],
            ModuleTypes.ATTACK_MODULE,
            task_manager.ATTACK_MODULE_LOADED_MSG,
            task_manager.ERROR_LOADING_ATTACK_MODULE
        )
        mock_attack_module_instance.execute.assert_called_once()
        task_manager._serialize_results.assert_called_once()
        task_manager._store_results_to_local_path.assert_called_once_with(run_id, '{"mock": "result"}')

@pytest.mark.asyncio
async def test_run_scan_connector_config_none():
    """Test run_scan when connector config returns None"""
    task_manager = TaskManager()
    mock_attack_module_instance = AsyncMock()
    mock_attack_module_instance.configure = MagicMock()
    mock_attack_module_instance.update_params = MagicMock()
    mock_attack_module_instance.execute.return_value = ([], {})
    
    with patch.object(task_manager, '_get_connector_config', return_value=None), \
         patch.object(task_manager, '_load_module', return_value=(mock_attack_module_instance, "am_id")):
        result = await task_manager.run_scan(
            run_id="test_id",
            test_name="test",
            attack_module={"name": "attack", "params": {}},
            metric={},
            connector="invalid_connector",
            dataset="dataset",
            prompt="prompt",
            prompt_processor="processor"
        )
        assert result == ""

@pytest.mark.asyncio
async def test_run_scan_attack_module_loading_fails():
    """Test run_scan when attack module loading fails"""
    task_manager = TaskManager()
    mock_connector_entity = MagicMock()
    with patch.object(task_manager, '_get_connector_config', return_value=mock_connector_entity), \
         patch.object(task_manager, '_load_module', side_effect=Exception("Load module failed")):
        with pytest.raises(Exception) as exc_info:
            await task_manager.run_scan(
                run_id="test_id",
                test_name="test",
                attack_module={"name": "attack", "params": {}},
                metric={},
                connector="connector",
                dataset="dataset",
                prompt="prompt",
                prompt_processor="processor"
            )
        assert str(exc_info.value) == "Load module failed"

@pytest.mark.asyncio
async def test_run_scan_serialization_fails():
    """Test run_scan when serialization fails"""
    task_manager = TaskManager()
    mock_connector_entity = MagicMock()
    mock_attack_module_instance = AsyncMock()
    mock_attack_module_instance.execute.return_value = ([], {})
    with patch.object(task_manager, '_get_connector_config', return_value=mock_connector_entity), \
         patch.object(task_manager, '_load_module', return_value=(mock_attack_module_instance, "am_id")), \
         patch.object(task_manager, '_convert_prompt_entities_to_dicts', return_value={}), \
         patch.object(task_manager, '_serialize_results', return_value=None):
        result = await task_manager.run_scan(
            run_id="test_id",
            test_name="test",
            attack_module={"name": "attack", "params": {}},
            metric={},
            connector="connector",
            dataset="dataset",
            prompt="prompt",
            prompt_processor="processor"
        )
        assert result == ""

@pytest.mark.asyncio
async def test_run_scan_write_result_false():
    """Test run_scan with write_result=False"""
    task_manager = TaskManager()
    mock_connector_entity = MagicMock()
    mock_attack_module_instance = AsyncMock()
    mock_attack_module_instance.execute.return_value = ([], {})
    with patch.object(task_manager, '_get_connector_config', return_value=mock_connector_entity), \
         patch.object(task_manager, '_load_module', return_value=(mock_attack_module_instance, "am_id")), \
         patch.object(task_manager, '_convert_prompt_entities_to_dicts', return_value={}), \
         patch.object(task_manager, '_serialize_results', return_value='{"serialized": "result"}'):
        result = await task_manager.run_scan(
            run_id="test_id",
            test_name="test",
            attack_module={"name": "attack", "params": {}},
            metric={},
            connector="connector",
            dataset="dataset",
            prompt="prompt",
            prompt_processor="processor",
            write_result=False
        )
        assert result == '{"serialized": "result"}'

@pytest.mark.asyncio
async def test_run_scan_exception_handling():
    """Test run_scan exception handling"""
    task_manager = TaskManager()
    mock_attack_module_instance = AsyncMock()
    mock_attack_module_instance.configure = MagicMock()
    mock_attack_module_instance.update_params = MagicMock()
    mock_attack_module_instance.execute.return_value = ([], {})
    
    with patch.object(task_manager, '_get_connector_config', side_effect=Exception("Test error")), \
         patch.object(task_manager, '_load_module', return_value=(mock_attack_module_instance, "am_id")):
        with pytest.raises(Exception) as exc_info:
            await task_manager.run_scan(
                run_id="test_id",
                test_name="test",
                attack_module={"name": "attack", "params": {}},
                metric={},
                connector="connector",
                dataset="dataset",
                prompt="prompt",
                prompt_processor="processor"
            )
        assert str(exc_info.value) == "Test error"

@pytest.mark.asyncio
async def test_run_scan_with_callback():
    """Test run_scan with callback function"""
    task_manager = TaskManager()
    mock_connector_entity = MagicMock()
    mock_attack_module_instance = AsyncMock()
    mock_attack_module_instance.execute.return_value = ([], {})
    callback_mock = MagicMock()
    with patch.object(task_manager, '_get_connector_config', return_value=mock_connector_entity), \
         patch.object(task_manager, '_load_module', return_value=(mock_attack_module_instance, "am_id")), \
         patch.object(task_manager, '_convert_prompt_entities_to_dicts', return_value={}), \
         patch.object(task_manager, '_serialize_results', return_value='{"mock": "result"}'), \
         patch.object(task_manager, '_store_results_to_local_path', return_value='/mock/path.json'):
        result = await task_manager.run_scan(
            run_id="test_id",
            test_name="test",
            attack_module={"name": "attack", "params": {}},
            metric={},
            connector="connector",
            dataset="dataset",
            prompt="prompt",
            prompt_processor="processor",
            callback_fn=callback_mock
        )
        # Verify callback was called at different stages
        assert callback_mock.call_count == 4
        callback_mock.assert_any_call(stage=0, message="Loading modules")
        callback_mock.assert_any_call(stage=1, message="Performing scan")
        callback_mock.assert_any_call(stage=2, message="Formatting results")
        callback_mock.assert_any_call(stage=3, message="Writing results")

@pytest.mark.asyncio
async def test_run_test():
    # Create a TaskManager instance
    task_manager = TaskManager()

    # Mock the dependencies
    mock_test_config_inst = MagicMock()
    mock_benchmark_test = MagicMock(type=TestTypes.BENCHMARK, name="benchmark_test", dataset="dataset", metric={}, prompt=None, attack_module=None)
    mock_scan_test = MagicMock(type=TestTypes.SCAN, name="scan_test", dataset="dataset", metric={}, prompt="prompt", attack_module={"name": "attack_module", "params": {}})
    mock_test_config_inst.get.return_value = [mock_benchmark_test, mock_scan_test]
    mock_benchmark_result = '{"benchmark": "result"}'
    mock_scan_result = '{"scan": "result"}'

    # Mock the methods in TaskManager
    with patch.object(task_manager, '_load_module', return_value=mock_test_config_inst), \
         patch.object(task_manager, 'run_benchmark', return_value=mock_benchmark_result), \
         patch.object(task_manager, 'run_scan', return_value=mock_scan_result), \
         patch.object(task_manager, '_store_results_to_local_path', return_value='/mock/path.json'):

        # Define test parameters
        run_id = "test_run_id"
        test_config_id = "test_config_id"
        connector_configuration = "test_connector"

        # Call the method
        result = await task_manager.run_test(
            run_id=run_id,
            test_config_id=test_config_id,
            connector_configuration=connector_configuration,
            prompt_processor="asyncio_prompt_processor_adapter",
            callback_fn=None,
            write_result=True
        )

        # Assertions
        assert result == '/mock/path.json'
        task_manager.run_benchmark.assert_called_once()
        task_manager.run_scan.assert_called_once()

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "run_id, test_name, attack_module, metric, connector, dataset, prompt, prompt_processor, expected_result, connector_config, load_module_result, execute_result, convert_result, serialize_result, store_result, load_module_exception",
    [
        # Good case 1
        (
            "run1", "scan1", {"name": "attack1", "params": {}}, {"name": "metric1"}, "connector1", "dataset1", "prompt1", "processor1",
            "/mock/path1.json",
            MagicMock(),  # connector_config
            (AsyncMock(), "am_id1"),  # load_module_result
            ([], {}),  # execute_result
            {},  # convert_result
            '{"mock": "result"}',  # serialize_result
            "/mock/path1.json",  # store_result
            None  # load_module_exception
        ),
        # Good case 2
        (
            "run2", "scan2", {"name": "attack2", "params": {}}, {"name": "metric2"}, "connector2", "dataset2", "prompt2", "processor2",
            "/mock/path2.json",
            MagicMock(),
            (AsyncMock(), "am_id2"),
            ([], {}),
            {},
            '{"mock": "result"}',
            "/mock/path2.json",
            None
        ),
        # Bad case 1: connector config is None
        (
            "run3", "scan3", {"name": "attack3", "params": {}}, {"name": "metric3"}, "bad_connector", "dataset3", "prompt3", "processor3",
            "",
            None,  # connector_config
            (AsyncMock(), "am_id3"),
            ([], {}),
            {},
            '{"mock": "result"}',
            "/mock/path3.json",
            None
        ),
        # Bad case 2: _load_module raises Exception
        (
            "run4", "scan4", {"name": "attack4", "params": {}}, {"name": "metric4"}, "connector4", "dataset4", "prompt4", "processor4",
            "",
            MagicMock(),
            None,  # load_module_result
            ([], {}),
            {},
            '{"mock": "result"}',
            "/mock/path4.json",
            Exception("Load module failed")
        ),
    ]
)
async def test_run_scan_input(
    run_id, test_name, attack_module, metric, connector, dataset, prompt, prompt_processor,
    expected_result, connector_config, load_module_result, execute_result, convert_result, serialize_result, store_result, load_module_exception
):
    task_manager = TaskManager()

    am_inst = AsyncMock()
    am_inst.execute.return_value = execute_result
    am_inst.configure = MagicMock()
    am_inst.update_params = MagicMock()
    load_module_side_effect = None
    if load_module_exception:
        load_module_side_effect = load_module_exception
    elif load_module_result:
        load_module_side_effect = lambda *args, **kwargs: (am_inst, "am_id")

    with patch.object(task_manager, '_get_connector_config', return_value=connector_config), \
         patch.object(task_manager, '_load_module', side_effect=load_module_side_effect if load_module_side_effect else lambda *a, **k: (am_inst, "am_id")), \
         patch.object(task_manager, '_convert_prompt_entities_to_dicts', return_value=convert_result), \
         patch.object(task_manager, '_serialize_results', return_value=serialize_result), \
         patch.object(task_manager, '_store_results_to_local_path', return_value=store_result):
        if load_module_exception:
            with pytest.raises(Exception):
                await task_manager.run_scan(
                    run_id=run_id,
                    test_name=test_name,
                    attack_module=attack_module,
                    metric=metric,
                    connector=connector,
                    dataset=dataset,
                    prompt=prompt,
                    prompt_processor=prompt_processor,
                    callback_fn=None,
                    write_result=True
                )
        else:
            result = await task_manager.run_scan(
                run_id=run_id,
                test_name=test_name,
                attack_module=attack_module,
                metric=metric,
                connector=connector,
                dataset=dataset,
                prompt=prompt,
                prompt_processor=prompt_processor,
                callback_fn=None,
                write_result=True
            )
            assert result == expected_result

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "run_id, test_name, dataset, metric, connector, prompt_processor, callback_fn, write_result, expected_result, connector_config, dataset_entity, prompt_processor_instance, prompts, process_prompts_result, serialize_result, store_result, load_module_side_effect, serialize_none, exception_in_connector_config",
    [
        # Good case 1
        (
            "run1", "benchmark1", "dataset1", {"name": "metric1"}, "connector1", "processor1", None, True,
            "/mock/path1.json",
            MagicMock(),  # connector_config
            MagicMock(),  # dataset_entity
            AsyncMock(),  # prompt_processor_instance
            ["prompt1", "prompt2"],  # prompts
            ([], {}),  # process_prompts_result
            '{"mock": "result"}',  # serialize_result
            "/mock/path1.json",  # store_result
            None,  # load_module_side_effect
            False,  # serialize_none
            False   # exception_in_connector_config
        ),
        # Good case 2
        (
            "run2", "benchmark2", "dataset2", {"name": "metric2"}, "connector2", "processor2", None, True,
            "/mock/path2.json",
            MagicMock(),
            MagicMock(),
            AsyncMock(),
            ["promptA"],
            ([], {}),
            '{"mock": "result"}',
            "/mock/path2.json",
            None,
            False,
            False
        ),
        # Bad case 1: connector config is None
        (
            "run3", "benchmark3", "dataset3", {"name": "metric3"}, "bad_connector", "processor3", None, True,
            "",
            None,  # connector_config
            MagicMock(),
            AsyncMock(),
            [],
            ([], {}),
            '{"mock": "result"}',
            "/mock/path3.json",
            None,
            False,
            False
        ),
        # Bad case 2: dataset loading fails
        (
            "run4", "benchmark4", "bad_dataset", {"name": "metric4"}, "connector4", "processor4", None, True,
            "",
            MagicMock(),
            None,  # dataset_entity
            AsyncMock(),
            [],
            ([], {}),
            '{"mock": "result"}',
            "/mock/path4.json",
            None,
            False,
            False
        ),
        # Bad case 3: serialization fails
        (
            "run5", "benchmark5", "dataset5", {"name": "metric5"}, "connector5", "processor5", None, True,
            "",
            MagicMock(),
            MagicMock(),
            AsyncMock(),
            ["promptX"],
            ([], {}),
            None,  # serialize_result
            "/mock/path5.json",
            None,
            True,
            False
        ),
        # Bad case 4: exception in connector config
        (
            "run6", "benchmark6", "dataset6", {"name": "metric6"}, "connector6", "processor6", None, True,
            None,
            Exception("Test error"),
            MagicMock(),
            AsyncMock(),
            [],
            ([], {}),
            '{"mock": "result"}',
            "/mock/path6.json",
            None,
            False,
            True
        ),
        # Good case 3: write_result=False
        (
            "run7", "benchmark7", "dataset7", {"name": "metric7"}, "connector7", "processor7", None, False,
            '{"mock": "result"}',
            MagicMock(),
            MagicMock(),
            AsyncMock(),
            ["promptY"],
            ([], {}),
            '{"mock": "result"}',
            "/mock/path7.json",
            None,
            False,
            False
        ),
    ]
)
async def test_run_benchmark_input(
    run_id, test_name, dataset, metric, connector, prompt_processor, callback_fn, write_result, expected_result,
    connector_config, dataset_entity, prompt_processor_instance, prompts, process_prompts_result, serialize_result, store_result,
    load_module_side_effect, serialize_none, exception_in_connector_config
):
    task_manager = TaskManager()
    # Setup mocks
    if isinstance(connector_config, Exception):
        get_connector_config_patch = patch.object(task_manager, '_get_connector_config', side_effect=connector_config)
    else:
        get_connector_config_patch = patch.object(task_manager, '_get_connector_config', return_value=connector_config)
    # _load_module side effect
    if dataset_entity is not None and prompt_processor_instance is not None:
        load_module_patch = patch.object(task_manager, '_load_module', side_effect=[dataset_entity, (prompt_processor_instance, "processor_id")])
    elif dataset_entity is None:
        load_module_patch = patch.object(task_manager, '_load_module', side_effect=[None, (prompt_processor_instance, "processor_id")])
    elif prompt_processor_instance is None:
        load_module_patch = patch.object(task_manager, '_load_module', side_effect=[dataset_entity, None])
    else:
        load_module_patch = patch.object(task_manager, '_load_module', side_effect=[dataset_entity, (prompt_processor_instance, "processor_id")])
    with get_connector_config_patch, \
         load_module_patch, \
         patch.object(task_manager, '_generate_prompts', return_value=prompts), \
         patch.object(task_manager, '_serialize_results', return_value=serialize_result), \
         patch.object(task_manager, '_store_results_to_local_path', return_value=store_result), \
         patch.object(task_manager, '_convert_prompt_entities_to_dicts', return_value={}), \
         patch.object(task_manager, '_format_metadata', return_value={}), \
         patch.object(prompt_processor_instance, 'process_prompts', return_value=process_prompts_result):
        if exception_in_connector_config:
            with pytest.raises(Exception):
                await task_manager.run_benchmark(
                    run_id=run_id,
                    test_name=test_name,
                    dataset=dataset,
                    metric=metric,
                    connector=connector,
                    prompt_processor=prompt_processor,
                    callback_fn=callback_fn,
                    write_result=write_result
                )
        else:
            result = await task_manager.run_benchmark(
                run_id=run_id,
                test_name=test_name,
                dataset=dataset,
                metric=metric,
                connector=connector,
                prompt_processor=prompt_processor,
                callback_fn=callback_fn,
                write_result=write_result
            )
            assert result == expected_result

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "run_id, test_config_id, connector_configuration, expected_result, test_config_inst, get_return, benchmark_result, scan_result, store_result, raises_value_error",
    [
        # Good case 1: two tests (benchmark and scan)
        (
            "run1", "config1", "connector1", "/mock/path1.json",
            MagicMock(),  # test_config_inst
            [
                MagicMock(type=TestTypes.BENCHMARK, name="bench1", dataset="ds1", metric={}, prompt=None, attack_module=None),
                MagicMock(type=TestTypes.SCAN, name="scan1", dataset="ds2", metric={}, prompt="prompt", attack_module={"name": "am", "params": {}})
            ],
            '{"benchmark": "result"}', '{"scan": "result"}', "/mock/path1.json", False
        ),
        # Good case 2: one test (benchmark)
        (
            "run2", "config2", "connector2", "/mock/path2.json",
            MagicMock(),
            [
                MagicMock(type=TestTypes.BENCHMARK, name="bench2", dataset="ds3", metric={}, prompt=None, attack_module=None)
            ],
            '{"benchmark": "result"}', '{"scan": "result"}', "/mock/path2.json", False
        ),
        # Bad case 1: test_config_inst is None
        (
            "run3", "config3", "connector3", "",
            None,  # test_config_inst
            None, '{"benchmark": "result"}', '{"scan": "result"}', "/mock/path3.json", False
        ),
        # Bad case 2: get returns None (invalid test_config_id)
        (
            "run4", "config4", "connector4", None,
            MagicMock(),
            None, '{"benchmark": "result"}', '{"scan": "result"}', "/mock/path4.json", True
        ),
    ]
)
async def test_run_test_input(
    run_id, test_config_id, connector_configuration, expected_result, test_config_inst, get_return, benchmark_result, scan_result, store_result, raises_value_error
):
    task_manager = TaskManager()

    if test_config_inst is not None:
        test_config_inst.get.return_value = get_return
    with patch.object(task_manager, '_load_module', return_value=test_config_inst), \
         patch.object(task_manager, 'run_benchmark', return_value=benchmark_result), \
         patch.object(task_manager, 'run_scan', return_value=scan_result), \
         patch.object(task_manager, '_store_results_to_local_path', return_value=store_result):
        if test_config_inst is None:
            result = await task_manager.run_test(
                run_id=run_id,
                test_config_id=test_config_id,
                connector_configuration=connector_configuration,
                prompt_processor="asyncio_prompt_processor_adapter",
                callback_fn=None,
                write_result=True
            )
            assert result == ""
        elif raises_value_error:
            with pytest.raises(ValueError):
                await task_manager.run_test(
                    run_id=run_id,
                    test_config_id=test_config_id,
                    connector_configuration=connector_configuration,
                    prompt_processor="asyncio_prompt_processor_adapter",
                    callback_fn=None,
                    write_result=True
                )
        else:
            result = await task_manager.run_test(
                run_id=run_id,
                test_config_id=test_config_id,
                connector_configuration=connector_configuration,
                prompt_processor="asyncio_prompt_processor_adapter",
                callback_fn=None,
                write_result=True
            )
            assert result == expected_result
