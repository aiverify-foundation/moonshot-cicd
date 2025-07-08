import os
from datetime import datetime

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from backend.principle_calculator import process_principle
from backend.report_validation import get_report_info
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Frame,
    FrameBreak,
    Image,
    KeepTogether,
    ListFlowable,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

"""
PDF Generator module for creating summary reports.

This module handles the generation of PDF reports including styling, layout and content.
It uses ReportLab to create professional looking documents with consistent branding.
"""

# Global file paths
GENERATED_REPORT_NAME = "summary_report.pdf"
OUTPUTS_DIRECTORY = "temp_report"
ASSETS_DIR = "assets"

IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
LOGO_PATH = os.path.join(IMAGES_DIR, "aiverify_logo.png")
LOGO_WHITE_PATH = os.path.join(IMAGES_DIR, "aiverify_logo_white.png")
BACKGROUND_IMAGE_PATH = os.path.join(IMAGES_DIR, "background_image.jpg")

FONTS_DIRECTORY = os.path.join(ASSETS_DIR, "fonts")
ROBOTO_REGULAR_PATH = os.path.join(FONTS_DIRECTORY, "Roboto-Regular.ttf")
ROBOTO_BOLD_PATH = os.path.join(FONTS_DIRECTORY, "Roboto-Bold.ttf")
ROBOTO_ITALIC_PATH = os.path.join(FONTS_DIRECTORY, "Roboto-Italic.ttf")

# Define a modern color palette
PRIMARY_COLOR = colors.HexColor("#1E5288")  # Deep blue
SECONDARY_COLOR = colors.HexColor("#D54E21")  # Accent orange
TERTIARY_COLOR = colors.HexColor("#3FB8AF")  # Teal
LIGHT_GRAY = colors.HexColor("#F5F5F5")  # Light gray for backgrounds
DARK_GRAY = colors.HexColor("#4A4A4A")  # For text
SUCCESS_COLOR = colors.HexColor("#4CAF50")  # Green for positive indicators
WARNING_COLOR = colors.HexColor("#FF9800")  # Orange for warnings
ERROR_COLOR = colors.HexColor("#F44336")  # Red for errors
COVER_COLOR = colors.white

# Register modern fonts if available, with fallbacks
try:
    # For custom/modern fonts - adjust paths as needed for your environment
    pdfmetrics.registerFont(TTFont("Roboto", ROBOTO_REGULAR_PATH))
    pdfmetrics.registerFont(TTFont("Roboto-Bold", ROBOTO_BOLD_PATH))
    pdfmetrics.registerFont(TTFont("Roboto-Italic", ROBOTO_ITALIC_PATH))
    BASE_FONT = "Roboto"
    BOLD_FONT = "Roboto-Bold"
    ITALIC_FONT = "Roboto-Italic"
except Exception:
    # Fallback to standard fonts if custom fonts aren't available
    BASE_FONT = "Helvetica"
    BOLD_FONT = "Helvetica-Bold"
    ITALIC_FONT = "Helvetica-Oblique"

# Register Montserrat ExtraBold font for cover page
try:
    MONT_EXTRA_BOLD_PATH = os.path.join(FONTS_DIRECTORY, "Montserrat-ExtraBold.ttf")
    pdfmetrics.registerFont(TTFont("Montserrat-ExtraBold", MONT_EXTRA_BOLD_PATH))
    COVER_FONT = "Montserrat-ExtraBold"
except Exception:
    COVER_FONT = "Helvetica-Bold"  # fallback


# Get default stylesheet and normal text style
styles = getSampleStyleSheet()
cover_title_style = ParagraphStyle(
    name="CoverTitle",
    fontName=COVER_FONT,
    fontSize=64,
    alignment=TA_LEFT,
    spaceAfter=24,
    textColor=COVER_COLOR,
    leading=72,
)
cover_company_name_style = ParagraphStyle(
    "CoverCompanyName",
    fontName=COVER_FONT,
    fontSize=20,
    spaceAfter=10,
    alignment=TA_LEFT,
    textColor=COVER_COLOR,
)
cover_date_generated_style = ParagraphStyle(
    "CoverDateGenerated",
    fontName=COVER_FONT,
    fontSize=16,
    spaceAfter=12,
    alignment=TA_LEFT,
    textColor=COVER_COLOR,
)
cover_subheader_style = ParagraphStyle(
    "CoverSubheader",
    fontName=COVER_FONT,
    fontSize=16,
    spaceAfter=8,
    alignment=TA_LEFT,
    textColor=COVER_COLOR,
)
text_style = ParagraphStyle(
    "TextStyle",
    parent=styles["Normal"],
    fontName=BASE_FONT,
    fontSize=9,
    leading=12,
    spaceAfter=6,
    alignment=TA_LEFT,
    textColor=DARK_GRAY,
)
header_text_style = ParagraphStyle(
    "HeaderStyle",
    parent=styles["Normal"],
    fontName=BOLD_FONT,
    fontSize=10,
    leading=13,
    spaceAfter=4,
    alignment=TA_LEFT,
    textColor=PRIMARY_COLOR,
)
subheader_text_style = ParagraphStyle(
    "SubheaderStyle",
    parent=styles["Normal"],
    fontName=BOLD_FONT,
    fontSize=9,
    leading=12,
    spaceAfter=4,
    alignment=TA_LEFT,
    textColor=SECONDARY_COLOR,
)
title_style = ParagraphStyle(
    name="Title",
    parent=styles["Title"],
    fontName=BOLD_FONT,
    fontSize=32,
    alignment=TA_LEFT,
    spaceAfter=24,
    textColor=PRIMARY_COLOR,
    leading=56,
)
company_name_style = ParagraphStyle(
    "CompanyNameStyle",
    parent=styles["Normal"],
    fontName=BOLD_FONT,
    fontSize=14,
    spaceAfter=10,
    alignment=TA_LEFT,
    textColor=DARK_GRAY,
)
date_generated_style = ParagraphStyle(
    "DateGeneratedStyle",
    parent=styles["Normal"],
    fontName=BASE_FONT,
    fontSize=12,
    spaceAfter=16,
    alignment=TA_LEFT,
    textColor=DARK_GRAY,
)


