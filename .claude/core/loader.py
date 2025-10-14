"""
Claude Enhancer v2.0 - Configuration Loader
============================================

Loads and manages configuration from various sources.
"""

from typing import Dict, Any, Optional, List
import json
import yaml
import os
import sys
import time
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


def load_features(features_dir: str = ".claude/features") -> Dict[str, Any]:
    """
    Load and initialize features

    Implements fast, lazy loading for personal use with dependency checking.
    Optimized for <100ms load time.

    Args:
        features_dir: Directory containing features (default: .claude/features)

    Returns:
        Dictionary of loaded features with their status:
        {
            "basic": {"enabled": True, "loaded": True, "capabilities": [...]},
            "standard": {"enabled": True, "loaded": True, "capabilities": [...]},
            "advanced": {"enabled": False, "loaded": False, "capabilities": []},
            "load_time_ms": 45.2,
            "errors": []
        }

    Example:
        >>> features = load_features()
        >>> print(features["basic"]["capabilities"])
        ["8-Phase Workflow (P0-P7)", "Branch Protection", ...]
    """
    start_time = time.perf_counter()

    result = {
        "basic": {"enabled": False, "loaded": False, "capabilities": []},
        "standard": {"enabled": False, "loaded": False, "capabilities": []},
        "advanced": {"enabled": False, "loaded": False, "capabilities": []},
        "load_time_ms": 0,
        "errors": []
    }

    # Convert to Path object
    features_path = Path(features_dir)

    if not features_path.exists():
        error_msg = f"Features directory not found: {features_dir}"
        logger.error(error_msg)
        result["errors"].append(error_msg)
        result["load_time_ms"] = (time.perf_counter() - start_time) * 1000
        return result

    # Load main feature config
    config_file = features_path / "config.yaml"
    config = {}

    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            error_msg = f"Failed to load feature config: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)

    # Get enabled features list
    enabled_features = config.get("enabled_features", ["basic", "standard"])
    feature_dependencies = config.get("feature_dependencies", {
        "standard": ["basic"],
        "advanced": ["basic", "standard"]
    })

    # Check and load each feature tier
    feature_tiers = ["basic", "standard", "advanced"]

    for tier in feature_tiers:
        tier_path = features_path / tier

        # Check if tier directory exists
        if not tier_path.exists():
            result[tier]["enabled"] = False
            result[tier]["loaded"] = False
            continue

        # Check if tier is enabled
        is_enabled = tier in enabled_features

        # Check dependencies
        dependencies = feature_dependencies.get(tier, [])
        dependencies_met = all(
            result[dep]["loaded"] for dep in dependencies
        )

        if not dependencies_met:
            error_msg = f"Feature '{tier}' dependencies not met: {dependencies}"
            logger.warning(error_msg)
            result["errors"].append(error_msg)
            result[tier]["enabled"] = False
            result[tier]["loaded"] = False
            continue

        result[tier]["enabled"] = is_enabled

        # Only load if enabled
        if is_enabled:
            try:
                # Try to import the feature module
                # Add feature path to sys.path temporarily
                tier_parent = str(tier_path.parent)
                if tier_parent not in sys.path:
                    sys.path.insert(0, tier_parent)

                # Import the feature module
                module_name = f"{tier}"
                try:
                    feature_module = __import__(module_name)

                    # Get the feature class (e.g., BasicFeatures)
                    class_name = f"{tier.capitalize()}Features"
                    if hasattr(feature_module, class_name):
                        feature_class = getattr(feature_module, class_name)
                        feature_instance = feature_class()

                        # Get capabilities
                        capabilities = feature_instance.get_capabilities()

                        result[tier]["loaded"] = True
                        result[tier]["capabilities"] = capabilities
                        result[tier]["version"] = getattr(feature_instance, "version", "unknown")

                        logger.info(f"Loaded feature: {tier} ({len(capabilities)} capabilities)")
                    else:
                        # Fallback: Load from config
                        tier_config_file = tier_path / "config.yaml"
                        if tier_config_file.exists():
                            with open(tier_config_file, 'r') as f:
                                tier_config = yaml.safe_load(f) or {}

                            result[tier]["loaded"] = True
                            result[tier]["capabilities"] = list(
                                tier_config.get("features", {}).keys()
                            )
                            result[tier]["version"] = tier_config.get("version", "unknown")

                except ImportError as ie:
                    # If import fails, try loading from config only
                    logger.debug(f"Could not import {module_name}: {ie}")

                    tier_config_file = tier_path / "config.yaml"
                    if tier_config_file.exists():
                        with open(tier_config_file, 'r') as f:
                            tier_config = yaml.safe_load(f) or {}

                        result[tier]["loaded"] = True
                        result[tier]["capabilities"] = list(
                            tier_config.get("features", {}).keys()
                        )
                        result[tier]["version"] = tier_config.get("version", "unknown")
                    else:
                        raise ImportError(f"Neither module nor config found for {tier}")

            except Exception as e:
                error_msg = f"Failed to load feature '{tier}': {e}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
                result[tier]["loaded"] = False
        else:
            result[tier]["loaded"] = False

    # Calculate load time
    load_time = (time.perf_counter() - start_time) * 1000
    result["load_time_ms"] = round(load_time, 2)

    # Log summary
    loaded_count = sum(1 for tier in feature_tiers if result[tier]["loaded"])
    logger.info(
        f"Feature loading complete: {loaded_count}/{len(feature_tiers)} loaded "
        f"in {result['load_time_ms']:.2f}ms"
    )

    # Warn if load time exceeds target
    if load_time > 100:
        logger.warning(
            f"Feature loading exceeded 100ms target: {load_time:.2f}ms"
        )

    return result


__all__ = ["ConfigLoader", "load_features"]
