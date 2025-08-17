"""
AI-CRM Core Module

Contains fundamental data models, exceptions, configuration, and utilities
that form the foundation of the AI-CRM system.
"""

# Import all core components for easy access
from .config import *
from .exceptions import *
from .models import *
from .utils import *

__all__ = [
    "config",
    "exceptions",
    "models",
    "utils",
]
