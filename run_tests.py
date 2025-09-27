#!/usr/bin/env python3
"""
Claude Enhancer 5.0 测试运行器
Initial-tests阶段 - 完整测试套件执行脚本
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path


class TestRunner:
    """测试运行器类"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = {
            "backend_unit": None,
            "frontend_unit": None,
            "integration": None,
            "coverage": None,
        }

    def run_backend_tests(self, verbose=False, coverage=False):
        """运行后端测试"""
        print("🧪 运行后端单元测试...")

        cmd = ["python", "-m", "pytest", "tests/"]

        if verbose:
            cmd.append("-v")

        if coverage:
            cmd.extend(
                [
                    "--cov=src",
                    "--cov-report=html:htmlcov",
                    "--cov-report=xml:coverage.xml",
                    "--cov-report=term-missing",
                ]
            )

        cmd.extend(
            ["--tb=short", "--disable-warnings", "-m", "not integration"]  # 排除集成测试
        )

        try:
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True, timeout=300
            )

            self.test_results["backend_unit"] = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
            }

            if result.returncode == 0:
                print("✅ 后端单元测试通过")
            else:
                print("❌ 后端单元测试失败")
                if verbose:
                    print(result.stdout)
                    print(result.stderr)

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print("⏰ 后端测试超时")
            return False
        except Exception as e:
            print(f"❌ 运行后端测试时出错: {e}")
            return False

    def run_frontend_tests(self, verbose=False, coverage=False):
        """运行前端测试"""
        print("🌐 运行前端组件测试...")

        frontend_dir = self.project_root / "frontend"
        if not frontend_dir.exists():
            print("⚠️ 前端目录不存在，跳过前端测试")
            return True

        # 检查是否有package.json
        package_json = frontend_dir / "package.json"
        if not package_json.exists():
            print("⚠️ 前端package.json不存在，跳过前端测试")
            return True

        cmd = ["npm", "test"]
        if coverage:
            cmd = ["npm", "run", "test:coverage"]

        try:
            result = subprocess.run(
                cmd, cwd=frontend_dir, capture_output=True, text=True, timeout=300
            )

            self.test_results["frontend_unit"] = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
            }

            if result.returncode == 0:
                print("✅ 前端组件测试通过")
            else:
                print("❌ 前端组件测试失败")
                if verbose:
                    print(result.stdout)
                    print(result.stderr)

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print("⏰ 前端测试超时")
            return False
        except FileNotFoundError:
            print("⚠️ npm命令不存在，跳过前端测试")
            return True
        except Exception as e:
            print(f"❌ 运行前端测试时出错: {e}")
            return False

    def run_integration_tests(self, verbose=False):
        """运行集成测试"""
        print("🔗 运行API集成测试...")

        cmd = ["python", "-m", "pytest", "tests/integration/", "-m", "integration"]

        if verbose:
            cmd.append("-v")

        cmd.extend(["--tb=short", "--disable-warnings"])

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600,  # 集成测试可能需要更长时间
            )

            self.test_results["integration"] = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
            }

            if result.returncode == 0:
                print("✅ 集成测试通过")
            else:
                print("❌ 集成测试失败")
                if verbose:
                    print(result.stdout)
                    print(result.stderr)

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print("⏰ 集成测试超时")
            return False
        except Exception as e:
            print(f"❌ 运行集成测试时出错: {e}")
            return False

    def generate_coverage_report(self):
        """生成覆盖率报告"""
        print("📊 生成测试覆盖率报告...")

        # 合并前后端覆盖率报告
        coverage_files = []

        # 后端覆盖率
        if (self.project_root / "coverage.xml").exists():
            coverage_files.append("coverage.xml")

        # 前端覆盖率
        frontend_coverage = self.project_root / "frontend" / "coverage"
        if frontend_coverage.exists():
            coverage_files.append(str(frontend_coverage))

        if coverage_files:
            print(f"📁 找到覆盖率文件: {coverage_files}")
            self.test_results["coverage"] = {
                "files": coverage_files,
                "html_report": str(self.project_root / "htmlcov"),
            }
            print("✅ 覆盖率报告已生成")
            return True
        else:
            print("⚠️ 未找到覆盖率文件")
            return False

    def run_linting(self):
        """运行代码检查"""
        print("🔍 运行代码质量检查...")

        # Python代码检查
        python_check = self.run_python_linting()

        # 前端代码检查
        frontend_check = self.run_frontend_linting()

        return python_check and frontend_check

    def run_python_linting(self):
        """运行Python代码检查"""
        checks = []

        # flake8检查
        try:
            result = subprocess.run(
                ["python", "-m", "flake8", "src/", "tests/"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )
            checks.append(("flake8", result.returncode == 0))
        except:
            checks.append(("flake8", False))

        # black格式检查
        try:
            result = subprocess.run(
                ["python", "-m", "black", "--check", "src/", "tests/"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )
            checks.append(("black", result.returncode == 0))
        except:
            checks.append(("black", False))

        passed = sum(1 for _, success in checks if success)
        total = len(checks)

        print(f"🐍 Python代码检查: {passed}/{total} 通过")
        return passed == total

    def run_frontend_linting(self):
        """运行前端代码检查"""
        frontend_dir = self.project_root / "frontend"
        if not frontend_dir.exists():
            return True

        try:
            result = subprocess.run(
                ["npm", "run", "lint"],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print("🌐 前端代码检查通过")
                return True
            else:
                print("🌐 前端代码检查失败")
                return False

        except:
            print("🌐 前端代码检查跳过（npm script不存在）")
            return True

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📋 测试结果总结")
        print("=" * 60)

        results = [
            ("后端单元测试", self.test_results["backend_unit"]),
            ("前端组件测试", self.test_results["frontend_unit"]),
            ("API集成测试", self.test_results["integration"]),
            ("覆盖率报告", self.test_results["coverage"]),
        ]

        passed = 0
        total = 0

        for name, result in results:
            if result is not None:
                total += 1
                if result.get("success", False) or result.get("files", False):
                    passed += 1
                    print(f"✅ {name}: 通过")
                else:
                    print(f"❌ {name}: 失败")
            else:
                print(f"⚠️ {name}: 跳过")

        print("-" * 60)
        print(f"总计: {passed}/{total} 项测试通过")

        if passed == total and total > 0:
            print("🎉 所有测试都通过了！")
            return True
        else:
            print("🔧 部分测试需要修复")
            return False

    def clean_test_artifacts(self):
        """清理测试产物"""
        print("🧹 清理测试产物...")

        artifacts = [
            ".pytest_cache",
            "htmlcov",
            "coverage.xml",
            "test-results.xml",
            "__pycache__",
            "frontend/coverage",
            "frontend/node_modules/.cache",
        ]

        for artifact in artifacts:
            artifact_path = self.project_root / artifact
            if artifact_path.exists():
                try:
                    if artifact_path.is_file():
                        artifact_path.unlink()
                    else:
                        import shutil

                        shutil.rmtree(artifact_path)
                    print(f"🗑️ 已删除: {artifact}")
                except Exception as e:
                    print(f"⚠️ 删除失败 {artifact}: {e}")

        print("✅ 清理完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Claude Enhancer 5.0 测试运行器")

    parser.add_argument(
        "--type",
        choices=["all", "backend", "frontend", "integration", "lint"],
        default="all",
        help="要运行的测试类型",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    parser.add_argument("--coverage", "-c", action="store_true", help="生成覆盖率报告")

    parser.add_argument("--clean", action="store_true", help="运行前清理测试产物")

    parser.add_argument("--fail-fast", action="store_true", help="遇到失败立即停止")

    args = parser.parse_args()

    runner = TestRunner()

    print("🚀 Claude Enhancer 5.0 测试开始")
    print("=" * 50)

    start_time = time.time()

    # 清理
    if args.clean:
        runner.clean_test_artifacts()

    success = True

    try:
        if args.type in ["all", "lint"]:
            lint_success = runner.run_linting()
            if not lint_success and args.fail_fast:
                success = False
                print("💥 代码检查失败，终止测试")
                return 1

        if args.type in ["all", "backend"]:
            backend_success = runner.run_backend_tests(args.verbose, args.coverage)
            success = success and backend_success
            if not backend_success and args.fail_fast:
                print("💥 后端测试失败，终止测试")
                return 1

        if args.type in ["all", "frontend"]:
            frontend_success = runner.run_frontend_tests(args.verbose, args.coverage)
            success = success and frontend_success
            if not frontend_success and args.fail_fast:
                print("💥 前端测试失败，终止测试")
                return 1

        if args.type in ["all", "integration"]:
            integration_success = runner.run_integration_tests(args.verbose)
            success = success and integration_success
            if not integration_success and args.fail_fast:
                print("💥 集成测试失败，终止测试")
                return 1

        if args.coverage:
            runner.generate_coverage_report()

    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        return 130

    except Exception as e:
        print(f"\n❌ 测试运行器出错: {e}")
        return 1

    finally:
        end_time = time.time()
        duration = end_time - start_time

        print(f"\n⏱️ 测试耗时: {duration:.2f}秒")
        runner.print_summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
