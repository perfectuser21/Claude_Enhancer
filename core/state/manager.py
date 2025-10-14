"""
Claude Enhancer v2.0 - State Manager
=====================================

Manages workflow state persistence and retrieval.
"""

from typing import Dict, Any, Optional
import json
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages workflow state persistence

    Handles reading and writing workflow state to disk,
    including current phase, context, and execution history.
    """

    def __init__(self, state_dir: str = ".workflow"):
        """
        Initialize state manager

        Args:
            state_dir: Directory for state files (default: .workflow)
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.current_file = self.state_dir / "current"
        self.state_file = self.state_dir / "state.json"
        self.history_file = self.state_dir / "history.json"

    def get_current_phase(self) -> Optional[str]:
        """Get current phase from state"""
        try:
            if self.current_file.exists():
                return self.current_file.read_text().strip()
        except Exception as e:
            logger.error(f"Failed to read current phase: {e}")
        return None

    def set_current_phase(self, phase: str) -> bool:
        """Set current phase"""
        try:
            self.current_file.write_text(phase)
            return True
        except Exception as e:
            logger.error(f"Failed to write current phase: {e}")
            return False

    def get_state(self) -> Dict[str, Any]:
        """Get workflow state"""
        try:
            if self.state_file.exists():
                return json.loads(self.state_file.read_text())
        except Exception as e:
            logger.error(f"Failed to read state: {e}")
        return {}

    def save_state(self, state: Dict[str, Any]) -> bool:
        """Save workflow state"""
        try:
            self.state_file.write_text(json.dumps(state, indent=2))
            return True
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False

    def add_history_entry(self, entry: Dict[str, Any]) -> bool:
        """Add entry to history"""
        try:
            history = []
            if self.history_file.exists():
                history = json.loads(self.history_file.read_text())

            history.append(entry)
            self.history_file.write_text(json.dumps(history, indent=2))
            return True
        except Exception as e:
            logger.error(f"Failed to add history entry: {e}")
            return False

    def get_history(self) -> list:
        """Get workflow history"""
        try:
            if self.history_file.exists():
                return json.loads(self.history_file.read_text())
        except Exception as e:
            logger.error(f"Failed to read history: {e}")
        return []

    def clear(self) -> bool:
        """Clear all state"""
        try:
            for f in [self.current_file, self.state_file, self.history_file]:
                if f.exists():
                    f.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to clear state: {e}")
            return False


__all__ = ["StateManager"]
