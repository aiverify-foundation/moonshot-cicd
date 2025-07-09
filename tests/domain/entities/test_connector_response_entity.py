import pytest
from pydantic import ValidationError
from src.domain.entities.connector_response_entity import ConnectorResponseEntity


class TestConnectorResponseEntity:
    """Test cases for ConnectorResponseEntity"""

    @pytest.mark.parametrize(
        "response,context,expected_response,expected_context,should_pass",
        [
            # Good cases
            (
                "This is a valid response",
                ["context1", "context2"],
                "This is a valid response",
                ["context1", "context2"],
                True
            ),
            (
                "",
                [],
                "",
                [],
                True
            ),
            # Bad cases - invalid types
            (
                123,  # response should be string
                ["context1"],
                None,
                None,
                False
            ),
            (
                "Valid response",
                "invalid_context",  # context should be list, not string
                None,
                None,
                False
            ),
        ]
    )
    def test_connector_response_entity_creation(
        self, response, context, expected_response, expected_context, should_pass
    ):
        """Test ConnectorResponseEntity creation with various inputs"""
        if should_pass:
            # Test successful creation
            entity = ConnectorResponseEntity(response=response, context=context)
            assert entity.response == expected_response
            assert entity.context == expected_context
        else:
            # Test validation errors
            with pytest.raises(ValidationError):
                ConnectorResponseEntity(response=response, context=context)

    def test_default_values(self):
        """Test that default values are properly set"""
        entity = ConnectorResponseEntity()
        assert entity.response == ""
        assert entity.context == []

    def test_model_serialization(self):
        """Test that the model can be serialized to dict"""
        entity = ConnectorResponseEntity(
            response="Test response",
            context=["item1", "item2"]
        )
        
        expected_dict = {
            "response": "Test response",
            "context": ["item1", "item2"]
        }
        
        assert entity.model_dump() == expected_dict

    def test_model_from_dict(self):
        """Test creating model from dictionary"""
        data = {
            "response": "Test response from dict",
            "context": ["context_item"]
        }
        
        entity = ConnectorResponseEntity(**data)
        assert entity.response == "Test response from dict"
        assert entity.context == ["context_item"]

    @pytest.mark.parametrize(
        "context_items,expected_length",
        [
            ([], 0),
            (["single_item"], 1),
            (["item1", "item2", "item3"], 3),
            ([1, 2, 3], 3),  # Mixed types in list should be allowed
        ]
    )
    def test_context_list_handling(self, context_items, expected_length):
        """Test that context properly handles different list contents"""
        entity = ConnectorResponseEntity(
            response="Test",
            context=context_items
        )
        assert len(entity.context) == expected_length
        assert entity.context == context_items 