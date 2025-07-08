import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st
from streamlit.logger import get_logger

logger = get_logger(__name__)

# Directory where workspace outputs are stored
OUTPUTS_DIRECTORY = Path("sessions")


def initialize(workspace_id: str = "", workspace_data: Optional[dict] = None) -> None:
    """
    Initialize a new workspace session.

    Creates a unique workspace session and sets up the workspace state in Streamlit's session state.
    Ensures the outputs directory exists for storing workspace data.

    Args:
        workspace_id: The identifier for the workspace. Defaults to an empty string.
        workspace_data: The data associated with the workspace. Defaults to None.

    Returns:
        None
    """
    logger.info("Starting the initialization of a new workspace.")

    # Validate workspace_id type and use empty string if not a string
    if not isinstance(workspace_id, str):
        workspace_id = ""

    # Validate workspace_data type and use empty dict if not a dict
    if not isinstance(workspace_data, dict):
        workspace_data = {}

    # Create outputs directory if it doesn't exist
    ensure_outputs_directory_exists()

    # Initialize the workspace state in Streamlit's session state
    st.session_state.update(
        {
            "workspace_id": workspace_id,
            "workspace_data": workspace_data,
        }
    )


def workspace_file_exists(workspace_id: str) -> bool:
    """
    Check if a workspace file with the given ID exists on disk.

    This function verifies the existence of a JSON file corresponding to the
    provided workspace ID in the outputs directory.

    Args:
        workspace_id: The workspace ID to check.

    Returns:
        bool: True if the workspace JSON file exists in the outputs directory, False otherwise.

    Raises:
        ValueError: If workspace_id is empty, None, or not a string.
    """
    # Validate that workspace_id is not empty, is a string, and is not None
    if not workspace_id or not isinstance(workspace_id, str) or workspace_id is None:
        raise ValueError("workspace_id must be a non-empty string")

    # Construct the file path for the workspace JSON file
    file_path = OUTPUTS_DIRECTORY / f"{workspace_id}.json"
    return file_path.exists()


def is_workspace_initialized() -> bool:
    """
    Determine if a workspace has been initialized in the current Streamlit session.

    Checks if a workspace ID is present, non-empty, and is a valid string type in the session state.
    This is used to verify that a workspace session is properly set up before performing
    workspace operations.

    Returns:
        bool: True if a workspace ID is present and non-empty in session state, False otherwise.

    Raises:
        TypeError: If workspace_id is not a string.
    """
    # Get the workspace_id from session state, defaulting to empty string if not found
    workspace_id = st.session_state.get("workspace_id", "")

    # Validate that workspace_id is a string type
    if not isinstance(workspace_id, str):
        raise TypeError("workspace_id must be a string")

    # Return True only if workspace_id is a non-empty string
    return bool(workspace_id)


def ensure_outputs_directory_exists() -> None:
    """
    Ensure the outputs directory exists for storing workspace data.

    Creates the outputs directory if it doesn't already exist. This is a prerequisite
    for saving workspace files and should be called before any file operations.

    Returns:
        None
    """
    # Check if the outputs directory already exists
    if not OUTPUTS_DIRECTORY.exists():
        # Create the directory with parent directories if needed
        OUTPUTS_DIRECTORY.mkdir(parents=True)
        logger.info(f"Outputs directory created: {OUTPUTS_DIRECTORY}")
    else:
        logger.info(f"Outputs directory already exists: {OUTPUTS_DIRECTORY}")


def get_available_workspaces() -> list:
    """
    Retrieve all available workspaces from the outputs directory.

    Scans the outputs directory for JSON files and loads their contents.
    This function is useful for displaying available workspaces to users
    or for workspace management operations.

    Returns:
        A list of dictionaries containing workspace IDs and their associated data.
        Each dictionary has the structure: {"workspace_id": str, "workspace_data": dict}
    """
    workspaces = []

    # Get all JSON files in the outputs directory
    json_files = list(OUTPUTS_DIRECTORY.glob("*.json"))

    # Process each JSON file and attempt to load its workspace data
    for file_path in json_files:
        workspace = _load_workspace_file(file_path)
        if workspace:
            workspaces.append(workspace)

    logger.info(f"Total available workspaces found: {len(workspaces)}")
    return workspaces


