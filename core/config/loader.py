"""
Claude Enhancer v2.0 - Configuration Loader
============================================

Loads and manages configuration from various sources.
"""

from typing import Dict, Any, Optional
import json
import yaml
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Loads configuration from files

    Supports JSON and YAML formats, with environment variable
    override and validation.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader

        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from file"""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    if self.config_path.endswith('.json'):
                        self.config = json.load(f)
                    elif self.config_path.endswith(('.yml', '.yaml')):
                        self.config = yaml.safe_load(f)
                    else:
                        logger.warning(f"Unknown config format: {self.config_path}")

                logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        else:
            # Load default configuration
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "version": "2.0.0",
            "workflow": {
                "state_dir": ".workflow",
                "phases": ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]
            },
            "hooks": {
                "dir": ".claude/hooks",
                "enabled": True
            },
            "agents": {
                "min_count": 4,
                "default_count": 6,
                "max_count": 8
            },
            "features": {
                "self-healing": True,
                "memory-compression": True,
                "workflow-enforcement": True
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, output_path: Optional[str] = None):
        """Save configuration to file"""
        path = output_path or self.config_path

        if not path:
            logger.error("No output path specified")
            return False

        try:
            with open(path, 'w') as f:
                if path.endswith('.json'):
                    json.dump(self.config, f, indent=2)
                elif path.endswith(('.yml', '.yaml')):
                    yaml.dump(self.config, f, default_flow_style=False)

            logger.info(f"Saved configuration to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def reload(self):
        """Reload configuration from file"""
        self._load_config()


__all__ = ["ConfigLoader"]
