#!/usr/bin/env python3
"""
Perfect21 代码质量门
===================

检查代码质量指标，包括复杂度、重复度、代码风格等
"""

import asyncio
import json
import subprocess
import ast
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .models import GateResult, GateStatus, GateSeverity


class CodeQualityGate:
    """代码质量门"""

    def __init__(self, project_root: str, config):
        self.project_root = Path(project_root)
        self.config = config

    async def check(self, context: str = "commit") -> GateResult:
        """执行代码质量检查"""
        start_time = datetime.now()
        violations = []
        details = {}
        suggestions = []

        try:
            # 1. 代码复杂度检查
            complexity_result = await self._check_complexity()
            details["complexity"] = complexity_result
            if complexity_result["max_complexity"] > self.config.max_complexity:
                violations.append({
                    "type": "high_complexity",
                    "message": f"发现过高复杂度: {complexity_result['max_complexity']} > {self.config.max_complexity}",
                    "file": complexity_result["highest_complexity_file"],
                    "severity": "high"
                })
                suggestions.append("重构复杂度过高的函数")

            # 2. 代码重复检查
            duplication_result = await self._check_duplications()
            details["duplications"] = duplication_result
            if duplication_result["duplication_percentage"] > self.config.max_duplications:
                violations.append({
                    "type": "high_duplication",
                    "message": f"代码重复率过高: {duplication_result['duplication_percentage']:.1f}% > {self.config.max_duplications}%",
                    "severity": "medium"
                })
                suggestions.append("消除代码重复")

            # 3. 代码风格检查
            style_result = await self._check_code_style()
            details["style"] = style_result
            if style_result["violations"] > 0:
                violations.append({
                    "type": "style_violations",
                    "message": f"发现 {style_result['violations']} 个代码风格问题",
                    "severity": "low"
                })
                suggestions.append("修复代码风格问题")

            # 4. 语法和导入检查
            syntax_result = await self._check_syntax_and_imports()
            details["syntax"] = syntax_result
            if syntax_result["syntax_errors"] > 0 or syntax_result["import_errors"] > 0:
                violations.append({
                    "type": "syntax_errors",
                    "message": f"语法错误: {syntax_result['syntax_errors']}, 导入错误: {syntax_result['import_errors']}",
                    "severity": "critical"
                })
                suggestions.append("修复语法和导入错误")

            # 5. 文档字符串检查
            docstring_result = await self._check_docstrings()
            details["docstrings"] = docstring_result
            if docstring_result["coverage"] < 70:  # 文档覆盖率阈值
                violations.append({
                    "type": "insufficient_documentation",
                    "message": f"文档覆盖率过低: {docstring_result['coverage']:.1f}%",
                    "severity": "medium"
                })
                suggestions.append("增加函数和类的文档字符串")

            # 计算总体分数
            score = self._calculate_quality_score(details, violations)

            # 确定状态
            if violations:
                critical_violations = [v for v in violations if v["severity"] == "critical"]
                high_violations = [v for v in violations if v["severity"] == "high"]

                if critical_violations:
                    status = GateStatus.FAILED
                    severity = GateSeverity.CRITICAL
                elif high_violations:
                    status = GateStatus.FAILED
                    severity = GateSeverity.HIGH
                elif score < self.config.min_code_quality_score:
                    status = GateStatus.FAILED
                    severity = GateSeverity.MEDIUM
                else:
                    status = GateStatus.WARNING
                    severity = GateSeverity.LOW
            else:
                status = GateStatus.PASSED
                severity = GateSeverity.INFO

            execution_time = (datetime.now() - start_time).total_seconds()

            return GateResult(
                gate_name="code_quality",
                status=status,
                severity=severity,
                score=score,
                message=self._generate_message(score, len(violations)),
                details=details,
                violations=violations,
                suggestions=suggestions,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                metadata={"context": context, "files_checked": details.get("syntax", {}).get("files_checked", 0)}
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return GateResult(
                gate_name="code_quality",
                status=GateStatus.FAILED,
                severity=GateSeverity.HIGH,
                score=0.0,
                message=f"代码质量检查失败: {str(e)}",
                details={"error": str(e)},
                violations=[{"type": "check_error", "message": str(e), "severity": "high"}],
                suggestions=["检查代码质量工具配置"],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                metadata={"context": context}
            )

    async def _check_complexity(self) -> Dict[str, Any]:
        """检查代码复杂度"""
        try:
            python_files = list(self.project_root.rglob("*.py"))
            # 排除特定目录
            python_files = [f for f in python_files if not any(exclude in str(f) for exclude in
                           ['venv', '__pycache__', '.git', 'core/claude-code-unified-agents'])]

            max_complexity = 0
            highest_complexity_file = ""
            complexity_violations = []

            for py_file in python_files:
                try:
                    result = subprocess.run(
                        ['python3', '-m', 'radon', 'cc', str(py_file), '-j'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode == 0 and result.stdout:
                        data = json.loads(result.stdout)
                        file_rel_path = str(py_file.relative_to(self.project_root))

                        if file_rel_path in data:
                            for item in data[file_rel_path]:
                                complexity = item.get('complexity', 0)
                                if complexity > max_complexity:
                                    max_complexity = complexity
                                    highest_complexity_file = file_rel_path

                                if complexity > self.config.max_complexity:
                                    complexity_violations.append({
                                        "file": file_rel_path,
                                        "function": item.get('name', 'unknown'),
                                        "complexity": complexity,
                                        "line": item.get('lineno', 0)
                                    })

                except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
                    continue

            return {
                "max_complexity": max_complexity,
                "highest_complexity_file": highest_complexity_file,
                "violations": complexity_violations,
                "files_checked": len(python_files)
            }

        except Exception:
            # 如果radon不可用，使用简单的AST分析
            return await self._simple_complexity_check()

    async def _simple_complexity_check(self) -> Dict[str, Any]:
        """简单的复杂度检查（不依赖外部工具）"""
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not any(exclude in str(f) for exclude in
                       ['venv', '__pycache__', '.git', 'core/claude-code-unified-agents'])]

        max_complexity = 0
        highest_complexity_file = ""
        complexity_violations = []

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)

                class ComplexityVisitor(ast.NodeVisitor):
                    def __init__(self):
                        self.complexity = 1  # 基础复杂度

                    def visit_If(self, node):
                        self.complexity += 1
                        self.generic_visit(node)

                    def visit_While(self, node):
                        self.complexity += 1
                        self.generic_visit(node)

                    def visit_For(self, node):
                        self.complexity += 1
                        self.generic_visit(node)

                    def visit_Try(self, node):
                        self.complexity += 1
                        self.generic_visit(node)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        visitor = ComplexityVisitor()
                        visitor.visit(node)

                        file_rel_path = str(py_file.relative_to(self.project_root))

                        if visitor.complexity > max_complexity:
                            max_complexity = visitor.complexity
                            highest_complexity_file = file_rel_path

                        if visitor.complexity > self.config.max_complexity:
                            complexity_violations.append({
                                "file": file_rel_path,
                                "function": node.name,
                                "complexity": visitor.complexity,
                                "line": node.lineno
                            })

            except Exception:
                continue

        return {
            "max_complexity": max_complexity,
            "highest_complexity_file": highest_complexity_file,
            "violations": complexity_violations,
            "files_checked": len(python_files)
        }

    async def _check_duplications(self) -> Dict[str, Any]:
        """检查代码重复"""
        try:
            # 使用简单的行级重复检测
            python_files = list(self.project_root.rglob("*.py"))
            python_files = [f for f in python_files if not any(exclude in str(f) for exclude in
                           ['venv', '__pycache__', '.git', 'core/claude-code-unified-agents'])]

            all_lines = []
            line_occurrences = {}

            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    for i, line in enumerate(lines):
                        clean_line = line.strip()
                        if len(clean_line) > 10 and not clean_line.startswith('#'):  # 忽略短行和注释
                            all_lines.append(clean_line)
                            if clean_line not in line_occurrences:
                                line_occurrences[clean_line] = []
                            line_occurrences[clean_line].append((str(py_file.relative_to(self.project_root)), i + 1))

                except Exception:
                    continue

            # 计算重复率
            duplicated_lines = sum(1 for line, occurrences in line_occurrences.items() if len(occurrences) > 1)
            total_lines = len(all_lines)
            duplication_percentage = (duplicated_lines / total_lines * 100) if total_lines > 0 else 0

            # 找出重复最多的代码块
            duplications = sorted(
                [(line, occurrences) for line, occurrences in line_occurrences.items() if len(occurrences) > 1],
                key=lambda x: len(x[1]),
                reverse=True
            )[:10]

            return {
                "duplication_percentage": duplication_percentage,
                "duplicated_lines": duplicated_lines,
                "total_lines": total_lines,
                "top_duplications": duplications,
                "files_checked": len(python_files)
            }

        except Exception as e:
            return {
                "duplication_percentage": 0,
                "error": str(e),
                "files_checked": 0
            }

    async def _check_code_style(self) -> Dict[str, Any]:
        """检查代码风格"""
        try:
            python_files = list(self.project_root.rglob("*.py"))
            python_files = [f for f in python_files if not any(exclude in str(f) for exclude in
                           ['venv', '__pycache__', '.git', 'core/claude-code-unified-agents'])]

            total_violations = 0
            style_issues = []

            for py_file in python_files:
                try:
                    # 使用flake8检查代码风格
                    result = subprocess.run(
                        ['python3', '-m', 'flake8', '--max-line-length=88', str(py_file)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.stdout:
                        violations = result.stdout.strip().split('\n')
                        total_violations += len(violations)

                        for violation in violations[:5]:  # 只记录前5个
                            if violation:
                                style_issues.append({
                                    "file": str(py_file.relative_to(self.project_root)),
                                    "issue": violation
                                })

                except (subprocess.TimeoutExpired, FileNotFoundError):
                    # 如果flake8不可用，使用简单检查
                    simple_issues = await self._simple_style_check(py_file)
                    total_violations += len(simple_issues)
                    style_issues.extend(simple_issues)

            return {
                "violations": total_violations,
                "issues": style_issues,
                "files_checked": len(python_files)
            }

        except Exception as e:
            return {
                "violations": 0,
                "error": str(e),
                "files_checked": 0
            }

    async def _simple_style_check(self, py_file: Path) -> List[Dict[str, Any]]:
        """简单的代码风格检查"""
        issues = []
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            file_rel_path = str(py_file.relative_to(self.project_root))

            for i, line in enumerate(lines):
                line_no = i + 1

                # 检查行长度
                if len(line.rstrip()) > 88:
                    issues.append({
                        "file": file_rel_path,
                        "issue": f"Line {line_no}: Line too long ({len(line.rstrip())} > 88)"
                    })

                # 检查尾随空格
                if line.rstrip() != line.rstrip('\n'):
                    issues.append({
                        "file": file_rel_path,
                        "issue": f"Line {line_no}: Trailing whitespace"
                    })

        except Exception:
            pass

        return issues

    async def _check_syntax_and_imports(self) -> Dict[str, Any]:
        """检查语法和导入错误"""
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not any(exclude in str(f) for exclude in
                       ['venv', '__pycache__', '.git', 'core/claude-code-unified-agents'])]

        syntax_errors = 0
        import_errors = 0
        error_details = []

        for py_file in python_files:
            try:
                # 检查语法
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                try:
                    ast.parse(content)
                except SyntaxError as e:
                    syntax_errors += 1
                    error_details.append({
                        "type": "syntax",
                        "file": str(py_file.relative_to(self.project_root)),
                        "line": e.lineno,
                        "message": str(e)
                    })

                # 检查导入（简单检查）
                try:
                    result = subprocess.run(
                        ['python3', '-m', 'py_compile', str(py_file)],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        cwd=str(self.project_root)
                    )

                    if result.returncode != 0 and 'import' in result.stderr.lower():
                        import_errors += 1
                        error_details.append({
                            "type": "import",
                            "file": str(py_file.relative_to(self.project_root)),
                            "message": result.stderr.strip()
                        })

                except subprocess.TimeoutExpired:
                    pass

            except Exception:
                continue

        return {
            "syntax_errors": syntax_errors,
            "import_errors": import_errors,
            "error_details": error_details,
            "files_checked": len(python_files)
        }

    async def _check_docstrings(self) -> Dict[str, Any]:
        """检查文档字符串覆盖率"""
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not any(exclude in str(f) for exclude in
                       ['venv', '__pycache__', '.git', 'core/claude-code-unified-agents'])]

        total_functions = 0
        documented_functions = 0
        total_classes = 0
        documented_classes = 0

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        total_functions += 1
                        if ast.get_docstring(node):
                            documented_functions += 1

                    elif isinstance(node, ast.ClassDef):
                        total_classes += 1
                        if ast.get_docstring(node):
                            documented_classes += 1

            except Exception:
                continue

        total_items = total_functions + total_classes
        documented_items = documented_functions + documented_classes
        coverage = (documented_items / total_items * 100) if total_items > 0 else 100

        return {
            "coverage": coverage,
            "total_functions": total_functions,
            "documented_functions": documented_functions,
            "total_classes": total_classes,
            "documented_classes": documented_classes,
            "files_checked": len(python_files)
        }

    def _calculate_quality_score(self, details: Dict[str, Any], violations: List[Dict[str, Any]]) -> float:
        """计算代码质量分数"""
        base_score = 100.0

        # 复杂度扣分
        complexity_data = details.get("complexity", {})
        max_complexity = complexity_data.get("max_complexity", 0)
        if max_complexity > self.config.max_complexity:
            excess = max_complexity - self.config.max_complexity
            base_score -= min(excess * 5, 30)  # 最多扣30分

        # 重复度扣分
        duplication_data = details.get("duplications", {})
        duplication_pct = duplication_data.get("duplication_percentage", 0)
        if duplication_pct > self.config.max_duplications:
            excess = duplication_pct - self.config.max_duplications
            base_score -= min(excess * 2, 20)  # 最多扣20分

        # 风格问题扣分
        style_data = details.get("style", {})
        style_violations = style_data.get("violations", 0)
        base_score -= min(style_violations * 0.5, 15)  # 最多扣15分

        # 语法错误扣分
        syntax_data = details.get("syntax", {})
        syntax_errors = syntax_data.get("syntax_errors", 0)
        import_errors = syntax_data.get("import_errors", 0)
        base_score -= syntax_errors * 20  # 语法错误严重扣分
        base_score -= import_errors * 10

        # 文档覆盖率扣分
        docstring_data = details.get("docstrings", {})
        doc_coverage = docstring_data.get("coverage", 100)
        if doc_coverage < 70:
            base_score -= (70 - doc_coverage) * 0.5

        # 确保分数在0-100范围内
        return max(0.0, min(100.0, base_score))

    def _generate_message(self, score: float, violation_count: int) -> str:
        """生成检查消息"""
        if score >= 90:
            return f"代码质量优秀 (分数: {score:.1f})"
        elif score >= 80:
            return f"代码质量良好 (分数: {score:.1f})"
        elif score >= 70:
            return f"代码质量一般 (分数: {score:.1f}, {violation_count}个问题)"
        elif score >= 60:
            return f"代码质量较差 (分数: {score:.1f}, {violation_count}个问题)"
        else:
            return f"代码质量很差 (分数: {score:.1f}, {violation_count}个问题)"