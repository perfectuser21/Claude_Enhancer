#!/usr/bin/env python3
"""
Perfect21 Plugin System
标准化插件系统架构
"""

import logging
import importlib
import inspect
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("Perfect21.PluginSystem")

class PluginLifecycle(Enum):
    """插件生命周期"""
    INIT = "init"
    ACTIVATE = "activate"
    EXECUTE = "execute"
    DEACTIVATE = "deactivate"
    CLEANUP = "cleanup"

@dataclass
class PluginManifest:
    """插件清单"""
    name: str
    version: str
    description: str
    author: str
    category: str
    priority: int
    dependencies: List[str]
    agents_supported: List[str]
    entry_point: str
    config_schema: Dict[str, Any]

class PluginInterface(ABC):
    """标准插件接口"""

    def __init__(self, manifest: PluginManifest):
        self.manifest = manifest
        self.is_active = False
        self.logger = logging.getLogger(f"Plugin.{manifest.name}")

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化插件"""
        pass

    @abstractmethod
    def activate(self) -> bool:
        """激活插件"""
        pass

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行插件主要功能"""
        pass

    @abstractmethod
    def deactivate(self) -> bool:
        """停用插件"""
        pass

    @abstractmethod
    def cleanup(self) -> bool:
        """清理插件资源"""
        pass

    def get_health_status(self) -> Dict[str, Any]:
        """获取插件健康状态"""
        return {
            'name': self.manifest.name,
            'version': self.manifest.version,
            'is_active': self.is_active,
            'status': 'healthy' if self.is_active else 'inactive'
        }

