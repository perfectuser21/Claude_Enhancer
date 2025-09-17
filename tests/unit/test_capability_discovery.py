#!/usr/bin/env python3
"""
Capability Discovery模块测试
测试能力发现、注册和验证功能
"""

import os
import sys
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from features.capability_discovery.capability import CapabilityLoader, Capability
from features.capability_discovery.registry import CapabilityRegistry

class TestCapabilityDiscovery:
    """能力发现测试类"""

    @pytest.fixture
    def temp_capability_dir(self):
        """临时能力目录"""
        temp_dir = tempfile.mkdtemp(prefix="capabilities_")
        yield temp_dir
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def sample_capability(self, temp_capability_dir):
        """示例能力文件"""
        capability_data = {
            "name": "test_capability",
            "version": "1.0.0",
            "description": "Test capability for unit testing",
            "entry_point": "test_module.main",
            "dependencies": ["requests", "json"],
            "metadata": {
                "category": "testing",
                "author": "test_user"
            }
        }

        capability_file = os.path.join(temp_capability_dir, "test_capability.json")
        with open(capability_file, 'w') as f:
            json.dump(capability_data, f)

        return capability_file, capability_data

    def test_capability_loader_initialization(self):
        """测试能力加载器初始化"""
        loader = CapabilityLoader()
        assert loader is not None
        assert hasattr(loader, 'scan_capabilities')
        assert hasattr(loader, 'load_capability')

    def test_capability_scanning(self, temp_capability_dir, sample_capability):
        """测试能力扫描功能"""
        loader = CapabilityLoader()
        capabilities = loader.scan_capabilities(temp_capability_dir)

        assert len(capabilities) > 0
        assert "test_capability" in [cap.name for cap in capabilities]

    def test_capability_loading(self, sample_capability):
        """测试能力加载功能"""
        capability_file, expected_data = sample_capability
        loader = CapabilityLoader()

        capability = loader.load_capability(capability_file)

        assert capability is not None
        assert capability.name == expected_data["name"]
        assert capability.version == expected_data["version"]
        assert capability.description == expected_data["description"]

    def test_capability_validation(self, sample_capability):
        """测试能力验证功能"""
        capability_file, capability_data = sample_capability
        loader = CapabilityLoader()

        capability = loader.load_capability(capability_file)
        is_valid = loader.validate_capability(capability)

        assert is_valid is True

    def test_invalid_capability_handling(self, temp_capability_dir):
        """测试无效能力文件处理"""
        # 创建无效的能力文件
        invalid_file = os.path.join(temp_capability_dir, "invalid.json")
        with open(invalid_file, 'w') as f:
            f.write("invalid json content")

        loader = CapabilityLoader()

        with pytest.raises(Exception):
            loader.load_capability(invalid_file)

    def test_capability_registry_initialization(self):
        """测试能力注册器初始化"""
        registry = CapabilityRegistry()
        assert registry is not None
        assert hasattr(registry, 'register_capability')
        assert hasattr(registry, 'get_capability')
        assert hasattr(registry, 'list_capabilities')

    def test_capability_registration(self, sample_capability):
        """测试能力注册功能"""
        capability_file, capability_data = sample_capability
        loader = CapabilityLoader()
        registry = CapabilityRegistry()

        capability = loader.load_capability(capability_file)
        result = registry.register_capability(capability)

        assert result is True
        assert registry.get_capability("test_capability") is not None

    def test_capability_listing(self, sample_capability):
        """测试能力列表功能"""
        capability_file, capability_data = sample_capability
        loader = CapabilityLoader()
        registry = CapabilityRegistry()

        capability = loader.load_capability(capability_file)
        registry.register_capability(capability)

        capabilities = registry.list_capabilities()
        assert len(capabilities) > 0
        assert "test_capability" in [cap.name for cap in capabilities]

    def test_capability_dependency_resolution(self, sample_capability):
        """测试能力依赖解析"""
        capability_file, capability_data = sample_capability
        loader = CapabilityLoader()

        capability = loader.load_capability(capability_file)
        dependencies = capability.dependencies

        assert "requests" in dependencies
        assert "json" in dependencies

    @patch('importlib.import_module')
    def test_capability_execution(self, mock_import, sample_capability):
        """测试能力执行"""
        mock_module = Mock()
        mock_module.main = Mock(return_value="success")
        mock_import.return_value = mock_module

        capability_file, capability_data = sample_capability
        loader = CapabilityLoader()
        capability = loader.load_capability(capability_file)

        # 模拟执行能力
        result = capability.execute()
        assert result == "success"

    def test_capability_metadata_handling(self, sample_capability):
        """测试能力元数据处理"""
        capability_file, capability_data = sample_capability
        loader = CapabilityLoader()

        capability = loader.load_capability(capability_file)

        assert capability.metadata["category"] == "testing"
        assert capability.metadata["author"] == "test_user"

    def test_capability_error_handling(self, temp_capability_dir):
        """测试能力错误处理"""
        loader = CapabilityLoader()

        # 测试不存在的文件
        with pytest.raises(FileNotFoundError):
            loader.load_capability("nonexistent.json")

        # 测试空目录扫描
        empty_dir = os.path.join(temp_capability_dir, "empty")
        os.makedirs(empty_dir, exist_ok=True)

        capabilities = loader.scan_capabilities(empty_dir)
        assert len(capabilities) == 0

class TestCapabilityIntegration:
    """能力发现集成测试"""

    def test_end_to_end_capability_workflow(self, temp_capability_dir):
        """测试端到端能力工作流"""
        # 1. 创建能力文件
        capability_data = {
            "name": "integration_test",
            "version": "1.0.0",
            "description": "Integration test capability",
            "entry_point": "test_module.main",
            "dependencies": [],
            "metadata": {
                "category": "integration"
            }
        }

        capability_file = os.path.join(temp_capability_dir, "integration_test.json")
        with open(capability_file, 'w') as f:
            json.dump(capability_data, f)

        # 2. 扫描和加载
        loader = CapabilityLoader()
        capabilities = loader.scan_capabilities(temp_capability_dir)

        assert len(capabilities) == 1
        capability = capabilities[0]

        # 3. 注册
        registry = CapabilityRegistry()
        result = registry.register_capability(capability)

        assert result is True

        # 4. 验证注册结果
        registered_capability = registry.get_capability("integration_test")
        assert registered_capability is not None
        assert registered_capability.name == "integration_test"

    def test_multiple_capabilities_management(self, temp_capability_dir):
        """测试多个能力管理"""
        # 创建多个能力文件
        capabilities_data = [
            {"name": "cap1", "version": "1.0.0", "description": "Capability 1", "entry_point": "cap1.main"},
            {"name": "cap2", "version": "1.0.0", "description": "Capability 2", "entry_point": "cap2.main"},
            {"name": "cap3", "version": "1.0.0", "description": "Capability 3", "entry_point": "cap3.main"}
        ]

        for cap_data in capabilities_data:
            cap_file = os.path.join(temp_capability_dir, f"{cap_data['name']}.json")
            with open(cap_file, 'w') as f:
                json.dump(cap_data, f)

        # 扫描和注册所有能力
        loader = CapabilityLoader()
        registry = CapabilityRegistry()

        capabilities = loader.scan_capabilities(temp_capability_dir)
        assert len(capabilities) == 3

        for capability in capabilities:
            registry.register_capability(capability)

        # 验证所有能力都已注册
        all_capabilities = registry.list_capabilities()
        assert len(all_capabilities) == 3

        capability_names = [cap.name for cap in all_capabilities]
        assert "cap1" in capability_names
        assert "cap2" in capability_names
        assert "cap3" in capability_names