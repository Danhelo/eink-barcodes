"""
Progress bar module - deprecated.

This module is kept for backward compatibility.
Use enhanced_progress.py instead.
"""

# Import the enhanced progress bar for backward compatibility
from .enhanced_progress import EnhancedProgressBar

# Re-export the enhanced progress bar
__all__ = ["EnhancedProgressBar"]
