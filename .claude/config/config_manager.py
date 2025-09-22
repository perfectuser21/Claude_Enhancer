#!/usr/bin/env python3
"""
Perfect21 Configuration Manager
==============================

CLI tool for managing Perfect21 unified configuration system.
Provides commands for:
- Loading and validating configurations
- Managing environment-specific settings
- Hot reloading configurations
- Configuration health checks
- Environment switching

Author: Perfect21 System (Technical Writer & System Architect)
Version: 1.0.0
"""

import os
import sys
import argparse
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Add config directory to Python path
sys.path.append(str(Path(__file__).parent))

from config_loader import ConfigurationLoader, ConfigEnvironment, ValidationLevel, ConfigurationError
from migration_tool import ConfigMigrator

class ConfigManager:
    """Configuration management CLI."""

    def __init__(self, config_dir: str = None):
        """Initialize configuration manager."""
        self.config_dir = Path(config_dir) if config_dir else Path(".claude/config")
        self.loader = ConfigurationLoader(config_dir)
        self.migrator = ConfigMigrator()

    def status(self) -> Dict[str, Any]:
        """Get configuration system status."""
        try:
            config = self.loader.load_config()
            validation = self.loader._validate_config(config)

            status = {
                "environment": self.loader.environment.value,
                "config_valid": validation.is_valid,
                "config_version": config.get('metadata', {}).get('version', 'Unknown'),
                "total_sections": len(config),
                "main_config_exists": (self.config_dir / "main.yaml").exists(),
                "env_config_exists": (self.config_dir / "env" / f"{self.loader.environment.value}.yaml").exists(),
                "errors": validation.errors,
                "warnings": validation.warnings
            }

            return status

        except Exception as e:
            return {
                "environment": "unknown",
                "config_valid": False,
                "error": str(e)
            }

    def validate(self, environment: str = None) -> bool:
        """Validate configuration for specific environment."""
        try:
            env = ConfigEnvironment(environment) if environment else None
            config = self.loader.load_config(environment=env)
            validation = self.loader._validate_config(config)

    # print(f"🔍 Validating configuration for {(env or self.loader.environment).value} environment")

            if validation.is_valid:
    # print("✅ Configuration is valid")

                if validation.warnings:
    # print("\n⚠️  Warnings:")
                    for warning in validation.warnings:
    # print(f"  • {warning}")

                return True
            else:
    # print("❌ Configuration validation failed")
    # print("\n🚨 Errors:")
                for error in validation.errors:
    # print(f"  • {error}")

                if validation.warnings:
    # print("\n⚠️  Warnings:")
                    for warning in validation.warnings:
    # print(f"  • {warning}")

                return False

        except Exception as e:
    # print(f"❌ Validation error: {e}")
            return False

    def get(self, key_path: str, environment: str = None, format_output: str = "yaml") -> Any:
        """Get configuration value by key path."""
        try:
            env = ConfigEnvironment(environment) if environment else None
            config = self.loader.load_config(environment=env)
            value = self.loader.get_config_value(key_path, config=config)

            if value is None:
    # print(f"❌ Configuration key not found: {key_path}")
                return None

    # print(f"📋 {key_path}:")

            if format_output == "json":
    # print(json.dumps(value, indent=2))
            elif format_output == "yaml":
    # print(yaml.dump(value, default_flow_style=False))
            else:
    # print(value)

            return value

        except Exception as e:
    # print(f"❌ Error getting configuration: {e}")
            return None

    def set(self, key_path: str, value: str, environment: str = None) -> bool:
        """Set configuration value by key path."""
        try:
            env = ConfigEnvironment(environment) if environment else None
            config = self.loader.load_config(environment=env)

            # Parse value (try JSON first, then string)
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                parsed_value = value

            # Set the value
            updated_config = self.loader.set_config_value(key_path, parsed_value, config)

    # print(f"✅ Configuration updated: {key_path} = {parsed_value}")
            return True

        except Exception as e:
    # print(f"❌ Error setting configuration: {e}")
            return False

    def reload(self, environment: str = None) -> bool:
        """Reload configuration from files."""
        try:
            env = ConfigEnvironment(environment) if environment else None
            config = self.loader.load_config(force_reload=True, environment=env)

            env_name = (env or self.loader.environment).value
    # print(f"🔄 Configuration reloaded for {env_name} environment")
    # print(f"📊 Loaded {len(config)} configuration sections")
            return True

        except Exception as e:
    # print(f"❌ Error reloading configuration: {e}")
            return False

    def switch_environment(self, environment: str) -> bool:
        """Switch to different environment."""
        try:
            env = ConfigEnvironment(environment)

            # Check if environment configuration exists
            env_file = self.config_dir / "env" / f"{environment}.yaml"
            if not env_file.exists():
    # print(f"❌ Environment configuration not found: {env_file}")
                return False

            # Load configuration for new environment
            config = self.loader.load_config(environment=env)

            # Update environment variable
            os.environ['PERFECT21_ENV'] = environment

    # print(f"🔄 Switched to {environment} environment")
    # print(f"📊 Loaded {len(config)} configuration sections")
            return True

        except Exception as e:
    # print(f"❌ Error switching environment: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health = {
            "timestamp": self.loader._get_timestamp(),
            "overall_status": "healthy",
            "checks": {}
        }

        # Check main configuration
        main_file = self.config_dir / "main.yaml"
        health["checks"]["main_config"] = {
            "status": "pass" if main_file.exists() else "fail",
            "file": str(main_file),
            "exists": main_file.exists()
        }

        # Check environment configurations
        env_dir = self.config_dir / "env"
        health["checks"]["env_configs"] = {}

        for env in ConfigEnvironment:
            env_file = env_dir / f"{env.value}.yaml"
            health["checks"]["env_configs"][env.value] = {
                "status": "pass" if env_file.exists() else "warn",
                "file": str(env_file),
                "exists": env_file.exists()
            }

        # Check schema file
        schema_file = self.config_dir / "schemas" / "config_schema.yaml"
        health["checks"]["schema"] = {
            "status": "pass" if schema_file.exists() else "warn",
            "file": str(schema_file),
            "exists": schema_file.exists()
        }

        # Validate current configuration
        try:
            config = self.loader.load_config()
            validation = self.loader._validate_config(config)

            health["checks"]["validation"] = {
                "status": "pass" if validation.is_valid else "fail",
                "errors": validation.errors,
                "warnings": validation.warnings
            }
        except Exception as e:
            health["checks"]["validation"] = {
                "status": "fail",
                "error": str(e)
            }

        # Check for legacy configurations
        legacy_files = self.migrator.discover_legacy_configs()
        health["checks"]["legacy_configs"] = {
            "status": "warn" if legacy_files else "pass",
            "count": len(legacy_files),
            "files": [str(f) for f in legacy_files]
        }

        # Determine overall status
        failed_checks = [k for k, v in health["checks"].items()
                        if isinstance(v, dict) and v.get("status") == "fail"]

        if failed_checks:
            health["overall_status"] = "unhealthy"
        elif any(isinstance(v, dict) and v.get("status") == "warn"
                for v in health["checks"].values()):
            health["overall_status"] = "warning"

        return health

    def list_environments(self) -> Dict[str, Any]:
        """List available environments."""
        env_dir = self.config_dir / "env"
        environments = {}

        for env in ConfigEnvironment:
            env_file = env_dir / f"{env.value}.yaml"
            environments[env.value] = {
                "exists": env_file.exists(),
                "file": str(env_file),
                "current": env == self.loader.environment
            }

        return environments

    def migrate_legacy(self, backup: bool = True, cleanup: bool = False) -> bool:
        """Migrate legacy configuration files."""
        try:
    # print("🔍 Discovering legacy configuration files...")
            legacy_files = self.migrator.discover_legacy_configs()

            if not legacy_files:
    # print("✅ No legacy configuration files found")
                return True

    # print(f"📋 Found {len(legacy_files)} legacy configuration files:")
            for file_path in legacy_files:
    # print(f"  • {file_path}")

    # print("\n🚀 Starting migration...")
            report = self.migrator.migrate_all(backup=backup)

            if report['status'] == 'success':
    # print("✅ Migration completed successfully!")
            elif report['status'] == 'partial_failure':
    # print("⚠️  Migration completed with some errors")
            else:
    # print("❌ Migration failed")
                return False

    # print(f"\n📊 Migration Summary:")
    # print(f"  • Files processed: {len(report['files'])}")
    # print(f"  • Successful: {sum(1 for f in report['files'] if f['status'] == 'migrated')}")
    # print(f"  • Errors: {len(report['errors'])}")

            if report['errors']:
    # print("\n❌ Errors:")
                for error in report['errors']:
    # print(f"  • {error}")

            if cleanup:
                self.migrator.cleanup_legacy_files(legacy_files, confirm=False)

            return True

        except Exception as e:
    # print(f"❌ Migration failed: {e}")
            return False

    def backup_config(self, backup_dir: str = None) -> str:
        """Create backup of current configuration."""
        import shutil
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(backup_dir) if backup_dir else self.config_dir.parent / "config_backups"
        backup_path = backup_dir / f"config_backup_{timestamp}"

        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            shutil.copytree(self.config_dir, backup_path / "config")

    # print(f"✅ Configuration backed up to: {backup_path}")
            return str(backup_path)

        except Exception as e:
    # print(f"❌ Backup failed: {e}")
            raise


