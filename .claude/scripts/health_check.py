#!/usr/bin/env python3
"""
DocGate文档质量管理系统健康检查脚本
Health Check Script for DocGate Documentation Quality Management System
"""

import sys
import os
import json
import yaml
import subprocess
import importlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple


# 颜色输出
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"  # No Color


def print_colored(message: str, color: str = Colors.NC) -> None:
    """打印带颜色的消息"""
    print(f"{color}{message}{Colors.NC}")


def print_success(message: str) -> None:
    print_colored(f"✅ {message}", Colors.GREEN)


def print_error(message: str) -> None:
    print_colored(f"❌ {message}", Colors.RED)


def print_warning(message: str) -> None:
    print_colored(f"⚠️  {message}", Colors.YELLOW)


def print_info(message: str) -> None:
    print_colored(f"ℹ️  {message}", Colors.BLUE)


def print_header(message: str) -> None:
    print_colored(f"\n{'='*60}", Colors.PURPLE)
    print_colored(f"🔍 {message}", Colors.PURPLE)
    print_colored(f"{'='*60}", Colors.PURPLE)


class HealthChecker:
    """DocGate系统健康检查器"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.claude_dir = self.project_root / ".claude"
        self.issues = []
        self.warnings = []
        self.successes = []

    def log_issue(self, message: str) -> None:
        """记录错误"""
        self.issues.append(message)
        print_error(message)

    def log_warning(self, message: str) -> None:
        """记录警告"""
        self.warnings.append(message)
        print_warning(message)

    def log_success(self, message: str) -> None:
        """记录成功"""
        self.successes.append(message)
        print_success(message)

    def check_directory_structure(self) -> bool:
        """检查目录结构"""
        print_header("检查目录结构")

        required_dirs = [
            self.claude_dir,
            self.claude_dir / "scripts",
            self.claude_dir / "hooks",
            self.claude_dir / "git-hooks",
            self.project_root / "docs",
            self.project_root / "docs" / "_templates",
            self.project_root / "backend" / "api" / "docgate",
        ]

        all_good = True
        for dir_path in required_dirs:
            if dir_path.exists():
                self.log_success(f"目录存在: {dir_path.relative_to(self.project_root)}")
            else:
                self.log_issue(f"目录缺失: {dir_path.relative_to(self.project_root)}")
                all_good = False

        return all_good

    def check_configuration_files(self) -> bool:
        """检查配置文件"""
        print_header("检查配置文件")

        config_files = [
            (self.project_root / ".docpolicy.yaml", "文档策略配置"),
            (self.claude_dir / "settings.json", "Claude设置"),
            (self.project_root / "DOCGATE_USAGE.md", "使用指南"),
        ]

        all_good = True
        for file_path, description in config_files:
            if file_path.exists():
                self.log_success(f"{description}: {file_path.name}")

                # 验证YAML/JSON格式
                if file_path.suffix in [".yaml", ".yml"]:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            yaml.safe_load(f)
                        self.log_success(f"YAML格式正确: {file_path.name}")
                    except yaml.YAMLError as e:
                        self.log_issue(f"YAML格式错误 {file_path.name}: {e}")
                        all_good = False

                elif file_path.suffix == ".json":
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            json.load(f)
                        self.log_success(f"JSON格式正确: {file_path.name}")
                    except json.JSONDecodeError as e:
                        self.log_issue(f"JSON格式错误 {file_path.name}: {e}")
                        all_good = False
            else:
                self.log_warning(f"{description}缺失: {file_path.name}")

        return all_good

    def check_git_hooks(self) -> bool:
        """检查Git hooks"""
        print_header("检查Git Hooks")

        git_dir = self.project_root / ".git"
        if not git_dir.exists():
            self.log_warning("非Git仓库，跳过Git hooks检查")
            return True

        hooks_dir = git_dir / "hooks"
        required_hooks = ["pre-commit", "commit-msg", "pre-push"]

        all_good = True
        for hook_name in required_hooks:
            hook_path = hooks_dir / hook_name
            if hook_path.exists():
                if os.access(hook_path, os.X_OK):
                    self.log_success(f"Git hook正常: {hook_name}")
                else:
                    self.log_issue(f"Git hook无执行权限: {hook_name}")
                    all_good = False
            else:
                self.log_issue(f"Git hook缺失: {hook_name}")
                all_good = False

        return all_good

    def check_python_dependencies(self) -> bool:
        """检查Python依赖"""
        print_header("检查Python依赖")

        required_modules = [
            ("fastapi", "FastAPI web框架"),
            ("pydantic", "数据验证"),
            ("yaml", "YAML解析"),
            ("requests", "HTTP客户端"),
            ("jinja2", "模板引擎"),
            ("aiofiles", "异步文件操作"),
            ("sqlalchemy", "ORM数据库"),
        ]

        all_good = True
        for module_name, description in required_modules:
            try:
                importlib.import_module(module_name)
                self.log_success(f"Python模块: {module_name} ({description})")
            except ImportError:
                self.log_issue(f"Python模块缺失: {module_name} ({description})")
                all_good = False

        return all_good

    def check_docgate_scripts(self) -> bool:
        """检查DocGate脚本"""
        print_header("检查DocGate脚本")

        scripts = [
            ("docgate_pre_commit_check.py", "预提交检查"),
            ("check_doc_links.py", "链接检查"),
            ("check_doc_structure.py", "结构检查"),
        ]

        scripts_dir = self.claude_dir / "scripts"
        all_good = True

        for script_name, description in scripts:
            script_path = scripts_dir / script_name
            if script_path.exists():
                if os.access(script_path, os.X_OK):
                    self.log_success(f"脚本正常: {script_name} ({description})")

                    # 测试脚本语法
                    try:
                        result = subprocess.run(
                            [sys.executable, "-m", "py_compile", str(script_path)],
                            capture_output=True,
                            text=True,
                        )

                        if result.returncode == 0:
                            self.log_success(f"脚本语法正确: {script_name}")
                        else:
                            self.log_issue(f"脚本语法错误 {script_name}: {result.stderr}")
                            all_good = False
                    except Exception as e:
                        self.log_warning(f"脚本语法检查失败 {script_name}: {e}")

                else:
                    self.log_issue(f"脚本无执行权限: {script_name}")
                    all_good = False
            else:
                self.log_issue(f"脚本缺失: {script_name}")
                all_good = False

        return all_good

    def check_document_templates(self) -> bool:
        """检查文档模板"""
        print_header("检查文档模板")

        templates_dir = self.project_root / "docs" / "_templates"
        required_templates = [
            ("requirement.md", "需求文档模板"),
            ("design.md", "设计文档模板"),
            ("api.md", "API文档模板"),
        ]

        all_good = True
        for template_name, description in required_templates:
            template_path = templates_dir / template_name
            if template_path.exists():
                self.log_success(f"模板存在: {template_name} ({description})")

                # 检查模板内容
                try:
                    with open(template_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if "---" in content and "title:" in content:
                        self.log_success(f"模板格式正确: {template_name}")
                    else:
                        self.log_warning(f"模板缺少YAML front matter: {template_name}")

                except Exception as e:
                    self.log_issue(f"模板读取失败 {template_name}: {e}")
                    all_good = False
            else:
                self.log_issue(f"模板缺失: {template_name}")
                all_good = False

        return all_good

    def check_api_structure(self) -> bool:
        """检查API结构"""
        print_header("检查API结构")

        api_dir = self.project_root / "backend" / "api" / "docgate"
        api_files = [
            ("__init__.py", "包初始化"),
            ("routes.py", "API路由"),
            ("models.py", "数据模型"),
            ("dependencies.py", "依赖注入"),
            ("exceptions.py", "异常处理"),
        ]

        all_good = True
        for file_name, description in api_files:
            file_path = api_dir / file_name
            if file_path.exists():
                self.log_success(f"API文件: {file_name} ({description})")
            else:
                self.log_warning(f"API文件缺失: {file_name} ({description})")

        return all_good

    def run_functional_tests(self) -> bool:
        """运行功能测试"""
        print_header("运行功能测试")

        all_good = True

        # 测试DocGate检查脚本
        script_path = self.claude_dir / "scripts" / "docgate_pre_commit_check.py"
        if script_path.exists():
            try:
                pass  # Auto-fixed empty block
                # 创建测试文件
                test_file = self.project_root / "test_doc.md"
                test_content = """---
