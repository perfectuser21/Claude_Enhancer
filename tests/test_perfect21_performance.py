#!/usr/bin/env python3
"""
Perfect21 性能测试分析器
深入分析系统的各个性能维度
"""

import os
import sys
import time
import psutil
import json
import asyncio
import threading
import tracemalloc
import gc
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import subprocess
import concurrent.futures
import resource

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Performance measurement utilities
@dataclass
class PerformanceMetrics:
    """性能指标数据结构"""
    timestamp: str
    startup_time: float
    memory_usage: Dict[str, float]
    cpu_usage: float
    io_operations: Dict[str, int]
    execution_times: Dict[str, float]
    parallel_efficiency: Dict[str, Any]
    database_metrics: Dict[str, Any]
    bottlenecks: List[str]
    recommendations: List[str]

class PerformanceProfiler:
    """性能分析器"""

    def __init__(self):
        self.start_time = time.time()
        self.measurements = []
        self.process = psutil.Process()
        self.baseline_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        # 启用内存跟踪
        tracemalloc.start()

        # 性能阈值配置
        self.thresholds = {
            'startup_time': 3.0,  # 秒
            'memory_growth': 100,  # MB
            'cpu_usage': 80,  # %
            'response_time': 1.0,  # 秒
            'parallel_efficiency': 0.7  # 70%
        }

    def measure_startup_performance(self) -> Dict[str, Any]:
        """测量启动性能"""
        print("🚀 测量Perfect21启动性能...")

        startup_metrics = {}

        # 测量核心模块加载时间
        module_load_times = {}

        modules_to_test = [
            'main.perfect21',
            'main.cli',
            'features.capability_discovery',
            'features.git_workflow',
            'features.workflow_orchestrator',
            'features.sync_point_manager',
            'features.parallel_executor'
        ]

        for module in modules_to_test:
            start = time.time()
            try:
                __import__(module)
                load_time = time.time() - start
                module_load_times[module] = load_time
                print(f"  ✅ {module}: {load_time:.3f}s")
            except ImportError as e:
                module_load_times[module] = -1
                print(f"  ❌ {module}: 导入失败 - {e}")

        # 测量Perfect21实例化时间
        start = time.time()
        try:
            from main.perfect21 import Perfect21
            p21 = Perfect21()
            instance_time = time.time() - start
            startup_metrics['instance_creation'] = instance_time
            print(f"  ✅ Perfect21实例化: {instance_time:.3f}s")

            # 测量第一次状态查询时间
            start = time.time()
            status = p21.status()
            first_call_time = time.time() - start
            startup_metrics['first_status_call'] = first_call_time
            print(f"  ✅ 首次状态查询: {first_call_time:.3f}s")

        except Exception as e:
            print(f"  ❌ Perfect21实例化失败: {e}")
            startup_metrics['instance_creation'] = -1
            startup_metrics['first_status_call'] = -1

        total_startup = time.time() - self.start_time
        startup_metrics['total_startup_time'] = total_startup
        startup_metrics['module_load_times'] = module_load_times

        print(f"📊 总启动时间: {total_startup:.3f}s")

        return startup_metrics

    def measure_memory_usage(self) -> Dict[str, Any]:
        """测量内存使用情况"""
        print("💾 分析内存使用模式...")

        memory_metrics = {}

        # 当前内存使用
        memory_info = self.process.memory_info()
        memory_metrics['rss'] = memory_info.rss / 1024 / 1024  # MB
        memory_metrics['vms'] = memory_info.vms / 1024 / 1024  # MB
        memory_metrics['shared'] = getattr(memory_info, 'shared', 0) / 1024 / 1024  # MB

        # 内存增长
        memory_growth = memory_metrics['rss'] - self.baseline_memory
        memory_metrics['growth_since_startup'] = memory_growth

        # Python对象内存统计
        current, peak = tracemalloc.get_traced_memory()
        memory_metrics['python_current'] = current / 1024 / 1024  # MB
        memory_metrics['python_peak'] = peak / 1024 / 1024  # MB

        # 垃圾回收统计
        gc_stats = gc.get_stats()
        memory_metrics['gc_stats'] = gc_stats
        memory_metrics['gc_objects'] = len(gc.get_objects())

        # 系统内存
        system_memory = psutil.virtual_memory()
        memory_metrics['system_total'] = system_memory.total / 1024 / 1024 / 1024  # GB
        memory_metrics['system_available'] = system_memory.available / 1024 / 1024 / 1024  # GB
        memory_metrics['system_usage_percent'] = system_memory.percent

        print(f"  RSS内存: {memory_metrics['rss']:.1f}MB")
        print(f"  Python内存: {memory_metrics['python_current']:.1f}MB (峰值: {memory_metrics['python_peak']:.1f}MB)")
        print(f"  内存增长: {memory_growth:.1f}MB")
        print(f"  系统内存使用: {memory_metrics['system_usage_percent']:.1f}%")

        return memory_metrics

    def measure_execution_performance(self) -> Dict[str, Any]:
        """测量执行性能"""
        print("⚡ 测量执行性能...")

        execution_metrics = {}

        # 测试各种操作的执行时间
        operations = [
            ('status_query', self._test_status_query),
            ('git_hooks_status', self._test_git_hooks_status),
            ('capability_discovery', self._test_capability_discovery),
            ('workflow_status', self._test_workflow_status),
            ('parallel_preparation', self._test_parallel_preparation)
        ]

        for op_name, op_func in operations:
            times = []
            for i in range(5):  # 运行5次取平均值
                start = time.time()
                try:
                    result = op_func()
                    execution_time = time.time() - start
                    times.append(execution_time)
                    if i == 0:  # 只在第一次显示结果
                        success = "✅" if result.get('success', True) else "❌"
                        print(f"  {success} {op_name}: {execution_time:.3f}s")
                except Exception as e:
                    times.append(-1)
                    print(f"  ❌ {op_name}: 失败 - {e}")

            valid_times = [t for t in times if t > 0]
            if valid_times:
                execution_metrics[op_name] = {
                    'avg_time': sum(valid_times) / len(valid_times),
                    'min_time': min(valid_times),
                    'max_time': max(valid_times),
                    'success_rate': len(valid_times) / len(times)
                }
            else:
                execution_metrics[op_name] = {
                    'avg_time': -1,
                    'success_rate': 0
                }

        return execution_metrics

    def measure_io_performance(self) -> Dict[str, Any]:
        """测量I/O性能"""
        print("💿 分析I/O性能...")

        io_metrics = {}

        # 进程I/O统计
        try:
            io_counters = self.process.io_counters()
            io_metrics['read_count'] = io_counters.read_count
            io_metrics['write_count'] = io_counters.write_count
            io_metrics['read_bytes'] = io_counters.read_bytes / 1024 / 1024  # MB
            io_metrics['write_bytes'] = io_counters.write_bytes / 1024 / 1024  # MB
        except (psutil.AccessDenied, AttributeError):
            io_metrics['error'] = '无法获取I/O统计'

        # 测试文件操作性能
        test_file = '/tmp/perfect21_io_test.txt'
        file_ops = {}

        # 写入测试
        start = time.time()
        try:
            with open(test_file, 'w') as f:
                f.write('x' * 1024 * 1024)  # 1MB
            file_ops['write_1mb'] = time.time() - start
        except Exception as e:
            file_ops['write_1mb'] = -1

        # 读取测试
        start = time.time()
        try:
            with open(test_file, 'r') as f:
                content = f.read()
            file_ops['read_1mb'] = time.time() - start
        except Exception as e:
            file_ops['read_1mb'] = -1

        # 清理测试文件
        try:
            os.remove(test_file)
        except:
            pass

        io_metrics['file_operations'] = file_ops

        # 磁盘使用情况
        try:
            disk_usage = psutil.disk_usage('.')
            io_metrics['disk_total'] = disk_usage.total / 1024 / 1024 / 1024  # GB
            io_metrics['disk_used'] = disk_usage.used / 1024 / 1024 / 1024  # GB
            io_metrics['disk_free'] = disk_usage.free / 1024 / 1024 / 1024  # GB
            io_metrics['disk_usage_percent'] = (disk_usage.used / disk_usage.total) * 100
        except Exception as e:
            io_metrics['disk_error'] = str(e)

        if 'read_bytes' in io_metrics:
            print(f"  I/O读取: {io_metrics['read_bytes']:.2f}MB ({io_metrics['read_count']}次)")
            print(f"  I/O写入: {io_metrics['write_bytes']:.2f}MB ({io_metrics['write_count']}次)")

        if 'write_1mb' in file_ops and file_ops['write_1mb'] > 0:
            print(f"  文件写入(1MB): {file_ops['write_1mb']:.3f}s")
        if 'read_1mb' in file_ops and file_ops['read_1mb'] > 0:
            print(f"  文件读取(1MB): {file_ops['read_1mb']:.3f}s")

        return io_metrics

    def measure_parallel_efficiency(self) -> Dict[str, Any]:
        """测量并行执行效率"""
        print("🔄 分析并行执行效率...")

        parallel_metrics = {}

        try:
            # 测试智能分解器
            from features.smart_decomposer import get_smart_decomposer

            decomposer = get_smart_decomposer()

            # 测试不同复杂度的任务分解
            test_tasks = [
                "实现一个简单的用户注册功能",
                "设计一个完整的电商系统，包括用户管理、商品管理、订单处理、支付集成、库存管理",
                "优化数据库查询性能"
            ]

            decomposition_times = []
            complexities = []

            for task in test_tasks:
                start = time.time()
                try:
                    analysis = decomposer.decompose_task(task)
                    decomp_time = time.time() - start
                    decomposition_times.append(decomp_time)

                    if analysis:
                        complexities.append(analysis.complexity.value)
                        print(f"  ✅ 任务分解: {decomp_time:.3f}s (复杂度: {analysis.complexity.value})")
                    else:
                        print(f"  ❌ 任务分解失败: {task[:30]}...")
                except Exception as e:
                    print(f"  ❌ 分解错误: {e}")
                    decomposition_times.append(-1)

            valid_times = [t for t in decomposition_times if t > 0]
            if valid_times:
                parallel_metrics['decomposition_avg_time'] = sum(valid_times) / len(valid_times)
                parallel_metrics['decomposition_success_rate'] = len(valid_times) / len(test_tasks)

            parallel_metrics['tested_complexities'] = complexities

        except ImportError:
            parallel_metrics['error'] = '并行执行模块未可用'
            print("  ⚠️ 并行执行模块未安装或不可用")

        # CPU核心数和并行潜力
        parallel_metrics['cpu_cores'] = psutil.cpu_count(logical=False)
        parallel_metrics['logical_cores'] = psutil.cpu_count(logical=True)
        parallel_metrics['cpu_freq'] = psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None

        print(f"  CPU核心: {parallel_metrics['cpu_cores']}物理 / {parallel_metrics['logical_cores']}逻辑")

        return parallel_metrics

    def measure_database_performance(self) -> Dict[str, Any]:
        """测量数据库性能"""
        print("🗄️ 分析数据库性能...")

        db_metrics = {}

        # 检查是否有数据库连接
        db_files = []
        for ext in ['.db', '.sqlite', '.sqlite3']:
            db_files.extend(Path('.').rglob(f'*{ext}'))

        db_metrics['database_files'] = [str(f) for f in db_files]
        db_metrics['database_count'] = len(db_files)

        # 分析数据库文件大小
        total_db_size = 0
        for db_file in db_files:
            try:
                size = db_file.stat().st_size / 1024 / 1024  # MB
                total_db_size += size
                print(f"  📁 {db_file.name}: {size:.2f}MB")
            except Exception as e:
                print(f"  ❌ 无法读取 {db_file}: {e}")

        db_metrics['total_database_size'] = total_db_size

        # 检查数据库配置文件
        config_files = []
        for pattern in ['*database*', '*db*', '*config*']:
            config_files.extend(Path('.').rglob(f'{pattern}.yaml'))
            config_files.extend(Path('.').rglob(f'{pattern}.yml'))
            config_files.extend(Path('.').rglob(f'{pattern}.json'))

        db_metrics['config_files'] = [str(f) for f in config_files]

        # 模拟数据库操作性能测试
        try:
            import sqlite3
            test_db = '/tmp/perfect21_db_test.sqlite'

            # 创建测试数据库
            start = time.time()
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()

            # 创建表
            cursor.execute('''
                CREATE TABLE test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    value INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 插入测试数据
            insert_start = time.time()
            for i in range(1000):
                cursor.execute('INSERT INTO test_table (name, value) VALUES (?, ?)',
                             (f'item_{i}', i))
            conn.commit()
            insert_time = time.time() - insert_start

            # 查询测试
            query_start = time.time()
            cursor.execute('SELECT COUNT(*) FROM test_table WHERE value > 500')
            result = cursor.fetchone()
            query_time = time.time() - query_start

            conn.close()

            # 清理
            os.remove(test_db)

            db_metrics['mock_performance'] = {
                'insert_1000_records': insert_time,
                'count_query': query_time,
                'total_test_time': time.time() - start
            }

            print(f"  ✅ 模拟DB插入(1000条): {insert_time:.3f}s")
            print(f"  ✅ 模拟DB查询: {query_time:.3f}s")

        except Exception as e:
            db_metrics['mock_performance'] = {'error': str(e)}
            print(f"  ❌ 数据库性能测试失败: {e}")

        return db_metrics

    def identify_bottlenecks(self, metrics: Dict[str, Any]) -> List[str]:
        """识别性能瓶颈"""
        bottlenecks = []

        # 检查启动时间
        startup = metrics.get('startup_performance', {})
        if startup.get('total_startup_time', 0) > self.thresholds['startup_time']:
            bottlenecks.append(f"启动时间过长: {startup.get('total_startup_time', 0):.2f}s > {self.thresholds['startup_time']}s")

        # 检查内存使用
        memory = metrics.get('memory_usage', {})
        if memory.get('growth_since_startup', 0) > self.thresholds['memory_growth']:
            bottlenecks.append(f"内存增长过多: {memory.get('growth_since_startup', 0):.1f}MB > {self.thresholds['memory_growth']}MB")

        # 检查CPU使用
        cpu_percent = metrics.get('cpu_usage', {}).get('current', 0)
        if cpu_percent > self.thresholds['cpu_usage']:
            bottlenecks.append(f"CPU使用率过高: {cpu_percent:.1f}% > {self.thresholds['cpu_usage']}%")

        # 检查执行时间
        execution = metrics.get('execution_performance', {})
        for op_name, op_metrics in execution.items():
            if isinstance(op_metrics, dict) and op_metrics.get('avg_time', 0) > self.thresholds['response_time']:
                bottlenecks.append(f"{op_name}响应时间过长: {op_metrics['avg_time']:.3f}s > {self.thresholds['response_time']}s")

        # 检查I/O性能
        io_metrics = metrics.get('io_performance', {})
        file_ops = io_metrics.get('file_operations', {})
        if file_ops.get('write_1mb', 0) > 1.0:  # 1MB写入超过1秒
            bottlenecks.append(f"文件写入性能较差: {file_ops['write_1mb']:.3f}s/MB")

        return bottlenecks

    def generate_recommendations(self, metrics: Dict[str, Any], bottlenecks: List[str]) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 基于瓶颈的建议
        for bottleneck in bottlenecks:
            if "启动时间" in bottleneck:
                recommendations.append("优化模块导入：使用延迟导入(lazy import)减少启动时间")
                recommendations.append("缓存配置：将配置文件解析结果缓存到内存")

            if "内存增长" in bottleneck:
                recommendations.append("内存管理：实现对象池和缓存清理机制")
                recommendations.append("垃圾回收：调整GC阈值，定期执行强制垃圾回收")

            if "CPU使用率" in bottleneck:
                recommendations.append("异步处理：将CPU密集型操作移至后台线程")
                recommendations.append("算法优化：优化关键路径的算法复杂度")

            if "响应时间" in bottleneck:
                recommendations.append("缓存策略：实现结果缓存减少重复计算")
                recommendations.append("数据库优化：添加索引和查询优化")

        # 基于系统资源的建议
        memory = metrics.get('memory_usage', {})
        if memory.get('system_usage_percent', 0) > 80:
            recommendations.append("系统内存不足：考虑增加系统内存或优化内存使用")

        parallel = metrics.get('parallel_efficiency', {})
        if parallel.get('cpu_cores', 1) > 2:
            recommendations.append("并行优化：充分利用多核CPU，增加并行执行的机会")

        # I/O优化建议
        io_metrics = metrics.get('io_performance', {})
        if io_metrics.get('disk_usage_percent', 0) > 90:
            recommendations.append("磁盘空间：清理临时文件，考虑增加存储空间")

        # 数据库优化建议
        db_metrics = metrics.get('database_performance', {})
        if db_metrics.get('total_database_size', 0) > 100:  # 100MB
            recommendations.append("数据库优化：考虑数据库清理、索引优化或分库分表")

        return recommendations

    # 测试辅助方法
    def _test_status_query(self) -> Dict[str, Any]:
        """测试状态查询"""
        try:
            from main.perfect21 import Perfect21
            p21 = Perfect21()
            return p21.status()
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _test_git_hooks_status(self) -> Dict[str, Any]:
        """测试Git钩子状态"""
        try:
            from features.git_workflow import GitHooks
            hooks = GitHooks('.')
            return hooks.get_hook_status()
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _test_capability_discovery(self) -> Dict[str, Any]:
        """测试能力发现"""
        try:
            from features.capability_discovery import get_perfect21_capabilities
            return get_perfect21_capabilities()
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _test_workflow_status(self) -> Dict[str, Any]:
        """测试工作流状态"""
        try:
            from features.git_workflow import WorkflowManager
            wm = WorkflowManager('.')
            return wm.get_workflow_status()
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _test_parallel_preparation(self) -> Dict[str, Any]:
        """测试并行准备"""
        try:
            from features.smart_decomposer import get_smart_decomposer
            decomposer = get_smart_decomposer()
            return {'success': True, 'decomposer_ready': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

def run_comprehensive_performance_analysis():
    """运行完整的性能分析"""
    print("🎯 Perfect21 性能分析开始")
    print("=" * 80)

    profiler = PerformanceProfiler()

    # 1. 启动性能分析
    startup_metrics = profiler.measure_startup_performance()
    print()

    # 2. 内存使用分析
    memory_metrics = profiler.measure_memory_usage()
    print()

    # 3. 执行性能分析
    execution_metrics = profiler.measure_execution_performance()
    print()

    # 4. I/O性能分析
    io_metrics = profiler.measure_io_performance()
    print()

    # 5. 并行效率分析
    parallel_metrics = profiler.measure_parallel_efficiency()
    print()

    # 6. 数据库性能分析
    database_metrics = profiler.measure_database_performance()
    print()

    # CPU使用率快照
    cpu_metrics = {
        'current': psutil.cpu_percent(interval=1),
        'per_cpu': psutil.cpu_percent(percpu=True),
        'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
    }

    # 综合所有指标
    all_metrics = {
        'timestamp': datetime.now().isoformat(),
        'startup_performance': startup_metrics,
        'memory_usage': memory_metrics,
        'cpu_usage': cpu_metrics,
        'execution_performance': execution_metrics,
        'io_performance': io_metrics,
        'parallel_efficiency': parallel_metrics,
        'database_performance': database_metrics
    }

    # 识别瓶颈
    print("🔍 分析性能瓶颈...")
    bottlenecks = profiler.identify_bottlenecks(all_metrics)
    all_metrics['bottlenecks'] = bottlenecks

    # 生成优化建议
    print("💡 生成优化建议...")
    recommendations = profiler.generate_recommendations(all_metrics, bottlenecks)
    all_metrics['recommendations'] = recommendations

    # 保存详细报告
    report_file = f"performance_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(all_metrics, f, indent=2, ensure_ascii=False, default=str)

    # 显示摘要
    print("\n" + "=" * 80)
    print("📊 Perfect21 性能分析摘要")
    print("=" * 80)

    # 关键指标
    print("🚀 关键性能指标:")
    print(f"  启动时间: {startup_metrics.get('total_startup_time', 0):.3f}s")
    print(f"  内存使用: {memory_metrics.get('rss', 0):.1f}MB")
    print(f"  CPU使用率: {cpu_metrics.get('current', 0):.1f}%")

    if execution_metrics:
        avg_response = sum(m.get('avg_time', 0) for m in execution_metrics.values() if isinstance(m, dict)) / len(execution_metrics)
        print(f"  平均响应时间: {avg_response:.3f}s")

    # 瓶颈分析
    print(f"\n🚨 发现瓶颈: {len(bottlenecks)}个")
    for bottleneck in bottlenecks:
        print(f"  ⚠️ {bottleneck}")

    # 优化建议
    print(f"\n💡 优化建议: {len(recommendations)}个")
    for i, rec in enumerate(recommendations[:5], 1):  # 显示前5个建议
        print(f"  {i}. {rec}")

    if len(recommendations) > 5:
        print(f"  ... 还有{len(recommendations) - 5}个建议")

    print(f"\n📄 详细报告已保存到: {report_file}")

    # 性能评级
    score = calculate_performance_score(all_metrics)
    grade = get_performance_grade(score)
    print(f"\n⭐ Perfect21 性能评级: {grade} ({score:.1f}/100)")

    return all_metrics

def calculate_performance_score(metrics: Dict[str, Any]) -> float:
    """计算性能得分"""
    score = 100.0

    # 启动时间 (20分)
    startup_time = metrics.get('startup_performance', {}).get('total_startup_time', 0)
    if startup_time > 5:
        score -= 20
    elif startup_time > 3:
        score -= 10
    elif startup_time > 1:
        score -= 5

    # 内存使用 (25分)
    memory_growth = metrics.get('memory_usage', {}).get('growth_since_startup', 0)
    if memory_growth > 200:
        score -= 25
    elif memory_growth > 100:
        score -= 15
    elif memory_growth > 50:
        score -= 8

    # CPU使用 (20分)
    cpu_usage = metrics.get('cpu_usage', {}).get('current', 0)
    if cpu_usage > 80:
        score -= 20
    elif cpu_usage > 60:
        score -= 10
    elif cpu_usage > 40:
        score -= 5

    # 响应时间 (20分)
    execution = metrics.get('execution_performance', {})
    if execution:
        avg_times = [m.get('avg_time', 0) for m in execution.values() if isinstance(m, dict) and m.get('avg_time', 0) > 0]
        if avg_times:
            avg_response = sum(avg_times) / len(avg_times)
            if avg_response > 2:
                score -= 20
            elif avg_response > 1:
                score -= 10
            elif avg_response > 0.5:
                score -= 5

    # 瓶颈数量 (15分)
    bottleneck_count = len(metrics.get('bottlenecks', []))
    if bottleneck_count > 5:
        score -= 15
    elif bottleneck_count > 3:
        score -= 10
    elif bottleneck_count > 1:
        score -= 5

    return max(0, score)

def get_performance_grade(score: float) -> str:
    """获取性能等级"""
    if score >= 90:
        return "A+ (优秀)"
    elif score >= 80:
        return "A (良好)"
    elif score >= 70:
        return "B (中等)"
    elif score >= 60:
        return "C (及格)"
    else:
        return "D (需要改进)"

if __name__ == '__main__':
    try:
        # 检查系统资源
        print("🔧 系统环境检查:")
        print(f"  Python版本: {sys.version}")
        print(f"  CPU: {psutil.cpu_count(logical=False)}核心 / {psutil.cpu_count(logical=True)}线程")
        print(f"  内存: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f}GB")
        print(f"  磁盘: {psutil.disk_usage('.').free / 1024 / 1024 / 1024:.1f}GB 可用")
        print()

        # 运行性能分析
        metrics = run_comprehensive_performance_analysis()

        print("\n✅ 性能分析完成!")

    except KeyboardInterrupt:
        print("\n\n⚠️ 性能分析被用户中断")
    except Exception as e:
        print(f"\n❌ 性能分析失败: {e}")
        traceback.print_exc()