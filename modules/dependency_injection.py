#!/usr/bin/env python3
"""
Perfect21 Dependency Injection System
依赖注入和控制反转容器
"""

import logging
from typing import Dict, Any, Optional, Type, Callable
from abc import ABC, abstractmethod

logger = logging.getLogger("Perfect21.DependencyInjection")

class ServiceInterface(ABC):
    """服务接口基类"""

    @abstractmethod
    def get_service_name(self) -> str:
        """获取服务名称"""
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """初始化服务"""
        pass

    @abstractmethod
    def cleanup(self) -> bool:
        """清理服务"""
        pass

class DIContainer:
    """依赖注入容器"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._dependencies: Dict[str, list] = {}

    def register_service(self, service_name: str, service_class: Type,
                        dependencies: list = None, singleton: bool = True):
        """注册服务"""
        self._factories[service_name] = service_class
        self._dependencies[service_name] = dependencies or []

        if singleton:
            logger.info(f"注册单例服务: {service_name}")
        else:
            logger.info(f"注册瞬态服务: {service_name}")

    def register_instance(self, service_name: str, instance: Any):
        """注册服务实例"""
        self._singletons[service_name] = instance
        logger.info(f"注册服务实例: {service_name}")

    def resolve(self, service_name: str) -> Any:
        """解析服务"""
        # 检查单例缓存
        if service_name in self._singletons:
            return self._singletons[service_name]

        # 检查工厂
        if service_name not in self._factories:
            raise ValueError(f"服务未注册: {service_name}")

        # 解析依赖
        dependencies = self._dependencies.get(service_name, [])
        resolved_deps = {}

        for dep in dependencies:
            resolved_deps[dep] = self.resolve(dep)

        # 创建实例
        service_class = self._factories[service_name]
        instance = service_class(**resolved_deps)

        # 缓存单例
        self._singletons[service_name] = instance

        logger.info(f"解析服务: {service_name}")
        return instance

    def get_dependency_graph(self) -> Dict[str, list]:
        """获取依赖图"""
        return self._dependencies.copy()

    def validate_dependencies(self) -> Dict[str, Any]:
        """验证依赖关系"""
        issues = {
            'circular_dependencies': [],
            'missing_dependencies': [],
            'unresolvable_services': []
        }

        # 检查循环依赖
        visited = set()
        rec_stack = set()

        def has_cycle(service: str) -> bool:
            visited.add(service)
            rec_stack.add(service)

            for dep in self._dependencies.get(service, []):
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    issues['circular_dependencies'].append(f"{service} -> {dep}")
                    return True

            rec_stack.remove(service)
            return False

        for service in self._factories:
            if service not in visited:
                has_cycle(service)

        # 检查缺失依赖
        for service, deps in self._dependencies.items():
            for dep in deps:
                if dep not in self._factories and dep not in self._singletons:
                    issues['missing_dependencies'].append(f"{service} 依赖缺失: {dep}")

        return issues

# 全局容器实例
container = DIContainer()

def setup_perfect21_services():
    """设置Perfect21服务依赖"""

    # 注册核心服务（无依赖）
    container.register_service('config_manager', None)  # 实际类需要导入
    container.register_service('logger', None)

    # 注册功能服务（有依赖）
    container.register_service('version_manager', None,
                             dependencies=['config_manager', 'logger'])

    container.register_service('capability_discovery', None,
                             dependencies=['config_manager', 'logger'])

    container.register_service('git_workflow', None,
                             dependencies=['config_manager', 'logger', 'capability_discovery'])

    container.register_service('claude_md_manager', None,
                             dependencies=['config_manager', 'logger', 'version_manager'])

    logger.info("Perfect21服务依赖配置完成")

if __name__ == "__main__":
    # 测试依赖验证
    setup_perfect21_services()
    issues = container.validate_dependencies()
    print("依赖验证结果:", issues)