title: "测试文档"
summary: "这是一个测试文档"
status: "draft"
last_updated: "2024-01-01"
---

# 测试文档

## 摘要
这是一个用于测试的文档。

## 关键点
- 测试点1
- 测试点2
- 测试点3
"""
                test_file.write_text(test_content, encoding="utf-8")

                # 运行检查
                result = subprocess.run(
                    [sys.executable, str(script_path), "--files", str(test_file)],
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    self.log_success("DocGate检查脚本功能正常")
                else:
                    self.log_warning(f"DocGate检查返回警告: {result.stdout}")

                # 清理测试文件
                test_file.unlink()

            except Exception as e:
                self.log_issue(f"功能测试失败: {e}")
                all_good = False

        return all_good

    def generate_health_report(self) -> Dict[str, Any]:
        """生成健康报告"""
        total_checks = len(self.successes) + len(self.warnings) + len(self.issues)

        if len(self.issues) == 0:
            status = "healthy"
            status_color = Colors.GREEN
        elif len(self.issues) <= 2:
            status = "degraded"
            status_color = Colors.YELLOW
        else:
            status = "unhealthy"
            status_color = Colors.RED

        report = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "summary": {
                "total_checks": total_checks,
                "successes": len(self.successes),
                "warnings": len(self.warnings),
                "issues": len(self.issues),
            },
            "details": {
                "successes": self.successes,
                "warnings": self.warnings,
                "issues": self.issues,
            },
        }

        print_header("健康检查报告")
        print_colored(f"系统状态: {status.upper()}", status_color)
        print_info(f"总检查项: {total_checks}")
        print_colored(f"成功: {len(self.successes)}", Colors.GREEN)
        print_colored(f"警告: {len(self.warnings)}", Colors.YELLOW)
        print_colored(f"错误: {len(self.issues)}", Colors.RED)

        return report

    def run_all_checks(self) -> bool:
        """运行所有检查"""
        print_colored("🏥 DocGate文档质量管理系统健康检查", Colors.PURPLE)
        print_colored("=" * 60, Colors.PURPLE)

        checks = [
            self.check_directory_structure,
            self.check_configuration_files,
            self.check_git_hooks,
            self.check_python_dependencies,
            self.check_docgate_scripts,
            self.check_document_templates,
            self.check_api_structure,
            self.run_functional_tests,
        ]

        all_passed = True
        for check in checks:
            try:
                result = check()
                if not result:
                    all_passed = False
            except Exception as e:
                self.log_issue(f"检查执行失败: {e}")
                all_passed = False

        # 生成报告
        report = self.generate_health_report()

        # 保存报告
        report_file = self.project_root / "docgate_health_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print_info(f"详细报告已保存: {report_file}")

        return all_passed


def main():
    """主函数"""
    try:
        checker = HealthChecker()
        success = checker.run_all_checks()

        print_header("检查完成")
        if success:
            print_success("DocGate系统健康状况良好!")
            sys.exit(0)
        else:
            print_error("DocGate系统存在问题，请查看上述错误信息")
            sys.exit(1)

    except KeyboardInterrupt:
        print_error("\n健康检查被中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"健康检查执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