def get_display_principle_name(principle_name, multiline=False):
    """
    Formats a principle name for display, with special handling for certain principles.

    This function takes a principle name and returns a formatted display version. It provides
    special handling for two specific principles:
    - "inc growth" -> "Inclusive growth, societal and environmental well-being"
    - "human agency" -> "Human agency & oversight"

    For all other principles, it returns the original name unchanged.

    When multiline=True, it returns versions with line breaks suitable for chart display.

    Args:
        principle_name (str): The principle name to format. If None, returns empty string.
        multiline (bool, optional): Whether to return a multiline version for charts.
            Defaults to False.

    Returns:
        str: The formatted display name. For known principles, returns a standardized version.
            For unknown principles, returns the original name. Returns empty string if input is None.

    Examples:
        >>> get_display_principle_name("inc growth")
        'Inclusive growth, societal and environmental well-being'
        >>> get_display_principle_name("inc growth", multiline=True)
        'Inclusive Growth, \nSocietal and \nEnvironmental \nWell-being'
        >>> get_display_principle_name("Test Principle")
        'Test Principle'
    """
    if not principle_name:
        return ""

    principle_map = {
        "inc growth": {
            True: "Inclusive Growth, \nSocietal and \nEnvironmental \nWell-being",
            False: "Inclusive growth, societal and environmental well-being",
        },
        "human agency": {
            True: "Human Agency &\n Oversight",
            False: "Human agency & oversight",
        },
    }

    principle_name = principle_name.strip().lower()
    return principle_map.get(principle_name, {}).get(multiline, principle_name)


def add_background_image(canvas, doc):
    """
    Adds a background image to the first page of the PDF document.

    This function adds a background image that fills the entire first page of the document.
    The image will be scaled to match the page dimensions. It also draws the company logo
    on every page.

    Args:
        canvas (Canvas): The ReportLab canvas object to draw on
        doc (SimpleDocTemplate): The document object containing page information

    Note:
        - Uses background image from assets/background_image.png
        - Image will only be added to the first page (doc.page == 1)
        - Logo is drawn on every page
    """
    if doc.page == 1:
        canvas.saveState()
        width, height = letter
        background_image = Image(BACKGROUND_IMAGE_PATH, width=width, height=height)
        background_image.drawOn(canvas, 0, 0)
        canvas.restoreState()

        # Draw the logo on every page
        draw_logo(canvas, doc)


def add_page_number(canvas, doc):
    """
    Adds page numbers and header/footer elements to each page.

    This function adds page numbers, date, divider lines and logo to each page except
    the first page. The header contains a divider line and logo, while the footer
    contains the page number, date and another divider line.

    Args:
        canvas (Canvas): The ReportLab canvas object to draw on
        doc (SimpleDocTemplate): The document object containing page information
    """
    width, height = letter
    if doc.page > 1:
        # Add header with a subtle divider line
        canvas.saveState()
        canvas.setStrokeColor(LIGHT_GRAY)
        canvas.line(
            0.5 * inch, height - 0.75 * inch, width - 0.5 * inch, height - 0.75 * inch
        )

        # Add footer with page number and divider
        canvas.setStrokeColor(LIGHT_GRAY)
        canvas.line(0.5 * inch, 0.75 * inch, width - 0.5 * inch, 0.75 * inch)

        # Page number
        page_number_text = f"Page {doc.page}"
        canvas.setFont(BASE_FONT, 9)
        canvas.setFillColor(DARK_GRAY)
        canvas.drawRightString(
            width - 0.5 * inch,  # Right margin
            0.5 * inch,  # Bottom margin
            page_number_text,
        )

        # Add current date on the left side of footer
        current_date = datetime.now().strftime("%B %d, %Y")
        canvas.drawString(0.5 * inch, 0.5 * inch, current_date)

        # Draw the logo on every page (smaller version for non-cover pages)
        draw_logo(canvas, doc, size_factor=0.7)
        canvas.restoreState()


def create_donut_chart(data, principle_name):
    """
    Creates a donut chart visualization for a specific principle.

    This function generates a donut chart showing the distribution of Yes/No/NA responses
    for a given principle. The chart includes the principle name in the center and a legend.

    Args:
        data (dict): Dictionary containing response counts for the principle
        principle_name (str): Name of the principle to display

    Returns:
        str: Filepath of the saved chart image

    Note:
        - Chart uses blue for Yes, orange for No, and green for N/A responses
        - Chart is saved as a PNG file in the outputs directory
        - Chart includes percentage labels and a legend
    """
    display_principle_name = get_display_principle_name(principle_name, multiline=True)

    sizes = [
        data[principle_name]["yes"],
        data[principle_name]["no"],
        data[principle_name]["na"],
    ]
    colors = ["#1E90FF", "#FF8C00", "#32CD32"]

    filtered_sizes = [size for size in sizes if size > 0]
    filtered_colors = [color for color, size in zip(colors, sizes) if size > 0]

    fig, ax = plt.subplots(figsize=(8, 8))

    ax.pie(
        filtered_sizes,
        colors=filtered_colors,
        startangle=90,
        autopct=lambda p: f"{int(p * sum(filtered_sizes) / 100)}",
        pctdistance=0.8,
        textprops=dict(color="white", fontsize=18, weight="bold"),
        wedgeprops=dict(edgecolor="white", linewidth=2),
    )

    centre_circle = plt.Circle((0, 0), 0.60, fc="white")
    fig.gca().add_artist(centre_circle)

    font_size = 24 if len(principle_name) <= 20 else 18

    # Capitalize each line separately, preserving \n
    def capitalize_multiline(text):
        return "\n".join(
            " ".join(word.capitalize() for word in line.split())
            for line in text.split("\n")
        )

    display_text = capitalize_multiline(display_principle_name)

    ax.text(
        0,
        0,
        display_text,
        horizontalalignment="center",
        verticalalignment="center",
        fontsize=font_size,
        weight="bold",
        wrap=True,
    )

    ax.axis("equal")
    plt.tight_layout()

    legend_handles = [
        mpatches.Patch(color="#1E90FF", label="Yes"),
        mpatches.Patch(color="#FF8C00", label="No"),
        mpatches.Patch(color="#32CD32", label="N/A"),
    ]

    ax.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.25),
        ncol=3,
        fontsize=24,
        frameon=True,
        borderpad=1.0,
        labelspacing=1.75,
    )
    chart_filename = os.path.join(
        OUTPUTS_DIRECTORY, f"{principle_name}_donut_chart.png"
    )
    plt.savefig(chart_filename, format="png", bbox_inches="tight", dpi=300)
    plt.close()

    return chart_filename


