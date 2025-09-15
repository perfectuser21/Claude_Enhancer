#!/usr/bin/env python3
"""
Perfect21 Git Hooks - Message Validator Plugin
Git提交消息格式验证插件
"""

import re
from typing import Dict, Any, List, Optional, Tuple

try:
    from ..base_plugin import (
        CommitWorkflowPlugin, PluginResult, PluginStatus, PluginMetadata, PluginPriority
    )
except ImportError:
    from features.git_workflow.plugins.base_plugin import (
        CommitWorkflowPlugin, PluginResult, PluginStatus, PluginMetadata, PluginPriority
    )


class MessageValidatorPlugin(CommitWorkflowPlugin):
    """Git提交消息验证插件"""

    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="message_validator",
            version="2.1.0",
            description="Git提交消息格式验证，支持Conventional Commits规范",
            author="Perfect21 Team",
            category="commit_workflow",
            priority=PluginPriority.HIGH,
            dependencies=["python:re"],
            supports_parallel=False,  # 消息验证不需要并行
            timeout=30
        )

    def execute(self, context: Dict[str, Any]) -> PluginResult:
        """执行提交消息验证"""
        commit_message = self.get_commit_message()

        if not commit_message:
            return PluginResult(
                status=PluginStatus.ERROR,
                message="无法获取提交消息"
            )

        # 执行各项验证
        validation_results = []

        # 基本格式检查
        validation_results.append(self._check_basic_format(commit_message))

        # Conventional Commits检查
        if self.get_config_value('enforce_conventional', True):
            validation_results.append(self._check_conventional_format(commit_message))

        # 长度检查
        validation_results.append(self._check_length_limits(commit_message))

        # 内容质量检查
        validation_results.append(self._check_content_quality(commit_message))

        # 禁用词检查
        validation_results.append(self._check_forbidden_patterns(commit_message))

        # Issue链接检查
        if self.get_config_value('require_issue_link', False):
            validation_results.append(self._check_issue_links(commit_message))

        # 分析结果
        passed_checks = [r for r in validation_results if r['passed']]
        failed_checks = [r for r in validation_results if not r['passed']]

        # 生成报告
        report = self._generate_validation_report(commit_message, validation_results)

        # 判断总体结果
        if failed_checks:
            # 检查是否有严重错误
            critical_failures = [r for r in failed_checks if r['severity'] == 'critical']

            if critical_failures:
                status = PluginStatus.FAILURE
                message = f"提交消息验证失败: {len(critical_failures)} 个严重错误"
            else:
                # 检查是否启用严格模式
                if self.get_config_value('strict_mode', False):
                    status = PluginStatus.FAILURE
                    message = f"严格模式下提交消息验证失败: {len(failed_checks)} 个问题"
                else:
                    status = PluginStatus.WARNING
                    message = f"提交消息有 {len(failed_checks)} 个建议改进的地方"
        else:
            status = PluginStatus.SUCCESS
            message = f"提交消息验证通过 ({len(passed_checks)} 项检查)"

        return PluginResult(
            status=status,
            message=message,
            details={
                "commit_message": commit_message,
                "total_checks": len(validation_results),
                "passed_checks": len(passed_checks),
                "failed_checks": len(failed_checks),
                "validation_results": validation_results,
                "report": report
            }
        )

    def _check_basic_format(self, message: str) -> Dict[str, Any]:
        """检查基本格式"""
        issues = []

        # 检查是否为空
        if not message.strip():
            issues.append("提交消息不能为空")

        # 检查首行是否以大写字母开头
        lines = message.split('\n')
        first_line = lines[0].strip()

        if first_line and not first_line[0].isupper():
            issues.append("提交消息首行应以大写字母开头")

        # 检查首行是否以句号结尾
        if first_line.endswith('.'):
            issues.append("提交消息首行不应以句号结尾")

        # 检查空行分隔
        if len(lines) > 2 and lines[1].strip():
            issues.append("提交消息第二行应为空行")

        return {
            "name": "基本格式检查",
            "passed": len(issues) == 0,
            "severity": "medium",
            "issues": issues
        }

    def _check_conventional_format(self, message: str) -> Dict[str, Any]:
        """检查Conventional Commits格式"""
        issues = []

        # Conventional Commits 正则表达式
        # 格式: type(scope): description
        conventional_pattern = r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .+'

        first_line = message.split('\n')[0].strip()

        if not re.match(conventional_pattern, first_line, re.IGNORECASE):
            issues.append("不符合Conventional Commits格式")

            # 提供详细建议
            allowed_types = self.get_config_value('allowed_types', [
                'feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore'
            ])

            issues.append(f"允许的类型: {', '.join(allowed_types)}")
            issues.append("正确格式: type(scope): description")
            issues.append("示例: feat(auth): add user login validation")

        return {
            "name": "Conventional Commits格式检查",
            "passed": len(issues) == 0,
            "severity": "high",
            "issues": issues
        }

    def _check_length_limits(self, message: str) -> Dict[str, Any]:
        """检查长度限制"""
        issues = []
        lines = message.split('\n')

        # 检查标题长度
        first_line = lines[0].strip()
        max_subject_length = self.get_config_value('max_subject_length', 72)

        if len(first_line) > max_subject_length:
            issues.append(f"标题过长 ({len(first_line)} > {max_subject_length} 字符)")

        # 检查最短长度
        min_subject_length = self.get_config_value('min_subject_length', 10)
        if len(first_line) < min_subject_length:
            issues.append(f"标题过短 ({len(first_line)} < {min_subject_length} 字符)")

        # 检查正文行长度
        max_body_line_length = self.get_config_value('max_body_line_length', 80)
        for i, line in enumerate(lines[2:], 3):  # 从第三行开始检查正文
            if len(line) > max_body_line_length:
                issues.append(f"第{i}行过长 ({len(line)} > {max_body_line_length} 字符)")

        return {
            "name": "长度限制检查",
            "passed": len(issues) == 0,
            "severity": "medium",
            "issues": issues
        }

    def _check_content_quality(self, message: str) -> Dict[str, Any]:
        """检查内容质量"""
        issues = []

        first_line = message.split('\n')[0].strip().lower()

        # 检查无意义的消息
        meaningless_patterns = [
            r'^(wip|temp|tmp|test|fix|update|change)$',
            r'^(fix bug|bug fix|fixes?)$',
            r'^(update|updates?)$',
            r'^(改|修改|更新|修复)$',
        ]

        for pattern in meaningless_patterns:
            if re.match(pattern, first_line, re.IGNORECASE):
                issues.append("提交消息过于简单，请提供更具描述性的说明")
                break

        # 检查拼写错误（简单版本）
        common_typos = {
            'teh': 'the',
            'adn': 'and',
            'nad': 'and',
            'taht': 'that',
            'fo': 'of',
            'fro': 'for'
        }

        words = re.findall(r'\b\w+\b', first_line.lower())
        for word in words:
            if word in common_typos:
                issues.append(f"可能的拼写错误: '{word}' -> '{common_typos[word]}'")

        # 检查是否包含有意义的动词
        action_verbs = ['add', 'remove', 'fix', 'update', 'improve', 'refactor', 'implement',
                       'create', 'delete', 'modify', 'enhance', 'optimize', 'cleanup']

        has_action = any(verb in first_line.lower() for verb in action_verbs)
        if not has_action and not re.match(r'^(feat|fix|docs)', first_line, re.IGNORECASE):
            issues.append("建议使用明确的动词描述所做的更改")

        return {
            "name": "内容质量检查",
            "passed": len(issues) == 0,
            "severity": "low",
            "issues": issues
        }

    def _check_forbidden_patterns(self, message: str) -> Dict[str, Any]:
        """检查禁用模式"""
        issues = []

        # 禁用词汇
        forbidden_words = self.get_config_value('forbidden_words', [
            'shit', 'fuck', 'damn', 'crap', 'stupid', 'idiot'
        ])

        message_lower = message.lower()
        for word in forbidden_words:
            if word.lower() in message_lower:
                issues.append(f"包含不当词汇: '{word}'")

        # 检查临时提交消息
        temp_patterns = [
            r'temporary',
            r'quick fix',
            r'hotfix',
            r'urgent',
            r'asap',
            r'临时',
            r'紧急',
        ]

        for pattern in temp_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                issues.append(f"检测到临时提交模式: '{pattern}' - 建议使用更正式的描述")

        return {
            "name": "禁用模式检查",
            "passed": len(issues) == 0,
            "severity": "medium",
            "issues": issues
        }

    def _check_issue_links(self, message: str) -> Dict[str, Any]:
        """检查Issue链接"""
        issues = []

        # 查找Issue引用模式
        issue_patterns = [
            r'#\d+',  # GitHub风格 #123
            r'issues?/\d+',  # issues/123
            r'close[sd]?\s+#\d+',  # closes #123
            r'fix(es)?\s+#\d+',  # fixes #123
            r'resolve[sd]?\s+#\d+',  # resolves #123
        ]

        has_issue_link = False
        for pattern in issue_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                has_issue_link = True
                break

        if not has_issue_link:
            issues.append("缺少Issue引用 (例如: #123, fixes #123)")

        return {
            "name": "Issue链接检查",
            "passed": len(issues) == 0,
            "severity": "medium",
            "issues": issues
        }

    def _generate_validation_report(self, message: str, results: List[Dict[str, Any]]) -> str:
        """生成验证报告"""
        lines = message.split('\n')
        first_line = lines[0].strip()

        passed_count = sum(1 for r in results if r['passed'])
        total_count = len(results)

        report = f"""
📝 提交消息验证报告
==================
消息: "{first_line}"
检查项目: {passed_count}/{total_count} 通过

"""

        # 按严重程度分组显示结果
        severity_order = ['critical', 'high', 'medium', 'low']

        for severity in severity_order:
            severity_results = [r for r in results if r['severity'] == severity]
            if not severity_results:
                continue

            severity_icon = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🔵'
            }[severity]

            severity_name = {
                'critical': '严重',
                'high': '高级',
                'medium': '中级',
                'low': '轻微'
            }[severity]

            report += f"{severity_icon} {severity_name}问题:\n"

            for result in severity_results:
                status_icon = "✅" if result['passed'] else "❌"
                report += f"  {status_icon} {result['name']}\n"

                if not result['passed'] and result['issues']:
                    for issue in result['issues']:
                        report += f"    - {issue}\n"

            report += "\n"

        # 提供改进建议
        failed_results = [r for r in results if not r['passed']]
        if failed_results:
            report += "💡 改进建议:\n"

            # 根据失败的检查提供具体建议
            suggestions = self._generate_suggestions(message, failed_results)
            for suggestion in suggestions:
                report += f"  • {suggestion}\n"

        return report.strip()

    def _generate_suggestions(self, message: str, failed_results: List[Dict[str, Any]]) -> List[str]:
        """生成改进建议"""
        suggestions = []

        failed_names = {r['name'] for r in failed_results}

        if 'Conventional Commits格式检查' in failed_names:
            suggestions.append("使用标准格式: type(scope): description")
            suggestions.append("例如: feat(user): add password validation")

        if '长度限制检查' in failed_names:
            suggestions.append("保持标题在72字符以内")
            suggestions.append("如需详细说明，在空行后添加正文")

        if '内容质量检查' in failed_names:
            suggestions.append("使用清晰的动词描述更改 (add, fix, update, remove)")
            suggestions.append("说明更改的原因和影响")

        if 'Issue链接检查' in failed_names:
            suggestions.append("添加相关Issue引用: #123 或 fixes #123")

        if '基本格式检查' in failed_names:
            suggestions.append("确保首行以大写字母开头")
            suggestions.append("第二行保留空行分隔标题和正文")

        # 提供示例
        if suggestions:
            suggestions.append("")
            suggestions.append("完整示例:")
            suggestions.append("feat(auth): add two-factor authentication")
            suggestions.append("")
            suggestions.append("Implement TOTP-based 2FA to enhance security.")
            suggestions.append("Users can now enable 2FA in account settings.")
            suggestions.append("")
            suggestions.append("Closes #456")

        return suggestions