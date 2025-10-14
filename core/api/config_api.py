"""
Claude Enhancer v2.0 - Config API
==================================

Public API for configuration operations.
"""

from typing import Dict, Any
import logging


logger = logging.getLogger(__name__)


class ConfigAPI:
    """
    Public API for configuration operations

    Version: 2.0.0
    """

    def __init__(self, loader):
        """
        Initialize config API

        Args:
            loader: ConfigLoader instance
        """
        self.loader = loader
        logger.info("ConfigAPI initialized")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        config = self.loader.config

        # Support dot notation (e.g., "workflow.max_agents")
        keys = key.split('.')
        value = config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        Set configuration value

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        config = self.loader.config

        # Support dot notation
        keys = key.split('.')
        current = config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value
        logger.info("Config updated: %s = %s", key, value)

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration

        Returns:
            Complete configuration dictionary
        """
        return self.loader.config.copy()

    def reload(self):
        """Reload configuration from files"""
        self.loader.load()
        logger.info("Configuration reloaded")

    def validate(self) -> Dict[str, Any]:
        """
        Validate current configuration

        Returns:
            Validation result dictionary
        """
        return self.loader.validator.validate(self.loader.config)