def draw_logo(canvas, doc, size_factor=1.0):
    """
    Draws the company logo on the PDF page.

    This function draws the company logo with proper scaling and positioning. The logo
    appears larger on the first page and smaller in the header of subsequent pages.

    Args:
        canvas (Canvas): The ReportLab canvas object to draw on
        doc (SimpleDocTemplate): The document object containing page information
        size_factor (float): Scaling factor for the logo size (default 1.0)

    Note:
        - Logo is positioned in bottom right on first page
        - Logo is positioned in top right header on subsequent pages
        - Logo maintains aspect ratio when scaled
    """
    width, height = letter

    # Use white logo for first page, regular logo for other pages
    logo_path = LOGO_WHITE_PATH if doc.page == 1 else LOGO_PATH
    logo = Image(logo_path)
    original_width, original_height = logo.wrap(0, 0)

    aspect_ratio = original_width / original_height

    desired_width = 2.5 * inch * size_factor
    desired_height = desired_width / aspect_ratio

    # For first page, position at top right
    if doc.page == 1:
        logo.drawWidth = desired_width
        logo.drawHeight = desired_height
        logo.drawOn(
            canvas,
            width - desired_width - 0.5 * inch,
            height - desired_height - 0.3 * inch,
        )
    else:
        # For other pages, position at top right in header area
        logo.drawWidth = desired_width * 0.7  # Even smaller for header
        logo.drawHeight = desired_height * 0.7
        logo.drawOn(
            canvas,
            width - logo.drawWidth - 0.5 * inch,
            height - logo.drawHeight - 0.3 * inch,
        )


def generate_pdf_cover_page(workspace_data):
    """
    Generates the cover page content for the PDF report.

    This function creates the cover page elements including title, company name,
    date and subtitle with proper styling and spacing.

    Args:
        workspace_data (dict): Dictionary containing workspace information including
            company_name key.

    Returns:
        list: List of PDF elements (Paragraphs, Spacers) that make up the cover page.

    Note:
        - Uses modern typography with Roboto font family
        - Includes company name, current date and subtitle
        - Elements are properly spaced using Spacer objects
    """
    cover_contents = []
    company_name = workspace_data.get("company_name", "Unknown Company")
    app_name = workspace_data.get("app_name", "Unknown Application")

    # Add more space at the top of the cover page
    cover_contents.append(Spacer(1, 2.5 * inch))

    # Add a styled title with better spacing at the top
    title = Paragraph("Summary Report", cover_title_style)
    cover_contents.append(title)

    # Set specific date
    date_generated = datetime.now().strftime("%d %B %Y")

    date_generated_paragraph = Paragraph(date_generated, cover_date_generated_style)
    cover_contents.append(date_generated_paragraph)

    company_name_paragraph = Paragraph(f"{company_name}", cover_company_name_style)
    cover_contents.append(company_name_paragraph)

    # Add a decorative line
    cover_contents.append(Spacer(1, 0.5 * inch))

    # Add application name
    cover_contents.append(Paragraph(f"{app_name}", cover_subheader_style))

    return cover_contents


def generate_pdf_individual_principle_page(
    workspace_data, principle_name, principle_number
):
    """
    Generates a PDF page for an individual principle assessment.

    This function creates a two-column page layout for a specific principle, including
    a donut chart visualization, description, recommendations and justifications where
    applicable.

    Args:
        workspace_data (dict): Dictionary containing workspace information and process checks
        principle_name (str): Name of the principle being assessed
        principle_number (str): Number/ID of the principle

    Returns:
        tuple: Contains two lists of PDF elements:
            - left_content: Elements for the left column
            - right_content: Elements for the right column

    Note:
        - Left column typically contains chart and "What It Means" section
        - Right column contains description and detailed analysis
        - Layout adapts based on assessment results (all yes vs mixed results)
    """
    display_principle_name = get_display_principle_name(principle_name, multiline=False)

    # Custom title style for principle page
    custom_principle_title_style = ParagraphStyle(
        name="CustomPrincipleTitle",
        parent=title_style,
        fontSize=22,
        leading=30,
        spaceAfter=18,
        textColor=PRIMARY_COLOR,
        fontName=BOLD_FONT,
        alignment=TA_LEFT,
        # You can add more customizations here if needed
    )

    # Process the principle data to get process checks and outcomes
    data = process_principle(workspace_data, principle_name, principle_number)
    chart_filename = create_donut_chart(data, principle_name)
    chart = Image(chart_filename, width=3 * inch, height=3.5 * inch)

    principle_title = Paragraph(
        f"{principle_number}. {display_principle_name.upper()}",
        custom_principle_title_style,
    )

    if data[principle_name].get("all_yes", False):
        left_content = []
        left_content.append(principle_title)
        left_content.append(Spacer(1, 0.2 * inch))
        left_content.append(chart)

        right_content = []
        right_content.append(
            Paragraph(
                f"<b>{data[principle_name]['description']}</b>", header_text_style
            )
        )
        right_content.append(Spacer(1, 12))
        right_content.append(Paragraph("What It Means:", header_text_style))
        for wim_text in data[principle_name]["wim"]:
            right_content.append(Paragraph(f"{wim_text}", text_style))

    else:
        left_content = []
        left_content.append(principle_title)
        left_content.append(Spacer(1, 0.2 * inch))
        left_content.append(chart)
        left_content.append(Spacer(1, 12))
        left_content.append(Paragraph("What It Means:", header_text_style))
        for wim_text in data[principle_name]["wim"]:
            left_content.append(Paragraph(f"{wim_text}", text_style))

        if data[principle_name]["no"] > 0 or data[principle_name]["na"] > 0:
            left_content.append(Paragraph("Recommendation:", header_text_style))
            recommendation = Paragraph(
                f"{data[principle_name]['recommendation']}",
                text_style,
            )
            left_content.append(recommendation)

        right_content = []
        right_content.append(
            Paragraph(
                f"<b>{data[principle_name]['description']}</b>", header_text_style
            )
        )
        if data[principle_name]["no"] > 0 or data[principle_name]["na"] > 0:
            for desc in data["process_to_achieve_outcomes"]:
                for point in desc.split("\n"):
                    right_content.append(
                        Paragraph(text=point.strip(), style=text_style, bulletText="•")
                    )

        if not data[principle_name].get("all_yes", False):
            justifications_title = Paragraph("Justifications:", header_text_style)
            right_content.append(justifications_title)

            justifications = data.get("justifications", None)
            if justifications:
                for justification in justifications:
                    right_content.append(
                        Paragraph(text=justification, style=text_style, bulletText="•")
                    )
            else:
                no_justification_text = Paragraph(
                    '<font color="red">The company did not provide any justification.</font>',
                    text_style,
                )
                right_content.append(no_justification_text)

    return left_content, right_content