class PluginManager:
    """插件管理器"""

    def __init__(self, plugins_directory: str = None):
        self.plugins_directory = plugins_directory or "features"
        self.plugins: Dict[str, PluginInterface] = {}
        self.manifests: Dict[str, PluginManifest] = {}
        self.plugin_graph: Dict[str, List[str]] = {}

    def discover_plugins(self) -> List[PluginManifest]:
        """发现插件"""
        manifests = []
        plugins_path = Path(self.plugins_directory)

        for plugin_dir in plugins_path.iterdir():
            if plugin_dir.is_dir() and (plugin_dir / "capability.py").exists():
                try:
                    manifest = self._load_plugin_manifest(plugin_dir)
                    if manifest:
                        manifests.append(manifest)
                        self.manifests[manifest.name] = manifest
                except Exception as e:
                    logger.error(f"加载插件清单失败 {plugin_dir}: {e}")

        logger.info(f"发现 {len(manifests)} 个插件")
        return manifests

    def _load_plugin_manifest(self, plugin_dir: Path) -> Optional[PluginManifest]:
        """加载插件清单"""
        try:
            # 动态导入capability模块
            module_path = f"{self.plugins_directory}.{plugin_dir.name}.capability"
            module = importlib.import_module(module_path)

            if hasattr(module, 'CAPABILITY'):
                cap = module.CAPABILITY
                return PluginManifest(
                    name=cap.get('name'),
                    version=cap.get('version'),
                    description=cap.get('description'),
                    author=cap.get('author', 'Perfect21 Team'),
                    category=cap.get('category'),
                    priority=cap.get('priority_score', 50),
                    dependencies=cap.get('dependencies', []),
                    agents_supported=cap.get('agents_can_use', []),
                    entry_point=f"{module_path}",
                    config_schema=cap.get('configuration', {})
                )
        except Exception as e:
            logger.error(f"解析插件清单失败 {plugin_dir}: {e}")

        return None

    def load_plugin(self, plugin_name: str) -> bool:
        """加载插件"""
        if plugin_name not in self.manifests:
            logger.error(f"插件不存在: {plugin_name}")
            return False

        manifest = self.manifests[plugin_name]

        try:
            # 动态导入插件模块
            module = importlib.import_module(manifest.entry_point.replace('.capability', ''))

            # 查找插件类
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, PluginInterface) and
                    obj != PluginInterface):
                    plugin_class = obj
                    break

            if not plugin_class:
                # 创建默认插件包装器
                plugin_class = self._create_default_plugin_wrapper(module, manifest)

            # 实例化插件
            plugin_instance = plugin_class(manifest)
            self.plugins[plugin_name] = plugin_instance

            logger.info(f"插件加载成功: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"插件加载失败 {plugin_name}: {e}")
            return False

    def _create_default_plugin_wrapper(self, module, manifest) -> Type[PluginInterface]:
        """为没有实现PluginInterface的模块创建默认包装器"""

        class DefaultPluginWrapper(PluginInterface):
            def __init__(self, manifest: PluginManifest):
                super().__init__(manifest)
                self.module = module

            def initialize(self, config: Dict[str, Any]) -> bool:
                if hasattr(self.module, 'initialize'):
                    return self.module.initialize()
                return True

            def activate(self) -> bool:
                self.is_active = True
                return True

            def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
                # 默认执行逻辑
                return {'status': 'executed', 'plugin': self.manifest.name}

            def deactivate(self) -> bool:
                self.is_active = False
                return True

            def cleanup(self) -> bool:
                return True

        return DefaultPluginWrapper

    def activate_plugin(self, plugin_name: str, config: Dict[str, Any] = None) -> bool:
        """激活插件"""
        if plugin_name not in self.plugins:
            if not self.load_plugin(plugin_name):
                return False

        plugin = self.plugins[plugin_name]
        config = config or {}

        try:
            if plugin.initialize(config) and plugin.activate():
                logger.info(f"插件激活成功: {plugin_name}")
                return True
            else:
                logger.error(f"插件激活失败: {plugin_name}")
                return False
        except Exception as e:
            logger.error(f"插件激活异常 {plugin_name}: {e}")
            return False

    def execute_plugin(self, plugin_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行插件"""
        if plugin_name not in self.plugins or not self.plugins[plugin_name].is_active:
            return {'error': f'插件未激活: {plugin_name}'}

        try:
            return self.plugins[plugin_name].execute(context)
        except Exception as e:
            logger.error(f"插件执行异常 {plugin_name}: {e}")
            return {'error': str(e)}

    def get_system_health(self) -> Dict[str, Any]:
        """获取插件系统健康状态"""
        health = {
            'total_plugins': len(self.manifests),
            'active_plugins': len([p for p in self.plugins.values() if p.is_active]),
            'plugin_status': {}
        }

        for name, plugin in self.plugins.items():
            health['plugin_status'][name] = plugin.get_health_status()

        return health

    def build_dependency_graph(self) -> Dict[str, List[str]]:
        """构建插件依赖图"""
        graph = {}
        for name, manifest in self.manifests.items():
            graph[name] = manifest.dependencies

        self.plugin_graph = graph
        return graph

    def get_load_order(self) -> List[str]:
        """获取插件加载顺序（基于依赖和优先级）"""
        # 拓扑排序 + 优先级排序
        visited = set()
        temp_visit = set()
        order = []

        def visit(plugin_name: str):
            if plugin_name in temp_visit:
                raise ValueError(f"检测到循环依赖: {plugin_name}")
            if plugin_name in visited:
                return

            temp_visit.add(plugin_name)

            # 先访问依赖
            manifest = self.manifests.get(plugin_name)
            if manifest:
                for dep in manifest.dependencies:
                    if dep in self.manifests:
                        visit(dep)

            temp_visit.remove(plugin_name)
            visited.add(plugin_name)
            order.append(plugin_name)

        # 按优先级排序后处理
        sorted_plugins = sorted(
            self.manifests.keys(),
            key=lambda x: self.manifests[x].priority,
            reverse=True
        )

        for plugin in sorted_plugins:
            if plugin not in visited:
                visit(plugin)

        return order

# 全局插件管理器
plugin_manager = PluginManager()

def bootstrap_plugin_system() -> Dict[str, Any]:
    """启动插件系统"""
    try:
        # 发现插件
        manifests = plugin_manager.discover_plugins()

        # 构建依赖图
        plugin_manager.build_dependency_graph()

        # 获取加载顺序
        load_order = plugin_manager.get_load_order()

        # 激活插件
        activated = 0
        for plugin_name in load_order:
            if plugin_manager.activate_plugin(plugin_name):
                activated += 1

        return {
            'success': True,
            'discovered': len(manifests),
            'activated': activated,
            'load_order': load_order,
            'health': plugin_manager.get_system_health()
        }

    except Exception as e:
        logger.error(f"插件系统启动失败: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    # 测试插件系统
    result = bootstrap_plugin_system()
    print("插件系统启动结果:", result)