import pytest
from pydantic import ValidationError

from src.domain.entities.metric_individual_entity import MetricIndividualEntity
from domain.entities.connector_response_entity import ConnectorResponseEntity


class TestMetricIndividualEntity:
    """Test class for MetricIndividualEntity"""

    def test_minimal_initialization(self):
        """Test MetricIndividualEntity with minimal required parameters"""
        # Arrange
        prompt = "What is machine learning?"
        predicted_result = ConnectorResponseEntity(
            response="Machine learning is a subset of AI"
        )
        target = "Expected answer about ML"

        # Act
        entity = MetricIndividualEntity(
            prompt=prompt,
            predicted_result=predicted_result,
            target=target
        )

        # Assert
        assert entity.prompt == prompt
        assert entity.predicted_result == predicted_result
        assert entity.target == target
        assert entity.reference_context == ""  # Default value
        assert entity.evaluated_result is None  # Default value

    def test_full_initialization(self):
        """Test MetricIndividualEntity with all parameters provided"""
        # Arrange
        prompt = "Explain deep learning concepts"
        predicted_result = ConnectorResponseEntity(
            response="Deep learning uses neural networks with multiple layers",
            context=["Context 1", "Context 2"]
        )
        target = "Comprehensive explanation of deep learning"
        reference_context = "Reference context for evaluation"
        evaluated_result = {"score": 0.85, "feedback": "Good response"}

        # Act
        entity = MetricIndividualEntity(
            prompt=prompt,
            predicted_result=predicted_result,
            target=target,
            reference_context=reference_context,
            evaluated_result=evaluated_result
        )

        # Assert
        assert entity.prompt == prompt
        assert entity.predicted_result == predicted_result
        assert entity.target == target
        assert entity.reference_context == reference_context
        assert entity.evaluated_result == evaluated_result

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
    ])
    def test_valid_prompt_variations(self, prompt):
        """Test MetricIndividualEntity with various valid prompt types"""
        # Arrange
        predicted_result = ConnectorResponseEntity(response="Test response")
        target = "Test target"

        # Act
        entity = MetricIndividualEntity(
            prompt=prompt,
            predicted_result=predicted_result,
            target=target
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
    ])
    def test_valid_target_variations(self, target):
        """Test MetricIndividualEntity with various valid target types"""
        # Arrange
        prompt = "Test prompt"
        predicted_result = ConnectorResponseEntity(response="Test response")

        # Act
        entity = MetricIndividualEntity(
            prompt=prompt,
            predicted_result=predicted_result,
            target=target
        )

        # Assert
        assert entity.target == target

    @pytest.mark.parametrize("predicted_result", [
        # Good cases - various valid ConnectorResponseEntity instances
        ConnectorResponseEntity(response="Simple response"),
        ConnectorResponseEntity(response="", context=[]),
        ConnectorResponseEntity(
            response="Complex response",
            context=["Context 1", "Context 2", "Context 3"]
        ),
        ConnectorResponseEntity(
            response="Response with unicode: 测试",
            context=["Unicode context: テスト"]
        ),
        ConnectorResponseEntity(
            response="Very long response " * 50,
            context=["Very long context " * 20]
        ),
    ])
    def test_valid_predicted_result_variations(self, predicted_result):
        """Test MetricIndividualEntity with various valid ConnectorResponseEntity instances"""
        # Arrange
        prompt = "Test prompt"
        target = "Test target"

        # Act
        entity = MetricIndividualEntity(
            prompt=prompt,
            predicted_result=predicted_result,
            target=target
        )

        # Assert
        assert entity.predicted_result == predicted_result
        assert isinstance(entity.predicted_result, ConnectorResponseEntity)

    @pytest.mark.parametrize("predicted_result_dict", [
        # Good cases - various valid dictionary inputs that should convert to ConnectorResponseEntity
        {"response": "Simple response"},
        {"response": "", "context": []},
        {"response": "Complex response", "context": ["Context 1", "Context 2"]},
        {"response": "Response with unicode: 测试", "context": ["Unicode context: テスト"]},
        {},  # Empty dict should work (default values)
    ])
    def test_valid_predicted_result_dict_variations(self, predicted_result_dict):
        """Test MetricIndividualEntity with various valid dictionary inputs for predicted_result"""
        # Arrange
        prompt = "Test prompt"
        target = "Test target"

        # Act
        entity = MetricIndividualEntity(
            prompt=prompt,
            predicted_result=predicted_result_dict,
            target=target
        )

        # Assert
        assert isinstance(entity.predicted_result, ConnectorResponseEntity)
        if "response" in predicted_result_dict:
            assert entity.predicted_result.response == predicted_result_dict["response"]
        if "context" in predicted_result_dict:
            assert entity.predicted_result.context == predicted_result_dict["context"]

    @pytest.mark.parametrize("predicted_result,expected_error", [
        # Bad cases - invalid predicted_result types
        (None, "Input should be a valid dictionary or instance of ConnectorResponseEntity"),
        ("string", "Input should be a valid dictionary or instance of ConnectorResponseEntity"),
        (123, "Input should be a valid dictionary or instance of ConnectorResponseEntity"),
        ([], "Input should be a valid dictionary or instance of ConnectorResponseEntity"),
        (True, "Input should be a valid dictionary or instance of ConnectorResponseEntity"),
    ])
    def test_invalid_predicted_result_types(self, predicted_result, expected_error):
        """Test MetricIndividualEntity with invalid predicted_result types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            MetricIndividualEntity(
                prompt="Test prompt",
                predicted_result=predicted_result,
                target="Test target"
            )
        assert expected_error in str(exc_info.value)

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
    ])
    def test_valid_reference_context_variations(self, reference_context):
        """Test MetricIndividualEntity with various valid reference_context strings"""
        # Arrange
        prompt = "Test prompt"
        predicted_result = ConnectorResponseEntity(response="Test response")
        target = "Test target"

        # Act
        entity = MetricIndividualEntity(
            prompt=prompt,
            predicted_result=predicted_result,
            target=target,
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
        """Test MetricIndividualEntity with invalid reference_context types"""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            MetricIndividualEntity(
                prompt="Test prompt",
                predicted_result=ConnectorResponseEntity(response="Test response"),
                target="Test target",
                reference_context=reference_context
            )
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("evaluated_result", [
        # Good cases - various valid evaluated_result types
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
    ])
    def test_valid_evaluated_result_variations(self, evaluated_result):
        """Test MetricIndividualEntity with various valid evaluated_result types"""
        # Arrange
        prompt = "Test prompt"
        predicted_result = ConnectorResponseEntity(response="Test response")
        target = "Test target"

        # Act
        entity = MetricIndividualEntity(
            prompt=prompt,
            predicted_result=predicted_result,
            target=target,
            evaluated_result=evaluated_result
        )

        # Assert
        assert entity.evaluated_result == evaluated_result

    def test_missing_required_fields(self):
        """Test MetricIndividualEntity with missing required fields"""
        # Test missing prompt
        with pytest.raises(ValidationError) as exc_info:
            MetricIndividualEntity(
                predicted_result=ConnectorResponseEntity(response="Test"),
                target="Test target"
            )
        assert "Field required" in str(exc_info.value)

        # Test missing predicted_result
        with pytest.raises(ValidationError) as exc_info:
            MetricIndividualEntity(
                prompt="Test prompt",
                target="Test target"
            )
        assert "Field required" in str(exc_info.value)

        # Test missing target
        with pytest.raises(ValidationError) as exc_info:
            MetricIndividualEntity(
                prompt="Test prompt",
                predicted_result=ConnectorResponseEntity(response="Test")
            )
        assert "Field required" in str(exc_info.value)

    def test_entity_serialization(self):
        """Test MetricIndividualEntity serialization to dictionary"""
        # Arrange
        prompt = "Serialization test prompt"
        predicted_result = ConnectorResponseEntity(
            response="Serialization test response",
            context=["Context 1", "Context 2"]
        )
        target = "Serialization test target"
        reference_context = "Serialization reference context"
        evaluated_result = {"score": 0.9, "feedback": "Excellent"}

        entity = MetricIndividualEntity(
            prompt=prompt,
            predicted_result=predicted_result,
            target=target,
            reference_context=reference_context,
            evaluated_result=evaluated_result
        )

        # Act
        entity_dict = entity.model_dump()

        # Assert
        expected_keys = ["prompt", "predicted_result", "target", "reference_context", "evaluated_result"]
        assert all(key in entity_dict for key in expected_keys)
        assert entity_dict["prompt"] == prompt
        assert entity_dict["target"] == target
        assert entity_dict["reference_context"] == reference_context
        assert entity_dict["evaluated_result"] == evaluated_result
        assert entity_dict["predicted_result"]["response"] == "Serialization test response"

    def test_entity_json_serialization(self):
        """Test MetricIndividualEntity JSON serialization"""
        # Arrange
        entity = MetricIndividualEntity(
            prompt="JSON test prompt",
            predicted_result=ConnectorResponseEntity(
                response="JSON test response",
                context=["JSON context"]
            ),
            target="JSON test target",
            evaluated_result={"json_score": 0.85}
        )

        # Act
        json_str = entity.model_dump_json()

        # Assert
        assert isinstance(json_str, str)
        assert "JSON test prompt" in json_str
        assert "JSON test response" in json_str
        assert "JSON test target" in json_str
        assert "json_score" in json_str

    def test_entity_from_dict(self):
        """Test MetricIndividualEntity creation from dictionary"""
        # Arrange
        entity_dict = {
            "prompt": "Dict test prompt",
            "predicted_result": {
                "response": "Dict test response",
                "context": ["Dict context 1", "Dict context 2"]
            },
            "target": "Dict test target",
            "reference_context": "Dict reference context",
            "evaluated_result": {"dict_score": 0.75}
        }

        # Act
        entity = MetricIndividualEntity(**entity_dict)

        # Assert
        assert entity.prompt == "Dict test prompt"
        assert isinstance(entity.predicted_result, ConnectorResponseEntity)
        assert entity.predicted_result.response == "Dict test response"
        assert entity.predicted_result.context == ["Dict context 1", "Dict context 2"]
        assert entity.target == "Dict test target"
        assert entity.reference_context == "Dict reference context"
        assert entity.evaluated_result == {"dict_score": 0.75}

    def test_inheritance_from_basemodel(self):
        """Test that MetricIndividualEntity inherits from BaseModel"""
        # Arrange
        entity = MetricIndividualEntity(
            prompt="Inheritance test",
            predicted_result=ConnectorResponseEntity(response="Test"),
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
        entity = MetricIndividualEntity(
            prompt="Config test",
            predicted_result=ConnectorResponseEntity(response="Test"),
            target="Test target"
        )

        # Assert
        assert hasattr(entity, 'Config')
        assert entity.Config.arbitrary_types_allowed is True

    @pytest.mark.parametrize("field_name,new_value", [
        ("prompt", "Updated prompt"),
        ("target", "Updated target"),
        ("reference_context", "Updated reference context"),
        ("evaluated_result", {"updated_score": 0.95}),
    ])
    def test_field_assignment_after_initialization(self, field_name, new_value):
        """Test field assignment after entity initialization"""
        # Arrange
        entity = MetricIndividualEntity(
            prompt="Original prompt",
            predicted_result=ConnectorResponseEntity(response="Original response"),
            target="Original target",
            reference_context="Original reference",
            evaluated_result={"original_score": 0.8}
        )

        # Act
        setattr(entity, field_name, new_value)

        # Assert
        assert getattr(entity, field_name) == new_value

    def test_predicted_result_assignment_after_initialization(self):
        """Test predicted_result assignment after initialization"""
        # Arrange
        entity = MetricIndividualEntity(
            prompt="Test prompt",
            predicted_result=ConnectorResponseEntity(response="Original response"),
            target="Test target"
        )

        new_predicted_result = ConnectorResponseEntity(
            response="New response",
            context=["New context"]
        )

        # Act
        entity.predicted_result = new_predicted_result

        # Assert
        assert entity.predicted_result == new_predicted_result
        assert entity.predicted_result.response == "New response"
        assert entity.predicted_result.context == ["New context"]

    def test_complex_nested_evaluated_result_structure(self):
        """Test MetricIndividualEntity with complex nested evaluated_result structure"""
        # Arrange
        complex_evaluated_result = {
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
        entity = MetricIndividualEntity(
            prompt="Complex evaluation test",
            predicted_result=ConnectorResponseEntity(response="Complex response"),
            target="Complex target",
            evaluated_result=complex_evaluated_result
        )

        # Assert
        assert entity.evaluated_result == complex_evaluated_result
        assert entity.evaluated_result["overall_score"] == 0.88
        assert entity.evaluated_result["detailed_scores"]["accuracy"] == 0.9
        assert "Clear explanation" in entity.evaluated_result["feedback"]["strengths"]

    @pytest.mark.parametrize("prompt,target,reference_context", [
        # Edge cases - boundary conditions
        ("", "", ""),  # All empty strings
        ("a", "b", "c"),  # Single character strings
        ("Very long prompt " * 100, "Very long target " * 100, "Very long reference " * 100),  # Very long strings
        (None, None, ""),  # None values where allowed
        (123, 456, "789"),  # Mixed types
    ])
    def test_edge_case_combinations(self, prompt, target, reference_context):
        """Test MetricIndividualEntity with edge case combinations"""
        # Act
        entity = MetricIndividualEntity(
            prompt=prompt,
            predicted_result=ConnectorResponseEntity(response="Edge case response"),
            target=target,
            reference_context=reference_context
        )

        # Assert
        assert entity.prompt == prompt
        assert entity.target == target
        assert entity.reference_context == reference_context

    def test_real_world_metric_individual_scenarios(self):
        """Test MetricIndividualEntity with real-world scenarios"""
        # Test QA scenario
        qa_entity = MetricIndividualEntity(
            prompt="What is the capital of France?",
            predicted_result=ConnectorResponseEntity(
                response="The capital of France is Paris.",
                context=["France is a country in Europe", "Paris is a major city"]
            ),
            target="Paris",
            reference_context="Geography knowledge base",
            evaluated_result={"accuracy": 1.0, "confidence": 0.95}
        )

        # Test sentiment analysis scenario
        sentiment_entity = MetricIndividualEntity(
            prompt="Analyze the sentiment: 'I love this product!'",
            predicted_result=ConnectorResponseEntity(
                response="Positive sentiment with high confidence",
                context=["Sentiment analysis context"]
            ),
            target="Positive",
            reference_context="Sentiment analysis guidelines",
            evaluated_result={"sentiment_accuracy": 0.9, "confidence_score": 0.85}
        )

        # Test code generation scenario
        code_entity = MetricIndividualEntity(
            prompt="Write a Python function to calculate factorial",
            predicted_result=ConnectorResponseEntity(
                response="def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)"
            ),
            target="Correct recursive factorial implementation",
            reference_context="Python coding standards",
            evaluated_result={
                "correctness": 1.0,
                "efficiency": 0.8,
                "readability": 0.9,
                "overall": 0.9
            }
        )

        # Assert
        assert qa_entity.evaluated_result["accuracy"] == 1.0
        assert sentiment_entity.evaluated_result["sentiment_accuracy"] == 0.9
        assert code_entity.evaluated_result["overall"] == 0.9

    def test_default_values(self):
        """Test that default values are correctly set"""
        # Act
        entity = MetricIndividualEntity(
            prompt="Default test",
            predicted_result=ConnectorResponseEntity(response="Test response"),
            target="Test target"
        )

        # Assert
        assert entity.reference_context == ""
        assert entity.evaluated_result is None

    def test_none_evaluated_result(self):
        """Test MetricIndividualEntity with None evaluated_result"""
        # Act
        entity = MetricIndividualEntity(
            prompt="None test",
            predicted_result=ConnectorResponseEntity(response="Test response"),
            target="Test target",
            evaluated_result=None
        )

        # Assert
        assert entity.evaluated_result is None

    def test_empty_string_fields(self):
        """Test MetricIndividualEntity with empty string fields"""
        # Act
        entity = MetricIndividualEntity(
            prompt="",  # Empty prompt
            predicted_result=ConnectorResponseEntity(response=""),  # Empty response
            target="",  # Empty target
            reference_context="",  # Empty reference context
            evaluated_result={}  # Empty dict
        )

        # Assert
        assert entity.prompt == ""
        assert entity.target == ""
        assert entity.reference_context == ""
        assert entity.evaluated_result == {}

    def test_connector_response_entity_integration(self):
        """Test integration with ConnectorResponseEntity"""
        # Arrange
        connector_response = ConnectorResponseEntity(
            response="Detailed AI response with comprehensive information",
            context=[
                "Context item 1: Background information",
                "Context item 2: Supporting details",
                "Context item 3: Additional references"
            ]
        )

        # Act
        entity = MetricIndividualEntity(
            prompt="Integration test prompt",
            predicted_result=connector_response,
            target="Integration test target",
            reference_context="Integration reference context",
            evaluated_result={"integration_score": 0.92}
        )

        # Assert
        assert isinstance(entity.predicted_result, ConnectorResponseEntity)
        assert entity.predicted_result.response == "Detailed AI response with comprehensive information"
        assert len(entity.predicted_result.context) == 3
        assert "Background information" in entity.predicted_result.context[0] 