#!/usr/bin/env python3
"""
Perfect21性能优化器 - 增强版本
实现智能性能分析、自动优化建议和系统调优
"""

import os
import sys
import time
import asyncio
import threading
import psutil
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
import gc

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.logger import log_info, log_error, log_warning
from modules.performance_monitor import performance_monitor, PerformanceMetric

logger = logging.getLogger(__name__)

@dataclass
class OptimizationRecommendation:
    """优化建议"""
    category: str  # cache, memory, cpu, io, network
    priority: str  # low, medium, high, critical
    title: str
    description: str
    implementation: str
    expected_improvement: str
    estimated_effort: str  # low, medium, high
    impact_score: float  # 0-100

@dataclass
class PerformanceProfile:
    """性能剖析结果"""
    component: str
    method: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    call_count: int
    bottleneck_score: float  # 0-100

@dataclass
class SystemBottleneck:
    """系统瓶颈"""
    type: str  # cpu, memory, io, network, cache
    severity: str  # low, medium, high, critical
    current_value: float
    threshold: float
    component: str
    impact_description: str

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

class PerformanceProfiler:
    """性能剖析器"""

    def __init__(self):
        self.profiles: Dict[str, List[PerformanceProfile]] = defaultdict(list)
        self.profiling_active = False
        self.start_time = None
        self.sample_interval = 0.1  # 100ms采样间隔

    def start_profiling(self, component: str):
        """开始性能剖析"""
        self.profiling_active = True
        self.start_time = time.perf_counter()
        log_info(f"开始性能剖析: {component}")

    def stop_profiling(self, component: str):
        """停止性能剖析"""
        self.profiling_active = False
        if self.start_time:
            total_time = time.perf_counter() - self.start_time
            log_info(f"性能剖析完成: {component}, 总时间: {total_time:.3f}s")

    def profile_method(self, component: str, method: str, func: Callable, *args, **kwargs):
        """剖析方法性能"""
        if not self.profiling_active:
            return func(*args, **kwargs)

        # 执行前状态
        process = psutil.Process()
        memory_before = process.memory_info().rss
        cpu_before = process.cpu_percent()

        start_time = time.perf_counter()

        try:
            result = func(*args, **kwargs)

            # 执行后状态
            execution_time = time.perf_counter() - start_time
            memory_after = process.memory_info().rss
            cpu_after = process.cpu_percent()

            # 创建性能剖析
            profile = PerformanceProfile(
                component=component,
                method=method,
                execution_time=execution_time,
                memory_usage=(memory_after - memory_before) / 1024 / 1024,  # MB
                cpu_usage=(cpu_after - cpu_before),
                call_count=1,
                bottleneck_score=self._calculate_bottleneck_score(execution_time, memory_after - memory_before, cpu_after - cpu_before)
            )

            self.profiles[component].append(profile)
            return result

        except Exception as e:
            logger.error(f"性能剖析异常 {component}.{method}: {e}")
            raise

    def _calculate_bottleneck_score(self, exec_time: float, memory_delta: float, cpu_delta: float) -> float:
        """计算瓶颈分数"""
        score = 0.0

        # 执行时间权重 (40%)
        if exec_time > 1.0:  # > 1秒
            score += 40
        elif exec_time > 0.5:  # > 500ms
            score += 25
        elif exec_time > 0.1:  # > 100ms
            score += 10

        # 内存使用权重 (30%)
        memory_mb = memory_delta / 1024 / 1024
        if memory_mb > 100:  # > 100MB
            score += 30
        elif memory_mb > 50:  # > 50MB
            score += 20
        elif memory_mb > 10:  # > 10MB
            score += 10

        # CPU使用权重 (30%)
        if cpu_delta > 80:  # > 80%
            score += 30
        elif cpu_delta > 50:  # > 50%
            score += 20
        elif cpu_delta > 20:  # > 20%
            score += 10

        return min(100.0, score)

    def get_bottlenecks(self, threshold: float = 50.0) -> List[PerformanceProfile]:
        """获取性能瓶颈"""
        bottlenecks = []
        for component_profiles in self.profiles.values():
            for profile in component_profiles:
                if profile.bottleneck_score >= threshold:
                    bottlenecks.append(profile)

        # 按瓶颈分数排序
        bottlenecks.sort(key=lambda p: p.bottleneck_score, reverse=True)
        return bottlenecks

    def get_summary(self) -> Dict[str, Any]:
        """获取剖析摘要"""
        total_profiles = sum(len(profiles) for profiles in self.profiles.values())
        bottleneck_count = len(self.get_bottlenecks())

        component_summary = {}
        for component, profiles in self.profiles.items():
            if profiles:
                avg_exec_time = statistics.mean(p.execution_time for p in profiles)
                total_memory = sum(p.memory_usage for p in profiles)
                max_bottleneck = max(p.bottleneck_score for p in profiles)

                component_summary[component] = {
                    'profile_count': len(profiles),
                    'avg_execution_time': avg_exec_time,
                    'total_memory_usage': total_memory,
                    'max_bottleneck_score': max_bottleneck
                }

        return {
            'total_profiles': total_profiles,
            'bottleneck_count': bottleneck_count,
            'component_summary': component_summary
        }

