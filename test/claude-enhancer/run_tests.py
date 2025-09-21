#!/usr/bin/env python3
"""
Claude Enhancer 测试执行器
统一的测试运行和报告生成工具
"""

import os
import sys
import argparse
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import concurrent.futures


class TestRunner:
    """测试运行器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_root = project_root / "test" / "claude-enhancer"
        self.results = {}
        self.start_time = None
        self.end_time = None

    def run_all_tests(self, parallel: bool = True, categories: List[str] = None) -> Dict[str, Any]:
        """运行所有测试"""
        self.start_time = time.time()

        test_categories = {
            "hooks": self.test_root / "hooks",
            "workflows": self.test_root / "workflows",
            "integration": self.test_root / "integration",
            "performance": self.test_root / "performance",
            "security": self.test_root / "security"
        }

        # 过滤要运行的测试类别
        if categories:
            test_categories = {k: v for k, v in test_categories.items() if k in categories}

        print(f"🚀 开始运行 Claude Enhancer 测试套件")
        print(f"📁 测试目录: {self.test_root}")
        print(f"🏷️  测试类别: {', '.join(test_categories.keys())}")
        print(f"⚡ 并行执行: {'是' if parallel else '否'}")
        print("-" * 60)

        if parallel:
            self._run_tests_parallel(test_categories)
        else:
            self._run_tests_sequential(test_categories)

        self.end_time = time.time()
        return self._generate_summary()

    def _run_tests_parallel(self, test_categories: Dict[str, Path]):
        """并行运行测试"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(test_categories)) as executor:
            futures = {
                executor.submit(self._run_test_category, category, path): category
                for category, path in test_categories.items()
            }

            for future in concurrent.futures.as_completed(futures):
                category = futures[future]
                try:
                    result = future.result()
                    self.results[category] = result
                    self._print_category_result(category, result)
                except Exception as e:
                    self.results[category] = {
                        "success": False,
                        "error": str(e),
                        "tests_run": 0,
                        "tests_passed": 0,
                        "tests_failed": 1,
                        "execution_time": 0
                    }
                    print(f"❌ {category} 测试失败: {e}")

    def _run_tests_sequential(self, test_categories: Dict[str, Path]):
        """顺序运行测试"""
        for category, path in test_categories.items():
            try:
                result = self._run_test_category(category, path)
                self.results[category] = result
                self._print_category_result(category, result)
            except Exception as e:
                self.results[category] = {
                    "success": False,
                    "error": str(e),
                    "tests_run": 0,
                    "tests_passed": 0,
                    "tests_failed": 1,
                    "execution_time": 0
                }
                print(f"❌ {category} 测试失败: {e}")

    def _run_test_category(self, category: str, test_path: Path) -> Dict[str, Any]:
        """运行单个测试类别"""
        if not test_path.exists():
            return {
                "success": False,
                "error": f"Test directory not found: {test_path}",
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 1,
                "execution_time": 0
            }

        start_time = time.time()

        # 查找测试文件
        test_files = list(test_path.glob("test_*.py"))
        if not test_files:
            return {
                "success": False,
                "error": "No test files found",
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 1,
                "execution_time": 0
            }

        # 运行pytest
        cmd = [
            sys.executable, "-m", "pytest",
            str(test_path),
            "-v",
            "--tb=short",
            "--json-report",
            f"--json-report-file={self.project_root}/test-results/{category}-results.json"
        ]

        # 为性能测试添加特殊标志
        if category == "performance":
            cmd.extend(["--benchmark-only", "--benchmark-json=performance-results.json"])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300  # 5分钟超时
            )

            end_time = time.time()
            execution_time = end_time - start_time

            # 解析pytest输出
            return self._parse_pytest_result(result, execution_time)

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Tests timed out after 5 minutes",
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 1,
                "execution_time": 300
            }

    def _parse_pytest_result(self, result: subprocess.CompletedProcess, execution_time: float) -> Dict[str, Any]:
        """解析pytest结果"""
        success = result.returncode == 0

        # 从输出中提取测试统计
        output_lines = result.stdout.split('\n')
        tests_run = 0
        tests_passed = 0
        tests_failed = 0
        tests_skipped = 0

        for line in output_lines:
            if "failed" in line and "passed" in line:
                # 解析类似 "2 failed, 8 passed in 1.23s" 的行
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "failed" and i > 0:
                        tests_failed = int(parts[i-1])
                    elif part == "passed" and i > 0:
                        tests_passed = int(parts[i-1])
                    elif part == "skipped" and i > 0:
                        tests_skipped = int(parts[i-1])

        tests_run = tests_passed + tests_failed + tests_skipped

        return {
            "success": success,
            "tests_run": tests_run,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed,
            "tests_skipped": tests_skipped,
            "execution_time": execution_time,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    def _print_category_result(self, category: str, result: Dict[str, Any]):
        """打印类别测试结果"""
        if result["success"]:
            status_icon = "✅"
            status_text = "通过"
        else:
            status_icon = "❌"
            status_text = "失败"

        print(f"{status_icon} {category.upper()} {status_text}")
        print(f"   📊 运行: {result['tests_run']}, 通过: {result['tests_passed']}, 失败: {result['tests_failed']}")
        print(f"   ⏱️  耗时: {result['execution_time']:.2f}s")

        if not result["success"] and "error" in result:
            print(f"   ❗ 错误: {result['error']}")

        print()

    def _generate_summary(self) -> Dict[str, Any]:
        """生成测试摘要"""
        total_tests = sum(r.get("tests_run", 0) for r in self.results.values())
        total_passed = sum(r.get("tests_passed", 0) for r in self.results.values())
        total_failed = sum(r.get("tests_failed", 0) for r in self.results.values())
        total_skipped = sum(r.get("tests_skipped", 0) for r in self.results.values())
        total_time = self.end_time - self.start_time if self.end_time and self.start_time else 0

        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        overall_success = all(r.get("success", False) for r in self.results.values())

        summary = {
            "overall_success": overall_success,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_skipped": total_skipped,
            "success_rate": success_rate,
            "total_execution_time": total_time,
            "categories": self.results,
            "timestamp": time.time()
        }

        self._print_summary(summary)
        return summary

    def _print_summary(self, summary: Dict[str, Any]):
        """打印测试摘要"""
        print("=" * 60)
        print("📋 Claude Enhancer 测试摘要")
        print("=" * 60)

        if summary["overall_success"]:
            print("🎉 所有测试通过！")
        else:
            print("⚠️  部分测试失败")

        print(f"📊 总计: {summary['total_tests']} 个测试")
        print(f"✅ 通过: {summary['total_passed']} 个")
        print(f"❌ 失败: {summary['total_failed']} 个")
        print(f"⏭️  跳过: {summary['total_skipped']} 个")
        print(f"📈 成功率: {summary['success_rate']:.1f}%")
        print(f"⏱️  总耗时: {summary['total_execution_time']:.2f}s")

        print("\n📁 分类详情:")
        for category, result in summary["categories"].items():
            status = "✅" if result.get("success", False) else "❌"
            print(f"  {status} {category}: {result.get('tests_passed', 0)}/{result.get('tests_run', 0)} 通过")

        print("=" * 60)

    def save_results(self, output_file: Path):
        """保存测试结果"""
        summary = self._generate_summary()

        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"📄 测试结果已保存到: {output_file}")


