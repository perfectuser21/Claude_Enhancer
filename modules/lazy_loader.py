#!/usr/bin/env python3
"""
Perfect21懒加载模块管理器
优化启动时间，按需加载重型模块和组件
"""

import os
import sys
import time
import threading
import weakref
import importlib
import inspect
from typing import Dict, Any, Optional, Callable, Type, Union, List
from functools import wraps, lru_cache
from contextlib import contextmanager
import gc
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.logger import log_info, log_error
from modules.config import config

logger = logging.getLogger(__name__)

class LazyModule:
    """懒加载模块包装器"""

    def __init__(self, module_name: str, factory_func: Optional[Callable] = None,
                 dependencies: List[str] = None, priority: int = 5):
        self.module_name = module_name
        self.factory_func = factory_func
        self.dependencies = dependencies or []
        self.priority = priority  # 优先级，数字越小优先级越高

        self._module = None
        self._loading = False
        self._loaded = False
        self._load_time = None
        self._access_count = 0
        self._lock = threading.RLock()
        self._error_count = 0
        self._last_error = None

    def __getattr__(self, name):
        """拦截属性访问，触发懒加载"""
        module = self._get_module()
        if module is None:
            raise ImportError(f"模块 {self.module_name} 加载失败")

        self._access_count += 1
        return getattr(module, name)

    def __call__(self, *args, **kwargs):
        """如果模块是可调用的，支持直接调用"""
        module = self._get_module()
        if module is None:
            raise ImportError(f"模块 {self.module_name} 加载失败")

        self._access_count += 1
        return module(*args, **kwargs)

    def _get_module(self):
        """获取模块实例，触发懒加载"""
        if self._loaded and self._module is not None:
            return self._module

        with self._lock:
            # 双重检查
            if self._loaded and self._module is not None:
                return self._module

            if self._loading:
                # 避免循环加载
                return None

            self._loading = True
            try:
                start_time = time.time()

                if self.factory_func:
                    self._module = self.factory_func()
                else:
                    self._module = importlib.import_module(self.module_name)

                self._load_time = time.time() - start_time
                self._loaded = True
                self._error_count = 0
                self._last_error = None

                logger.debug(f"懒加载模块成功: {self.module_name} ({self._load_time:.3f}s)")
                return self._module

            except Exception as e:
                self._error_count += 1
                self._last_error = str(e)
                logger.error(f"懒加载模块失败: {self.module_name} - {e}")
                return None
            finally:
                self._loading = False

    def is_loaded(self) -> bool:
        """检查模块是否已加载"""
        return self._loaded

    def get_stats(self) -> Dict[str, Any]:
        """获取模块统计信息"""
        return {
            'module_name': self.module_name,
            'loaded': self._loaded,
            'load_time': self._load_time,
            'access_count': self._access_count,
            'error_count': self._error_count,
            'last_error': self._last_error,
            'priority': self.priority,
            'dependencies': self.dependencies
        }

    def unload(self):
        """卸载模块"""
        with self._lock:
            if self._module and hasattr(self._module, 'cleanup'):
                try:
                    self._module.cleanup()
                except Exception as e:
                    logger.warning(f"模块清理失败: {self.module_name} - {e}")

            self._module = None
            self._loaded = False
            self._loading = False

class LazyClass:
    """懒加载类包装器"""

    def __init__(self, class_path: str, factory_func: Optional[Callable] = None,
                 singleton: bool = False):
        self.class_path = class_path
        self.factory_func = factory_func
        self.singleton = singleton

        self._class = None
        self._instance = None
        self._loaded = False
        self._lock = threading.RLock()

    def __call__(self, *args, **kwargs):
        """创建类实例"""
        cls = self._get_class()
        if cls is None:
            raise ImportError(f"类 {self.class_path} 加载失败")

        if self.singleton:
            if self._instance is None:
                with self._lock:
                    if self._instance is None:
                        self._instance = cls(*args, **kwargs)
            return self._instance
        else:
            return cls(*args, **kwargs)

    def _get_class(self):
        """获取类，触发懒加载"""
        if self._loaded and self._class is not None:
            return self._class

        with self._lock:
            if self._loaded and self._class is not None:
                return self._class

            try:
                if self.factory_func:
                    self._class = self.factory_func()
                else:
                    module_path, class_name = self.class_path.rsplit('.', 1)
                    module = importlib.import_module(module_path)
                    self._class = getattr(module, class_name)

                self._loaded = True
                logger.debug(f"懒加载类成功: {self.class_path}")
                return self._class

            except Exception as e:
                logger.error(f"懒加载类失败: {self.class_path} - {e}")
                return None

