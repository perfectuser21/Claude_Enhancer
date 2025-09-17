#!/usr/bin/env python3
"""
Perfect21 架构性能基准测试
分析Manager类的加载性能、内存使用和耦合度
"""

import time
import sys
import os
import gc
import psutil
import importlib
from typing import Dict, List, Any
from dataclasses import dataclass

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

@dataclass
class ManagerBenchmark:
    """Manager性能基准"""
    name: str
    module_path: str
    load_time_ms: float
    memory_usage_mb: float
    dependencies: List[str]
    class_count: int
    lines_of_code: int
    success: bool = True
    error: str = None

class ArchitectureAnalyzer:
    """架构分析器"""

    def __init__(self):
        self.manager_modules = [
            ('architecture_manager', 'modules.architecture_manager'),
            ('parallel_manager', 'features.parallel_manager'),
            ('workflow_orchestrator', 'features.workflow_orchestrator.orchestrator'),
            ('sync_point_manager', 'features.sync_point_manager.sync_manager'),
            ('auth_manager', 'features.auth_system.auth_manager'),
            ('token_manager', 'features.auth_system.token_manager'),
            ('task_manager', 'features.workflow_orchestrator.task_manager'),
            ('workspace_manager', 'features.multi_workspace.workspace_manager'),
            ('decision_recorder', 'features.decision_recorder.adr_manager'),
            ('branch_manager', 'features.git_workflow.branch_manager'),
            ('hooks_manager', 'features.git_workflow.hooks_manager'),
            ('plugin_manager', 'features.git_workflow.plugins.plugin_manager'),
            ('lifecycle_manager', 'features.claude_md_manager.lifecycle_manager'),
            ('template_manager', 'features.claude_md_manager.template_manager'),
            ('version_manager', 'features.version_manager.version_manager'),
        ]

    def analyze_manager_performance(self, name: str, module_path: str) -> ManagerBenchmark:
        """分析单个Manager的性能"""
        print(f"分析 {name}...")

        # 记录初始内存
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        try:
            # 测量加载时间
            start_time = time.time()

            # 动态导入模块
            module = importlib.import_module(module_path)

            load_time = (time.time() - start_time) * 1000

            # 测量内存使用
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_usage = final_memory - initial_memory

            # 分析模块信息
            dependencies = self._analyze_dependencies(module)
            class_count = self._count_manager_classes(module)
            lines_of_code = self._count_lines_of_code(module_path)

            return ManagerBenchmark(
                name=name,
                module_path=module_path,
                load_time_ms=load_time,
                memory_usage_mb=memory_usage,
                dependencies=dependencies,
                class_count=class_count,
                lines_of_code=lines_of_code
            )

        except Exception as e:
            return ManagerBenchmark(
                name=name,
                module_path=module_path,
                load_time_ms=0,
                memory_usage_mb=0,
                dependencies=[],
                class_count=0,
                lines_of_code=0,
                success=False,
                error=str(e)
            )

    def _analyze_dependencies(self, module) -> List[str]:
        """分析模块依赖"""
        dependencies = []

        # 检查模块的__dict__中的导入
        for name, obj in module.__dict__.items():
            if hasattr(obj, '__module__') and obj.__module__:
                if 'perfect21' in obj.__module__.lower() or 'features' in obj.__module__:
                    dependencies.append(obj.__module__)

        return list(set(dependencies))

    def _count_manager_classes(self, module) -> int:
        """统计Manager类数量"""
        count = 0
        for name, obj in module.__dict__.items():
            if isinstance(obj, type) and 'manager' in name.lower():
                count += 1
        return count

    def _count_lines_of_code(self, module_path: str) -> int:
        """统计代码行数"""
        try:
            # 尝试找到文件路径
            file_path = module_path.replace('.', '/') + '.py'
            full_path = os.path.join(os.path.dirname(__file__), file_path)

            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    return len([line for line in f if line.strip() and not line.strip().startswith('#')])
        except:
            pass
        return 0

    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """运行综合架构分析"""
        print("🔍 Perfect21 架构性能分析开始...")
        print("=" * 80)

        benchmarks = []

        # 分析每个Manager
        for name, module_path in self.manager_modules:
            benchmark = self.analyze_manager_performance(name, module_path)
            benchmarks.append(benchmark)

            # 强制垃圾回收
            gc.collect()

        # 生成分析报告
        return self._generate_analysis_report(benchmarks)

    def _generate_analysis_report(self, benchmarks: List[ManagerBenchmark]) -> Dict[str, Any]:
        """生成分析报告"""
        successful_benchmarks = [b for b in benchmarks if b.success]
        failed_benchmarks = [b for b in benchmarks if not b.success]

        # 性能统计
        total_load_time = sum(b.load_time_ms for b in successful_benchmarks)
        total_memory = sum(b.memory_usage_mb for b in successful_benchmarks)
        total_lines = sum(b.lines_of_code for b in successful_benchmarks)

        # 识别性能瓶颈
        slow_managers = sorted(successful_benchmarks, key=lambda x: x.load_time_ms, reverse=True)[:5]
        memory_heavy = sorted(successful_benchmarks, key=lambda x: x.memory_usage_mb, reverse=True)[:5]

        # 依赖分析
        dependency_graph = self._analyze_dependency_coupling(successful_benchmarks)

        report = {
            'summary': {
                'total_managers': len(benchmarks),
                'successful_loads': len(successful_benchmarks),
                'failed_loads': len(failed_benchmarks),
                'total_load_time_ms': total_load_time,
                'total_memory_mb': total_memory,
                'total_lines_of_code': total_lines,
                'average_load_time_ms': total_load_time / len(successful_benchmarks) if successful_benchmarks else 0,
                'average_memory_mb': total_memory / len(successful_benchmarks) if successful_benchmarks else 0
            },
            'performance_bottlenecks': {
                'slowest_managers': [(b.name, b.load_time_ms) for b in slow_managers],
                'memory_heavy_managers': [(b.name, b.memory_usage_mb) for b in memory_heavy],
            },
            'coupling_analysis': dependency_graph,
            'failed_modules': [(b.name, b.error) for b in failed_benchmarks],
            'detailed_benchmarks': [
                {
                    'name': b.name,
                    'load_time_ms': b.load_time_ms,
                    'memory_mb': b.memory_usage_mb,
                    'dependencies_count': len(b.dependencies),
                    'lines_of_code': b.lines_of_code,
                    'success': b.success
                } for b in benchmarks
            ]
        }

        return report

    def _analyze_dependency_coupling(self, benchmarks: List[ManagerBenchmark]) -> Dict[str, Any]:
        """分析依赖耦合度"""
        # 构建依赖图
        dependency_count = {}
        for benchmark in benchmarks:
            dependency_count[benchmark.name] = len(benchmark.dependencies)

        # 识别高耦合模块
        high_coupling = {name: count for name, count in dependency_count.items() if count > 3}

        return {
            'dependency_counts': dependency_count,
            'high_coupling_modules': high_coupling,
            'average_dependencies': sum(dependency_count.values()) / len(dependency_count) if dependency_count else 0
        }

    def generate_refactoring_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """生成重构建议"""
        recommendations = []

        # 性能优化建议
        if report['summary']['total_load_time_ms'] > 1000:
            recommendations.append("⚠️ 总加载时间超过1秒，建议优化模块加载策略")

        if report['summary']['total_memory_mb'] > 50:
            recommendations.append("⚠️ 内存使用过高，建议实现懒加载机制")

        # 模块合并建议
        if report['summary']['total_managers'] > 20:
            recommendations.append("🔄 Manager类过多，建议合并功能相近的模块")

        # 耦合度建议
        high_coupling = report['coupling_analysis']['high_coupling_modules']
        if high_coupling:
            recommendations.append(f"🔗 高耦合模块需要解耦: {list(high_coupling.keys())}")

        # 失败模块建议
        if report['failed_modules']:
            recommendations.append(f"❌ 修复失败的模块: {[name for name, _ in report['failed_modules']]}")

        return recommendations