def generate_pdf_introduction_page(workspace_data, doc):
    """
    Adds the second page content to the PDF elements list, including the aim of AI Verify,
    use case details, and scope of checks.

    Args:
        workspace_data: The data containing information about the workspace.
        doc: The document object containing page information.

    Returns:
        list: List of PDF elements for the introduction page
    """
    introduction_contents = []

    # Switch to introduction page template
    introduction_contents.append(NextPageTemplate("IntroductionPage"))
    introduction_contents.append(PageBreak())

    # Add "Introduction" title at the start
    introduction_title = Paragraph("Introduction", title_style)
    introduction_contents.append(introduction_title)

    # Add aim section
    aim_title = Paragraph(
        "Aim of AI Verify Testing Framework for Generative AI", header_text_style
    )
    aim_content = Paragraph(
        "AI Verify aims to help organisations validate the performance of their AI "
        "systems against a set of internationally recognised principles and document "
        "that their AI systems have been developed and deployed with processes designed "
        "to achieve the desired outcomes of these principles.",
        text_style,
    )
    introduction_contents.append(aim_title)
    introduction_contents.append(aim_content)
    introduction_contents.append(Spacer(1, 12))

    # Add intro text
    intro_text = Paragraph("Companies can use this report to:", text_style)
    introduction_contents.append(intro_text)

    # Add bullet points for company benefits
    benefits = [
        "Identify potential gaps and take appropriate actions to address them, where applicable.",
        "Demonstrate their implementation of responsible AI practices and build trust with their stakeholders.",
    ]
    for benefit in benefits:
        introduction_contents.append(
            Paragraph(text=benefit, style=text_style, bulletText="•")
        )
    introduction_contents.append(Spacer(1, 12))

    # Add note content
    note_content = Paragraph(
        "Please note that only reports generated by AI Verify-Project Moonshot "
        "toolkit, in accordance with the AI Verify Testing Framework, and without any "
        "modification, are considered AI Verify reports.",
        header_text_style,
    )
    introduction_contents.append(note_content)
    introduction_contents.append(Spacer(1, 12))

    # Add use case details
    app_name = workspace_data.get("app_name", "Unknown Application")
    app_description = workspace_data.get("app_description", "No description available.")

    use_case_title = Paragraph("Details of Use Case", header_text_style)
    use_case_content = Paragraph(
        f"Name of application tested: {app_name}<br/>"
        f"Purpose of the use case/application: {app_description}",
        text_style,
    )
    introduction_contents.append(use_case_title)
    introduction_contents.append(use_case_content)
    introduction_contents.append(Spacer(1, 12))

    # Add scope section
    scope_title = Paragraph("Scope of Checks and Technical Tests", header_text_style)
    scope_content = Paragraph(
        "This summary report provides an overview of how the AI system performs "
        "vis-à-vis the AI Verify Testing Framework for Generative AI. The Framework "
        "covers 11 AI governance principles: ",
        text_style,
    )
    introduction_contents.append(scope_title)
    introduction_contents.append(scope_content)

    # Add principles list
    principles = [
        "Transparency",
        "Explainability",
        "Repeatability / Reproducibility",
        "Safety",
        "Security",
        "Robustness",
        "Fairness",
        "Data Governance",
        "Accountability",
        "Human Agency and Oversight",
        "Inclusive Growth, Societal and Environmental Well-being",
    ]

    for i, principle in enumerate(principles, 1):
        introduction_contents.append(
            Paragraph(text=f"{i}. {principle}", style=text_style)
        )

    return introduction_contents


