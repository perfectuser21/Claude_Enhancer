#!/usr/bin/env python3
"""
Perfect21功能扫描器
自动发现features目录中的功能模块
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import importlib.util

logger = logging.getLogger("CapabilityScanner")

class CapabilityScanner:
    """功能模块扫描器"""

    def __init__(self, features_root: str = None):
        """
        初始化扫描器

        Args:
            features_root: features目录路径，默认为当前目录的features子目录
        """
        self.features_root = features_root or os.path.join(os.getcwd(), 'features')
        self.capabilities_cache = {}
        self.last_scan_time = 0

        logger.info(f"功能扫描器初始化 - 扫描目录: {self.features_root}")

    def scan_all_features(self) -> Dict[str, Any]:
        """
        扫描所有功能模块

        Returns:
            Dict: 发现的所有功能模块信息
        """
        logger.info("开始扫描所有功能模块...")

        capabilities = {}
        features_path = Path(self.features_root)

        if not features_path.exists():
            logger.warning(f"features目录不存在: {self.features_root}")
            return capabilities

        # 遍历features目录
        for feature_dir in features_path.iterdir():
            if not feature_dir.is_dir():
                continue

            if feature_dir.name.startswith('.') or feature_dir.name == '__pycache__':
                continue

            logger.debug(f"扫描功能目录: {feature_dir.name}")

            # 查找功能描述文件
            capability_info = self._scan_feature_directory(feature_dir)
            if capability_info:
                capabilities[feature_dir.name] = capability_info
                logger.info(f"发现功能: {feature_dir.name}")

        logger.info(f"扫描完成，发现 {len(capabilities)} 个功能模块")
        self.capabilities_cache = capabilities

        return capabilities

    def _scan_feature_directory(self, feature_dir: Path) -> Optional[Dict[str, Any]]:
        """
        扫描单个功能目录

        Args:
            feature_dir: 功能目录路径

        Returns:
            Optional[Dict]: 功能信息，如果找不到描述文件则返回None
        """
        capability_files = [
            'capability.py',
            'capability.yaml',
            'capability.json',
            'feature.py'
        ]

        for filename in capability_files:
            capability_file = feature_dir / filename
            if capability_file.exists():
                try:
                    return self._load_capability_file(capability_file)
                except Exception as e:
                    logger.error(f"加载功能描述文件失败: {capability_file} - {e}")
                    continue

        # 如果没有找到描述文件，尝试自动生成基本信息
        logger.warning(f"功能目录 {feature_dir.name} 缺少描述文件")
        return self._generate_basic_capability(feature_dir)

    def _load_capability_file(self, capability_file: Path) -> Dict[str, Any]:
        """
        加载功能描述文件

        Args:
            capability_file: 功能描述文件路径

        Returns:
            Dict: 功能信息
        """
        if capability_file.suffix == '.py':
            return self._load_python_capability(capability_file)
        elif capability_file.suffix == '.yaml':
            return self._load_yaml_capability(capability_file)
        elif capability_file.suffix == '.json':
            return self._load_json_capability(capability_file)
        else:
            raise ValueError(f"不支持的功能描述文件格式: {capability_file.suffix}")

    def _load_python_capability(self, capability_file: Path) -> Dict[str, Any]:
        """加载Python格式的功能描述"""
        spec = importlib.util.spec_from_file_location("capability", capability_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, 'CAPABILITY'):
            capability = module.CAPABILITY
            # 添加元信息
            capability['_meta'] = {
                'source_file': str(capability_file),
                'format': 'python',
                'feature_directory': str(capability_file.parent)
            }
            return capability
        else:
            raise ValueError("Python功能描述文件必须包含CAPABILITY字典")

    def _load_yaml_capability(self, capability_file: Path) -> Dict[str, Any]:
        """加载YAML格式的功能描述"""
        try:
            import yaml
            with open(capability_file, 'r', encoding='utf-8') as f:
                capability = yaml.safe_load(f)
                capability['_meta'] = {
                    'source_file': str(capability_file),
                    'format': 'yaml',
                    'feature_directory': str(capability_file.parent)
                }
                return capability
        except ImportError:
            raise ImportError("需要安装PyYAML来支持YAML格式的功能描述文件")

    def _load_json_capability(self, capability_file: Path) -> Dict[str, Any]:
        """加载JSON格式的功能描述"""
        import json
        with open(capability_file, 'r', encoding='utf-8') as f:
            capability = json.load(f)
            capability['_meta'] = {
                'source_file': str(capability_file),
                'format': 'json',
                'feature_directory': str(capability_file.parent)
            }
            return capability

    def _generate_basic_capability(self, feature_dir: Path) -> Dict[str, Any]:
        """
        为缺少描述文件的功能目录生成基本信息

        Args:
            feature_dir: 功能目录路径

        Returns:
            Dict: 基本功能信息
        """
        return {
            'name': feature_dir.name,
            'description': f'自动生成的功能描述: {feature_dir.name}',
            'category': 'unknown',
            'priority': 'low',
            'is_core': False,
            'auto_generated': True,
            'agents_can_use': ['orchestrator'],
            'functions': {},
            'integration_points': [],
            '_meta': {
                'source_file': None,
                'format': 'auto_generated',
                'feature_directory': str(feature_dir)
            }
        }

    def get_capability_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        根据名称获取功能信息

        Args:
            name: 功能名称

        Returns:
            Optional[Dict]: 功能信息
        """
        if not self.capabilities_cache:
            self.scan_all_features()

        return self.capabilities_cache.get(name)

    def is_capability_available(self, name: str) -> bool:
        """
        检查功能是否可用

        Args:
            name: 功能名称

        Returns:
            bool: 功能是否可用
        """
        capability = self.get_capability_by_name(name)
        return capability is not None

    def get_capabilities_by_category(self, category: str) -> Dict[str, Any]:
        """
        根据分类获取功能列表

        Args:
            category: 功能分类

        Returns:
            Dict: 该分类的所有功能
        """
        if not self.capabilities_cache:
            self.scan_all_features()

        return {
            name: capability
            for name, capability in self.capabilities_cache.items()
            if capability.get('category') == category
        }

    def get_core_capabilities(self) -> Dict[str, Any]:
        """
        获取所有核心功能

        Returns:
            Dict: 所有核心功能
        """
        if not self.capabilities_cache:
            self.scan_all_features()

        return {
            name: capability
            for name, capability in self.capabilities_cache.items()
            if capability.get('is_core', False)
        }

    def validate_capability(self, capability: Dict[str, Any]) -> List[str]:
        """
        验证功能描述的完整性

        Args:
            capability: 功能描述字典

        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        required_fields = ['name', 'description', 'agents_can_use']

        for field in required_fields:
            if field not in capability:
                errors.append(f"缺少必需字段: {field}")

        # 验证agents_can_use是否为列表
        if 'agents_can_use' in capability and not isinstance(capability['agents_can_use'], list):
            errors.append("agents_can_use必须是列表类型")

        # 验证functions是否为字典
        if 'functions' in capability and not isinstance(capability['functions'], dict):
            errors.append("functions必须是字典类型")

        return errors

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取扫描统计信息

        Returns:
            Dict: 统计信息
        """
        if not self.capabilities_cache:
            self.scan_all_features()

        stats = {
            'total_capabilities': len(self.capabilities_cache),
            'by_category': {},
            'by_priority': {},
            'core_capabilities': 0,
            'auto_generated': 0
        }

        for capability in self.capabilities_cache.values():
            # 按分类统计
            category = capability.get('category', 'unknown')
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1

            # 按优先级统计
            priority = capability.get('priority', 'low')
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1

            # 核心功能统计
            if capability.get('is_core', False):
                stats['core_capabilities'] += 1

            # 自动生成统计
            if capability.get('auto_generated', False):
                stats['auto_generated'] += 1

        return stats