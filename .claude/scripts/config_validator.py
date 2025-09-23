#!/usr/bin/env python3

"""
Claude Enhancer Configuration Validator
Validates unified configuration against schema and business rules
"""

import sys
import yaml
import json
import jsonschema
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from datetime import datetime


class ConfigValidator:
    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.errors = []
        self.warnings = []
        self.info = []

    def log_error(self, message: str, section: str = None):
        """Log an error message"""
        error_msg = f"[ERROR] {f'{section}: ' if section else ''}{message}"
        self.errors.append(error_msg)
        print(error_msg, file=sys.stderr)

    def log_warning(self, message: str, section: str = None):
        """Log a warning message"""
        warning_msg = f"[WARNING] {f'{section}: ' if section else ''}{message}"
        self.warnings.append(warning_msg)
        print(warning_msg)

    def log_info(self, message: str, section: str = None):
        """Log an info message"""
        info_msg = f"[INFO] {f'{section}: ' if section else ''}{message}"
        self.info.append(info_msg)
        print(info_msg)

    def load_yaml_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load and parse YAML file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.log_error(f"Configuration file not found: {file_path}")
            return None
        except yaml.YAMLError as e:
            self.log_error(f"Invalid YAML syntax in {file_path}: {e}")
            return None
        except Exception as e:
            self.log_error(f"Error loading {file_path}: {e}")
            return None

    def load_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load and parse JSON file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            self.log_error(f"Configuration file not found: {file_path}")
            return None
        except json.JSONDecodeError as e:
            self.log_error(f"Invalid JSON syntax in {file_path}: {e}")
            return None
        except Exception as e:
            self.log_error(f"Error loading {file_path}: {e}")
            return None

    def validate_schema(self, config: Dict[str, Any], schema_file: Path) -> bool:
        """Validate configuration against JSON schema"""
        if not schema_file.exists():
            self.log_warning(f"Schema file not found: {schema_file}")
            return True  # Skip schema validation if schema not available

        try:
            schema = self.load_yaml_file(schema_file)
            if schema is None:
                return False

            jsonschema.validate(config, schema)
            self.log_info("Schema validation passed")
            return True

        except jsonschema.ValidationError as e:
            self.log_error(f"Schema validation failed: {e.message}", "schema")
            return False
        except Exception as e:
            self.log_error(f"Schema validation error: {e}", "schema")
            return False

    def validate_metadata(self, config: Dict[str, Any]) -> bool:
        """Validate metadata section"""
        metadata = config.get("metadata", {})
        valid = True

        # Check required fields
        required_fields = ["version", "name", "description", "schema_version"]
        for field in required_fields:
            if field not in metadata:
                self.log_error(f"Missing required metadata field: {field}", "metadata")
                valid = False

        # Validate version format
        version = metadata.get("version")
        if version and not self._is_valid_version(version):
            self.log_error(f"Invalid version format: {version}", "metadata")
            valid = False

        return valid

    def validate_system(self, config: Dict[str, Any]) -> bool:
        """Validate system section"""
        system = config.get("system", {})
        valid = True

        # Check required fields
        required_fields = ["name", "mode", "version"]
        for field in required_fields:
            if field not in system:
                self.log_error(f"Missing required system field: {field}", "system")
                valid = False

        # Validate mode
        mode = system.get("mode")
        valid_modes = ["advisory", "warning", "enforcement"]
        if mode and mode not in valid_modes:
            self.log_error(
                f"Invalid system mode: {mode}. Valid modes: {valid_modes}", "system"
            )
            valid = False

        return valid

    def validate_workflow(self, config: Dict[str, Any]) -> bool:
        """Validate workflow configuration"""
        workflow = config.get("workflow", {})
        phases = workflow.get("phases", {})
        valid = True

        # Check for all 8 phases
        expected_phases = [f"phase_{i}" for i in range(8)]
        for phase in expected_phases:
            if phase not in phases:
                self.log_error(f"Missing workflow phase: {phase}", "workflow")
                valid = False
                continue

            phase_config = phases[phase]

            # Validate required phase fields
            required_fields = ["name", "description", "required"]
            for field in required_fields:
                if field not in phase_config:
                    self.log_error(f"Missing field '{field}' in {phase}", "workflow")
                    valid = False

            # Validate agent counts
            agents_min = phase_config.get("agents_min")
            agents_max = phase_config.get("agents_max")

            if agents_min is not None and agents_max is not None:
                if agents_min > agents_max:
                    self.log_error(
                        f"agents_min ({agents_min}) > agents_max ({agents_max}) in {phase}",
                        "workflow",
                    )
                    valid = False

        return valid

    def validate_agents(self, config: Dict[str, Any]) -> bool:
        """Validate agent configuration"""
        agents = config.get("agents", {})
        valid = True

        # Validate strategy section
        strategy = agents.get("strategy", {})
        required_strategies = ["simple_tasks", "standard_tasks", "complex_tasks"]

        for strategy_name in required_strategies:
            if strategy_name not in strategy:
                self.log_error(f"Missing agent strategy: {strategy_name}", "agents")
                valid = False
                continue

            strategy_config = strategy[strategy_name]
            required_fields = ["agent_count", "duration", "description"]

            for field in required_fields:
                if field not in strategy_config:
                    self.log_error(
                        f"Missing field '{field}' in {strategy_name}", "agents"
                    )
                    valid = False

        # Validate execution section
        execution = agents.get("execution", {})
        required_execution_fields = ["mode", "enforce_parallel", "timeout"]

        for field in required_execution_fields:
            if field not in execution:
                self.log_error(f"Missing execution field: {field}", "agents")
                valid = False

        # Validate execution mode
        mode = execution.get("mode")
        valid_modes = ["parallel", "sequential", "mixed"]
        if mode and mode not in valid_modes:
            self.log_error(
                f"Invalid execution mode: {mode}. Valid modes: {valid_modes}", "agents"
            )
            valid = False

        return valid

    def validate_task_types(self, config: Dict[str, Any]) -> bool:
        """Validate task types configuration"""
        task_types = config.get("task_types", {})
        valid = True

        if not task_types:
            self.log_error("No task types defined", "task_types")
            return False

        for task_name, task_config in task_types.items():
            # Validate required fields
            required_fields = ["keywords", "required_agents", "minimum_count"]
            for field in required_fields:
                if field not in task_config:
                    self.log_error(
                        f"Missing field '{field}' in task type '{task_name}'",
                        "task_types",
                    )
                    valid = False

            # Validate keywords
            keywords = task_config.get("keywords", [])
            if not isinstance(keywords, list) or not keywords:
                self.log_error(
                    f"Task type '{task_name}' must have non-empty keywords list",
                    "task_types",
                )
                valid = False

            # Validate required_agents
            required_agents = task_config.get("required_agents", [])
            if not isinstance(required_agents, list) or not required_agents:
                self.log_error(
                    f"Task type '{task_name}' must have non-empty required_agents list",
                    "task_types",
                )
                valid = False

            # Validate minimum_count
            minimum_count = task_config.get("minimum_count")
            if minimum_count is not None:
                if not isinstance(minimum_count, int) or minimum_count < 1:
                    self.log_error(
                        f"Task type '{task_name}' minimum_count must be positive integer",
                        "task_types",
                    )
                    valid = False

                # Check if minimum_count matches required_agents count
                if len(required_agents) > minimum_count:
                    self.log_warning(
                        f"Task type '{task_name}' has more required_agents ({len(required_agents)}) than minimum_count ({minimum_count})",
                        "task_types",
                    )

        return valid

    def validate_hooks(self, config: Dict[str, Any]) -> bool:
        """Validate hooks configuration"""
        hooks = config.get("hooks", {})
        valid = True

        # Validate enforcement level
        enforcement_level = hooks.get("enforcement_level")
        valid_levels = ["advisory", "warning", "strict"]
        if enforcement_level and enforcement_level not in valid_levels:
            self.log_error(
                f"Invalid enforcement level: {enforcement_level}. Valid levels: {valid_levels}",
                "hooks",
            )
            valid = False

        # Validate hook sections
        hook_sections = ["pre_tool_use", "user_prompt_submit", "post_tool_use"]
        for section in hook_sections:
            section_hooks = hooks.get(section, [])
            if isinstance(section_hooks, list):
                for i, hook in enumerate(section_hooks):
                    if not self._validate_hook_definition(hook, f"{section}[{i}]"):
                        valid = False

        return valid

    def validate_quality_gates(self, config: Dict[str, Any]) -> bool:
        """Validate quality gates configuration"""
        quality_gates = config.get("quality_gates", {})
        valid = True

        checks = quality_gates.get("checks", [])
        if not isinstance(checks, list):
            self.log_error("Quality gates checks must be a list", "quality_gates")
            return False

        for i, check in enumerate(checks):
            required_fields = ["name", "description", "blocking"]
            for field in required_fields:
                if field not in check:
                    self.log_error(
                        f"Missing field '{field}' in quality gate check [{i}]",
                        "quality_gates",
                    )
                    valid = False

        return valid

    def validate_environments(self, config: Dict[str, Any]) -> bool:
        """Validate environment configurations"""
        environments = config.get("environments", {})
        valid = True

        expected_envs = ["development", "testing", "production"]
        for env in expected_envs:
            if env not in environments:
                self.log_warning(
                    f"Missing environment configuration: {env}", "environments"
                )

        # Validate each environment
        for env_name, env_config in environments.items():
            if "extends" in env_config:
                extends_file = self.config_dir / env_config["extends"]
                if not extends_file.exists():
                    self.log_error(
                        f"Environment '{env_name}' extends non-existent file: {env_config['extends']}",
                        "environments",
                    )
                    valid = False

        return valid

    def validate_cross_references(self, config: Dict[str, Any]) -> bool:
        """Validate cross-references between sections"""
        valid = True

        # Validate task type complexity references
        task_types = config.get("task_types", {})
        agent_strategy = config.get("agents", {}).get("strategy", {})

        for task_name, task_config in task_types.items():
            complexity = task_config.get("complexity")
            if complexity:
                strategy_key = f"{complexity}_tasks"
                if strategy_key not in agent_strategy:
                    self.log_error(
                        f"Task type '{task_name}' references unknown complexity '{complexity}'",
                        "cross_reference",
                    )
                    valid = False

        return valid

    def validate_business_rules(self, config: Dict[str, Any]) -> bool:
        """Validate business logic rules"""
        valid = True

        # Rule: Authentication tasks should have security auditor
        task_types = config.get("task_types", {})
        auth_task = task_types.get("authentication", {})
        required_agents = auth_task.get("required_agents", [])

        if "security-auditor" not in required_agents:
            self.log_error(
                "Authentication task type must include 'security-auditor'",
                "business_rules",
            )
            valid = False

        # Rule: Production mode should be enforcement
        environments = config.get("environments", {})
        prod_env = environments.get("production", {})
        prod_system = prod_env.get("system", {})
        prod_mode = prod_system.get("mode")

        if prod_mode and prod_mode != "enforcement":
            self.log_warning(
                f"Production mode should be 'enforcement', found: {prod_mode}",
                "business_rules",
            )

        # Rule: Complex tasks should have higher agent counts
        agents = config.get("agents", {})
        strategy = agents.get("strategy", {})

        simple_count = strategy.get("simple_tasks", {}).get("agent_count", 0)
        complex_count = strategy.get("complex_tasks", {}).get("agent_count", 0)

        if simple_count >= complex_count:
            self.log_error(
                f"Complex tasks agent count ({complex_count}) should be > simple tasks ({simple_count})",
                "business_rules",
            )
            valid = False

        return valid

    def _validate_hook_definition(self, hook: Dict[str, Any], context: str) -> bool:
        """Validate individual hook definition"""
        required_fields = ["name", "command", "description", "timeout", "enabled"]
        valid = True

        for field in required_fields:
            if field not in hook:
                self.log_error(f"Missing field '{field}' in hook {context}", "hooks")
                valid = False

        # Validate timeout
        timeout = hook.get("timeout")
        if timeout is not None and (not isinstance(timeout, int) or timeout <= 0):
            self.log_error(f"Hook {context} timeout must be positive integer", "hooks")
            valid = False

        return valid

    def _is_valid_version(self, version: str) -> bool:
        """Check if version follows semantic versioning"""
        import re

        pattern = r"^\d+\.\d+\.\d+$"
        return bool(re.match(pattern, version))

    def validate_config_file(self, config_file: Path, schema_file: Path = None) -> bool:
        """Validate a configuration file"""
        self.log_info(f"Validating configuration: {config_file}")

        # Load configuration
        config = self.load_yaml_file(config_file)
        if config is None:
            return False

        # Schema validation
        if schema_file and schema_file.exists():
            if not self.validate_schema(config, schema_file):
                return False

        # Section validations
        validations = [
            self.validate_metadata(config),
            self.validate_system(config),
            self.validate_workflow(config),
            self.validate_agents(config),
            self.validate_task_types(config),
            self.validate_hooks(config),
            self.validate_quality_gates(config),
            self.validate_environments(config),
            self.validate_cross_references(config),
            self.validate_business_rules(config),
        ]

        return all(validations)

    def generate_report(self, output_file: Path = None) -> str:
        """Generate validation report"""
        report = []
        report.append("# Claude Enhancer Configuration Validation Report")
        report.append(
            f"\n**Validation Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report.append(f"**Validator Version**: 2.0.0\n")

        # Summary
        total_issues = len(self.errors) + len(self.warnings)
        if total_issues == 0:
            report.append("## ✅ Validation Summary\n")
            report.append("**Status**: PASSED")
            report.append("**Issues Found**: 0")
        else:
            report.append("## ⚠️ Validation Summary\n")
            report.append(
                f"**Status**: {'FAILED' if self.errors else 'PASSED WITH WARNINGS'}"
            )
            report.append(f"**Errors**: {len(self.errors)}")
            report.append(f"**Warnings**: {len(self.warnings)}")

        # Errors
        if self.errors:
            report.append("\n## 🚨 Errors\n")
            for error in self.errors:
                report.append(f"- {error}")

        # Warnings
        if self.warnings:
            report.append("\n## ⚠️ Warnings\n")
            for warning in self.warnings:
                report.append(f"- {warning}")

        # Info
        if self.info:
            report.append("\n## ℹ️ Information\n")
            for info in self.info:
                report.append(f"- {info}")

        report_content = "\n".join(report)

        if output_file:
            output_file.write_text(report_content, encoding="utf-8")
            self.log_info(f"Report saved to: {output_file}")

        return report_content


def main():
    parser = argparse.ArgumentParser(
        description="Claude Enhancer Configuration Validator"
    )
    parser.add_argument("config_file", help="Configuration file to validate")
    parser.add_argument("--schema", help="Schema file for validation")
    parser.add_argument("--report", help="Output file for validation report")
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )

    args = parser.parse_args()

    config_file = Path(args.config_file)
    schema_file = Path(args.schema) if args.schema else None

    validator = ConfigValidator(config_file.parent)

    # Validate configuration
    is_valid = validator.validate_config_file(config_file, schema_file)

    # Generate report
    report_file = Path(args.report) if args.report else None
    report = validator.generate_report(report_file)

    if not report_file:
        print("\n" + report)

    # Exit with appropriate code
    if args.strict and validator.warnings:
        print("\nValidation failed (strict mode with warnings)", file=sys.stderr)
        sys.exit(1)
    elif not is_valid or validator.errors:
        print("\nValidation failed", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nValidation passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