def generate_pdf_process_checks(workspace_data):
    """
    Generates the process checks (Annex A) section for the PDF report.

    This function creates the process checks section, including grouping by principle and group,
    and formatting each process check as a table.

    Args:
        workspace_data (dict): Dictionary containing all workspace information including process checks.
        doc: (optional) The document object containing page information (not used, for API consistency).

    Returns:
        list: List of PDF elements (PageBreaks, Paragraphs, Tables, etc.) for the process checks section.
    """
    process_checks_contents = []
    styles = getSampleStyleSheet()
    process_checks_contents.append(PageBreak())

    # Centered "Annex A" title
    centered_title_style = ParagraphStyle(
        "AnnexATitleCentered",
        parent=title_style,
        alignment=TA_CENTER,
        fontSize=32,
        spaceAfter=24,
        textColor=PRIMARY_COLOR,
        leading=56,
    )
    # Add vertical space to move the title to the middle of the page
    process_checks_contents.append(Spacer(1, 4 * inch))
    title = Paragraph("Annex A", centered_title_style)
    process_checks_contents.append(title)

    # Set table width to match the page's main content area (letter width - 2*0.75 inch margin)
    page_width, _ = letter
    left_margin = 0.75 * inch
    right_margin = 0.75 * inch
    table_total_width = page_width - left_margin - right_margin
    # Proportional column widths (same as before, but scaled to total width)
    col_widths = [
        table_total_width * 0.4,
        table_total_width * 0.4,
        table_total_width * 0.2,
    ]

    grouped_data = {}
    for outcome_id, processes in workspace_data.get("process_checks", {}).items():
        for process_id, process_info in processes.items():
            principle_key = process_info.get("principle_key", "Unknown Principle")
            if principle_key not in grouped_data:
                grouped_data[principle_key] = {}
            group_key = ".".join(process_id.split(".")[:2])
            if group_key not in grouped_data[principle_key]:
                grouped_data[principle_key][group_key] = []
            grouped_data[principle_key][group_key].append((process_id, process_info))
    for principle_key, groups in grouped_data.items():
        process_checks_contents.append(PageBreak())
        process_checks_contents.append(
            Paragraph(f"<b>{principle_key}</b>", styles["Heading2"])
        )
        process_checks_contents.append(Spacer(1, 6))
        for group_key, processes in groups.items():
            outcomes = processes[0][1].get("outcomes", "No outcomes available")
            process_checks_contents.append(
                Paragraph(f"<b>{group_key} - {outcomes}</b>", styles["Heading3"])
            )
            process_checks_contents.append(Spacer(1, 6))
            for process_id, process_info in processes:
                elaboration_text = process_info.get("elaboration", "").strip()
                if not elaboration_text:
                    elaboration_text = "&nbsp;" * 255
                data = [
                    [
                        Paragraph(
                            f"<b>{process_id} Process</b><br/>"
                            f"{process_info.get('process_to_achieve_outcomes', '')}",
                            styles["Normal"],
                        ),
                        Paragraph(
                            f"<b>Evidence</b><br/>{process_info.get('evidence', '')}",
                            styles["Normal"],
                        ),
                        Paragraph(
                            f"<b>Implemented</b><br/>"
                            f"{process_info.get('implementation', '')}<br/><br/>"
                            f"<b>Evidence Type</b><br/>"
                            f"{process_info.get('evidence_type', '')}",
                            styles["Normal"],
                        ),
                    ],
                    [
                        Paragraph(
                            f"<b>Elaboration</b><br/>{elaboration_text}",
                            styles["Normal"],
                        ),
                        "",
                        "",
                    ],
                ]
                table = Table(data, colWidths=col_widths)
                table.hAlign = (
                    "LEFT"  # Align table with left margin (default for content)
                )
                table.setStyle(
                    TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                            ("SPAN", (0, 1), (-1, 1)),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTNAME", (0, 1), (-1, 1), "Helvetica"),
                            ("FONTSIZE", (0, 0), (-1, -1), 10),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                            ("MINHEIGHT", (0, 1), (-1, 1), 50),
                        ]
                    )
                )
                process_checks_contents.append(KeepTogether([table]))
                process_checks_contents.append(Spacer(1, 12))
    return process_checks_contents


def compile_results(process_checks):
    """
    Compiles overall and per-principle statistics from process checks.

    Args:
        process_checks (dict): The process checks data.

    Returns:
        tuple: (overall_stats, principle_stats)
    """
    overall_stats = {"Total Yes": 0, "Total No": 0, "Total N/A": 0}
    principle_stats = {}
    for outcome_id, processes in process_checks.items():
        for process_id, process_info in processes.items():
            principle = process_info.get("principle_key", "Unknown Principle")
            if principle not in principle_stats:
                principle_stats[principle] = {"yes": 0, "no": 0, "na": 0}
            impl = process_info.get("implementation", "").strip().lower()
            if impl == "yes":
                overall_stats["Total Yes"] += 1
                principle_stats[principle]["yes"] += 1
            elif impl == "no":
                overall_stats["Total No"] += 1
                principle_stats[principle]["no"] += 1
            elif impl in ("n/a", "na", "not applicable"):
                overall_stats["Total N/A"] += 1
                principle_stats[principle]["na"] += 1
    return overall_stats, principle_stats


