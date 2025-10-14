"""
Claude Enhancer v2.0 - Hook API
================================

Public API for hook operations.
"""

from typing import Dict, Any, List
import logging


logger = logging.getLogger(__name__)


class HookAPI:
    """
    Public API for hook operations

    Version: 2.0.0
    """

    def __init__(self, manager):
        """
        Initialize hook API

        Args:
            manager: HookManager instance
        """
        self.manager = manager
        logger.info("HookAPI initialized")

    def register_hook(self, hook: Any):
        """
        Register a hook

        Args:
            hook: Hook object to register
        """
        self.manager.register(hook)
        logger.info("Hook registered: %s", hook.name if hasattr(hook, 'name') else 'unknown')

    def validate_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an event against registered hooks

        Args:
            event: Event dictionary to validate

        Returns:
            Validation result dictionary
        """
        from core.api.events import Event

        event_obj = Event(
            name=event.get('name', 'unknown'),
            data=event.get('data', {})
        )

        result = self.manager.validate(event_obj)

        return {
            'passed': result.passed,
            'should_block': result.should_block,
            'should_warn': result.should_warn,
            'messages': result.messages,
            'violations': result.violations
        }

    def list_hooks(self) -> List[Dict[str, Any]]:
        """
        List all registered hooks

        Returns:
            List of hook information dictionaries
        """
        hooks = self.manager.list_hooks()

        return [
            {
                'id': hook.id,
                'name': hook.name,
                'type': hook.type,
                'enabled': hook.enabled
            }
            for hook in hooks
        ]

    def enable_hook(self, hook_id: str):
        """
        Enable a hook

        Args:
            hook_id: ID of hook to enable
        """
        self.manager.enable_hook(hook_id)
        logger.info("Hook enabled: %s", hook_id)

    def disable_hook(self, hook_id: str):
        """
        Disable a hook

        Args:
            hook_id: ID of hook to disable
        """
        self.manager.disable_hook(hook_id)
        logger.info("Hook disabled: %s", hook_id)
