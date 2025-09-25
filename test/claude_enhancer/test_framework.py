#!/usr/bin/env python3
"""
Claude Enhancer 升级版测试框架
准确、全面的性能测试工具，确保测试结果真实反映系统性能
"""

import os
import time
import subprocess
import json
import sys
import threading
import psutil
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import statistics
from contextlib import contextmanager
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
import logging


@dataclass
class TestResult:
    """测试结果数据类"""

    test_name: str
    description: str
    success: bool
    execution_time: float
    memory_peak: Optional[float] = None
    cpu_percent: Optional[float] = None
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BenchmarkSuite:
    """基准测试套件"""

    name: str
    description: str
    tests: List[TestResult]
    baseline_time: Optional[float] = None
    performance_target: Optional[float] = None


class SystemMonitor:
    """系统资源监控器"""

    def __init__(self):
        self.monitoring = False
        self.metrics = {
            "cpu_percent": [],
            "memory_percent": [],
            "memory_mb": [],
            "disk_io": [],
            "network_io": [],
        }
        self.monitor_thread = None

    def start_monitoring(self, interval: float = 0.1):
        """开始监控系统资源"""
        self.monitoring = True
        self.metrics = {key: [] for key in self.metrics.keys()}

        def monitor():
            while self.monitoring:
                try:
                    # CPU使用率
                    cpu_percent = psutil.cpu_percent(interval=None)
                    self.metrics["cpu_percent"].append(cpu_percent)

                    # 内存使用
                    memory = psutil.virtual_memory()
                    self.metrics["memory_percent"].append(memory.percent)
                    self.metrics["memory_mb"].append(memory.used / 1024 / 1024)

                    # 磁盘IO
                    disk_io = psutil.disk_io_counters()
                    if disk_io:
                        self.metrics["disk_io"].append(
                            disk_io.read_bytes + disk_io.write_bytes
                        )

                    # 网络IO
                    net_io = psutil.net_io_counters()
                    if net_io:
                        self.metrics["network_io"].append(
                            net_io.bytes_sent + net_io.bytes_recv
                        )

                    time.sleep(interval)
                except Exception:
                    pass

        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self) -> Dict[str, float]:
        """停止监控并返回统计数据"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)

        stats = {}
        for key, values in self.metrics.items():
            if values:
                stats[f"{key}_avg"] = statistics.mean(values)
                stats[f"{key}_max"] = max(values)
                stats[f"{key}_min"] = min(values)

        return stats


class AccurateTestRunner:
    """准确的测试运行器"""

    def __init__(self, claude_dir: str = "/home/xx/dev/Claude_Enhancer/.claude"):
        self.claude_dir = Path(claude_dir)
        self.project_dir = self.claude_dir.parent
        self.temp_dir = None
        self.setup_logging()

    def setup_logging(self):
        """设置日志记录"""
        log_dir = self.project_dir / "test" / "claude_enhancer" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(
                    log_dir / f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                ),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    @contextmanager
    def isolated_environment(self):
        """创建隔离的测试环境"""
        self.temp_dir = tempfile.mkdtemp(prefix="claude_test_")
        try:
            # 复制必要的配置文件到临时目录
            test_claude_dir = Path(self.temp_dir) / ".claude"
            test_claude_dir.mkdir(parents=True)

            # 复制关键配置文件
            config_files = ["settings.json", "config.yaml"]
            for config_file in config_files:
                src = self.claude_dir / config_file
                if src.exists():
                    shutil.copy2(src, test_claude_dir / config_file)

            yield test_claude_dir
        finally:
            if self.temp_dir and Path(self.temp_dir).exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_command_with_monitoring(
        self,
        command: str,
        timeout: float = 30.0,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> TestResult:
        """运行命令并监控资源使用"""

        monitor = SystemMonitor()
        start_time = time.perf_counter()

        try:
            # 开始资源监控
            monitor.start_monitoring()

            # 准备环境
            test_env = os.environ.copy()
            if env:
                test_env.update(env)

            # 运行命令
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd or self.project_dir,
                env=test_env,
            )

            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return_code = process.returncode
                success = return_code == 0

            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

                stdout, stderr = "TIMEOUT", "Command timed out"
                return_code = -1
                success = False

        except Exception as e:
            stdout, stderr = "", str(e)
            return_code = -1
            success = False

        finally:
            end_time = time.perf_counter()
            execution_time = end_time - start_time

            # 停止监控并获取统计数据
            system_stats = monitor.stop_monitoring()

        return TestResult(
            test_name=command,
            description=f"Command: {command}",
            success=success,
            execution_time=execution_time,
            memory_peak=system_stats.get("memory_mb_max"),
            cpu_percent=system_stats.get("cpu_percent_avg"),
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            metadata=system_stats,
        )

    def verify_file_exists_and_executable(self, file_path: Path) -> bool:
        """验证文件存在且可执行"""
        if not file_path.exists():
            self.logger.warning(f"File does not exist: {file_path}")
            return False

        if not os.access(file_path, os.R_OK):
            self.logger.warning(f"File not readable: {file_path}")
            return False

        # 如果是脚本文件，检查是否可执行
        if file_path.suffix in [".sh", ".py"]:
            if not os.access(file_path, os.X_OK):
                try:
                    os.chmod(file_path, 0o755)
                    self.logger.info(f"Made file executable: {file_path}")
                except OSError as e:
                    self.logger.error(
                        f"Failed to make file executable: {file_path}, error: {e}"
                    )
                    return False

        return True

    def test_hook_system_accuracy(self) -> List[TestResult]:
        """精确测试Hook系统"""
        results = []

        # 获取所有实际存在的Hook文件
        hook_files = []
        hooks_dir = self.claude_dir / "hooks"

        if hooks_dir.exists():
            for hook_file in hooks_dir.glob("*.sh"):
                if self.verify_file_exists_and_executable(hook_file):
                    hook_files.append(hook_file)

        self.logger.info(f"Found {len(hook_files)} executable hook files")

        for hook_file in hook_files:
            # 测试Hook的基本功能
            test_commands = [
                f"bash {hook_file} --help",
                f"bash {hook_file} --test",
                f"bash {hook_file} --dry-run",
            ]

            for cmd in test_commands:
                result = self.run_command_with_monitoring(
                    cmd,
                    timeout=10.0,
                    env={"CLAUDE_TEST_MODE": "1", "HOOK_TEST_MODE": "1"},
                )
                result.test_name = f"hook_{hook_file.name}_{cmd.split()[-1]}"
                result.description = (
                    f"Testing {hook_file.name} with {cmd.split()[-1]} flag"
                )
                results.append(result)

        return results

    def test_performance_scripts_accuracy(self) -> List[TestResult]:
        """精确测试性能脚本"""
        results = []

        scripts_dir = self.claude_dir / "scripts"
        performance_scripts = []

        if scripts_dir.exists():
            # 查找所有性能相关的脚本
            for script_file in scripts_dir.glob("*performance*.sh"):
                if self.verify_file_exists_and_executable(script_file):
                    performance_scripts.append(script_file)

            for script_file in scripts_dir.glob("*benchmark*.sh"):
                if self.verify_file_exists_and_executable(script_file):
                    performance_scripts.append(script_file)

        self.logger.info(f"Found {len(performance_scripts)} performance script files")

        for script_file in performance_scripts:
            # 使用隔离环境测试
            with self.isolated_environment() as test_env_dir:
                result = self.run_command_with_monitoring(
                    f"bash {script_file}",
                    timeout=30.0,
                    env={
                        "CLAUDE_TEST_MODE": "1",
                        "PERFORMANCE_TEST_MODE": "1",
                        "CLAUDE_DIR": str(test_env_dir),
                    },
                )
                result.test_name = f"perf_script_{script_file.name}"
                result.description = f"Performance test of {script_file.name}"
                results.append(result)

        return results

    def run_baseline_benchmarks(self) -> BenchmarkSuite:
        """运行基准测试"""
        baseline_tests = []

        # 基本系统操作基准
        basic_operations = [
            ("echo 'test'", "Basic shell command"),
            ("ls /tmp", "Directory listing"),
            ("date", "System date"),
            ("whoami", "User identification"),
            ("pwd", "Working directory"),
        ]

        for cmd, desc in basic_operations:
            result = self.run_command_with_monitoring(cmd, timeout=5.0)
            result.test_name = f"baseline_{cmd.replace(' ', '_').replace(chr(39), '')}"
            result.description = desc
            baseline_tests.append(result)

        # 文件系统操作基准
        with tempfile.TemporaryDirectory() as temp_dir:
            file_operations = [
                (f"touch {temp_dir}/test_file", "File creation"),
                (f"echo 'test content' > {temp_dir}/test_file", "File write"),
                (f"cat {temp_dir}/test_file", "File read"),
                (f"rm {temp_dir}/test_file", "File deletion"),
            ]

            for cmd, desc in file_operations:
                result = self.run_command_with_monitoring(cmd, timeout=5.0)
                result.test_name = f"fs_baseline_{desc.lower().replace(' ', '_')}"
                result.description = desc
                baseline_tests.append(result)

        return BenchmarkSuite(
            name="Baseline System Operations",
            description="Basic system operations to establish performance baseline",
            tests=baseline_tests,
            baseline_time=statistics.mean(
                [t.execution_time for t in baseline_tests if t.success]
            ),
        )

    def run_stress_tests(self, iterations: int = 10) -> List[TestResult]:
        """运行压力测试"""
        stress_results = []

        # Hook系统压力测试
        hook_files = list((self.claude_dir / "hooks").glob("*.sh"))
        executable_hooks = [
            h for h in hook_files if self.verify_file_exists_and_executable(h)
        ]

        if executable_hooks:
            # 选择一个轻量级的Hook进行压力测试
            test_hook = executable_hooks[0]

            for i in range(iterations):
                result = self.run_command_with_monitoring(
                    f"bash {test_hook} --test",
                    timeout=5.0,
                    env={"CLAUDE_TEST_MODE": "1", "STRESS_TEST_ITERATION": str(i)},
                )
                result.test_name = f"stress_hook_{i:03d}"
                result.description = f"Stress test iteration {i+1}/{iterations}"
                stress_results.append(result)

        return stress_results

    def analyze_test_consistency(self, results: List[TestResult]) -> Dict[str, Any]:
        """分析测试结果的一致性"""
        analysis = {
            "total_tests": len(results),
            "successful_tests": sum(1 for r in results if r.success),
            "failed_tests": sum(1 for r in results if not r.success),
            "success_rate": 0.0,
            "execution_times": [],
            "consistency_score": 0.0,
            "outliers": [],
        }

        if analysis["total_tests"] > 0:
            analysis["success_rate"] = (
                analysis["successful_tests"] / analysis["total_tests"]
            )

        # 分析执行时间
        execution_times = [r.execution_time for r in results if r.success]
        if execution_times:
            analysis["execution_times"] = {
                "mean": statistics.mean(execution_times),
                "median": statistics.median(execution_times),
                "std_dev": statistics.stdev(execution_times)
                if len(execution_times) > 1
                else 0,
                "min": min(execution_times),
                "max": max(execution_times),
            }

            # 检测异常值（超出2个标准差）
            if len(execution_times) > 1:
                mean_time = analysis["execution_times"]["mean"]
                std_dev = analysis["execution_times"]["std_dev"]

                for i, result in enumerate(results):
                    if (
                        result.success
                        and abs(result.execution_time - mean_time) > 2 * std_dev
                    ):
                        analysis["outliers"].append(
                            {
                                "test_name": result.test_name,
                                "execution_time": result.execution_time,
                                "deviation": abs(result.execution_time - mean_time)
                                / std_dev,
                            }
                        )

            # 计算一致性分数（基于标准差）
            if analysis["execution_times"]["mean"] > 0:
                cv = (
                    analysis["execution_times"]["std_dev"]
                    / analysis["execution_times"]["mean"]
                )
                analysis["consistency_score"] = max(0, 1 - cv)  # 变异系数越小，一致性越高

        return analysis


class ComprehensiveTestSuite:
    """综合测试套件"""

    def __init__(self, claude_dir: str = "/home/xx/dev/Claude_Enhancer/.claude"):
        self.runner = AccurateTestRunner(claude_dir)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_environment": self.get_test_environment(),
            "baseline_suite": None,
            "hook_tests": [],
            "performance_tests": [],
            "stress_tests": [],
            "unit_tests": [],
            "integration_tests": [],
            "analysis": {},
            "recommendations": [],
        }

    def get_test_environment(self) -> Dict[str, Any]:
        """获取测试环境信息"""
        return {
            "python_version": sys.version,
            "platform": sys.platform,
            "cpu_count": os.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "disk_free_gb": psutil.disk_usage("/").free / (1024**3),
            "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
        }

    def run_unit_tests(self) -> List[TestResult]:
        """运行单元测试"""
        unit_results = []

        # 测试配置文件解析
        config_files = [
            self.runner.claude_dir / "settings.json",
            self.runner.claude_dir / "config.yaml",
        ]

        for config_file in config_files:
            if config_file.exists():
                if config_file.suffix == ".json":
                    cmd = (
                        f"python3 -c 'import json; json.load(open(\"{config_file}\"))'"
                    )
                elif config_file.suffix in [".yaml", ".yml"]:
                    cmd = f"python3 -c 'import yaml; yaml.safe_load(open(\"{config_file}\"))'"
                else:
                    continue

                result = self.runner.run_command_with_monitoring(cmd, timeout=5.0)
                result.test_name = f"unit_config_parse_{config_file.name}"
                result.description = f"Parse configuration file {config_file.name}"
                unit_results.append(result)

        return unit_results

    def run_integration_tests(self) -> List[TestResult]:
        """运行集成测试"""
        integration_results = []

        # 测试Hook系统与配置的集成
        settings_file = self.runner.claude_dir / "settings.json"
        if settings_file.exists():
            # 验证Hook配置的完整性
            cmd = f"""
            python3 -c "