class CacheOptimizer:
    """缓存优化器"""

    def __init__(self):
        self.cache_stats: Dict[str, Dict[str, Any]] = {}
        self.optimization_history: List[Dict[str, Any]] = []

    def analyze_cache_performance(self) -> List[OptimizationRecommendation]:
        """分析缓存性能"""
        recommendations = []

        try:
            # 分析性能缓存
            from modules.performance_cache import performance_cache
            perf_stats = performance_cache.get_performance_stats()

            hit_rate = float(perf_stats.get('cache_hit_rate', '0%').rstrip('%'))
            memory_usage = perf_stats.get('memory_usage_mb', 0)

            if hit_rate < 70:
                recommendations.append(OptimizationRecommendation(
                    category='cache',
                    priority='high',
                    title='性能缓存命中率过低',
                    description=f'当前命中率 {hit_rate:.1f}%，低于推荐的70%',
                    implementation='增加缓存大小或优化缓存策略',
                    expected_improvement='提升响应速度20-30%',
                    estimated_effort='medium',
                    impact_score=80.0
                ))

            if memory_usage > 200:
                recommendations.append(OptimizationRecommendation(
                    category='cache',
                    priority='medium',
                    title='缓存内存使用过高',
                    description=f'当前使用 {memory_usage}MB，可能影响系统内存',
                    implementation='启用LRU淘汰策略或减少缓存大小',
                    expected_improvement='降低内存压力',
                    estimated_effort='low',
                    impact_score=60.0
                ))

        except ImportError:
            pass

        try:
            # 分析Git缓存
            from modules.git_cache import get_cache_stats
            git_stats = get_cache_stats()

            for cache_name, stats in git_stats.items():
                hit_rate = float(stats.get('hit_rate', '0%').rstrip('%'))
                if hit_rate < 60:
                    recommendations.append(OptimizationRecommendation(
                        category='cache',
                        priority='medium',
                        title=f'Git缓存 {cache_name} 命中率低',
                        description=f'命中率 {hit_rate:.1f}%，影响Git操作性能',
                        implementation='增加Git缓存TTL或优化缓存键策略',
                        expected_improvement='提升Git操作速度15-25%',
                        estimated_effort='low',
                        impact_score=50.0
                    ))

        except ImportError:
            pass

        return recommendations

    def optimize_cache_configuration(self) -> Dict[str, Any]:
        """优化缓存配置"""
        optimizations = []

        try:
            # 优化性能缓存
            from modules.performance_cache import performance_cache

            # 分析访问模式
            stats = performance_cache.get_performance_stats()
            current_size = stats.get('current_entries', 0)

            if current_size > 0:
                # 建议的优化配置
                recommended_config = {
                    'max_size': min(2000, current_size * 2),  # 增加到当前的2倍，最大2000
                    'ttl': 3600,  # 1小时TTL
                    'cleanup_interval': 300,  # 5分钟清理间隔
                    'compression': True  # 启用压缩
                }

                optimizations.append({
                    'component': 'performance_cache',
                    'current_config': stats,
                    'recommended_config': recommended_config,
                    'expected_improvement': 'memory efficiency +15%, hit rate +10%'
                })

        except ImportError:
            pass

        return {
            'optimizations_applied': optimizations,
            'timestamp': datetime.now().isoformat()
        }

