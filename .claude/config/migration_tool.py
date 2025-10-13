#!/usr/bin/env python3
"""
Claude Enhancer Configuration Migration Tool
=====================================

Migrates legacy configuration files to the new unified format.
Supports migration from:
- settings.json (Claude Code settings)
- config.yaml (Hook configuration)
- enhancer_config.yaml (Enhancer-specific settings)
- task_agent_mapping.yaml (Task-agent mappings)

Author: Claude Enhancer System (DevOps Engineer & System Architect)
Version: 1.0.0
"""

import os
import yaml
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging


class ConfigMigrator:
    """Configuration migration utility."""

    def __init__(self, project_root: str = None):
        """Initialize migration tool."""
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.claude_dir = self.project_root / ".claude"
        self.config_dir = self.claude_dir / "config"
        self.logger = self._setup_logging()

        # Migration mappings
        self.migration_mappings = {
            "settings.json": self._migrate_settings_json,
            "config.yaml": self._migrate_config_yaml,
            "enhancer_config.yaml": self._migrate_enhancer_config,
            "task_agent_mapping.yaml": self._migrate_task_agent_mapping,
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for migration tool."""
        logger = logging.getLogger("claude-enhancer.migration")

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] Migration: %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    def discover_legacy_configs(self) -> List[Path]:
        """Discover legacy configuration files."""
        legacy_files = []

        search_paths = [self.claude_dir, self.claude_dir / "hooks", self.project_root]

        for search_path in search_paths:
            if not search_path.exists():
                continue

            for pattern in self.migration_mappings.keys():
                files = list(search_path.glob(pattern))
                legacy_files.extend(files)

        # Remove duplicates and sort
        unique_files = list(set(legacy_files))
        unique_files.sort()

        self.logger.info(f"Discovered {len(unique_files)} legacy configuration files")
        return unique_files

    def migrate_all(self, backup: bool = True) -> Dict[str, Any]:
        """
        Migrate all discovered legacy configurations.

        Args:
            backup: Whether to backup original files

        Returns:
            Migration report
        """
        legacy_files = self.discover_legacy_configs()

        if not legacy_files:
            self.logger.info("No legacy configuration files found")
            return {"status": "no_files", "files": []}

        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "env").mkdir(exist_ok=True)

        # Initialize unified configuration
        unified_config = self._create_base_config()

        migration_report = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "files": [],
            "errors": [],
            "warnings": [],
        }

        # Process each legacy file
        for legacy_file in legacy_files:
            try:
                self.logger.info(f"Migrating: {legacy_file}")

                # Backup original file
                if backup:
                    backup_path = self._backup_file(legacy_file)
                    self.logger.info(f"Backed up to: {backup_path}")

                # Load legacy configuration
                legacy_config = self._load_legacy_file(legacy_file)

                # Migrate configuration
                migrated_data = self._migrate_legacy_config(legacy_file, legacy_config)

                # Merge into unified configuration
                unified_config = self._merge_migrated_data(
                    unified_config, migrated_data
                )

                migration_report["files"].append(
                    {
                        "file": str(legacy_file),
                        "status": "migrated",
                        "backup": str(backup_path) if backup else None,
                    }
                )

            except Exception as e:
                error_msg = f"Failed to migrate {legacy_file}: {e}"
                self.logger.error(error_msg)
                migration_report["errors"].append(error_msg)
                migration_report["files"].append(
                    {"file": str(legacy_file), "status": "error", "error": str(e)}
                )

        # Save unified configuration
        try:
            self._save_unified_config(unified_config)
            self.logger.info("Unified configuration saved successfully")
        except Exception as e:
            migration_report["errors"].append(f"Failed to save unified config: {e}")
            migration_report["status"] = "partial_failure"

        # Generate migration report
        self._save_migration_report(migration_report)

        return migration_report

    def _create_base_config(self) -> Dict[str, Any]:
        """Create base unified configuration structure."""
        return {
            "metadata": {
                "version": "1.0.0",
                "name": "Claude Enhancer Configuration System",
                "description": "Migrated from legacy configuration files",
                "last_updated": datetime.now().isoformat(),
                "schema_version": "1.0",
            },
            "system": {
                "name": "Claude Enhancer Claude Enhancer",
                "mode": "enforcement",
                "version": "4.0.0",
                "description": "强制循环直到符合标准",
            },
            "workflow": {"phases": {}},
            "agents": {"strategy": {}, "execution": {}, "selection": {}},
            "task_types": {},
            "hooks": {
                "enabled": True,
                "enforcement_level": "strict",
                "pre_tool_use": [],
                "user_prompt_submit": [],
                "post_tool_use": [],
            },
            "quality_gates": {"enabled": True, "strict_mode": True, "checks": []},
            "logging": {
                "enabled": True,
                "level": "INFO",
                "file": "/tmp/claude-enhancer-config.log",
            },
            "performance": {
                "cache": {"enabled": True, "ttl": 300},
                "parallel_execution": {"max_concurrent_agents": 10, "timeout": 30000},
            },
            "security": {"validation": {"enabled": True, "strict_mode": True}},
            "integrations": {"git_hooks": {"enabled": True, "auto_install": False}},
            "notifications": {"enabled": True, "formats": ["emoji"]},
            "whitelist": {
                "operations": ["rollback", "hotfix", "emergency"],
                "paths": ["*.md", "*/test/*", "*/docs/*"],
            },
        }

    def _load_legacy_file(self, file_path: Path) -> Dict[str, Any]:
        """Load legacy configuration file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.suffix == ".json":
                    return json.load(f)
                else:
                    return yaml.safe_load(f) or {}
        except Exception as e:
            raise Exception(f"Failed to load {file_path}: {e}")

    def _migrate_legacy_config(
        self, file_path: Path, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Migrate specific legacy configuration file."""
        filename = file_path.name

        for pattern, migrator in self.migration_mappings.items():
            if filename == pattern or file_path.match(pattern):
                return migrator(config)

        # Fallback migration
        return self._migrate_generic_config(config)

    def _migrate_settings_json(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate settings.json (Claude Code settings)."""
        migrated = {}

        # Migrate hooks
        if "hooks" in config:
            hooks = config["hooks"]
            migrated["hooks"] = {"enabled": True, "enforcement_level": "strict"}

            # Migrate hook definitions
            for event, hook_list in hooks.items():
                if event in ["PreToolUse", "PostToolUse", "UserPromptSubmit"]:
                    event_key = self._convert_hook_event_name(event)
                    migrated["hooks"][event_key] = []

                    for hook in hook_list:
                        migrated_hook = {
                            "name": hook.get("description", "Unknown")
                            .replace(" ", "_")
                            .lower(),
                            "command": hook.get("command", ""),
                            "description": hook.get("description", ""),
                            "timeout": hook.get("timeout", 5000),
                            "enabled": True,
                        }

                        if "matcher" in hook:
                            migrated_hook["matcher"] = hook["matcher"]

                        migrated["hooks"][event_key].append(migrated_hook)

        # Migrate environment variables
        if "environment" in config:
            env = config["environment"]
            migrated["system"] = {
                "mode": env.get("CLAUDE_ENHANCER_MODE", "enforcement"),
                "version": config.get("version", "4.0.0"),
            }

            # Migrate agent settings
            migrated["agents"] = {
                "execution": {
                    "enforce_parallel": env.get("ENFORCE_PARALLEL", "true").lower()
                    == "true",
                    "timeout": 30000,
                },
                "selection": {"enforce_minimum": True},
            }

            # Migrate other environment settings
            if "MIN_AGENTS" in env:
                migrated["agents"]["selection"]["minimum_agents"] = int(
                    env["MIN_AGENTS"]
                )

        return migrated

    def _migrate_config_yaml(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate config.yaml (Hook configuration)."""
        migrated = {}

        # Migrate rules
        if "rules" in config:
            rules = config["rules"]
            migrated["agents"] = {
                "selection": {
                    "enforce_minimum": rules.get("block_on_violation", True),
                    "show_recommendations": rules.get("suggest_agents", True),
                },
                "execution": {
                    "enforce_parallel": rules.get("enforce_parallel", True),
                    "warn_sequential": rules.get("warn_sequential", True),
                    "block_on_violation": rules.get("block_on_violation", True),
                },
            }

            if "min_agents" in rules:
                migrated["agents"]["selection"]["minimum_agents"] = rules["min_agents"]

        # Migrate task types
        if "task_types" in config:
            migrated["task_types"] = {}
            for task_name, task_config in config["task_types"].items():
                migrated["task_types"][task_name] = {
                    "keywords": task_config.get("keywords", []),
                    "required_agents": task_config.get("required_agents", []),
                    "minimum_count": task_config.get("min_count", 3),
                    "complexity": "standard",
                }

        # Migrate logging
        if "logging" in config:
            logging_config = config["logging"]
            migrated["logging"] = {
                "enabled": logging_config.get("enabled", True),
                "level": logging_config.get("level", "INFO"),
                "file": logging_config.get("file", "/tmp/claude-hooks.log"),
            }

        # Migrate whitelist
        if "whitelist" in config:
            whitelist = config["whitelist"]
            migrated["whitelist"] = {
                "operations": whitelist.get("operations", []),
                "paths": whitelist.get("paths", []),
            }

        return migrated

    def _migrate_enhancer_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate enhancer_config.yaml."""
        migrated = {}

        # Migrate hooks configuration
        if "hooks" in config:
            hooks = config["hooks"]
            migrated["hooks"] = {
                "enabled": True,
                "enforcement_level": "strict"
                if hooks.get("agent_validator", {}).get("strict")
                else "warning",
            }

            # Migrate quality gates
            if "quality_gates" in hooks:
                quality_gates = hooks["quality_gates"]
                migrated["quality_gates"] = {
                    "enabled": quality_gates.get("enabled", True),
                    "strict_mode": True,
                    "checks": [],
                }

                for check in quality_gates.get("checks", []):
                    migrated["quality_gates"]["checks"].append(
                        {
                            "name": check.replace("_", "_validation"),
                            "description": f"Validate {check.replace('_', ' ')}",
                            "blocking": True,
                        }
                    )

        # Migrate execution modes
        if "execution_modes" in config:
            modes = config["execution_modes"]
            migrated["agents"] = migrated.get("agents", {})
            migrated["agents"]["execution"] = {
                "mode": "parallel",
                "enforce_parallel": True,
                "timeout": 30000,
            }

        # Migrate task types
        if "task_types" in config:
            migrated["task_types"] = {}
            for task_name, task_config in config["task_types"].items():
                migrated["task_types"][task_name] = {
                    "keywords": task_config.get("keywords", []),
                    "required_agents": task_config.get("required", [])
                    + task_config.get("recommended", []),
                    "minimum_count": len(task_config.get("required", [])),
                    "complexity": "standard",
                }

        return migrated

    def _migrate_task_agent_mapping(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate task_agent_mapping.yaml."""
        migrated = {}

        # Migrate task types
        if "task_types" in config:
            migrated["task_types"] = {}
            for task_name, task_config in config["task_types"].items():
                migrated["task_types"][task_name] = {
                    "keywords": task_config.get("keywords", []),
                    "required_agents": task_config.get("required_agents", []),
                    "minimum_count": task_config.get("minimum_count", 3),
                    "complexity": self._determine_complexity(
                        task_config.get("minimum_count", 3)
                    ),
                }

        # Migrate execution modes
        if "execution_modes" in config:
            modes = config["execution_modes"]
            migrated["agents"] = {
                "execution": {
                    "mode": "parallel",
                    "enforce_parallel": True,
                    "timeout": 30000,
                }
            }

        # Migrate quality gates
        if "quality_gates" in config:
            gates = config["quality_gates"]
            migrated["quality_gates"] = {
                "enabled": True,
                "strict_mode": True,
                "checks": [],
            }

            for check_type in ["before_execution", "after_execution"]:
                if check_type in gates:
                    for check in gates[check_type]:
                        migrated["quality_gates"]["checks"].append(
                            {
                                "name": check,
                                "description": f"Quality gate: {check.replace('_', ' ')}",
                                "blocking": True,
                            }
                        )

        return migrated

    def _migrate_generic_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generic migration for unknown configuration files."""
        migrated = {}

        # Try to extract common patterns
        if "agents" in config:
            migrated["agents"] = config["agents"]

        if "tasks" in config or "task_types" in config:
            task_section = config.get("tasks") or config.get("task_types")
            migrated["task_types"] = task_section

        if "hooks" in config:
            migrated["hooks"] = config["hooks"]

        return migrated

    def _merge_migrated_data(
        self, base_config: Dict[str, Any], migrated_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge migrated data into base configuration."""

        def deep_merge(base: Dict, override: Dict) -> Dict:
            result = base.copy()

            for key, value in override.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = deep_merge(result[key], value)
                elif (
                    key in result
                    and isinstance(result[key], list)
                    and isinstance(value, list)
                ):
                    # Merge lists, avoiding duplicates for simple values
                    combined = result[key] + value
                    if all(
                        isinstance(item, (str, int, float, bool)) for item in combined
                    ):
                        result[key] = list(set(combined))
                    else:
                        result[key] = combined
                else:
                    result[key] = value

            return result

        return deep_merge(base_config, migrated_data)

    def _save_unified_config(self, config: Dict[str, Any]):
        """Save unified configuration to main.yaml."""
        main_config_path = self.config_dir / "main.yaml"

        with open(main_config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)

        self.logger.info(f"Unified configuration saved to: {main_config_path}")

    def _save_migration_report(self, report: Dict[str, Any]):
        """Save migration report."""
        report_path = self.config_dir / "migration_report.json"

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Migration report saved to: {report_path}")

    def _backup_file(self, file_path: Path) -> Path:
        """Create backup of original file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".backup.{timestamp}{file_path.suffix}")

        shutil.copy2(file_path, backup_path)
        return backup_path

    def _convert_hook_event_name(self, event_name: str) -> str:
        """Convert hook event names to new format."""
        mapping = {
            "PreToolUse": "pre_tool_use",
            "PostToolUse": "post_tool_use",
            "UserPromptSubmit": "user_prompt_submit",
        }
        return mapping.get(event_name, event_name.lower())

    def _determine_complexity(self, agent_count: int) -> str:
        """Determine task complexity based on agent count."""
        if agent_count <= 3:
            return "simple"
        elif agent_count <= 6:
            return "standard"
        else:
            return "complex"

    def cleanup_legacy_files(self, files: List[Path], confirm: bool = True):
        """Clean up legacy configuration files after successful migration."""
        if confirm:
            response = input(f"Delete {len(files)} legacy configuration files? (y/N): ")
            if response.lower() != "y":
                self.logger.info("Legacy file cleanup cancelled")
                return

        deleted_count = 0
        for file_path in files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    deleted_count += 1
                    self.logger.info(f"Deleted: {file_path}")
            except Exception as e:
                self.logger.error(f"Failed to delete {file_path}: {e}")

        self.logger.info(f"Cleaned up {deleted_count} legacy configuration files")


def main():
    """CLI interface for migration tool."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Claude Enhancer Configuration Migration Tool"
    )
    parser.add_argument("--project-root", help="Project root directory")
    parser.add_argument(
        "--no-backup", action="store_true", help="Skip backing up original files"
    )
    parser.add_argument(
        "--cleanup", action="store_true", help="Clean up legacy files after migration"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force migration without confirmation"
    )
    parser.add_argument(
        "--discover-only", action="store_true", help="Only discover legacy files"
    )

    args = parser.parse_args()

    # Create migrator
    migrator = ConfigMigrator(args.project_root)

    try:
        if args.discover_only:
            legacy_files = migrator.discover_legacy_configs()
            # print(f"📋 Found {len(legacy_files)} legacy configuration files:")
            for file_path in legacy_files:
                pass  # print(f"  • {file_path}")
            return

        # Discover legacy files
        legacy_files = migrator.discover_legacy_configs()

        if not legacy_files:
            pass  # Auto-fixed empty block
            # print("✅ No legacy configuration files found")
            return

        # print(f"📋 Found {len(legacy_files)} legacy configuration files:")
        for file_path in legacy_files:
            pass  # print(f"  • {file_path}")

        # Confirm migration
        if not args.force:
            response = input("\n🔄 Proceed with migration? (y/N): ")
            if response.lower() != "y":
                pass  # print("❌ Migration cancelled")
                return

        # Perform migration
        # print("\n🚀 Starting migration...")
        report = migrator.migrate_all(backup=not args.no_backup)

        # Display results
        if report["status"] == "success":
            pass  # print("✅ Migration completed successfully!")
        elif report["status"] == "partial_failure":
            pass  # print("⚠️  Migration completed with some errors")
        else:
            pass  # print("❌ Migration failed")

        pass  # print(f"\n📊 Migration Summary:")
        # print(f"  • Files processed: {len(report['files'])}")
        # print(f"  • Successful: {sum(1 for f in report['files'] if f['status'] == 'migrated')}")
        # print(f"  • Errors: {len(report['errors'])}")

        if report["errors"]:
            pass  # print("\n❌ Errors:")
            for error in report["errors"]:
                pass  # print(f"  • {error}")

        # Clean up legacy files
        if args.cleanup and report["status"] in ["success", "partial_failure"]:
            migrator.cleanup_legacy_files(legacy_files, confirm=not args.force)

        pass  # print(f"\n📁 Configuration saved to: {migrator.config_dir / 'main.yaml'}")
        pass  # print(f"📄 Migration report: {migrator.config_dir / 'migration_report.json'}")

    except Exception as e:
        pass  # print(f"❌ Migration failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