class LazyLoadManager:
    """懒加载管理器"""

    def __init__(self):
        self._modules: Dict[str, LazyModule] = {}
        self._classes: Dict[str, LazyClass] = {}
        self._preload_queue: List[str] = []
        self._lock = threading.RLock()

        # 统计信息
        self._stats = {
            'total_modules': 0,
            'loaded_modules': 0,
            'total_load_time': 0,
            'failed_loads': 0
        }

        # 预加载配置
        self._preload_enabled = config.get('lazy_load.preload_enabled', True)
        self._preload_threshold = config.get('lazy_load.preload_threshold', 3)  # 访问3次后预加载

        log_info("懒加载管理器初始化完成")

    def register_module(self, name: str, module_name: str, factory_func: Optional[Callable] = None,
                       dependencies: List[str] = None, priority: int = 5) -> LazyModule:
        """注册懒加载模块"""
        with self._lock:
            if name in self._modules:
                logger.warning(f"模块已存在，覆盖注册: {name}")

            lazy_module = LazyModule(module_name, factory_func, dependencies, priority)
            self._modules[name] = lazy_module
            self._stats['total_modules'] += 1

            logger.debug(f"注册懒加载模块: {name} -> {module_name}")
            return lazy_module

    def register_class(self, name: str, class_path: str, factory_func: Optional[Callable] = None,
                      singleton: bool = False) -> LazyClass:
        """注册懒加载类"""
        with self._lock:
            if name in self._classes:
                logger.warning(f"类已存在，覆盖注册: {name}")

            lazy_class = LazyClass(class_path, factory_func, singleton)
            self._classes[name] = lazy_class

            logger.debug(f"注册懒加载类: {name} -> {class_path}")
            return lazy_class

    def get_module(self, name: str) -> Optional[LazyModule]:
        """获取懒加载模块"""
        with self._lock:
            return self._modules.get(name)

    def get_class(self, name: str) -> Optional[LazyClass]:
        """获取懒加载类"""
        with self._lock:
            return self._classes.get(name)

    def preload_module(self, name: str) -> bool:
        """预加载模块"""
        lazy_module = self.get_module(name)
        if lazy_module is None:
            return False

        try:
            # 先加载依赖
            for dep in lazy_module.dependencies:
                if not self.preload_module(dep):
                    logger.warning(f"依赖模块加载失败: {dep}")

            # 触发加载
            lazy_module._get_module()

            if lazy_module.is_loaded():
                self._stats['loaded_modules'] += 1
                self._stats['total_load_time'] += lazy_module._load_time or 0
                return True
            else:
                self._stats['failed_loads'] += 1
                return False

        except Exception as e:
            self._stats['failed_loads'] += 1
            logger.error(f"预加载模块失败: {name} - {e}")
            return False

    def preload_by_priority(self, max_priority: int = 3) -> Dict[str, bool]:
        """按优先级预加载模块"""
        results = {}

        with self._lock:
            # 按优先级排序
            modules_to_load = [
                (name, module) for name, module in self._modules.items()
                if module.priority <= max_priority and not module.is_loaded()
            ]
            modules_to_load.sort(key=lambda x: x[1].priority)

        for name, module in modules_to_load:
            results[name] = self.preload_module(name)

        loaded_count = sum(results.values())
        log_info(f"按优先级预加载完成: {loaded_count}/{len(results)} 个模块")
        return results

    def preload_dependencies(self, module_name: str) -> bool:
        """预加载模块的所有依赖"""
        lazy_module = self.get_module(module_name)
        if lazy_module is None:
            return False

        for dep in lazy_module.dependencies:
            if not self.preload_module(dep):
                return False

        return True

    def unload_module(self, name: str) -> bool:
        """卸载模块"""
        lazy_module = self.get_module(name)
        if lazy_module is None:
            return False

        try:
            lazy_module.unload()
            if lazy_module.is_loaded():
                self._stats['loaded_modules'] -= 1

            logger.debug(f"卸载模块: {name}")
            return True

        except Exception as e:
            logger.error(f"卸载模块失败: {name} - {e}")
            return False

    def unload_all(self):
        """卸载所有模块"""
        with self._lock:
            # 按依赖关系逆序卸载
            for name in list(self._modules.keys()):
                self.unload_module(name)

            for name, lazy_class in list(self._classes.items()):
                if lazy_class.singleton and lazy_class._instance:
                    if hasattr(lazy_class._instance, 'cleanup'):
                        try:
                            lazy_class._instance.cleanup()
                        except Exception as e:
                            logger.warning(f"类实例清理失败: {name} - {e}")

        # 强制垃圾回收
        gc.collect()
        log_info("所有懒加载模块已卸载")

    def get_load_stats(self) -> Dict[str, Any]:
        """获取加载统计信息"""
        with self._lock:
            module_stats = []
            for name, module in self._modules.items():
                module_stats.append({
                    'name': name,
                    **module.get_stats()
                })

            return {
                'total_modules': self._stats['total_modules'],
                'loaded_modules': self._stats['loaded_modules'],
                'total_load_time': self._stats['total_load_time'],
                'failed_loads': self._stats['failed_loads'],
                'load_success_rate': (
                    (self._stats['loaded_modules'] / max(self._stats['total_modules'], 1)) * 100
                    if self._stats['total_modules'] > 0 else 0
                ),
                'avg_load_time': (
                    self._stats['total_load_time'] / max(self._stats['loaded_modules'], 1)
                    if self._stats['loaded_modules'] > 0 else 0
                ),
                'modules': module_stats
            }

    def optimize_loading(self):
        """优化加载策略"""
        stats = self.get_load_stats()

        # 识别高频访问模块
        high_access_modules = [
            m for m in stats['modules']
            if m['access_count'] >= self._preload_threshold and not m['loaded']
        ]

        # 预加载高频模块
        for module_info in high_access_modules:
            self.preload_module(module_info['name'])

        # 卸载长期未使用的模块
        import time
        current_time = time.time()
        unused_threshold = 300  # 5分钟未使用

        for name, module in list(self._modules.items()):
            if module.is_loaded() and module._access_count == 0:
                # 检查最后访问时间
                if hasattr(module, '_last_access') and \
                   current_time - module._last_access > unused_threshold:
                    self.unload_module(name)

        log_info("懒加载优化完成")

