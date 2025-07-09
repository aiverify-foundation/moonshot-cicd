import re
from datetime import datetime

import bleach
import streamlit as st
from backend.actions_components.actions_component import create_actions_component
from backend.cards_component.cards_component import create_component
from backend.map import get_map_color_mapping, load_map_data
from backend.spreadsheet import export_excel, read_principles_from_excel
from backend.workspace import save_workspace
from frontend.styles.process_check_styles import (
    get_main_styles,
    get_process_check_density_styles,
    get_process_check_styles,
)
from streamlit_scroll_to_top import scroll_to_here

# Global variable for the reference Excel file path
REFERENCE_EXCEL_FILE_PATH = "assets/references/aivtf-excel.xlsx"

# Implementation choices for process checks
IMPLEMENTATION_CHOICES = ("Yes", "No", "N/A")


class ProcessCheck:
    """
    Main class for handling process check functionality.

    This class manages the loading, display, and interaction with process checks
    based on principles data loaded from an Excel file. It provides functionality for:
    - Loading and initializing process check data
    - Displaying the process check interface
    - Handling user interactions and responses
    - Managing progress tracking
    - Supporting import/export of process check data
    """

    def __init__(self):
        """
        Initialize the ProcessCheck class and load principles data.

        This method handles two scenarios:
        1. If imported Excel principles data exists in the session state:
            - Loads that data into self.principles_data
            - Removes existing process checks from workspace data
            - Clears the imported data from session state
        2. Otherwise:
            - Loads principles data from the reference Excel file specified by REFERENCE_EXCEL_FILE_PATH
        """
        if st.session_state.get("imported_excel_principles_data", {}):
            self.principles_data = st.session_state["imported_excel_principles_data"]
            st.session_state["workspace_data"].pop("process_checks", None)
            st.session_state["imported_excel_principles_data"] = {}
        else:
            self.principles_data = read_principles_from_excel(REFERENCE_EXCEL_FILE_PATH)

    def _filter_principle_checks(self, principle_key: str) -> dict:
        """
        Filter process checks for a specific principle.

        Args:
            principle_key: The key identifying the principle to filter for.

        Returns:
            dict: Dictionary of process checks filtered for the specified principle.
        """
        principle_checks = {}
        for outcome_id, processes in st.session_state["workspace_data"][
            "process_checks"
        ].items():
            principle_processes = {
                process_id: process_info
                for process_id, process_info in processes.items()
                if process_info["principle_key"] == principle_key
            }

            if principle_processes:
                principle_checks[outcome_id] = principle_processes

        return principle_checks

    def _get_progress_data(self) -> tuple:
        """
        Calculate progress metrics for the progress bar.

        Returns:
            tuple: Contains (progress_ratio, progress_message) where:
                - progress_ratio (float): Ratio of answered questions to total questions (0-1)
                - progress_message (str): Formatted message showing progress statistics
        """
        progress_data = st.session_state["workspace_data"]["progress_data"]
        total_questions = progress_data.get("total_questions", 0)
        answered_questions = progress_data.get("total_answered_questions", 0)

        progress_ratio = (
            answered_questions / total_questions if total_questions > 0 else 0
        )
        percentage = int(progress_ratio * 100)
        progress_message = f"Overall Progress: {answered_questions} of {total_questions} questions answered ({percentage}%)"  # noqa: E501

        return progress_ratio, progress_message

    def _group_process_checks_by_outcome(
        self, sorted_checks: list, principle_key: str
    ) -> dict:
        """
        Group process checks by their outcome ID and prepare the data structure for each check.

        Args:
            sorted_checks: List of tuples (process_id, process_data) containing process check information
            principle_key: String identifier for the principle these checks belong to

        Returns:
            dict: Grouped process checks by outcome ID, with each process containing complete metadata
        """
        outcome_groups = {}
        all_keys = self.get_all_process_check_keys()
        for process_id, process_data in sorted_checks:
            outcome_id = process_data.get("outcome_id", "")
            if not outcome_id:
                continue
            if outcome_id not in outcome_groups:
                outcome_groups[outcome_id] = []
            # Build process_info dynamically
            process_info = {k: process_data.get(k, "") for k in all_keys}

            # Check if implementation value is in IMPLEMENTATION_CHOICES
            if (
                "implementation" in process_info
                and process_info["implementation"] not in IMPLEMENTATION_CHOICES
            ):
                process_info["implementation"] = None

            process_info["principle_key"] = principle_key
            process_info["process_id"] = process_id
            outcome_groups[outcome_id].append(process_info)
        return outcome_groups

    def _merge_imported_implementation_data(
        self, import_excel_file
    ) -> tuple[dict, str, bool]:
        """
        Merge implementation and elaboration values from an imported Excel file with existing principles data.

        Args:
            import_excel_file: The Excel file containing implementation data to merge

        Returns:
            tuple: Contains (merged_data, error_message, success_flag) where:
                - merged_data (dict): The merged principles data if successful
                - error_message (str): Error message if merge failed, empty string if successful
                - success_flag (bool): True if merge was successful, False otherwise
        """
        self.uploaded_file_data = read_principles_from_excel(import_excel_file)
        if not self.uploaded_file_data:
            return (
                {},
                (
                    "We were unable to load the principles data from your file. "
                    "Please ensure you have selected a valid Excel file in the correct format and try again."
                ),
                False,
            )

        # Create a deep copy of the current principles data
        updated_principles_data = self.principles_data.copy()

        # Dynamically determine fields to compare (excluding implementation and elaboration)
        fields_to_compare = self.get_all_process_check_keys()
        fields_to_compare = [
            k for k in fields_to_compare if k not in ("implementation", "elaboration")
        ]

        # Iterate through each principle in the uploaded data
        for principle_key, principle_data in self.uploaded_file_data.items():
            if principle_key not in updated_principles_data:
                continue

            # Get the process checks for this principle
            uploaded_checks = principle_data.get("process_checks", {})
            current_checks = updated_principles_data[principle_key].get(
                "process_checks", {}
            )

            # Iterate through each process check
            for check_id, check_data in uploaded_checks.items():
                if check_id not in current_checks:
                    continue

                # Get the current check data
                current_check = current_checks[check_id]

                # Check if all fields match
                if all(
                    check_data.get(field) == current_check.get(field)
                    for field in fields_to_compare
                ):
                    current_check["implementation"] = check_data.get("implementation")
                    current_check["elaboration"] = check_data.get("elaboration")

        return updated_principles_data, "", True

    def _prepare_principles_data_with_progress(self) -> dict:
        """
        Prepare principles data with progress information for the component.

        Returns:
            dict: Principles data with added progress metrics including:
                - total_checks: Total number of checks for each principle
                - answered_checks: Number of answered checks for each principle
        """
        principles_data_with_progress = {}
        progress_data = st.session_state["workspace_data"]["progress_data"][
            "principles"
        ]

        for principle_key, principle_data in self.principles_data.items():
            # Make a shallow copy of the principle data
            principle_copy = principle_data.copy()

            # Add progress metrics if available
            if principle_key in progress_data:
                principle_stats = progress_data[principle_key]
                principle_copy.update(
                    {
                        "total_checks": principle_stats["principle_total"],
                        "answered_checks": principle_stats["principle_answered"],
                    }
                )
            principles_data_with_progress[principle_key] = principle_copy

        return principles_data_with_progress

    def _render_evidence_section(self, evidence_type: str, evidence: str) -> None:
        """
        Render the evidence section of a process.

        Args:
            evidence_type: Description of the evidence type expected for this process check
            evidence: Detailed description of what evidence should be provided
        """
        if evidence_type:
            st.markdown(
                '<div class="pc-evidence-tag">Evidence Type</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f"{evidence_type}",
                unsafe_allow_html=True,
            )

        if evidence:
            # Reduce vertical spacing
            st.markdown(
                '<div style="margin-top: 6px;"></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="pc-evidence-tag">Evidence</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f"{evidence}",
                unsafe_allow_html=True,
            )

    def _render_implementation_section(
        self, process_id: str, process_info: dict, outcome_id: str, outcome: str
    ) -> None:
        """
        Render the implementation status and elaboration section of a process.

        Args:
            process_id: The ID of the process being rendered
            process_info: Dictionary containing process information including current implementation status
            outcome_id: The ID of the parent outcome this process belongs to
            outcome: The description of the parent outcome
        """
        impl_col, elab_col = st.columns([1, 2], gap="small")

        with impl_col:
            st.markdown(
                "<div style='font-weight: 600; margin-bottom: 4px;'>Implemented?</div>",
                unsafe_allow_html=True,
            )

            # Get current value from session state if exists
            current_value = None
            if process_info["implementation"] is not None:
                options = list(IMPLEMENTATION_CHOICES)
                current_value = options.index(process_info["implementation"])

            is_implemented = st.radio(
                f"Implementation Status for {process_id}",
                options=list(IMPLEMENTATION_CHOICES),
                horizontal=True,
                label_visibility="collapsed",
                index=current_value,
            )

            # Check if the implementation status has changed
            previous_status = process_info["implementation"]

            # Update the session state
            st.session_state["workspace_data"]["process_checks"][outcome_id][
                process_id
            ]["implementation"] = is_implemented

            # If the status has changed, set refresh flag
            if previous_status != is_implemented:
                st.session_state["needs_refresh"] = True

        with elab_col:
            st.markdown(
                "<div style='font-weight: 600; margin-bottom: 4px;'>Elaboration:</div>",
                unsafe_allow_html=True,
            )

            # Get current value from session state
            current_elaboration = process_info["elaboration"] or ""

            elaboration = st.text_area(
                f"Elaboration for {process_id}",
                value=current_elaboration,
                placeholder="It is a good practice to provide reasons if 'No' or 'N/A' is selected. You can also provide elaborations if 'Yes' is selected e.g. location of evidence.",  # noqa: E501
                height=75,
                label_visibility="collapsed",
            )

            # Update the session state
            st.session_state["workspace_data"]["process_checks"][outcome_id][
                process_id
            ]["elaboration"] = elaboration

    def _render_map_badges_native(self, process_map_data: list) -> None:
        """
        Render colored badges for mapped governance framework items.

        Args:
            process_map_data: List containing map data with color keys and framework items to be displayed as badges
        """
        if not process_map_data:
            return

        color_mapping = get_map_color_mapping()
        badges_markdown = ""

        for color in process_map_data:
            if not color:
                continue

            framework_name = color_mapping.get(color, "")
            badge_text = f"{framework_name}" if framework_name else color
            badges_markdown += f":{color}-badge[{badge_text}] "

        if badges_markdown:
            st.markdown(badges_markdown)

    def _render_outcome_container(
        self, outcome_id: str, processes: dict, map_data: dict
    ) -> None:
        """
        Render a container for a specific outcome and its processes.

        Args:
            outcome_id: The ID of the outcome to render
            processes: Dictionary of processes associated with this outcome
            map_data: Dictionary containing mapping data for governance frameworks
        """
        with st.container(border=True):
            # Apply compact spacing styles
            st.markdown(get_process_check_density_styles(), unsafe_allow_html=True)

            # Get the outcome from the first process in the group
            first_process = next(iter(processes.values()))
            outcome = first_process["outcomes"]

            # Display outcome ID and header with reduced spacing
            st.markdown(
                f"""
            <div>
                <div class="pc-id-tag" style="margin-bottom: 4px;">Outcome {outcome_id}</div>
                <div class="pc-outcome-title">{outcome}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Display each process
            process_ids = list(processes.keys())
            for i, process_id in enumerate(process_ids):
                process_info = processes[process_id]
                process_map_data = map_data.get(process_id, [])
                self._render_process(
                    process_id, process_info, outcome_id, outcome, process_map_data
                )

                # Add horizontal line between processes (not after the last one)
                if i < len(process_ids) - 1:
                    st.markdown(
                        "<hr style='margin-top: 8px !important; margin-bottom: 8px !important;'>",
                        unsafe_allow_html=True,
                    )

    def _render_process(
        self,
        process_id: str,
        process_info: dict,
        outcome_id: str,
        outcome: str,
        process_map_data: list,
    ) -> None:
        """
        Render a single process with its details and input fields.

        Args:
            process_id: The ID of the process to render
            process_info: Dictionary containing process information including implementation status and elaboration
            outcome_id: The ID of the parent outcome
            outcome: The description of the parent outcome
            process_map_data: List containing mapping data for governance frameworks related to this process
        """
        process_to_achieve_outcomes = process_info["process_to_achieve_outcomes"]
        evidence_type = process_info["evidence_type"]
        evidence = process_info["evidence"]

        # Process information header section
        id_col, badges_col = st.columns([2, 4])

        with id_col:
            # Display process ID
            st.markdown(
                f'<div class="pc-id-tag" style="margin-bottom: 4px;">Process {process_id}</div>',
                unsafe_allow_html=True,
            )

        with badges_col:
            # Render badges if map data exists
            if process_map_data:
                self._render_map_badges_native(process_map_data)

        # Create two columns for process and evidence information
        left_col, right_col = st.columns([1, 2], gap="small")

        with left_col:
            if process_to_achieve_outcomes:
                st.markdown(
                    f"{process_to_achieve_outcomes}",
                    unsafe_allow_html=True,
                )

        with right_col:
            self._render_evidence_section(evidence_type, evidence)

        # Reduce space between process description and implementation status
        st.markdown(
            '<div style="margin-top: 6px;"></div>',
            unsafe_allow_html=True,
        )

        # Implementation status and elaboration columns
        self._render_implementation_section(
            process_id, process_info, outcome_id, outcome
        )

    def display(self):
        """
        Display the main process check interface in the Streamlit app.

        This method orchestrates the display of all components including:
        - Instructions
        - Action buttons
        - Progress bar
        - Process check content pane
        """
        self.initialize_process_checks_data()
        self.display_instructions()
        self.render_action_buttons()

        # Add a separator and a gap before the progress bar
        st.markdown("---")
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        # Get the current process check completion statistics
        st.session_state["workspace_data"][
            "progress_data"
        ] = self.get_process_check_stats()

        self.render_progress_bar()
        self.render_process_checks_pane()

    def display_edit_form(self):
        """
        Display a form for editing app information.

        The form includes:
        - Application name input
        - Application description input
        - Save and Cancel buttons
        - Input validation and error handling
        """
        # Get current values from session state
        workspace_data = st.session_state["workspace_data"]
        current_app_name = workspace_data.get("app_name", "")
        current_app_description = workspace_data.get("app_description", "")

        # Create a form for editing
        with st.form("edit_app_info_form"):
            # Create input fields pre-filled with current values
            new_app_name = st.text_input(
                "Application Name",
                key="app_name",
                value=current_app_name,
                help="The name of the application will be reflected in the report generated after you complete the process checks and technical tests (optional)",  # noqa: E501
                max_chars=50,
            )

            new_app_description = st.text_area(
                "Application Description",
                key="app_description",
                value=current_app_description,
                help="Briefly describe the application being assessed, including its purpose, key features, and any relevant context. This will help provide a clearer understanding of the application for your stakeholders reading the report",  # noqa: E501
                max_chars=256,
                height=150,
            )

            # Create save and cancel buttons with consistent ordering
            col1, col2 = st.columns(2)
            with col1:
                save_button = st.form_submit_button(
                    "Save Changes", type="primary", use_container_width=True
                )
            with col2:
                cancel_button = st.form_submit_button(
                    "Cancel", use_container_width=True
                )

        # Handle form actions outside the form block
        if save_button:
            if new_app_name and new_app_description:
                # Sanitize inputs
                sanitized_app_name = bleach.clean(new_app_name.strip(), strip=True)
                sanitized_app_description = bleach.clean(
                    new_app_description.strip(), strip=True
                )

                if sanitized_app_name and sanitized_app_description:
                    # Update session state with new values
                    workspace_data["app_name"] = sanitized_app_name
                    workspace_data["app_description"] = sanitized_app_description

                    # Exit edit mode and refresh UI
                    st.session_state["edit_mode"] = False
                    st.session_state["needs_refresh"] = True
                    st.rerun()
                else:
                    st.error(
                        "Please enter both an application name and description to save changes."
                    )
            else:
                st.error(
                    "Please enter both an application name and description to save changes."
                )

        if cancel_button:
            # Exit edit mode without saving changes
            st.session_state["edit_mode"] = False
            st.rerun()

    def display_import_form(self) -> None:
        """
        Display a dialog for importing Excel files.

        The dialog includes:
        - File upload widget
        - Warning about data overwrite
        - Import and Cancel buttons
        - Error handling and success feedback
        """

        @st.dialog("Import from Excel")
        def import_dialog() -> None:
            st.write(
                "If you have worked on the process checks in an offline Excel file, you can import the file here to auto-populate the responses and generate a report."  # noqa: E501
            )
            st.warning(
                """
            Importing a new file will:
            - Completely overwrite your current progress and responses
            - Delete all existing implementation status selections
            - Remove any elaboration text you have entered

            This action cannot be undone. Make sure to export or backup your current data first if needed.
            """,
                icon="⚠️",
            )

            uploaded_file = st.file_uploader("Choose a file", type=["xlsx"])

            error_message_to_display = None
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "Import", use_container_width=True, disabled=uploaded_file is None
                ):
                    if uploaded_file is not None:
                        # Merge implementation data from the uploaded file
                        merged_data, error_msg, success = (
                            self._merge_imported_implementation_data(uploaded_file)
                        )

                        if success:
                            # Update principles data
                            st.session_state["imported_excel_principles_data"] = (
                                merged_data
                            )
                            st.session_state["workspace_data"]["process_checks"] = {}
                            st.rerun()
                        else:
                            error_message_to_display = error_msg
            with col2:
                if st.button("Cancel", use_container_width=True):
                    st.rerun()

            if error_message_to_display:
                st.error(error_message_to_display)

        # Call the dialog function to display it
        import_dialog()

    def display_instructions(self) -> None:
        """
        Display instructions for completing the process checklist.

        Shows an expandable section containing:
        - Overview of the process checks section
        - Instructions for answering questions
        - Information about auto-save functionality
        - Guidance on offline work using Excel export/import
        """
        with st.expander("Instructions", expanded=True):
            st.markdown(
                """
            - In this section, you will need to complete all the process checks questions in the 11 principles

            - Click on each principle to answer the process checks questions

            - For each process check question, select one of the following options: **Yes**, **No** or **Not Applicable**
                1.	**Yes**: If the process is implemented, you can provide supporting evidence
                2.	**No**: If the process is not implemented, provide reasons to show that the decision is a
                deliberate and considered one
                3.	**Not Applicable**: If the process does not apply to your application, you can provide reasons to
                show that the decision is a deliberate and considered one

            - **:violet[Auto-saved enabled: Your progress on the process checks will be saved automatically]**

            - Once you have completed all 11 principles, you can click the "Next" button to proceed to the next section

            - If you prefer to complete the process checks offline, you may use the "Export" button to export the
            current session into an Excel file. When you are ready to generate the Summary Report, use "Import" button
            to import the completed Excel file and continue with the rest of the steps.
            """  # noqa: E501
            )

    def get_all_process_check_keys(self):
        """
        Get all possible keys from process checks across all principles.

        Returns:
            list: List of all unique keys found in process checks data structures
        """
        keys = set()
        for principle in self.principles_data.values():
            for process in principle.get("process_checks", {}).values():
                keys.update(process.keys())
        return list(keys)

    def get_friendly_principle_name(self, principle_name: str) -> str:
        """
        Convert a principle name to a more user-friendly format.

        Args:
            principle_name: The original principle name with potential HTML entities

        Returns:
            str: A user-friendly version of the principle name with proper formatting and special case handling
        """
        # Mapping for HTML entity replacement and text normalization
        principles_mapping = {
            "10. Human agency": "10. Human agency & oversight",
            "11. Inclusive growth": "11. Inclusive growth, societal and environmental well-being",
        }

        # Replace HTML entities and normalize text if found in mapping
        if principle_name in principles_mapping:
            principle_name = principles_mapping[principle_name]

        # Clean and format the name
        name_str = str(principle_name).strip()
        name_without_prefix = re.sub(r"^\d+\.\s*", "", name_str)
        friendly_name = name_without_prefix.replace("_", " ").title()
        return friendly_name.strip()

    def get_process_check_stats(self) -> dict:
        """
        Calculate comprehensive statistics for process checks.

        Returns:
            dict: Dictionary containing:
                - total_questions: Total number of questions across all principles
                - total_answered_questions: Total number of answered questions
                - principles: Dictionary of per-principle statistics including:
                    - principle_total: Total questions for each principle
                    - principle_answered: Answered questions for each principle
        """
        stats = {"total_questions": 0, "total_answered_questions": 0, "principles": {}}

        # Initialize principle counters
        for principle_key in self.principles_data:
            process_checks = self.principles_data[principle_key].get(
                "process_checks", {}
            )
            principle_total = len(process_checks)

            stats["principles"][principle_key] = {
                "principle_total": principle_total,
                "principle_answered": 0,
            }
            stats["total_questions"] += principle_total

        # Skip counting answered if no workspace data
        if (
            "workspace_data" not in st.session_state
            or "process_checks" not in st.session_state["workspace_data"]
        ):
            return stats

        # Count answered questions from workspace data
        for processes in st.session_state["workspace_data"]["process_checks"].values():
            for process_info in processes.values():
                principle_key = process_info["principle_key"]

                # Check if implementation has a valid answer
                if process_info.get("implementation") in IMPLEMENTATION_CHOICES:
                    if principle_key in stats["principles"]:
                        stats["principles"][principle_key]["principle_answered"] += 1
                        stats["total_answered_questions"] += 1

        return stats

    def initialize_process_checks_data(self) -> None:
        """
        Initialize the process checks data in session state.

        This method:
        1. Creates the process_checks data structure if it doesn't exist
        2. Groups process checks by outcome ID
        3. Sorts outcomes and processes
        4. Stores the organized data in the session state
        """
        if "process_checks" not in st.session_state.get("workspace_data", {}):
            process_checks_data = {}

            # Iterate through all principles and their process checks
            for principle_key, principle_data in self.principles_data.items():
                process_checks = principle_data.get("process_checks", {})

                # Sort process checks by ID
                sorted_checks = sorted(process_checks.items(), key=lambda x: x[0])

                # Group process checks by outcome_id
                outcome_groups = self._group_process_checks_by_outcome(
                    sorted_checks, principle_key
                )

                # Sort outcome groups by version-style outcome_id keys
                sorted_outcome_ids = self.sort_versions(outcome_groups.keys())

                # Store in the data structure
                for outcome_id in sorted_outcome_ids:
                    if outcome_id:  # Only store if outcome is non-empty
                        if outcome_id not in process_checks_data:
                            process_checks_data[outcome_id] = {}

                        for process_info in outcome_groups[outcome_id]:
                            process_id = process_info["process_id"]
                            process_checks_data[outcome_id][process_id] = process_info

            # Store in session state
            st.session_state["workspace_data"]["process_checks"] = process_checks_data

    def render_action_buttons(self) -> None:
        """
        Render the action buttons for process checks using a custom component.

        Displays:
        - Application information with edit capability
        - Auto-save indicator
        - Export to Excel button
        - Import from Excel button
        """
        # Get data
        workspace_id = st.session_state.get("workspace_id", "")
        workspace_data = st.session_state["workspace_data"]
        app_name = workspace_data.get("app_name", "")
        app_description = workspace_data.get("app_description", "")

        # Initialize session state variables if they don't exist
        if "edit_mode" not in st.session_state:
            st.session_state["edit_mode"] = False

        # Create the component and get any action returned (only if not in edit mode)
        if st.session_state["edit_mode"]:
            # Display the edit form instead of the component
            self.display_edit_form()
        else:
            # Create two columns
            left_col, right_col = st.columns([3, 1])

            with left_col:
                action = create_actions_component(
                    workspace_id=workspace_id,
                    app_name=app_name,
                    app_description=app_description,
                )
                # Handle actions returned from the component
                if action == "edit":
                    # Enter edit mode
                    st.session_state["edit_mode"] = True
                    st.rerun()

            with right_col:
                # Create a container with custom CSS to make buttons the same width
                with st.container():
                    # Auto-save enabled indicator
                    st.markdown(
                        """
                        <div style="color: #2e7d32; font-size: 14px; margin-bottom: 10px; display: flex; align-items: center; justify-content: center;">
                            <span style="margin-right: 5px;">↻</span> Auto-save enabled
                        </div>
                        """,  # noqa: E501
                        unsafe_allow_html=True,
                    )

                    # Display last saved date if available
                    last_saved = st.session_state["workspace_data"]["last_saved"]
                    # Format the timestamp from ISO format to DDMMYY HHMMSS
                    try:
                        # Parse the ISO timestamp
                        dt = datetime.fromisoformat(last_saved)
                        # Format to DDMMYY HHMMSS
                        formatted_last_saved = dt.strftime("%d/%m/%y %H:%M:%S")
                    except (ValueError, TypeError):
                        # Fallback to original format if parsing fails
                        formatted_last_saved = last_saved

                    st.markdown(
                        f"""
                        <div style="color: #6b7280; font-size: 14px; margin-bottom: 70px; display: flex;
                        align-items: center; justify-content: center;">
                            Last saved: {formatted_last_saved}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Export button with cached data
                    st.download_button(
                        label="Export as Excel",
                        help=(
                            "Export the current process checks into an Excel file and work on it offline. "
                            "Once you've made your updates, you can import the file using the "
                            '"Import from Excel" button below to automatically populate your responses in the tool.'
                        ),
                        icon=":material/file_download:",
                        data=get_export_data(
                            REFERENCE_EXCEL_FILE_PATH,
                            st.session_state["workspace_data"]["process_checks"],
                        ),
                        file_name=f"process_checks_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.xlsx",
                        use_container_width=True,
                    )

                    # Import button with fixed label length
                    if st.button(
                        "Import from Excel",
                        help=(
                            "If you have worked on the process checks in an offline Excel file, "
                            "you can import the file here to auto-populate the responses and generate a report.\n\n"
                            "Please note that importing will override your current progress and responses. "
                            "To avoid losing any work, we recommend exporting your latest work before "
                            "importing a new file."
                        ),
                        icon=":material/file_upload:",
                        use_container_width=True,
                    ):
                        self.display_import_form()

    def render_process_checks(
        self, principle_name: str, principle_description: str, principle_key: str
    ) -> None:
        """
        Render the process checks for a principle.

        Args:
            principle_name: The user-friendly name of the principle.
            principle_description: The description of the principle.
            principle_key: The key identifying the current principle.
        """
        # Display header
        st.header(principle_name)

        # Add principle description below the header
        if principle_description:
            st.markdown(
                f'<div class="pc-description">{principle_description}</div>',
                unsafe_allow_html=True,
            )

        # Apply process check styles
        st.markdown(get_process_check_styles(), unsafe_allow_html=True)

        # Filter process checks for this principle
        principle_checks = self._filter_principle_checks(principle_key)

        # Load map data
        map_data = load_map_data()

        # Display each outcome group
        for outcome_id, processes in principle_checks.items():
            if (
                outcome_id and processes
            ):  # Only display if outcome is non-empty and has processes
                self._render_outcome_container(outcome_id, processes, map_data)

    def render_process_checks_pane(self) -> None:
        """
        Render the principles content pane in the Streamlit app.

        Creates a two-column layout with:
        - Left column: Principle selection cards showing progress
        - Right column: Detailed process checks for selected principle with navigation

        The component maintains state between renders using st.session_state["cards_component"]
        to track the currently selected principle index.

        Handles navigation between principles via Previous/Next buttons and card selection.
        Automatically saves workspace data and refreshes the page when needed.
        """
        if "scroll_to_top" not in st.session_state:
            st.session_state["scroll_to_top"] = False

        # Apply main styles
        st.markdown(get_main_styles(), unsafe_allow_html=True)

        # Initialize cards component state if not already set
        if "cards_component" not in st.session_state:
            st.session_state["cards_component"] = 0

        # Get principle names and progress data
        principles_data_with_progress = self._prepare_principles_data_with_progress()
        friendly_principles_names = [
            self.get_friendly_principle_name(name)
            for name in self.principles_data.keys()
        ]

        # Create two-column layout
        left_col, right_col = st.columns([1, 3], gap="small")
        with left_col:
            # Render principle selection cards and handle selection
            selected_index = create_component(
                friendly_principles_names,
                principles_data_with_progress,
                st.session_state["cards_component"],
                key=f"cards_{st.session_state['cards_component']}",
            )
            if (
                selected_index is not None
                and selected_index != st.session_state["cards_component"]
            ):
                st.session_state["cards_component"] = selected_index
                st.rerun()

        with right_col:
            if st.session_state["scroll_to_top"]:
                scroll_to_here(0, key="top")
                st.session_state["scroll_to_top"] = False

            # Get currently selected principle
            current_index = st.session_state["cards_component"]
            if 0 <= current_index < len(friendly_principles_names):
                principle_key = list(self.principles_data.keys())[current_index]
                principle_name = friendly_principles_names[current_index]
                principle_description = self.principles_data[principle_key].get(
                    "principle_description", ""
                )

                # Display process checks for selected principle
                self.render_process_checks(
                    principle_name, principle_description, principle_key
                )

            # Add Previous/Next navigation buttons
            nav_col1, _, nav_col3 = st.columns([2, 4, 2])
            with nav_col1:
                if st.button(
                    ":material/arrow_back: Previous Principle",
                    use_container_width=True,
                    disabled=st.session_state["cards_component"] == 0,
                ):
                    st.session_state["cards_component"] = max(
                        0, st.session_state["cards_component"] - 1
                    )
                    st.session_state["scroll_to_top"] = True
                    st.rerun()
            with nav_col3:
                if st.button(
                    "Next Principle :material/arrow_forward:",
                    use_container_width=True,
                    disabled=st.session_state["cards_component"]
                    == len(friendly_principles_names) - 1,
                ):
                    st.session_state["cards_component"] = min(
                        len(friendly_principles_names) - 1,
                        st.session_state["cards_component"] + 1,
                    )
                    st.session_state["scroll_to_top"] = True
                    st.rerun()

        # Save workspace data
        save_workspace(
            st.session_state["workspace_id"], st.session_state["workspace_data"]
        )

        # Handle page refresh if needed
        if st.session_state.get("needs_refresh", False):
            st.session_state["needs_refresh"] = False
            st.rerun()

    def render_progress_bar(self) -> None:
        """
        Render a progress bar to indicate the completion status of questions.
        """
        progress_ratio, progress_message = self._get_progress_data()
        self.progress_bar = st.progress(progress_ratio, progress_message)

    def sort_versions(self, versions) -> list:
        """
        Sort a list of version numbers in human-friendly version order.

        Args:
            versions: List of version strings to sort.

        Returns:
            list: Sorted list of version strings.
        """
        return sorted(versions, key=lambda v: [int(part) for part in str(v).split(".")])


def click_back_button():
    """
    Decrement the 'section' in the session state to navigate to the previous section.
    """
    st.session_state["section"] -= 1


def click_next_button():
    """
    Increment the 'section' in the session state to navigate to the next section.
    """
    st.session_state["section"] += 1


def click_start_over_button() -> None:
    """
    Return to the home page by clearing the session state.

    Displays a confirmation dialog before returning to the home page.
    Progress is automatically saved, so no data will be lost.

    Returns:
        None
    """

    # Using st.dialog as a function decorator
    @st.dialog("Return to Home Page")
    def confirm_reset_dialog() -> None:
        st.write(
            "Do you want to return to Home Page? Don't worry, your progress has been saved."
        )
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Yes, start over", use_container_width=True):
                server_started = st.session_state.get("server_started", False)
                st.session_state.clear()
                st.session_state["server_started"] = server_started
                st.rerun()

        with col2:
            if st.button("No, cancel", use_container_width=True):
                st.rerun()

    # Call the dialog function to display it
    confirm_reset_dialog()


def display_navigation_buttons() -> None:
    """
    Display navigation buttons for moving between sections of the process checks.

    Shows Back, Start Over, and Next buttons as appropriate based on the current section.
    Only displays navigation controls when the user has progressed beyond the triage section.
    The Next button is disabled if not all questions are answered.
    """
    if st.session_state["section"] >= 1:
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("---")

    # Regular navigation buttons
    col1, _, col2, col3 = st.columns([2, 6, 2, 2])
    with col1:
        if st.session_state["section"] >= 1:
            st.button(
                ":material/home: Home",
                on_click=click_start_over_button,
                use_container_width=True,
            )
    with col2:
        if st.session_state["section"] > 1:
            st.button("← Back", on_click=click_back_button, use_container_width=True)
    with col3:
        # Display the Next button for sections 1-4
        if 1 <= st.session_state["section"] < 5:
            # Get progress data from session state
            progress_data = st.session_state["workspace_data"].get("progress_data", {})
            total_questions = progress_data.get("total_questions", 0)
            total_answered = progress_data.get("total_answered_questions", 0)

            # Disable Next if not all questions are answered
            st.button(
                "Next →",
                on_click=click_next_button,
                use_container_width=True,
                disabled=(total_answered != total_questions),
                help=(
                    "Please answer all questions before proceeding."
                    if total_answered != total_questions
                    else None
                ),
            )


def display_process_check() -> None:
    """
    Display the process check interface and handle user interactions.

    This function manages the workflow for process checks:
    1. Ensures a workspace exists or guides the user to create one
    2. Initializes the ProcessCheck component
    3. Displays the interface with all necessary components
    """
    # Initialize and display the process checks interface
    process_check = ProcessCheck()
    process_check.display()

    # Display the navigation buttons
    display_navigation_buttons()


@st.cache_data
def get_export_data(reference_file_path, process_checks_data):
    """
    Generate and cache Excel export data from process checks.

    This function uses Streamlit's caching decorator to avoid regenerating the Excel file
    unless the inputs change. It takes a reference Excel template and process check data
    and returns the bytes of the generated Excel file.

    Args:
        reference_file_path (str): Path to the Excel template file used as reference
        process_checks_data (dict): Dictionary containing process check responses and data

    Returns:
        bytes: The generated Excel file content as bytes
    """
    return export_excel(reference_file_path, process_checks_data)
