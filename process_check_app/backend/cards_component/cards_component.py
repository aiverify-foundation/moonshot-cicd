import os

import streamlit.components.v1 as components


def create_component(
    principles_names: list[str],
    principles_data: dict[str, dict],
    current_index: int = 0,
    key: str = "cards_component",
):
    """
    Create a Streamlit component for interactive principle cards with progress tracking.

    This component generates a vertical list of clickable cards representing different principles.
    Each card displays the principle name, progress information (number of answered vs total checks),
    and a visual progress bar. The cards provide bidirectional communication with Streamlit,
    allowing users to click on cards to select different principles.

    Args:
        principles_names: List of principle names to display as card titles
        principles_data: Dictionary containing principle data with progress metrics.
                        Each key should correspond to a principle with nested dict containing:
                        - 'total_checks': Total number of checks for the principle
                        - 'answered_checks': Number of completed checks for the principle
        current_index: Currently selected principle index (0-based). Defaults to 0.
        key: Unique identifier for the component instance. Defaults to "cards_component".

    Returns:
        The created Streamlit component instance with the rendered interactive cards

    Raises:
        TypeError: If any parameter is not of the expected type
        ValueError: If current_index is negative
    """
    # Validate inputs
    if not isinstance(principles_names, list):
        raise TypeError("principles_names must be a list")
    if not isinstance(principles_data, dict):
        raise TypeError("principles_data must be a dictionary")
    if not isinstance(current_index, int):
        raise TypeError("current_index must be an integer")
    if not isinstance(key, str):
        raise TypeError("key must be a string")

    if current_index < 0:
        raise ValueError("current_index must be greater than or equal to 0")

    # Create component directory
    component_dir = os.path.dirname(__file__)

    # Set the path for index.html directly in the current directory
    index_html_path = os.path.join(component_dir, "index.html")

    # Generate the HTML
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .vertical-card {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 10px 8px;
                margin-bottom: 12px;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .vertical-card:hover {
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .card-header {
                display: flex;
                align-items: center;
            }
            .card-icon {
                width: 22px;
                height: 22px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 8px;
                flex-shrink: 0;
                font-weight: bold;
                font-size: 0.8rem;
                letter-spacing: -0.01em;
            }
            .card-title {
                font-weight: 600;
                font-size: 0.9rem;
                margin: 0;
                line-height: 1.2;
                letter-spacing: -0.01em;
            }
            .card-progress {
                margin-top: 4px;
                font-size: 0.75rem;
                color: #6b7280;
                letter-spacing: 0.01em;
                padding-left: 30px;
            }
            .small-progress {
                height: 3px;
                margin-top: 4px;
                background-color: #e5e7eb;
                border-radius: 2px;
                overflow: hidden;
                margin-left: 30px;
            }
            .progress-fill {
                height: 100%;
                background-color: #3b82f6;
                transition: width 0.3s ease;
            }
            #principles-nav {
                padding: 0;
                margin: 0;
                font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', Arial, sans-serif;
            }
        </style>
    </head>
    <body>
        <div id="principles-nav"></div>
        
        <script>
            // Function to send messages to Streamlit
            function sendMessageToStreamlit(type, data) {
                const outData = Object.assign({
                    isStreamlitMessage: true,
                    type: type,
                }, data);
                window.parent.postMessage(outData, "*");
            }
            
            // Initialize component
            function init() {
                sendMessageToStreamlit("streamlit:componentReady", {apiVersion: 1});
            }
            
            // Set the frame height
            function setFrameHeight(height) {
                sendMessageToStreamlit("streamlit:setFrameHeight", {height: height});
            }
            
            // Send data to Python
            function sendDataToPython(data) {
                sendMessageToStreamlit("streamlit:setComponentValue", data);
            }
            
            // Function to select a principle
            function selectPrinciple(index) {
                // Send data to Python
                sendDataToPython({
                    value: index,
                    dataType: "json",
                });
                
                // Update UI
                updateCardStyles(index);
            }
            
            // Update card styles based on active index
            function updateCardStyles(activeIndex) {
                const cards = document.querySelectorAll('.vertical-card');
                cards.forEach(card => {
                    const cardIndex = parseInt(card.dataset.index);
                    const cardTitle = card.querySelector('.card-title');
                    const cardIcon = card.querySelector('.card-icon');
                    
                    if (cardIndex === activeIndex) {
                        // Active card
                        card.style.borderLeft = '3px solid #3b82f6';
                        card.style.backgroundColor = '#f0f9ff';
                        card.style.transform = 'none';
                        card.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
                        cardTitle.style.color = '#1a56db';
                        cardIcon.style.backgroundColor = '#3b82f6';
                        cardIcon.style.color = 'white';
                    } else {
                        // Inactive card
                        card.style.borderLeft = '1px solid #d1d5db';
                        card.style.backgroundColor = 'white';
                        card.style.transform = 'none';
                        card.style.boxShadow = 'none';
                        cardTitle.style.color = '#1f2937';
                        
                        // Check if it's a completed card by looking for the ✓ symbol
                        if (cardIcon.innerHTML.trim() === '✓') {
                            cardIcon.style.backgroundColor = '#22c55e';
                            cardIcon.style.color = 'white';
                        } else {
                            cardIcon.style.backgroundColor = '#fbbf24';
                            cardIcon.style.color = '#7c2d12';
                        }
                    }
                });
            }
            
            // Generate card HTML with a more reliable click handler
            function generateCardHTML(name, index, isActive, isCompleted, progress) {
                const iconBgColor = isCompleted ? '#22c55e' : isActive ? '#3b82f6' : '#fbbf24';
                const iconColor = isCompleted || isActive ? 'white' : '#7c2d12';
                const icon = isCompleted ? '✓' : (index + 1).toString();
                const titleColor = isActive ? '#1a56db' : '#1f2937';
                const bgColor = isActive ? '#f0f9ff' : 'white';
                const borderStyle = isActive ? '3px solid #3b82f6' : '1px solid #d1d5db';
                
                return `
                    <div class="vertical-card ${isActive ? 'active' : ''}"
                        data-index="${index}"
                        id="card-${index}"
                        style="padding-left: 8px; background-color: ${bgColor}; border-left: ${borderStyle};">
                        <div class="card-header">
                            <div class="card-icon" style="background-color: ${iconBgColor}; color: ${iconColor};">
                                ${icon}
                            </div>
                            <div class="card-title" style="color: ${titleColor};">${name}</div>
                        </div>
                        <div class="card-progress">
                            ${progress.answered} of ${progress.total} checks
                        </div>
                        <div class="small-progress">
                            <div class="progress-fill" style="width: ${progress.percentage}%"></div>
                        </div>
                    </div>
                `;
            }
            
            // Add event listeners to cards
            function addCardEventListeners() {
                const cards = document.querySelectorAll('.vertical-card');
                cards.forEach(card => {
                    const index = parseInt(card.dataset.index);
                    card.addEventListener('click', function(e) {
                        e.stopPropagation(); // Prevent event bubbling
                        selectPrinciple(index);
                    });
                });
            }
            
            // Handle data from Python
            function onDataFromPython(event) {
                if (event.data.type !== "streamlit:render") return;
                
                const data = event.data.args;
                if (!data) return;
                
                const principlesNames = data.principles_names || [];
                const principlesData = data.principles_data || {};
                const currentIndex = data.current_index || 0;
                
                // Generate all cards
                const nav = document.getElementById('principles-nav');
                let cardsHtml = '';
                
                principlesNames.forEach((name, i) => {
                    try {
                        const principleKey = Object.keys(principlesData)[i];
                        const principleInfo = principlesData[principleKey];
                        
                        // Get actual check counts from the processed data
                        const totalChecks = principleInfo.total_checks || 0;
                        const answeredChecks = principleInfo.answered_checks || 0;
                        const progressPercentage = totalChecks > 0 ? (answeredChecks / totalChecks * 100) : 0;
                        
                        // Create progress object with actual counts
                        const progress = {
                            total: totalChecks,
                            answered: answeredChecks,
                            percentage: progressPercentage
                        };
                        
                        const isCompleted = progress.percentage === 100 && totalChecks > 0;
                        const isActive = i === currentIndex;
                        
                        cardsHtml += generateCardHTML(name, i, isActive, isCompleted, progress);
                    } catch (e) {
                        console.error(`Error rendering card ${i}:`, e);
                    }
                });
                
                nav.innerHTML = cardsHtml;
                
                // Add event listeners after rendering cards
                addCardEventListeners();
                
                // Set height based on number of cards
                setFrameHeight(principlesNames.length * 90);
            }
            
            // Event listeners
            window.addEventListener("message", onDataFromPython);
            window.addEventListener("load", function() {
                setFrameHeight(0); // Initial height
            });
            
            // Initialize the component
            init();
        </script>
    </body>
    </html>
    """  # noqa: E501, W291, W293

    write_file = True
    if os.path.exists(index_html_path):
        with open(index_html_path, "r") as f:
            existing_content = f.read()
        if existing_content == html_content:
            write_file = False

    if write_file:
        with open(index_html_path, "w") as f:
            f.write(html_content)

    # Create and return the component
    component = components.declare_component("cards_component", path=component_dir)

    # Return the instantiated component with updated data
    return component(
        principles_names=principles_names,
        principles_data=principles_data,
        current_index=current_index,
        key=key,
    )