# 装饰器支持
def lazy_import(module_path: str, dependencies: List[str] = None):
    """懒导入装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 确保依赖模块已加载
            if dependencies:
                for dep in dependencies:
                    lazy_manager.preload_module(dep)

            # 动态导入模块
            try:
                module = importlib.import_module(module_path)
                # 将模块添加到函数的全局命名空间
                func.__globals__[module_path.split('.')[-1]] = module
                return func(*args, **kwargs)
            except ImportError as e:
                logger.error(f"懒导入失败: {module_path} - {e}")
                raise

        return wrapper
    return decorator

def lazy_property(factory_func: Callable):
    """懒加载属性装饰器"""
    attr_name = f"_lazy_{factory_func.__name__}"

    @property
    def lazy_prop(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, factory_func(self))
        return getattr(self, attr_name)

    return lazy_prop

# Perfect21特定的懒加载配置
def setup_perfect21_lazy_loading():
    """设置Perfect21的懒加载配置"""

    # Git工作流相关模块（高优先级）
    lazy_manager.register_module(
        'git_workflow',
        'features.git_workflow',
        priority=1,
        dependencies=[]
    )

    # 并行执行器（高优先级）
    lazy_manager.register_module(
        'parallel_executor',
        'features.parallel_executor',
        priority=1,
        dependencies=['smart_decomposer']
    )

    # 智能分解器（中优先级）
    lazy_manager.register_module(
        'smart_decomposer',
        'features.smart_decomposer',
        priority=2
    )

    # 工作流编排器（中优先级）
    lazy_manager.register_module(
        'workflow_orchestrator',
        'features.workflow_orchestrator.orchestrator',
        priority=2
    )

    # 缓存管理器（高优先级）
    lazy_manager.register_module(
        'cache_manager',
        'modules.cache',
        priority=1
    )

    # 数据库管理器（中优先级）
    lazy_manager.register_module(
        'database_manager',
        'modules.database',
        priority=2
    )

    # 学习反馈系统（低优先级）
    lazy_manager.register_module(
        'learning_feedback',
        'features.learning_feedback',
        priority=4
    )

    # 多工作空间系统（低优先级）
    lazy_manager.register_module(
        'multi_workspace',
        'features.multi_workspace',
        priority=4
    )

    # CLAUDE.md管理器（低优先级）
    lazy_manager.register_module(
        'claude_md_manager',
        'features.claude_md_manager',
        priority=5
    )

    # 预防性质量检查（中优先级）
    lazy_manager.register_module(
        'preventive_quality',
        'features.preventive_quality',
        priority=3
    )

    # 注册常用类
    lazy_manager.register_class(
        'Perfect21',
        'main.perfect21.Perfect21',
        singleton=True
    )

    log_info("Perfect21懒加载配置完成")

# 全局懒加载管理器实例
lazy_manager = LazyLoadManager()

# 便捷函数
def get_lazy_module(name: str):
    """获取懒加载模块"""
    return lazy_manager.get_module(name)

def get_lazy_class(name: str):
    """获取懒加载类"""
    return lazy_manager.get_class(name)

def preload_critical_modules():
    """预加载关键模块"""
    return lazy_manager.preload_by_priority(max_priority=2)

def optimize_module_loading():
    """优化模块加载"""
    lazy_manager.optimize_loading()

# 启动时设置
setup_perfect21_lazy_loading()

# 如果配置启用，预加载关键模块
if config.get('lazy_load.preload_critical', True):
    try:
        preload_critical_modules()
    except Exception as e:
        log_error("预加载关键模块失败", e)