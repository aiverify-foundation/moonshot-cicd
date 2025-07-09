def get_main_styles() -> str:
    """
    Get the main application styles.

    Returns:
        str: CSS styles for the main application components.
    """
    return """
    <style>
    /* Base typography */
    h1 {
        margin-bottom: 0.5rem !important;
    }
    
    /* Content blocks */
    .pc-description {
        font-size: 1rem;
        color: #4b5563;
        line-height: 1.5;
        margin-bottom: 1rem;
        padding: 0.75rem;
        background-color: #f9fafb;
        border-radius: 6px;
        border-left: 4px solid #6b7280;
    }
    
    /* Layout adjustments */
    .element-container {
        margin-bottom: 0.5rem !important;
    }

    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background-color: #3b82f6 !important;
    }
    </style>
    """  # noqa: W293


def get_process_check_styles() -> str:
    """
    Get styles for the process checks components.

    Returns:
        str: CSS styles for all process check UI elements.
    """
    return """
    <style>
    /* Containers */
    .pc-outcome {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        background-color: white;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    /* Typography */
    .pc-outcome-title {
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 1rem;
        padding: 0.5rem;
        border-radius: 4px;
    }
    
    .pc-process {
        border: 1px solid #f0f0f0;
        border-radius: 4px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .pc-id-tag {
        display: inline-block;
        background-color: #f3f4f6;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 0.9rem;
        font-weight: 600;
        color: #4b5563;
        margin-bottom: 12px;
    }
    
    .pc-evidence-tag {
        display: inline-block;
        background-color: #f3f4f6;
        border-radius: 4px;
        padding: 3px 6px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #4b5563;
        margin-bottom: 8px;
    }
    
    /* Form elements */
    textarea {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        transition: all 0.2s ease-in-out !important;
    }
    textarea:hover {
        background-color: #f9fafb !important;
        border: 2px solid #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
    }
    textarea:focus {
        background-color: #ffffff !important;
        border: 2px solid #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* Streamlit-specific */
    [data-testid="column"] {
        border: 1px dashed #e0e0e0;
        border-radius: 5px;
        padding: 10px;
    }
    </style>
    """  # noqa: W293


def get_process_check_density_styles() -> str:
    """
    Get styles that create a more compact layout for process checks.

    Returns:
        str: CSS styles that reduce spacing between process check elements for a denser UI.
    """
    return """
    <style>
    /* Layout adjustments */
    .element-container {
        margin-bottom: 0.25rem !important;
    }
    
    [data-testid="stVerticalBlockBorderWrapper"] {
        padding-top: 0.5rem !important;
    }
    
    /* Element spacing */
    .pc-id-tag {
        margin-bottom: 6px !important;
        margin-top: 0 !important;
    }
    
    .pc-id-tag:first-of-type {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    .pc-outcome-title {
        margin-bottom: 0.5rem !important;
        padding: 0.25rem !important;
        padding-top: 0 !important;
    }
    
    .pc-evidence-tag {
        margin-bottom: 4px !important;
    }
    
    /* Form elements */
    textarea {
        padding: 4px !important;
    }
    
    /* Other elements */
    hr {
        margin: 12px 0 !important;
    }
    
    [data-testid="stVerticalBlockBorderWrapper"] > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    </style>
    """  # noqa: W293


def get_action_buttons_styles() -> str:
    """
    Get styles for the action buttons section.

    Returns:
        str: CSS styles for the workspace info and action buttons area.
    """
    return """
    <style>
    /* Button container styling */
    .button-container [data-testid="column"] {
        border: none !important;
        padding: 5px !important;
        padding-top: 0 !important;
    }
    
    /* Workspace info styling */
    .workspace-info {
        display: flex;
        flex-direction: column;
        margin: 0 !important;
        padding: 0 !important;
        height: 100%;
    }
    
    .workspace-id {
        font-family: monospace;
        font-weight: 600;
        font-size: 0.95rem;
        margin-right: 15px;
        background-color: #f3f0ff;
        padding: 2px 6px;
        border-radius: 4px;
        color: #6200ee;
    }
    
    /* Target the horizontal line to reduce padding */
    hr {
        margin-top: 0 !important;
        margin-bottom: 10px !important;
    }
    </style>
    """  # noqa: W293
