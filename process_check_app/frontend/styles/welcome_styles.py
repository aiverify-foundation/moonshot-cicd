def get_welcome_custom_css():
    """
    Returns custom CSS styling for the welcome page.

    The CSS includes styling for:
    - Headers (h3) with deep purple color
    - Card containers with flex layout
    - Individual cards with hover effects and purple borders
    - Card titles with consistent styling
    - Link styling for framework cards
    - Responsive design for mobile screens

    Returns:
        str: CSS styling as a string that can be injected into HTML
    """
    return """
        <style>
        h3 {
            color: #4C1D95 !important;  /* Deep purple color */
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }
        
        .cards-container {
            display: flex;
            gap: 1.5rem;
            margin: 1rem 0 1.5rem 0;
            flex-wrap: wrap;
        }
        
        .cards-container a {
            text-decoration: none;
        }
        
        .card {
            flex: 1;
            width: 300px;
            height: 300px;
            background: #ffffff;
            color: #000000;
            padding: 2rem;
            border-radius: 16px;
            border: 2px solid #8B5CF6;
            box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
            transition: all 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 24px rgba(139, 92, 246, 0.3);
            border-color: #6D28D9;  /* Darker purple on hover */
        }
        
        .card-title {
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 1.2rem;
            text-align: center;
            line-height: 1.4;
            color: #4C1D95;  /* Match h3 color */
        }
                
        @media (max-width: 768px) {
            .cards-container {
                flex-direction: column;
            }
            
            .card {
                min-width: unset;
                margin-bottom: 1rem;
            }
            
            .card:hover {
                transform: translateY(-2px);  /* Reduced hover effect on mobile */
            }
        }
        </style>
    """  # noqa: W293
