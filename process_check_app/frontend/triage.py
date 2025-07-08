import streamlit as st
from backend.workspace import get_available_workspaces, initialize, load_workspace
from streamlit.logger import get_logger

logger = get_logger(__name__)


def apply_custom_styles():
    """
    Apply custom CSS styles for the triage page.

    Sets up styling for fonts, containers, headers, buttons, and dividers
    to create a consistent and visually appealing user interface.

    Returns:
        None
    """
    st.markdown(
        """
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Poppins:wght@600;700;800&display=swap');
        
        /* Main container styling */
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
            font-family: 'Inter', sans-serif;
        }
        
        /* Header styling */
        .main-header {
            font-family: 'Poppins', sans-serif;
            font-size: 3rem;
            font-weight: 700;
            text-align: center;
            margin: 2rem auto 6rem;  
            color: #1E3A8A;
            line-height: 1.2;
            letter-spacing: -0.5px;
            padding: 0 1rem;
        }
        
        /* Subtitle styling */
        .subtitle {
            font-family: 'Inter', sans-serif;
            font-size: 1.2rem;
            text-align: center;
            color: #4B5563;
            margin-bottom: 1.5rem;
            font-weight: 500;
            letter-spacing: -0.2px;
        }
        
        /* Button styling */
        .stButton button {
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            letter-spacing: 0.2px !important;
        }
        
        /* Divider styling */
        .custom-divider {
            display: flex;
            align-items: center;
            text-align: center;
            color: #6B7280;
            font-size: 1.1rem;
            margin: 3rem 0;
            font-family: 'Inter', sans-serif;
            font-weight: 500;
        }
        
        .custom-divider::before,
        .custom-divider::after {
            content: '';
            flex: 1;
            border-bottom: 2px solid #E5E7EB;
        }
        
        .custom-divider span {
            margin: 0 1rem;
            font-weight: 500;
        }
        </style>
    """,  # noqa: E501, W291, W293
        unsafe_allow_html=True,
    )


def display_continue_button(available_workspaces):
    """
    Display the button for continuing an existing workspace.

    Shows a divider followed by a button that opens a dialog to select
    a previously saved workspace. The button is disabled if no workspaces
    are available.

    Args:
        available_workspaces: list of available workspace dictionaries

    Returns:
        None
    """
    # Custom divider
    st.markdown(
        """
        <div class="custom-divider">
            <span>Or</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Second section with button for returning users
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "Continue Where You Left Off",
            type="secondary",
            use_container_width=True,
            disabled=len(available_workspaces) == 0,
        ):
            resume_workspace_dialog(available_workspaces)


def display_header():
    """
    Display the main header of the application.

    Renders the application title with custom styling using HTML markup.

    Returns:
        None
    """
    st.markdown(
        '<h1 class="main-header">Welcome to Process Checks for Generative AI</h1>',
        unsafe_allow_html=True,
    )


def display_logo():
    """
    Display the application logo.

    Creates a three-column layout and displays the logo in the middle column
    for proper centering and visual balance.

    Returns:
        None
    """
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("assets/images/aiverify_logo.png", width=700)  # Display logo


def display_new_process_button():
    """
    Display the button for starting a new process check.

    Creates a centered button that navigates to the first section of the application
    when clicked.

    Returns:
        None
    """
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "Start New Process Checks", type="primary", use_container_width=True
        ):
            st.session_state["section"] = 1
            st.rerun()


@st.dialog("Welcome Back!")
def resume_workspace_dialog(available_workspaces):
    """
    Dialog to select a workspace ID to resume from.

    Displays available workspaces for the user to select from and handles
    the resumption of the selected workspace.

    Args:
        available_workspaces: list of available workspace dictionaries

    Returns:
        None
    """
    # Display page content
    st.markdown(
        """
        We have saved your progress, so you can pick up right where you left off.

        You can review your previous answers and make any changes.
        """
    )

    # Extract workspace IDs for the selectbox
    available_ids = [workspace["workspace_id"] for workspace in available_workspaces]

    # Option to select from available IDs
    selected_id = st.selectbox(
        "Select your previous workspace",
        options=available_ids,
        index=None,
        placeholder="Dropdown to select Workspace ID",
    )

    st.write("")  # Add spacing

    # Create buttons for user actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "Resume",
            type="primary",
            use_container_width=True,
            disabled=not selected_id,
        ):
            if selected_id:
                # Load the full workspace data
                workspace_data = load_workspace(selected_id)
                if workspace_data is None:
                    st.error(
                        f"Could not load workspace data for ID: {selected_id}. Please select a different workspace."
                    )
                    return  # Prevent continuation if workspace data is None
                elif not workspace_data:  # Check if workspace_data is empty
                    logger.warning(
                        f"Workspace data for ID: {selected_id} is empty. You can still continue."
                    )
                # Update the session state with the selected ID and data
                initialize(selected_id, workspace_data)
                st.session_state["needs_resume"] = True
                st.session_state["section"] = 3
                st.rerun()

    with col2:
        if st.button("Cancel", type="secondary", use_container_width=True):
            st.rerun()


def triage():
    """
    Display the triage page for the AI Verify Testing Framework application.

    This function sets up the user interface, including custom styles, logo,
    headers, and buttons for navigation. It retrieves available workspaces
    and displays options for starting a new process check or continuing
    from a previous session.

    Returns:
        None
    """
    # Apply custom styles
    apply_custom_styles()

    # Display logo and header
    display_logo()
    display_header()

    # Add vertical space
    for _ in range(9):
        st.write("\n")

    # Get actual workspace data from files
    available_workspaces = get_available_workspaces()

    # Display buttons for new and returning users
    display_new_process_button()
    display_continue_button(available_workspaces)