def _load_workspace_file(file_path: Path) -> Optional[dict]:
    """
    Load a workspace file and return its contents.

    This is a private helper function that handles the low-level file loading
    operations for workspace JSON files. It safely loads the file and handles
    any potential errors during the process.

    Args:
        file_path: Path to the workspace JSON file

    Returns:
        Dictionary containing workspace ID and data, or None if loading failed.
        The returned dictionary has the structure: {"workspace_id": str, "workspace_data": dict}
    """
    try:
        # Open and read the JSON file
        with file_path.open("r") as file:
            workspace_data = json.load(file)
            # Extract workspace ID from the filename (without extension)
            workspace_id = file_path.stem
            return {"workspace_id": workspace_id, "workspace_data": workspace_data}
    except Exception as e:
        # Log any errors that occur during file loading
        logger.error(f"Error reading workspace file {file_path.name}: {str(e)}")
        return None


def load_workspace(workspace_id: str) -> Optional[dict]:
    """
    Load workspace data for a specific workspace ID.

    Attempts to read and parse the JSON file associated with the given workspace ID.
    This function is used to retrieve previously saved workspace data for continuing
    work on an existing workspace.

    Args:
        workspace_id: The ID of the workspace to load.

    Returns:
        The workspace data if found, or None if the workspace doesn't exist or cannot be loaded.
    """
    # Construct the file path for the workspace JSON file
    file_path = OUTPUTS_DIRECTORY / f"{workspace_id}.json"

    # Check if the workspace file exists
    if not file_path.exists():
        logger.warning(f"Workspace file for ID '{workspace_id}' does not exist.")
        return None

    try:
        # Read and parse the JSON file
        with file_path.open("r") as file:
            workspace_data = json.load(file)
            logger.info(f"Workspace data successfully loaded for ID '{workspace_id}'.")
            return workspace_data
    except Exception as e:
        # Log any errors that occur during file loading
        logger.error(f"Error loading workspace data for ID '{workspace_id}': {str(e)}")
        return None


def save_workspace(workspace_id: str, workspace_data: dict) -> bool:
    """
    Save workspace data to a JSON file.

    Persists the workspace data to disk as a JSON file, adding a timestamp
    to track when the workspace was last saved. This function ensures data
    persistence across application sessions.

    Args:
        workspace_id: The identifier for the workspace
        workspace_data: The data to save

    Returns:
        True if the workspace was successfully saved, False otherwise

    Raises:
        ValueError: If workspace_id is not a string or workspace_data is not a dict
    """
    # Validate workspace_id type
    if not isinstance(workspace_id, str):
        raise ValueError("workspace_id must be a string")

    # Validate workspace_data type
    if not isinstance(workspace_data, dict):
        raise ValueError("workspace_data must be a dictionary")

    # Add last saved timestamp to workspace data for tracking purposes
    workspace_data["last_saved"] = datetime.now().isoformat(timespec="seconds")

    # Ensure the outputs directory exists before attempting to save
    ensure_outputs_directory_exists()

    # Construct the file path for the workspace JSON file
    file_path = OUTPUTS_DIRECTORY / f"{workspace_id}.json"

    try:
        # Write the workspace data to the JSON file with proper formatting
        with file_path.open("w") as file:
            json.dump(workspace_data, file, indent=2)

        logger.info(f"Workspace data successfully written to file: {file_path}")
        return True
    except Exception as e:
        # Log any errors that occur during file writing
        logger.error(f"Error writing workspace data to file {file_path}: {str(e)}")
        return False
