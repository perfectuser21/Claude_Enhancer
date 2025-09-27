#!/usr/bin/env python3
"""
Claude Enhancer 5.0 - 综合测试执行器
作为test-engineer设计的统一测试管理平台

功能特性:
1. 统一管理所有测试框架
2. 智能测试执行计划
3. 并行测试支持
4. 测试结果聚合分析
5. 综合测试报告生成
6. CI/CD集成支持
"""

import os
import sys
import time
import json
import argparse
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import threading
import queue


@dataclass
class TestFrameworkConfig:
    """测试框架配置"""

    name: str
    description: str
    script_path: str
    category: str  # "unit", "integration", "performance", "regression", "recovery"
    priority: int  # 1-5, 1为最高优先级
    estimated_duration: int  # 预估执行时间（秒）
    dependencies: List[str]  # 依赖的其他测试框架
    parallel_safe: bool  # 是否可以并行执行


@dataclass
class TestExecutionResult:
    """测试执行结果"""

    framework_name: str
    success: bool
    duration: float
    output: str
    error_output: str
    report_file: Optional[str] = None
    metrics: Dict[str, Any] = None


class TestOrchestrator:
    """测试执行编排器"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.test_dir = os.path.join(project_root, "test")
        self.reports_dir = os.path.join(self.test_dir, "comprehensive_reports")
        self.quick_mode = False  # 添加quick_mode状态追踪

        # 确保目录存在
        os.makedirs(self.reports_dir, exist_ok=True)

        # 初始化测试框架配置
        self.test_frameworks = self._initialize_test_frameworks()

        # 执行状态跟踪
        self.execution_queue = queue.Queue()
        self.completed_tests = {}
        self.failed_tests = {}

    def _initialize_test_frameworks(self) -> Dict[str, TestFrameworkConfig]:
        """初始化测试框架配置"""
        frameworks = {
            "document_quality": TestFrameworkConfig(
                name="document_quality",
                description="文档质量管理系统测试",
                script_path="test/document_quality_management_test_strategy.py",
                category="unit",
                priority=1,
                estimated_duration=300,  # 5分钟
                dependencies=[],
                parallel_safe=True,
            ),
            "performance_benchmark": TestFrameworkConfig(
                name="performance_benchmark",
                description="性能基准测试",
                script_path="test/performance_benchmark_runner.py",
                category="performance",
                priority=2,
                estimated_duration=600,  # 10分钟
                dependencies=[],
                parallel_safe=False,  # 性能测试需要独占资源
            ),
            "regression_test": TestFrameworkConfig(
                name="regression_test",
                description="回归测试",
                script_path="test/regression_test_framework.py",
                category="regression",
                priority=3,
                estimated_duration=480,  # 8分钟
                dependencies=["performance_benchmark"],  # 需要性能基线
                parallel_safe=True,
            ),
            "failure_recovery": TestFrameworkConfig(
                name="failure_recovery",
                description="故障恢复测试",
                script_path="test/failure_recovery_test_framework.py",
                category="recovery",
                priority=4,
                estimated_duration=900,  # 15分钟
                dependencies=[],
                parallel_safe=False,  # 故障注入可能影响其他测试
            ),
            "shell_integration": TestFrameworkConfig(
                name="shell_integration",
                description="Shell脚本集成测试",
                script_path="test/run_document_quality_tests.sh",
                category="integration",
                priority=2,
                estimated_duration=180,  # 3分钟
                dependencies=[],
                parallel_safe=True,
            ),
        }

        return frameworks

    def run_all_tests(
        self, parallel: bool = True, quick_mode: bool = False
    ) -> Dict[str, TestExecutionResult]:
        """运行所有测试"""
        self.quick_mode = quick_mode  # 保存quick_mode状态
        print("🚀 Claude Enhancer 5.0 - 综合测试执行器")
        print(f"📁 项目路径: {self.project_root}")
        print(f"🔧 并行模式: {'启用' if parallel else '禁用'}")
        print(f"⚡ 快速模式: {'启用' if quick_mode else '禁用'}")
        print("=" * 60)

        start_time = time.time()

        # 根据模式选择测试框架
        selected_frameworks = self._select_frameworks(quick_mode)

        # 计算执行计划
        execution_plan = self._create_execution_plan(selected_frameworks, parallel)

        print(f"📋 测试计划: {len(execution_plan)} 个阶段")
        for i, phase in enumerate(execution_plan, 1):
            framework_names = [f.name for f in phase]
            estimated_time = sum(f.estimated_duration for f in phase)
            print(
                f"  阶段 {i}: {', '.join(framework_names)} (预估{estimated_time//60}分{estimated_time%60}秒)"
            )

        # 执行测试
        results = {}

        for phase_num, phase_frameworks in enumerate(execution_plan, 1):
            print(f"\n🔄 执行阶段 {phase_num}/{len(execution_plan)}")

            if len(phase_frameworks) == 1 or not parallel:
                # 串行执行
                for framework in phase_frameworks:
                    result = self._execute_single_test(framework)
                    results[framework.name] = result
            else:
                # 并行执行
                phase_results = self._execute_parallel_tests(phase_frameworks)
                results.update(phase_results)

        total_time = time.time() - start_time

        # 生成综合报告
        print(f"\n📊 生成综合测试报告...")
        report_file = self._generate_comprehensive_report(results, total_time)

        # 输出总结
        self._print_execution_summary(results, total_time, report_file)

        return results

    def _select_frameworks(self, quick_mode: bool) -> List[TestFrameworkConfig]:
        """根据模式选择测试框架"""
        if quick_mode:
            # 快速模式：只运行高优先级和快速的测试
            return [
                f
                for f in self.test_frameworks.values()
                if f.priority <= 2 and f.estimated_duration <= 300
            ]
        else:
            # 完整模式：运行所有测试
            return list(self.test_frameworks.values())

    def _create_execution_plan(
        self, frameworks: List[TestFrameworkConfig], parallel: bool
    ) -> List[List[TestFrameworkConfig]]:
        """创建测试执行计划"""
        if not parallel:
            # 串行执行：按优先级排序
            sorted_frameworks = sorted(frameworks, key=lambda f: f.priority)
            return [[f] for f in sorted_frameworks]

        # 并行执行：考虑依赖关系和并行安全性
        plan = []
        remaining = frameworks.copy()
        completed = set()

        while remaining:
            # 找出当前可以执行的框架
            ready_frameworks = []

            for framework in remaining:
                # 检查依赖是否已完成
                dependencies_met = all(
                    dep in completed for dep in framework.dependencies
                )

                if dependencies_met:
                    ready_frameworks.append(framework)

            if not ready_frameworks:
                # 避免死锁：如果没有可执行的框架，强制执行一个
                ready_frameworks = [remaining[0]]

            # 将可并行的框架分组
            parallel_group = []
            serial_only = []

            for framework in ready_frameworks:
                if framework.parallel_safe:
                    parallel_group.append(framework)
                else:
                    serial_only.append(framework)

            # 先执行并行安全的测试
            if parallel_group:
                plan.append(parallel_group)
                for f in parallel_group:
                    remaining.remove(f)
                    completed.add(f.name)

            # 然后逐个执行非并行安全的测试
            for framework in serial_only:
                plan.append([framework])
                remaining.remove(framework)
                completed.add(framework.name)

        return plan

    def _execute_single_test(
        self, framework: TestFrameworkConfig
    ) -> TestExecutionResult:
        """执行单个测试框架"""
        print(f"  🧪 执行: {framework.description}")

        start_time = time.time()
        script_path = os.path.join(self.project_root, framework.script_path)

        try:
            # 根据脚本类型选择执行方式
            if script_path.endswith(".py"):
                cmd = [sys.executable, script_path, "--project-root", self.project_root]
            elif script_path.endswith(".sh"):
                cmd = ["bash", script_path]
                if self.quick_mode:
                    cmd.append("--quick")
            else:
                raise ValueError(f"Unsupported script type: {script_path}")

            # 执行测试
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=framework.estimated_duration * 2,  # 超时时间为预估时间的2倍
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            # 尝试提取报告文件路径
            report_file = self._extract_report_file(result.stdout, framework.name)

            # 尝试提取性能指标
            metrics = self._extract_metrics(result.stdout)

            test_result = TestExecutionResult(
                framework_name=framework.name,
                success=success,
                duration=duration,
                output=result.stdout,
                error_output=result.stderr,
                report_file=report_file,
                metrics=metrics,
            )

            # 输出结果
            status_icon = "✅" if success else "❌"
            print(
                f"    {status_icon} {framework.description}: {'成功' if success else '失败'} ({duration:.1f}s)"
            )

            if not success:
                print(f"    📋 错误信息: {result.stderr[:200]}...")

            return test_result

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"    ⏰ {framework.description}: 超时 ({duration:.1f}s)")

            return TestExecutionResult(
                framework_name=framework.name,
                success=False,
                duration=duration,
                output="",
                error_output="Test execution timeout",
                report_file=None,
                metrics={},
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"    ❌ {framework.description}: 执行失败 - {e}")

            return TestExecutionResult(
                framework_name=framework.name,
                success=False,
                duration=duration,
                output="",
                error_output=str(e),
                report_file=None,
                metrics={},
            )

    def _execute_parallel_tests(
        self, frameworks: List[TestFrameworkConfig]
    ) -> Dict[str, TestExecutionResult]:
        """并行执行多个测试框架"""
        print(f"  🔄 并行执行: {', '.join(f.description for f in frameworks)}")

        results = {}

        with ThreadPoolExecutor(max_workers=len(frameworks)) as executor:
            # 提交所有任务
            future_to_framework = {
                executor.submit(self._execute_single_test, framework): framework
                for framework in frameworks
            }

            # 收集结果
            for future in as_completed(future_to_framework):
                framework = future_to_framework[future]
                try:
                    result = future.result()
                    results[framework.name] = result
                except Exception as e:
                    print(f"    ❌ {framework.description}: 并行执行失败 - {e}")
                    results[framework.name] = TestExecutionResult(
                        framework_name=framework.name,
                        success=False,
                        duration=0,
                        output="",
                        error_output=str(e),
                        report_file=None,
                        metrics={},
                    )

        return results

    def _extract_report_file(self, output: str, framework_name: str) -> Optional[str]:
        """从输出中提取报告文件路径"""
        # 查找常见的报告文件路径模式
        patterns = [
            "报告已生成:",
            "报告保存在:",
            "Report generated:",
            "Report saved to:",
            f"{framework_name}_report_",
            "report_",
        ]

        lines = output.split("\n")
        for line in lines:
            for pattern in patterns:
                if pattern in line:
                    # 尝试提取文件路径
                    parts = line.split()
                    for part in parts:
                        if ".md" in part or ".html" in part or ".txt" in part:
                            return part.strip()

        return None

    def _extract_metrics(self, output: str) -> Dict[str, Any]:
        """从输出中提取性能指标"""
        metrics = {}

        lines = output.split("\n")
        for line in lines:
            # 查找指标模式
            if "平均执行时间:" in line:
                try:
                    value = line.split(":")[1].strip().replace("ms", "")
                    metrics["avg_execution_time_ms"] = float(value)
                except:
                    pass

            elif "成功率:" in line:
                try:
                    value = line.split(":")[1].strip().replace("%", "")
                    metrics["success_rate"] = float(value)
                except:
                    pass

            elif "内存使用:" in line:
                try:
                    value = line.split(":")[1].strip().replace("MB", "")
                    metrics["memory_usage_mb"] = float(value)
                except:
                    pass

        return metrics

    def _generate_comprehensive_report(
        self, results: Dict[str, TestExecutionResult], total_time: float
    ) -> str:
        """生成综合测试报告"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(
            self.reports_dir, f"comprehensive_test_report_{timestamp}.md"
        )

        # 统计数据
        total_tests = len(results)
        successful_tests = sum(1 for r in results.values() if r.success)
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        # 按类别分组
        category_stats = {}
        for framework_name, result in results.items():
            framework = self.test_frameworks.get(framework_name)
            if framework:
                category = framework.category
                if category not in category_stats:
                    category_stats[category] = {
                        "total": 0,
                        "successful": 0,
                        "duration": 0,
                    }

                category_stats[category]["total"] += 1
                if result.success:
                    category_stats[category]["successful"] += 1
                category_stats[category]["duration"] += result.duration

        # 生成报告内容
        report_content = f"""# Claude Enhancer 5.0 - 综合测试报告

**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**测试执行器**: Comprehensive Test Runner
**项目路径**: {self.project_root}
**执行时长**: {total_time:.2f}秒

## 📊 执行摘要

### 整体测试结果
"""

        # 计算整体评级
        if success_rate >= 95 and failed_tests == 0:
            grade = "A+ (优秀)"
            grade_emoji = "🌟"
        elif success_rate >= 90:
            grade = "A (良好)"
            grade_emoji = "✅"
        elif success_rate >= 80:
            grade = "B (及格)"
            grade_emoji = "⚠️"
        elif success_rate >= 70:
            grade = "C (需改进)"
            grade_emoji = "❌"
        else:
            grade = "D (不合格)"
            grade_emoji = "🚨"

        report_content += f"""
{grade_emoji} **整体评级**: {grade}
📈 **成功率**: {success_rate:.1f}%
✅ **成功测试**: {successful_tests}
❌ **失败测试**: {failed_tests}
⏱️ **总执行时间**: {total_time:.1f}秒

| 指标 | 数值 | 状态 |
|------|------|------|
| 总测试框架 | {total_tests} | - |
| 成功执行 | {successful_tests} | {'✅' if successful_tests == total_tests else '⚠️'} |
| 失败执行 | {failed_tests} | {'✅' if failed_tests == 0 else '❌'} |
| 平均执行时间 | {total_time/total_tests:.1f}秒 | {'✅' if total_time/total_tests < 300 else '⚠️'} |

## 🧪 测试框架结果

### 详细执行结果

| 测试框架 | 描述 | 状态 | 执行时间 | 报告文件 |
|---------|------|------|----------|----------|
"""

        for framework_name, result in results.items():
            framework = self.test_frameworks.get(
                framework_name,
                TestFrameworkConfig(
                    name=framework_name,
                    description="Unknown",
                    script_path="",
                    category="unknown",
                    priority=5,
                    estimated_duration=0,
                    dependencies=[],
                    parallel_safe=True,
                ),
            )

            status_icon = "✅" if result.success else "❌"
            report_link = f"[报告]({result.report_file})" if result.report_file else "无"

            report_content += f"| {framework.description} | {framework.category} | {status_icon} | {result.duration:.1f}s | {report_link} |\n"

        report_content += f"""
### 按类别统计

"""

        for category, stats in category_stats.items():
            category_success_rate = (
                (stats["successful"] / stats["total"] * 100)
                if stats["total"] > 0
                else 0
            )
            status_icon = (
                "✅"
                if category_success_rate >= 90
                else "⚠️"
                if category_success_rate >= 70
                else "❌"
            )

            report_content += f"""
#### {category.upper()} 测试
- **成功率**: {category_success_rate:.1f}% ({stats['successful']}/{stats['total']}) {status_icon}
- **总耗时**: {stats['duration']:.1f}秒
- **平均耗时**: {stats['duration']/stats['total']:.1f}秒
"""

        report_content += f"""
## 📈 性能指标分析

### 执行时间分析
"""

        # 性能分析
        execution_times = [r.duration for r in results.values()]
        if execution_times:
            fastest_test = min(execution_times)
            slowest_test = max(execution_times)
            avg_test_time = sum(execution_times) / len(execution_times)

            report_content += f"""
- **最快测试**: {fastest_test:.1f}秒
- **最慢测试**: {slowest_test:.1f}秒
- **平均时间**: {avg_test_time:.1f}秒
- **时间标准差**: {(sum((t - avg_test_time)**2 for t in execution_times) / len(execution_times))**0.5:.1f}秒
"""

        # 提取性能指标
        performance_metrics = {}
        for framework_name, result in results.items():
            if result.metrics:
                performance_metrics[framework_name] = result.metrics

        if performance_metrics:
            report_content += f"""
### 性能指标汇总

| 测试框架 | 平均执行时间 | 成功率 | 内存使用 |
|---------|-------------|--------|----------|
"""

            for framework_name, metrics in performance_metrics.items():
                exec_time = metrics.get("avg_execution_time_ms", 0)
                success_rate_metric = metrics.get("success_rate", 0)
                memory_usage = metrics.get("memory_usage_mb", 0)

                report_content += f"| {framework_name} | {exec_time:.2f}ms | {success_rate_metric:.1f}% | {memory_usage:.2f}MB |\n"

        report_content += f"""
## ❌ 失败分析

"""

        failed_results = {
            name: result for name, result in results.items() if not result.success
        }

        if failed_results:
            report_content += "### 失败的测试框架\n\n"

            for framework_name, result in failed_results.items():
                framework = self.test_frameworks.get(framework_name)
                report_content += f"""
#### {framework.description if framework else framework_name}
- **错误信息**: {result.error_output[:200]}{'...' if len(result.error_output) > 200 else ''}
- **执行时间**: {result.duration:.1f}秒
- **建议**: {self._get_failure_recommendation(framework_name, result)}
"""
        else:
            report_content += "✅ **无失败测试** - 所有测试框架都执行成功\n"

        report_content += f"""
## 🎯 改进建议

### 立即处理项
"""

        immediate_actions = []
        long_term_actions = []

        # 分析失败和性能问题
        for framework_name, result in results.items():
            framework = self.test_frameworks.get(framework_name)

            if not result.success:
                immediate_actions.append(
                    f"修复 {framework.description if framework else framework_name} 的执行问题"
                )

            elif (
                result.duration > framework.estimated_duration * 1.5
                if framework
                else False
            ):
                long_term_actions.append(f"优化 {framework.description} 的执行性能")

        if immediate_actions:
            for action in immediate_actions:
                report_content += f"- {action}\n"
        else:
            report_content += "✅ **无需立即处理的问题**\n"

        report_content += f"""
### 长期优化建议
"""

        if long_term_actions:
            for action in long_term_actions:
                report_content += f"- {action}\n"
        else:
            report_content += "- 继续保持当前优秀的测试执行状态\n"

        report_content += f"""
- 考虑增加更多并行安全的测试框架
- 实施测试结果缓存机制
- 建立测试性能回归监控
- 扩展CI/CD集成能力

## 🚀 CI/CD 集成

### Jenkins Pipeline 示例
```groovy
pipeline {{
    agent any
    stages {{
        stage('Comprehensive Tests') {{
            steps {{
                sh 'python test/comprehensive_test_runner.py --quick'
            }}
        }}
    }}
    post {{
        always {{
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'test/comprehensive_reports',
                reportFiles: '*.md',
                reportName: 'Test Report'
            ])
        }}
    }}
}}
```

### GitHub Actions 示例
```yaml
name: Comprehensive Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Run comprehensive tests
      run: python test/comprehensive_test_runner.py
    - name: Upload test reports
      uses: actions/upload-artifact@v2
      with:
        name: test-reports
        path: test/comprehensive_reports/
```

## 🏆 结论

### 测试质量评估
{grade_emoji} **整体评级**: {grade}

### 关键发现
"""

        key_findings = []

        if success_rate >= 95:
            key_findings.append("✅ 测试执行质量优秀，所有框架运行稳定")
        elif success_rate >= 90:
            key_findings.append("👍 测试执行质量良好，少数框架需要关注")
        else:
            key_findings.append("⚠️ 测试执行质量需要改进，多个框架存在问题")

        if failed_tests == 0:
            key_findings.append("✅ 所有测试框架都成功执行")
        else:
            key_findings.append(f"🔧 {failed_tests}个测试框架需要修复")

        if (
            total_time
            < sum(f.estimated_duration for f in self.test_frameworks.values()) * 0.8
        ):
            key_findings.append("⚡ 测试执行效率优秀")
        else:
            key_findings.append("🐌 测试执行效率需要优化")

        for finding in key_findings:
            report_content += f"- {finding}\n"

        report_content += f"""
### 部署建议
"""

        if grade.startswith("A"):
            report_content += "**✅ 推荐部署**: 所有测试都通过，系统质量优秀，可以安全部署到生产环境。\n"
        elif grade.startswith("B"):
            report_content += "**👌 可以部署**: 大部分测试通过，建议修复失败的测试后部署。\n"
        elif grade.startswith("C"):
            report_content += "**⚠️ 谨慎部署**: 存在较多问题，建议先修复关键问题再考虑部署。\n"
        else:
            report_content += "**🛑 不建议部署**: 测试失败率过高，需要重大修复才能部署。\n"

        report_content += f"""
---
*报告由 Claude Enhancer Comprehensive Test Runner 自动生成*
*测试工程师: Test Engineer Professional*
*生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""

        # 保存报告
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)

        return report_file

    def _get_failure_recommendation(
        self, framework_name: str, result: TestExecutionResult
    ) -> str:
        """获取失败建议"""
        error_msg = result.error_output.lower()

        if "timeout" in error_msg:
            return "增加超时时间或优化测试执行效率"
        elif "permission" in error_msg:
            return "检查文件权限和执行权限设置"
        elif "module" in error_msg or "import" in error_msg:
            return "检查Python依赖和模块路径"
        elif "command not found" in error_msg:
            return "检查系统依赖和环境配置"
        elif "connection" in error_msg or "network" in error_msg:
            return "检查网络连接和防火墙设置"
        else:
            return "查看详细错误日志，进行具体问题排查"

    def _print_execution_summary(
        self,
        results: Dict[str, TestExecutionResult],
        total_time: float,
        report_file: str,
    ):
        """打印执行摘要"""
        total_tests = len(results)
        successful_tests = sum(1 for r in results.values() if r.success)
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        print("\n" + "=" * 60)
        print("🏆 综合测试执行完成")
        print(f"⏱️ 总执行时间: {total_time:.2f}秒")
        print(f"📊 综合报告: {report_file}")
        print(f"📈 成功率: {success_rate:.1f}%")
        print(f"✅ 成功: {successful_tests}/{total_tests}")

        if failed_tests > 0:
            print(f"❌ 失败: {failed_tests}")
            print("⚠️ 建议: 查看报告了解失败详情")
        else:
            print("🌟 所有测试框架都成功执行!")

        print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Claude Enhancer 5.0 综合测试执行器")
    parser.add_argument("--project-root", help="项目根目录路径")
    parser.add_argument("--parallel", action="store_true", default=True, help="启用并行执行")
    parser.add_argument("--no-parallel", action="store_true", help="禁用并行执行")
    parser.add_argument("--quick", action="store_true", help="快速测试模式")
    parser.add_argument("--framework", help="只运行指定的测试框架")
    parser.add_argument("--list", action="store_true", help="列出所有可用的测试框架")

    args = parser.parse_args()

    try:
        project_root = args.project_root or "/home/xx/dev/Claude Enhancer 5.0"
        orchestrator = TestOrchestrator(project_root)

        if args.list:
            print("📋 可用的测试框架:")
            for name, framework in orchestrator.test_frameworks.items():
                print(
                    f"  - {name}: {framework.description} ({framework.category}, {framework.estimated_duration}s)"
                )
            return

        if args.framework:
            # 运行指定框架
            framework = orchestrator.test_frameworks.get(args.framework)
            if not framework:
                print(f"❌ 未找到测试框架: {args.framework}")
                return

            result = orchestrator._execute_single_test(framework)
            success_icon = "✅" if result.success else "❌"
            print(
                f"{success_icon} {framework.description}: {'成功' if result.success else '失败'}"
            )
            return

        # 运行综合测试
        parallel = args.parallel and not args.no_parallel
        results = orchestrator.run_all_tests(parallel=parallel, quick_mode=args.quick)

        # 返回适当的退出码
        failed_count = sum(1 for r in results.values() if not r.success)
        sys.exit(0 if failed_count == 0 else 1)

    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
