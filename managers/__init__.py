#!/usr/bin/env python3
"""
Perfect21 统一Manager系统
提供Manager类的注册表、工厂和生命周期管理

设计目标:
- 统一Manager创建和销毁
- 提供Manager依赖注入
- 支持Manager的懒加载
- 简化Manager间的通信
"""

import os
import sys
import logging
from typing import Dict, Type, Any, Optional, Set
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

# 配置日志
logger = logging.getLogger("Perfect21.Managers")

# ================== 基础接口和类型定义 ==================

class ManagerType(Enum):
    """Manager类型"""
    DOCUMENT = "document"
    AUTHENTICATION = "authentication"
    WORKFLOW = "workflow"
    GIT_INTEGRATION = "git_integration"
    CONFIGURATION = "configuration"
    DATA = "data"
    WORKSPACE = "workspace"
    VERSION = "version"
    INFRASTRUCTURE = "infrastructure"
    MONITORING = "monitoring"

class ManagerStatus(Enum):
    """Manager状态"""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    CLEANING_UP = "cleaning_up"
    DESTROYED = "destroyed"

@dataclass
class ManagerInfo:
    """Manager信息"""
    name: str
    manager_type: ManagerType
    description: str
    dependencies: Set[str]
    status: ManagerStatus
    instance: Optional[Any] = None
    error_message: Optional[str] = None

class BaseManager(ABC):
    """Manager基类"""

    def __init__(self, name: str):
        self.name = name
        self.status = ManagerStatus.NOT_INITIALIZED
        self._dependencies: Set[str] = set()

    @abstractmethod
    def initialize(self, **kwargs) -> bool:
        """初始化Manager"""
        pass

    @abstractmethod
    def cleanup(self):
        """清理Manager资源"""
        pass

    def get_dependencies(self) -> Set[str]:
        """获取依赖的Manager"""
        return self._dependencies.copy()

    def add_dependency(self, manager_name: str):
        """添加依赖"""
        self._dependencies.add(manager_name)

    def remove_dependency(self, manager_name: str):
        """移除依赖"""
        self._dependencies.discard(manager_name)

# ================== Manager注册表 ==================

class ManagerRegistry:
    """Manager注册表"""

    def __init__(self):
        self._managers: Dict[str, ManagerInfo] = {}
        self._manager_classes: Dict[str, Type] = {}
        self._initialization_order: list = []

    def register(self, name: str, manager_class: Type, manager_type: ManagerType,
                description: str = "", dependencies: Set[str] = None):
        """注册Manager类"""
        if dependencies is None:
            dependencies = set()

        self._manager_classes[name] = manager_class
        self._managers[name] = ManagerInfo(
            name=name,
            manager_type=manager_type,
            description=description,
            dependencies=dependencies,
            status=ManagerStatus.NOT_INITIALIZED
        )

        logger.info(f"注册Manager: {name} ({manager_type.value})")

    def unregister(self, name: str):
        """注销Manager"""
        if name in self._managers:
            manager_info = self._managers[name]
            if manager_info.instance and manager_info.status == ManagerStatus.READY:
                try:
                    manager_info.instance.cleanup()
                except Exception as e:
                    logger.error(f"清理Manager {name} 失败: {e}")

            del self._managers[name]
            if name in self._manager_classes:
                del self._manager_classes[name]

            logger.info(f"注销Manager: {name}")

    def get_manager_info(self, name: str) -> Optional[ManagerInfo]:
        """获取Manager信息"""
        return self._managers.get(name)

    def list_managers(self, manager_type: ManagerType = None,
                     status: ManagerStatus = None) -> Dict[str, ManagerInfo]:
        """列出Manager"""
        filtered_managers = {}

        for name, info in self._managers.items():
            if manager_type and info.manager_type != manager_type:
                continue
            if status and info.status != status:
                continue
            filtered_managers[name] = info

        return filtered_managers

    def get_dependency_order(self) -> list:
        """获取按依赖关系排序的Manager列表"""
        if self._initialization_order:
            return self._initialization_order.copy()

        # 拓扑排序解决依赖关系
        visited = set()
        temp_visited = set()
        order = []

        def visit(name: str):
            if name in temp_visited:
                raise ValueError(f"检测到循环依赖: {name}")
            if name in visited:
                return

            temp_visited.add(name)

            manager_info = self._managers.get(name)
            if manager_info:
                for dependency in manager_info.dependencies:
                    if dependency in self._managers:
                        visit(dependency)

            temp_visited.remove(name)
            visited.add(name)
            order.append(name)

        for name in self._managers:
            if name not in visited:
                visit(name)

        self._initialization_order = order
        return order.copy()