class TestValidator:
    """测试验证器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def validate_test_environment(self) -> bool:
        """验证测试环境"""
        print("🔍 验证测试环境...")

        checks = [
            self._check_python_version,
            self._check_required_packages,
            self._check_test_files,
            self._check_hook_scripts
        ]

        all_passed = True
        for check in checks:
            try:
                if not check():
                    all_passed = False
            except Exception as e:
                print(f"❌ 环境检查失败: {e}")
                all_passed = False

        if all_passed:
            print("✅ 测试环境验证通过")
        else:
            print("❌ 测试环境验证失败")

        return all_passed

    def _check_python_version(self) -> bool:
        """检查Python版本"""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 7:
            print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            print(f"❌ Python版本过低: {version.major}.{version.minor}.{version.micro} (需要 3.7+)")
            return False

    def _check_required_packages(self) -> bool:
        """检查必需的包"""
        required_packages = [
            "pytest",
            "psutil",
            "memory_profiler"
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package} 已安装")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package} 未安装")

        if missing_packages:
            print(f"💡 请安装缺失的包: pip install {' '.join(missing_packages)}")
            return False

        return True

    def _check_test_files(self) -> bool:
        """检查测试文件"""
        test_root = self.project_root / "test" / "claude-enhancer"
        if not test_root.exists():
            print(f"❌ 测试目录不存在: {test_root}")
            return False

        test_categories = ["hooks", "workflows", "integration", "performance", "security"]
        all_exist = True

        for category in test_categories:
            category_path = test_root / category
            if category_path.exists():
                test_files = list(category_path.glob("test_*.py"))
                print(f"✅ {category}: {len(test_files)} 个测试文件")
            else:
                print(f"❌ {category} 目录不存在")
                all_exist = False

        return all_exist

    def _check_hook_scripts(self) -> bool:
        """检查Hook脚本"""
        hooks_dir = self.project_root / ".claude" / "hooks"
        if not hooks_dir.exists():
            print(f"❌ Hooks目录不存在: {hooks_dir}")
            return False

        required_scripts = [
            "agent_validator.sh",
            "phase_manager.py"
        ]

        all_exist = True
        for script in required_scripts:
            script_path = hooks_dir / script
            if script_path.exists():
                print(f"✅ {script} 存在")
            else:
                print(f"❌ {script} 不存在")
                all_exist = False

        return all_exist


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Claude Enhancer 测试运行器")
    parser.add_argument("--categories", nargs="+",
                       choices=["hooks", "workflows", "integration", "performance", "security"],
                       help="要运行的测试类别")
    parser.add_argument("--sequential", action="store_true", help="顺序运行测试（默认并行）")
    parser.add_argument("--validate-only", action="store_true", help="只验证环境，不运行测试")
    parser.add_argument("--output", type=str, help="结果输出文件路径")

    args = parser.parse_args()

    # 确定项目根目录
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent

    print("🧪 Claude Enhancer 测试套件")
    print(f"📁 项目根目录: {project_root}")
    print()

    # 验证测试环境
    validator = TestValidator(project_root)
    if not validator.validate_test_environment():
        sys.exit(1)

    if args.validate_only:
        print("✅ 环境验证完成")
        return

    # 运行测试
    runner = TestRunner(project_root)

    try:
        results = runner.run_all_tests(
            parallel=not args.sequential,
            categories=args.categories
        )

        # 保存结果
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = project_root / "test-results" / "claude-enhancer-results.json"

        runner.save_results(output_path)

        # 根据测试结果设置退出码
        if results["overall_success"]:
            print("\n🎉 所有测试成功完成！")
            sys.exit(0)
        else:
            print("\n❌ 部分测试失败")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 测试执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()