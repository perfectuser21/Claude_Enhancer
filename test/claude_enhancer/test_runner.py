#!/usr/bin/env python3
"""
Claude Enhancer 测试运行器
统一运行所有测试套件的主控制器
"""

import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import subprocess

# 导入测试套件
try:
    from test_framework import ComprehensiveTestSuite
    from unit_tests import run_tests as run_unit_tests
    from benchmark_suite import ComprehensiveBenchmarkSuite
    from stress_test_suite import ComprehensiveStressTestSuite
except ImportError as e:
    print(f"❌ 导入测试模块失败: {e}")
    print("请确保所有测试文件都在同一目录下")
    sys.exit(1)


class TestOrchestrator:
    """测试编排器 - 统一管理所有测试套件"""

    def __init__(self, claude_dir: str = "/home/xx/dev/Claude_Enhancer/.claude"):
        self.claude_dir = Path(claude_dir)
        self.project_dir = self.claude_dir.parent
        self.test_dir = self.project_dir / "test" / "claude_enhancer"
        self.setup_logging()

        # 测试结果存储
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_environment": self.get_test_environment(),
            "test_suites": {},
            "summary": {},
            "recommendations": [],
            "performance_trends": {},
        }

    def setup_logging(self):
        """设置日志系统"""
        log_dir = self.test_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = (
            log_dir
            / f"test_orchestrator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"测试日志保存到: {log_file}")

    def get_test_environment(self) -> Dict[str, Any]:
        """获取测试环境信息"""
        try:
            import psutil

            env_info = {
                "python_version": sys.version,
                "platform": sys.platform,
                "cpu_count": psutil.cpu_count(),
                "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "memory_available_gb": psutil.virtual_memory().available / (1024**3),
                "disk_total_gb": psutil.disk_usage("/").total / (1024**3),
                "disk_free_gb": psutil.disk_usage("/").free / (1024**3),
                "load_average": getattr(__import__("os"), "getloadavg", lambda: None)(),
                "claude_enhancer_path": str(self.claude_dir),
                "test_time": datetime.now().isoformat(),
            }

            # 检查关键依赖
            dependencies = [
                "psutil",
                "json",
                "subprocess",
                "threading",
                "concurrent.futures",
            ]
            env_info["dependencies_available"] = {}

            for dep in dependencies:
                try:
                    __import__(dep)
                    env_info["dependencies_available"][dep] = True
                except ImportError:
                    env_info["dependencies_available"][dep] = False

            return env_info

        except Exception as e:
            self.logger.error(f"获取环境信息失败: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def run_unit_tests_suite(self) -> Dict[str, Any]:
        """运行单元测试套件"""
        self.logger.info("🧪 开始运行单元测试套件...")
        start_time = time.perf_counter()

        try:
            pass  # Auto-fixed empty block
            # 运行单元测试
            success = run_unit_tests()
            duration = time.perf_counter() - start_time

            result = {
                "suite_name": "unit_tests",
                "success": success,
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
                "details": "详细结果请查看单元测试日志",
            }

            self.logger.info(f"✅ 单元测试完成 - 成功: {success}, 耗时: {duration:.2f}s")
            return result

        except Exception as e:
            duration = time.perf_counter() - start_time
            self.logger.error(f"❌ 单元测试失败: {e}")
            return {
                "suite_name": "unit_tests",
                "success": False,
                "duration": duration,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def run_comprehensive_tests_suite(self) -> Dict[str, Any]:
        """运行综合测试套件"""
        self.logger.info("🔬 开始运行综合测试套件...")
        start_time = time.perf_counter()

        try:
            suite = ComprehensiveTestSuite(str(self.claude_dir))
            results = suite.run_full_test_suite()
            report_path = suite.save_detailed_report()

            duration = time.perf_counter() - start_time

            result = {
                "suite_name": "comprehensive_tests",
                "success": True,
                "duration": duration,
                "results": results,
                "report_path": str(report_path),
                "timestamp": datetime.now().isoformat(),
            }

            self.logger.info(f"✅ 综合测试完成 - 耗时: {duration:.2f}s")
            return result

        except Exception as e:
            duration = time.perf_counter() - start_time
            self.logger.error(f"❌ 综合测试失败: {e}")
            return {
                "suite_name": "comprehensive_tests",
                "success": False,
                "duration": duration,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def run_benchmark_suite(self) -> Dict[str, Any]:
        """运行基准测试套件"""
        self.logger.info("🏃 开始运行基准测试套件...")
        start_time = time.perf_counter()

        try:
            suite = ComprehensiveBenchmarkSuite(str(self.claude_dir))
            results = suite.run_full_benchmark_suite()
            report_path = suite.save_report(results)

            duration = time.perf_counter() - start_time

            result = {
                "suite_name": "benchmark_tests",
                "success": True,
                "duration": duration,
                "results": results,
                "report_path": str(report_path),
                "timestamp": datetime.now().isoformat(),
            }

            self.logger.info(f"✅ 基准测试完成 - 耗时: {duration:.2f}s")
            return result

        except Exception as e:
            duration = time.perf_counter() - start_time
            self.logger.error(f"❌ 基准测试失败: {e}")
            return {
                "suite_name": "benchmark_tests",
                "success": False,
                "duration": duration,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def run_stress_tests_suite(self, duration: float = 120.0) -> Dict[str, Any]:
        """运行压力测试套件"""
        self.logger.info("💪 开始运行压力测试套件...")
        start_time = time.perf_counter()

        try:
            suite = ComprehensiveStressTestSuite(str(self.claude_dir))
            results = suite.run_full_stress_test_suite(duration)
            report_path = suite.save_stress_test_report(results)

            actual_duration = time.perf_counter() - start_time

            result = {
                "suite_name": "stress_tests",
                "success": True,
                "duration": actual_duration,
                "test_duration": duration,
                "results": results,
                "report_path": str(report_path),
                "timestamp": datetime.now().isoformat(),
            }

            self.logger.info(f"✅ 压力测试完成 - 耗时: {actual_duration:.2f}s")
            return result

        except Exception as e:
            actual_duration = time.perf_counter() - start_time
            self.logger.error(f"❌ 压力测试失败: {e}")
            return {
                "suite_name": "stress_tests",
                "success": False,
                "duration": actual_duration,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def run_quick_validation(self) -> Dict[str, Any]:
        """运行快速验证测试"""
        self.logger.info("⚡ 开始运行快速验证测试...")
        start_time = time.perf_counter()

        validation_results = []

        try:
            pass  # Auto-fixed empty block
            # 1. 检查配置文件
            config_files = [
                self.claude_dir / "settings.json",
                self.claude_dir / "config.yaml",
            ]

            for config_file in config_files:
                if config_file.exists():
                    try:
                        if config_file.suffix == ".json":
                            with open(config_file, "r") as f:
                                json.load(f)
                        elif config_file.suffix in [".yaml", ".yml"]:
                            import yaml

                            with open(config_file, "r") as f:
                                yaml.safe_load(f)

                        validation_results.append(
                            {
                                "test": f"config_parse_{config_file.name}",
                                "success": True,
                                "message": f"配置文件 {config_file.name} 解析成功",
                            }
                        )
                    except Exception as e:
                        validation_results.append(
                            {
                                "test": f"config_parse_{config_file.name}",
                                "success": False,
                                "error": str(e),
                            }
                        )

            # 2. 检查Hook文件
            hooks_dir = self.claude_dir / "hooks"
            if hooks_dir.exists():
                hook_count = len(list(hooks_dir.glob("*.sh")))
                validation_results.append(
                    {
                        "test": "hook_files_check",
                        "success": hook_count > 0,
                        "message": f"发现 {hook_count} 个Hook文件",
                    }
                )

                # 检查几个关键Hook
                key_hooks = [
                    "smart_agent_selector.sh",
                    "quality_gate.sh",
                    "performance_monitor.sh",
                ]
                for hook_name in key_hooks:
                    hook_path = hooks_dir / hook_name
                    if hook_path.exists():
                        pass  # Auto-fixed empty block
                        # 语法检查
                        try:
                            result = subprocess.run(
                                ["bash", "-n", str(hook_path)],
                                capture_output=True,
                                text=True,
                                timeout=5,
                            )
                            validation_results.append(
                                {
                                    "test": f"hook_syntax_{hook_name}",
                                    "success": result.returncode == 0,
                                    "message": "语法检查通过"
                                    if result.returncode == 0
                                    else f"语法错误: {result.stderr}",
                                }
                            )
                        except Exception as e:
                            validation_results.append(
                                {
                                    "test": f"hook_syntax_{hook_name}",
                                    "success": False,
                                    "error": str(e),
                                }
                            )

            # 3. 检查Python依赖
            required_packages = ["psutil", "json", "yaml", "subprocess", "threading"]
            for package in required_packages:
                try:
                    __import__(package)
                    validation_results.append(
                        {
                            "test": f"dependency_{package}",
                            "success": True,
                            "message": f"依赖 {package} 可用",
                        }
                    )
                except ImportError:
                    validation_results.append(
                        {
                            "test": f"dependency_{package}",
                            "success": False,
                            "error": f"缺少依赖: {package}",
                        }
                    )

            duration = time.perf_counter() - start_time

            # 统计结果
            total_tests = len(validation_results)
            successful_tests = sum(1 for r in validation_results if r["success"])

            result = {
                "suite_name": "quick_validation",
                "success": successful_tests == total_tests,
                "duration": duration,
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "details": validation_results,
                "timestamp": datetime.now().isoformat(),
            }

            self.logger.info(
                f"✅ 快速验证完成 - 成功: {successful_tests}/{total_tests}, 耗时: {duration:.2f}s"
            )
            return result

        except Exception as e:
            duration = time.perf_counter() - start_time
            self.logger.error(f"❌ 快速验证失败: {e}")
            return {
                "suite_name": "quick_validation",
                "success": False,
                "duration": duration,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def run_all_tests(
        self, include_stress: bool = True, stress_duration: float = 120.0
    ) -> Dict[str, Any]:
        """运行所有测试套件"""
        self.logger.info("🚀 开始运行完整测试套件...")
        overall_start_time = time.perf_counter()

        print("=" * 80)
        print("🧪 Claude Enhancer 综合测试框架")
        print("=" * 80)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试环境: {self.claude_dir}")
        print("=" * 80)

        # 1. 快速验证
        print("\n⚡ Phase 1: 快速验证测试")
        self.results["test_suites"]["quick_validation"] = self.run_quick_validation()

        # 2. 单元测试
        print("\n🧪 Phase 2: 单元测试")
        self.results["test_suites"]["unit_tests"] = self.run_unit_tests_suite()

        # 3. 综合测试
        print("\n🔬 Phase 3: 综合功能测试")
        self.results["test_suites"][
            "comprehensive_tests"
        ] = self.run_comprehensive_tests_suite()

        # 4. 基准测试
        print("\n🏃 Phase 4: 基准性能测试")
        self.results["test_suites"]["benchmark_tests"] = self.run_benchmark_suite()

        # 5. 压力测试（可选）
        if include_stress:
            print(f"\n💪 Phase 5: 压力测试 (持续时间: {stress_duration}s)")
            self.results["test_suites"]["stress_tests"] = self.run_stress_tests_suite(
                stress_duration
            )

        # 6. 生成总结和建议
        print("\n📊 Phase 6: 结果分析和建议生成")
        self.analyze_overall_results()
        self.generate_comprehensive_recommendations()

        overall_duration = time.perf_counter() - overall_start_time
        self.results["total_duration"] = overall_duration

        print("\n" + "=" * 80)
        print("✅ 所有测试套件执行完成!")
        print(f"总耗时: {overall_duration:.2f}秒")
        print("=" * 80)

        return self.results

    def analyze_overall_results(self):
        """分析总体测试结果"""
        summary = {
            "total_suites": len(self.results["test_suites"]),
            "successful_suites": 0,
            "failed_suites": 0,
            "total_duration": 0,
            "suite_details": {},
        }

        for suite_name, suite_result in self.results["test_suites"].items():
            summary["total_duration"] += suite_result.get("duration", 0)

            if suite_result.get("success", False):
                summary["successful_suites"] += 1
            else:
                summary["failed_suites"] += 1

            # 提取每个套件的关键指标
            if suite_name == "quick_validation":
                summary["suite_details"][suite_name] = {
                    "total_tests": suite_result.get("total_tests", 0),
                    "successful_tests": suite_result.get("successful_tests", 0),
                    "success_rate": suite_result.get("successful_tests", 0)
                    / max(suite_result.get("total_tests", 1), 1),
                }
            elif suite_name in [
                "comprehensive_tests",
                "benchmark_tests",
                "stress_tests",
            ]:
                # 从嵌套结果中提取信息
                results = suite_result.get("results", {})
                if isinstance(results, dict):
                    if "analysis" in results:
                        analysis = results["analysis"]
                        if "overall" in analysis:
                            overall = analysis["overall"]
                            summary["suite_details"][suite_name] = {
                                "total_tests": overall.get("total_tests", 0),
                                "successful_tests": overall.get("successful_tests", 0),
                                "success_rate": overall.get("success_rate", 0),
                            }

        summary["overall_success_rate"] = summary["successful_suites"] / max(
            summary["total_suites"], 1
        )
        self.results["summary"] = summary

    def generate_comprehensive_recommendations(self):
        """生成综合建议"""
        recommendations = []

        # 基于总体成功率的建议
        overall_success_rate = self.results["summary"]["overall_success_rate"]
        if overall_success_rate < 0.8:
            recommendations.append(
                {
                    "category": "Overall System Health",
                    "priority": "CRITICAL",
                    "issue": f"测试套件整体成功率较低: {overall_success_rate:.1%}",
                    "recommendation": "需要立即排查系统基础问题",
                    "affected_suites": [
                        name
                        for name, result in self.results["test_suites"].items()
                        if not result.get("success", False)
                    ],
                }
            )

        # 收集各套件的具体建议
        for suite_name, suite_result in self.results["test_suites"].items():
            if not suite_result.get("success", False):
                recommendations.append(
                    {
                        "category": f"{suite_name.title()} Issues",
                        "priority": "HIGH",
                        "issue": f"{suite_name} 测试失败",
                        "recommendation": f"检查 {suite_name} 的具体错误信息并修复",
                        "error": suite_result.get("error", "未知错误"),
                    }
                )

            # 从套件结果中提取具体建议
            if "results" in suite_result and isinstance(suite_result["results"], dict):
                suite_recommendations = suite_result["results"].get(
                    "recommendations", []
                )
                for rec in suite_recommendations:
                    rec["source_suite"] = suite_name
                    recommendations.append(rec)

        # 性能相关建议
        total_duration = self.results["summary"]["total_duration"]
        if total_duration > 300:  # 超过5分钟
            recommendations.append(
                {
                    "category": "Performance",
                    "priority": "MEDIUM",
                    "issue": f"测试执行时间过长: {total_duration:.1f}秒",
                    "recommendation": "考虑优化测试执行效率或并行化测试",
                }
            )

        self.results["recommendations"] = recommendations

    def save_final_report(
        self, filename: str = "claude_enhancer_test_report.json"
    ) -> Path:
        """保存最终测试报告"""
        report_path = self.test_dir / filename
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        self.logger.info(f"📄 最终测试报告已保存到: {report_path}")
        return report_path

    def print_final_summary(self):
        """打印最终摘要"""
        print("\n" + "=" * 80)
        print("📋 Claude Enhancer 测试框架 - 最终摘要")
        print("=" * 80)

        summary = self.results["summary"]
        print(f"测试套件总数: {summary['total_suites']}")
        print(f"成功套件: {summary['successful_suites']}")
        print(f"失败套件: {summary['failed_suites']}")
        print(f"整体成功率: {summary['overall_success_rate']:.1%}")
        print(f"总执行时间: {summary['total_duration']:.2f}秒")

        # 显示各套件详情
        print(f"\n📊 各套件详情:")
        for suite_name, suite_result in self.results["test_suites"].items():
            status = "✅" if suite_result.get("success", False) else "❌"
            duration = suite_result.get("duration", 0)
            print(f"  {status} {suite_name}: {duration:.2f}s")

        # 显示关键建议
        recommendations = self.results.get("recommendations", [])
        critical_recs = [r for r in recommendations if r.get("priority") == "CRITICAL"]
        high_recs = [r for r in recommendations if r.get("priority") == "HIGH"]

        if critical_recs:
            print(f"\n🚨 关键问题 ({len(critical_recs)}个):")
            for rec in critical_recs[:3]:
                print(f"  - {rec['issue']}")

        if high_recs:
            print(f"\n⚠️  重要问题 ({len(high_recs)}个):")
            for rec in high_recs[:3]:
                print(f"  - {rec['issue']}")

        print(f"\n💡 总建议数: {len(recommendations)}")
        print("=" * 80)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Claude Enhancer 测试框架")
    parser.add_argument(
        "--claude-dir",
        default="/home/xx/dev/Claude_Enhancer/.claude",
        help="Claude目录路径",
    )
    parser.add_argument("--quick", action="store_true", help="只运行快速验证测试")
    parser.add_argument("--no-stress", action="store_true", help="跳过压力测试")
    parser.add_argument(
        "--stress-duration", type=float, default=120.0, help="压力测试持续时间（秒）"
    )
    parser.add_argument(
        "--suite",
        choices=["unit", "comprehensive", "benchmark", "stress", "validation"],
        help="只运行指定的测试套件",
    )

    args = parser.parse_args()

    try:
        orchestrator = TestOrchestrator(args.claude_dir)

        if args.quick:
            pass  # Auto-fixed empty block
            # 只运行快速验证
            result = orchestrator.run_quick_validation()
            print("\n⚡ 快速验证结果:")
            print(f"成功: {result['successful_tests']}/{result['total_tests']}")
            return result["success"]

        elif args.suite:
            pass  # Auto-fixed empty block
            # 运行指定套件
            if args.suite == "unit":
                result = orchestrator.run_unit_tests_suite()
            elif args.suite == "comprehensive":
                result = orchestrator.run_comprehensive_tests_suite()
            elif args.suite == "benchmark":
                result = orchestrator.run_benchmark_suite()
            elif args.suite == "stress":
                result = orchestrator.run_stress_tests_suite(args.stress_duration)
            elif args.suite == "validation":
                result = orchestrator.run_quick_validation()

            print(
                f"\n{args.suite.title()} 测试结果: {'✅ 成功' if result['success'] else '❌ 失败'}"
            )
            return result["success"]

        else:
            pass  # Auto-fixed empty block
            # 运行完整测试套件
            results = orchestrator.run_all_tests(
                include_stress=not args.no_stress, stress_duration=args.stress_duration
            )

            # 保存报告并打印摘要
            report_path = orchestrator.save_final_report()
            orchestrator.print_final_summary()

            print(f"\n📄 完整报告: {report_path}")

            # 根据总体成功率决定退出代码
            overall_success = results["summary"]["overall_success_rate"]
            return overall_success >= 0.8

    except Exception as e:
        print(f"❌ 测试框架执行失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
