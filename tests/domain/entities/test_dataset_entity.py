import pytest
from pydantic import ValidationError
from datetime import datetime

from src.domain.entities.dataset_entity import DatasetEntity


class TestDatasetEntity:
    """Test class for DatasetEntity"""

    def test_minimal_initialization(self):
        """Test DatasetEntity with minimal required parameters"""
        # Arrange
        id_val = "test_dataset_123"
        name = "Test Dataset"
        description = "A test dataset for unit testing"
        examples = [{"input": "test", "output": "result"}]

        # Act
        entity = DatasetEntity(
            id=id_val,
            name=name,
            description=description,
            examples=examples
        )

        # Assert
        assert entity.id == id_val
        assert entity.name == name
        assert entity.description == description
        assert entity.examples == examples
        assert entity.num_of_dataset_prompts == 0  # Default value
        assert entity.created_date == ""  # Default value
        assert entity.reference == ""  # Default value
        assert entity.license == ""  # Default value

    def test_full_initialization(self):
        """Test DatasetEntity with all parameters provided"""
        # Arrange
        id_val = "comprehensive_dataset_456"
        name = "Comprehensive Test Dataset"
        description = "A comprehensive dataset with all fields populated"
        examples = [
            {"input": "What is AI?", "output": "Artificial Intelligence"},
            {"input": "Define ML", "output": "Machine Learning"},
            {"input": "Explain NLP", "output": "Natural Language Processing"}
        ]
        num_prompts = 150
        created_date = "2023-12-01 10:30:00"
        reference = "https://example.com/dataset"
        license = "MIT License"

        # Act
        entity = DatasetEntity(
            id=id_val,
            name=name,
            description=description,
            examples=examples,
            num_of_dataset_prompts=num_prompts,
            created_date=created_date,
            reference=reference,
            license=license
        )

        # Assert
        assert entity.id == id_val
        assert entity.name == name
        assert entity.description == description
        assert entity.examples == examples
        assert entity.num_of_dataset_prompts == num_prompts
        assert entity.created_date == created_date
        assert entity.reference == reference
        assert entity.license == license

    @pytest.mark.parametrize("id_val,name,description,examples", [
        # Good cases - various valid combinations
        ("simple_id", "Simple Name", "Simple description", []),
        ("dataset-with-hyphens", "Dataset With Hyphens", "Description with hyphens", [{"test": "data"}]),
        ("Dataset123", "Dataset With Numbers", "Description 123", [{"input": "test", "output": "result", "metadata": {"category": "A"}}]),
        ("dataset_with_underscores", "Dataset_With_Underscores", "Description_with_underscores", [{"complex": {"nested": {"data": "value"}}}]),
        ("UPPERCASE_DATASET", "UPPERCASE DATASET", "UPPERCASE DESCRIPTION", [{"a": 1}, {"b": 2}, {"c": 3}]),
        ("mixed_Case_Dataset", "Mixed Case Dataset", "Mixed case description", [{"key": "value"} for _ in range(10)]),
        ("dataset.with.dots", "Dataset.With.Dots", "Description with dots.", [{"input": f"test_{i}", "output": f"result_{i}"} for i in range(3)]),
        ("d", "D", "D", [{"single": "char"}]),  # Single character
        ("very_long_dataset_id_with_many_characters_and_descriptive_text", 
         "Very Long Dataset Name With Many Words And Descriptive Text", 
         "Very long description with multiple sentences and various details about the dataset contents and purpose.",
         [{"very": "long", "complex": {"nested": {"data": "structure", "with": ["multiple", "levels", "of", "nesting"]}}}]),
        ("unicode_dataset_名前", "Unicode Dataset 名前", "Unicode description 説明", [{"unicode": "データ"}]),
        ("dataset with spaces", "Dataset With Spaces", "Description with spaces", [{"space": "test"}]),
        ("dataset!@#$%^&*()", "Dataset!@#$%^&*()", "Description!@#$%^&*()", [{"special": "chars"}]),  # Special characters
    ])
    def test_valid_parameter_variations(self, id_val, name, description, examples):
        """Test DatasetEntity with various valid parameter combinations"""
        # Act
        entity = DatasetEntity(
            id=id_val,
            name=name,
            description=description,
            examples=examples
        )

        # Assert
        assert entity.id == id_val
        assert entity.name == name
        assert entity.description == description
        assert entity.examples == examples

    @pytest.mark.parametrize("field_name,invalid_value,expected_error", [
        # Bad cases - invalid types for required fields
        ("id", None, "Input should be a valid string"),
        ("id", 123, "Input should be a valid string"),
        ("id", [], "Input should be a valid string"),
        ("id", {}, "Input should be a valid string"),
        ("id", True, "Input should be a valid string"),
        ("name", None, "Input should be a valid string"),
        ("name", 123, "Input should be a valid string"),
        ("name", [], "Input should be a valid string"),
        ("name", {}, "Input should be a valid string"),
        ("name", True, "Input should be a valid string"),
        ("description", None, "Input should be a valid string"),
        ("description", 123, "Input should be a valid string"),
        ("description", [], "Input should be a valid string"),
        ("description", {}, "Input should be a valid string"),
        ("description", True, "Input should be a valid string"),
        ("examples", None, "Input should be a valid list"),
        ("examples", "string", "Input should be a valid list"),
        ("examples", 123, "Input should be a valid list"),
        ("examples", {}, "Input should be a valid list"),
        ("examples", True, "Input should be a valid list"),
    ])
    def test_invalid_required_field_types(self, field_name, invalid_value, expected_error):
        """Test DatasetEntity with invalid types for required fields"""
        # Arrange
        valid_params = {
            "id": "test_id",
            "name": "Test Name",
            "description": "Test description",
            "examples": [{"test": "data"}]
        }
        valid_params[field_name] = invalid_value

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DatasetEntity(**valid_params)
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize("field_name,invalid_value,expected_error", [
        # Bad cases - invalid types for optional fields
        ("num_of_dataset_prompts", "string", "Input should be a valid integer"),
        ("num_of_dataset_prompts", [], "Input should be a valid integer"),
        ("num_of_dataset_prompts", {}, "Input should be a valid integer"),
        ("created_date", 123, "Input should be a valid string"),
        ("created_date", [], "Input should be a valid string"),
        ("created_date", {}, "Input should be a valid string"),
        ("created_date", True, "Input should be a valid string"),
        ("reference", 123, "Input should be a valid string"),
        ("reference", [], "Input should be a valid string"),
        ("reference", {}, "Input should be a valid string"),
        ("reference", True, "Input should be a valid string"),
        ("license", 123, "Input should be a valid string"),
        ("license", [], "Input should be a valid string"),
        ("license", {}, "Input should be a valid string"),
        ("license", True, "Input should be a valid string"),
    ])
    def test_invalid_optional_field_types(self, field_name, invalid_value, expected_error):
        """Test DatasetEntity with invalid types for optional fields"""
        # Arrange
        valid_params = {
            "id": "test_id",
            "name": "Test Name",
            "description": "Test description",
            "examples": [{"test": "data"}]
        }
        valid_params[field_name] = invalid_value

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DatasetEntity(**valid_params)
        assert expected_error in str(exc_info.value)

    def test_missing_required_fields(self):
        """Test DatasetEntity with missing required fields"""
        # Test missing id
        with pytest.raises(ValidationError) as exc_info:
            DatasetEntity(
                name="Test Name",
                description="Test description",
                examples=[{"test": "data"}]
            )
        assert "Field required" in str(exc_info.value)

        # Test missing name
        with pytest.raises(ValidationError) as exc_info:
            DatasetEntity(
                id="test_id",
                description="Test description",
                examples=[{"test": "data"}]
            )
        assert "Field required" in str(exc_info.value)

        # Test missing description
        with pytest.raises(ValidationError) as exc_info:
            DatasetEntity(
                id="test_id",
                name="Test Name",
                examples=[{"test": "data"}]
            )
        assert "Field required" in str(exc_info.value)

        # Test missing examples
        with pytest.raises(ValidationError) as exc_info:
            DatasetEntity(
                id="test_id",
                name="Test Name",
                description="Test description"
            )
        assert "Field required" in str(exc_info.value)

    @pytest.mark.parametrize("num_prompts", [
        # Good cases - valid integer values
        0,
        1,
        10,
        100,
        1000,
        999999,
        -1,  # Negative numbers might be valid depending on business logic
        -100,
    ])
    def test_valid_num_of_dataset_prompts(self, num_prompts):
        """Test DatasetEntity with various valid num_of_dataset_prompts values"""
        # Act
        entity = DatasetEntity(
            id="test_id",
            name="Test Name",
            description="Test description",
            examples=[{"test": "data"}],
            num_of_dataset_prompts=num_prompts
        )

        # Assert
        assert entity.num_of_dataset_prompts == num_prompts

    @pytest.mark.parametrize("examples_data", [
        # Good cases - various valid examples structures
        [],  # Empty list
        [{}],  # List with empty dict
        [{"simple": "value"}],  # Simple key-value
        [{"input": "test", "output": "result"}],  # Typical structure
        [{"a": 1, "b": 2, "c": 3}],  # Multiple key-value pairs
        [{"nested": {"data": {"value": "test"}}}],  # Nested structure
        [{"list": ["item1", "item2", "item3"]}],  # List values
        [{"mixed": {"string": "text", "number": 42, "boolean": True, "list": [1, 2, 3]}}],  # Mixed types
        [{"example": i} for i in range(100)],  # Large list
        [{"unicode": "テスト", "emoji": "🚀", "special": "café"}],  # Unicode characters
    ])
    def test_valid_examples_structures(self, examples_data):
        """Test DatasetEntity with various valid examples structures"""
        # Act
        entity = DatasetEntity(
            id="test_id",
            name="Test Name",
            description="Test description",
            examples=examples_data
        )

        # Assert
        assert entity.examples == examples_data

    def test_entity_serialization(self):
        """Test DatasetEntity serialization to dictionary"""
        # Arrange
        entity = DatasetEntity(
            id="serialization_test",
            name="Serialization Test Dataset",
            description="Dataset for testing serialization",
            examples=[{"input": "test", "output": "result"}],
            num_of_dataset_prompts=50,
            created_date="2023-12-01 15:30:00",
            reference="https://example.com/dataset",
            license="Apache 2.0"
        )

        # Act
        entity_dict = entity.model_dump()

        # Assert
        expected_keys = ["id", "name", "description", "examples", "num_of_dataset_prompts", "created_date", "reference", "license"]
        assert all(key in entity_dict for key in expected_keys)
        assert entity_dict["id"] == "serialization_test"
        assert entity_dict["name"] == "Serialization Test Dataset"
        assert entity_dict["description"] == "Dataset for testing serialization"
        assert entity_dict["examples"] == [{"input": "test", "output": "result"}]
        assert entity_dict["num_of_dataset_prompts"] == 50
        assert entity_dict["created_date"] == "2023-12-01 15:30:00"
        assert entity_dict["reference"] == "https://example.com/dataset"
        assert entity_dict["license"] == "Apache 2.0"

    def test_entity_json_serialization(self):
        """Test DatasetEntity JSON serialization"""
        # Arrange
        entity = DatasetEntity(
            id="json_test",
            name="JSON Test Dataset",
            description="Dataset for JSON serialization testing",
            examples=[{"json": "test", "data": {"nested": "value"}}],
            num_of_dataset_prompts=25
        )

        # Act
        json_str = entity.model_dump_json()

        # Assert
        assert isinstance(json_str, str)
        assert "json_test" in json_str
        assert "JSON Test Dataset" in json_str
        assert "Dataset for JSON serialization testing" in json_str
        assert "nested" in json_str

    def test_entity_from_dict(self):
        """Test DatasetEntity creation from dictionary"""
        # Arrange
        entity_dict = {
            "id": "dict_test",
            "name": "Dict Test Dataset",
            "description": "Dataset created from dictionary",
            "examples": [{"dict": "example", "value": 42}],
            "num_of_dataset_prompts": 75,
            "created_date": "2023-12-01 12:00:00",
            "reference": "https://example.com/dict-dataset",
            "license": "BSD 3-Clause"
        }

        # Act
        entity = DatasetEntity(**entity_dict)

        # Assert
        assert entity.id == "dict_test"
        assert entity.name == "Dict Test Dataset"
        assert entity.description == "Dataset created from dictionary"
        assert entity.examples == [{"dict": "example", "value": 42}]
        assert entity.num_of_dataset_prompts == 75
        assert entity.created_date == "2023-12-01 12:00:00"
        assert entity.reference == "https://example.com/dict-dataset"
        assert entity.license == "BSD 3-Clause"

    def test_inheritance_from_basemodel(self):
        """Test that DatasetEntity inherits from BaseModel"""
        # Arrange
        entity = DatasetEntity(
            id="inheritance_test",
            name="Inheritance Test",
            description="Testing BaseModel inheritance",
            examples=[{"test": "inheritance"}]
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
        entity = DatasetEntity(
            id="config_test",
            name="Config Test",
            description="Testing arbitrary types config",
            examples=[{"custom": "object"}]
        )

        # Assert
        assert hasattr(entity, 'Config')
        assert entity.Config.arbitrary_types_allowed is True

    @pytest.mark.parametrize("field_name,new_value", [
        ("id", "updated_id"),
        ("name", "Updated Dataset Name"),
        ("description", "Updated description with new content"),
        ("examples", [{"updated": "example", "new": "data"}]),
        ("num_of_dataset_prompts", 200),
        ("created_date", "2024-01-01 10:00:00"),
        ("reference", "https://updated-example.com/dataset"),
        ("license", "GPL v3"),
    ])
    def test_field_assignment_after_initialization(self, field_name, new_value):
        """Test field assignment after entity initialization"""
        # Arrange
        entity = DatasetEntity(
            id="original_id",
            name="Original Name",
            description="Original description",
            examples=[{"original": "example"}],
            num_of_dataset_prompts=10,
            created_date="2023-01-01 00:00:00",
            reference="https://original-example.com",
            license="MIT"
        )

        # Act
        setattr(entity, field_name, new_value)

        # Assert
        assert getattr(entity, field_name) == new_value

    def test_complex_nested_examples_structure(self):
        """Test DatasetEntity with complex nested examples structure"""
        # Arrange
        complex_examples = [
            {
                "id": "example_1",
                "input": {
                    "prompt": "Analyze this data",
                    "context": ["context1", "context2"],
                    "metadata": {
                        "source": "user_input",
                        "timestamp": "2023-12-01T10:30:00Z",
                        "priority": "high"
                    }
                },
                "output": {
                    "response": "Analysis complete",
                    "confidence": 0.95,
                    "details": {
                        "findings": ["finding1", "finding2"],
                        "recommendations": ["rec1", "rec2"]
                    }
                },
                "annotations": {
                    "quality": "excellent",
                    "reviewed_by": "expert_1",
                    "tags": ["analysis", "high_quality", "reviewed"]
                }
            },
            {
                "id": "example_2",
                "input": "Simple string input",
                "output": "Simple string output",
                "metadata": {"type": "simple"}
            }
        ]

        # Act
        entity = DatasetEntity(
            id="complex_test",
            name="Complex Examples Test",
            description="Testing complex nested examples",
            examples=complex_examples
        )

        # Assert
        assert entity.examples == complex_examples
        assert entity.examples[0]["input"]["metadata"]["priority"] == "high"
        assert entity.examples[0]["output"]["confidence"] == 0.95
        assert "analysis" in entity.examples[0]["annotations"]["tags"]

    @pytest.mark.parametrize("created_date", [
        # Good cases - various valid date string formats
        "",  # Empty string (default)
        "2023-12-01 10:30:00",  # Standard format
        "2023-01-01 00:00:00",  # Start of year
        "2023-12-31 23:59:59",  # End of year
        "2024-02-29 12:00:00",  # Leap year
        "1990-01-01 12:00:00",  # Old date
        "2050-01-01 12:00:00",  # Future date
        "Custom date format: 2023-12-01",  # Non-standard format (business logic dependent)
        "ISO format: 2023-12-01T10:30:00Z",  # ISO format
    ])
    def test_valid_created_date_formats(self, created_date):
        """Test DatasetEntity with various valid created_date formats"""
        # Act
        entity = DatasetEntity(
            id="date_test",
            name="Date Test",
            description="Testing date formats",
            examples=[{"test": "date"}],
            created_date=created_date
        )

        # Assert
        assert entity.created_date == created_date

    def test_edge_case_empty_strings(self):
        """Test DatasetEntity with edge case empty strings"""
        # Act
        entity = DatasetEntity(
            id="",  # Empty ID
            name="",  # Empty name
            description="",  # Empty description
            examples=[],  # Empty examples
            created_date="",
            reference="",
            license=""
        )

        # Assert
        assert entity.id == ""
        assert entity.name == ""
        assert entity.description == ""
        assert entity.examples == []
        assert entity.created_date == ""
        assert entity.reference == ""
        assert entity.license == ""

    def test_large_dataset_examples(self):
        """Test DatasetEntity with large number of examples"""
        # Arrange
        large_examples = [{"example_id": i, "data": f"data_{i}"} for i in range(1000)]

        # Act
        entity = DatasetEntity(
            id="large_dataset",
            name="Large Dataset Test",
            description="Testing with large number of examples",
            examples=large_examples,
            num_of_dataset_prompts=1000
        )

        # Assert
        assert len(entity.examples) == 1000
        assert entity.examples[0]["example_id"] == 0
        assert entity.examples[999]["example_id"] == 999
        assert entity.num_of_dataset_prompts == 1000 