def generate_pdf_overview_page(process_checks, test_result_info):
    """
    Generates the overview completion status page content.

    This function creates the overview page elements including a donut chart,
    summary statistics, alignment text, and technical test results.

    Args:
        process_checks (dict): The process checks data.
        test_result_info (dict or None): Technical test results.

    Returns:
        list: List of PDF elements for the overview page.
    """

    overview_contents = []
    overview_contents.append(PageBreak())

    # Title
    overview_title_style = ParagraphStyle(
        "OverviewTitleStyle",
        parent=styles["Normal"],
        fontName=BOLD_FONT,
        fontSize=16,
        leading=20,
        spaceAfter=16,
        alignment=TA_LEFT,
        textColor=PRIMARY_COLOR,
    )
    title_paragraph = Paragraph("Overall Completion Status", overview_title_style)

    # Compile stats
    overall_stats, principle_stats = compile_results(process_checks)
    total_answered = sum(overall_stats.values())
    yes_count = overall_stats.get("Total Yes", 0)
    no_count = overall_stats.get("Total No", 0)
    na_count = overall_stats.get("Total N/A", 0)
    sizes = [yes_count, no_count, na_count]
    colors_list = ["#1E90FF", "#FF8C00", "#32CD32"]
    filtered_sizes = [size for size in sizes if size > 0]
    filtered_colors = [color for color, size in zip(colors_list, sizes) if size > 0]
    filtered_labels = [
        label for label, size in zip(["Yes", "No", "N/A"], sizes) if size > 0
    ]

    # Donut chart
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(
        filtered_sizes,
        labels=filtered_labels,
        colors=filtered_colors,
        startangle=90,
        autopct=lambda p: f"{int(p * sum(filtered_sizes) / 100)}",
        pctdistance=0.8,
        textprops=dict(color="white", fontsize=18, weight="bold"),
        wedgeprops=dict(edgecolor="white", linewidth=2),
    )
    centre_circle = plt.Circle((0, 0), 0.60, fc="white")
    fig.gca().add_artist(centre_circle)
    ax.text(
        0,
        0,
        "Process Checks",
        horizontalalignment="center",
        verticalalignment="center",
        fontsize=24,
        weight="bold",
    )
    ax.axis("equal")
    plt.tight_layout()
    legend_handles = [
        mpatches.Patch(color="#1E90FF", label="Yes"),
        mpatches.Patch(color="#FF8C00", label="No"),
        mpatches.Patch(color="#32CD32", label="N/A"),
    ]
    ax.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.25),
        ncol=3,
        fontsize=24,
        frameon=True,
        borderpad=1.0,
        labelspacing=1.75,
    )
    chart_filename = os.path.join(
        OUTPUTS_DIRECTORY, "overview_completion_status_donut_chart.png"
    )
    plt.savefig(chart_filename, format="png", bbox_inches="tight", dpi=300)
    plt.close()
    chart_image = Image(chart_filename, width=3 * inch, height=3.5 * inch)

    # Description
    description_intro = f"The company has completed the process checklist of {total_answered} process checks, of which:"
    description_intro_paragraph = Paragraph(description_intro, text_style)
    description_items = [
        f'<b>{yes_count} process checks</b> are indicated as "Yes", meaning that the Company has documentary evidence for the implementation.',  # noqa: E501
        f'<b>{no_count} process checks</b> are indicated as "No", meaning that the Company has not implemented them.',  # noqa: E501
        f'<b>{na_count} process checks</b> are indicated as "Not Applicable", meaning that the Company has not implemented them because these processes are not applicable to the AI system being tested.',  # noqa: E501
    ]
    description_list = ListFlowable(
        [Paragraph(item, text_style) for item in description_items],
        bulletType="bullet",
    )

    # Side-by-side layout
    side_by_side_table_data = [
        [chart_image, [description_intro_paragraph, description_list]]
    ]
    # Reduce the width of the right column from 4.5*inch to 3.5*inch
    side_by_side_table = Table(
        side_by_side_table_data, colWidths=[3.5 * inch, 3.5 * inch]
    )
    side_by_side_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
            ]
        )
    )

    overview_contents.append(
        KeepTogether(
            [
                title_paragraph,
                Spacer(1, 12),
                side_by_side_table,
                Spacer(1, 12),
            ]
        )
    )

    # Alignment text
    # Use a ParagraphStyle with bold font for the heading, and normal style for the rest
    alignment_heading = Paragraph(
        "Alignment with other international frameworks", header_text_style
    )
    alignment_body = Paragraph(
        "By completing the AI Verify testing framework for Generative AI, "
        "which is mapped to Hiroshima Process International Code of Conduct "
        "for Organizations Developing Advanced AI Systems (CoC) and US National "
        "Institute of Standards and Technology's (NIST) Artificial Intelligence "
        "Risk Management Framework Profile (AI RMF): Generative Artificial "
        "Intelligence, the Company has assessed its responsible AI practices against "
        "these frameworks as well. AI Verify processes that are mapped to these "
        'frameworks will have respective labels e.g. "Hiroshima Process CoC" or "US '
        'NIST AI RMF" next to them.',
        text_style,
    )
    alignment_paragraph = KeepTogether([alignment_heading, alignment_body])
    overview_contents.append(alignment_paragraph)
    overview_contents.append(Spacer(1, 8))

    # Technical test section
    technical_test_header = Paragraph(
        "Technical Test (see details under Safety principle)", header_text_style
    )
    overview_contents.append(technical_test_header)
    if not test_result_info:
        no_test_paragraph = Paragraph("<b>No technical test uploaded.</b>", text_style)
        overview_contents.append(no_test_paragraph)
        overview_contents.append(Spacer(1, 4))
    else:
        # Show summary boxes
        test_success = test_result_info.get("total_tests", {}).get("test_success", 0)
        test_fail = test_result_info.get("total_tests", {}).get("test_fail", 0)
        test_skip = test_result_info.get("total_tests", {}).get("test_skip", 0)
        test_results_data = [
            (
                f"Test Successfully Run: {test_success}",
                "",
                "#228B22",
            ),
            (f"Test Failed to Complete: {test_fail}", "", "#FF0000"),
            (f"Test Skipped: {test_skip}", "", "#A9A9A9"),
        ]

        # Define colors and icons
        box_bg_colors = ["#eafbe7", "#ffeaea", "#f2f2f2"]
        box_border_colors = ["#228B22", "#FF0000", "#A9A9A9"]
        icon_html = [
            '<font size="13" color="#228B22">&#9679;</font>',
            '<font size="13" color="#FF0000">&#9679;</font>',
            '<font size="13" color="#A9A9A9">&#9679;</font>',
        ]

        # Prepare the content for each cell
        cell_contents = []
        for idx, (label, value, color) in enumerate(test_results_data):
            cell = Paragraph(
                f'<para align="center">{icon_html[idx]} <b>{label}</b></para>',
                ParagraphStyle(
                    "SummaryCell",
                    alignment=TA_CENTER,
                    fontName=BOLD_FONT,
                    fontSize=11,
                    leading=14,
                    spaceAfter=2,
                ),
            )
            cell_contents.append(cell)

        # Create a single-row table with three columns, each wide enough for the text
        summary_table = Table(
            [cell_contents],
            colWidths=[2 * inch, 2.1 * inch, 2 * inch],  # Shrunk from 2.2 to 1.7
            hAlign="CENTER",
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), box_bg_colors[0]),
                    ("BACKGROUND", (1, 0), (1, 0), box_bg_colors[1]),
                    ("BACKGROUND", (2, 0), (2, 0), box_bg_colors[2]),
                    ("BOX", (0, 0), (0, 0), 1.5, box_border_colors[0]),
                    ("BOX", (1, 0), (1, 0), 1.5, box_border_colors[1]),
                    ("BOX", (2, 0), (2, 0), 1.5, box_border_colors[2]),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),  # Slightly reduced padding
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            ),
        )

        overview_contents.append(Spacer(1, 8))
        overview_contents.append(summary_table)
        overview_contents.append(Spacer(1, 12))

        # List test names
        test_names = [
            entry.get("test_name", "Unnamed Test")
            for entry in test_result_info.get("evaluation_summaries_and_metadata", [])
        ]
        test_names_header = Paragraph(
            "Name of Tests Successfully Run:", subheader_text_style
        )
        overview_contents.append(test_names_header)
        overview_contents.append(Spacer(1, 4))
        bullet_list = ListFlowable(
            [
                Paragraph(
                    test_name,
                    ParagraphStyle(
                        "BulletListTextStyle",
                        parent=text_style,
                        fontSize=12,
                        leading=15,
                        leftIndent=0,
                    ),
                )
                for test_name in test_names
            ],
            bulletType="bullet",
            start="circle",
            bulletFontSize=8,
            leftIndent=18,
            bulletOffsetY=0,
            bulletAlign="left",
        )
        overview_contents.append(bullet_list)
        overview_contents.append(Spacer(1, 4))

    return overview_contents


