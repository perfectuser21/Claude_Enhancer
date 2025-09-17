#!/usr/bin/env python3
"""
Perfect21 依赖注入容器
实现控制反转(IoC)，解决模块间高耦合问题
"""

import inspect
from typing import Dict, Type, Any, Optional, List, Callable, TypeVar, get_type_hints
from threading import Lock
from .interfaces import (
    IServiceRegistry, ILogger, Perfect21Exception,
    ServiceNotFoundException
)

T = TypeVar('T')


class DIContainer(IServiceRegistry):
    """依赖注入容器 - 单例模式"""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DIContainer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._services: Dict[str, Any] = {}
            self._factories: Dict[str, Callable] = {}
            self._singletons: Dict[str, Any] = {}
            self._interfaces: Dict[str, Type] = {}
            self._dependencies: Dict[str, List[str]] = {}
            self._lock = Lock()
            self._initialized = True

    def register_service(self, name: str, service: Any, interface: Type = None) -> None:
        """注册服务实例"""
        with self._lock:
            if interface:
                self._validate_interface_implementation(service, interface)
                self._interfaces[name] = interface

            self._services[name] = service
            self._analyze_dependencies(name, service)

    def register_factory(self, name: str, factory: Callable, interface: Type = None, singleton: bool = False) -> None:
        """注册服务工厂"""
        with self._lock:
            if interface:
                self._interfaces[name] = interface

            self._factories[name] = factory

            if singleton:
                self._singletons[name] = None

            self._analyze_factory_dependencies(name, factory)

    def register_singleton(self, name: str, service_class: Type, interface: Type = None) -> None:
        """注册单例服务"""
        def factory():
            return service_class()

        self.register_factory(name, factory, interface, singleton=True)

    def get_service(self, name: str, interface: Type = None) -> Any:
        """获取服务"""
        with self._lock:
            # 检查是否是单例且已创建
            if name in self._singletons:
                if self._singletons[name] is not None:
                    return self._singletons[name]

            # 检查是否有工厂
            if name in self._factories:
                service = self._create_from_factory(name)

                # 如果是单例，保存实例
                if name in self._singletons:
                    self._singletons[name] = service

                return service

            # 检查是否有直接注册的服务
            if name in self._services:
                service = self._services[name]

                if interface:
                    self._validate_interface_implementation(service, interface)

                return service

            raise ServiceNotFoundException(f"Service '{name}' not found")

    def unregister_service(self, name: str) -> None:
        """注销服务"""
        with self._lock:
            self._services.pop(name, None)
            self._factories.pop(name, None)
            self._singletons.pop(name, None)
            self._interfaces.pop(name, None)
            self._dependencies.pop(name, None)

    def list_services(self) -> List[str]:
        """列出所有服务"""
        with self._lock:
            services = set(self._services.keys())
            services.update(self._factories.keys())
            return sorted(list(services))

    def inject_dependencies(self, target: Any) -> None:
        """为目标对象注入依赖"""
        target_class = target.__class__

        # 检查构造函数参数
        init_signature = inspect.signature(target_class.__init__)
        type_hints = get_type_hints(target_class.__init__)

        for param_name, param in init_signature.parameters.items():
            if param_name == 'self':
                continue

            # 查找对应的服务
            service_name = param_name
            param_type = type_hints.get(param_name)

            try:
                service = self.get_service(service_name, param_type)
                setattr(target, param_name, service)
            except ServiceNotFoundException:
                # 如果没有默认值且找不到服务，抛出异常
                if param.default == inspect.Parameter.empty:
                    raise ServiceNotFoundException(
                        f"Required dependency '{param_name}' not found for {target_class.__name__}"
                    )

    def resolve_dependencies(self, service_name: str) -> List[str]:
        """解析服务依赖关系"""
        dependencies = []

        def _resolve_recursive(name: str, visited: set):
            if name in visited:
                raise Perfect21Exception(f"Circular dependency detected: {name}")

            visited.add(name)

            if name in self._dependencies:
                for dep in self._dependencies[name]:
                    _resolve_recursive(dep, visited.copy())
                    dependencies.append(dep)

            dependencies.append(name)

        _resolve_recursive(service_name, set())
        return dependencies

    def _create_from_factory(self, name: str) -> Any:
        """从工厂创建服务"""
        factory = self._factories[name]

        # 分析工厂依赖
        signature = inspect.signature(factory)
        type_hints = get_type_hints(factory)

        kwargs = {}
        for param_name, param in signature.parameters.items():
            param_type = type_hints.get(param_name)

            try:
                service = self.get_service(param_name, param_type)
                kwargs[param_name] = service
            except ServiceNotFoundException:
                if param.default == inspect.Parameter.empty:
                    raise ServiceNotFoundException(
                        f"Required dependency '{param_name}' not found for factory '{name}'"
                    )

        return factory(**kwargs)

    def _validate_interface_implementation(self, service: Any, interface: Type) -> None:
        """验证服务是否实现了接口"""
        if not isinstance(service, interface):
            raise Perfect21Exception(
                f"Service {service.__class__.__name__} does not implement interface {interface.__name__}"
            )

    def _analyze_dependencies(self, name: str, service: Any) -> None:
        """分析服务依赖"""
        service_class = service.__class__
        init_signature = inspect.signature(service_class.__init__)

        dependencies = []
        for param_name, param in init_signature.parameters.items():
            if param_name == 'self':
                continue
            dependencies.append(param_name)

        self._dependencies[name] = dependencies

    def _analyze_factory_dependencies(self, name: str, factory: Callable) -> None:
        """分析工厂依赖"""
        signature = inspect.signature(factory)

        dependencies = []
        for param_name, param in signature.parameters.items():
            dependencies.append(param_name)

        self._dependencies[name] = dependencies

    def clear_all(self) -> None:
        """清空所有注册的服务"""
        with self._lock:
            self._services.clear()
            self._factories.clear()
            self._singletons.clear()
            self._interfaces.clear()
            self._dependencies.clear()


