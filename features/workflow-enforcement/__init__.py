"""
Workflow Enforcement Feature
=============================

Enhanced workflow enforcement with 5-layer detection.

Features:
- Phase state detection (P0-P7)
- Branch state detection
- Continuation keyword recognition ("继续", "好的", etc.)
- Programming keyword detection
- Workflow state file checking

Version: 2.0.0
Status: Optional (can be disabled)
"""

__version__ = "2.0.0"
__feature_name__ = "workflow-enforcement"
__feature_status__ = "enabled"

DEPENDENCIES = ["self-healing"]  # Requires self-healing for state management

__all__ = [
    "__version__",
    "__feature_name__",
    "__feature_status__"
]
