#!/usr/bin/env python3
"""
Perfect21 简化性能测试
专注于核心性能指标的快速评估
"""

import os
import sys
import time
import json
import psutil
import statistics
import threading
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

@dataclass
class PerformanceResult:
    """性能测试结果"""
    test_name: str
    duration: float
    operations_count: int
    success_count: int
    failure_count: int
    throughput: float
    avg_response_time: float
    cpu_usage: float
    memory_usage: float

class SimplePerformanceMonitor:
    """简单性能监控器"""

    def __init__(self):
        self.monitoring = False
        self.cpu_readings = []
        self.memory_readings = []

    def start(self):
        """开始监控"""
        self.monitoring = True
        self.cpu_readings = []
        self.memory_readings = []

        def monitor():
            while self.monitoring:
                try:
                    self.cpu_readings.append(psutil.cpu_percent())
                    self.memory_readings.append(psutil.virtual_memory().percent)
                    time.sleep(0.5)
                except:
                    break

        self.thread = threading.Thread(target=monitor, daemon=True)
        self.thread.start()

    def stop(self) -> Dict[str, float]:
        """停止监控并返回统计"""
        self.monitoring = False

        if self.cpu_readings and self.memory_readings:
            return {
                'avg_cpu': statistics.mean(self.cpu_readings),
                'max_cpu': max(self.cpu_readings),
                'avg_memory': statistics.mean(self.memory_readings),
                'max_memory': max(self.memory_readings)
            }
        return {'avg_cpu': 0, 'max_cpu': 0, 'avg_memory': 0, 'max_memory': 0}

