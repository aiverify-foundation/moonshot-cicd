#!/usr/bin/env python3
"""
Script to demonstrate exporting the FastAPI application.
This shows how to import and use the FastAPI app in different contexts.
"""

import json
from src.entrypoints.api import app

def export_openapi_schema():
    """Export the OpenAPI schema of the FastAPI application."""
    openapi_schema = app.openapi()
    
    # Save to file
    with open("openapi_schema.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print("OpenAPI schema exported to openapi_schema.json")
    return openapi_schema

def export_app_info():
    """Export basic information about the FastAPI application."""
    app_info = {
        "title": app.title,
        "description": app.description,
        "version": app.version,
        "docs_url": app.docs_url,
        "redoc_url": app.redoc_url,
        "routes": []
    }
    
    # Get route information
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            app_info["routes"].append({
                "path": route.path,
                "methods": list(route.methods),
                "name": getattr(route, 'name', 'unnamed')
            })
    
    # Save to file
    with open("app_info.json", "w") as f:
        json.dump(app_info, f, indent=2)
    
    print("App info exported to app_info.json")
    return app_info

if __name__ == "__main__":
    print("Exporting FastAPI application...")
    
    # Export OpenAPI schema
    openapi_schema = export_openapi_schema()
    
    # Export app info
    app_info = export_app_info()
    
    print("\nFastAPI application exported successfully!")
    print(f"Title: {app_info['title']}")
    print(f"Version: {app_info['version']}")
    print(f"Number of routes: {len(app_info['routes'])}")
    print(f"Documentation available at: {app_info['docs_url']}")
