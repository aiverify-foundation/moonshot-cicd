import pytest
from pydantic import ValidationError

from src.domain.entities.prompt_entity import PromptEntity
from domain.services.enums.task_manager_status import TaskManagerStatus


class TestPromptEntity:
    """Test class for PromptEntity"""

    def test_minimal_initialization(self):
        """Test PromptEntity with minimal required parameters"""
        # Arrange
        index = 0
        prompt = "What is artificial intelligence?"
        target = "AI is a field of computer science"

        # Act
        entity = PromptEntity(
            index=index,
            prompt=prompt,
            target=target
        )

        # Assert
        assert entity.index == index
        assert entity.prompt == prompt
        assert entity.target == target
        assert entity.model_prediction is None  # Default value
        assert entity.reference_context == ""  # Default value
        assert entity.evaluation_result is None  # Default value
        assert entity.additional_info == {}  # Default value
        assert entity.state == TaskManagerStatus.PENDING  # Default value

    def test_full_initialization(self):
        """Test PromptEntity with all parameters provided"""
        # Arrange
        index = 42
        prompt = "Explain machine learning algorithms"
        target = "Comprehensive explanation of ML algorithms"
        model_prediction = "Machine learning algorithms are computational methods..."
        reference_context = "Reference context for ML evaluation"
        evaluation_result = {"accuracy": 0.92, "relevance": 0.88}
        additional_info = {"category": "ML", "difficulty": "intermediate", "tags": ["algorithms", "learning"]}
        state = TaskManagerStatus.COMPLETED

        # Act
        entity = PromptEntity(
            index=index,
            prompt=prompt,
            target=target,
            model_prediction=model_prediction,
            reference_context=reference_context,
            evaluation_result=evaluation_result,
            additional_info=additional_info,
            state=state
        )

        # Assert
        assert entity.index == index
        assert entity.prompt == prompt
        assert entity.target == target
        assert entity.model_prediction == model_prediction
        assert entity.reference_context == reference_context
        assert entity.evaluation_result == evaluation_result
        assert entity.additional_info == additional_info
        assert entity.state == state

    @pytest.mark.parametrize("index", [
        # Good cases - various valid index types
        0,  # Zero index
        1,  # Positive integer
        -1,  # Negative integer
        100,  # Large integer
        999999,  # Very large integer
        123.456,  # Float
        "0",  # String index
        "prompt_1",  # String identifier
        "batch_A_item_5",  # Complex string identifier
        None,  # None value
        True,  # Boolean
        False,  # Boolean
        [0, 1, 2],  # List as index
        {"batch": "A", "item": 5},  # Dict as index
        {"nested": {"index": {"value": 42}}},  # Complex nested structure
    ])
    def test_valid_index_variations(self, index):
        """Test PromptEntity with various valid index types"""
        # Act
        entity = PromptEntity(
            index=index,
            prompt="Test prompt",
            target="Test target"
        )

        # Assert
        assert entity.index == index

    @pytest.mark.parametrize("prompt", [
        # Good cases - various valid prompt types
        "Simple string prompt",
        "",  # Empty string
        "Multi-line\nprompt\nwith\nbreaks",
        "Prompt with special chars: !@#$%^&*()",
        "Unicode prompt: 你好世界",
        "Very long prompt " * 100,  # Long prompt
        123,  # Integer
        123.456,  # Float
        True,  # Boolean
        False,  # Boolean
        ["List", "of", "prompts"],  # List
        {"prompt": "dict prompt", "type": "question"},  # Dict
        None,  # None value
        {"complex": {"nested": {"prompt": "test"}}},  # Complex nested structure
        {"instruction": "Analyze the following", "context": "AI research", "question": "What are the benefits?"},
    ])
    def test_valid_prompt_variations(self, prompt):
        """Test PromptEntity with various valid prompt types"""
        # Act
        entity = PromptEntity(
            index=0,
            prompt=prompt,
            target="Test target"
        )

        # Assert
        assert entity.prompt == prompt

    @pytest.mark.parametrize("target", [
        # Good cases - various valid target types
        "Simple string target",
        "",  # Empty string
        "Multi-line\ntarget\nwith\nbreaks",
        "Target with special chars: !@#$%^&*()",
        "Unicode target: こんにちは",
        123,  # Integer
        123.456,  # Float
        True,  # Boolean
        False,  # Boolean
        ["Expected", "answers", "list"],  # List
        {"expected": "answer", "score": 1.0},  # Dict
        None,  # None value
        {"complex": {"nested": {"target": "value"}}},  # Complex nested structure
        [{"answer": "A"}, {"answer": "B"}],  # List of dicts
        {"ground_truth": "Correct answer", "alternatives": ["Alt 1", "Alt 2"]},
    ])
    def test_valid_target_variations(self, target):
        """Test PromptEntity with various valid target types"""
        # Act
        entity = PromptEntity(
            index=0,
            prompt="Test prompt",
            target=target
        )

        # Assert
        assert entity.target == target

    @pytest.mark.parametrize("model_prediction", [
        # Good cases - various valid model_prediction types
        None,  # Default value
        "Simple prediction string",
        "",  # Empty string
        "Multi-line\nprediction\nwith\ndetails",
        "Prediction with special chars: !@#$%^&*()",
        "Unicode prediction: 予測結果",
        123,  # Integer prediction
        123.456,  # Float prediction
        True,  # Boolean prediction
        False,  # Boolean prediction
        ["Multiple", "prediction", "options"],  # List prediction
        {"prediction": "text", "confidence": 0.95},  # Dict prediction
        {"detailed": {"prediction": "result", "metadata": {"model": "gpt-4"}}},  # Complex nested
        {"text": "Generated text", "embeddings": [0.1, 0.2, 0.3], "tokens": 150},
    ])
    def test_valid_model_prediction_variations(self, model_prediction):
        """Test PromptEntity with various valid model_prediction types"""
        # Act
        entity = PromptEntity(
            index=0,
            prompt="Test prompt",
            target="Test target",
            model_prediction=model_prediction
        )

        # Assert
        assert entity.model_prediction == model_prediction

    @pytest.mark.parametrize("reference_context", [
        # Good cases - various valid reference_context strings
        "",  # Empty string (default)
        "Simple reference context",
        "Multi-line\nreference\ncontext",
        "Reference with special chars: !@#$%^&*()",
        "Unicode reference: 参考文脈",
        "Very long reference context " * 100,
        "JSON-like: {\"reference\": \"context\", \"type\": \"evaluation\"}",
        "Template: Please evaluate based on the following criteria:\n1. Accuracy\n2. Relevance\n3. Completeness",
        "Context with citations: According to Smith et al. (2023), AI systems...",
        "Multi-paragraph context:\n\nParagraph 1: Introduction to the topic.\n\nParagraph 2: Detailed analysis.",
    ])
    def test_valid_reference_context_variations(self, reference_context):
        """Test PromptEntity with various valid reference_context strings"""
        # Act
        entity = PromptEntity(
            index=0,
            prompt="Test prompt",
            target="Test target",
            reference_context=reference_context
        )

        # Assert
        assert entity.reference_context == reference_context

    @pytest.mark.parametrize("reference_context,expected_error", [
        # Bad cases - invalid reference_context types
        (123, "Input should be a valid string"),
        ([], "Input should be a valid string"),
        ({}, "Input should be a valid string"),
        (True, "Input should be a valid string"),
        (None, "Input should be a valid string"),
        (3.14, "Input should be a valid string"),
    ])
    def test_invalid_reference_context_types(self, reference_context, expected_error):
        """Test PromptEntity with invalid reference_context types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PromptEntity(
                index=0,
                prompt="Test prompt",
                target="Test target",
                reference_context=reference_context
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("evaluation_result", [
        # Good cases - various valid evaluation_result types
        None,  # Default value
        {"score": 0.85},
        {"score": 0.95, "feedback": "Excellent response"},
        {"accuracy": 0.8, "relevance": 0.9, "coherence": 0.85},
        {"detailed": {"scores": [0.8, 0.9, 0.7], "comments": ["Good", "Better", "Average"]}},
        "String evaluation result",
        123,  # Numeric result
        123.456,  # Float result
        True,  # Boolean result
        False,  # Boolean result
        ["evaluation", "results", "list"],  # List result
        {"complex": {"nested": {"evaluation": {"final_score": 0.88}}}},  # Complex nested
        {"metrics": {"bleu": 0.82, "rouge": 0.76}, "human_eval": {"clarity": 9, "accuracy": 8}},
    ])
    def test_valid_evaluation_result_variations(self, evaluation_result):
        """Test PromptEntity with various valid evaluation_result types"""
        # Act
        entity = PromptEntity(
            index=0,
            prompt="Test prompt",
            target="Test target",
            evaluation_result=evaluation_result
        )

        # Assert
        assert entity.evaluation_result == evaluation_result

    @pytest.mark.parametrize("additional_info", [
        # Good cases - various valid additional_info dictionaries
        {},  # Empty dict (default)
        {"category": "test"},
        {"type": "question", "difficulty": "easy"},
        {"metadata": {"source": "dataset.json", "line": 42}},
        {"tags": ["AI", "ML", "NLP"], "priority": 1},
        {"nested": {"config": {"value": 42}}},
        {"mixed_types": {"string": "test", "number": 123, "boolean": True, "list": [1, 2, 3]}},
        {"large_config": {f"param_{i}": i for i in range(50)}},
        {"unicode_info": {"名前": "テスト", "説明": "パラメータ"}},
        {"complex": {"experiment": {"id": "exp_001", "variants": ["A", "B"], "metrics": {"accuracy": 0.95}}}},
    ])
    def test_valid_additional_info_variations(self, additional_info):
        """Test PromptEntity with various valid additional_info dictionaries"""
        # Act
        entity = PromptEntity(
            index=0,
            prompt="Test prompt",
            target="Test target",
            additional_info=additional_info
        )

        # Assert
        assert entity.additional_info == additional_info

    @pytest.mark.parametrize("additional_info,expected_error", [
        # Bad cases - invalid additional_info types
        ("string", "Input should be a valid dictionary"),
        (123, "Input should be a valid dictionary"),
        ([], "Input should be a valid dictionary"),
        (True, "Input should be a valid dictionary"),
        (None, "Input should be a valid dictionary"),
    ])
    def test_invalid_additional_info_types(self, additional_info, expected_error):
        """Test PromptEntity with invalid additional_info types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PromptEntity(
                index=0,
                prompt="Test prompt",
                target="Test target",
                additional_info=additional_info
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("state", [
        # Good cases - various valid TaskManagerStatus values
        TaskManagerStatus.PENDING,
        TaskManagerStatus.RUNNING,
        TaskManagerStatus.COMPLETED,
        TaskManagerStatus.ERROR,
        TaskManagerStatus.COMPLETED_WITH_ERRORS,
    ])
    def test_valid_state_variations(self, state):
        """Test PromptEntity with various valid TaskManagerStatus values"""
        # Act
        entity = PromptEntity(
            index=0,
            prompt="Test prompt",
            target="Test target",
            state=state
        )

        # Assert
        assert entity.state == state

    @pytest.mark.parametrize("state,expected_error", [
        # Bad cases - invalid state types (removed valid enum string values)
        ("invalid_status", "Input should be 'pending', 'running', 'error', 'completed' or 'completed_with_errors'"),
        (123, "Input should be 'pending', 'running', 'error', 'completed' or 'completed_with_errors'"),
        ([], "Input should be 'pending', 'running', 'error', 'completed' or 'completed_with_errors'"),
        ({}, "Input should be 'pending', 'running', 'error', 'completed' or 'completed_with_errors'"),
        (True, "Input should be 'pending', 'running', 'error', 'completed' or 'completed_with_errors'"),
        (None, "Input should be 'pending', 'running', 'error', 'completed' or 'completed_with_errors'"),
    ])
    def test_invalid_state_types(self, state, expected_error):
        """Test PromptEntity with invalid state types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PromptEntity(
                index=0,
                prompt="Test prompt",
                target="Test target",
                state=state
            )
        assert expected_error in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test PromptEntity with missing required fields"""
        # Test missing index
        with pytest.raises(ValidationError) as exc_info:
            PromptEntity(
                prompt="Test prompt",
                target="Test target"
            )
        assert "Field required" in str(exc_info.value)

        # Test missing prompt
        with pytest.raises(ValidationError) as exc_info:
            PromptEntity(
                index=0,
                target="Test target"
            )
        assert "Field required" in str(exc_info.value)

        # Test missing target
        with pytest.raises(ValidationError) as exc_info:
            PromptEntity(
                index=0,
                prompt="Test prompt"
            )
        assert "Field required" in str(exc_info.value)

    def test_entity_serialization(self):
        """Test PromptEntity serialization to dictionary"""
        # Arrange
        index = 5
        prompt = "Serialization test prompt"
        target = "Serialization test target"
        model_prediction = "Serialization test prediction"
        reference_context = "Serialization reference context"
        evaluation_result = {"score": 0.9, "feedback": "Excellent"}
        additional_info = {"test": "serialization", "category": "unit_test"}
        state = TaskManagerStatus.COMPLETED

        entity = PromptEntity(
            index=index,
            prompt=prompt,
            target=target,
            model_prediction=model_prediction,
            reference_context=reference_context,
            evaluation_result=evaluation_result,
            additional_info=additional_info,
            state=state
        )

        # Act
        entity_dict = entity.model_dump()

        # Assert
        expected_keys = ["index", "prompt", "target", "model_prediction", "reference_context", 
                        "evaluation_result", "additional_info", "state"]
        assert all(key in entity_dict for key in expected_keys)
        assert entity_dict["index"] == index
        assert entity_dict["prompt"] == prompt
        assert entity_dict["target"] == target
        assert entity_dict["model_prediction"] == model_prediction
        assert entity_dict["reference_context"] == reference_context
        assert entity_dict["evaluation_result"] == evaluation_result
        assert entity_dict["additional_info"] == additional_info
        assert entity_dict["state"] == state  # Enum instance, not value

    def test_entity_json_serialization(self):
        """Test PromptEntity JSON serialization"""
        # Arrange
        entity = PromptEntity(
            index=10,
            prompt="JSON test prompt",
            target="JSON test target",
            model_prediction="JSON test prediction",
            evaluation_result={"json_score": 0.85},
            additional_info={"json_test": True},
            state=TaskManagerStatus.RUNNING
        )

        # Act
        json_str = entity.model_dump_json()

        # Assert
        assert isinstance(json_str, str)
        assert "JSON test prompt" in json_str
        assert "JSON test target" in json_str
        assert "JSON test prediction" in json_str
        assert "json_score" in json_str
        assert "json_test" in json_str
        assert '"state":"running"' in json_str

    def test_entity_from_dict(self):
        """Test PromptEntity creation from dictionary"""
        # Arrange
        entity_dict = {
            "index": 15,
            "prompt": "Dict test prompt",
            "target": "Dict test target",
            "model_prediction": "Dict test prediction",
            "reference_context": "Dict reference context",
            "evaluation_result": {"dict_score": 0.75},
            "additional_info": {"dict_test": True, "category": "test"},
            "state": TaskManagerStatus.COMPLETED
        }

        # Act
        entity = PromptEntity(**entity_dict)

        # Assert
        assert entity.index == 15
        assert entity.prompt == "Dict test prompt"
        assert entity.target == "Dict test target"
        assert entity.model_prediction == "Dict test prediction"
        assert entity.reference_context == "Dict reference context"
        assert entity.evaluation_result == {"dict_score": 0.75}
        assert entity.additional_info == {"dict_test": True, "category": "test"}
        assert entity.state == TaskManagerStatus.COMPLETED

    def test_inheritance_from_basemodel(self):
        """Test that PromptEntity inherits from BaseModel"""
        # Arrange
        entity = PromptEntity(
            index=0,
            prompt="Inheritance test",
            target="Test target"
        )

        # Act & Assert
        from pydantic import BaseModel
        assert isinstance(entity, BaseModel)
        assert hasattr(entity, 'model_dump')
        assert hasattr(entity, 'model_dump_json')
        assert hasattr(entity, 'model_validate')

    def test_arbitrary_types_allowed_config(self):
        """Test that the Config allows arbitrary types"""
        # Act
        entity = PromptEntity(
            index=0,
            prompt="Config test",
            target="Test target"
        )

        # Assert
        assert hasattr(entity, 'Config')
        assert entity.Config.arbitrary_types_allowed is True

    @pytest.mark.parametrize("field_name,new_value", [
        ("index", 999),
        ("prompt", "Updated prompt"),
        ("target", "Updated target"),
        ("model_prediction", "Updated prediction"),
        ("reference_context", "Updated reference context"),
        ("evaluation_result", {"updated_score": 0.95}),
        ("additional_info", {"updated": True, "new_field": "value"}),
        ("state", TaskManagerStatus.ERROR),
    ])
    def test_field_assignment_after_initialization(self, field_name, new_value):
        """Test field assignment after entity initialization"""
        # Arrange
        entity = PromptEntity(
            index=0,
            prompt="Original prompt",
            target="Original target",
            model_prediction="Original prediction",
            reference_context="Original reference",
            evaluation_result={"original_score": 0.8},
            additional_info={"original": True},
            state=TaskManagerStatus.PENDING
        )

        # Act
        setattr(entity, field_name, new_value)

        # Assert
        assert getattr(entity, field_name) == new_value

    def test_complex_nested_evaluation_result_structure(self):
        """Test PromptEntity with complex nested evaluation_result structure"""
        # Arrange
        complex_evaluation_result = {
            "overall_score": 0.88,
            "detailed_scores": {
                "accuracy": 0.9,
                "relevance": 0.85,
                "coherence": 0.9,
                "completeness": 0.85
            },
            "feedback": {
                "strengths": ["Clear explanation", "Good examples", "Comprehensive coverage"],
                "weaknesses": ["Could be more concise", "Some technical jargon"],
                "suggestions": ["Add more practical examples", "Simplify language"]
            },
            "metadata": {
                "evaluator": "expert_system",
                "timestamp": "2023-12-01T10:30:00Z",
                "version": "2.1.0"
            }
        }

        # Act
        entity = PromptEntity(
            index=0,
            prompt="Complex evaluation test",
            target="Complex target",
            evaluation_result=complex_evaluation_result
        )

        # Assert
        assert entity.evaluation_result == complex_evaluation_result
        assert entity.evaluation_result["overall_score"] == 0.88
        assert entity.evaluation_result["detailed_scores"]["accuracy"] == 0.9
        assert "Clear explanation" in entity.evaluation_result["feedback"]["strengths"]

    @pytest.mark.parametrize("index,prompt,target,state", [
        # Edge cases - boundary conditions
        (0, "", "", TaskManagerStatus.PENDING),  # All minimal values
        (-1, "a", "b", TaskManagerStatus.COMPLETED),  # Single character strings
        (999999, "Very long prompt " * 100, "Very long target " * 100, TaskManagerStatus.ERROR),  # Very long strings
        (None, None, None, TaskManagerStatus.COMPLETED_WITH_ERRORS),  # None values where allowed
        (123.456, 789, True, TaskManagerStatus.RUNNING),  # Mixed types
    ])
    def test_edge_case_combinations(self, index, prompt, target, state):
        """Test PromptEntity with edge case combinations"""
        # Act
        entity = PromptEntity(
            index=index,
            prompt=prompt,
            target=target,
            state=state
        )

        # Assert
        assert entity.index == index
        assert entity.prompt == prompt
        assert entity.target == target
        assert entity.state == state

    def test_real_world_prompt_scenarios(self):
        """Test PromptEntity with real-world scenarios"""
        # Test QA scenario
        qa_entity = PromptEntity(
            index=1,
            prompt="What is the capital of France?",
            target="Paris",
            model_prediction="The capital of France is Paris.",
            reference_context="Geography knowledge base",
            evaluation_result={"accuracy": 1.0, "confidence": 0.95},
            additional_info={"category": "geography", "difficulty": "easy", "source": "trivia_dataset"},
            state=TaskManagerStatus.COMPLETED
        )

        # Test code generation scenario
        code_entity = PromptEntity(
            index=2,
            prompt="Write a Python function to calculate factorial",
            target="def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
            model_prediction="def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
            reference_context="Python coding standards",
            evaluation_result={"correctness": 1.0, "efficiency": 0.8, "readability": 0.9},
            additional_info={"language": "python", "type": "function", "complexity": "recursive"},
            state=TaskManagerStatus.COMPLETED
        )

        # Test sentiment analysis scenario
        sentiment_entity = PromptEntity(
            index=3,
            prompt="Analyze the sentiment: 'I love this product!'",
            target="positive",
            model_prediction="positive",
            reference_context="Sentiment analysis guidelines",
            evaluation_result={"sentiment_accuracy": 1.0, "confidence_score": 0.92},
            additional_info={"task": "sentiment_analysis", "domain": "product_reviews"},
            state=TaskManagerStatus.COMPLETED
        )

        # Assert
        assert qa_entity.evaluation_result["accuracy"] == 1.0
        assert code_entity.evaluation_result["correctness"] == 1.0
        assert sentiment_entity.evaluation_result["sentiment_accuracy"] == 1.0

    def test_default_values(self):
        """Test that default values are correctly set"""
        # Act
        entity = PromptEntity(
            index=0,
            prompt="Default test",
            target="Test target"
        )

        # Assert
        assert entity.model_prediction is None
        assert entity.reference_context == ""
        assert entity.evaluation_result is None
        assert entity.additional_info == {}
        assert entity.state == TaskManagerStatus.PENDING

    def test_task_manager_status_enum_integration(self):
        """Test integration with TaskManagerStatus enum"""
        # Test all enum values
        for status in TaskManagerStatus:
            entity = PromptEntity(
                index=0,
                prompt="Status test",
                target="Test target",
                state=status
            )
            assert entity.state == status
            assert isinstance(entity.state, TaskManagerStatus)

    def test_workflow_state_transitions(self):
        """Test simulating workflow state transitions"""
        # Arrange
        entity = PromptEntity(
            index=0,
            prompt="Workflow test",
            target="Test target",
            state=TaskManagerStatus.PENDING
        )

        # Act & Assert - Simulate state transitions
        assert entity.state == TaskManagerStatus.PENDING

        entity.state = TaskManagerStatus.RUNNING
        assert entity.state == TaskManagerStatus.RUNNING

        entity.state = TaskManagerStatus.COMPLETED
        assert entity.state == TaskManagerStatus.COMPLETED

    def test_empty_and_none_values(self):
        """Test PromptEntity with empty and None values"""
        # Act
        entity = PromptEntity(
            index=None,  # None index
            prompt="",   # Empty prompt
            target=None, # None target
            model_prediction=None,  # None prediction
            reference_context="",   # Empty reference context
            evaluation_result=None, # None evaluation
            additional_info={},     # Empty additional info
            state=TaskManagerStatus.PENDING
        )

        # Assert
        assert entity.index is None
        assert entity.prompt == ""
        assert entity.target is None
        assert entity.model_prediction is None
        assert entity.reference_context == ""
        assert entity.evaluation_result is None
        assert entity.additional_info == {}
        assert entity.state == TaskManagerStatus.PENDING

    def test_large_data_structures(self):
        """Test PromptEntity with large data structures"""
        # Arrange
        large_prompt = {
            "instruction": "Process the following data",
            "context": "A" * 1000,  # Large context
            "examples": [{"input": f"example_{i}", "output": f"result_{i}"} for i in range(100)]
        }
        large_additional_info = {
            f"metadata_{i}": {"value": i, "description": f"Description {i}" * 10}
            for i in range(50)
        }

        # Act
        entity = PromptEntity(
            index=0,
            prompt=large_prompt,
            target="Large data test",
            additional_info=large_additional_info
        )

        # Assert
        assert entity.prompt == large_prompt
        assert len(entity.prompt["examples"]) == 100
        assert len(entity.additional_info) == 50
        assert entity.additional_info["metadata_0"]["value"] == 0 