class Injectable:
    """可注入装饰器"""

    def __init__(self, name: str = None, interface: Type = None, singleton: bool = False):
        self.name = name
        self.interface = interface
        self.singleton = singleton

    def __call__(self, cls):
        service_name = self.name or cls.__name__.lower().replace('_', '')

        # 注册到容器
        container = DIContainer()

        if self.singleton:
            container.register_singleton(service_name, cls, self.interface)
        else:
            container.register_factory(service_name, cls, self.interface)

        return cls


def inject(service_name: str = None, interface: Type = None):
    """依赖注入装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            container = DIContainer()

            # 分析函数参数
            signature = inspect.signature(func)
            type_hints = get_type_hints(func)

            for param_name, param in signature.parameters.items():
                if param_name not in kwargs:
                    param_type = type_hints.get(param_name, interface)
                    name = service_name or param_name

                    try:
                        service = container.get_service(name, param_type)
                        kwargs[param_name] = service
                    except ServiceNotFoundException:
                        if param.default == inspect.Parameter.empty:
                            raise

            return func(*args, **kwargs)
        return wrapper
    return decorator


class ServiceLocator:
    """服务定位器 - 提供简化的服务访问"""

    _container = DIContainer()

    @classmethod
    def get(cls, service_name: str, interface: Type = None) -> Any:
        """获取服务"""
        return cls._container.get_service(service_name, interface)

    @classmethod
    def register(cls, name: str, service: Any, interface: Type = None) -> None:
        """注册服务"""
        cls._container.register_service(name, service, interface)

    @classmethod
    def register_factory(cls, name: str, factory: Callable, interface: Type = None, singleton: bool = False) -> None:
        """注册工厂"""
        cls._container.register_factory(name, factory, interface, singleton)


# 全局容器实例
container = DIContainer()