# ================== Manager工厂 ==================

class ManagerFactory:
    """Manager工厂"""

    def __init__(self, registry: ManagerRegistry):
        self.registry = registry
        self._instances: Dict[str, Any] = {}

    def create_manager(self, name: str, **kwargs) -> Optional[Any]:
        """创建Manager实例"""
        manager_info = self.registry.get_manager_info(name)
        if not manager_info:
            logger.error(f"未找到Manager: {name}")
            return None

        if manager_info.instance:
            logger.warning(f"Manager {name} 已经存在实例")
            return manager_info.instance

        try:
            manager_info.status = ManagerStatus.INITIALIZING

            # 获取Manager类
            manager_class = self.registry._manager_classes[name]

            # 创建实例
            instance = manager_class(**kwargs)

            # 初始化
            if hasattr(instance, 'initialize'):
                if not instance.initialize(**kwargs):
                    manager_info.status = ManagerStatus.ERROR
                    manager_info.error_message = "初始化失败"
                    return None

            manager_info.instance = instance
            manager_info.status = ManagerStatus.READY
            self._instances[name] = instance

            logger.info(f"创建Manager成功: {name}")
            return instance

        except Exception as e:
            manager_info.status = ManagerStatus.ERROR
            manager_info.error_message = str(e)
            logger.error(f"创建Manager失败: {name} - {e}")
            return None

    def get_manager(self, name: str) -> Optional[Any]:
        """获取Manager实例（懒加载）"""
        if name in self._instances:
            return self._instances[name]

        return self.create_manager(name)

    def destroy_manager(self, name: str):
        """销毁Manager实例"""
        manager_info = self.registry.get_manager_info(name)
        if not manager_info or not manager_info.instance:
            return

        try:
            manager_info.status = ManagerStatus.CLEANING_UP

            # 调用清理方法
            if hasattr(manager_info.instance, 'cleanup'):
                manager_info.instance.cleanup()

            # 移除实例
            if name in self._instances:
                del self._instances[name]

            manager_info.instance = None
            manager_info.status = ManagerStatus.DESTROYED

            logger.info(f"销毁Manager成功: {name}")

        except Exception as e:
            manager_info.status = ManagerStatus.ERROR
            manager_info.error_message = f"清理失败: {str(e)}"
            logger.error(f"销毁Manager失败: {name} - {e}")

    def initialize_all(self, **kwargs):
        """按依赖顺序初始化所有Manager"""
        order = self.registry.get_dependency_order()

        for name in order:
            manager = self.get_manager(name)
            if not manager:
                logger.error(f"初始化Manager失败: {name}")

    def cleanup_all(self):
        """清理所有Manager"""
        # 按反向依赖顺序清理
        order = self.registry.get_dependency_order()
        order.reverse()

        for name in order:
            self.destroy_manager(name)

# ================== Perfect21Manager系统 ==================

