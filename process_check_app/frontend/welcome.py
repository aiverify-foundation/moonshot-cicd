import streamlit as st
from backend.map import get_map_color_mapping
from frontend.styles.welcome_styles import get_welcome_custom_css

# Path to welcome page image asset
WELCOME_IMAGE_PATH = "assets/images/welcome_image.png"


def click_back_button():
    """
    Navigate to the previous section by decrementing the section counter.

    Decrements the 'section' value in the session state to move back one section.

    Returns:
        None
    """
    st.session_state["section"] -= 1


def click_next_button():
    """
    Navigate to the next section by incrementing the section counter.

    Increments the 'section' value in the session state to advance one section.

    Returns:
        None
    """
    st.session_state["section"] += 1


def click_start_over_button() -> None:
    """
    Return to the home page by clearing the session state.

    Displays a confirmation dialog before resetting. Progress is automatically saved
    to persistent storage, so no data will be lost. Preserves the server_started flag
    when clearing session state.

    Returns:
        None
    """

    # Using st.dialog as a function decorator to create modal dialog
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
    Display navigation buttons for moving between sections.

    Shows a combination of Home, Back and Next buttons based on the current section:
    - Home button shown for sections >= 1
    - Back button shown for sections > 1
    - Next button shown for sections 1-4

    Adds a divider line above buttons for sections >= 1.

    Returns:
        None
    """
    if st.session_state["section"] >= 1:
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("---")

    # Create 4 columns with specific width ratios for button layout
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
        # Only show Next button for sections 1-4
        if st.session_state["section"] < 5 and st.session_state["section"] >= 1:
            st.button(
                "Next →",
                on_click=click_next_button,
                use_container_width=True,
            )


def welcome():
    """
    Display the welcome/introduction page for the AI Verify Process Checklist.

    Renders a comprehensive introduction page that includes:
    - Overview of the testing framework and its purpose
    - Target audience descriptions (AI owners, compliance teams, auditors)
    - List of 11 AI governance principles covered
    - Links to mapped international frameworks (NIST, ISO, Hiroshima Process)
    - Framework mapping indicators/badges
    - Information about technical testing capabilities

    Applies custom styling for headers and framework badges.
    Includes navigation controls at the bottom.

    Returns:
        None
    """
    # Apply custom purple styling for headers and cards
    st.markdown(get_welcome_custom_css(), unsafe_allow_html=True)

    st.write(
        """
        ### AI Verify Testing Framework for Generative AI - Process Checks
        This tool helps you assess and document the responsible AI practices that you have implemented in deploying
        your Generative AI application, and generate a summary report.

        ### How can the Testing Framework and Generated Report help companies?
    """
    )

    # Display welcome image
    st.image(WELCOME_IMAGE_PATH, use_container_width=True)

    st.write(
        """
        ### Who should use this tool?
        - **AI Application Owners / Developers** looking to demonstrate and document responsible AI governance practices

        - **Internal Compliance Teams** looking to ensure responsible AI practices have been implemented

        - **External Auditors** looking to validate your clients' implementation of responsible AI practices

        ### About the Testing Framework Process Checks
        The testing framework covers responsible AI practices and measures that are aligned with 11 internationally
        recognised AI governance principles:


        1.	Transparency
        2.	Explainability
        3.	Repeatability / Reproducibility
        4.	Safety
        5.	Security
        6.	Robustness
        7.	Fairness
        8.	Data Governance
        9.	Accountability
        10.	Human Agency and Oversight
        11.	Inclusive Growth, Societal and Environmental Well-being


        The processes in the testing framework are mapped to the following international frameworks:
        - [U.S. National Institute of Standards and Technology  Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile (US NIST AI RMF)](https://go.gov.sg/crosswalk-aivtfxairmf-genaiprofile)
        - [ISO/IEC 42001: 2023 - AI Management System](https://go.gov.sg/crosswalk-aivtf-iso42001)
        - [Hiroshima Process International Code of Conduct for Organizations Developing Advanced AI Systems (Hiroshima Process CoC)](https://go.gov.sg/crosswalk-aivtf-coc)
    """  # noqa: E501
    )

    st.markdown(
        f"""
        AI Verify processes that are mapped to these frameworks will have respective labels next to them e.g.,
        {"".join(f":{color}-badge[{name}]" for color, name in get_map_color_mapping().items())}
        """
    )

    st.write(
        """
        ### Technical Testing for Generative AI Applications
        In the process checks, references were made to conduct technical tests on the Generative AI applications.
        These can be achieved through the use of technical testing tools such as Project Moonshot.


        Only results from the technical tests conducted using Project Moonshot can be uploaded into this tool to be
        included in the summary report. Access Project Moonshot [here](https://github.com/aiverify-foundation).
        """  # noqa: E501, W291, W293
    )

    # Add navigation controls at bottom of page
    display_navigation_buttons()
