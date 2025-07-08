def get_started_styles() -> str:
    """
    Get styles for the Getting Started page components.

    Returns:
        str: CSS styles for purple headers and disabled textarea resizing.
    """
    return """
    <style>
    h3 {
        color: #4C1D95 !important;  /* Purple color */
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }

    textarea {
        resize: none !important;
    }
    </style>
    """
