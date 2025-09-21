#!/usr/bin/env python3
"""
Perfect21 自动化测试套件
高质量测试框架 - 像专业的质量检查员团队
"""

import os
import sys
import time
import json
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib
import traceback

# 测试框架依赖
import pytest
import coverage
from memory_profiler import profile
import psutil


@dataclass
class TestResult:
    """测试结果数据类"""
    module: str
    test_name: str
    status: str  # "passed", "failed", "skipped", "error"
    duration: float
    memory_usage: float
    error_message: Optional[str] = None
    coverage_data: Optional[Dict] = None


@dataclass
class TestSuiteMetrics:
    """测试套件指标"""
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    total_duration: float
    coverage_percentage: float
    memory_peak: float
    success_rate: float


class TestLogger:
    """测试日志管理器"""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """设置日志配置"""
        logger = logging.getLogger('perfect21_test_suite')
        logger.setLevel(logging.INFO)

        # 创建日志目录
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # 文件处理器
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)

    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)

    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)


class CoverageAnalyzer:
    """代码覆盖率分析器"""

    def __init__(self, source_dirs: List[str]):
        self.source_dirs = source_dirs
        self.cov = coverage.Coverage()

    def start_coverage(self):
        """开始覆盖率收集"""
        self.cov.start()

    def stop_coverage(self):
        """停止覆盖率收集"""
        self.cov.stop()
        self.cov.save()

    def generate_report(self, output_dir: Path) -> Dict[str, Any]:
        """生成覆盖率报告"""
        output_dir.mkdir(parents=True, exist_ok=True)

        # HTML报告
        html_dir = output_dir / "coverage_html"
        self.cov.html_report(directory=str(html_dir))

        # XML报告 (for CI/CD)
        xml_file = output_dir / "coverage.xml"
        self.cov.xml_report(outfile=str(xml_file))

        # JSON报告
        json_file = output_dir / "coverage.json"
        self.cov.json_report(outfile=str(json_file))

        # 获取覆盖率数据
        total_coverage = self.cov.report()

        return {
            "total_coverage": total_coverage,
            "html_report": str(html_dir),
            "xml_report": str(xml_file),
            "json_report": str(json_file)
        }


class PerformanceProfiler:
    """性能分析器"""

    def __init__(self):
        self.process = psutil.Process()
        self.start_time = None
        self.memory_samples = []

    def start_profiling(self):
        """开始性能分析"""
        self.start_time = time.time()
        self.memory_samples = []
        self._sample_memory()

    def _sample_memory(self):
        """采样内存使用"""
        try:
            memory_info = self.process.memory_info()
            self.memory_samples.append(memory_info.rss / 1024 / 1024)  # MB
        except:
            pass

    def stop_profiling(self) -> Dict[str, float]:
        """停止性能分析并返回结果"""
        end_time = time.time()
        self._sample_memory()

        duration = end_time - self.start_time if self.start_time else 0
        peak_memory = max(self.memory_samples) if self.memory_samples else 0

        return {
            "duration": duration,
            "peak_memory_mb": peak_memory,
            "avg_memory_mb": sum(self.memory_samples) / len(self.memory_samples) if self.memory_samples else 0
        }


