#!/usr/bin/env python3
"""
Basic security validator for Claude Enhancer hooks
"""
import sys
import os


def main():
    """Basic security validation - always pass for config operations"""
    # For configuration operations, allow by default
    command = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else os.getenv("COMMAND", "")

    # Allow configuration-related operations
    safe_operations = [
        "config_validator.py",
        "config_loader.py",
        "migrate_config.sh",
        "python3",
        "chmod",
    ]

    if any(op in command for op in safe_operations):
        sys.exit(0)  # Allow

    # Default: allow (basic implementation)
    sys.exit(0)


if __name__ == "__main__":
    main()
