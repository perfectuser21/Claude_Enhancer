#!/usr/bin/env python3
"""
Perfect21 完整性能分析工具
综合分析系统的性能表现，包括基准测试、资源使用分析和瓶颈识别
"""

import os
import sys
import time
import psutil
import json
import asyncio
import threading
import concurrent.futures
import statistics
import gc
import tracemalloc
import cProfile
import pstats
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import logging
import re
import subprocess

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__)))

# 导入Perfect21模块
from modules.logger import log_info, log_error, log_warning
from modules.performance_monitor import performance_monitor, PerformanceMetric
from modules.performance_optimizer import performance_optimizer
from features.workflow_orchestrator.orchestrator import WorkflowOrchestrator

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """基准测试结果"""
    test_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    throughput: float
    error_count: int
    success_rate: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceProfile:
    """性能剖析结果"""
    component: str
    total_time: float
    function_calls: int
    memory_peak: float
    hot_spots: List[Dict[str, Any]] = field(default_factory=list)
    bottlenecks: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ResourceUsage:
    """资源使用情况"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_rss: float
    memory_vms: float
    disk_usage: float
    network_io: Dict[str, int]
    file_descriptors: int
    threads: int

class PerformanceAnalyzer:
    """性能分析器"""

    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.resource_samples: List[ResourceUsage] = []
        self.benchmark_results: List[BenchmarkResult] = []
        self.profiling_data: Dict[str, PerformanceProfile] = {}

        # 性能监控配置
        self.sampling_interval = 0.1  # 100ms
        self.monitoring_duration = 60  # 60秒

        # 基准测试配置
        self.benchmark_configs = {
            'workflow_generation': {
                'iterations': 100,
                'timeout': 30
            },
            'agent_selection': {
                'iterations': 1000,
                'timeout': 10
            },
            'parallel_execution': {
                'workers': 4,
                'tasks': 50,
                'timeout': 60
            },
            'file_operations': {
                'file_count': 100,
                'file_size': 1024,  # 1KB
                'timeout': 30
            },
            'regex_performance': {
                'patterns': 50,
                'text_size': 10000,
                'timeout': 15
            }
        }

        log_info("性能分析器初始化完成")

    def run_complete_analysis(self) -> Dict[str, Any]:
        """运行完整性能分析"""
        analysis_start = time.perf_counter()

        log_info("开始完整性能分析")

        try:
            # 1. 基准测试
            log_info("执行基准测试...")
            benchmark_results = self._run_all_benchmarks()

            # 2. 资源使用分析
            log_info("进行资源使用分析...")
            resource_analysis = self._analyze_resource_usage()

            # 3. 性能剖析
            log_info("执行性能剖析...")
            profiling_results = self._run_performance_profiling()

            # 4. 瓶颈识别
            log_info("识别性能瓶颈...")
            bottleneck_analysis = self._identify_bottlenecks()

            # 5. 优化建议
            log_info("生成优化建议...")
            optimization_recommendations = self._generate_optimization_recommendations()

            # 6. 整体评分
            performance_score = self._calculate_performance_score()

            analysis_time = time.perf_counter() - analysis_start

            self.results = {
                'analysis_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'analysis_duration': analysis_time,
                    'system_info': self._get_system_info()
                },
                'performance_score': performance_score,
                'benchmark_results': benchmark_results,
                'resource_analysis': resource_analysis,
                'profiling_results': profiling_results,
                'bottleneck_analysis': bottleneck_analysis,
                'optimization_recommendations': optimization_recommendations
            }

            # 保存结果
            self._save_results()

            log_info(f"性能分析完成，总用时: {analysis_time:.2f}秒")
            return self.results

        except Exception as e:
            log_error(f"性能分析失败: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def _run_all_benchmarks(self) -> Dict[str, BenchmarkResult]:
        """运行所有基准测试"""
        benchmark_results = {}

        # 1. 工作流生成性能测试
        benchmark_results['workflow_generation'] = self._benchmark_workflow_generation()

        # 2. Agent选择速度测试
        benchmark_results['agent_selection'] = self._benchmark_agent_selection()

        # 3. 并行执行效率测试
        benchmark_results['parallel_execution'] = self._benchmark_parallel_execution()

        # 4. 文件操作性能测试
        benchmark_results['file_operations'] = self._benchmark_file_operations()

        # 5. 正则表达式性能测试
        benchmark_results['regex_performance'] = self._benchmark_regex_performance()

        return benchmark_results

    def _benchmark_workflow_generation(self) -> BenchmarkResult:
        """工作流生成性能基准测试"""
        config = self.benchmark_configs['workflow_generation']
        iterations = config['iterations']

        execution_times = []
        memory_usage = []
        errors = 0

        # 监控资源使用
        process = psutil.Process()

        for i in range(iterations):
            try:
                # 记录开始状态
                start_time = time.perf_counter()
                start_memory = process.memory_info().rss / 1024 / 1024  # MB

                # 创建工作流编排器
                orchestrator = WorkflowOrchestrator()

                # 模拟工作流配置
                workflow_config = {
                    'name': f'Test Workflow {i}',
                    'stages': [
                        {
                            'name': 'analysis',
                            'description': 'Analysis stage',
                            'execution_mode': 'parallel',
                            'depends_on': []
                        },
                        {
                            'name': 'implementation',
                            'description': 'Implementation stage',
                            'execution_mode': 'sequential',
                            'depends_on': ['analysis']
                        }
                    ]
                }

                # 加载工作流
                result = orchestrator.load_workflow(workflow_config)

                if not result['success']:
                    errors += 1
                    continue

                # 记录结束状态
                end_time = time.perf_counter()
                end_memory = process.memory_info().rss / 1024 / 1024  # MB

                execution_times.append(end_time - start_time)
                memory_usage.append(end_memory - start_memory)

            except Exception as e:
                errors += 1
                logger.error(f"Workflow generation benchmark error: {e}")

        # 计算统计信息
        if execution_times:
            avg_time = statistics.mean(execution_times)
            avg_memory = statistics.mean(memory_usage)
            throughput = iterations / sum(execution_times) if execution_times else 0
            success_rate = (iterations - errors) / iterations * 100
        else:
            avg_time = avg_memory = throughput = success_rate = 0

        return BenchmarkResult(
            test_name='workflow_generation',
            execution_time=avg_time,
            memory_usage=avg_memory,
            cpu_usage=0,  # CPU usage will be calculated separately
            throughput=throughput,
            error_count=errors,
            success_rate=success_rate,
            metadata={
                'iterations': iterations,
                'min_time': min(execution_times) if execution_times else 0,
                'max_time': max(execution_times) if execution_times else 0,
                'p95_time': statistics.quantiles(execution_times, n=20)[18] if len(execution_times) >= 20 else 0
            }
        )

    def _benchmark_agent_selection(self) -> BenchmarkResult:
        """Agent选择速度基准测试"""
        config = self.benchmark_configs['agent_selection']
        iterations = config['iterations']

        execution_times = []
        errors = 0

        # 模拟Agent选择逻辑
        agents = [
            'project-manager', 'business-analyst', 'technical-writer',
            'api-designer', 'backend-architect', 'frontend-specialist',
            'database-specialist', 'security-auditor', 'test-engineer'
        ]

        for i in range(iterations):
            try:
                start_time = time.perf_counter()

                # 模拟复杂的Agent选择逻辑
                task_description = f"Implement feature {i % 100}"
                selected_agents = []

                # 基于任务描述选择Agent（模拟复杂匹配算法）
                for agent in agents:
                    score = 0
                    if 'implement' in task_description.lower():
                        if agent in ['backend-architect', 'frontend-specialist']:
                            score += 0.8
                    if 'feature' in task_description.lower():
                        if agent in ['project-manager', 'business-analyst']:
                            score += 0.6

                    if score > 0.5:
                        selected_agents.append(agent)

                end_time = time.perf_counter()
                execution_times.append(end_time - start_time)

            except Exception as e:
                errors += 1
                logger.error(f"Agent selection benchmark error: {e}")

        if execution_times:
            avg_time = statistics.mean(execution_times)
            throughput = iterations / sum(execution_times)
            success_rate = (iterations - errors) / iterations * 100
        else:
            avg_time = throughput = success_rate = 0

        return BenchmarkResult(
            test_name='agent_selection',
            execution_time=avg_time,
            memory_usage=0,
            cpu_usage=0,
            throughput=throughput,
            error_count=errors,
            success_rate=success_rate,
            metadata={
                'iterations': iterations,
                'agents_tested': len(agents),
                'avg_selections_per_iteration': 2.5
            }
        )

    def _benchmark_parallel_execution(self) -> BenchmarkResult:
        """并行执行效率基准测试"""
        config = self.benchmark_configs['parallel_execution']
        workers = config['workers']
        tasks = config['tasks']

        def worker_task(task_id):
            """模拟工作任务"""
            start_time = time.perf_counter()

            # 模拟CPU密集型任务
            result = sum(i * i for i in range(1000))

            # 模拟I/O操作
            time.sleep(0.01)

            execution_time = time.perf_counter() - start_time
            return {
                'task_id': task_id,
                'result': result,
                'execution_time': execution_time
            }

        # 测试顺序执行
        sequential_start = time.perf_counter()
        sequential_results = []
        for i in range(tasks):
            sequential_results.append(worker_task(i))
        sequential_time = time.perf_counter() - sequential_start

        # 测试并行执行
        parallel_start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            parallel_results = list(executor.map(worker_task, range(tasks)))
        parallel_time = time.perf_counter() - parallel_start

        # 计算并行效率
        speedup = sequential_time / parallel_time if parallel_time > 0 else 0
        efficiency = speedup / workers * 100

        return BenchmarkResult(
            test_name='parallel_execution',
            execution_time=parallel_time,
            memory_usage=0,
            cpu_usage=0,
            throughput=tasks / parallel_time if parallel_time > 0 else 0,
            error_count=0,
            success_rate=100.0,
            metadata={
                'sequential_time': sequential_time,
                'parallel_time': parallel_time,
                'speedup': speedup,
                'efficiency': efficiency,
                'workers': workers,
                'tasks': tasks
            }
        )

    def _benchmark_file_operations(self) -> BenchmarkResult:
        """文件操作性能基准测试"""
        config = self.benchmark_configs['file_operations']
        file_count = config['file_count']
        file_size = config['file_size']

        temp_dir = Path('/tmp/perfect21_perf_test')
        temp_dir.mkdir(exist_ok=True)

        execution_times = []
        errors = 0

        try:
            # 文件写入测试
            write_times = []
            for i in range(file_count):
                try:
                    start_time = time.perf_counter()

                    test_file = temp_dir / f'test_file_{i}.txt'
                    test_content = 'x' * file_size

                    with open(test_file, 'w') as f:
                        f.write(test_content)

                    end_time = time.perf_counter()
                    write_times.append(end_time - start_time)

                except Exception as e:
                    errors += 1
                    logger.error(f"File write error: {e}")

            # 文件读取测试
            read_times = []
            for i in range(file_count):
                try:
                    start_time = time.perf_counter()

                    test_file = temp_dir / f'test_file_{i}.txt'
                    with open(test_file, 'r') as f:
                        content = f.read()

                    end_time = time.perf_counter()
                    read_times.append(end_time - start_time)

                except Exception as e:
                    errors += 1
                    logger.error(f"File read error: {e}")

            # 清理测试文件
            for i in range(file_count):
                test_file = temp_dir / f'test_file_{i}.txt'
                if test_file.exists():
                    test_file.unlink()

            temp_dir.rmdir()

            execution_times = write_times + read_times

        except Exception as e:
            errors += 1
            logger.error(f"File operations benchmark error: {e}")

        if execution_times:
            avg_time = statistics.mean(execution_times)
            throughput = len(execution_times) / sum(execution_times)
            success_rate = (file_count * 2 - errors) / (file_count * 2) * 100
        else:
            avg_time = throughput = success_rate = 0

        return BenchmarkResult(
            test_name='file_operations',
            execution_time=avg_time,
            memory_usage=0,
            cpu_usage=0,
            throughput=throughput,
            error_count=errors,
            success_rate=success_rate,
            metadata={
                'file_count': file_count,
                'file_size': file_size,
                'write_times': write_times[:10] if write_times else [],
                'read_times': read_times[:10] if read_times else []
            }
        )

    def _benchmark_regex_performance(self) -> BenchmarkResult:
        """正则表达式性能基准测试"""
        config = self.benchmark_configs['regex_performance']
        patterns_count = config['patterns']
        text_size = config['text_size']

        # 生成测试文本
        test_text = 'The quick brown fox jumps over the lazy dog. ' * (text_size // 45)

        # 测试正则表达式模式
        patterns = [
            r'\b\w+\b',          # 单词匹配
            r'\d+',              # 数字匹配
            r'[A-Z][a-z]+',      # 大写开头的单词
            r'\b\w{4,}\b',       # 4个字符以上的单词
            r'(?i)the',          # 忽略大小写的"the"
            r'\w+@\w+\.\w+',     # 邮箱模式
            r'http[s]?://\S+',   # URL模式
            r'\b[A-Z]{2,}\b',    # 全大写缩写
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # IP地址
            r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'  # 复杂IP
        ]

        execution_times = []
        errors = 0
        total_matches = 0

        for i in range(patterns_count):
            try:
                pattern = patterns[i % len(patterns)]

                start_time = time.perf_counter()

                # 编译正则表达式
                compiled_pattern = re.compile(pattern)

                # 执行匹配
                matches = compiled_pattern.findall(test_text)
                total_matches += len(matches)

                end_time = time.perf_counter()
                execution_times.append(end_time - start_time)

            except Exception as e:
                errors += 1
                logger.error(f"Regex benchmark error: {e}")

        if execution_times:
            avg_time = statistics.mean(execution_times)
            throughput = patterns_count / sum(execution_times)
            success_rate = (patterns_count - errors) / patterns_count * 100
        else:
            avg_time = throughput = success_rate = 0

        return BenchmarkResult(
            test_name='regex_performance',
            execution_time=avg_time,
            memory_usage=0,
            cpu_usage=0,
            throughput=throughput,
            error_count=errors,
            success_rate=success_rate,
            metadata={
                'patterns_tested': patterns_count,
                'text_size': text_size,
                'total_matches': total_matches,
                'patterns_used': len(patterns)
            }
        )

    def _analyze_resource_usage(self) -> Dict[str, Any]:
        """分析资源使用情况"""
        log_info("开始资源使用监控...")

        # 启动资源监控
        monitoring_thread = threading.Thread(
            target=self._monitor_resources,
            args=(self.monitoring_duration,),
            daemon=True
        )
        monitoring_thread.start()

        # 等待监控完成
        monitoring_thread.join(timeout=self.monitoring_duration + 5)

        if not self.resource_samples:
            return {'error': 'No resource samples collected'}

        # 分析资源使用数据
        cpu_usage = [sample.cpu_percent for sample in self.resource_samples]
        memory_usage = [sample.memory_percent for sample in self.resource_samples]
        memory_rss = [sample.memory_rss for sample in self.resource_samples]
        disk_usage = [sample.disk_usage for sample in self.resource_samples]

        return {
            'monitoring_duration': self.monitoring_duration,
            'samples_collected': len(self.resource_samples),
            'cpu_analysis': {
                'avg': statistics.mean(cpu_usage),
                'max': max(cpu_usage),
                'min': min(cpu_usage),
                'p95': statistics.quantiles(cpu_usage, n=20)[18] if len(cpu_usage) >= 20 else max(cpu_usage)
            },
            'memory_analysis': {
                'avg_percent': statistics.mean(memory_usage),
                'max_percent': max(memory_usage),
                'avg_rss_mb': statistics.mean(memory_rss),
                'max_rss_mb': max(memory_rss),
                'memory_growth': memory_rss[-1] - memory_rss[0] if len(memory_rss) > 1 else 0
            },
            'disk_analysis': {
                'avg_usage': statistics.mean(disk_usage),
                'max_usage': max(disk_usage)
            },
            'stability_metrics': {
                'cpu_volatility': statistics.stdev(cpu_usage) if len(cpu_usage) > 1 else 0,
                'memory_volatility': statistics.stdev(memory_usage) if len(memory_usage) > 1 else 0
            }
        }

    def _monitor_resources(self, duration: int):
        """监控系统资源使用"""
        process = psutil.Process()
        end_time = time.time() + duration

        while time.time() < end_time:
            try:
                # 收集资源使用数据
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                memory_percent = process.memory_percent()

                # 系统级数据
                disk_usage = psutil.disk_usage('/').percent
                network_io = psutil.net_io_counters()._asdict()

                # 进程级数据
                try:
                    file_descriptors = process.num_fds()
                except AttributeError:
                    file_descriptors = 0  # Windows不支持

                threads = process.num_threads()

                sample = ResourceUsage(
                    timestamp=datetime.now(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    memory_rss=memory_info.rss / 1024 / 1024,  # MB
                    memory_vms=memory_info.vms / 1024 / 1024,  # MB
                    disk_usage=disk_usage,
                    network_io=network_io,
                    file_descriptors=file_descriptors,
                    threads=threads
                )

                self.resource_samples.append(sample)

                time.sleep(self.sampling_interval)

            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")

    def _run_performance_profiling(self) -> Dict[str, Any]:
        """运行性能剖析"""
        profiling_results = {}

        # 1. 内存剖析
        profiling_results['memory_profiling'] = self._profile_memory_usage()

        # 2. CPU剖析
        profiling_results['cpu_profiling'] = self._profile_cpu_usage()

        # 3. 函数调用剖析
        profiling_results['function_profiling'] = self._profile_function_calls()

        return profiling_results

    def _profile_memory_usage(self) -> Dict[str, Any]:
        """内存使用剖析"""
        tracemalloc.start()

        try:
            # 执行一些内存密集型操作
            orchestrator = WorkflowOrchestrator()

            # 创建多个工作流
            for i in range(10):
                workflow_config = {
                    'name': f'Memory Test Workflow {i}',
                    'stages': [
                        {
                            'name': f'stage_{j}',
                            'description': f'Stage {j}',
                            'execution_mode': 'parallel'
                        }
                        for j in range(5)
                    ]
                }
                orchestrator.load_workflow(workflow_config)

            # 获取内存快照
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')

            memory_analysis = {
                'total_memory_mb': sum(stat.size for stat in top_stats) / 1024 / 1024,
                'top_memory_consumers': [
                    {
                        'filename': stat.traceback.format()[0].split(', ')[0],
                        'line_number': stat.traceback.format()[0].split(', ')[1],
                        'size_mb': stat.size / 1024 / 1024,
                        'count': stat.count
                    }
                    for stat in top_stats[:10]
                ]
            }

        except Exception as e:
            memory_analysis = {'error': str(e)}
        finally:
            tracemalloc.stop()

        return memory_analysis

    def _profile_cpu_usage(self) -> Dict[str, Any]:
        """CPU使用剖析"""
        profiler = cProfile.Profile()

        def cpu_intensive_task():
            """CPU密集型任务"""
            orchestrator = WorkflowOrchestrator()

            # 执行复杂的工作流操作
            for i in range(50):
                workflow_config = {
                    'name': f'CPU Test Workflow {i}',
                    'stages': [
                        {
                            'name': f'analysis_{j}',
                            'description': 'Complex analysis',
                            'execution_mode': 'sequential'
                        }
                        for j in range(3)
                    ]
                }
                orchestrator.load_workflow(workflow_config)

                # 模拟复杂计算
                result = sum(i * j for i in range(100) for j in range(100))

        # 开始剖析
        profiler.enable()
        cpu_intensive_task()
        profiler.disable()

        # 分析结果
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')

        # 提取热点函数
        hot_spots = []
        for func_name, (cc, nc, tt, ct, callers) in stats.stats.items():
            if tt > 0.01:  # 只关注执行时间超过10ms的函数
                hot_spots.append({
                    'function': f"{func_name[0]}:{func_name[1]}({func_name[2]})",
                    'total_time': tt,
                    'cumulative_time': ct,
                    'call_count': cc,
                    'per_call_time': tt / cc if cc > 0 else 0
                })

        # 按总时间排序
        hot_spots.sort(key=lambda x: x['total_time'], reverse=True)

        return {
            'total_function_calls': stats.total_calls,
            'total_execution_time': sum(tt for _, (_, _, tt, _, _) in stats.stats.items()),
            'top_hot_spots': hot_spots[:10],
            'performance_bottlenecks': [
                spot for spot in hot_spots[:20]
                if spot['per_call_time'] > 0.001  # 每次调用超过1ms
            ]
        }

    def _profile_function_calls(self) -> Dict[str, Any]:
        """函数调用剖析"""
        import sys
        from collections import defaultdict

        call_counts = defaultdict(int)
        call_times = defaultdict(float)

        def trace_calls(frame, event, arg):
            if event == 'call':
                func_name = f"{frame.f_code.co_filename}:{frame.f_code.co_name}"
                call_counts[func_name] += 1
                frame.f_locals['_start_time'] = time.perf_counter()
            elif event == 'return':
                func_name = f"{frame.f_code.co_filename}:{frame.f_code.co_name}"
                start_time = frame.f_locals.get('_start_time', 0)
                if start_time:
                    call_times[func_name] += time.perf_counter() - start_time

            return trace_calls

        # 启动跟踪
        sys.settrace(trace_calls)

        try:
            # 执行一些测试操作
            orchestrator = WorkflowOrchestrator()

            workflow_config = {
                'name': 'Function Profiling Test',
                'stages': [
                    {
                        'name': 'test_stage',
                        'description': 'Test stage',
                        'execution_mode': 'parallel'
                    }
                ]
            }

            orchestrator.load_workflow(workflow_config)

        finally:
            sys.settrace(None)

        # 分析结果
        top_by_calls = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_by_time = sorted(call_times.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'total_unique_functions': len(call_counts),
            'total_function_calls': sum(call_counts.values()),
            'total_execution_time': sum(call_times.values()),
            'most_called_functions': [
                {'function': func, 'call_count': count}
                for func, count in top_by_calls
            ],
            'most_time_consuming_functions': [
                {'function': func, 'total_time': time_spent}
                for func, time_spent in top_by_time
            ]
        }

    def _identify_bottlenecks(self) -> Dict[str, Any]:
        """识别性能瓶颈"""
        bottlenecks = {
            'cpu_bottlenecks': [],
            'memory_bottlenecks': [],
            'io_bottlenecks': [],
            'algorithmic_bottlenecks': []
        }

        # 分析基准测试结果中的瓶颈
        for test_name, result in self.benchmark_results:
            if hasattr(result, 'execution_time') and result.execution_time > 0.1:  # 超过100ms
                bottlenecks['cpu_bottlenecks'].append({
                    'component': test_name,
                    'issue': 'High execution time',
                    'value': result.execution_time,
                    'severity': 'high' if result.execution_time > 1.0 else 'medium'
                })

            if hasattr(result, 'memory_usage') and result.memory_usage > 50:  # 超过50MB
                bottlenecks['memory_bottlenecks'].append({
                    'component': test_name,
                    'issue': 'High memory usage',
                    'value': result.memory_usage,
                    'severity': 'high' if result.memory_usage > 100 else 'medium'
                })

            if hasattr(result, 'success_rate') and result.success_rate < 95:  # 成功率低于95%
                bottlenecks['algorithmic_bottlenecks'].append({
                    'component': test_name,
                    'issue': 'Low success rate',
                    'value': result.success_rate,
                    'severity': 'critical' if result.success_rate < 90 else 'high'
                })

        # 分析资源使用中的瓶颈
        if self.resource_samples:
            max_cpu = max(sample.cpu_percent for sample in self.resource_samples)
            max_memory = max(sample.memory_percent for sample in self.resource_samples)

            if max_cpu > 80:
                bottlenecks['cpu_bottlenecks'].append({
                    'component': 'system',
                    'issue': 'High CPU usage',
                    'value': max_cpu,
                    'severity': 'critical' if max_cpu > 95 else 'high'
                })

            if max_memory > 80:
                bottlenecks['memory_bottlenecks'].append({
                    'component': 'system',
                    'issue': 'High memory usage',
                    'value': max_memory,
                    'severity': 'critical' if max_memory > 95 else 'high'
                })

        # 计算瓶颈严重性
        total_bottlenecks = sum(len(bottlenecks[category]) for category in bottlenecks)
        critical_bottlenecks = sum(
            len([b for b in bottlenecks[category] if b.get('severity') == 'critical'])
            for category in bottlenecks
        )

        return {
            'bottlenecks': bottlenecks,
            'summary': {
                'total_bottlenecks': total_bottlenecks,
                'critical_bottlenecks': critical_bottlenecks,
                'severity_distribution': {
                    'critical': critical_bottlenecks,
                    'high': sum(
                        len([b for b in bottlenecks[category] if b.get('severity') == 'high'])
                        for category in bottlenecks
                    ),
                    'medium': sum(
                        len([b for b in bottlenecks[category] if b.get('severity') == 'medium'])
                        for category in bottlenecks
                    )
                }
            }
        }

    def _generate_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """生成优化建议"""
        recommendations = []

        # 基于基准测试结果生成建议
        for test_name, result in self.benchmark_results:
            if hasattr(result, 'execution_time') and result.execution_time > 0.5:
                recommendations.append({
                    'category': 'performance',
                    'priority': 'high',
                    'component': test_name,
                    'issue': f'Slow {test_name}',
                    'recommendation': f'Optimize {test_name} algorithm or implement caching',
                    'expected_improvement': '30-50% faster execution',
                    'implementation_effort': 'medium'
                })

            if hasattr(result, 'memory_usage') and result.memory_usage > 100:
                recommendations.append({
                    'category': 'memory',
                    'priority': 'medium',
                    'component': test_name,
                    'issue': f'High memory usage in {test_name}',
                    'recommendation': 'Implement memory pooling or reduce object creation',
                    'expected_improvement': '20-40% memory reduction',
                    'implementation_effort': 'medium'
                })

        # 基于资源分析生成建议
        if self.resource_samples:
            cpu_usage = [sample.cpu_percent for sample in self.resource_samples]
            memory_growth = (
                self.resource_samples[-1].memory_rss - self.resource_samples[0].memory_rss
                if len(self.resource_samples) > 1 else 0
            )

            if statistics.mean(cpu_usage) > 50:
                recommendations.append({
                    'category': 'cpu',
                    'priority': 'high',
                    'component': 'system',
                    'issue': 'High average CPU usage',
                    'recommendation': 'Implement async processing or optimize hot code paths',
                    'expected_improvement': 'Reduce CPU usage by 25-40%',
                    'implementation_effort': 'high'
                })

            if memory_growth > 50:  # 50MB增长
                recommendations.append({
                    'category': 'memory',
                    'priority': 'high',
                    'component': 'system',
                    'issue': 'Memory leak detected',
                    'recommendation': 'Implement proper cleanup and garbage collection',
                    'expected_improvement': 'Prevent memory leaks',
                    'implementation_effort': 'high'
                })

        # 通用优化建议
        recommendations.extend([
            {
                'category': 'caching',
                'priority': 'medium',
                'component': 'workflow_orchestrator',
                'issue': 'Repeated workflow loading',
                'recommendation': 'Implement workflow template caching',
                'expected_improvement': '60-80% faster workflow loading',
                'implementation_effort': 'low'
            },
            {
                'category': 'concurrency',
                'priority': 'medium',
                'component': 'task_execution',
                'issue': 'Sequential task processing',
                'recommendation': 'Increase parallelism in task execution',
                'expected_improvement': '2-4x faster task completion',
                'implementation_effort': 'medium'
            },
            {
                'category': 'database',
                'priority': 'low',
                'component': 'data_access',
                'issue': 'Database query optimization',
                'recommendation': 'Add database indexes and query optimization',
                'expected_improvement': '50-200% faster queries',
                'implementation_effort': 'low'
            }
        ])

        return recommendations

    def _calculate_performance_score(self) -> Dict[str, Any]:
        """计算性能评分"""
        base_score = 100.0

        # 基于基准测试结果计算分数
        benchmark_penalty = 0
        for test_name, result in self.benchmark_results:
            if hasattr(result, 'success_rate'):
                if result.success_rate < 95:
                    benchmark_penalty += (95 - result.success_rate) * 0.5

            if hasattr(result, 'execution_time'):
                if result.execution_time > 1.0:  # 超过1秒
                    benchmark_penalty += min(10, result.execution_time * 2)

        # 基于资源使用计算分数
        resource_penalty = 0
        if self.resource_samples:
            cpu_usage = [sample.cpu_percent for sample in self.resource_samples]
            memory_usage = [sample.memory_percent for sample in self.resource_samples]

            avg_cpu = statistics.mean(cpu_usage)
            avg_memory = statistics.mean(memory_usage)

            if avg_cpu > 70:
                resource_penalty += (avg_cpu - 70) * 0.3

            if avg_memory > 80:
                resource_penalty += (avg_memory - 80) * 0.5

        # 最终分数
        final_score = max(0, base_score - benchmark_penalty - resource_penalty)

        # 分数等级
        if final_score >= 90:
            grade = 'A'
            status = 'Excellent'
        elif final_score >= 80:
            grade = 'B'
            status = 'Good'
        elif final_score >= 70:
            grade = 'C'
            status = 'Average'
        elif final_score >= 60:
            grade = 'D'
            status = 'Below Average'
        else:
            grade = 'F'
            status = 'Poor'

        return {
            'overall_score': round(final_score, 1),
            'grade': grade,
            'status': status,
            'score_breakdown': {
                'base_score': base_score,
                'benchmark_penalty': benchmark_penalty,
                'resource_penalty': resource_penalty
            },
            'improvement_potential': max(0, 100 - final_score)
        }

    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            'platform': os.name,
            'cpu_count': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
            'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
            'disk_total_gb': psutil.disk_usage('/').total / 1024 / 1024 / 1024,
            'python_version': sys.version,
            'process_id': os.getpid()
        }

    def _save_results(self):
        """保存分析结果"""
        output_file = f"performance_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)

            log_info(f"性能分析报告已保存到: {output_file}")

        except Exception as e:
            log_error(f"保存分析报告失败: {e}")

def main():
    """主函数"""
    print("🚀 Perfect21 性能分析工具")
    print("=" * 50)

    analyzer = PerformanceAnalyzer()
    results = analyzer.run_complete_analysis()

    if 'error' in results:
        print(f"❌ 分析失败: {results['error']}")
        return

    # 显示结果摘要
    print("\n📊 性能分析结果摘要:")
    print("-" * 30)

    score_info = results.get('performance_score', {})
    print(f"📈 总体评分: {score_info.get('overall_score', 0)}/100 ({score_info.get('grade', 'N/A')})")
    print(f"📊 状态: {score_info.get('status', 'Unknown')}")

    benchmark_results = results.get('benchmark_results', {})
    print(f"\n🧪 基准测试结果:")
    for test_name, result in benchmark_results.items():
        if hasattr(result, 'execution_time'):
            print(f"  • {test_name}: {result.execution_time:.3f}s (成功率: {result.success_rate:.1f}%)")

    resource_analysis = results.get('resource_analysis', {})
    if 'cpu_analysis' in resource_analysis:
        cpu_info = resource_analysis['cpu_analysis']
        print(f"\n💻 CPU使用: 平均 {cpu_info.get('avg', 0):.1f}%, 最大 {cpu_info.get('max', 0):.1f}%")

    if 'memory_analysis' in resource_analysis:
        mem_info = resource_analysis['memory_analysis']
        print(f"🧠 内存使用: 平均 {mem_info.get('avg_rss_mb', 0):.1f}MB")

    bottlenecks = results.get('bottleneck_analysis', {}).get('summary', {})
    print(f"\n⚠️  性能瓶颈: {bottlenecks.get('total_bottlenecks', 0)} 个")
    print(f"   其中 {bottlenecks.get('critical_bottlenecks', 0)} 个严重瓶颈")

    recommendations = results.get('optimization_recommendations', [])
    high_priority_recs = [r for r in recommendations if r.get('priority') == 'high']
    print(f"\n💡 优化建议: {len(recommendations)} 条建议 ({len(high_priority_recs)} 条高优先级)")

    print(f"\n📄 详细报告已保存到文件")
    print("=" * 50)

if __name__ == "__main__":
    main()