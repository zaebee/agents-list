"""
Backward compatibility import for models.py
TODO: Remove this after all imports are updated
"""

import warnings

warnings.warn(
    "Importing from 'models' is deprecated. Use 'from ai_crm.core import models' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.ai_crm.core.models import *
