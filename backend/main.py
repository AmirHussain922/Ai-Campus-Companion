"""
AI Campus Companion - Backend Entry Point

This is the main entry point for the FastAPI backend application.
It imports the app factory from app.main and creates the application instance.

Usage:
    Development: uvicorn main:app --reload --port 8000
    Production: uvicorn main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from app.main import create_app

# Create the FastAPI application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    # Run the application when executed directly
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
