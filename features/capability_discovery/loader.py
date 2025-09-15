#!/usr/bin/env python3
"""
Perfect21动态加载器
支持运行时热加载功能模块
"""

import os
import sys
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import importlib
import importlib.util

from .scanner import CapabilityScanner
from .registry import CapabilityRegistry

logger = logging.getLogger("CapabilityLoader")

class CapabilityLoader:
    """功能动态加载器"""

    def __init__(self, features_root: str = None, auto_reload: bool = True):
        """
        初始化加载器

        Args:
            features_root: features目录路径
            auto_reload: 是否启用自动重载
        """
        self.features_root = features_root or os.path.join(os.getcwd(), 'features')
        self.auto_reload = auto_reload

        # 初始化组件
        self.scanner = CapabilityScanner(self.features_root)
        self.registry = CapabilityRegistry()

        # 加载状态
        self.loaded_capabilities = {}
        self.load_callbacks = []
        self.unload_callbacks = []

        # 监控线程
        self._monitor_thread = None
        self._monitor_running = False
        self._last_scan_time = 0

        logger.info(f"功能加载器初始化 - 自动重载: {auto_reload}")

    def bootstrap(self) -> Dict[str, bool]:
        """
        启动加载器，执行初始扫描和注册

        Returns:
            Dict[str, bool]: 加载结果
        """
        logger.info("启动Perfect21功能发现和加载系统...")

        try:
            # 1. 扫描所有功能
            capabilities = self.scanner.scan_all_features()
            logger.info(f"发现 {len(capabilities)} 个功能模块")

            # 2. 验证功能
            validated_capabilities = self._validate_capabilities(capabilities)
            logger.info(f"验证通过 {len(validated_capabilities)} 个功能模块")

            # 3. 加载功能
            load_results = self._load_capabilities(validated_capabilities)

            # 4. 注册到claude-code-unified-agents
            registration_results = self.registry.register_capabilities(validated_capabilities)

            # 5. 启动监控
            if self.auto_reload:
                self._start_monitoring()

            # 6. 合并结果
            final_results = {}
            for name in capabilities.keys():
                loaded = load_results.get(name, False)
                registered = registration_results.get(name, False)
                final_results[name] = loaded and registered

            success_count = sum(final_results.values())
            logger.info(f"Perfect21功能发现系统启动完成: {success_count}/{len(capabilities)} 功能可用")

            return final_results

        except Exception as e:
            logger.error(f"启动功能发现系统失败: {e}")
            return {}

    def _validate_capabilities(self, capabilities: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证功能模块

        Args:
            capabilities: 原始功能字典

        Returns:
            Dict[str, Any]: 验证通过的功能字典
        """
        validated = {}

        for name, capability in capabilities.items():
            errors = self.scanner.validate_capability(capability)

            if errors:
                logger.warning(f"功能 {name} 验证失败: {errors}")
                continue

            # 检查功能目录是否存在
            feature_dir = capability.get('_meta', {}).get('feature_directory')
            if feature_dir and not os.path.exists(feature_dir):
                logger.warning(f"功能目录不存在: {feature_dir}")
                continue

            validated[name] = capability
            logger.debug(f"功能验证通过: {name}")

        return validated

    def _load_capabilities(self, capabilities: Dict[str, Any]) -> Dict[str, bool]:
        """
        加载功能模块

        Args:
            capabilities: 功能字典

        Returns:
            Dict[str, bool]: 加载结果
        """
        results = {}

        # 按优先级排序
        sorted_capabilities = self._sort_by_load_order(capabilities)

        for name, capability in sorted_capabilities:
            try:
                success = self._load_single_capability(name, capability)
                results[name] = success

                if success:
                    self.loaded_capabilities[name] = capability
                    self._notify_load_callbacks(name, capability)
                    logger.info(f"功能加载成功: {name}")
                else:
                    logger.warning(f"功能加载失败: {name}")

            except Exception as e:
                logger.error(f"加载功能 {name} 时发生异常: {e}")
                results[name] = False

        return results

    def _sort_by_load_order(self, capabilities: Dict[str, Any]) -> List[tuple]:
        """
        按加载顺序排序功能

        Args:
            capabilities: 功能字典

        Returns:
            List[tuple]: 排序后的(name, capability)元组列表
        """
        def get_load_order(item):
            name, capability = item
            # capability_discovery优先级最高
            if name == 'capability_discovery':
                return (0, 0)

            is_core = capability.get('is_core', False)
            priority_order = {'critical': 1, 'high': 2, 'medium': 3, 'low': 4}
            priority = capability.get('priority', 'low')

            return (1 if is_core else 2, priority_order.get(priority, 4))

        return sorted(capabilities.items(), key=get_load_order)

    def _load_single_capability(self, name: str, capability: Dict[str, Any]) -> bool:
        """
        加载单个功能模块

        Args:
            name: 功能名称
            capability: 功能信息

        Returns:
            bool: 加载是否成功
        """
        try:
            feature_dir = capability.get('_meta', {}).get('feature_directory')
            if not feature_dir:
                logger.warning(f"功能 {name} 缺少feature_directory信息")
                return False

            # 查找主模块文件
            main_module_file = self._find_main_module(feature_dir, name)
            if not main_module_file:
                logger.debug(f"功能 {name} 没有主模块文件，跳过加载")
                return True  # 没有主模块也算成功

            # 动态导入模块
            module = self._import_module(main_module_file, name)
            if not module:
                return False

            # 调用初始化函数（如果存在）
            if hasattr(module, 'initialize'):
                try:
                    module.initialize()
                    logger.debug(f"功能 {name} 初始化成功")
                except Exception as e:
                    logger.error(f"功能 {name} 初始化失败: {e}")
                    return False

            return True

        except Exception as e:
            logger.error(f"加载功能 {name} 失败: {e}")
            return False

    def _find_main_module(self, feature_dir: str, name: str) -> Optional[str]:
        """
        查找功能的主模块文件

        Args:
            feature_dir: 功能目录
            name: 功能名称

        Returns:
            Optional[str]: 主模块文件路径
        """
        possible_files = [
            os.path.join(feature_dir, f'{name}.py'),
            os.path.join(feature_dir, 'main.py'),
            os.path.join(feature_dir, '__init__.py'),
            os.path.join(feature_dir, f'{name}_manager.py'),
            os.path.join(feature_dir, 'manager.py')
        ]

        for file_path in possible_files:
            if os.path.exists(file_path):
                return file_path

        return None

    def _import_module(self, module_file: str, name: str) -> Optional[Any]:
        """
        动态导入模块

        Args:
            module_file: 模块文件路径
            name: 模块名称

        Returns:
            Optional[Any]: 导入的模块对象
        """
        try:
            spec = importlib.util.spec_from_file_location(f"perfect21_{name}", module_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            return module

        except Exception as e:
            logger.error(f"导入模块 {module_file} 失败: {e}")
            return None

    def _start_monitoring(self) -> None:
        """启动文件监控"""
        if self._monitor_running:
            return

        self._monitor_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_features, daemon=True)
        self._monitor_thread.start()

        logger.info("启动功能监控线程")

    def _monitor_features(self) -> None:
        """监控功能变化"""
        while self._monitor_running:
            try:
                # 检查features目录的修改时间
                if self._has_features_changed():
                    logger.info("检测到功能变化，执行热重载...")
                    self._hot_reload()

                time.sleep(5)  # 每5秒检查一次

            except Exception as e:
                logger.error(f"监控功能变化时发生异常: {e}")
                time.sleep(10)

    def _has_features_changed(self) -> bool:
        """检查功能是否有变化"""
        features_path = Path(self.features_root)
        if not features_path.exists():
            return False

        # 获取features目录及其子目录的最新修改时间
        latest_mtime = 0

        for root, dirs, files in os.walk(features_path):
            # 跳过隐藏目录和缓存目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

            for file in files:
                if file.endswith(('.py', '.yaml', '.json')) and not file.startswith('.'):
                    file_path = os.path.join(root, file)
                    mtime = os.path.getmtime(file_path)
                    latest_mtime = max(latest_mtime, mtime)

        if latest_mtime > self._last_scan_time:
            self._last_scan_time = latest_mtime
            return True

        return False

    def _hot_reload(self) -> None:
        """执行热重载"""
        try:
            # 重新扫描功能
            new_capabilities = self.scanner.scan_all_features()

            # 检查新增功能
            for name, capability in new_capabilities.items():
                if name not in self.loaded_capabilities:
                    logger.info(f"发现新功能: {name}")

                    # 验证并加载新功能
                    errors = self.scanner.validate_capability(capability)
                    if not errors:
                        if self._load_single_capability(name, capability):
                            self.loaded_capabilities[name] = capability

                            # 注册到claude-code-unified-agents
                            registration_result = self.registry.register_capabilities({name: capability})
                            if registration_result.get(name, False):
                                self._notify_load_callbacks(name, capability)
                                logger.info(f"新功能热加载成功: {name}")
                            else:
                                logger.warning(f"新功能注册失败: {name}")

            # 检查移除的功能
            for name in list(self.loaded_capabilities.keys()):
                if name not in new_capabilities:
                    logger.info(f"功能已移除: {name}")
                    self._unload_capability(name)

        except Exception as e:
            logger.error(f"热重载失败: {e}")

    def _unload_capability(self, name: str) -> bool:
        """
        卸载功能

        Args:
            name: 功能名称

        Returns:
            bool: 卸载是否成功
        """
        try:
            if name in self.loaded_capabilities:
                capability = self.loaded_capabilities[name]

                # 注销功能
                self.registry.unregister_capability(name)

                # 从加载列表移除
                del self.loaded_capabilities[name]

                # 通知回调
                self._notify_unload_callbacks(name, capability)

                logger.info(f"功能卸载成功: {name}")
                return True

        except Exception as e:
            logger.error(f"卸载功能 {name} 失败: {e}")

        return False

    def add_load_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        添加功能加载回调

        Args:
            callback: 回调函数，参数为(name, capability)
        """
        self.load_callbacks.append(callback)

    def add_unload_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        添加功能卸载回调

        Args:
            callback: 回调函数，参数为(name, capability)
        """
        self.unload_callbacks.append(callback)

    def _notify_load_callbacks(self, name: str, capability: Dict[str, Any]) -> None:
        """通知加载回调"""
        for callback in self.load_callbacks:
            try:
                callback(name, capability)
            except Exception as e:
                logger.error(f"执行加载回调失败: {e}")

    def _notify_unload_callbacks(self, name: str, capability: Dict[str, Any]) -> None:
        """通知卸载回调"""
        for callback in self.unload_callbacks:
            try:
                callback(name, capability)
            except Exception as e:
                logger.error(f"执行卸载回调失败: {e}")

    def get_loaded_capabilities(self) -> Dict[str, Any]:
        """
        获取已加载的功能列表

        Returns:
            Dict[str, Any]: 已加载的功能
        """
        return self.loaded_capabilities.copy()

    def is_capability_loaded(self, name: str) -> bool:
        """
        检查功能是否已加载

        Args:
            name: 功能名称

        Returns:
            bool: 功能是否已加载
        """
        return name in self.loaded_capabilities

    def reload_capability(self, name: str) -> bool:
        """
        重新加载指定功能

        Args:
            name: 功能名称

        Returns:
            bool: 重新加载是否成功
        """
        if name in self.loaded_capabilities:
            # 先卸载
            if not self._unload_capability(name):
                return False

        # 重新扫描单个功能
        capability = self.scanner.get_capability_by_name(name)
        if not capability:
            logger.error(f"未找到功能: {name}")
            return False

        # 重新加载
        if self._load_single_capability(name, capability):
            self.loaded_capabilities[name] = capability

            # 重新注册
            registration_result = self.registry.register_capabilities({name: capability})
            if registration_result.get(name, False):
                self._notify_load_callbacks(name, capability)
                logger.info(f"功能重新加载成功: {name}")
                return True

        return False

    def stop_monitoring(self) -> None:
        """停止监控"""
        if self._monitor_running:
            self._monitor_running = False
            if self._monitor_thread:
                self._monitor_thread.join(timeout=5)
            logger.info("停止功能监控")

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取加载统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        scanner_stats = self.scanner.get_statistics()
        registry_stats = self.registry.get_registration_statistics()

        return {
            'loaded_capabilities': len(self.loaded_capabilities),
            'auto_reload_enabled': self.auto_reload,
            'monitoring_active': self._monitor_running,
            'scanner_stats': scanner_stats,
            'registry_stats': registry_stats,
            'load_callbacks': len(self.load_callbacks),
            'unload_callbacks': len(self.unload_callbacks)
        }

    def __del__(self):
        """清理资源"""
        self.stop_monitoring()