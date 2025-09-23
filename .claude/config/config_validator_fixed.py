#!/usr/bin/env python3
"""修复版配置验证器"""

import sys
import yaml
import json
from pathlib import Path


def validate_config():
    """验证配置文件"""
    config_file = Path(__file__).parent / "main.yaml"

    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        # 基础验证
        required_keys = ["metadata", "system", "workflow", "agents"]
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing required key: {key}")
                return False

        print("✅ Configuration valid")
        return True

    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        sys.exit(0 if validate_config() else 1)
    else:
        print("Usage: python3 config_validator_fixed.py validate")
