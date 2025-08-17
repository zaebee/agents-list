"""
Backward compatibility import for exceptions.py
TODO: Remove this after all imports are updated
"""

import warnings

warnings.warn(
    "Importing from 'exceptions' is deprecated. Use 'from ai_crm.core import exceptions' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.ai_crm.core.exceptions import *