class TestModuleRunner:
    """测试模块运行器"""

    def __init__(self, logger: TestLogger):
        self.logger = logger
        self.results = []

    def run_pytest_module(self, module_path: Path, test_config: Dict) -> List[TestResult]:
        """运行pytest模块"""
        self.logger.info(f"🧪 运行测试模块: {module_path}")

        # 构建pytest命令
        cmd = [
            sys.executable, "-m", "pytest",
            str(module_path),
            "-v",
            "--tb=short",
            "--json-report",
            f"--json-report-file={module_path.parent}/test-results.json"
        ]

        # 添加覆盖率参数
        if test_config.get("coverage", True):
            cmd.extend([
                f"--cov={test_config.get('source_dir', 'src')}",
                "--cov-report=term-missing"
            ])

        # 添加性能标记
        if test_config.get("performance_tests", False):
            cmd.append("-m performance")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=test_config.get("timeout", 300)
            )

            return self._parse_pytest_results(module_path, result)

        except subprocess.TimeoutExpired:
            self.logger.error(f"❌ 测试模块超时: {module_path}")
            return [TestResult(
                module=str(module_path),
                test_name="module_timeout",
                status="error",
                duration=test_config.get("timeout", 300),
                memory_usage=0,
                error_message="Test module timed out"
            )]

    def _parse_pytest_results(self, module_path: Path, result: subprocess.CompletedProcess) -> List[TestResult]:
        """解析pytest结果"""
        test_results = []

        # 尝试解析JSON报告
        json_report_path = module_path.parent / "test-results.json"
        if json_report_path.exists():
            try:
                with open(json_report_path, 'r') as f:
                    report_data = json.load(f)

                for test in report_data.get("tests", []):
                    test_results.append(TestResult(
                        module=str(module_path),
                        test_name=test["nodeid"],
                        status=test["outcome"],
                        duration=test.get("duration", 0),
                        memory_usage=0,  # TODO: 从内存分析器获取
                        error_message=test.get("call", {}).get("longrepr", None) if test["outcome"] == "failed" else None
                    ))
            except Exception as e:
                self.logger.error(f"解析测试结果失败: {e}")

        # 如果没有JSON报告，从输出解析
        if not test_results:
            test_results = self._parse_stdout_results(module_path, result)

        return test_results

    def _parse_stdout_results(self, module_path: Path, result: subprocess.CompletedProcess) -> List[TestResult]:
        """从标准输出解析结果"""
        lines = result.stdout.split('\n')
        test_results = []

        for line in lines:
            if '::' in line and any(status in line for status in ['PASSED', 'FAILED', 'SKIPPED', 'ERROR']):
                parts = line.split()
                if len(parts) >= 2:
                    test_name = parts[0]
                    status = parts[1].lower()

                    test_results.append(TestResult(
                        module=str(module_path),
                        test_name=test_name,
                        status=status,
                        duration=0,  # 无法从输出获取
                        memory_usage=0,
                        error_message=None
                    ))

        return test_results