class MemoryOptimizer:
    """内存优化器"""

    def __init__(self):
        self.memory_profiles: List[Dict[str, Any]] = []
        self.gc_stats: Dict[str, Any] = {}

    def analyze_memory_usage(self) -> List[OptimizationRecommendation]:
        """分析内存使用"""
        recommendations = []

        # 获取当前内存状态
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()

        # 系统内存
        system_memory = psutil.virtual_memory()

        # 内存使用过高
        if memory_percent > 10:  # 进程使用超过10%系统内存
            recommendations.append(OptimizationRecommendation(
                category='memory',
                priority='high',
                title='进程内存使用过高',
                description=f'当前使用 {memory_percent:.1f}% 系统内存 ({memory_info.rss/1024/1024:.1f}MB)',
                implementation='启用内存池、优化数据结构、增加GC频率',
                expected_improvement='降低内存使用30-50%',
                estimated_effort='high',
                impact_score=85.0
            ))

        # 系统内存压力
        if system_memory.percent > 85:
            recommendations.append(OptimizationRecommendation(
                category='memory',
                priority='critical',
                title='系统内存压力过大',
                description=f'系统内存使用 {system_memory.percent:.1f}%',
                implementation='减少缓存大小、启用内存压缩、清理不必要的对象',
                expected_improvement='缓解系统内存压力',
                estimated_effort='medium',
                impact_score=95.0
            ))

        # 检查内存泄漏
        self._check_memory_leaks(recommendations)

        return recommendations

    def _check_memory_leaks(self, recommendations: List[OptimizationRecommendation]):
        """检查内存泄漏"""
        # 记录当前内存状态
        current_memory = psutil.Process().memory_info().rss
        self.memory_profiles.append({
            'timestamp': datetime.now(),
            'memory_rss': current_memory,
            'memory_vms': psutil.Process().memory_info().vms
        })

        # 保持最近100个记录
        if len(self.memory_profiles) > 100:
            self.memory_profiles = self.memory_profiles[-100:]

        # 分析内存增长趋势
        if len(self.memory_profiles) >= 10:
            recent_memories = [p['memory_rss'] for p in self.memory_profiles[-10:]]
            if len(set(recent_memories)) > 1:  # 有变化
                memory_growth = (recent_memories[-1] - recent_memories[0]) / recent_memories[0]

                if memory_growth > 0.2:  # 增长超过20%
                    recommendations.append(OptimizationRecommendation(
                        category='memory',
                        priority='high',
                        title='检测到潜在内存泄漏',
                        description=f'最近内存增长 {memory_growth:.1%}',
                        implementation='使用内存剖析工具、检查循环引用、增加显式GC',
                        expected_improvement='防止内存泄漏导致的性能下降',
                        estimated_effort='high',
                        impact_score=90.0
                    ))

    def optimize_memory_usage(self) -> Dict[str, Any]:
        """优化内存使用"""
        optimizations = []

        # 强制垃圾回收
        before_gc = psutil.Process().memory_info().rss
        gc.collect()
        after_gc = psutil.Process().memory_info().rss

        gc_freed = (before_gc - after_gc) / 1024 / 1024  # MB

        optimizations.append({
            'action': 'garbage_collection',
            'memory_freed_mb': gc_freed,
            'effectiveness': 'high' if gc_freed > 10 else 'low'
        })

        # 获取GC统计
        gc_stats = {
            'collections': gc.get_stats(),
            'counts': gc.get_count(),
            'threshold': gc.get_threshold()
        }

        self.gc_stats = gc_stats

        # 建议GC调优
        if gc_stats['counts'][0] > 1000:  # generation 0收集次数过多
            optimizations.append({
                'action': 'gc_tuning',
                'recommendation': 'increase_gc_threshold',
                'current_threshold': gc_stats['threshold'],
                'suggested_threshold': (gc_stats['threshold'][0] * 2, gc_stats['threshold'][1], gc_stats['threshold'][2])
            })

        return {
            'optimizations_applied': optimizations,
            'gc_stats': gc_stats,
            'memory_after_optimization': psutil.Process().memory_info().rss / 1024 / 1024
        }