def run_architecture_benchmark():
    """运行架构基准测试"""
    analyzer = ArchitectureAnalyzer()

    print("🚀 Perfect21 架构分析工具")
    print("=" * 80)

    # 运行分析
    report = analyzer.run_comprehensive_analysis()

    # 生成建议
    recommendations = analyzer.generate_refactoring_recommendations(report)

    # 打印结果
    print("\n📊 分析结果:")
    print("-" * 40)
    summary = report['summary']
    print(f"总Manager数量: {summary['total_managers']}")
    print(f"成功加载: {summary['successful_loads']}")
    print(f"加载失败: {summary['failed_loads']}")
    print(f"总加载时间: {summary['total_load_time_ms']:.1f}ms")
    print(f"总内存使用: {summary['total_memory_mb']:.1f}MB")
    print(f"总代码行数: {summary['total_lines_of_code']}")
    print(f"平均加载时间: {summary['average_load_time_ms']:.1f}ms")

    print(f"\n🐌 最慢的5个Manager:")
    for name, time_ms in report['performance_bottlenecks']['slowest_managers']:
        print(f"  • {name}: {time_ms:.1f}ms")

    print(f"\n🧠 内存使用最多的5个Manager:")
    for name, memory_mb in report['performance_bottlenecks']['memory_heavy_managers']:
        print(f"  • {name}: {memory_mb:.1f}MB")

    print(f"\n🔗 高耦合模块:")
    for name, dep_count in report['coupling_analysis']['high_coupling_modules'].items():
        print(f"  • {name}: {dep_count}个依赖")

    if report['failed_modules']:
        print(f"\n❌ 失败的模块:")
        for name, error in report['failed_modules']:
            print(f"  • {name}: {error}")

    print(f"\n💡 重构建议:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")

    return report

if __name__ == "__main__":
    report = run_architecture_benchmark()

    # 保存详细报告
    import json
    with open('architecture_performance_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📄 详细报告已保存到: architecture_performance_report.json")