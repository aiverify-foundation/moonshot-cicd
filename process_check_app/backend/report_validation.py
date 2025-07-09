import json
from typing import Any

from backend.schema.ms_ga_schema import (
    Schema1,
    extract_ga_report_info,
)
from backend.schema.ms_v06_schema import Schema2, extract_06_report_info
from pydantic import ValidationError


def validate_json(data: dict[str, Any]) -> bool:
    """
    Validate if the provided JSON data conforms to either the Moonshot GA schema (Schema1)
    or the Moonshot v0.6 schema (Schema2).

    This function attempts validation against both supported schemas sequentially.
    It first tries Schema1 (Moonshot GA format) and falls back to Schema2 (v0.6 format)
    if the first validation fails.

    Args:
        data (dict[str, Any]): The JSON data structure to validate against known schemas

    Returns:
        bool: True if data successfully validates against either schema, False if both fail

    Note:
        The function catches both ValidationError (from Pydantic validation failures)
        and TypeError (from basic type mismatches) to handle various malformed data cases.
    """
    try:
        # Attempt validation against Moonshot GA schema (Schema1)
        Schema1(**data)
        return True
    except (ValidationError, TypeError):
        try:
            # Attempt validation against Moonshot v0.6 schema (Schema2)
            Schema2(**data)
            return True
        except (ValidationError, TypeError):
            # Data does not conform to either supported schema
            return False


def get_report_info(filepath: str) -> dict[str, Any]:
    """
    Extract report information from a JSON file based on its schema.

    Args:
        filepath (str): Path to the JSON file to process

    Returns:
        dict[str, Any]: Extracted report information if successful, empty dict if file not found

    Raises:
        ValueError: If the JSON data does not match any known schema
    """
    try:
        with open(filepath, "r") as file:
            data = json.load(file)
        # Try to validate against Schema 1
        Schema1(**data)
        return extract_ga_report_info(data)
    except ValidationError:
        try:
            # Try to validate against Schema 2
            Schema2(**data)
            return extract_06_report_info(data)
        except ValidationError:
            # If both validations fail, raise an error
            raise ValueError("Data does not match any known schema.")
    except FileNotFoundError:
        return {}