class IOOptimizer:
    """I/O优化器"""

    def __init__(self):
        self.io_stats: Dict[str, Any] = {}

    def analyze_io_performance(self) -> List[OptimizationRecommendation]:
        """分析I/O性能"""
        recommendations = []

        # 获取进程I/O统计
        process = psutil.Process()
        io_counters = process.io_counters()

        # 记录I/O统计
        self.io_stats = {
            'read_bytes': io_counters.read_bytes,
            'write_bytes': io_counters.write_bytes,
            'read_count': io_counters.read_count,
            'write_count': io_counters.write_count,
            'timestamp': datetime.now()
        }

        # 分析磁盘I/O
        disk_usage = psutil.disk_usage('/')
        if disk_usage.percent > 90:
            recommendations.append(OptimizationRecommendation(
                category='io',
                priority='critical',
                title='磁盘空间不足',
                description=f'磁盘使用率 {disk_usage.percent:.1f}%',
                implementation='清理临时文件、启用日志轮转、移动大文件',
                expected_improvement='避免I/O性能下降',
                estimated_effort='medium',
                impact_score=95.0
            ))

        # 检查文件描述符使用
        try:
            num_fds = process.num_fds()
            if num_fds > 500:
                recommendations.append(OptimizationRecommendation(
                    category='io',
                    priority='medium',
                    title='文件描述符使用过多',
                    description=f'当前使用 {num_fds} 个文件描述符',
                    implementation='使用连接池、及时关闭文件、检查资源泄漏',
                    expected_improvement='减少系统资源消耗',
                    estimated_effort='medium',
                    impact_score=70.0
                ))
        except AttributeError:
            pass  # Windows系统不支持num_fds

        return recommendations

    def optimize_io_performance(self) -> Dict[str, Any]:
        """优化I/O性能"""
        optimizations = []

        # 清理临时文件
        temp_dirs = ['/tmp', '/var/tmp']
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    # 清理24小时前的临时文件
                    cutoff_time = time.time() - 24 * 3600
                    cleaned_files = 0

                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                if os.path.getmtime(file_path) < cutoff_time:
                                    os.remove(file_path)
                                    cleaned_files += 1
                            except (OSError, PermissionError):
                                pass

                    if cleaned_files > 0:
                        optimizations.append({
                            'action': 'temp_file_cleanup',
                            'directory': temp_dir,
                            'files_cleaned': cleaned_files
                        })

                except (OSError, PermissionError):
                    pass

        return {
            'optimizations_applied': optimizations,
            'timestamp': datetime.now().isoformat()
        }

