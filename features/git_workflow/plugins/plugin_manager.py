#!/usr/bin/env python3
"""
Perfect21 Git Hooks Plugin Manager
插件发现、加载和执行管理器
"""

import os
import sys
import time
import json
import logging
import importlib
import concurrent.futures
from typing import Dict, Any, List, Optional, Type, Union
from pathlib import Path
from dataclasses import asdict

from .base_plugin import BasePlugin, PluginResult, PluginStatus, PluginMetadata

logger = logging.getLogger("Perfect21.PluginManager")


class PluginManager:
    """插件管理器"""

    def __init__(self, plugins_dir: str = None, config: Dict[str, Any] = None):
        self.plugins_dir = plugins_dir or os.path.join(
            os.path.dirname(__file__)
        )
        self.config = config or {}

        # 插件注册表
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_classes: Dict[str, Type[BasePlugin]] = {}

        # 执行统计
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0
        }

        self.logger = logger

    def discover_plugins(self) -> Dict[str, str]:
        """
        发现所有可用的插件

        Returns:
            Dict[str, str]: 插件名称到文件路径的映射
        """
        discovered = {}

        # 发现内置插件
        builtin_dir = os.path.join(self.plugins_dir, 'built_in')
        if os.path.exists(builtin_dir):
            for file_path in Path(builtin_dir).rglob('*.py'):
                if file_path.name.startswith('__'):
                    continue

                plugin_name = file_path.stem
                discovered[plugin_name] = str(file_path)

        # 发现外部插件
        external_dir = os.path.join(self.plugins_dir, 'external')
        if os.path.exists(external_dir):
            for file_path in Path(external_dir).rglob('*.py'):
                if file_path.name.startswith('__'):
                    continue

                plugin_name = file_path.stem
                discovered[plugin_name] = str(file_path)

        self.logger.info(f"发现 {len(discovered)} 个插件: {list(discovered.keys())}")
        return discovered

    def load_plugin(self, plugin_name: str, plugin_path: str = None) -> bool:
        """
        加载单个插件

        Args:
            plugin_name: 插件名称
            plugin_path: 插件文件路径

        Returns:
            bool: 是否加载成功
        """
        try:
            if plugin_path and os.path.exists(plugin_path):
                # 从文件路径加载
                import importlib.util
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
                module = importlib.util.module_from_spec(spec)

                # 添加当前目录到sys.path以支持相对导入
                original_path = sys.path.copy()
                plugin_dir = os.path.dirname(plugin_path)
                if plugin_dir not in sys.path:
                    sys.path.insert(0, plugin_dir)

                try:
                    spec.loader.exec_module(module)
                finally:
                    # 恢复原始路径
                    sys.path[:] = original_path
            else:
                # 从模块路径加载
                import importlib
                try:
                    module_path = f"features.git_workflow.plugins.built_in.{plugin_name}"
                    module = importlib.import_module(module_path)
                except ImportError:
                    # 尝试相对导入
                    module_path = f".built_in.{plugin_name}"
                    module = importlib.import_module(module_path, package=__package__)

            # 查找插件类（排除抽象基类）
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, BasePlugin) and
                    attr != BasePlugin and
                    not getattr(attr, '__abstractmethods__', None)):  # 排除抽象类
                    plugin_class = attr
                    break

            if not plugin_class:
                self.logger.error(f"在模块 {plugin_name} 中未找到插件类")
                return False

            # 获取插件配置
            plugin_config = self.config.get('plugins', {}).get(plugin_name, {})

            # 创建插件实例
            plugin_instance = plugin_class(plugin_config.get('config', {}))

            # 验证环境
            if not plugin_instance.validate_environment():
                self.logger.error(f"插件 {plugin_name} 环境验证失败")
                return False

            # 执行插件设置
            if not plugin_instance.setup():
                self.logger.error(f"插件 {plugin_name} 初始化失败")
                return False

            # 注册插件
            self.plugins[plugin_name] = plugin_instance
            self.plugin_classes[plugin_name] = plugin_class

            self.logger.info(f"成功加载插件: {plugin_name}")
            return True

        except Exception as e:
            self.logger.error(f"加载插件 {plugin_name} 失败: {e}")
            return False

    def load_all_plugins(self) -> Dict[str, bool]:
        """
        加载所有发现的插件

        Returns:
            Dict[str, bool]: 插件名称到加载状态的映射
        """
        discovered = self.discover_plugins()
        results = {}

        for plugin_name, plugin_path in discovered.items():
            results[plugin_name] = self.load_plugin(plugin_name, plugin_path)

        loaded_count = sum(1 for success in results.values() if success)
        self.logger.info(f"插件加载完成: {loaded_count}/{len(discovered)} 个插件成功加载")

        return results

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """获取插件实例"""
        return self.plugins.get(plugin_name)

    def get_enabled_plugins(self) -> Dict[str, BasePlugin]:
        """获取所有启用的插件"""
        return {name: plugin for name, plugin in self.plugins.items() if plugin.enabled}

    def execute_plugin(self, plugin_name: str, context: Dict[str, Any]) -> PluginResult:
        """
        执行单个插件

        Args:
            plugin_name: 插件名称
            context: 执行上下文

        Returns:
            PluginResult: 执行结果
        """
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return PluginResult(
                status=PluginStatus.ERROR,
                message=f"插件不存在: {plugin_name}"
            )

        if not plugin.enabled:
            return PluginResult(
                status=PluginStatus.SKIPPED,
                message=f"插件已禁用: {plugin_name}"
            )

        if plugin.should_skip(context):
            return PluginResult(
                status=PluginStatus.SKIPPED,
                message=f"插件跳过执行: {plugin_name}"
            )

        start_time = time.time()

        try:
            # 设置执行上下文
            plugin.execution_context = context

            # 执行插件前的验证
            if not plugin.validate_environment():
                return PluginResult(
                    status=PluginStatus.ERROR,
                    message="插件环境验证失败",
                    execution_time=time.time() - start_time
                )

            # 执行插件
            result = plugin.execute(context)
            result.execution_time = time.time() - start_time

            # 验证返回结果
            if not isinstance(result, PluginResult):
                self.logger.warning(f"插件 {plugin_name} 返回了无效的结果类型")
                result = PluginResult(
                    status=PluginStatus.ERROR,
                    message="插件返回了无效的结果类型",
                    execution_time=time.time() - start_time
                )

            # 更新统计信息
            self.execution_stats["total_executions"] += 1
            self.execution_stats["total_execution_time"] += result.execution_time

            if result.status == PluginStatus.SUCCESS:
                self.execution_stats["successful_executions"] += 1
            elif result.status == PluginStatus.FAILURE:
                self.execution_stats["failed_executions"] += 1

            self.logger.info(f"插件 {plugin_name} 执行完成: {result.status.value} ({result.execution_time:.2f}s)")
            return result

        except KeyboardInterrupt:
            # 处理用户中断
            execution_time = time.time() - start_time
            self.execution_stats["total_executions"] += 1
            self.execution_stats["failed_executions"] += 1
            self.execution_stats["total_execution_time"] += execution_time

            self.logger.warning(f"插件 {plugin_name} 被用户中断")
            return PluginResult(
                status=PluginStatus.ERROR,
                message="插件执行被用户中断",
                execution_time=execution_time
            )

        except TimeoutError:
            # 处理超时
            execution_time = time.time() - start_time
            self.execution_stats["total_executions"] += 1
            self.execution_stats["failed_executions"] += 1
            self.execution_stats["total_execution_time"] += execution_time

            self.logger.error(f"插件 {plugin_name} 执行超时")
            return PluginResult(
                status=PluginStatus.ERROR,
                message=f"插件执行超时 ({plugin.metadata.timeout}秒)",
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.execution_stats["total_executions"] += 1
            self.execution_stats["failed_executions"] += 1
            self.execution_stats["total_execution_time"] += execution_time

            # 记录详细的错误信息
            import traceback
            error_details = traceback.format_exc()
            self.logger.error(f"插件 {plugin_name} 执行异常: {e}\n{error_details}")

            error_result = PluginResult(
                status=PluginStatus.ERROR,
                message=f"插件执行异常: {str(e)}",
                execution_time=execution_time,
                error=error_details
            )

            return error_result

    def execute_plugins(self, plugin_names: List[str], context: Dict[str, Any],
                       parallel: bool = True, max_workers: int = 4) -> Dict[str, PluginResult]:
        """
        执行多个插件

        Args:
            plugin_names: 插件名称列表
            context: 执行上下文
            parallel: 是否并行执行
            max_workers: 最大工作线程数

        Returns:
            Dict[str, PluginResult]: 插件名称到执行结果的映射
        """
        results = {}

        if not parallel or len(plugin_names) == 1:
            # 串行执行
            for plugin_name in plugin_names:
                results[plugin_name] = self.execute_plugin(plugin_name, context)
        else:
            # 并行执行
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_plugin = {
                    executor.submit(self.execute_plugin, plugin_name, context): plugin_name
                    for plugin_name in plugin_names
                }

                for future in concurrent.futures.as_completed(future_to_plugin):
                    plugin_name = future_to_plugin[future]
                    try:
                        results[plugin_name] = future.result(timeout=120)  # 2分钟超时
                    except concurrent.futures.TimeoutError:
                        self.logger.error(f"插件 {plugin_name} 并行执行超时")
                        results[plugin_name] = PluginResult(
                            status=PluginStatus.ERROR,
                            message="并行执行超时"
                        )
                    except KeyboardInterrupt:
                        self.logger.warning(f"插件 {plugin_name} 并行执行被中断")
                        results[plugin_name] = PluginResult(
                            status=PluginStatus.ERROR,
                            message="并行执行被用户中断"
                        )
                    except Exception as e:
                        import traceback
                        error_details = traceback.format_exc()
                        self.logger.error(f"插件 {plugin_name} 并行执行异常: {e}\n{error_details}")
                        results[plugin_name] = PluginResult(
                            status=PluginStatus.ERROR,
                            message=f"并行执行异常: {str(e)}",
                            error=error_details
                        )

        return results

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件信息"""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return None

        return {
            "name": plugin_name,
            "enabled": plugin.enabled,
            "metadata": asdict(plugin.metadata),
            "config": plugin.config
        }

    def get_all_plugins_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有插件信息"""
        return {
            name: self.get_plugin_info(name)
            for name in self.plugins.keys()
        }

    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        plugin = self.plugins.get(plugin_name)
        if plugin:
            plugin.enabled = True
            self.logger.info(f"插件 {plugin_name} 已启用")
            return True
        return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        plugin = self.plugins.get(plugin_name)
        if plugin:
            plugin.enabled = False
            self.logger.info(f"插件 {plugin_name} 已禁用")
            return True
        return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]

            # 执行清理
            try:
                plugin.teardown()
            except Exception as e:
                self.logger.warning(f"插件 {plugin_name} 清理失败: {e}")

            # 清理插件内部引用
            if hasattr(plugin, 'execution_context'):
                plugin.execution_context.clear()
            if hasattr(plugin, 'config'):
                plugin.config.clear()

            # 从注册表中移除
            del self.plugins[plugin_name]
            if plugin_name in self.plugin_classes:
                del self.plugin_classes[plugin_name]

            # 清理对象引用
            del plugin

            self.logger.info(f"插件 {plugin_name} 已卸载")
            return True

        return False

    def reload_plugin(self, plugin_name: str) -> bool:
        """重新加载插件"""
        # 先卸载
        if plugin_name in self.plugins:
            if not self.unload_plugin(plugin_name):
                return False

        # 重新发现和加载
        discovered = self.discover_plugins()
        plugin_path = discovered.get(plugin_name)

        if plugin_path:
            return self.load_plugin(plugin_name, plugin_path)

        return False

    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        stats = self.execution_stats.copy()

        if stats["total_executions"] > 0:
            stats["success_rate"] = (stats["successful_executions"] / stats["total_executions"]) * 100
            stats["average_execution_time"] = stats["total_execution_time"] / stats["total_executions"]
        else:
            stats["success_rate"] = 0.0
            stats["average_execution_time"] = 0.0

        return stats

    def generate_report(self) -> str:
        """生成插件管理器报告"""
        stats = self.get_execution_stats()
        plugin_count = len(self.plugins)
        enabled_count = len(self.get_enabled_plugins())

        return f"""
📊 Perfect21 插件管理器报告
============================
插件总数: {plugin_count}
启用插件: {enabled_count}
禁用插件: {plugin_count - enabled_count}

📈 执行统计:
总执行次数: {stats['total_executions']}
成功次数: {stats['successful_executions']}
失败次数: {stats['failed_executions']}
成功率: {stats['success_rate']:.1f}%
平均执行时间: {stats['average_execution_time']:.2f}s

🔌 已加载插件:
{chr(10).join(f'  - {name} ({"✅" if plugin.enabled else "❌"})' for name, plugin in self.plugins.items())}
        """.strip()

    def cleanup(self) -> None:
        """清理所有插件"""
        plugin_names = list(self.plugins.keys())
        for plugin_name in plugin_names:
            self.unload_plugin(plugin_name)

        # 强制清理引用
        self.plugins.clear()
        self.plugin_classes.clear()

        # 清理执行统计
        self.execution_stats.clear()
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0
        }

        # 清理配置引用
        if hasattr(self, 'config') and self.config:
            self.config.clear()

        # 清理sys.modules中的插件模块（谨慎操作）
        try:
            import sys
            modules_to_remove = []
            for module_name in list(sys.modules.keys()):
                if ('features.git_workflow.plugins.built_in' in module_name and
                    module_name != 'features.git_workflow.plugins.built_in'):
                    modules_to_remove.append(module_name)

            for module_name in modules_to_remove:
                try:
                    if module_name in sys.modules:
                        del sys.modules[module_name]
                except (KeyError, AttributeError):
                    pass
        except Exception as e:
            # 如果sys模块清理失败，记录警告但不影响其他清理
            self.logger.warning(f"清理sys.modules失败，忽略: {e}")

        # 强制垃圾回收 (多次执行以确保完全清理)
        import gc
        for _ in range(3):
            gc.collect()

        self.logger.info("所有插件及内存已清理")

    def __del__(self):
        """析构函数，确保插件被清理"""
        try:
            self.cleanup()
        except:
            pass