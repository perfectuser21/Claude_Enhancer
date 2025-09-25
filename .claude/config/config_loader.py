#!/usr/bin/env python3
"""
Claude Enhancer Unified Configuration Loader
=====================================

A comprehensive configuration management system that:
- Loads and merges configurations from multiple sources
- Supports environment-specific overrides
- Validates configuration schemas
- Handles environment variable substitution
- Provides fallback defaults
- Supports hot reloading

Author: Claude Enhancer System (Backend Architect & Infrastructure Engineer)
Version: 1.0.0
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime


class ConfigEnvironment(Enum):
    """Configuration environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class ValidationLevel(Enum):
    """Configuration validation levels."""

    STRICT = "strict"
    WARNING = "warning"
    ADVISORY = "advisory"


@dataclass
class ConfigMetadata:
    """Configuration metadata."""

    version: str
    name: str
    description: str
    last_updated: str
    schema_version: str
    environment: str = "development"
    validation_level: ValidationLevel = ValidationLevel.STRICT


@dataclass
class ConfigValidationResult:
    """Configuration validation result."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Optional[ConfigMetadata] = None


class ConfigurationError(Exception):
    """Configuration-related errors."""

    pass


class ConfigurationLoader:
    """
    Unified configuration loader for Claude Enhancer system.

    Features:
    - Hierarchical configuration loading (main + environment)
    - Environment variable substitution
    - Schema validation
    - Hot reloading
    - Backward compatibility with legacy configs
    """

    def __init__(self, config_dir: str = None):
        """Initialize configuration loader."""
        self.config_dir = Path(config_dir) if config_dir else Path(".claude/config")
        self.logger = self._setup_logging()
        self._config_cache = {}
        self._file_timestamps = {}
        self._validation_schemas = {}

        # Environment detection
        self.environment = self._detect_environment()

        # Load validation schemas
        self._load_validation_schemas()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for configuration loader."""
        logger = logging.getLogger("claude-enhancer.config")

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] Config: %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    def _detect_environment(self) -> ConfigEnvironment:
        """Detect current environment from various sources."""
        # Priority order: ENV var > file > default
        env_var = os.getenv("PERFECT21_ENV", "").lower()

        if env_var in [e.value for e in ConfigEnvironment]:
            return ConfigEnvironment(env_var)

        # Check for environment indicator files
        if (self.config_dir / "env" / "production.yaml").exists():
            prod_indicators = [".production", "PRODUCTION", "/var/log"]
            if any(Path(indicator).exists() for indicator in prod_indicators):
                return ConfigEnvironment.PRODUCTION

        if (self.config_dir / "env" / "testing.yaml").exists():
            test_indicators = [".testing", "CI", "TESTING"]
            if any(os.getenv(indicator) for indicator in test_indicators):
                return ConfigEnvironment.TESTING

        return ConfigEnvironment.DEVELOPMENT

    def _load_validation_schemas(self):
        """Load configuration validation schemas."""
        schema_file = self.config_dir / "schemas" / "config_schema.yaml"
        if schema_file.exists():
            try:
                with open(schema_file, "r", encoding="utf-8") as f:
                    self._validation_schemas = yaml.safe_load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load validation schemas: {e}")

    def load_config(
        self,
        force_reload: bool = False,
        environment: Optional[ConfigEnvironment] = None,
    ) -> Dict[str, Any]:
        """
        Load complete configuration with environment overrides.

        Args:
            force_reload: Force reload even if cached
            environment: Override detected environment

        Returns:
            Complete merged configuration
        """
        try:
            env = environment or self.environment
            cache_key = f"config_{env.value}"

            # Check cache and file timestamps
            if not force_reload and self._is_cache_valid(cache_key):
                self.logger.debug(f"Using cached config for {env.value}")
                return self._config_cache[cache_key]

            # Load main configuration
            main_config = self._load_main_config()

            # Load environment-specific overrides
            env_config = self._load_environment_config(env)

            # Merge configurations
            merged_config = self._merge_configs(main_config, env_config)

            # Apply environment variable overrides
            final_config = self._apply_env_overrides(merged_config)

            # Validate configuration
            validation_result = self._validate_config(final_config)
            if not validation_result.is_valid:
                if (
                    validation_result.metadata
                    and validation_result.metadata.validation_level
                    == ValidationLevel.STRICT
                ):
                    raise ConfigurationError(
                        f"Configuration validation failed: {validation_result.errors}"
                    )
                else:
                    self.logger.warning(
                        f"Configuration warnings: {validation_result.warnings}"
                    )

            # Cache the result
            self._config_cache[cache_key] = final_config
            self._update_file_timestamps()

            self.logger.info(
                f"Configuration loaded successfully for {env.value} environment"
            )
            return final_config

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Configuration loading failed: {e}")

    def _load_main_config(self) -> Dict[str, Any]:
        """Load main configuration file."""
        main_file = self.config_dir / "main.yaml"

        if not main_file.exists():
            raise ConfigurationError(f"Main configuration file not found: {main_file}")

        try:
            with open(main_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            self.logger.debug("Main configuration loaded successfully")
            return config

        except Exception as e:
            raise ConfigurationError(f"Failed to load main config: {e}")

    def _load_environment_config(
        self, environment: ConfigEnvironment
    ) -> Dict[str, Any]:
        """Load environment-specific configuration."""
        env_file = self.config_dir / "env" / f"{environment.value}.yaml"

        if not env_file.exists():
            self.logger.warning(
                f"Environment config not found: {env_file}, using defaults"
            )
            return {}

        try:
            with open(env_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            self.logger.debug(f"Environment configuration loaded: {environment.value}")
            return config

        except Exception as e:
            self.logger.warning(f"Failed to load environment config: {e}")
            return {}

    def _merge_configs(
        self, main_config: Dict[str, Any], env_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge main and environment configurations."""

        def deep_merge(base: Dict, override: Dict) -> Dict:
            """Recursively merge dictionaries."""
            result = base.copy()

            for key, value in override.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value

            return result

        merged = deep_merge(main_config, env_config)
        self.logger.debug("Configurations merged successfully")
        return merged

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides."""

        def substitute_env_vars(obj: Any) -> Any:
            """Recursively substitute environment variables."""
            if isinstance(obj, str):
                # Pattern: ${ENV_VAR} or ${ENV_VAR:default}
                pattern = r"\$\{([^}]+)\}"
                matches = re.findall(pattern, obj)

                for match in matches:
                    if ":" in match:
                        env_var, default = match.split(":", 1)
                    else:
                        env_var, default = match, None

                    # Get environment variable value
                    env_value = os.getenv(env_var.strip(), default)
                    if env_value is None:
                        if default is None:
                            self.logger.warning(
                                f"Environment variable {env_var} not found and no default provided"
                            )
                            continue
                        env_value = default

                    # Replace in string
                    obj = obj.replace(f"${{{match}}}", str(env_value))

                return obj

            elif isinstance(obj, dict):
                return {k: substitute_env_vars(v) for k, v in obj.items()}

            elif isinstance(obj, list):
                return [substitute_env_vars(item) for item in obj]

            return obj

        # Apply PERFECT21_ prefixed environment variables
        env_overrides = {}
        for key, value in os.environ.items():
            if key.startswith("PERFECT21_"):
                config_key = key.replace("PERFECT21_", "").lower()
                # Convert to nested dict structure
                keys = config_key.split("_")
                current = env_overrides
                for k in keys[:-1]:
                    current = current.setdefault(k, {})
                current[keys[-1]] = value

        # Merge environment overrides
        if env_overrides:
            config = self._merge_configs(config, env_overrides)
            self.logger.debug(f"Applied {len(env_overrides)} environment overrides")

        # Substitute environment variables in values
        config = substitute_env_vars(config)

        return config

    def _validate_config(self, config: Dict[str, Any]) -> ConfigValidationResult:
        """Validate configuration against schema."""
        errors = []
        warnings = []

        try:
            # Extract metadata
            metadata_dict = config.get("metadata", {})
            metadata = ConfigMetadata(
                version=metadata_dict.get("version", "1.0.0"),
                name=metadata_dict.get("name", "Unknown"),
                description=metadata_dict.get("description", ""),
                last_updated=metadata_dict.get(
                    "last_updated", datetime.now().isoformat()
                ),
                schema_version=metadata_dict.get("schema_version", "1.0"),
                environment=config.get("environment", "development"),
            )

            # Required sections validation
            required_sections = [
                "metadata",
                "system",
                "workflow",
                "agents",
                "task_types",
            ]

            for section in required_sections:
                if section not in config:
                    errors.append(f"Required section missing: {section}")

            # Workflow validation
            if "workflow" in config:
                workflow = config["workflow"]
                if "phases" in workflow:
                    phases = workflow["phases"]
                    required_phases = [f"phase_{i}" for i in range(8)]

                    for phase in required_phases:
                        if phase not in phases:
                            warnings.append(f"Workflow phase missing: {phase}")

            # Agent strategy validation
            if "agents" in config:
                agents = config["agents"]
                if "strategy" in agents:
                    strategy = agents["strategy"]
                    required_strategies = [
                        "simple_tasks",
                        "standard_tasks",
                        "complex_tasks",
                    ]

                    for strat in required_strategies:
                        if strat not in strategy:
                            warnings.append(f"Agent strategy missing: {strat}")

            # Task types validation
            if "task_types" in config:
                task_types = config["task_types"]
                for task_name, task_config in task_types.items():
                    if "required_agents" not in task_config:
                        warnings.append(
                            f"Task type {task_name} missing required_agents"
                        )
                    if "minimum_count" not in task_config:
                        warnings.append(f"Task type {task_name} missing minimum_count")

            # Environment-specific validation
            env = metadata.environment
            if env == "production":
                # Production requires stricter settings
                if config.get("system", {}).get("mode") != "enforcement":
                    errors.append("Production environment must use enforcement mode")

                if not config.get("quality_gates", {}).get("enabled"):
                    errors.append(
                        "Production environment must have quality gates enabled"
                    )

            is_valid = len(errors) == 0

            return ConfigValidationResult(
                is_valid=is_valid, errors=errors, warnings=warnings, metadata=metadata
            )

        except Exception as e:
            return ConfigValidationResult(
                is_valid=False, errors=[f"Validation error: {e}"], warnings=warnings
            )

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached configuration is still valid."""
        if cache_key not in self._config_cache:
            return False

        # Check if any config files have been modified
        config_files = [
            self.config_dir.parent / "config.yaml",
            self.config_dir / "main.yaml",
            self.config_dir / "env" / f"{self.environment.value}.yaml",
        ]

        for file_path in config_files:
            if file_path.exists():
                current_mtime = file_path.stat().st_mtime
                cached_mtime = self._file_timestamps.get(str(file_path), 0)

                if current_mtime > cached_mtime:
                    return False

        return True

    def _update_file_timestamps(self):
        """Update cached file timestamps."""
        config_files = [
            self.config_dir.parent / "config.yaml",
            self.config_dir / "main.yaml",
            self.config_dir / "env" / f"{self.environment.value}.yaml",
        ]

        for file_path in config_files:
            if file_path.exists():
                self._file_timestamps[str(file_path)] = file_path.stat().st_mtime

    def get_config_value(
        self, key_path: str, default: Any = None, config: Dict[str, Any] = None
    ) -> Any:
        """
        Get configuration value by dot-notation path.

        Args:
            key_path: Dot-separated path (e.g., 'agents.strategy.simple_tasks')
            default: Default value if key not found
            config: Configuration dict (loads if None)

        Returns:
            Configuration value or default
        """
        if config is None:
            config = self.load_config()

        keys = key_path.split(".")
        current = config

        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default

    def set_config_value(
        self, key_path: str, value: Any, config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Set configuration value by dot-notation path.

        Args:
            key_path: Dot-separated path
            value: Value to set
            config: Configuration dict (loads if None)

        Returns:
            Updated configuration
        """
        if config is None:
            config = self.load_config()

        keys = key_path.split(".")
        current = config

        # Navigate to parent of target key
        for key in keys[:-1]:
            current = current.setdefault(key, {})

        # Set the value
        current[keys[-1]] = value

        # Invalidate cache
        cache_key = f"config_{self.environment.value}"
        if cache_key in self._config_cache:
            del self._config_cache[cache_key]

        return config

    def reload_config(self) -> Dict[str, Any]:
        """Force reload configuration from files."""
        self.logger.info("Force reloading configuration")
        return self.load_config(force_reload=True)

    def migrate_legacy_config(self, legacy_path: str) -> Dict[str, Any]:
        """
        Migrate legacy configuration files to new format.

        Args:
            legacy_path: Path to legacy configuration file

        Returns:
            Migrated configuration
        """
        legacy_file = Path(legacy_path)

        if not legacy_file.exists():
            raise ConfigurationError(f"Legacy config file not found: {legacy_path}")

        try:
            # Load legacy configuration
            with open(legacy_file, "r", encoding="utf-8") as f:
                if legacy_file.suffix == ".json":
                    legacy_config = json.load(f)
                else:
                    legacy_config = yaml.safe_load(f)

            # Create backup
            backup_path = legacy_file.with_suffix(
                f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}{legacy_file.suffix}'
            )
            legacy_file.rename(backup_path)
            self.logger.info(f"Legacy config backed up to: {backup_path}")

            # Migrate to new format
            migrated_config = self._convert_legacy_format(legacy_config)

            self.logger.info(f"Legacy configuration migrated from {legacy_path}")
            return migrated_config

        except Exception as e:
            raise ConfigurationError(f"Failed to migrate legacy config: {e}")

    def _convert_legacy_format(self, legacy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy configuration format to new unified format."""
        # This is a simplified migration - would need to be expanded based on actual legacy formats
        migrated = {
            "metadata": {
                "version": "1.0.0",
                "name": "Migrated Configuration",
                "description": "Migrated from legacy format",
                "last_updated": datetime.now().isoformat(),
                "schema_version": "1.0",
            }
        }

        # Map legacy settings.json format
        if "hooks" in legacy_config:
            migrated["hooks"] = legacy_config["hooks"]

        if "environment" in legacy_config:
            migrated["system"] = {
                "mode": legacy_config["environment"].get(
                    "CLAUDE_ENHANCER_MODE", "advisory"
                )
            }

        # Map other legacy formats as needed
        # This would be expanded based on actual legacy configuration structures

        return migrated


def create_config_loader(config_dir: str = None) -> ConfigurationLoader:
    """Factory function to create configuration loader."""
    return ConfigurationLoader(config_dir)


# CLI interface for configuration management
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Claude Enhancer Configuration Manager"
    )
    parser.add_argument("--config-dir", help="Configuration directory path")
    parser.add_argument(
        "--environment",
        choices=[e.value for e in ConfigEnvironment],
        help="Override environment",
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate configuration"
    )
    parser.add_argument(
        "--reload", action="store_true", help="Force reload configuration"
    )
    parser.add_argument("--get", help="Get configuration value (dot notation)")
    parser.add_argument("--migrate", help="Migrate legacy configuration file")

    args = parser.parse_args()

    # Create loader
    loader = create_config_loader(args.config_dir)

    try:
        if args.migrate:
            config = loader.migrate_legacy_config(args.migrate)
            print("✅ Legacy configuration migrated successfully")

        elif args.validate:
            config = loader.load_config()
            validation = loader._validate_config(config)

            if validation.is_valid:
                print("✅ Configuration is valid")
            else:
                print("❌ Configuration validation failed:")
                for error in validation.errors:
                    print(f"  • {error}")

            if validation.warnings:
                print("⚠️  Configuration warnings:")
                for warning in validation.warnings:
                    print(f"  • {warning}")

        elif args.get:
            config = loader.load_config()
            value = loader.get_config_value(args.get, config=config)
            print(f"{args.get}: {value}")

        else:
            config = loader.load_config(force_reload=args.reload)
            print(f"✅ Configuration loaded for {loader.environment.value} environment")
            print(f"📋 Configuration sections: {list(config.keys())}")

    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        exit(1)