import json
import os
settings_path = '{settings_file}'
if os.path.exists(settings_path):
    with open(settings_path) as f:
        settings = json.load(f)
    hooks = settings.get('hooks', {{}})
    for hook_type, hook_list in hooks.items():
        if isinstance(hook_list, list):
            for hook in hook_list:
                if 'command' in hook:
                    print(f'Hook found: {{hook_type}} -> {{hook[\"command\"]}}')
print('Integration test completed')
"
            """

            result = self.runner.run_command_with_monitoring(cmd, timeout=10.0)
            result.test_name = "integration_hook_config"
            result.description = "Verify hook system configuration integration"
            integration_results.append(result)

        return integration_results

    def run_full_test_suite(self) -> Dict[str, Any]:
        """运行完整的测试套件"""
        print("🧪 开始运行综合测试套件...")
        print("=" * 80)

        # 1. 建立基准线
        print("📊 建立性能基准线...")
        self.results["baseline_suite"] = self.runner.run_baseline_benchmarks()

        # 2. 单元测试
        print("🔬 运行单元测试...")
        self.results["unit_tests"] = self.run_unit_tests()

        # 3. Hook系统测试
        print("🔗 测试Hook系统...")
        self.results["hook_tests"] = self.runner.test_hook_system_accuracy()

        # 4. 性能脚本测试
        print("⚡ 测试性能脚本...")
        self.results[
            "performance_tests"
        ] = self.runner.test_performance_scripts_accuracy()

        # 5. 集成测试
        print("🔄 运行集成测试...")
        self.results["integration_tests"] = self.run_integration_tests()

        # 6. 压力测试
        print("💪 运行压力测试...")
        self.results["stress_tests"] = self.runner.run_stress_tests(iterations=5)

        # 7. 分析结果
        print("📈 分析测试结果...")
        self.analyze_all_results()

        # 8. 生成建议
        print("💡 生成优化建议...")
        self.generate_recommendations()

        print("✅ 测试套件执行完成!")
        return self.results

    def analyze_all_results(self):
        """分析所有测试结果"""
        all_tests = []

        # 收集所有测试结果
        if self.results["baseline_suite"]:
            all_tests.extend(self.results["baseline_suite"].tests)
        all_tests.extend(self.results["unit_tests"])
        all_tests.extend(self.results["hook_tests"])
        all_tests.extend(self.results["performance_tests"])
        all_tests.extend(self.results["integration_tests"])
        all_tests.extend(self.results["stress_tests"])

        # 总体分析
        self.results["analysis"]["overall"] = self.runner.analyze_test_consistency(
            all_tests
        )

        # 分类分析
        categories = {
            "unit_tests": self.results["unit_tests"],
            "hook_tests": self.results["hook_tests"],
            "performance_tests": self.results["performance_tests"],
            "integration_tests": self.results["integration_tests"],
            "stress_tests": self.results["stress_tests"],
        }

        for category, tests in categories.items():
            if tests:
                self.results["analysis"][
                    category
                ] = self.runner.analyze_test_consistency(tests)

    def generate_recommendations(self):
        """生成优化建议"""
        recommendations = []

        # 基于分析结果生成建议
        overall_analysis = self.results["analysis"].get("overall", {})

        # 成功率建议
        success_rate = overall_analysis.get("success_rate", 0)
        if success_rate < 0.9:
            recommendations.append(
                {
                    "category": "Reliability",
                    "priority": "HIGH",
                    "issue": f"整体测试成功率较低: {success_rate:.1%}",
                    "recommendation": "需要检查失败的测试用例，修复潜在问题",
                    "action_items": ["检查测试环境配置", "验证依赖项是否齐全", "修复失败的脚本或配置"],
                }
            )

        # 性能一致性建议
        consistency_score = overall_analysis.get("consistency_score", 0)
        if consistency_score < 0.8:
            recommendations.append(
                {
                    "category": "Performance Consistency",
                    "priority": "MEDIUM",
                    "issue": f"测试执行时间变化较大，一致性分数: {consistency_score:.2f}",
                    "recommendation": "优化测试环境稳定性，减少性能波动",
                    "action_items": ["检查系统负载", "优化资源争用", "考虑使用更稳定的测试环境"],
                }
            )

        # 异常值建议
        outliers = overall_analysis.get("outliers", [])
        if outliers:
            recommendations.append(
                {
                    "category": "Performance Outliers",
                    "priority": "MEDIUM",
                    "issue": f"发现 {len(outliers)} 个执行时间异常的测试",
                    "recommendation": "调查异常测试用例，优化性能瓶颈",
                    "details": outliers[:5],  # 只显示前5个
                    "action_items": ["分析异常测试的具体原因", "优化慢速操作", "考虑增加超时处理"],
                }
            )

        self.results["recommendations"] = recommendations

    def save_detailed_report(
        self, filename: str = "comprehensive_test_report.json"
    ) -> Path:
        """保存详细的测试报告"""
        report_path = self.runner.project_dir / "test" / "claude_enhancer" / filename
        report_path.parent.mkdir(parents=True, exist_ok=True)

        # 转换TestResult对象为字典
        serializable_results = {}

        for key, value in self.results.items():
            if key == "baseline_suite" and value:
                serializable_results[key] = {
                    "name": value.name,
                    "description": value.description,
                    "tests": [asdict(test) for test in value.tests],
                    "baseline_time": value.baseline_time,
                    "performance_target": value.performance_target,
                }
            elif (
                isinstance(value, list)
                and value
                and hasattr(value[0], "__dataclass_fields__")
            ):
                serializable_results[key] = [asdict(item) for item in value]
            else:
                serializable_results[key] = value

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)

        print(f"📄 详细测试报告已保存到: {report_path}")
        return report_path


def main():
    """主函数"""
    try:
        suite = ComprehensiveTestSuite()
        results = suite.run_full_test_suite()
        report_path = suite.save_detailed_report()

        # 打印摘要
        print("\n" + "=" * 80)
        print("📋 测试摘要")
        print("=" * 80)

        overall = results["analysis"].get("overall", {})
        print(f"总测试数量: {overall.get('total_tests', 0)}")
        print(f"成功测试: {overall.get('successful_tests', 0)}")
        print(f"失败测试: {overall.get('failed_tests', 0)}")
        print(f"成功率: {overall.get('success_rate', 0):.1%}")

        exec_times = overall.get("execution_times", {})
        if exec_times:
            print(f"平均执行时间: {exec_times.get('mean', 0):.4f}s")
            print(
                f"执行时间范围: {exec_times.get('min', 0):.4f}s - {exec_times.get('max', 0):.4f}s"
            )
            print(f"一致性分数: {overall.get('consistency_score', 0):.2f}")

        print(f"\n💡 生成了 {len(results.get('recommendations', []))} 条优化建议")
        print(f"📄 详细报告: {report_path}")

        return True

    except Exception as e:
        print(f"❌ 测试套件执行失败: {e}")
        logging.exception("Test suite execution failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
