#!/usr/bin/env python3
"""
Perfect21性能优化Feature
集成所有性能优化功能的统一接口
"""

import os
import sys
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from modules.enhanced_performance_optimizer import (
    enhanced_performance_optimizer,
    optimize_agent_execution,
    batch_git_operations,
    optimize_memory,
    start_performance_optimization,
    get_performance_report,
    run_benchmark,
    optimized_execution
)
from modules.logger import log_info, log_warning, log_error
from core.interfaces import FeatureBase

class PerformanceOptimizerFeature(FeatureBase):
    """性能优化器功能"""

    def __init__(self):
        super().__init__()
        self.name = "performance_optimizer"
        self.version = "2.0.0"
        self.description = "Perfect21智能性能优化系统"

        # 优化配置
        self.config = {
            'auto_optimization': True,
            'optimization_interval': 300,
            'memory_threshold': 80.0,
            'cache_hit_threshold': 70.0,
            'benchmark_enabled': True
        }

        log_info("性能优化器Feature初始化完成")

    async def initialize(self) -> bool:
        """初始化性能优化器"""
        try:
            # 启动性能监控
            from modules.performance_monitor import start_performance_monitoring
            start_performance_monitoring()

            # 建立性能基线
            await self._establish_baselines()

            # 启动自动优化（如果配置启用）
            if self.config['auto_optimization']:
                start_performance_optimization()

            log_info("性能优化器初始化成功")
            return True

        except Exception as e:
            log_error(f"性能优化器初始化失败: {e}")
            return False

    async def _establish_baselines(self) -> None:
        """建立性能基线"""
        log_info("建立性能基线...")

        # 运行基准测试建立基线
        benchmark_results = run_benchmark()

        for test_name in benchmark_results.get('results', {}):
            enhanced_performance_optimizer.benchmark_system.establish_baseline(test_name)

        log_info("性能基线建立完成")

    async def optimize_system(self, optimization_types: List[str] = None) -> Dict[str, Any]:
        """系统优化"""
        if optimization_types is None:
            optimization_types = ['memory', 'cache', 'git', 'benchmark']

        results = {}
        start_time = time.perf_counter()

        try:
            async with optimized_execution() as optimizer:

                if 'memory' in optimization_types:
                    log_info("执行内存优化...")
                    memory_result = await optimize_memory()
                    results['memory'] = memory_result

                if 'cache' in optimization_types:
                    log_info("执行缓存优化...")
                    await optimizer.cache_system._evict_cache()
                    cache_stats = optimizer.cache_system.get_cache_stats()
                    results['cache'] = cache_stats

                if 'git' in optimization_types:
                    log_info("执行Git优化...")
                    git_stats = optimizer.git_optimizer.get_optimization_stats()
                    results['git'] = git_stats

                if 'benchmark' in optimization_types and self.config['benchmark_enabled']:
                    log_info("运行基准测试...")
                    benchmark_result = run_benchmark()
                    results['benchmark'] = benchmark_result

        except Exception as e:
            log_error(f"系统优化失败: {e}")
            results['error'] = str(e)

        execution_time = time.perf_counter() - start_time
        results['optimization_time'] = execution_time
        results['timestamp'] = datetime.now().isoformat()

        log_info(f"系统优化完成，用时: {execution_time:.3f}s")
        return results

    async def analyze_performance(self) -> Dict[str, Any]:
        """性能分析"""
        log_info("执行性能分析...")

        # 获取全面性能报告
        report = get_performance_report()

        # 性能分析和建议
        analysis = {
            'overall_health': self._calculate_health_score(report),
            'bottlenecks': self._identify_bottlenecks(report),
            'recommendations': self._generate_recommendations(report),
            'trends': self._analyze_trends(report)
        }

        report['analysis'] = analysis

        log_info("性能分析完成")
        return report

    def _calculate_health_score(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """计算健康分数"""
        base_score = 100.0

        # 内存健康 (25%)
        memory_usage = report['memory_stats']['percent']
        if memory_usage > 90:
            base_score -= 25
        elif memory_usage > 80:
            base_score -= 15
        elif memory_usage > 70:
            base_score -= 5

        # 缓存健康 (25%)
        cache_hit_rate = float(report['cache_stats']['hit_rate'].rstrip('%'))
        if cache_hit_rate < 50:
            base_score -= 25
        elif cache_hit_rate < 70:
            base_score -= 15
        elif cache_hit_rate < 85:
            base_score -= 5

        # Git优化健康 (25%)
        git_optimization = float(report['git_optimization_stats']['optimization_ratio'].rstrip('%'))
        if git_optimization < 30:
            base_score -= 25
        elif git_optimization < 60:
            base_score -= 15
        elif git_optimization < 80:
            base_score -= 5

        # 性能回归检查 (25%)
        benchmark_summary = report.get('benchmark_summary', {})
        regression_count = 0
        for test_name, stats in benchmark_summary.items():
            if stats['baseline'] > 0:
                regression_ratio = (stats['latest'] - stats['baseline']) / stats['baseline']
                if regression_ratio > 0.2:  # 20%回归
                    regression_count += 1

        if regression_count > 2:
            base_score -= 25
        elif regression_count > 0:
            base_score -= 10

        health_score = max(0.0, min(100.0, base_score))

        if health_score >= 90:
            status = 'excellent'
        elif health_score >= 75:
            status = 'good'
        elif health_score >= 60:
            status = 'fair'
        else:
            status = 'poor'

        return {
            'score': health_score,
            'status': status,
            'memory_component': 25 - max(0, min(25, (memory_usage - 70) / 20 * 25)),
            'cache_component': 25 - max(0, min(25, (85 - cache_hit_rate) / 35 * 25)),
            'git_component': 25 - max(0, min(25, (80 - git_optimization) / 50 * 25)),
            'regression_component': 25 - (regression_count * 12.5)
        }

    def _identify_bottlenecks(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别性能瓶颈"""
        bottlenecks = []

        # 内存瓶颈
        memory_usage = report['memory_stats']['percent']
        if memory_usage > 85:
            bottlenecks.append({
                'type': 'memory',
                'severity': 'high' if memory_usage > 95 else 'medium',
                'value': memory_usage,
                'description': f'内存使用率 {memory_usage:.1f}% 过高',
                'impact': 'system_stability'
            })

        # 缓存瓶颈
        cache_hit_rate = float(report['cache_stats']['hit_rate'].rstrip('%'))
        if cache_hit_rate < 70:
            bottlenecks.append({
                'type': 'cache',
                'severity': 'high' if cache_hit_rate < 50 else 'medium',
                'value': cache_hit_rate,
                'description': f'缓存命中率 {cache_hit_rate:.1f}% 过低',
                'impact': 'response_time'
            })

        # Git操作瓶颈
        pending_ops = report['git_optimization_stats']['pending_operations']
        if pending_ops > 10:
            bottlenecks.append({
                'type': 'git_operations',
                'severity': 'medium',
                'value': pending_ops,
                'description': f'{pending_ops} 个Git操作待处理',
                'impact': 'git_performance'
            })

        # 性能回归瓶颈
        for test_name, stats in report.get('benchmark_summary', {}).items():
            if stats['baseline'] > 0:
                regression_ratio = (stats['latest'] - stats['baseline']) / stats['baseline']
                if regression_ratio > 0.3:  # 30%回归
                    bottlenecks.append({
                        'type': 'performance_regression',
                        'severity': 'high',
                        'value': regression_ratio,
                        'description': f'{test_name} 性能回归 {regression_ratio:.1%}',
                        'impact': 'overall_performance'
                    })

        return bottlenecks

    def _generate_recommendations(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成优化建议"""
        recommendations = []

        # 内存优化建议
        memory_usage = report['memory_stats']['percent']
        if memory_usage > 80:
            recommendations.append({
                'category': 'memory',
                'priority': 'high',
                'title': '内存使用优化',
                'description': f'当前内存使用率 {memory_usage:.1f}%，建议进行内存优化',
                'actions': [
                    '执行垃圾回收清理未使用对象',
                    '清理过期缓存释放内存',
                    '检查内存泄漏和循环引用',
                    '启用内存压缩和对象复用'
                ],
                'expected_improvement': '降低内存使用20-30%'
            })

        # 缓存优化建议
        cache_hit_rate = float(report['cache_stats']['hit_rate'].rstrip('%'))
        if cache_hit_rate < 75:
            recommendations.append({
                'category': 'cache',
                'priority': 'medium',
                'title': '缓存策略优化',
                'description': f'缓存命中率 {cache_hit_rate:.1f}% 有提升空间',
                'actions': [
                    '分析缓存访问模式优化缓存键',
                    '增加热点数据的缓存时间',
                    '启用智能预测缓存',
                    '调整缓存淘汰策略'
                ],
                'expected_improvement': '提升缓存命中率至85%以上'
            })

        # Git优化建议
        git_optimization = float(report['git_optimization_stats']['optimization_ratio'].rstrip('%'))
        if git_optimization < 70:
            recommendations.append({
                'category': 'git',
                'priority': 'medium',
                'title': 'Git操作批量化',
                'description': f'Git操作批量化率 {git_optimization:.1f}% 有提升空间',
                'actions': [
                    '启用Git操作批量处理',
                    '增加Git结果缓存时间',
                    '优化Git操作调用频率',
                    '合并相似的Git查询'
                ],
                'expected_improvement': '提升Git操作效率40-60%'
            })

        # 基准测试建议
        benchmark_summary = report.get('benchmark_summary', {})
        regression_tests = []
        for test_name, stats in benchmark_summary.items():
            if stats['baseline'] > 0:
                regression_ratio = (stats['latest'] - stats['baseline']) / stats['baseline']
                if regression_ratio > 0.2:
                    regression_tests.append(test_name)

        if regression_tests:
            recommendations.append({
                'category': 'performance',
                'priority': 'high',
                'title': '性能回归修复',
                'description': f'检测到 {len(regression_tests)} 个测试性能回归',
                'actions': [
                    f'分析回归测试: {", ".join(regression_tests)}',
                    '检查最近的代码变更影响',
                    '优化回归测试中的瓶颈',
                    '重新建立性能基线'
                ],
                'expected_improvement': '恢复原有性能水平'
            })

        return recommendations

    def _analyze_trends(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """分析性能趋势"""
        trends = {}

        # 内存使用趋势
        memory_metrics = report.get('performance_metrics', {}).get('memory_usage_mb', {})
        if memory_metrics.get('count', 0) > 10:
            latest = memory_metrics.get('latest', 0)
            average = memory_metrics.get('average', 0)
            if latest > average * 1.1:
                trends['memory'] = 'increasing'
            elif latest < average * 0.9:
                trends['memory'] = 'decreasing'
            else:
                trends['memory'] = 'stable'
        else:
            trends['memory'] = 'insufficient_data'

        # 响应时间趋势
        response_metrics = report.get('performance_metrics', {}).get('response_time_p95', {})
        if response_metrics.get('count', 0) > 10:
            latest = response_metrics.get('latest', 0)
            average = response_metrics.get('average', 0)
            if latest > average * 1.1:
                trends['response_time'] = 'degrading'
            elif latest < average * 0.9:
                trends['response_time'] = 'improving'
            else:
                trends['response_time'] = 'stable'
        else:
            trends['response_time'] = 'insufficient_data'

        # 缓存命中率趋势
        cache_metrics = report.get('performance_metrics', {}).get('cache_hit_rate', {})
        if cache_metrics.get('count', 0) > 10:
            latest = cache_metrics.get('latest', 0)
            average = cache_metrics.get('average', 0)
            if latest > average * 1.05:
                trends['cache_hit_rate'] = 'improving'
            elif latest < average * 0.95:
                trends['cache_hit_rate'] = 'degrading'
            else:
                trends['cache_hit_rate'] = 'stable'
        else:
            trends['cache_hit_rate'] = 'insufficient_data'

        return trends

    async def execute(self, command: str, args: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行性能优化命令"""
        args = args or {}

        if command == 'optimize':
            optimization_types = args.get('types', ['memory', 'cache', 'git'])
            return await self.optimize_system(optimization_types)

        elif command == 'analyze':
            return await self.analyze_performance()

        elif command == 'benchmark':
            return run_benchmark()

        elif command == 'report':
            return get_performance_report()

        elif command == 'start_auto':
            start_performance_optimization()
            return {'status': 'success', 'message': '自动优化已启动'}

        elif command == 'stop_auto':
            enhanced_performance_optimizer.stop_auto_optimization()
            return {'status': 'success', 'message': '自动优化已停止'}

        elif command == 'memory_optimize':
            return await optimize_memory()

        elif command == 'agent_optimize':
            agent_type = args.get('agent_type', 'default')
            params = args.get('params', {})
            return await optimize_agent_execution(agent_type, params)

        else:
            return {'status': 'error', 'message': f'未知命令: {command}'}

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            'name': self.name,
            'version': self.version,
            'auto_optimization': enhanced_performance_optimizer.auto_optimization,
            'config': self.config,
            'quick_stats': {
                'cache_stats': enhanced_performance_optimizer.cache_system.get_cache_stats(),
                'memory_rss_mb': enhanced_performance_optimizer.memory_optimizer.get_memory_stats()['rss_mb'],
                'resource_pools': len(enhanced_performance_optimizer.resource_manager.pools),
                'optimization_history': len(enhanced_performance_optimizer.optimization_history)
            }
        }

# 创建Feature实例
performance_optimizer_feature = PerformanceOptimizerFeature()

# 便捷函数
async def optimize_perfect21_performance(types: List[str] = None) -> Dict[str, Any]:
    """便捷函数：优化Perfect21性能"""
    return await performance_optimizer_feature.optimize_system(types)

async def analyze_perfect21_performance() -> Dict[str, Any]:
    """便捷函数：分析Perfect21性能"""
    return await performance_optimizer_feature.analyze_performance()

def get_perfect21_performance_status() -> Dict[str, Any]:
    """便捷函数：获取性能状态"""
    return performance_optimizer_feature.get_status()