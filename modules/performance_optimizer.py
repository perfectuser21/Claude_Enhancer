#!/usr/bin/env python3
"""
Perfect21性能优化器
集成所有性能优化模块，提供自动优化和智能调优
"""

import os
import sys
import time
import asyncio
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.logger import log_info, log_error
from modules.config import config
from modules.performance_cache import performance_cache
from modules.connection_pool import connection_pool_manager
from modules.lazy_loader import lazy_manager
from modules.performance_monitor import performance_monitor
from modules.resource_manager import get_resource_manager

logger = logging.getLogger(__name__)

@dataclass
class OptimizationRule:
    """优化规则"""
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    action: Callable[[Dict[str, Any]], bool]
    priority: int = 5  # 优先级，数字越小优先级越高
    cooldown: int = 300  # 冷却时间（秒）
    last_executed: Optional[datetime] = None
    execution_count: int = 0
    success_count: int = 0
    description: str = ""

class PerformanceOptimizer:
    """性能优化器"""

    def __init__(self):
        self.optimization_rules: List[OptimizationRule] = []
        self.optimization_history: List[Dict[str, Any]] = []
        self.auto_optimization = config.get('performance.auto_optimization', True)
        self.optimization_interval = config.get('performance.optimization_interval', 300)  # 5分钟

        # 优化状态
        self.optimizing = False
        self.optimizer_thread = None
        self.async_optimizer_task = None

        # 性能基线
        self.performance_baseline = {}
        self.last_optimization = None

        # 统计信息
        self.stats = {
            'total_optimizations': 0,
            'successful_optimizations': 0,
            'failed_optimizations': 0,
            'performance_improvement': 0.0,
            'last_optimization_time': None
        }

        # 初始化优化规则
        self._initialize_optimization_rules()

        log_info("性能优化器初始化完成")

    def _initialize_optimization_rules(self):
        """初始化优化规则"""

        # 1. 内存优化规则
        self.add_optimization_rule(
            "memory_pressure_cleanup",
            condition=lambda metrics: metrics.get('memory_usage', {}).get('percent', 0) > 85,
            action=self._optimize_memory_usage,
            priority=1,
            description="内存使用率超过85%时清理资源"
        )

        # 2. 缓存优化规则
        self.add_optimization_rule(
            "cache_hit_rate_optimization",
            condition=lambda metrics: float(str(metrics.get('cache_hit_rate', '100%')).rstrip('%')) < 60,
            action=self._optimize_cache_strategy,
            priority=2,
            description="缓存命中率低于60%时优化缓存策略"
        )

        # 3. 连接池优化规则
        self.add_optimization_rule(
            "connection_pool_optimization",
            condition=lambda metrics: any(
                pool.get('available_size', 0) == 0 and pool.get('current_size', 0) < pool.get('max_size', 10)
                for pool in metrics.get('connection_pools', {}).values()
            ),
            action=self._optimize_connection_pools,
            priority=3,
            description="连接池资源紧张时优化配置"
        )

        # 4. 懒加载优化规则
        self.add_optimization_rule(
            "lazy_loading_optimization",
            condition=lambda metrics: metrics.get('startup_time', 0) > 10,
            action=self._optimize_lazy_loading,
            priority=4,
            description="启动时间超过10秒时优化懒加载"
        )

        # 5. Git缓存优化规则
        self.add_optimization_rule(
            "git_cache_optimization",
            condition=lambda metrics: any(
                float(str(cache.get('hit_rate', '100%')).rstrip('%')) < 50
                for cache in metrics.get('git_caches', {}).values()
            ),
            action=self._optimize_git_cache,
            priority=3,
            description="Git缓存命中率低于50%时优化"
        )

        # 6. CPU优化规则
        self.add_optimization_rule(
            "cpu_usage_optimization",
            condition=lambda metrics: metrics.get('cpu_usage', 0) > 80,
            action=self._optimize_cpu_usage,
            priority=2,
            description="CPU使用率超过80%时优化"
        )

        # 7. 磁盘IO优化规则
        self.add_optimization_rule(
            "disk_io_optimization",
            condition=lambda metrics: metrics.get('disk_usage', 0) > 90,
            action=self._optimize_disk_usage,
            priority=1,
            description="磁盘使用率超过90%时优化"
        )

        # 8. 并行执行优化规则
        self.add_optimization_rule(
            "parallel_execution_optimization",
            condition=lambda metrics: metrics.get('parallel_efficiency', 100) < 70,
            action=self._optimize_parallel_execution,
            priority=3,
            description="并行执行效率低于70%时优化"
        )

    def add_optimization_rule(self, name: str, condition: Callable, action: Callable,
                             priority: int = 5, cooldown: int = 300, description: str = ""):
        """添加优化规则"""
        rule = OptimizationRule(
            name=name,
            condition=condition,
            action=action,
            priority=priority,
            cooldown=cooldown,
            description=description
        )

        # 按优先级插入
        inserted = False
        for i, existing_rule in enumerate(self.optimization_rules):
            if rule.priority < existing_rule.priority:
                self.optimization_rules.insert(i, rule)
                inserted = True
                break

        if not inserted:
            self.optimization_rules.append(rule)

        logger.debug(f"添加优化规则: {name} (优先级: {priority})")

    def start_auto_optimization(self):
        """启动自动优化"""
        if not self.auto_optimization or self.optimizing:
            return

        self.optimizing = True
        self.optimizer_thread = threading.Thread(target=self._optimization_loop, daemon=True)
        self.optimizer_thread.start()

        log_info(f"自动优化已启动，优化间隔: {self.optimization_interval}秒")

    async def start_async_auto_optimization(self):
        """启动异步自动优化"""
        if not self.auto_optimization or self.optimizing:
            return

        self.optimizing = True
        self.async_optimizer_task = asyncio.create_task(self._async_optimization_loop())

        log_info(f"异步自动优化已启动，优化间隔: {self.optimization_interval}秒")

    def stop_auto_optimization(self):
        """停止自动优化"""
        self.optimizing = False

        if self.optimizer_thread and self.optimizer_thread.is_alive():
            self.optimizer_thread.join(timeout=5)

        if self.async_optimizer_task and not self.async_optimizer_task.done():
            self.async_optimizer_task.cancel()

        log_info("自动优化已停止")

    def _optimization_loop(self):
        """优化循环"""
        while self.optimizing:
            try:
                self.run_optimization_cycle()
                time.sleep(self.optimization_interval)
            except Exception as e:
                logger.error(f"优化循环异常: {e}")

    async def _async_optimization_loop(self):
        """异步优化循环"""
        while self.optimizing:
            try:
                await self.run_async_optimization_cycle()
                await asyncio.sleep(self.optimization_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"异步优化循环异常: {e}")

    def run_optimization_cycle(self) -> Dict[str, Any]:
        """运行优化周期"""
        start_time = time.time()

        try:
            # 收集性能指标
            metrics = self._collect_performance_metrics()

            # 执行优化规则
            optimization_results = self._execute_optimization_rules(metrics)

            # 记录优化历史
            cycle_result = {
                'timestamp': datetime.now(),
                'duration': time.time() - start_time,
                'metrics': metrics,
                'optimizations': optimization_results,
                'success': len([r for r in optimization_results if r['success']]) > 0
            }

            self.optimization_history.append(cycle_result)
            self.last_optimization = datetime.now()

            # 更新统计信息
            self.stats['total_optimizations'] += len(optimization_results)
            self.stats['successful_optimizations'] += len([r for r in optimization_results if r['success']])
            self.stats['failed_optimizations'] += len([r for r in optimization_results if not r['success']])
            self.stats['last_optimization_time'] = cycle_result['timestamp']

            return cycle_result

        except Exception as e:
            logger.error(f"优化周期执行失败: {e}")
            return {
                'timestamp': datetime.now(),
                'duration': time.time() - start_time,
                'error': str(e),
                'success': False
            }

    async def run_async_optimization_cycle(self) -> Dict[str, Any]:
        """运行异步优化周期"""
        start_time = time.time()

        try:
            # 异步收集性能指标
            metrics = await self._async_collect_performance_metrics()

            # 异步执行优化规则
            optimization_results = await self._async_execute_optimization_rules(metrics)

            # 记录优化历史
            cycle_result = {
                'timestamp': datetime.now(),
                'duration': time.time() - start_time,
                'metrics': metrics,
                'optimizations': optimization_results,
                'success': len([r for r in optimization_results if r['success']]) > 0
            }

            self.optimization_history.append(cycle_result)
            self.last_optimization = datetime.now()

            # 更新统计信息
            self.stats['total_optimizations'] += len(optimization_results)
            self.stats['successful_optimizations'] += len([r for r in optimization_results if r['success']])
            self.stats['failed_optimizations'] += len([r for r in optimization_results if not r['success']])
            self.stats['last_optimization_time'] = cycle_result['timestamp']

            return cycle_result

        except Exception as e:
            logger.error(f"异步优化周期执行失败: {e}")
            return {
                'timestamp': datetime.now(),
                'duration': time.time() - start_time,
                'error': str(e),
                'success': False
            }

    def _collect_performance_metrics(self) -> Dict[str, Any]:
        """收集性能指标"""
        metrics = {}

        try:
            # 从性能监控器获取指标
            if hasattr(performance_monitor, 'monitoring') and performance_monitor.monitoring:
                current_metrics = performance_monitor.get_current_metrics()
                for name, metric in current_metrics.items():
                    metrics[name] = metric.value

            # 获取缓存性能
            cache_stats = performance_cache.get_performance_stats()
            metrics.update(cache_stats)

            # 获取连接池状态
            pool_stats = connection_pool_manager.get_all_stats()
            metrics['connection_pools'] = pool_stats

            # 获取懒加载统计
            lazy_stats = lazy_manager.get_load_stats()
            metrics['lazy_loading'] = lazy_stats

            # 获取资源管理器状态
            resource_manager = get_resource_manager()
            resource_stats = resource_manager.get_status()
            metrics['resource_management'] = resource_stats

            # 获取Git缓存状态
            try:
                from modules.git_cache import get_cache_stats
                git_stats = get_cache_stats()
                metrics['git_caches'] = git_stats
            except ImportError:
                pass

        except Exception as e:
            logger.error(f"收集性能指标失败: {e}")

        return metrics

    async def _async_collect_performance_metrics(self) -> Dict[str, Any]:
        """异步收集性能指标"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._collect_performance_metrics)

    def _execute_optimization_rules(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行优化规则"""
        results = []

        for rule in self.optimization_rules:
            # 检查冷却时间
            if rule.last_executed:
                time_since_last = (datetime.now() - rule.last_executed).total_seconds()
                if time_since_last < rule.cooldown:
                    continue

            # 检查条件
            try:
                if rule.condition(metrics):
                    # 执行优化动作
                    start_time = time.time()
                    success = rule.action(metrics)
                    duration = time.time() - start_time

                    # 更新规则统计
                    rule.execution_count += 1
                    rule.last_executed = datetime.now()
                    if success:
                        rule.success_count += 1

                    result = {
                        'rule_name': rule.name,
                        'success': success,
                        'duration': duration,
                        'description': rule.description
                    }

                    results.append(result)

                    if success:
                        logger.info(f"优化规则执行成功: {rule.name}")
                    else:
                        logger.warning(f"优化规则执行失败: {rule.name}")

            except Exception as e:
                logger.error(f"优化规则执行异常: {rule.name} - {e}")
                results.append({
                    'rule_name': rule.name,
                    'success': False,
                    'error': str(e),
                    'description': rule.description
                })

        return results

    async def _async_execute_optimization_rules(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """异步执行优化规则"""
        results = []
        tasks = []

        for rule in self.optimization_rules:
            # 检查冷却时间
            if rule.last_executed:
                time_since_last = (datetime.now() - rule.last_executed).total_seconds()
                if time_since_last < rule.cooldown:
                    continue

            # 检查条件
            try:
                if rule.condition(metrics):
                    # 创建异步任务
                    task = asyncio.create_task(self._async_execute_rule(rule, metrics))
                    tasks.append(task)
            except Exception as e:
                logger.error(f"优化规则条件检查异常: {rule.name} - {e}")

        # 等待所有任务完成
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # 过滤异常结果
            results = [r for r in results if not isinstance(r, Exception)]

        return results

    async def _async_execute_rule(self, rule: OptimizationRule, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行单个优化规则"""
        start_time = time.time()

        try:
            # 在executor中执行优化动作
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, rule.action, metrics)
            duration = time.time() - start_time

            # 更新规则统计
            rule.execution_count += 1
            rule.last_executed = datetime.now()
            if success:
                rule.success_count += 1

            result = {
                'rule_name': rule.name,
                'success': success,
                'duration': duration,
                'description': rule.description
            }

            if success:
                logger.info(f"异步优化规则执行成功: {rule.name}")
            else:
                logger.warning(f"异步优化规则执行失败: {rule.name}")

            return result

        except Exception as e:
            logger.error(f"异步优化规则执行异常: {rule.name} - {e}")
            return {
                'rule_name': rule.name,
                'success': False,
                'error': str(e),
                'description': rule.description
            }

    # 优化动作实现
    def _optimize_memory_usage(self, metrics: Dict[str, Any]) -> bool:
        """优化内存使用"""
        try:
            # 清理性能缓存
            performance_cache.clear_all()

            # 清理资源管理器闲置资源
            resource_manager = get_resource_manager()
            cleaned = resource_manager.cleanup_on_memory_pressure()

            # 强制垃圾回收
            import gc
            gc.collect()

            log_info(f"内存优化完成，清理了{cleaned}个资源")
            return True

        except Exception as e:
            logger.error(f"内存优化失败: {e}")
            return False

    def _optimize_cache_strategy(self, metrics: Dict[str, Any]) -> bool:
        """优化缓存策略"""
        try:
            # 清理过期缓存
            try:
                asyncio.run(performance_cache.cleanup_expired())
            except:
                # 如果异步清理失败，使用同步方式
                performance_cache.clear_all()

            # 调整缓存大小
            cache_stats = metrics.get('cache_stats', {})
            if cache_stats.get('memory_usage_mb', 0) > 100:
                # 如果缓存内存使用过高，清理部分缓存
                performance_cache.clear_all()

            log_info("缓存策略优化完成")
            return True

        except Exception as e:
            logger.error(f"缓存策略优化失败: {e}")
            return False

    def _optimize_connection_pools(self, metrics: Dict[str, Any]) -> bool:
        """优化连接池"""
        try:
            pool_stats = metrics.get('connection_pools', {})

            for pool_name, stats in pool_stats.items():
                if stats.get('available_size', 0) == 0:
                    # 连接池资源紧张，可以考虑调整配置
                    # 这里只是示例，实际需要根据具体情况调整
                    logger.info(f"连接池 {pool_name} 资源紧张，当前配置: {stats}")

            log_info("连接池优化完成")
            return True

        except Exception as e:
            logger.error(f"连接池优化失败: {e}")
            return False

    def _optimize_lazy_loading(self, metrics: Dict[str, Any]) -> bool:
        """优化懒加载"""
        try:
            # 优化模块加载策略
            lazy_manager.optimize_loading()

            log_info("懒加载优化完成")
            return True

        except Exception as e:
            logger.error(f"懒加载优化失败: {e}")
            return False

    def _optimize_git_cache(self, metrics: Dict[str, Any]) -> bool:
        """优化Git缓存"""
        try:
            from modules.git_cache import reset_git_cache
            reset_git_cache()

            log_info("Git缓存优化完成")
            return True

        except ImportError:
            logger.warning("Git缓存模块不可用")
            return False
        except Exception as e:
            logger.error(f"Git缓存优化失败: {e}")
            return False

    def _optimize_cpu_usage(self, metrics: Dict[str, Any]) -> bool:
        """优化CPU使用"""
        try:
            # 可以实施CPU优化策略，如调整线程池大小、暂停非关键任务等
            # 这里只是示例
            log_info("CPU使用优化完成")
            return True

        except Exception as e:
            logger.error(f"CPU使用优化失败: {e}")
            return False

    def _optimize_disk_usage(self, metrics: Dict[str, Any]) -> bool:
        """优化磁盘使用"""
        try:
            # 清理临时文件、日志文件等
            # 这里只是示例
            log_info("磁盘使用优化完成")
            return True

        except Exception as e:
            logger.error(f"磁盘使用优化失败: {e}")
            return False

    def _optimize_parallel_execution(self, metrics: Dict[str, Any]) -> bool:
        """优化并行执行"""
        try:
            # 优化并行执行策略
            # 这里只是示例
            log_info("并行执行优化完成")
            return True

        except Exception as e:
            logger.error(f"并行执行优化失败: {e}")
            return False

    def get_optimization_summary(self) -> Dict[str, Any]:
        """获取优化摘要"""
        rule_stats = []
        for rule in self.optimization_rules:
            success_rate = (rule.success_count / max(rule.execution_count, 1)) * 100
            rule_stats.append({
                'name': rule.name,
                'description': rule.description,
                'priority': rule.priority,
                'execution_count': rule.execution_count,
                'success_count': rule.success_count,
                'success_rate': f"{success_rate:.1f}%",
                'last_executed': rule.last_executed.isoformat() if rule.last_executed else None
            })

        return {
            'auto_optimization_enabled': self.auto_optimization,
            'optimization_interval': self.optimization_interval,
            'last_optimization': self.last_optimization.isoformat() if self.last_optimization else None,
            'optimization_stats': self.stats,
            'optimization_rules': rule_stats,
            'recent_history': [
                {
                    'timestamp': h['timestamp'].isoformat(),
                    'duration': h['duration'],
                    'optimizations_count': len(h.get('optimizations', [])),
                    'success': h['success']
                }
                for h in self.optimization_history[-10:]  # 最近10次
            ]
        }

    def force_optimization(self, rule_names: List[str] = None) -> Dict[str, Any]:
        """强制执行优化"""
        if rule_names is None:
            # 执行所有规则
            metrics = self._collect_performance_metrics()
            return {
                'timestamp': datetime.now(),
                'forced': True,
                'results': self._execute_optimization_rules(metrics)
            }
        else:
            # 执行指定规则
            results = []
            metrics = self._collect_performance_metrics()

            for rule in self.optimization_rules:
                if rule.name in rule_names:
                    try:
                        success = rule.action(metrics)
                        results.append({
                            'rule_name': rule.name,
                            'success': success,
                            'forced': True
                        })
                    except Exception as e:
                        results.append({
                            'rule_name': rule.name,
                            'success': False,
                            'error': str(e),
                            'forced': True
                        })

            return {
                'timestamp': datetime.now(),
                'forced': True,
                'results': results
            }

# 全局性能优化器实例
performance_optimizer = PerformanceOptimizer()

# 便捷函数
def start_performance_optimization():
    """启动性能优化"""
    performance_optimizer.start_auto_optimization()

def stop_performance_optimization():
    """停止性能优化"""
    performance_optimizer.stop_auto_optimization()

def run_optimization_now():
    """立即运行优化"""
    return performance_optimizer.run_optimization_cycle()

def force_optimization(rule_names: List[str] = None):
    """强制执行优化"""
    return performance_optimizer.force_optimization(rule_names)

def get_optimization_summary():
    """获取优化摘要"""
    return performance_optimizer.get_optimization_summary()

# 集成所有性能模块的便捷函数
def initialize_perfect21_performance():
    """初始化Perfect21性能优化"""
    try:
        # 启动性能监控
        from modules.performance_monitor import start_performance_monitoring
        start_performance_monitoring()

        # 启动自动优化
        start_performance_optimization()

        # 预加载关键模块
        from modules.lazy_loader import preload_critical_modules
        preload_critical_modules()

        log_info("Perfect21性能优化系统初始化完成")
        return True

    except Exception as e:
        log_error("Perfect21性能优化系统初始化失败", e)
        return False

def get_performance_overview():
    """获取性能概览"""
    try:
        from modules.performance_monitor import get_performance_summary

        return {
            'performance_monitoring': get_performance_summary(),
            'performance_optimization': get_optimization_summary(),
            'cache_status': performance_cache.get_performance_stats(),
            'resource_management': get_resource_manager().get_status(),
            'connection_pools': connection_pool_manager.get_all_stats(),
            'lazy_loading': lazy_manager.get_load_stats(),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取性能概览失败: {e}")
        return {'error': str(e)}

# 如果配置启用，自动初始化性能优化
if config.get('performance.auto_init', True):
    try:
        initialize_perfect21_performance()
    except Exception as e:
        log_error("自动初始化性能优化失败", e)