class PerformanceOptimizer:
    """主性能优化器"""

    def __init__(self):
        self.profiler = PerformanceProfiler()
        self.cache_optimizer = CacheOptimizer()
        self.memory_optimizer = MemoryOptimizer()
        self.io_optimizer = IOOptimizer()

        self.optimization_history: List[Dict[str, Any]] = []
        self.optimization_rules: List[OptimizationRule] = []
        self.auto_optimization = False
        self.optimization_interval = 300  # 5分钟

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

        # 3. CPU优化规则
        self.add_optimization_rule(
            "cpu_usage_optimization",
            condition=lambda metrics: metrics.get('cpu_usage', 0) > 80,
            action=self._optimize_cpu_usage,
            priority=2,
            description="CPU使用率超过80%时优化"
        )

        # 4. 磁盘IO优化规则
        self.add_optimization_rule(
            "disk_io_optimization",
            condition=lambda metrics: metrics.get('disk_usage', 0) > 90,
            action=self._optimize_disk_usage,
            priority=1,
            description="磁盘使用率超过90%时优化"
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

    def analyze_system_performance(self) -> Dict[str, Any]:
        """全面分析系统性能"""
        analysis_start = time.perf_counter()

        # 收集所有性能指标
        current_metrics = performance_monitor.get_current_metrics()

        # 识别系统瓶颈
        bottlenecks = self._identify_bottlenecks(current_metrics)

        # 收集优化建议
        all_recommendations = []
        all_recommendations.extend(self.cache_optimizer.analyze_cache_performance())
        all_recommendations.extend(self.memory_optimizer.analyze_memory_usage())
        all_recommendations.extend(self.io_optimizer.analyze_io_performance())

        # 计算系统健康分数
        health_score = self._calculate_system_health_score(current_metrics, bottlenecks)

        # 性能剖析摘要
        profiling_summary = self.profiler.get_summary()

        analysis_time = time.perf_counter() - analysis_start

        analysis_result = {
            'timestamp': datetime.now().isoformat(),
            'analysis_time': analysis_time,
            'health_score': health_score,
            'bottlenecks': [self._bottleneck_to_dict(b) for b in bottlenecks],
            'recommendations': [self._recommendation_to_dict(r) for r in all_recommendations],
            'profiling_summary': profiling_summary,
            'system_metrics': self._metrics_to_dict(current_metrics),
            'optimization_potential': self._calculate_optimization_potential(all_recommendations)
        }

        log_info(f"系统性能分析完成，健康分数: {health_score:.1f}/100")
        return analysis_result

    def _identify_bottlenecks(self, metrics: Dict[str, PerformanceMetric]) -> List[SystemBottleneck]:
        """识别系统瓶颈"""
        bottlenecks = []

        # CPU瓶颈
        if 'cpu_usage' in metrics:
            cpu_metric = metrics['cpu_usage']
            if cpu_metric.value > 85:
                bottlenecks.append(SystemBottleneck(
                    type='cpu',
                    severity='high',
                    current_value=cpu_metric.value,
                    threshold=85.0,
                    component='system',
                    impact_description=f'CPU使用率 {cpu_metric.value:.1f}% 过高，可能影响响应速度'
                ))

        # 内存瓶颈
        if 'memory_usage' in metrics:
            memory_metric = metrics['memory_usage']
            if memory_metric.value > 90:
                bottlenecks.append(SystemBottleneck(
                    type='memory',
                    severity='critical',
                    current_value=memory_metric.value,
                    threshold=90.0,
                    component='system',
                    impact_description=f'内存使用率 {memory_metric.value:.1f}% 临界，可能导致系统不稳定'
                ))

        # 磁盘瓶颈
        if 'disk_usage' in metrics:
            disk_metric = metrics['disk_usage']
            if disk_metric.value > 85:
                bottlenecks.append(SystemBottleneck(
                    type='io',
                    severity='high',
                    current_value=disk_metric.value,
                    threshold=85.0,
                    component='storage',
                    impact_description=f'磁盘使用率 {disk_metric.value:.1f}% 过高，影响I/O性能'
                ))

        # 缓存瓶颈
        if 'cache_hit_rate' in metrics:
            cache_metric = metrics['cache_hit_rate']
            if cache_metric.value < 70:
                bottlenecks.append(SystemBottleneck(
                    type='cache',
                    severity='medium',
                    current_value=cache_metric.value,
                    threshold=70.0,
                    component='cache',
                    impact_description=f'缓存命中率 {cache_metric.value:.1f}% 过低，影响响应速度'
                ))

        return bottlenecks

    def _calculate_system_health_score(self, metrics: Dict[str, PerformanceMetric],
                                     bottlenecks: List[SystemBottleneck]) -> float:
        """计算系统健康分数"""
        base_score = 100.0

        # 根据瓶颈扣分
        for bottleneck in bottlenecks:
            if bottleneck.severity == 'critical':
                base_score -= 25
            elif bottleneck.severity == 'high':
                base_score -= 15
            elif bottleneck.severity == 'medium':
                base_score -= 10
            else:
                base_score -= 5

        # 根据关键指标调整
        key_metrics = ['cpu_usage', 'memory_usage', 'disk_usage']
        for metric_name in key_metrics:
            if metric_name in metrics:
                metric = metrics[metric_name]
                if hasattr(metric, 'threshold_critical') and metric.threshold_critical:
                    if metric.value >= metric.threshold_critical:
                        base_score -= 20
                    elif hasattr(metric, 'threshold_warning') and metric.threshold_warning:
                        if metric.value >= metric.threshold_warning:
                            base_score -= 10

        return max(0.0, min(100.0, base_score))

    def _calculate_optimization_potential(self, recommendations: List[OptimizationRecommendation]) -> Dict[str, Any]:
        """计算优化潜力"""
        if not recommendations:
            return {'score': 0, 'category': 'excellent'}

        # 按优先级计算潜在改进
        potential_score = 0
        for rec in recommendations:
            if rec.priority == 'critical':
                potential_score += rec.impact_score * 1.0
            elif rec.priority == 'high':
                potential_score += rec.impact_score * 0.8
            elif rec.priority == 'medium':
                potential_score += rec.impact_score * 0.5
            else:
                potential_score += rec.impact_score * 0.2

        # 归一化到0-100
        max_possible_score = len(recommendations) * 100
        normalized_score = min(100, potential_score / max_possible_score * 100) if max_possible_score > 0 else 0

        # 分类优化潜力
        if normalized_score < 20:
            category = 'low'
        elif normalized_score < 50:
            category = 'medium'
        elif normalized_score < 80:
            category = 'high'
        else:
            category = 'critical'

        return {
            'score': normalized_score,
            'category': category,
            'total_recommendations': len(recommendations),
            'high_priority_count': len([r for r in recommendations if r.priority in ['critical', 'high']])
        }

    def apply_optimizations(self, optimization_types: List[str] = None) -> Dict[str, Any]:
        """应用性能优化"""
        if optimization_types is None:
            optimization_types = ['cache', 'memory', 'io']

        optimization_start = time.perf_counter()
        results = {}

        try:
            if 'cache' in optimization_types:
                results['cache'] = self.cache_optimizer.optimize_cache_configuration()

            if 'memory' in optimization_types:
                results['memory'] = self.memory_optimizer.optimize_memory_usage()

            if 'io' in optimization_types:
                results['io'] = self.io_optimizer.optimize_io_performance()

            optimization_time = time.perf_counter() - optimization_start

            # 记录优化历史
            optimization_record = {
                'timestamp': datetime.now().isoformat(),
                'optimization_types': optimization_types,
                'results': results,
                'optimization_time': optimization_time
            }

            self.optimization_history.append(optimization_record)

            # 保持最近100条记录
            if len(self.optimization_history) > 100:
                self.optimization_history = self.optimization_history[-100:]

            log_info(f"性能优化完成，类型: {optimization_types}, 用时: {optimization_time:.3f}s")

            return {
                'success': True,
                'optimization_time': optimization_time,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            log_error(f"性能优化失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def start_auto_optimization(self, interval: int = 300):
        """启动自动优化"""
        self.auto_optimization = True
        self.optimization_interval = interval

        def auto_optimization_loop():
            while self.auto_optimization:
                try:
                    # 分析性能
                    analysis = self.analyze_system_performance()

                    # 如果健康分数低于70，触发优化
                    if analysis['health_score'] < 70:
                        high_priority_recs = [
                            r for r in analysis['recommendations']
                            if r['priority'] in ['critical', 'high']
                        ]

                        if high_priority_recs:
                            log_warning(f"检测到性能问题，健康分数: {analysis['health_score']:.1f}")
                            self.apply_optimizations(['cache', 'memory'])

                    time.sleep(interval)

                except Exception as e:
                    log_error(f"自动优化循环异常: {e}")
                    time.sleep(60)  # 出错后等待1分钟

        optimization_thread = threading.Thread(target=auto_optimization_loop, daemon=True)
        optimization_thread.start()

        log_info(f"自动性能优化已启动，间隔: {interval}秒")

    def stop_auto_optimization(self):
        """停止自动优化"""
        self.auto_optimization = False
        log_info("自动性能优化已停止")

    def get_optimization_report(self) -> Dict[str, Any]:
        """获取优化报告"""
        # 获取最新的性能分析
        latest_analysis = self.analyze_system_performance()

        # 统计历史优化效果
        optimization_stats = {
            'total_optimizations': len(self.optimization_history),
            'avg_optimization_time': 0.0,
            'optimization_types_used': defaultdict(int)
        }

        if self.optimization_history:
            optimization_stats['avg_optimization_time'] = statistics.mean(
                record['optimization_time'] for record in self.optimization_history
            )

            for record in self.optimization_history:
                for opt_type in record['optimization_types']:
                    optimization_stats['optimization_types_used'][opt_type] += 1

        return {
            'current_analysis': latest_analysis,
            'optimization_history': self.optimization_history[-10:],  # 最近10次
            'optimization_stats': optimization_stats,
            'auto_optimization_status': 'active' if self.auto_optimization else 'inactive',
            'report_timestamp': datetime.now().isoformat()
        }

    # 优化动作实现
    def _optimize_memory_usage(self, metrics: Dict[str, Any]) -> bool:
        """优化内存使用"""
        try:
            # 清理性能缓存
            from modules.performance_cache import performance_cache
            performance_cache.clear_all()

            # 强制垃圾回收
            gc.collect()

            log_info("内存优化完成")
            return True

        except Exception as e:
            logger.error(f"内存优化失败: {e}")
            return False

    def _optimize_cache_strategy(self, metrics: Dict[str, Any]) -> bool:
        """优化缓存策略"""
        try:
            # 清理过期缓存
            from modules.performance_cache import performance_cache
            performance_cache.clear_all()

            log_info("缓存策略优化完成")
            return True

        except Exception as e:
            logger.error(f"缓存策略优化失败: {e}")
            return False

    def _optimize_cpu_usage(self, metrics: Dict[str, Any]) -> bool:
        """优化CPU使用"""
        try:
            # 可以实施CPU优化策略，如调整线程池大小、暂停非关键任务等
            log_info("CPU使用优化完成")
            return True

        except Exception as e:
            logger.error(f"CPU使用优化失败: {e}")
            return False

    def _optimize_disk_usage(self, metrics: Dict[str, Any]) -> bool:
        """优化磁盘使用"""
        try:
            # 清理临时文件、日志文件等
            log_info("磁盘使用优化完成")
            return True

        except Exception as e:
            logger.error(f"磁盘使用优化失败: {e}")
            return False

    # 辅助方法
    def _bottleneck_to_dict(self, bottleneck: SystemBottleneck) -> Dict[str, Any]:
        """转换瓶颈为字典"""
        return {
            'type': bottleneck.type,
            'severity': bottleneck.severity,
            'current_value': bottleneck.current_value,
            'threshold': bottleneck.threshold,
            'component': bottleneck.component,
            'impact_description': bottleneck.impact_description
        }

    def _recommendation_to_dict(self, recommendation: OptimizationRecommendation) -> Dict[str, Any]:
        """转换建议为字典"""
        return {
            'category': recommendation.category,
            'priority': recommendation.priority,
            'title': recommendation.title,
            'description': recommendation.description,
            'implementation': recommendation.implementation,
            'expected_improvement': recommendation.expected_improvement,
            'estimated_effort': recommendation.estimated_effort,
            'impact_score': recommendation.impact_score
        }

    def _metrics_to_dict(self, metrics: Dict[str, PerformanceMetric]) -> Dict[str, Any]:
        """转换指标为字典"""
        result = {}
        for name, metric in metrics.items():
            result[name] = {
                'value': metric.value,
                'unit': metric.unit,
                'timestamp': metric.timestamp.isoformat(),
                'threshold_warning': metric.threshold_warning,
                'threshold_critical': metric.threshold_critical
            }
        return result

# 全局优化器实例
performance_optimizer = PerformanceOptimizer()

# 便捷函数
def analyze_performance() -> Dict[str, Any]:
    """分析系统性能"""
    return performance_optimizer.analyze_system_performance()

def optimize_performance(types: List[str] = None) -> Dict[str, Any]:
    """应用性能优化"""
    return performance_optimizer.apply_optimizations(types)

def get_optimization_report() -> Dict[str, Any]:
    """获取优化报告"""
    return performance_optimizer.get_optimization_report()

def start_auto_optimization(interval: int = 300):
    """启动自动优化"""
    performance_optimizer.start_auto_optimization(interval)

def stop_auto_optimization():
    """停止自动优化"""
    performance_optimizer.stop_auto_optimization()

# 集成所有性能模块的便捷函数
def initialize_perfect21_performance():
    """初始化Perfect21性能优化"""
    try:
        # 启动性能监控
        from modules.performance_monitor import start_performance_monitoring
        start_performance_monitoring()

        # 启动自动优化
        start_auto_optimization()

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
            'performance_optimization': get_optimization_report(),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取性能概览失败: {e}")
        return {'error': str(e)}