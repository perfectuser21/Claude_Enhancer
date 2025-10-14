"""
Claude Enhancer v2.0 - Hook Manager
====================================

Manages hook registration and execution.
"""

from typing import Dict, Any, List, Callable, Optional
import logging
import subprocess
import os

logger = logging.getLogger(__name__)


class HookManager:
    """
    Manages hooks for workflow events

    Handles registration and execution of hooks at various
    points in the workflow lifecycle.
    """

    def __init__(self, hooks_dir: str = ".claude/hooks"):
        """
        Initialize hook manager

        Args:
            hooks_dir: Directory containing hook scripts
        """
        self.hooks_dir = hooks_dir
        self.hooks: Dict[str, List[str]] = {}
        self._load_hooks()

    def _load_hooks(self):
        """Load hooks from directory"""
        if not os.path.exists(self.hooks_dir):
            logger.warning(f"Hooks directory not found: {self.hooks_dir}")
            return

        # Hook types
        hook_types = [
            "PrePrompt",
            "PostPrompt",
            "PreToolUse",
            "PostToolUse",
            "UserPromptSubmit"
        ]

        for hook_type in hook_types:
            self.hooks[hook_type] = []

        # Scan for hook scripts
        for item in os.listdir(self.hooks_dir):
            full_path = os.path.join(self.hooks_dir, item)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                # Determine hook type from filename or register as generic
                self.hooks.setdefault("Generic", []).append(full_path)

    def execute_hook(self, hook_type: str, context: Dict[str, Any]) -> bool:
        """
        Execute hooks of given type

        Args:
            hook_type: Type of hook to execute
            context: Context data to pass to hooks

        Returns:
            True if all hooks succeeded, False otherwise
        """
        if hook_type not in self.hooks:
            return True

        for hook_path in self.hooks[hook_type]:
            try:
                result = subprocess.run(
                    [hook_path],
                    input=str(context),
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    logger.error(f"Hook failed: {hook_path}")
                    logger.error(f"Output: {result.stderr}")
                    return False

            except Exception as e:
                logger.error(f"Failed to execute hook {hook_path}: {e}")
                return False

        return True

    def register_hook(self, hook_type: str, hook_path: str):
        """Register a new hook"""
        if hook_type not in self.hooks:
            self.hooks[hook_type] = []

        if hook_path not in self.hooks[hook_type]:
            self.hooks[hook_type].append(hook_path)

    def list_hooks(self, hook_type: Optional[str] = None) -> Dict[str, List[str]]:
        """List registered hooks"""
        if hook_type:
            return {hook_type: self.hooks.get(hook_type, [])}
        return self.hooks


__all__ = ["HookManager"]