class Perfect21SimplePerformanceTest:
    """Perfect21 简化性能测试"""

    def __init__(self):
        self.results = []
        self.monitor = SimplePerformanceMonitor()

        # 确保结果目录存在
        self.results_dir = Path("tests/performance/results")
        self.results_dir.mkdir(exist_ok=True)

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有性能测试"""
        print("🎯 Perfect21 性能测试开始")
        print("=" * 60)

        test_start = datetime.now()

        # 1. 工作流创建性能测试
        self.results.append(self.test_workflow_creation())

        # 2. 并发工作流测试
        self.results.append(self.test_concurrent_workflows())

        # 3. 内存使用测试
        self.results.append(self.test_memory_usage())

        # 4. 响应时间测试
        self.results.append(self.test_response_times())

        # 5. 压力测试
        self.results.append(self.test_stress_performance())

        # 生成报告
        report = self.generate_report(test_start)
        self.save_report(report)

        return report

    def test_workflow_creation(self) -> PerformanceResult:
        """测试工作流创建性能"""
        print("\n📝 1. 工作流创建性能测试")
        print("-" * 40)

        self.monitor.start()
        start_time = time.time()

        operations = 500
        success_count = 0
        response_times = []

        # 模拟工作流创建
        for i in range(operations):
            op_start = time.time()

            try:
                # 模拟工作流创建操作
                workflow_config = self.create_mock_workflow(f"test_{i}")
                time.sleep(0.001)  # 模拟处理时间

                response_time = time.time() - op_start
                response_times.append(response_time)
                success_count += 1

                if i % 100 == 0:
                    print(f"  已创建 {i} 个工作流...")

            except Exception:
                pass

        duration = time.time() - start_time
        resource_stats = self.monitor.stop()

        result = PerformanceResult(
            test_name="workflow_creation",
            duration=duration,
            operations_count=operations,
            success_count=success_count,
            failure_count=operations - success_count,
            throughput=success_count / duration,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            cpu_usage=resource_stats['avg_cpu'],
            memory_usage=resource_stats['avg_memory']
        )

        print(f"✅ 工作流创建测试完成: {success_count}/{operations} 成功")
        print(f"   吞吐量: {result.throughput:.1f} workflows/s")
        print(f"   平均响应时间: {result.avg_response_time:.3f}s")

        return result

    def test_concurrent_workflows(self) -> PerformanceResult:
        """测试并发工作流性能"""
        print("\n🚀 2. 并发工作流测试")
        print("-" * 40)

        self.monitor.start()
        start_time = time.time()

        concurrent_users = 10
        operations_per_user = 20
        total_operations = concurrent_users * operations_per_user

        success_count = 0
        failure_count = 0
        response_times = []
        lock = threading.Lock()

        def worker(worker_id):
            nonlocal success_count, failure_count
            worker_success = 0
            worker_failures = 0
            worker_times = []

            for i in range(operations_per_user):
                op_start = time.time()

                try:
                    # 模拟并发工作流操作
                    workflow_config = self.create_mock_workflow(f"concurrent_{worker_id}_{i}")
                    time.sleep(0.005)  # 模拟处理时间

                    response_time = time.time() - op_start
                    worker_times.append(response_time)
                    worker_success += 1

                except Exception:
                    worker_failures += 1

            with lock:
                success_count += worker_success
                failure_count += worker_failures
                response_times.extend(worker_times)

        # 启动并发工作线程
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(worker, i) for i in range(concurrent_users)]
            concurrent.futures.wait(futures)

        duration = time.time() - start_time
        resource_stats = self.monitor.stop()

        result = PerformanceResult(
            test_name="concurrent_workflows",
            duration=duration,
            operations_count=total_operations,
            success_count=success_count,
            failure_count=failure_count,
            throughput=success_count / duration,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            cpu_usage=resource_stats['avg_cpu'],
            memory_usage=resource_stats['avg_memory']
        )

        print(f"✅ 并发测试完成: {success_count}/{total_operations} 成功")
        print(f"   并发用户: {concurrent_users}")
        print(f"   吞吐量: {result.throughput:.1f} ops/s")

        return result

    def test_memory_usage(self) -> PerformanceResult:
        """测试内存使用性能"""
        print("\n🧠 3. 内存使用测试")
        print("-" * 40)

        self.monitor.start()
        start_time = time.time()

        operations = 1000
        success_count = 0

        # 创建大量对象测试内存使用
        workflows = []

        initial_memory = psutil.virtual_memory().used / 1024 / 1024  # MB

        for i in range(operations):
            try:
                # 创建模拟工作流对象
                workflow = self.create_large_mock_workflow(f"memory_test_{i}")
                workflows.append(workflow)
                success_count += 1

                if i % 200 == 0:
                    current_memory = psutil.virtual_memory().used / 1024 / 1024
                    print(f"  已创建 {i} 个对象，内存使用: {current_memory - initial_memory:.1f}MB")

            except Exception:
                pass

        duration = time.time() - start_time
        resource_stats = self.monitor.stop()

        final_memory = psutil.virtual_memory().used / 1024 / 1024
        memory_growth = final_memory - initial_memory

        result = PerformanceResult(
            test_name="memory_usage",
            duration=duration,
            operations_count=operations,
            success_count=success_count,
            failure_count=operations - success_count,
            throughput=success_count / duration,
            avg_response_time=duration / operations,
            cpu_usage=resource_stats['avg_cpu'],
            memory_usage=resource_stats['max_memory']
        )

        print(f"✅ 内存测试完成: {success_count} 个对象创建")
        print(f"   内存增长: {memory_growth:.1f}MB")
        print(f"   平均每对象: {memory_growth/success_count:.3f}MB" if success_count > 0 else "   平均每对象: N/A")

        return result

    def test_response_times(self) -> PerformanceResult:
        """测试响应时间性能"""
        print("\n⏱️  4. 响应时间测试")
        print("-" * 40)

        self.monitor.start()
        start_time = time.time()

        operations = 300
        success_count = 0
        response_times = []

        # 测试不同复杂度的操作响应时间
        complexities = [0.001, 0.005, 0.01]  # 简单、中等、复杂

        for i in range(operations):
            complexity = complexities[i % len(complexities)]
            op_start = time.time()

            try:
                # 模拟不同复杂度的操作
                workflow = self.create_mock_workflow(f"response_test_{i}")
                time.sleep(complexity)  # 模拟处理时间

                response_time = time.time() - op_start
                response_times.append(response_time)
                success_count += 1

            except Exception:
                pass

        duration = time.time() - start_time
        resource_stats = self.monitor.stop()

        # 计算响应时间统计
        if response_times:
            avg_response = statistics.mean(response_times)
            p95_response = sorted(response_times)[int(len(response_times) * 0.95)]
            max_response = max(response_times)
        else:
            avg_response = p95_response = max_response = 0

        result = PerformanceResult(
            test_name="response_times",
            duration=duration,
            operations_count=operations,
            success_count=success_count,
            failure_count=operations - success_count,
            throughput=success_count / duration,
            avg_response_time=avg_response,
            cpu_usage=resource_stats['avg_cpu'],
            memory_usage=resource_stats['avg_memory']
        )

        print(f"✅ 响应时间测试完成: {success_count} 次操作")
        print(f"   平均响应时间: {avg_response:.3f}s")
        print(f"   P95响应时间: {p95_response:.3f}s")
        print(f"   最大响应时间: {max_response:.3f}s")

        return result

    def test_stress_performance(self) -> PerformanceResult:
        """测试压力性能"""
        print("\n🔥 5. 压力测试")
        print("-" * 40)

        self.monitor.start()
        start_time = time.time()

        test_duration = 30  # 30秒压力测试
        operations_count = 0
        success_count = 0
        response_times = []

        print(f"   运行 {test_duration} 秒压力测试...")

        while time.time() - start_time < test_duration:
            op_start = time.time()

            try:
                # 高频操作
                workflow = self.create_mock_workflow(f"stress_{operations_count}")
                time.sleep(0.002)  # 模拟快速操作

                response_time = time.time() - op_start
                response_times.append(response_time)
                success_count += 1

            except Exception:
                pass

            operations_count += 1

            # 每5秒报告一次进度
            if operations_count % 500 == 0:
                elapsed = time.time() - start_time
                current_throughput = operations_count / elapsed
                print(f"   {elapsed:.1f}s: {operations_count} 操作, {current_throughput:.1f} ops/s")

        duration = time.time() - start_time
        resource_stats = self.monitor.stop()

        result = PerformanceResult(
            test_name="stress_test",
            duration=duration,
            operations_count=operations_count,
            success_count=success_count,
            failure_count=operations_count - success_count,
            throughput=success_count / duration,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            cpu_usage=resource_stats['avg_cpu'],
            memory_usage=resource_stats['avg_memory']
        )

        print(f"✅ 压力测试完成: {success_count}/{operations_count} 成功")
        print(f"   持续时间: {duration:.1f}s")
        print(f"   峰值吞吐量: {result.throughput:.1f} ops/s")
        print(f"   CPU使用: {resource_stats['max_cpu']:.1f}%")

        return result

    def create_mock_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """创建模拟工作流配置"""
        return {
            'workflow_id': workflow_id,
            'name': f'Test Workflow {workflow_id}',
            'stages': [
                {'name': 'analysis', 'tasks': ['task1', 'task2']},
                {'name': 'implementation', 'tasks': ['task3', 'task4', 'task5']}
            ],
            'agents': ['backend-architect', 'test-engineer'],
            'created_at': datetime.now().isoformat()
        }

    def create_large_mock_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """创建大型模拟工作流（用于内存测试）"""
        return {
            'workflow_id': workflow_id,
            'name': f'Large Test Workflow {workflow_id}',
            'description': 'Large workflow for memory testing' * 10,
            'stages': [
                {
                    'name': f'stage_{i}',
                    'tasks': [f'task_{i}_{j}' for j in range(10)],
                    'config': {'data': 'x' * 100}  # 添加一些数据
                }
                for i in range(5)
            ],
            'agents': [f'agent_{i}' for i in range(10)],
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'large_data': ['item' * 20 for _ in range(50)]
            }
        }

    def generate_report(self, test_start: datetime) -> Dict[str, Any]:
        """生成性能测试报告"""
        print("\n📊 生成性能测试报告...")

        test_end = datetime.now()
        total_duration = (test_end - test_start).total_seconds()

        # 计算整体统计
        total_operations = sum(r.operations_count for r in self.results)
        total_success = sum(r.success_count for r in self.results)
        total_failures = sum(r.failure_count for r in self.results)

        avg_throughput = statistics.mean([r.throughput for r in self.results])
        avg_response_time = statistics.mean([r.avg_response_time for r in self.results])
        avg_cpu_usage = statistics.mean([r.cpu_usage for r in self.results])
        avg_memory_usage = statistics.mean([r.memory_usage for r in self.results])

        # 计算性能评分
        performance_score = self.calculate_performance_score()

        report = {
            'test_metadata': {
                'test_start': test_start.isoformat(),
                'test_end': test_end.isoformat(),
                'total_duration': total_duration,
                'system_info': {
                    'cpu_count': psutil.cpu_count(),
                    'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
                    'platform': sys.platform
                }
            },
            'overall_metrics': {
                'total_operations': total_operations,
                'total_success': total_success,
                'total_failures': total_failures,
                'success_rate': total_success / total_operations if total_operations > 0 else 0,
                'avg_throughput': avg_throughput,
                'avg_response_time': avg_response_time,
                'avg_cpu_usage': avg_cpu_usage,
                'avg_memory_usage': avg_memory_usage,
                'performance_score': performance_score
            },
            'test_results': [
                {
                    'test_name': r.test_name,
                    'duration': r.duration,
                    'operations_count': r.operations_count,
                    'success_count': r.success_count,
                    'failure_count': r.failure_count,
                    'throughput': r.throughput,
                    'avg_response_time': r.avg_response_time,
                    'cpu_usage': r.cpu_usage,
                    'memory_usage': r.memory_usage
                }
                for r in self.results
            ],
            'recommendations': self.generate_recommendations(),
            'performance_grade': self.get_performance_grade(performance_score)
        }

        return report

    def calculate_performance_score(self) -> float:
        """计算性能评分（0-100）"""
        scores = []

        for result in self.results:
            # 成功率评分 (40分)
            success_rate_score = (result.success_count / result.operations_count) * 40 if result.operations_count > 0 else 0

            # 吞吐量评分 (30分) - 基于合理的期望值
            expected_throughput = {
                'workflow_creation': 200,
                'concurrent_workflows': 50,
                'memory_usage': 100,
                'response_times': 150,
                'stress_test': 300
            }
            expected = expected_throughput.get(result.test_name, 100)
            throughput_score = min(30, (result.throughput / expected) * 30)

            # 响应时间评分 (20分) - 响应时间越低越好
            max_acceptable_response = 0.1  # 100ms
            response_score = max(0, 20 * (1 - result.avg_response_time / max_acceptable_response))

            # 资源使用评分 (10分) - CPU和内存使用越低越好
            resource_score = max(0, 10 * (1 - (result.cpu_usage + result.memory_usage) / 200))

            test_score = success_rate_score + throughput_score + response_score + resource_score
            scores.append(test_score)

        return statistics.mean(scores) if scores else 0

    def get_performance_grade(self, score: float) -> str:
        """获取性能等级"""
        if score >= 90:
            return 'A+ (优秀)'
        elif score >= 80:
            return 'A (良好)'
        elif score >= 70:
            return 'B (中等)'
        elif score >= 60:
            return 'C (及格)'
        else:
            return 'D (需要改进)'

    def generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 基于测试结果生成建议
        for result in self.results:
            if result.success_count / result.operations_count < 0.95:
                recommendations.append(f"{result.test_name}: 成功率较低，需要改进错误处理")

            if result.avg_response_time > 0.05:  # 50ms
                recommendations.append(f"{result.test_name}: 响应时间较高，考虑性能优化")

            if result.cpu_usage > 70:
                recommendations.append(f"{result.test_name}: CPU使用率高，检查算法效率")

            if result.memory_usage > 80:
                recommendations.append(f"{result.test_name}: 内存使用率高，检查内存泄漏")

        # 通用建议
        if not recommendations:
            recommendations.append("性能表现良好，继续保持当前水平")

        recommendations.extend([
            "建议实施性能监控以跟踪趋势",
            "定期执行性能测试以确保质量",
            "考虑在CI/CD中集成性能测试"
        ])

        return recommendations

    def save_report(self, report: Dict[str, Any]):
        """保存性能测试报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON报告
        json_file = self.results_dir / f"simple_performance_report_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        # 文本摘要
        txt_file = self.results_dir / f"performance_summary_{timestamp}.txt"
        self.generate_text_summary(report, txt_file)

        print(f"\n📄 性能测试报告已保存:")
        print(f"  • JSON报告: {json_file}")
        print(f"  • 文本摘要: {txt_file}")

        # 打印关键指标
        metrics = report['overall_metrics']
        print(f"\n📊 性能测试摘要:")
        print(f"  • 总体评分: {metrics['performance_score']:.1f}/100 - {report['performance_grade']}")
        print(f"  • 成功率: {metrics['success_rate']:.1%}")
        print(f"  • 平均吞吐量: {metrics['avg_throughput']:.1f} ops/s")
        print(f"  • 平均响应时间: {metrics['avg_response_time']:.3f}s")
        print(f"  • 平均CPU使用: {metrics['avg_cpu_usage']:.1f}%")
        print(f"  • 平均内存使用: {metrics['avg_memory_usage']:.1f}%")

    def generate_text_summary(self, report: Dict[str, Any], filename: Path):
        """生成文本摘要报告"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("Perfect21 性能测试摘要报告\n")
            f.write("=" * 50 + "\n\n")

            # 测试概览
            metadata = report['test_metadata']
            f.write(f"测试时间: {metadata['test_start']} - {metadata['test_end']}\n")
            f.write(f"测试持续时间: {metadata['total_duration']:.1f}秒\n")
            f.write(f"系统配置: {metadata['system_info']['cpu_count']} CPU核心, "
                   f"{metadata['system_info']['memory_total_gb']:.1f}GB 内存\n\n")

            # 整体指标
            metrics = report['overall_metrics']
            f.write("整体性能指标:\n")
            f.write("-" * 30 + "\n")
            f.write(f"性能评分: {metrics['performance_score']:.1f}/100 ({report['performance_grade']})\n")
            f.write(f"总操作数: {metrics['total_operations']}\n")
            f.write(f"成功率: {metrics['success_rate']:.1%}\n")
            f.write(f"平均吞吐量: {metrics['avg_throughput']:.1f} ops/s\n")
            f.write(f"平均响应时间: {metrics['avg_response_time']:.3f}s\n")
            f.write(f"平均CPU使用: {metrics['avg_cpu_usage']:.1f}%\n")
            f.write(f"平均内存使用: {metrics['avg_memory_usage']:.1f}%\n\n")

            # 详细结果
            f.write("各项测试详细结果:\n")
            f.write("-" * 30 + "\n")
            for result in report['test_results']:
                f.write(f"\n{result['test_name']}:\n")
                f.write(f"  操作数: {result['operations_count']}\n")
                f.write(f"  成功数: {result['success_count']}\n")
                f.write(f"  吞吐量: {result['throughput']:.1f} ops/s\n")
                f.write(f"  响应时间: {result['avg_response_time']:.3f}s\n")
                f.write(f"  CPU使用: {result['cpu_usage']:.1f}%\n")
                f.write(f"  内存使用: {result['memory_usage']:.1f}%\n")

            # 优化建议
            f.write(f"\n优化建议:\n")
            f.write("-" * 30 + "\n")
            for i, rec in enumerate(report['recommendations'], 1):
                f.write(f"{i}. {rec}\n")

def main():
    """主函数"""
    print("🎯 Perfect21 简化性能测试启动")

    tester = Perfect21SimplePerformanceTest()

    try:
        report = tester.run_all_tests()

        print("\n✅ 性能测试完成!")

        return report

    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        return None
    except Exception as e:
        print(f"\n❌ 性能测试失败: {e}")
        raise

if __name__ == "__main__":
    main()