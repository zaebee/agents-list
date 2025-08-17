"""
AI-CRM API Module

FastAPI-based REST API endpoints and web application interface.
"""

# Import main FastAPI app for easy access
from .main import app

__all__ = [
    "app",  # Main FastAPI application
    "docs",  # API documentation
    "main",  # Main module
    "routes",  # Route modules
]