class Perfect21ManagerSystem:
    """Perfect21 Manager系统"""

    def __init__(self):
        self.registry = ManagerRegistry()
        self.factory = ManagerFactory(self.registry)
        self._setup_default_managers()

    def _setup_default_managers(self):
        """设置默认的Manager"""
        try:
            # 导入Manager类
            from .document_manager import DocumentManager
            from .authentication_manager import AuthenticationManager

            # 注册核心Manager
            self.registry.register(
                "document",
                DocumentManager,
                ManagerType.DOCUMENT,
                "文档内容管理器，整合内容分析、生命周期跟踪、模板引擎和ADR记录"
            )

            self.registry.register(
                "authentication",
                AuthenticationManager,
                ManagerType.AUTHENTICATION,
                "认证授权管理器，整合用户认证、令牌管理和权限控制"
            )

            # 注册工作流相关Manager（待实现）
            # self.registry.register(
            #     "workflow",
            #     WorkflowOrchestrator,
            #     ManagerType.WORKFLOW,
            #     "工作流编排器，整合任务管理、并行执行和同步点管理",
            #     {"authentication"}  # 依赖认证Manager
            # )

            # 注册Git集成Manager（待实现）
            # self.registry.register(
            #     "git_integration",
            #     GitIntegrationManager,
            #     ManagerType.GIT_INTEGRATION,
            #     "Git集成管理器，整合hooks管理、分支控制和Git缓存"
            # )

            # 注册配置Manager（待实现）
            # self.registry.register(
            #     "configuration",
            #     ConfigurationManager,
            #     ManagerType.CONFIGURATION,
            #     "配置状态管理器，整合配置管理和状态跟踪"
            # )

            logger.info("默认Manager注册完成")

        except ImportError as e:
            logger.error(f"导入Manager类失败: {e}")

    # =================== 便捷访问接口 ===================

    @property
    def document(self):
        """获取文档管理器"""
        return self.factory.get_manager("document")

    @property
    def auth(self):
        """获取认证管理器"""
        return self.factory.get_manager("authentication")

    @property
    def workflow(self):
        """获取工作流管理器"""
        return self.factory.get_manager("workflow")

    @property
    def git(self):
        """获取Git集成管理器"""
        return self.factory.get_manager("git_integration")

    @property
    def config(self):
        """获取配置管理器"""
        return self.factory.get_manager("configuration")

    @property
    def workspace(self):
        """获取工作空间管理器"""
        return self.factory.get_manager("workspace")

    @property
    def version(self):
        """获取版本管理器"""
        return self.factory.get_manager("version")

    # =================== 系统管理接口 ===================

    def initialize_system(self, **kwargs):
        """初始化Manager系统"""
        try:
            logger.info("初始化Perfect21 Manager系统...")
            self.factory.initialize_all(**kwargs)
            logger.info("Perfect21 Manager系统初始化完成")
        except Exception as e:
            logger.error(f"Manager系统初始化失败: {e}")
            raise

    def shutdown_system(self):
        """关闭Manager系统"""
        try:
            logger.info("关闭Perfect21 Manager系统...")
            self.factory.cleanup_all()
            logger.info("Perfect21 Manager系统关闭完成")
        except Exception as e:
            logger.error(f"Manager系统关闭失败: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        managers = self.registry.list_managers()
        status_summary = {}

        for status in ManagerStatus:
            status_summary[status.value] = len([
                m for m in managers.values() if m.status == status
            ])

        return {
            'total_managers': len(managers),
            'status_summary': status_summary,
            'manager_details': {
                name: {
                    'type': info.manager_type.value,
                    'status': info.status.value,
                    'description': info.description,
                    'dependencies': list(info.dependencies),
                    'error': info.error_message
                } for name, info in managers.items()
            }
        }

    def health_check(self) -> Dict[str, Any]:
        """系统健康检查"""
        managers = self.registry.list_managers()
        healthy_count = 0
        unhealthy_managers = []

        for name, info in managers.items():
            if info.status == ManagerStatus.READY:
                # 检查Manager是否有健康检查方法
                if info.instance and hasattr(info.instance, 'health_check'):
                    try:
                        health_result = info.instance.health_check()
                        if health_result.get('status') == 'healthy':
                            healthy_count += 1
                        else:
                            unhealthy_managers.append({
                                'name': name,
                                'issue': health_result.get('message', 'Unknown issue')
                            })
                    except Exception as e:
                        unhealthy_managers.append({
                            'name': name,
                            'issue': f'健康检查失败: {str(e)}'
                        })
                else:
                    healthy_count += 1  # 没有健康检查方法的认为是健康的
            else:
                unhealthy_managers.append({
                    'name': name,
                    'issue': f'状态异常: {info.status.value}'
                })

        return {
            'overall_health': 'healthy' if len(unhealthy_managers) == 0 else 'unhealthy',
            'healthy_managers': healthy_count,
            'total_managers': len(managers),
            'unhealthy_managers': unhealthy_managers
        }

# ================== 全局Manager系统实例 ==================

# 创建全局Manager系统实例
manager_system = Perfect21ManagerSystem()

# 向后兼容的快捷访问
def get_document_manager():
    """获取文档管理器"""
    return manager_system.document

def get_auth_manager():
    """获取认证管理器"""
    return manager_system.auth

def get_workflow_manager():
    """获取工作流管理器"""
    return manager_system.workflow

def get_git_manager():
    """获取Git管理器"""
    return manager_system.git

def get_config_manager():
    """获取配置管理器"""
    return manager_system.config

# ================== 使用示例 ==================

def main():
    """使用示例"""
    try:
        # 初始化系统
        manager_system.initialize_system()

        # 使用文档管理器
        doc_manager = manager_system.document
        if doc_manager:
            health = doc_manager.analyze_document_health()
            print(f"文档健康等级: {health.health_grade.value}")

        # 使用认证管理器
        auth_manager = manager_system.auth
        if auth_manager:
            stats = auth_manager.get_authentication_stats()
            print(f"认证统计: {stats}")

        # 系统状态检查
        status = manager_system.get_system_status()
        print(f"系统状态: {status['status_summary']}")

        # 健康检查
        health = manager_system.health_check()
        print(f"系统健康: {health['overall_health']}")

    except Exception as e:
        logger.error(f"示例运行失败: {e}")

    finally:
        # 关闭系统
        manager_system.shutdown_system()

if __name__ == "__main__":
    main()