def generate_pdf_technical_test_page(test_result_info):
    """
    Generates the technical test results page content.

    This function creates the technical test results page, including a table of test names and scores,
    explanatory text, and recommendations.

    Args:
        test_result_info (dict): Technical test results.

    Returns:
        list: List of PDF elements for the technical test results page.
    """
    technical_test_contents = []
    technical_test_contents.append(PageBreak())

    # Title
    title_style = ParagraphStyle(
        "TechnicalTestTitle",
        fontName=BOLD_FONT,
        fontSize=16,
        leading=20,
        spaceAfter=16,
        alignment=TA_LEFT,
        textColor=PRIMARY_COLOR,
    )
    title = Paragraph("Technical Test", title_style)
    technical_test_contents.append(title)

    # Description
    description_style = ParagraphStyle(
        "DescriptionStyle",
        fontName=BASE_FONT,
        fontSize=12,
        leading=15,
        spaceAfter=14,
        alignment=TA_LEFT,
        textColor=DARK_GRAY,
    )
    description = Paragraph(
        "The Company has conducted the following tests:", description_style
    )
    technical_test_contents.append(description)

    # Table of test results
    evaluation_summaries_and_metadata = test_result_info.get(
        "evaluation_summaries_and_metadata", []
    )
    table_data = [["Test Name", "Score"]]
    for entry in evaluation_summaries_and_metadata:
        test_name = entry.get("test_name", "Unknown Test")
        if (
            isinstance(entry.get("summary", None), dict)
            and "avg_grade_value" in entry["summary"]
        ):
            # For Moonshot 0.6
            avg_grade = entry["summary"]["avg_grade_value"]
            score = f"average grade value : {avg_grade}"
        elif isinstance(entry.get("summary", None), dict):
            # For Moonshot GA
            summary_dict = entry["summary"]
            if len(summary_dict) == 1:
                key, value = next(iter(summary_dict.items()))
                if isinstance(value, dict):
                    value_str = "<br/>".join(f"{k}: {v}" for k, v in value.items())
                else:
                    value_str = str(value)
                score = Paragraph(
                    f"<b>{key.replace('_', ' ').capitalize()}</b><br/>{value_str}",
                    getSampleStyleSheet()["Normal"],
                )
            else:
                score = str(summary_dict)
        else:
            score = entry.get("summary", "N/A")
        table_data.append([test_name, score])
    # Make the score column wider
    table = Table(table_data, colWidths=[3.0 * inch, 3.5 * inch], hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_COLOR),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), BOLD_FONT),
                ("FONTNAME", (0, 1), (-1, -1), BASE_FONT),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    technical_test_contents.append(Spacer(1, 8))
    technical_test_contents.append(table)
    technical_test_contents.append(Spacer(1, 18))

    # What it means
    what_it_means_title_style = ParagraphStyle(
        "WhatItMeansTitleStyle",
        parent=getSampleStyleSheet()["Heading3"],
        fontName=BOLD_FONT,
        fontSize=13,
        leading=18,
        alignment=TA_LEFT,
        spaceAfter=4,
        textColor=PRIMARY_COLOR,
    )
    what_it_means_style = ParagraphStyle(
        "WhatItMeansStyle",
        parent=getSampleStyleSheet()["Normal"],
        fontName=BASE_FONT,
        fontSize=11,
        leading=15,
        alignment=TA_LEFT,
        spaceAfter=10,
    )
    # Add the title as a separate paragraph
    what_it_means_title = Paragraph("What It Means:", what_it_means_title_style)
    what_it_means_text = (
        "The tests conducted can provide valuable insights into the AI application's performance and "
        "safety. Each test is accompanied by a score, with the interpretation varying: in some cases, "
        "higher scores indicate better performance or reliability, while in others, lower scores are "
        "preferable (e.g., fewer adverse outcomes or successful prompt injections)."
    )
    what_it_means_paragraph = Paragraph(what_it_means_text, what_it_means_style)
    technical_test_contents.append(what_it_means_title)
    technical_test_contents.append(what_it_means_paragraph)
    technical_test_contents.append(Spacer(1, 10))

    # Recommendation
    recommendation_title_style = ParagraphStyle(
        "RecommendationTitleStyle",
        parent=getSampleStyleSheet()["Heading3"],
        fontName=BOLD_FONT,
        fontSize=13,
        leading=18,
        alignment=TA_LEFT,
        spaceAfter=4,
        textColor=PRIMARY_COLOR,
    )
    recommendation_style = ParagraphStyle(
        "RecommendationStyle",
        parent=getSampleStyleSheet()["Normal"],
        fontName=BASE_FONT,
        fontSize=11,
        leading=15,
        alignment=TA_LEFT,
        spaceAfter=10,
    )
    # Add the title as a separate paragraph
    recommendation_title = Paragraph("Recommendation:", recommendation_title_style)
    recommendation_text = (
        "The test results highlight areas for improvement. High performance or low risk scores "
        "suggest the AI system is performing well or safe in those areas, while lower performance or "
        "higher risk scores indicate potential risks that could impact business operations or expose the "
        "Company to safety issues. Company would need to assess if the test score is acceptable "
        "according to Company's risk tolerance level."
    )
    recommendation_paragraph = Paragraph(recommendation_text, recommendation_style)
    technical_test_contents.append(recommendation_title)
    technical_test_contents.append(recommendation_paragraph)
    technical_test_contents.append(Spacer(1, 8))

    return technical_test_contents