def main():
    """CLI interface."""
    parser = argparse.ArgumentParser(
        description="Perfect21 Configuration Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Global options
    parser.add_argument("--config-dir", help="Configuration directory path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show configuration status")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.add_argument("--environment", "-e", help="Environment to validate")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get configuration value")
    get_parser.add_argument("key", help="Configuration key path (dot notation)")
    get_parser.add_argument("--environment", "-e", help="Environment")
    get_parser.add_argument("--format", choices=["yaml", "json", "raw"], default="yaml", help="Output format")

    # Set command
    set_parser = subparsers.add_parser("set", help="Set configuration value")
    set_parser.add_argument("key", help="Configuration key path (dot notation)")
    set_parser.add_argument("value", help="Value to set (JSON or string)")
    set_parser.add_argument("--environment", "-e", help="Environment")

    # Reload command
    reload_parser = subparsers.add_parser("reload", help="Reload configuration")
    reload_parser.add_argument("--environment", "-e", help="Environment")

    # Switch command
    switch_parser = subparsers.add_parser("switch", help="Switch environment")
    switch_parser.add_argument("environment", choices=[e.value for e in ConfigEnvironment], help="Target environment")

    # Health command
    health_parser = subparsers.add_parser("health", help="Health check")

    # List command
    list_parser = subparsers.add_parser("list", help="List environments")

    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Migrate legacy configurations")
    migrate_parser.add_argument("--no-backup", action="store_true", help="Skip backup")
    migrate_parser.add_argument("--cleanup", action="store_true", help="Clean up legacy files")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Backup configuration")
    backup_parser.add_argument("--dir", help="Backup directory")

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # Create manager
    manager = ConfigManager(args.config_dir)

    try:
        if args.command == "status":
            status = manager.status()
    # print("📊 Configuration Status:")
    # print(f"  Environment: {status.get('environment', 'unknown')}")
    # print(f"  Valid: {'✅' if status.get('config_valid') else '❌'}")
    # print(f"  Version: {status.get('config_version', 'unknown')}")
    # print(f"  Sections: {status.get('total_sections', 0)}")

            if status.get('errors'):
    # print("\n❌ Errors:")
                for error in status['errors']:
    # print(f"  • {error}")

        elif args.command == "validate":
            success = manager.validate(args.environment)
            sys.exit(0 if success else 1)

        elif args.command == "get":
            value = manager.get(args.key, args.environment, args.format)
            sys.exit(0 if value is not None else 1)

        elif args.command == "set":
            success = manager.set(args.key, args.value, args.environment)
            sys.exit(0 if success else 1)

        elif args.command == "reload":
            success = manager.reload(args.environment)
            sys.exit(0 if success else 1)

        elif args.command == "switch":
            success = manager.switch_environment(args.environment)
            sys.exit(0 if success else 1)

        elif args.command == "health":
            health = manager.health_check()
            status_icon = {"healthy": "✅", "warning": "⚠️", "unhealthy": "❌"}

    # print(f"🏥 Configuration Health Check")
    # print(f"Overall Status: {status_icon.get(health['overall_status'], '❓')} {health['overall_status']}")

            for check_name, check_result in health['checks'].items():
                if isinstance(check_result, dict):
                    status = check_result.get('status', 'unknown')
                    icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(status, "❓")
    # print(f"  {check_name}: {icon} {status}")

                    if status == "fail" and check_result.get('errors'):
                        for error in check_result['errors']:
    # print(f"    • {error}")

        elif args.command == "list":
            environments = manager.list_environments()
    # print("🌍 Available Environments:")
            for env_name, env_info in environments.items():
                status = "✅ exists" if env_info['exists'] else "❌ missing"
                current = " (current)" if env_info['current'] else ""
    # print(f"  • {env_name}: {status}{current}")

        elif args.command == "migrate":
            success = manager.migrate_legacy(
                backup=not args.no_backup,
                cleanup=args.cleanup
            )
            sys.exit(0 if success else 1)

        elif args.command == "backup":
            backup_path = manager.backup_config(args.dir)

        else:
            parser.print_help()

    except KeyboardInterrupt:
    # print("\n❌ Operation cancelled")
        sys.exit(1)
    except Exception as e:
    # print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()