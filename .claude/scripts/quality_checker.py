#!/usr/bin/env python3
"""
Claude Enhancer 5.0 质量检查工具
=================================

自动化代码质量检查工具，实现代码审查指南中定义的质量标准。
提供全面的代码质量评估、安全检查和性能分析。

Features:
- 代码规范检查
- 安全漏洞扫描
- 性能基准测试
- 可维护性分析
- 质量报告生成

Author: Claude Code Review Expert
Version: 1.0.0
"""

import os
import sys
import json
import yaml
import subprocess
import argparse
import logging
import time
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """质量评分数据类"""

    readability: int = 0  # 可读性 (0-25)
    security: int = 0  # 安全性 (0-30)
    performance: int = 0  # 性能 (0-20)
    maintainability: int = 0  # 可维护性 (0-25)

    @property
    def total(self) -> int:
        """总分"""
        return (
            self.readability + self.security + self.performance + self.maintainability
        )

    @property
    def grade(self) -> str:
        """评级"""
        if self.total >= 90:
            return "优秀"
        elif self.total >= 80:
            return "良好"
        elif self.total >= 70:
            return "及格"
        else:
            return "需改进"


@dataclass
class QualityIssue:
    """质量问题数据类"""

    file_path: str
    line_number: int
    severity: str  # critical, major, minor, info
    category: str  # readability, security, performance, maintainability
    message: str
    rule_id: str
    suggestion: Optional[str] = None


@dataclass
class QualityReport:
    """质量报告数据类"""

    timestamp: str
    project_path: str
    total_files: int
    score: QualityScore
    issues: List[QualityIssue]
    recommendations: List[str]
    execution_time: float


