#!/usr/bin/env python3
"""
Perfect21 Git Hooks - Commit Quality Plugin
代码提交质量检查插件
"""

import os
import re
import ast
import subprocess
from typing import Dict, Any, List, Optional

try:
    from ..base_plugin import (
        QualityCheckPlugin, PluginResult, PluginStatus, PluginMetadata, PluginPriority
    )
except ImportError:
    from features.git_workflow.plugins.base_plugin import (
        QualityCheckPlugin, PluginResult, PluginStatus, PluginMetadata, PluginPriority
    )


class CommitQualityPlugin(QualityCheckPlugin):
    """代码提交质量检查插件"""

    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="commit_quality",
            version="2.2.0",
            description="代码提交质量检查，包括语法、格式、文档等",
            author="Perfect21 Team",
            category="commit_workflow",
            priority=PluginPriority.CRITICAL,
            dependencies=["python:ast"],
            supports_parallel=True,
            timeout=120
        )

    def execute(self, context: Dict[str, Any]) -> PluginResult:
        """执行代码质量检查"""
        staged_files = self.get_staged_files()

        if not staged_files:
            return PluginResult(
                status=PluginStatus.SKIPPED,
                message="没有已暂存的文件需要检查"
            )

        # 过滤需要检查的文件类型
        checkable_files = self._filter_checkable_files(staged_files)

        if not checkable_files:
            return PluginResult(
                status=PluginStatus.SKIPPED,
                message="没有需要检查质量的文件类型"
            )

        # 执行质量检查
        results = []
        total_issues = 0

        for file_path in checkable_files:
            file_result = self._check_file_comprehensive(file_path)
            results.append(file_result)
            total_issues += len(file_result.get('issues', []))

        # 生成报告
        report = self._generate_detailed_report(results)

        # 判断结果
        severity_threshold = self.get_config_value('severity_threshold', 'medium')
        max_issues = self.get_config_value('max_issues', 10)

        critical_issues = self._count_issues_by_severity(results, 'critical')
        high_issues = self._count_issues_by_severity(results, 'high')

        if critical_issues > 0 or (severity_threshold == 'high' and high_issues > 0):
            status = PluginStatus.FAILURE
            message = f"发现 {critical_issues} 个严重问题, {high_issues} 个高级问题"
        elif total_issues > max_issues:
            status = PluginStatus.WARNING
            message = f"发现 {total_issues} 个问题 (超过限制 {max_issues})"
        else:
            status = PluginStatus.SUCCESS
            message = f"质量检查通过，发现 {total_issues} 个问题"

        return PluginResult(
            status=status,
            message=message,
            details={
                "total_files": len(checkable_files),
                "total_issues": total_issues,
                "critical_issues": critical_issues,
                "high_issues": high_issues,
                "report": report,
                "results": results
            }
        )

    def _filter_checkable_files(self, files: List[str]) -> List[str]:
        """过滤可检查的文件"""
        checkable_extensions = self.get_config_value(
            'checkable_extensions',
            ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h']
        )

        return self.filter_files_by_extension(files, checkable_extensions)

    def _check_file_comprehensive(self, file_path: str) -> Dict[str, Any]:
        """全面检查文件质量"""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 根据文件类型执行不同检查
            if file_path.endswith('.py'):
                issues.extend(self._check_python_file(file_path, content))
            elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
                issues.extend(self._check_javascript_file(file_path, content))

            # 通用检查
            issues.extend(self._check_general_quality(file_path, content))

            # 计算质量分数
            score = self._calculate_quality_score(issues, len(content.split('\n')))

            return {
                "file": file_path,
                "issues": issues,
                "score": score,
                "lines": len(content.split('\n'))
            }

        except Exception as e:
            return {
                "file": file_path,
                "issues": [{
                    "type": "error",
                    "severity": "critical",
                    "line": 1,
                    "message": f"文件检查失败: {str(e)}"
                }],
                "score": 0,
                "lines": 0
            }

    def _check_python_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """检查Python文件"""
        issues = []

        # 语法检查
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append({
                "type": "syntax_error",
                "severity": "critical",
                "line": e.lineno or 1,
                "message": f"语法错误: {e.msg}"
            })
            return issues  # 语法错误时不继续检查

        lines = content.split('\n')

        # 检查导入规范
        issues.extend(self._check_python_imports(lines))

        # 检查函数和类文档
        if self.get_config_value('check_docstrings', True):
            issues.extend(self._check_python_docstrings(content, lines))

        # 检查行长度
        max_line_length = self.get_config_value('max_line_length', 88)
        issues.extend(self._check_line_length(lines, max_line_length))

        return issues

    def _check_javascript_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """检查JavaScript/TypeScript文件"""
        issues = []
        lines = content.split('\n')

        # 检查基本语法问题
        issues.extend(self._check_js_syntax_issues(lines))

        # 检查console.log语句
        issues.extend(self._check_console_statements(lines))

        return issues

    def _check_general_quality(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """通用质量检查"""
        issues = []
        lines = content.split('\n')

        # 检查空白行
        issues.extend(self._check_whitespace_issues(lines))

        # 检查TODO注释
        issues.extend(self._check_todo_comments(lines))

        # 检查敏感信息泄露
        issues.extend(self._check_sensitive_info(lines))

        return issues

    def _check_python_imports(self, lines: List[str]) -> List[Dict[str, Any]]:
        """检查Python导入规范"""
        issues = []
        import_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(('import ', 'from ')):
                import_lines.append((i + 1, stripped))

        # 检查导入顺序和分组
        if len(import_lines) > 1:
            for i, (line_num, import_stmt) in enumerate(import_lines[:-1]):
                current_group = self._get_import_group(import_stmt)
                next_group = self._get_import_group(import_lines[i + 1][1])

                if current_group > next_group:
                    issues.append({
                        "type": "import_order",
                        "severity": "medium",
                        "line": line_num,
                        "message": "导入顺序不规范，应该先标准库，再第三方库，最后本地模块"
                    })

        return issues

    def _check_python_docstrings(self, content: str, lines: List[str]) -> List[Dict[str, Any]]:
        """检查Python文档字符串"""
        issues = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        issues.append({
                            "type": "missing_docstring",
                            "severity": "medium",
                            "line": node.lineno,
                            "message": f"缺少文档字符串: {node.name}"
                        })
        except:
            pass  # 语法错误时跳过

        return issues

    def _check_line_length(self, lines: List[str], max_length: int) -> List[Dict[str, Any]]:
        """检查行长度"""
        issues = []

        for i, line in enumerate(lines):
            if len(line) > max_length:
                issues.append({
                    "type": "line_too_long",
                    "severity": "low",
                    "line": i + 1,
                    "message": f"行长度 {len(line)} 超过限制 {max_length}"
                })

        return issues

    def _check_js_syntax_issues(self, lines: List[str]) -> List[Dict[str, Any]]:
        """检查JavaScript基本语法问题"""
        issues = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 检查分号
            if (stripped and
                not stripped.startswith(('/', '*', '//')) and
                not stripped.endswith((';', '{', '}', ',')) and
                not stripped.startswith(('if', 'else', 'for', 'while', 'function', 'class'))):
                if re.search(r'\w+\s*=\s*', stripped):
                    issues.append({
                        "type": "missing_semicolon",
                        "severity": "low",
                        "line": i + 1,
                        "message": "可能缺少分号"
                    })

        return issues

    def _check_console_statements(self, lines: List[str]) -> List[Dict[str, Any]]:
        """检查console语句"""
        issues = []

        for i, line in enumerate(lines):
            if 'console.' in line and not line.strip().startswith('//'):
                issues.append({
                    "type": "debug_statement",
                    "severity": "medium",
                    "line": i + 1,
                    "message": "发现console语句，可能是调试代码"
                })

        return issues

    def _check_whitespace_issues(self, lines: List[str]) -> List[Dict[str, Any]]:
        """检查空白字符问题"""
        issues = []

        for i, line in enumerate(lines):
            # 检查行末空白
            if line.rstrip() != line:
                issues.append({
                    "type": "trailing_whitespace",
                    "severity": "low",
                    "line": i + 1,
                    "message": "行末有多余空白字符"
                })

        return issues

    def _check_todo_comments(self, lines: List[str]) -> List[Dict[str, Any]]:
        """检查TODO注释"""
        issues = []

        for i, line in enumerate(lines):
            if re.search(r'(TODO|FIXME|HACK|XXX)', line, re.IGNORECASE):
                issues.append({
                    "type": "todo_comment",
                    "severity": "low",
                    "line": i + 1,
                    "message": "发现TODO注释，需要后续处理"
                })

        return issues

    def _check_sensitive_info(self, lines: List[str]) -> List[Dict[str, Any]]:
        """检查敏感信息"""
        issues = []

        sensitive_patterns = [
            (r'password\s*=\s*["\'][^"\']*["\']', "可能的密码泄露"),
            (r'api[_-]?key\s*=\s*["\'][^"\']*["\']', "可能的API密钥泄露"),
            (r'secret\s*=\s*["\'][^"\']*["\']', "可能的密钥泄露"),
        ]

        for i, line in enumerate(lines):
            for pattern, message in sensitive_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        "type": "security_risk",
                        "severity": "high",
                        "line": i + 1,
                        "message": message
                    })

        return issues

    def _get_import_group(self, import_stmt: str) -> int:
        """获取导入语句的分组（用于排序）"""
        if import_stmt.startswith('from __future__'):
            return 0
        elif '.' not in import_stmt.split()[1]:
            return 1  # 标准库
        elif import_stmt.split()[1].startswith('.'):
            return 3  # 相对导入
        else:
            return 2  # 第三方库

    def _calculate_quality_score(self, issues: List[Dict[str, Any]], line_count: int) -> float:
        """计算质量分数"""
        if line_count == 0:
            return 0.0

        penalty = 0
        for issue in issues:
            severity = issue.get('severity', 'low')
            if severity == 'critical':
                penalty += 20
            elif severity == 'high':
                penalty += 10
            elif severity == 'medium':
                penalty += 5
            else:  # low
                penalty += 1

        # 基于行数调整惩罚
        penalty_per_line = penalty / line_count
        score = max(0, 100 - penalty_per_line * 10)

        return round(score, 1)

    def _count_issues_by_severity(self, results: List[Dict[str, Any]], severity: str) -> int:
        """按严重程度统计问题数量"""
        count = 0
        for result in results:
            for issue in result.get('issues', []):
                if issue.get('severity') == severity:
                    count += 1
        return count

    def _generate_detailed_report(self, results: List[Dict[str, Any]]) -> str:
        """生成详细报告"""
        total_files = len(results)
        total_issues = sum(len(r.get('issues', [])) for r in results)
        avg_score = sum(r.get('score', 0) for r in results) / max(total_files, 1)

        # 统计各类问题
        issue_types = {}
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}

        for result in results:
            for issue in result.get('issues', []):
                issue_type = issue.get('type', 'unknown')
                severity = issue.get('severity', 'low')

                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
                severity_counts[severity] += 1

        # 生成报告
        report = f"""
📊 代码质量检查报告
==================
检查文件: {total_files}
发现问题: {total_issues}
平均分数: {avg_score:.1f}/100.0

🔍 问题严重程度分布:
严重: {severity_counts['critical']} | 高级: {severity_counts['high']} | 中级: {severity_counts['medium']} | 轻微: {severity_counts['low']}

📈 问题类型分布:
"""

        for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
            report += f"  {issue_type}: {count}\n"

        # 添加具体文件问题
        if total_issues > 0:
            report += "\n📋 具体问题:\n"
            for result in results:
                if result.get('issues'):
                    report += f"\n📄 {result['file']} (分数: {result['score']}/100):\n"
                    for issue in result['issues'][:3]:  # 只显示前3个问题
                        severity_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵'}.get(issue['severity'], '⚪')
                        report += f"  {severity_icon} 第{issue['line']}行: {issue['message']}\n"

                    if len(result['issues']) > 3:
                        report += f"  ... 还有 {len(result['issues']) - 3} 个问题\n"

        return report.strip()