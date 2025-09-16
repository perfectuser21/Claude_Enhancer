#!/usr/bin/env python3
"""
Version Manager导入修复包装器
解决模块导入路径问题
"""

import os
import sys
import importlib.util
from pathlib import Path

def get_version_manager():
    """动态获取VersionManager类"""
    try:
        # 尝试正常导入
        from features.version_manager import get_global_version_manager
        return get_global_version_manager()
    except ImportError:
        # 使用动态导入
        current_dir = Path(__file__).parent
        vm_file = current_dir / "features" / "version_manager" / "version_manager.py"

        if vm_file.exists():
            spec = importlib.util.spec_from_file_location("version_manager_module", vm_file)
            vm_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(vm_module)

            return vm_module.VersionManager()
        else:
            raise ImportError(f"无法找到version_manager.py: {vm_file}")

def test_version_manager():
    """测试版本管理器功能"""
    try:
        vm = get_version_manager()
        version = vm.get_current_version()
        print(f"✅ Version Manager测试成功，版本: {version}")
        return True
    except Exception as e:
        print(f"❌ Version Manager测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_version_manager()
    sys.exit(0 if success else 1)
