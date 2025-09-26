#!/usr/bin/env python3
"""
Claude Enhancer 5.1 Hook验证脚本
验证所有Hook的存在性、可执行性和基础功能

用于E2E测试前的环境检查
"""

import os
import sys
import json
import subprocess
import time
from typing import Dict, List, Tuple
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HookValidator:
    """Hook验证器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.path.abspath(".")
        self.hooks_dir = os.path.join(self.project_root, ".claude", "hooks")
        self.results = {}

    def _run_hook(
        self, hook_name: str, context: Dict = None, timeout: int = 10
    ) -> Tuple[bool, str, float]:
        """执行Hook并返回结果"""
        hook_path = os.path.join(self.hooks_dir, f"{hook_name}.sh")

        if not os.path.exists(hook_path):
            return False, f"Hook文件不存在: {hook_path}", 0.0

        if not os.access(hook_path, os.X_OK):
            return False, f"Hook文件不可执行: {hook_path}", 0.0

        # 准备环境变量
        env = os.environ.copy()
        if context:
            for key, value in context.items():
                env[f"TEST_{key.upper()}"] = str(value)

        start_time = time.time()
        try:
            result = subprocess.run(
                ["bash", hook_path],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
            duration = time.time() - start_time

            success = result.returncode == 0
            output = result.stdout + result.stderr

            return success, output.strip(), duration

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return False, f"Hook执行超时 ({timeout}s)", duration
        except Exception as e:
            duration = time.time() - start_time
            return False, f"Hook执行异常: {str(e)}", duration

    def validate_hook(self, hook_name: str, test_scenarios: List[Dict] = None) -> Dict:
        """验证单个Hook"""
        logger.info(f"🔍 验证Hook: {hook_name}")

        hook_result = {
            "name": hook_name,
            "exists": False,
            "executable": False,
            "scenarios": [],
            "performance": {},
            "overall_status": "FAIL",
        }

        hook_path = os.path.join(self.hooks_dir, f"{hook_name}.sh")

        # 检查存在性
        if os.path.exists(hook_path):
            hook_result["exists"] = True

            # 检查可执行性
            if os.access(hook_path, os.X_OK):
                hook_result["executable"] = True
            else:
                logger.warning(f"Hook文件存在但不可执行: {hook_name}")
        else:
            logger.warning(f"Hook文件不存在: {hook_name}")
            hook_result["overall_status"] = "NOT_FOUND"
            return hook_result

        # 执行测试场景
        if test_scenarios:
            total_duration = 0
            successful_scenarios = 0

            for scenario in test_scenarios:
                scenario_name = scenario.get("name", "default")
                context = scenario.get("input", {})
                expected = scenario.get("expected_output", [])
                timeout = scenario.get("timeout", 10)

                success, output, duration = self._run_hook(hook_name, context, timeout)
                total_duration += duration

                # 验证输出
                output_valid = True
                if expected:
                    output_valid = any(
                        exp.lower() in output.lower() for exp in expected
                    )

                scenario_result = {
                    "name": scenario_name,
                    "success": success,
                    "duration": duration,
                    "output_valid": output_valid,
                    "output": output[:200] + "..." if len(output) > 200 else output,
                }

                hook_result["scenarios"].append(scenario_result)

                if success and output_valid:
                    successful_scenarios += 1

            # 性能统计
            hook_result["performance"] = {
                "total_duration": total_duration,
                "average_duration": total_duration / len(test_scenarios)
                if test_scenarios
                else 0,
                "max_duration": max(s["duration"] for s in hook_result["scenarios"]),
                "successful_scenarios": successful_scenarios,
                "total_scenarios": len(test_scenarios),
                "success_rate": successful_scenarios / len(test_scenarios) * 100
                if test_scenarios
                else 0,
            }

        else:
            # 基础执行测试
            success, output, duration = self._run_hook(hook_name, {"test": "basic"}, 5)

            hook_result["scenarios"] = [
                {
                    "name": "basic_execution",
                    "success": success,
                    "duration": duration,
                    "output_valid": True,
                    "output": output[:200] + "..." if len(output) > 200 else output,
                }
            ]

            hook_result["performance"] = {
                "total_duration": duration,
                "average_duration": duration,
                "max_duration": duration,
                "successful_scenarios": 1 if success else 0,
                "total_scenarios": 1,
                "success_rate": 100.0 if success else 0.0,
            }

        # 确定整体状态
        if hook_result["performance"]["success_rate"] >= 80:
            hook_result["overall_status"] = "PASS"
        elif hook_result["performance"]["success_rate"] >= 50:
            hook_result["overall_status"] = "PARTIAL"
        else:
            hook_result["overall_status"] = "FAIL"

        return hook_result

    def validate_all_hooks(self, config_file: str = None) -> Dict:
        """验证所有Hook"""
        logger.info("🚀 开始验证所有Hook")

        # 加载配置
        test_scenarios = {}
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    test_scenarios = config.get("hook_test_scenarios", {})
            except Exception as e:
                logger.warning(f"无法加载配置文件: {e}")

        # 发现所有Hook
        hooks_to_test = []
        if os.path.exists(self.hooks_dir):
            for file in os.listdir(self.hooks_dir):
                if file.endswith(".sh"):
                    hook_name = file[:-3]  # 移除.sh后缀
                    hooks_to_test.append(hook_name)

        logger.info(f"发现{len(hooks_to_test)}个Hook文件")

        # 优先测试的关键Hook
        priority_hooks = [
            "smart_agent_selector",
            "error_handler",
            "performance_monitor",
            "branch_helper",
            "p1_requirements_analyzer",
            "agent-output-summarizer",
        ]

        # 按优先级排序
        hooks_sorted = []
        for hook in priority_hooks:
            if hook in hooks_to_test:
                hooks_sorted.append(hook)
                hooks_to_test.remove(hook)
        hooks_sorted.extend(sorted(hooks_to_test))

        # 验证每个Hook
        validation_results = {
            "summary": {
                "total_hooks": len(hooks_sorted),
                "validated": 0,
                "passed": 0,
                "partial": 0,
                "failed": 0,
                "not_found": 0,
                "start_time": time.time(),
            },
            "hook_results": {},
            "performance_overview": {},
            "recommendations": [],
        }

        for hook_name in hooks_sorted:
            scenarios = test_scenarios.get(hook_name, None)
            result = self.validate_hook(hook_name, scenarios)

            validation_results["hook_results"][hook_name] = result
            validation_results["summary"]["validated"] += 1

            # 更新统计
            status = result["overall_status"]
            if status == "PASS":
                validation_results["summary"]["passed"] += 1
            elif status == "PARTIAL":
                validation_results["summary"]["partial"] += 1
            elif status == "FAIL":
                validation_results["summary"]["failed"] += 1
            elif status == "NOT_FOUND":
                validation_results["summary"]["not_found"] += 1

        validation_results["summary"]["end_time"] = time.time()
        validation_results["summary"]["total_duration"] = (
            validation_results["summary"]["end_time"]
            - validation_results["summary"]["start_time"]
        )

        # 生成性能概览
        all_durations = []
        for hook_result in validation_results["hook_results"].values():
            if hook_result["performance"]:
                all_durations.append(hook_result["performance"]["average_duration"])

        if all_durations:
            validation_results["performance_overview"] = {
                "average_hook_duration": sum(all_durations) / len(all_durations),
                "max_hook_duration": max(all_durations),
                "min_hook_duration": min(all_durations),
                "total_hook_execution_time": sum(all_durations),
            }

        # 生成建议
        validation_results["recommendations"] = self._generate_recommendations(
            validation_results
        )

        return validation_results

    def _generate_recommendations(self, results: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []

        summary = results["summary"]
        hook_results = results["hook_results"]

        # 基于统计生成建议
        success_rate = (summary["passed"] / max(1, summary["total_hooks"])) * 100

        if success_rate < 70:
            recommendations.append(f"Hook总体通过率较低({success_rate:.1f}%)，建议重点检查失败的Hook")

        if summary["not_found"] > 0:
            recommendations.append(
                f"发现{summary['not_found']}个Hook文件不存在，建议检查.claude/hooks目录"
            )

        # 性能建议
        if "performance_overview" in results:
            perf = results["performance_overview"]
            if perf["max_hook_duration"] > 5.0:
                recommendations.append(
                    f"部分Hook执行时间过长(最长{perf['max_hook_duration']:.2f}s)，建议优化性能"
                )

            if perf["average_hook_duration"] > 2.0:
                recommendations.append(
                    f"Hook平均执行时间较长({perf['average_hook_duration']:.2f}s)，建议整体优化"
                )

        # 具体Hook建议
        critical_hooks_missing = []
        critical_hooks = [
            "smart_agent_selector",
            "error_handler",
            "performance_monitor",
        ]

        for hook in critical_hooks:
            if hook in hook_results:
                if hook_results[hook]["overall_status"] not in ["PASS", "PARTIAL"]:
                    critical_hooks_missing.append(hook)
            else:
                critical_hooks_missing.append(hook)

        if critical_hooks_missing:
            recommendations.append(f"关键Hook功能异常: {', '.join(critical_hooks_missing)}")

        # 可执行性问题
        non_executable = []
        for hook_name, result in hook_results.items():
            if result["exists"] and not result["executable"]:
                non_executable.append(hook_name)

        if non_executable:
            recommendations.append(
                f"以下Hook文件存在但不可执行: {', '.join(non_executable)}，请运行chmod +x"
            )

        if not recommendations:
            recommendations.append("所有Hook验证通过，系统准备就绪！")

        return recommendations

    def print_summary(self, results: Dict) -> None:
        """打印验证摘要"""
        summary = results["summary"]

        print("\n" + "=" * 60)
        print("🔧 Claude Enhancer 5.1 Hook验证报告")
        print("=" * 60)
        print(f"📊 总计Hook: {summary['total_hooks']}")
        print(f"✅ 通过: {summary['passed']}")
        print(f"⚠️  部分通过: {summary['partial']}")
        print(f"❌ 失败: {summary['failed']}")
        print(f"🔍 未找到: {summary['not_found']}")
        print(f"⏱️  验证时间: {summary['total_duration']:.2f}秒")
        print()

        # 性能概览
        if "performance_overview" in results:
            perf = results["performance_overview"]
            print("⚡ 性能概览:")
            print(f"   平均执行时间: {perf['average_hook_duration']:.3f}秒")
            print(f"   最长执行时间: {perf['max_hook_duration']:.3f}秒")
            print(f"   最短执行时间: {perf['min_hook_duration']:.3f}秒")
            print()

        # Hook状态详情
        print("📋 Hook详细状态:")
        for hook_name, result in results["hook_results"].items():
            status = result["overall_status"]
            icon = {"PASS": "✅", "PARTIAL": "⚠️", "FAIL": "❌", "NOT_FOUND": "🔍"}.get(
                status, "❓"
            )

            duration = result["performance"].get("average_duration", 0)
            success_rate = result["performance"].get("success_rate", 0)

            print(
                f"   {icon} {hook_name:<30} ({success_rate:>5.1f}%) {duration:>6.3f}s"
            )

        print()

        # 建议
        if results["recommendations"]:
            print("💡 优化建议:")
            for i, rec in enumerate(results["recommendations"], 1):
                print(f"   {i}. {rec}")

        print("\n" + "=" * 60)

    def save_results(self, results: Dict, filename: str = None) -> str:
        """保存验证结果"""
        if filename is None:
            timestamp = int(time.time())
            filename = f"hook_validation_results_{timestamp}.json"

        filepath = os.path.join(self.project_root, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"📄 验证结果已保存: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"保存验证结果失败: {e}")
            return ""


def main():
    """主函数"""
    print("🔧 启动Claude Enhancer 5.1 Hook验证")

    # 获取项目根目录
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.path.abspath(".")

    # 获取配置文件
    config_file = os.path.join(project_root, "e2e_test_config.json")
    if not os.path.exists(config_file):
        config_file = None
        logger.warning("未找到配置文件，使用默认设置")

    # 创建验证器
    validator = HookValidator(project_root)

    try:
        # 执行验证
        results = validator.validate_all_hooks(config_file)

        # 打印摘要
        validator.print_summary(results)

        # 保存结果
        validator.save_results(results)

        # 返回退出代码
        success_rate = (
            results["summary"]["passed"] / max(1, results["summary"]["total_hooks"])
        ) * 100
        if success_rate >= 80:
            print("🎉 Hook验证通过！")
            sys.exit(0)
        elif success_rate >= 50:
            print("⚠️  Hook验证部分通过，建议检查失败项")
            sys.exit(1)
        else:
            print("❌ Hook验证失败，需要修复问题")
            sys.exit(2)

    except KeyboardInterrupt:
        print("\n⛔ 验证被用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"验证过程异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
