import http.server
import socketserver
import threading

import streamlit as st
from frontend.generate_report import display_generate_report
from frontend.get_started import getting_started
from frontend.process_check import display_process_check
from frontend.triage import triage
from frontend.upload_result import upload_result
from frontend.welcome import welcome
from streamlit.logger import get_logger

logger = get_logger(__name__)


def apply_custom_css():
    """
    Apply custom CSS styles to the Streamlit application.

    Hides the default Streamlit header and footer, and applies custom styles
    for the sections bar to enhance the user interface.

    Returns:
        None
    """
    hide_decoration_bar_style = """<style>header {visibility: hidden;}</style>"""
    st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

    hide_streamlit_footer = """<style>#MainMenu {visibility: hidden;}
                            footer {visibility: hidden;}</style>"""
    st.markdown(hide_streamlit_footer, unsafe_allow_html=True)

    st.markdown(
        """
        <style>
        .container {
            display: flex;
            align-items: flex-start;
            justify-content: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin-top: -100px;
            margin-bottom: 60px;
            position: relative;
        }
        .section {
            text-align: center;
            position: relative;
            width: 120px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .box {
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: bold;
            border-radius: 50%;
            position: relative;
            z-index: 1;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .box.active {
            background-color: #8a2be2;
            color: white;
            box-shadow: 0 4px 8px rgba(138,43,226,0.3);
        }
        .box.inactive {
            background-color: #f0f0f0;
            color: #757575;
            border: 2px solid #e0e0e0;
        }
        .line-container {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-left: -10px;
            margin-right: -10px;
            width: 100px;
            height: 50px;
        }
        .line {
            width: 100%;
            height: 3px;
            background-color: #e0e0e0;
            position: relative;
            transition: all 0.3s ease;
        }
        .line.completed {
            background-color: #8a2be2;
        }
        .label {
            width: 120px;
            margin-top: 15px;
            font-size: 14px;
            font-weight: 500;
            color: #757575;
        }
        .label.completed {
            font-weight: 600;
            color: #333333;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )


def display_sections_bar():
    """
    Render the sections bar at the top of the application.

    Visually represents the application sections, highlighting the current section
    and completed sections to guide the user through the process. Only displays
    when the current section is 1 or greater.

    Returns:
        None
    """
    section = st.session_state.get("section")
    if (
        section is not None and section >= 1
    ):  # Only display if the current section is greater than or equal to 1
        st.markdown(
            f"""
            <div class="container">
                <div class="section">
                    <div class="box {'active' if section >= 1 else 'inactive'}">1</div>
                    <div class="label {'completed' if section >= 1 else ''}">Welcome</div>
                </div>
                <div class="line-container">
                    <div class="line {'completed' if section > 1 else ''}"></div>
                </div>
                <div class="section">
                    <div class="box {'active' if section >= 2 else 'inactive'}">2</div>
                    <div class="label {'completed' if section >= 2 else ''}">Getting Started</div>
                </div>
                <div class="line-container">
                    <div class="line {'completed' if section > 2 else ''}"></div>
                </div>
                <div class="section">
                    <div class="box {'active' if section >= 3 else 'inactive'}">3</div>
                    <div class="label {'completed' if section >= 3 else ''}">Complete Process Checks</div>
                </div>
                <div class="line-container">
                    <div class="line {'completed' if section > 3 else ''}"></div>
                </div>
                <div class="section">
                    <div class="box {'active' if section >= 4 else 'inactive'}">4</div>
                    <div class="label {'completed' if section >= 4 else ''}">Upload Technical Tests Results</div>
                </div>
                <div class="line-container">
                    <div class="line {'completed' if section > 4 else ''}"></div>
                </div>
                <div class="section">
                    <div class="box {'active' if section >= 5 else 'inactive'}">5</div>
                    <div class="label {'completed' if section >= 5 else ''}">Generate Report</div>
                </div>
            </div>
        """,
            unsafe_allow_html=True,
        )


def display_current_section():
    """
    Display the content for the current section based on the session state.

    Shows the appropriate content for the current section based on the section value
    in the session state, allowing users to navigate through the application seamlessly.

    Returns:
        None
    """
    section = st.session_state.get("section")
    if section == 0:
        triage()  # Display the triage section
    elif section == 1:
        welcome()  # Display the welcome section
    elif section == 2:
        getting_started()  # Display the getting started section
    elif section == 3:
        display_process_check()  # Display the process checks section
    elif section == 4:
        upload_result()  # Display the upload result section
    elif section == 5:
        display_generate_report()  # Display the generate report section


def set_custom_width_layout():
    """
    Configure the page layout with a custom width between "centered" and "wide".

    Sets the page title and applies custom CSS to adjust the container width
    for better content display.

    Returns:
        None
    """
    # Create a layout width between "centered" and "wide"
    st.set_page_config(
        page_title="AI Verify Process Checks Tool for Generative AI",
        layout="centered",  # Start with centered as base
        page_icon="assets/images/favicon.jpg",  # Set the favicon
    )

    # Apply custom CSS to make it wider than default centered, but not as wide as "wide"
    st.markdown(
        """
    <style>
    .block-container {
        max-width: 1000px;  # Adjust this value as needed (centered is ~730px, wide is ~1168px)
        padding-top: 1rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 3rem;
        margin: 0 auto;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def start_http_server():
    """Start a simple HTTP server on port 8000."""
    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()


def main():
    """
    Initialize the application and display the UI components.

    Sets up the session state for new sessions, configures the page layout,
    applies custom CSS, and renders the UI components including the sections bar,
    current section content, and navigation buttons.

    Returns:
        None
    """
    # Initialize the application if section is not set
    if "section" not in st.session_state:  # Check if section is not initialized
        logger.info("Initializing the application.")
        st.session_state["section"] = 0

    # Check if the server has already been started
    if "server_started" not in st.session_state:
        # Start the HTTP server in a new thread
        server_thread = threading.Thread(target=start_http_server)
        server_thread.daemon = (
            True  # This allows the program to exit even if the thread is running
        )
        server_thread.start()

        # Set the flag to indicate the server has been started
        st.session_state["server_started"] = True

    # Set the page layout and width
    set_custom_width_layout()

    # Apply custom CSS styles
    apply_custom_css()

    # Display the sections bar
    display_sections_bar()

    # Display the content for the current section
    display_current_section()


# Main execution
if __name__ == "__main__":
    main()