class QualityChecker:
    """代码质量检查器"""

    def __init__(self, project_path: str = "."):
        """
        初始化质量检查器

        Args:
            project_path: 项目根路径
        """
        self.project_path = Path(project_path).resolve()
        self.claude_dir = self.project_path / ".claude"
        self.temp_dir = Path("/tmp/claude_quality_check")
        self.temp_dir.mkdir(exist_ok=True)

        # 检查工具
        self.tools = self._check_available_tools()

        # 质量规则配置
        self.rules = self._load_quality_rules()

    def _check_available_tools(self) -> Dict[str, bool]:
        """检查可用的质量检查工具"""
        tools = {
            "flake8": self._command_exists("flake8"),
            "black": self._command_exists("black"),
            "mypy": self._command_exists("mypy"),
            "bandit": self._command_exists("bandit"),
            "shellcheck": self._command_exists("shellcheck"),
            "yamllint": self._command_exists("yamllint"),
            "pytest": self._command_exists("pytest"),
        }

        logger.info(f"可用工具: {[k for k, v in tools.items() if v]}")
        return tools

    def _command_exists(self, command: str) -> bool:
        """检查命令是否存在"""
        try:
            subprocess.run(["which", command], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def _load_quality_rules(self) -> Dict[str, Any]:
        """加载质量规则配置"""
        rules_file = self.claude_dir / "config" / "quality_rules.yaml"

        # 默认规则
        default_rules = {
            "readability": {
                "max_line_length": 88,
                "max_function_lines": 50,
                "max_file_lines": 500,
                "max_complexity": 10,
                "require_docstrings": True,
            },
            "security": {
                "check_hardcoded_secrets": True,
                "check_sql_injection": True,
                "check_command_injection": True,
                "check_path_traversal": True,
            },
            "performance": {
                "max_response_time_ms": 100,
                "max_memory_mb": 100,
                "check_n_plus_one": True,
                "check_inefficient_loops": True,
            },
            "maintainability": {
                "min_test_coverage": 80,
                "max_dependency_depth": 5,
                "check_code_duplication": True,
                "require_type_hints": True,
            },
        }

        if rules_file.exists():
            try:
                with open(rules_file, "r", encoding="utf-8") as f:
                    custom_rules = yaml.safe_load(f)
                    # 合并自定义规则
                    default_rules.update(custom_rules)
            except Exception as e:
                logger.warning(f"加载自定义规则失败: {e}")

        return default_rules

    def check_project(
        self, include_patterns: List[str] = None, exclude_patterns: List[str] = None
    ) -> QualityReport:
        """
        检查整个项目

        Args:
            include_patterns: 包含的文件模式
            exclude_patterns: 排除的文件模式

        Returns:
            质量报告
        """
        start_time = time.time()
        logger.info(f"开始检查项目: {self.project_path}")

        # 默认模式
        if include_patterns is None:
            include_patterns = ["**/*.py", "**/*.sh", "**/*.yaml", "**/*.yml"]

        if exclude_patterns is None:
            exclude_patterns = [
                "**/venv/**",
                "**/.venv/**",
                "**/node_modules/**",
                "**/__pycache__/**",
                "**/.git/**",
                "**/.*",
            ]

        # 获取要检查的文件
        files_to_check = self._get_files_to_check(include_patterns, exclude_patterns)
        logger.info(f"发现 {len(files_to_check)} 个文件需要检查")

        # 初始化问题列表
        all_issues = []

        # 分类检查
        all_issues.extend(self._check_readability(files_to_check))
        all_issues.extend(self._check_security(files_to_check))
        all_issues.extend(self._check_performance(files_to_check))
        all_issues.extend(self._check_maintainability(files_to_check))

        # 计算分数
        score = self._calculate_score(all_issues, len(files_to_check))

        # 生成建议
        recommendations = self._generate_recommendations(all_issues, score)

        execution_time = time.time() - start_time

        # 创建报告
        report = QualityReport(
            timestamp=datetime.now().isoformat(),
            project_path=str(self.project_path),
            total_files=len(files_to_check),
            score=score,
            issues=all_issues,
            recommendations=recommendations,
            execution_time=execution_time,
        )

        logger.info(f"质量检查完成，总分: {score.total}/100 ({score.grade})")
        return report

    def _get_files_to_check(
        self, include_patterns: List[str], exclude_patterns: List[str]
    ) -> List[Path]:
        """获取需要检查的文件列表"""
        files = []

        for pattern in include_patterns:
            for file_path in self.project_path.glob(pattern):
                if file_path.is_file():
                    pass  # Auto-fixed empty block
                    # 检查是否被排除
                    should_exclude = False
                    for exclude_pattern in exclude_patterns:
                        if file_path.match(exclude_pattern):
                            should_exclude = True
                            break

                    if not should_exclude:
                        files.append(file_path)

        return sorted(list(set(files)))

    def _check_readability(self, files: List[Path]) -> List[QualityIssue]:
        """检查代码可读性"""
        issues = []
        logger.info("检查代码可读性...")

        for file_path in files:
            try:
                pass  # Auto-fixed empty block
                # Python文件检查
                if file_path.suffix == ".py":
                    issues.extend(self._check_python_readability(file_path))

                # Shell脚本检查
                elif file_path.suffix == ".sh":
                    issues.extend(self._check_shell_readability(file_path))

                # YAML文件检查
                elif file_path.suffix in [".yaml", ".yml"]:
                    issues.extend(self._check_yaml_readability(file_path))

            except Exception as e:
                logger.error(f"检查文件 {file_path} 时出错: {e}")

        logger.info(f"可读性检查完成，发现 {len(issues)} 个问题")
        return issues

    def _check_python_readability(self, file_path: Path) -> List[QualityIssue]:
        """检查Python文件可读性"""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            # 检查行长度
            max_length = self.rules["readability"]["max_line_length"]
            for i, line in enumerate(lines, 1):
                if len(line) > max_length:
                    issues.append(
                        QualityIssue(
                            file_path=str(file_path),
                            line_number=i,
                            severity="minor",
                            category="readability",
                            message=f"行长度超过限制 ({len(line)} > {max_length})",
                            rule_id="R001",
                            suggestion=f"建议将长行拆分为多行",
                        )
                    )

            # 检查文件长度
            max_file_lines = self.rules["readability"]["max_file_lines"]
            if len(lines) > max_file_lines:
                issues.append(
                    QualityIssue(
                        file_path=str(file_path),
                        line_number=1,
                        severity="major",
                        category="readability",
                        message=f"文件过长 ({len(lines)} > {max_file_lines})",
                        rule_id="R002",
                        suggestion="考虑将文件拆分为更小的模块",
                    )
                )

            # 使用flake8检查代码规范
            if self.tools["flake8"]:
                issues.extend(self._run_flake8(file_path))

            # 使用black检查格式
            if self.tools["black"]:
                issues.extend(self._run_black_check(file_path))

        except Exception as e:
            logger.error(f"检查Python文件 {file_path} 时出错: {e}")

        return issues

    def _check_shell_readability(self, file_path: Path) -> List[QualityIssue]:
        """检查Shell脚本可读性"""
        issues = []

        try:
            pass  # Auto-fixed empty block
            # 使用shellcheck检查
            if self.tools["shellcheck"]:
                issues.extend(self._run_shellcheck(file_path))

            # 基本格式检查
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            # 检查shebang
            if not lines[0].startswith("#!"):
                issues.append(
                    QualityIssue(
                        file_path=str(file_path),
                        line_number=1,
                        severity="major",
                        category="readability",
                        message="缺少shebang声明",
                        rule_id="R101",
                        suggestion="添加 #!/bin/bash 或适当的shebang",
                    )
                )

            # 检查set命令
            has_set_e = any("set -e" in line for line in lines[:10])
            if not has_set_e:
                issues.append(
                    QualityIssue(
                        file_path=str(file_path),
                        line_number=2,
                        severity="major",
                        category="readability",
                        message="建议添加 set -e 启用严格模式",
                        rule_id="R102",
                        suggestion="在脚本开头添加 set -e",
                    )
                )

        except Exception as e:
            logger.error(f"检查Shell文件 {file_path} 时出错: {e}")

        return issues

    def _check_yaml_readability(self, file_path: Path) -> List[QualityIssue]:
        """检查YAML文件可读性"""
        issues = []

        try:
            pass  # Auto-fixed empty block
            # 使用yamllint检查
            if self.tools["yamllint"]:
                issues.extend(self._run_yamllint(file_path))

            # 验证YAML语法
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError as e:
                    issues.append(
                        QualityIssue(
                            file_path=str(file_path),
                            line_number=getattr(e, "problem_mark", {}).get("line", 1),
                            severity="critical",
                            category="readability",
                            message=f"YAML语法错误: {e}",
                            rule_id="R201",
                            suggestion="修复YAML语法错误",
                        )
                    )

        except Exception as e:
            logger.error(f"检查YAML文件 {file_path} 时出错: {e}")

        return issues

    def _check_security(self, files: List[Path]) -> List[QualityIssue]:
        """检查安全性"""
        issues = []
        logger.info("检查安全性...")

        # 使用bandit检查Python安全性
        python_files = [f for f in files if f.suffix == ".py"]
        if python_files and self.tools["bandit"]:
            issues.extend(self._run_bandit(python_files))

        # 自定义安全检查
        for file_path in files:
            try:
                issues.extend(self._check_custom_security(file_path))
            except Exception as e:
                logger.error(f"安全检查文件 {file_path} 时出错: {e}")

        logger.info(f"安全检查完成，发现 {len(issues)} 个问题")
        return issues

    def _check_custom_security(self, file_path: Path) -> List[QualityIssue]:
        """自定义安全检查"""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            # 检查硬编码密码/密钥
            sensitive_patterns = [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']',
            ]

            import re

            for i, line in enumerate(lines, 1):
                for pattern in sensitive_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append(
                            QualityIssue(
                                file_path=str(file_path),
                                line_number=i,
                                severity="critical",
                                category="security",
                                message="检测到可能的硬编码敏感信息",
                                rule_id="S001",
                                suggestion="使用环境变量或配置文件存储敏感信息",
                            )
                        )

            # 检查命令注入风险 (Shell脚本)
            if file_path.suffix == ".sh":
                dangerous_patterns = [r"eval\s+", r"\$\([^)]*\$", r"`[^`]*\$"]

                for i, line in enumerate(lines, 1):
                    for pattern in dangerous_patterns:
                        if re.search(pattern, line):
                            issues.append(
                                QualityIssue(
                                    file_path=str(file_path),
                                    line_number=i,
                                    severity="major",
                                    category="security",
                                    message="检测到潜在的命令注入风险",
                                    rule_id="S101",
                                    suggestion="避免动态命令执行，使用安全的替代方案",
                                )
                            )

        except Exception as e:
            logger.error(f"自定义安全检查失败: {e}")

        return issues

    def _check_performance(self, files: List[Path]) -> List[QualityIssue]:
        """检查性能"""
        issues = []
        logger.info("检查性能...")

        for file_path in files:
            try:
                if file_path.suffix == ".py":
                    issues.extend(self._check_python_performance(file_path))
                elif file_path.suffix == ".sh":
                    issues.extend(self._check_shell_performance(file_path))
            except Exception as e:
                logger.error(f"性能检查文件 {file_path} 时出错: {e}")

        logger.info(f"性能检查完成，发现 {len(issues)} 个问题")
        return issues

    def _check_python_performance(self, file_path: Path) -> List[QualityIssue]:
        """检查Python性能"""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            import re

            # 检查低效的字符串拼接
            for i, line in enumerate(lines, 1):
                if re.search(r'\+\s*=\s*["\']', line):
                    issues.append(
                        QualityIssue(
                            file_path=str(file_path),
                            line_number=i,
                            severity="minor",
                            category="performance",
                            message="检测到低效的字符串拼接",
                            rule_id="P001",
                            suggestion="考虑使用join()或f-string",
                        )
                    )

            # 检查循环中的重复计算
            in_loop = False
            for i, line in enumerate(lines, 1):
                if re.search(r"for\s+\w+\s+in", line):
                    in_loop = True
                elif line.strip() == "" or not line.startswith(" "):
                    in_loop = False

                if in_loop and re.search(r"len\(", line):
                    issues.append(
                        QualityIssue(
                            file_path=str(file_path),
                            line_number=i,
                            severity="minor",
                            category="performance",
                            message="循环中重复计算len()",
                            rule_id="P002",
                            suggestion="将len()计算移到循环外",
                        )
                    )

        except Exception as e:
            logger.error(f"Python性能检查失败: {e}")

        return issues

    def _check_shell_performance(self, file_path: Path) -> List[QualityIssue]:
        """检查Shell脚本性能"""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            import re

            # 检查频繁的外部命令调用
            for i, line in enumerate(lines, 1):
                pass  # Auto-fixed empty block
                # 检查在循环中使用外部命令
                if "while" in line or "for" in line:
                    pass  # Auto-fixed empty block
                    # 简单检查下几行是否有外部命令
                    for j in range(i, min(i + 10, len(lines))):
                        if re.search(r"(grep|sed|awk|cut)\s", lines[j]):
                            issues.append(
                                QualityIssue(
                                    file_path=str(file_path),
                                    line_number=j + 1,
                                    severity="minor",
                                    category="performance",
                                    message="循环中使用外部命令可能影响性能",
                                    rule_id="P101",
                                    suggestion="考虑使用内置的bash功能",
                                )
                            )
                            break

        except Exception as e:
            logger.error(f"Shell性能检查失败: {e}")

        return issues

    def _check_maintainability(self, files: List[Path]) -> List[QualityIssue]:
        """检查可维护性"""
        issues = []
        logger.info("检查可维护性...")

        # 检查测试覆盖率
        if self.tools["pytest"]:
            issues.extend(self._check_test_coverage())

        # 检查代码重复
        issues.extend(self._check_code_duplication(files))

        # 检查类型提示 (Python)
        python_files = [f for f in files if f.suffix == ".py"]
        for file_path in python_files:
            issues.extend(self._check_type_hints(file_path))

        logger.info(f"可维护性检查完成，发现 {len(issues)} 个问题")
        return issues

    def _check_test_coverage(self) -> List[QualityIssue]:
        """检查测试覆盖率"""
        issues = []

        try:
            pass  # Auto-fixed empty block
            # 运行pytest获取覆盖率
            result = subprocess.run(
                [
                    "pytest",
                    "--cov=.claude",
                    "--cov-report=json",
                    "--cov-report=term-missing",
                    "--quiet",
                ],
                capture_output=True,
                text=True,
                cwd=self.project_path,
            )

            # 查找coverage.json文件
            coverage_file = self.project_path / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, "r") as f:
                    coverage_data = json.load(f)

                total_coverage = coverage_data.get("totals", {}).get(
                    "percent_covered", 0
                )
                min_coverage = self.rules["maintainability"]["min_test_coverage"]

                if total_coverage < min_coverage:
                    issues.append(
                        QualityIssue(
                            file_path="项目整体",
                            line_number=1,
                            severity="major",
                            category="maintainability",
                            message=f"测试覆盖率不足 ({total_coverage:.1f}% < {min_coverage}%)",
                            rule_id="M001",
                            suggestion="增加单元测试提高覆盖率",
                        )
                    )

        except Exception as e:
            logger.warning(f"测试覆盖率检查失败: {e}")

        return issues

    def _check_code_duplication(self, files: List[Path]) -> List[QualityIssue]:
        """检查代码重复"""
        issues = []

        try:
            pass  # Auto-fixed empty block
            # 简单的代码重复检查 - 计算文件内容哈希
            file_hashes = {}

            for file_path in files:
                if file_path.suffix in [".py", ".sh"]:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        # 去除空白和注释后计算哈希
                        normalized = re.sub(r"#.*$", "", content, flags=re.MULTILINE)
                        normalized = re.sub(r"\s+", " ", normalized).strip()

                        if len(normalized) > 100:  # 只检查足够长的文件
                            content_hash = hashlib.md5(normalized.encode()).hexdigest()

                            if content_hash in file_hashes:
                                issues.append(
                                    QualityIssue(
                                        file_path=str(file_path),
                                        line_number=1,
                                        severity="major",
                                        category="maintainability",
                                        message=f"检测到重复代码，与 {file_hashes[content_hash]} 相似",
                                        rule_id="M002",
                                        suggestion="考虑提取公共代码到共享模块",
                                    )
                                )
                            else:
                                file_hashes[content_hash] = str(file_path)

        except Exception as e:
            logger.error(f"代码重复检查失败: {e}")

        return issues

    def _check_type_hints(self, file_path: Path) -> List[QualityIssue]:
        """检查Python类型提示"""
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            import ast

            try:
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        pass  # Auto-fixed empty block
                        # 检查函数参数类型提示
                        for arg in node.args.args:
                            if arg.annotation is None and arg.arg != "self":
                                issues.append(
                                    QualityIssue(
                                        file_path=str(file_path),
                                        line_number=node.lineno,
                                        severity="minor",
                                        category="maintainability",
                                        message=f"函数 {node.name} 的参数 {arg.arg} 缺少类型提示",
                                        rule_id="M003",
                                        suggestion="添加类型提示提高代码可读性",
                                    )
                                )

                        # 检查返回值类型提示
                        if node.returns is None and node.name != "__init__":
                            issues.append(
                                QualityIssue(
                                    file_path=str(file_path),
                                    line_number=node.lineno,
                                    severity="minor",
                                    category="maintainability",
                                    message=f"函数 {node.name} 缺少返回值类型提示",
                                    rule_id="M004",
                                    suggestion="添加返回值类型提示",
                                )
                            )

            except SyntaxError:
                pass  # Auto-fixed empty block
                # 语法错误，跳过类型检查
                pass

        except Exception as e:
            logger.error(f"类型提示检查失败: {e}")

        return issues

    def _run_flake8(self, file_path: Path) -> List[QualityIssue]:
        """运行flake8检查"""
        issues = []

        try:
            result = subprocess.run(
                ["flake8", "--format=json", str(file_path)],
                capture_output=True,
                text=True,
            )

            if result.stdout:
                flake8_issues = json.loads(result.stdout)
                for issue in flake8_issues:
                    issues.append(
                        QualityIssue(
                            file_path=issue["filename"],
                            line_number=issue["line_number"],
                            severity="minor",
                            category="readability",
                            message=f"Flake8: {issue['text']}",
                            rule_id=issue["code"],
                            suggestion="修复代码规范问题",
                        )
                    )

        except Exception as e:
            logger.debug(f"flake8检查失败: {e}")

        return issues

    def _run_black_check(self, file_path: Path) -> List[QualityIssue]:
        """运行black格式检查"""
        issues = []

        try:
            result = subprocess.run(
                ["black", "--check", "--diff", str(file_path)],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0 and result.stdout:
                issues.append(
                    QualityIssue(
                        file_path=str(file_path),
                        line_number=1,
                        severity="minor",
                        category="readability",
                        message="代码格式不符合black标准",
                        rule_id="BLACK001",
                        suggestion="运行 black 命令格式化代码",
                    )
                )

        except Exception as e:
            logger.debug(f"black检查失败: {e}")

        return issues

    def _run_shellcheck(self, file_path: Path) -> List[QualityIssue]:
        """运行shellcheck检查"""
        issues = []

        try:
            result = subprocess.run(
                ["shellcheck", "-f", "json", str(file_path)],
                capture_output=True,
                text=True,
            )

            if result.stdout:
                shellcheck_issues = json.loads(result.stdout)
                for issue in shellcheck_issues:
                    severity_map = {
                        "error": "critical",
                        "warning": "major",
                        "info": "minor",
                        "style": "minor",
                    }

                    issues.append(
                        QualityIssue(
                            file_path=str(file_path),
                            line_number=issue["line"],
                            severity=severity_map.get(issue["level"], "minor"),
                            category="readability",
                            message=f"ShellCheck: {issue['message']}",
                            rule_id=f"SC{issue['code']}",
                            suggestion="修复shell脚本问题",
                        )
                    )

        except Exception as e:
            logger.debug(f"shellcheck检查失败: {e}")

        return issues

    def _run_yamllint(self, file_path: Path) -> List[QualityIssue]:
        """运行yamllint检查"""
        issues = []

        try:
            result = subprocess.run(
                ["yamllint", "-f", "parsable", str(file_path)],
                capture_output=True,
                text=True,
            )

            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if ":" in line:
                        parts = line.split(":")
                        if len(parts) >= 4:
                            issues.append(
                                QualityIssue(
                                    file_path=parts[0],
                                    line_number=int(parts[1]),
                                    severity="minor",
                                    category="readability",
                                    message=f"YAML: {':'.join(parts[3:])}",
                                    rule_id="YAML001",
                                    suggestion="修复YAML格式问题",
                                )
                            )

        except Exception as e:
            logger.debug(f"yamllint检查失败: {e}")

        return issues

    def _run_bandit(self, files: List[Path]) -> List[QualityIssue]:
        """运行bandit安全检查"""
        issues = []

        try:
            pass  # Auto-fixed empty block
            # 创建临时文件列表
            files_list = self.temp_dir / "bandit_files.txt"
            with open(files_list, "w") as f:
                for file_path in files:
                    f.write(f"{file_path}\n")

            result = subprocess.run(
                ["bandit", "-f", "json", "-r", str(self.project_path / ".claude")],
                capture_output=True,
                text=True,
            )

            if result.stdout:
                bandit_report = json.loads(result.stdout)
                for issue in bandit_report.get("results", []):
                    severity_map = {
                        "HIGH": "critical",
                        "MEDIUM": "major",
                        "LOW": "minor",
                    }

                    issues.append(
                        QualityIssue(
                            file_path=issue["filename"],
                            line_number=issue["line_number"],
                            severity=severity_map.get(issue["issue_severity"], "minor"),
                            category="security",
                            message=f"Bandit: {issue['issue_text']}",
                            rule_id=issue["test_id"],
                            suggestion="修复安全问题",
                        )
                    )

        except Exception as e:
            logger.debug(f"bandit检查失败: {e}")

        return issues

    def _calculate_score(
        self, issues: List[QualityIssue], total_files: int
    ) -> QualityScore:
        """计算质量分数"""
        score = QualityScore()

        # 按类别分组问题
        category_issues = {}
        for issue in issues:
            if issue.category not in category_issues:
                category_issues[issue.category] = []
            category_issues[issue.category].append(issue)

        # 计算各项分数
        score.readability = self._calculate_category_score(
            category_issues.get("readability", []), 25, total_files
        )

        score.security = self._calculate_category_score(
            category_issues.get("security", []), 30, total_files
        )

        score.performance = self._calculate_category_score(
            category_issues.get("performance", []), 20, total_files
        )

        score.maintainability = self._calculate_category_score(
            category_issues.get("maintainability", []), 25, total_files
        )

        return score

    def _calculate_category_score(
        self, issues: List[QualityIssue], max_score: int, total_files: int
    ) -> int:
        """计算单个类别分数"""
        if not issues:
            return max_score

        # 按严重性分配权重
        severity_weights = {"critical": 10, "major": 5, "minor": 2, "info": 1}

        total_penalty = sum(severity_weights.get(issue.severity, 1) for issue in issues)

        # 根据文件数量调整惩罚
        normalized_penalty = total_penalty / max(total_files, 1)

        # 计算分数（确保不低于0）
        score = max(0, max_score - int(normalized_penalty))

        return score

    def _generate_recommendations(
        self, issues: List[QualityIssue], score: QualityScore
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 按严重性分类问题
        critical_issues = [i for i in issues if i.severity == "critical"]
        major_issues = [i for i in issues if i.severity == "major"]

        if critical_issues:
            recommendations.append(f"🚨 高优先级：修复 {len(critical_issues)} 个严重安全问题")

        if major_issues:
            recommendations.append(f"⚠️ 中优先级：解决 {len(major_issues)} 个重要质量问题")

        # 按类别提供具体建议
        if score.readability < 20:
            recommendations.append("📖 改进代码可读性：统一代码格式，增加注释")

        if score.security < 25:
            recommendations.append("🔒 加强安全性：修复安全漏洞，添加输入验证")

        if score.performance < 15:
            recommendations.append("⚡ 优化性能：优化算法，减少资源消耗")

        if score.maintainability < 20:
            recommendations.append("🔧 提高可维护性：增加测试，添加类型提示")

        # 工具使用建议
        if not self.tools["black"]:
            recommendations.append("🛠️ 安装并使用 black 进行代码格式化")

        if not self.tools["flake8"]:
            recommendations.append("🛠️ 安装并使用 flake8 进行代码规范检查")

        return recommendations

    def generate_report(self, report: QualityReport, output_file: str = None) -> str:
        """生成质量报告"""
        if output_file is None:
            output_file = (
                f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            )

        output_path = self.project_path / output_file

        # 生成Markdown报告
        content = f"""# 代码质量审查报告

## 📊 总体评分: {report.score.total}/100 ({report.score.grade})

**检查时间**: {report.timestamp}
**项目路径**: {report.project_path}
**检查文件数**: {report.total_files}
**执行时间**: {report.execution_time:.2f}秒

### 🎯 分项得分
- **可读性**: {report.score.readability}/25
- **安全性**: {report.score.security}/30
- **性能**: {report.score.performance}/20
- **可维护性**: {report.score.maintainability}/25

### 📋 问题统计
"""

        # 统计问题
        issue_stats = {}
        severity_stats = {}

        for issue in report.issues:
            pass  # Auto-fixed empty block
            # 按类别统计
            if issue.category not in issue_stats:
                issue_stats[issue.category] = 0
            issue_stats[issue.category] += 1

            # 按严重性统计
            if issue.severity not in severity_stats:
                severity_stats[issue.severity] = 0
            severity_stats[issue.severity] += 1

        content += "\n#### 按类别分布\n"
        for category, count in issue_stats.items():
            content += f"- {category}: {count}个\n"

        content += "\n#### 按严重性分布\n"
        for severity, count in severity_stats.items():
            icon = {"critical": "🚨", "major": "⚠️", "minor": "💡", "info": "ℹ️"}.get(
                severity, "•"
            )
            content += f"- {icon} {severity}: {count}个\n"

        # 详细问题列表
        if report.issues:
            content += "\n### 🔍 详细问题列表\n\n"

            # 按文件分组
            issues_by_file = {}
            for issue in report.issues:
                if issue.file_path not in issues_by_file:
                    issues_by_file[issue.file_path] = []
                issues_by_file[issue.file_path].append(issue)

            for file_path, file_issues in issues_by_file.items():
                rel_path = (
                    Path(file_path).relative_to(self.project_path)
                    if Path(file_path).is_absolute()
                    else file_path
                )
                content += f"#### 📄 {rel_path}\n\n"

                for issue in sorted(file_issues, key=lambda x: x.line_number):
                    severity_icon = {
                        "critical": "🚨",
                        "major": "⚠️",
                        "minor": "💡",
                        "info": "ℹ️",
                    }.get(issue.severity, "•")

                    content += f"**{severity_icon} 第{issue.line_number}行** [{issue.rule_id}] {issue.message}\n"
                    if issue.suggestion:
                        content += f"  💡 建议: {issue.suggestion}\n"
                    content += "\n"

        # 改进建议
        if report.recommendations:
            content += "\n### 💡 改进建议\n\n"
            for rec in report.recommendations:
                content += f"- {rec}\n"

        # 质量改进行动计划
        content += "\n### 📋 行动计划\n\n"

        critical_count = len([i for i in report.issues if i.severity == "critical"])
        major_count = len([i for i in report.issues if i.severity == "major"])
        minor_count = len([i for i in report.issues if i.severity == "minor"])

        if critical_count > 0:
            content += f"- [ ] **立即处理**: 修复 {critical_count} 个严重问题\n"

        if major_count > 0:
            content += f"- [ ] **本周内**: 解决 {major_count} 个重要问题\n"

        if minor_count > 0:
            content += f"- [ ] **逐步改进**: 优化 {minor_count} 个次要问题\n"

        content += "\n### 🏆 质量改进目标\n\n"
        if report.score.total < 70:
            content += "- 🎯 短期目标: 达到70分（及格线）\n"
            content += "- 🎯 中期目标: 达到80分（良好）\n"
            content += "- 🎯 长期目标: 达到90分（优秀）\n"
        elif report.score.total < 80:
            content += "- 🎯 短期目标: 达到80分（良好）\n"
            content += "- 🎯 长期目标: 达到90分（优秀）\n"
        elif report.score.total < 90:
            content += "- 🎯 目标: 达到90分（优秀）\n"
        else:
            content += "- 🏆 恭喜！已达到优秀水平，继续保持！\n"

        content += f"\n---\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        content += f"*质量检查工具: Claude Enhancer Quality Checker v1.0.0*\n"

        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"质量报告已保存到: {output_path}")
        return str(output_path)

    def save_json_report(self, report: QualityReport, output_file: str = None) -> str:
        """保存JSON格式报告"""
        if output_file is None:
            output_file = (
                f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

        output_path = self.project_path / output_file

        # 转换为可序列化的字典
        report_dict = {
            "timestamp": report.timestamp,
            "project_path": report.project_path,
            "total_files": report.total_files,
            "score": asdict(report.score),
            "issues": [asdict(issue) for issue in report.issues],
            "recommendations": report.recommendations,
            "execution_time": report.execution_time,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"JSON报告已保存到: {output_path}")
        return str(output_path)


def main():
    """CLI入口"""
    parser = argparse.ArgumentParser(
        description="Claude Enhancer 5.0 代码质量检查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python quality_checker.py --project /path/to/project
  python quality_checker.py --include "**/*.py" --exclude "**/test_*"
  python quality_checker.py --output-format both --report-name my_report
        """,
    )

    parser.add_argument("--project", "-p", default=".", help="项目路径 (默认: 当前目录)")

    parser.add_argument(
        "--include",
        nargs="+",
        default=["**/*.py", "**/*.sh", "**/*.yaml", "**/*.yml"],
        help="包含的文件模式 (默认: Python, Shell, YAML文件)",
    )

    parser.add_argument(
        "--exclude",
        nargs="+",
        default=[
            "**/venv/**",
            "**/.venv/**",
            "**/node_modules/**",
            "**/.__pycache__/**",
            "**/.git/**",
        ],
        help="排除的文件模式",
    )

    parser.add_argument(
        "--output-format",
        choices=["markdown", "json", "both"],
        default="markdown",
        help="输出格式 (默认: markdown)",
    )

    parser.add_argument("--report-name", help="报告文件名前缀")

    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    parser.add_argument("--config", help="自定义配置文件路径")

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        pass  # Auto-fixed empty block
        # 创建质量检查器
        checker = QualityChecker(args.project)

        # 执行检查
        report = checker.check_project(args.include, args.exclude)

        # 生成报告
        if args.output_format in ["markdown", "both"]:
            md_file = args.report_name + ".md" if args.report_name else None
            md_path = checker.generate_report(report, md_file)
            print(f"📄 Markdown报告: {md_path}")

        if args.output_format in ["json", "both"]:
            json_file = args.report_name + ".json" if args.report_name else None
            json_path = checker.save_json_report(report, json_file)
            print(f"📊 JSON报告: {json_path}")

        # 输出摘要
        print(f"\n🎯 质量检查完成")
        print(f"总分: {report.score.total}/100 ({report.score.grade})")
        print(f"问题总数: {len(report.issues)}")

        # 根据质量分数设置退出码
        if report.score.total >= 80:
            sys.exit(0)  # 良好及以上
        elif report.score.total >= 70:
            sys.exit(1)  # 及格但需改进
        else:
            sys.exit(2)  # 不及格

    except KeyboardInterrupt:
        print("\n❌ 检查被中断")
        sys.exit(130)

    except Exception as e:
        logger.error(f"质量检查失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