def generate_pdf_report(workspace_data):
    """
    Generates a complete PDF report from workspace assessment data.

    This function orchestrates the creation of a multi-page PDF report including
    cover page and individual principle assessment pages. It handles page templates,
    content flow and document building.

    Args:
        workspace_data (dict): Dictionary containing all workspace information including
            company details and process check results

    Returns:
        str: File path of the generated PDF report

    Note:
        - Creates temp directory if needed
        - Uses different page templates for cover and content pages
        - Handles two-column layout with proper content flow
        - Includes all principles in standardized order
    """
    # Ensure temp_report directory exists
    os.makedirs(OUTPUTS_DIRECTORY, exist_ok=True)

    # Define the output path for the PDF report
    pdf_file_path = os.path.join(OUTPUTS_DIRECTORY, GENERATED_REPORT_NAME)

    # Get page templates for different sections of the PDF
    cover_page = get_pdf_cover_template()  # Template for cover/title page
    introduction_page = (
        get_pdf_introduction_template()
    )  # Template for introduction page
    first_page, later_pages = (
        get_pdf_principle_template()
    )  # Templates for content pages

    # Create the PDF document with letter size pages
    doc = SimpleDocTemplate(pdf_file_path, pagesize=letter)

    # Add all page templates in order
    doc.addPageTemplates([cover_page, introduction_page, first_page, later_pages])

    # Add contents to the pdf
    pdf_contents = []

    # Add cover page contents
    pdf_contents.extend(generate_pdf_cover_page(workspace_data))

    # Add second page
    pdf_contents.extend(generate_pdf_introduction_page(workspace_data, doc))

    # Add overview completion status
    file_path = workspace_data.get("upload_results", {}).get(
        "file_path", "Unknown File Path"
    )
    test_result_info = get_report_info(file_path)
    pdf_contents.extend(
        generate_pdf_overview_page(
            workspace_data.get("process_checks", {}), test_result_info
        )
    )

    # Prepare for individual principle pages
    principles = [
        ("transparency", "1"),
        ("explainability", "2"),
        ("reproducibility", "3"),
        ("safety", "4"),
        ("security", "5"),
        ("robustness", "6"),
        ("fairness", "7"),
        ("data governance", "8"),
        ("accountability", "9"),
        ("human agency", "10"),
        ("inc growth", "11"),
    ]

    for principle, number in principles:
        # Build the final content layout
        left_content, right_content = generate_pdf_individual_principle_page(
            workspace_data, principle, number
        )

        # 1. Add left column content
        pdf_contents.append(NextPageTemplate("FirstPage"))
        pdf_contents.append(PageBreak())
        pdf_contents.extend(left_content)

        # 2. Add frame break to move to right column
        pdf_contents.append(FrameBreak())

        # 3. Switch to later pages template before right content
        for content in right_content:
            pdf_contents.append(NextPageTemplate("LaterPages"))
            pdf_contents.append(content)

        if principle == "safety" and test_result_info != {}:
            pdf_contents.append(NextPageTemplate("IntroductionPage"))
            pdf_contents.extend(generate_pdf_technical_test_page(test_result_info))

    pdf_contents.extend(generate_pdf_process_checks(workspace_data))

    # Build the document
    doc.build(pdf_contents)

    return pdf_file_path


def get_pdf_cover_template():
    """
    Creates a template for the PDF report cover page.

    This function defines the layout and styling for the cover page including margins,
    frames and callbacks for background image and page numbering.

    Returns:
        PageTemplate: A configured template for the cover page

    Note:
        - Uses balanced margins
        - Includes background image
        - Sets up page numbering
    """
    width, height = letter

    # Create a frame with improved margins
    frame = Frame(
        1.25 * inch,  # Increased left margin
        1.25 * inch,  # Increased bottom margin
        width - 2.5 * inch,  # Width with balanced margins
        height - 2.5 * inch,  # Height with balanced margins
        id="cover",
        showBoundary=0,  # Hide frame boundary
        rightPadding=12,
        leftPadding=12,
        topPadding=12,
        bottomPadding=12,
    )

    # Create the cover page template with improved styling
    cover_page = PageTemplate(
        id="CoverPage",
        frames=[frame],
        onPage=add_background_image,
        onPageEnd=add_page_number,
    )

    return cover_page


def get_pdf_introduction_template():
    """
    Creates a template for the introduction page with a single column layout.

    This template includes headers and footers but uses a single wide column
    for content, unlike the two-column layout used in principle pages.

    Returns:
        PageTemplate: A configured template for the introduction page
    """
    width, height = letter

    # Create a frame with balanced margins
    frame = Frame(
        0.75 * inch,  # Left margin
        inch,  # Bottom margin
        width - 1.5 * inch,  # Width (page width minus margins)
        height - 2 * inch,  # Height (page height minus margins)
        id="introduction",
        showBoundary=0,
        leftPadding=12,
        rightPadding=12,
        topPadding=12,
        bottomPadding=12,
    )

    # Create the introduction page template
    introduction_page = PageTemplate(
        id="IntroductionPage",
        frames=[frame],
        onPageEnd=add_page_number,  # Add headers/footers
    )

    return introduction_page


def get_pdf_principle_template():
    """
    Creates templates for principle content pages with two-column layout.

    This function defines two templates:
    1. First page template with two columns (left and right)
    2. Subsequent pages template with only a right column

    Returns:
        tuple: Contains:
            - first_page (PageTemplate): Template for first page with two columns
            - later_pages (PageTemplate): Template for subsequent pages with right column

    Note:
        - Left column starts at 1 inch from left
        - Right column starts at 4.5 inches from left
        - Both columns are 3.75 inches wide
        - Columns are 9 inches tall
        - Includes page numbering
    """
    # First page template with both columns
    frame1 = Frame(0.5 * inch, inch, 3.75 * inch, 9 * inch, id="left")  # Left column
    frame2 = Frame(4.5 * inch, inch, 3.75 * inch, 9 * inch, id="right")  # Right column
    first_page = PageTemplate(
        id="FirstPage", frames=[frame1, frame2], onPageEnd=add_page_number
    )

    # Subsequent pages with only right column
    frame_next = Frame(4.5 * inch, inch, 3.75 * inch, 9 * inch, id="rightCont")
    later_pages = PageTemplate(
        id="LaterPages", frames=[frame_next], onPageEnd=add_page_number
    )

    return first_page, later_pages