class TestSuiteRunner:
    """测试套件主运行器"""

    def __init__(self, project_root: Path, config: Dict):
        self.project_root = project_root
        self.config = config
        self.logger = TestLogger(project_root / "test-results" / "test-suite.log")
        self.coverage_analyzer = CoverageAnalyzer(config.get("source_dirs", ["src"]))
        self.performance_profiler = PerformanceProfiler()
        self.module_runner = TestModuleRunner(self.logger)
        self.all_results = []

    def run_complete_suite(self) -> TestSuiteMetrics:
        """运行完整测试套件"""
        self.logger.info("🚀 开始Perfect21全面测试套件执行")
        self.logger.info(f"📁 项目根目录: {self.project_root}")

        # 开始性能分析和覆盖率收集
        self.performance_profiler.start_profiling()
        self.coverage_analyzer.start_coverage()

        try:
            # 按优先级运行测试
            self._run_unit_tests()
            self._run_integration_tests()
            self._run_security_tests()
            self._run_performance_tests()
            self._run_e2e_tests()

        except Exception as e:
            self.logger.error(f"💥 测试套件执行失败: {e}")
            self.logger.error(traceback.format_exc())

        finally:
            # 停止分析
            self.coverage_analyzer.stop_coverage()
            perf_data = self.performance_profiler.stop_profiling()

        # 生成报告
        metrics = self._calculate_metrics(perf_data)
        self._generate_comprehensive_report(metrics)

        return metrics

    def _run_unit_tests(self):
        """运行单元测试"""
        self.logger.info("🧪 执行单元测试套件...")

        unit_test_dirs = [
            self.project_root / "test" / "unit",
            self.project_root / "test" / "auth" / "unit"
        ]

        self._run_test_categories(unit_test_dirs, {
            "timeout": 300,
            "coverage": True,
            "parallel": True
        })

    def _run_integration_tests(self):
        """运行集成测试"""
        self.logger.info("🔗 执行集成测试套件...")

        integration_test_dirs = [
            self.project_root / "test" / "integration",
            self.project_root / "test" / "auth" / "integration"
        ]

        self._run_test_categories(integration_test_dirs, {
            "timeout": 600,
            "coverage": True,
            "setup_required": True
        })

    def _run_security_tests(self):
        """运行安全测试"""
        self.logger.info("🔒 执行安全测试套件...")

        security_test_dirs = [
            self.project_root / "test" / "security",
            self.project_root / "test" / "auth" / "security"
        ]

        # 运行安全测试
        self._run_test_categories(security_test_dirs, {
            "timeout": 300,
            "security_focus": True
        })

        # 运行安全扫描
        self._run_security_scans()

    def _run_performance_tests(self):
        """运行性能测试"""
        self.logger.info("⚡ 执行性能测试套件...")

        performance_test_dirs = [
            self.project_root / "test" / "performance",
            self.project_root / "test" / "auth" / "performance"
        ]

        self._run_test_categories(performance_test_dirs, {
            "timeout": 900,
            "performance_tests": True,
            "benchmark": True
        })

    def _run_e2e_tests(self):
        """运行端到端测试"""
        self.logger.info("🎯 执行端到端测试套件...")

        e2e_test_dirs = [
            self.project_root / "test" / "e2e"
        ]

        self._run_test_categories(e2e_test_dirs, {
            "timeout": 1800,
            "browser_required": True
        })

    def _run_test_categories(self, test_dirs: List[Path], config: Dict):
        """运行测试类别"""
        for test_dir in test_dirs:
            if test_dir.exists():
                test_files = list(test_dir.glob("test_*.py"))
                if test_files:
                    self.logger.info(f"📂 运行测试目录: {test_dir}")

                    for test_file in test_files:
                        results = self.module_runner.run_pytest_module(test_file, config)
                        self.all_results.extend(results)
                else:
                    self.logger.warning(f"⚠️  测试目录为空: {test_dir}")
            else:
                self.logger.warning(f"⚠️  测试目录不存在: {test_dir}")

    def _run_security_scans(self):
        """运行安全扫描工具"""
        self.logger.info("🛡️  运行安全扫描...")

        scans = [
            {
                "name": "Bandit安全扫描",
                "cmd": ["bandit", "-r", ".", "-f", "json", "-o", "test-results/bandit-report.json"]
            },
            {
                "name": "Safety依赖检查",
                "cmd": ["safety", "check", "--json", "--output", "test-results/safety-report.json"]
            }
        ]

        for scan in scans:
            try:
                self.logger.info(f"🔍 执行: {scan['name']}")
                subprocess.run(scan["cmd"], cwd=self.project_root, timeout=300)
                self.logger.info(f"✅ {scan['name']} 完成")
            except Exception as e:
                self.logger.error(f"❌ {scan['name']} 失败: {e}")

    def _calculate_metrics(self, perf_data: Dict) -> TestSuiteMetrics:
        """计算测试指标"""
        total_tests = len(self.all_results)
        passed = len([r for r in self.all_results if r.status == "passed"])
        failed = len([r for r in self.all_results if r.status == "failed"])
        skipped = len([r for r in self.all_results if r.status == "skipped"])
        errors = len([r for r in self.all_results if r.status == "error"])

        total_duration = sum(r.duration for r in self.all_results)
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0

        # 生成覆盖率报告
        coverage_report = self.coverage_analyzer.generate_report(
            self.project_root / "test-results" / "coverage"
        )

        return TestSuiteMetrics(
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            total_duration=total_duration,
            coverage_percentage=coverage_report.get("total_coverage", 0),
            memory_peak=perf_data["peak_memory_mb"],
            success_rate=success_rate
        )

    def _generate_comprehensive_report(self, metrics: TestSuiteMetrics):
        """生成综合测试报告"""
        report_dir = self.project_root / "test-results"
        report_dir.mkdir(parents=True, exist_ok=True)

        # 生成JSON报告
        json_report = {
            "timestamp": time.time(),
            "metrics": asdict(metrics),
            "detailed_results": [asdict(r) for r in self.all_results],
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "working_directory": str(self.project_root)
            }
        }

        with open(report_dir / "comprehensive-report.json", "w") as f:
            json.dump(json_report, f, indent=2)

        # 生成HTML报告
        self._generate_html_report(metrics, report_dir)

        # 打印摘要
        self._print_summary(metrics)

    def _generate_html_report(self, metrics: TestSuiteMetrics, report_dir: Path):
        """生成HTML报告"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Perfect21 测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2196F3; color: white; padding: 20px; border-radius: 5px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
        .metric {{ background: #f5f5f5; padding: 15px; border-radius: 5px; text-align: center; }}
        .metric h3 {{ margin: 0; color: #333; }}
        .metric .value {{ font-size: 24px; font-weight: bold; color: #2196F3; }}
        .status-passed {{ color: #4CAF50; }}
        .status-failed {{ color: #F44336; }}
        .status-skipped {{ color: #FF9800; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Perfect21 综合测试报告</h1>
        <p>生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="metrics">
        <div class="metric">
            <h3>总测试数</h3>
            <div class="value">{metrics.total_tests}</div>
        </div>
        <div class="metric">
            <h3>成功率</h3>
            <div class="value">{metrics.success_rate:.1f}%</div>
        </div>
        <div class="metric">
            <h3>覆盖率</h3>
            <div class="value">{metrics.coverage_percentage:.1f}%</div>
        </div>
        <div class="metric">
            <h3>执行时间</h3>
            <div class="value">{metrics.total_duration:.1f}s</div>
        </div>
    </div>

    <h2>📊 测试结果详情</h2>
    <table>
        <tr>
            <th>状态</th>
            <th>数量</th>
            <th>百分比</th>
        </tr>
        <tr class="status-passed">
            <td>✅ 通过</td>
            <td>{metrics.passed}</td>
            <td>{(metrics.passed/metrics.total_tests*100):.1f}%</td>
        </tr>
        <tr class="status-failed">
            <td>❌ 失败</td>
            <td>{metrics.failed}</td>
            <td>{(metrics.failed/metrics.total_tests*100):.1f}%</td>
        </tr>
        <tr class="status-skipped">
            <td>⏭️ 跳过</td>
            <td>{metrics.skipped}</td>
            <td>{(metrics.skipped/metrics.total_tests*100):.1f}%</td>
        </tr>
    </table>

    <h2>📈 性能指标</h2>
    <p>峰值内存使用: {metrics.memory_peak:.1f} MB</p>
    <p>平均测试执行时间: {(metrics.total_duration/metrics.total_tests):.2f}s</p>

</body>
</html>
        """

        with open(report_dir / "test-report.html", "w", encoding="utf-8") as f:
            f.write(html_content)

    def _print_summary(self, metrics: TestSuiteMetrics):
        """打印测试摘要"""
        print("\n" + "="*60)
        print("🎯 Perfect21 测试套件执行完成")
        print("="*60)

        if metrics.success_rate >= 95:
            print("🎉 测试结果: 优秀")
        elif metrics.success_rate >= 85:
            print("✅ 测试结果: 良好")
        else:
            print("⚠️  测试结果: 需要改进")

        print(f"📊 总计: {metrics.total_tests} 个测试")
        print(f"✅ 通过: {metrics.passed} 个 ({metrics.passed/metrics.total_tests*100:.1f}%)")
        print(f"❌ 失败: {metrics.failed} 个 ({metrics.failed/metrics.total_tests*100:.1f}%)")
        print(f"⏭️  跳过: {metrics.skipped} 个 ({metrics.skipped/metrics.total_tests*100:.1f}%)")
        print(f"📈 成功率: {metrics.success_rate:.1f}%")
        print(f"📊 覆盖率: {metrics.coverage_percentage:.1f}%")
        print(f"⏱️  总耗时: {metrics.total_duration:.1f}s")
        print(f"💾 峰值内存: {metrics.memory_peak:.1f}MB")
        print("="*60)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Perfect21 自动化测试套件")
    parser.add_argument("--project-root", type=str, default=".", help="项目根目录")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--categories", nargs="+",
                       choices=["unit", "integration", "security", "performance", "e2e"],
                       help="要运行的测试类别")

    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    # 默认配置
    config = {
        "source_dirs": ["src", "backend", "auth-system"],
        "test_timeout": 1800,
        "coverage_threshold": 85,
        "performance_threshold": {
            "max_response_time": 200,
            "max_memory_usage": 512
        }
    }

    # 加载自定义配置
    if args.config and Path(args.config).exists():
        with open(args.config, 'r') as f:
            custom_config = json.load(f)
            config.update(custom_config)

    # 运行测试套件
    runner = TestSuiteRunner(project_root, config)
    metrics = runner.run_complete_suite()

    # 根据结果设置退出码
    if metrics.success_rate >= 95 and metrics.coverage_percentage >= config["coverage_threshold"]:
        print("🎉 所有质量标准通过！")
        sys.exit(0)
    elif metrics.failed == 0:
        print("⚠️  质量标准部分通过")
        sys.exit(1)
    else:
        print("❌ 质量标准未通过")
        sys.exit(2)


if __name__ == "__main__":
    main()