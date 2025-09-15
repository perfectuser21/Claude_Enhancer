#!/usr/bin/env python3
"""
Perfect21 Git Hooks - Security Scan Plugin
安全扫描插件，检测潜在的安全风险
"""

import os
import re
import json
import hashlib
import subprocess
from typing import Dict, Any, List, Optional, Tuple

try:
    from ..base_plugin import (
        SecurityPlugin, PluginResult, PluginStatus, PluginMetadata, PluginPriority
    )
except ImportError:
    from features.git_workflow.plugins.base_plugin import (
        SecurityPlugin, PluginResult, PluginStatus, PluginMetadata, PluginPriority
    )


class SecurityScanPlugin(SecurityPlugin):
    """安全扫描插件"""

    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="security_scan",
            version="2.1.0",
            description="安全扫描插件，检测敏感信息泄露、依赖漏洞等",
            author="Perfect21 Team",
            category="security",
            priority=PluginPriority.CRITICAL,
            dependencies=["python:re", "python:hashlib"],
            supports_parallel=True,
            timeout=180
        )

    def execute(self, context: Dict[str, Any]) -> PluginResult:
        """执行安全扫描"""
        staged_files = self.get_staged_files()

        if not staged_files:
            return PluginResult(
                status=PluginStatus.SKIPPED,
                message="没有已暂存的文件需要扫描"
            )

        # 执行各项安全检查
        scan_results = {
            "secrets": self._scan_secrets(staged_files),
            "dependencies": self._scan_dependencies(staged_files),
            "permissions": self._scan_permissions(staged_files),
            "hardcoded": self._scan_hardcoded_values(staged_files),
            "injection": self._scan_injection_risks(staged_files)
        }

        # 统计问题
        total_issues = sum(len(results) for results in scan_results.values())
        critical_issues = self._count_critical_issues(scan_results)

        # 生成报告
        report = self._generate_security_report(scan_results, staged_files)

        # 判断结果
        if critical_issues > 0:
            status = PluginStatus.FAILURE
            message = f"发现 {critical_issues} 个严重安全问题"
        elif total_issues > 0:
            security_level = self.get_config_value('security_level', 'strict')
            if security_level == 'strict' and total_issues > 0:
                status = PluginStatus.FAILURE
                message = f"严格模式下发现 {total_issues} 个安全问题"
            else:
                status = PluginStatus.WARNING
                message = f"发现 {total_issues} 个潜在安全问题"
        else:
            status = PluginStatus.SUCCESS
            message = "安全扫描通过，未发现安全问题"

        return PluginResult(
            status=status,
            message=message,
            details={
                "total_files": len(staged_files),
                "total_issues": total_issues,
                "critical_issues": critical_issues,
                "scan_results": scan_results,
                "report": report
            }
        )

    def _scan_secrets(self, files: List[str]) -> List[Dict[str, Any]]:
        """扫描敏感信息泄露"""
        secrets = []

        # 扩展的敏感信息模式
        secret_patterns = [
            (r'["\']?password["\']?\s*[:=]\s*["\']([^"\']+)["\']', 'password', 'critical'),
            (r'["\']?api[_-]?key["\']?\s*[:=]\s*["\']([^"\']+)["\']', 'api_key', 'critical'),
            (r'["\']?secret[_-]?key["\']?\s*[:=]\s*["\']([^"\']+)["\']', 'secret_key', 'critical'),
            (r'["\']?token["\']?\s*[:=]\s*["\']([^"\']+)["\']', 'token', 'high'),
            (r'["\']?access[_-]?token["\']?\s*[:=]\s*["\']([^"\']+)["\']', 'access_token', 'critical'),
            (r'["\']?auth[_-]?token["\']?\s*["\']([^"\']+)["\']', 'auth_token', 'critical'),
            (r'(?:mysql|postgres|mongodb)://[^:]+:[^@]+@[^/]+', 'database_url', 'critical'),
            (r'["\']?database[_-]?url["\']?\s*[:=]\s*["\']([^"\']+)["\']', 'database_url', 'critical'),
            (r'-----BEGIN[A-Z ]*PRIVATE KEY-----', 'private_key', 'critical'),
            (r'[A-Za-z0-9+/]{40,}={0,2}', 'potential_base64', 'medium'),  # 可能的base64编码
            (r'[0-9a-fA-F]{32,64}', 'potential_hash', 'low'),  # 可能的哈希值
            (r'sk-[A-Za-z0-9]{32,}', 'openai_key', 'critical'),  # OpenAI API密钥
            (r'ghp_[A-Za-z0-9]{36}', 'github_token', 'critical'),  # GitHub个人访问令牌
            (r'gho_[A-Za-z0-9]{36}', 'github_oauth', 'critical'),  # GitHub OAuth令牌
            (r'ghu_[A-Za-z0-9]{36}', 'github_user', 'critical'),  # GitHub用户令牌
            (r'ghs_[A-Za-z0-9]{36}', 'github_server', 'critical'),  # GitHub服务器令牌
            (r'AKIA[0-9A-Z]{16}', 'aws_access_key', 'critical'),  # AWS访问密钥
        ]

        for file_path in files:
            if self._should_scan_file(file_path):
                file_secrets = self.scan_for_secrets(file_path)

                # 使用更精确的模式检查
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    for pattern, secret_type, severity in secret_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                        for match in matches:
                            # 跳过注释中的内容（简单检查）
                            line_start = content.rfind('\n', 0, match.start()) + 1
                            line = content[line_start:content.find('\n', match.start())]
                            if line.strip().startswith(('#', '//', '/*', '*')):
                                continue

                            secrets.append({
                                "file": file_path,
                                "type": secret_type,
                                "severity": severity,
                                "line": content[:match.start()].count('\n') + 1,
                                "pattern": pattern[:50] + "..." if len(pattern) > 50 else pattern,
                                "match": match.group()[:20] + "..." if len(match.group()) > 20 else match.group()
                            })

                except Exception as e:
                    self.logger.warning(f"无法扫描文件 {file_path}: {e}")

        return secrets

    def _scan_dependencies(self, files: List[str]) -> List[Dict[str, Any]]:
        """扫描依赖安全漏洞"""
        vulnerabilities = []

        # 检查各种依赖文件
        dependency_files = [
            ('requirements.txt', 'python'),
            ('Pipfile', 'python'),
            ('package.json', 'nodejs'),
            ('pom.xml', 'java'),
            ('Gemfile', 'ruby'),
            ('go.mod', 'golang')
        ]

        for file_path in files:
            file_name = os.path.basename(file_path)

            for dep_file, ecosystem in dependency_files:
                if file_name == dep_file:
                    file_vulns = self._check_dependency_file(file_path, ecosystem)
                    vulnerabilities.extend(file_vulns)

        return vulnerabilities

    def _scan_permissions(self, files: List[str]) -> List[Dict[str, Any]]:
        """扫描文件权限问题"""
        permission_issues = []

        for file_path in files:
            if os.path.exists(file_path):
                try:
                    stat_info = os.stat(file_path)
                    permissions = oct(stat_info.st_mode)[-3:]

                    # 检查过于宽松的权限
                    if permissions.endswith('7') or permissions.endswith('6'):
                        permission_issues.append({
                            "file": file_path,
                            "type": "overly_permissive",
                            "severity": "medium",
                            "permissions": permissions,
                            "message": f"文件权限过于宽松: {permissions}"
                        })

                    # 检查可执行脚本
                    if file_path.endswith(('.sh', '.py', '.pl', '.rb')):
                        if not permissions.startswith('7'):
                            permission_issues.append({
                                "file": file_path,
                                "type": "script_permissions",
                                "severity": "low",
                                "permissions": permissions,
                                "message": f"脚本文件可能需要执行权限"
                            })

                except Exception as e:
                    self.logger.warning(f"无法检查文件权限 {file_path}: {e}")

        return permission_issues

    def _scan_hardcoded_values(self, files: List[str]) -> List[Dict[str, Any]]:
        """扫描硬编码值"""
        hardcoded_issues = []

        hardcoded_patterns = [
            (r'localhost:\d+', 'localhost_url', 'low'),
            (r'127\.0\.0\.1:\d+', 'localhost_ip', 'low'),
            (r'0\.0\.0\.0:\d+', 'bind_all_ip', 'medium'),
            (r'/tmp/[^"\s]+', 'tmp_path', 'low'),
            (r'["\']DEBUG["\']?\s*[:=]\s*True', 'debug_mode', 'high'),
            (r'["\']PRODUCTION["\']?\s*[:=]\s*False', 'production_flag', 'medium'),
        ]

        for file_path in files:
            if self._should_scan_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    for pattern, issue_type, severity in hardcoded_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            hardcoded_issues.append({
                                "file": file_path,
                                "type": issue_type,
                                "severity": severity,
                                "line": content[:match.start()].count('\n') + 1,
                                "match": match.group(),
                                "message": f"发现硬编码值: {match.group()}"
                            })

                except Exception as e:
                    self.logger.warning(f"无法扫描硬编码值 {file_path}: {e}")

        return hardcoded_issues

    def _scan_injection_risks(self, files: List[str]) -> List[Dict[str, Any]]:
        """扫描注入攻击风险"""
        injection_risks = []

        injection_patterns = [
            (r'eval\s*\([^)]*\)', 'code_injection', 'critical'),
            (r'exec\s*\([^)]*\)', 'code_injection', 'critical'),
            (r'system\s*\([^)]*\)', 'command_injection', 'high'),
            (r'os\.system\s*\([^)]*\)', 'command_injection', 'high'),
            (r'subprocess\.call\s*\([^)]*shell\s*=\s*True', 'shell_injection', 'high'),
            (r'SELECT\s+.*\s+FROM\s+.*\s+WHERE\s+.*\+', 'sql_injection', 'high'),
            (r'document\.write\s*\([^)]*\)', 'xss_risk', 'medium'),
            (r'innerHTML\s*=\s*[^;]*\+', 'xss_risk', 'medium'),
        ]

        for file_path in files:
            if self._should_scan_file(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    for pattern, risk_type, severity in injection_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            injection_risks.append({
                                "file": file_path,
                                "type": risk_type,
                                "severity": severity,
                                "line": content[:match.start()].count('\n') + 1,
                                "match": match.group()[:50] + "..." if len(match.group()) > 50 else match.group(),
                                "message": f"潜在{risk_type}风险"
                            })

                except Exception as e:
                    self.logger.warning(f"无法扫描注入风险 {file_path}: {e}")

        return injection_risks

    def _should_scan_file(self, file_path: str) -> bool:
        """判断是否应该扫描文件"""
        # 跳过二进制文件和某些类型的文件
        skip_extensions = {'.pyc', '.pyo', '.jpg', '.png', '.gif', '.pdf', '.zip', '.tar', '.gz'}
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext in skip_extensions:
            return False

        # 跳过大文件
        try:
            if os.path.getsize(file_path) > 1024 * 1024:  # 1MB
                return False
        except:
            return False

        return True

    def _check_dependency_file(self, file_path: str, ecosystem: str) -> List[Dict[str, Any]]:
        """检查依赖文件的安全漏洞"""
        vulnerabilities = []

        # 这里可以集成真实的漏洞数据库
        # 目前实现简单的已知漏洞检查
        known_vulnerable = {
            'python': [
                ('django', '< 3.2.0', 'SQL注入漏洞'),
                ('requests', '< 2.25.0', 'HTTP请求漏洞'),
                ('pyyaml', '< 5.4.0', '任意代码执行'),
            ],
            'nodejs': [
                ('lodash', '< 4.17.11', '原型污染'),
                ('axios', '< 0.21.1', 'SSRF漏洞'),
                ('express', '< 4.17.0', '路径遍历'),
            ]
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if ecosystem in known_vulnerable:
                for package, version_constraint, description in known_vulnerable[ecosystem]:
                    if package in content:
                        vulnerabilities.append({
                            "file": file_path,
                            "type": "vulnerable_dependency",
                            "severity": "high",
                            "package": package,
                            "constraint": version_constraint,
                            "description": description,
                            "message": f"依赖包 {package} 存在已知漏洞"
                        })

        except Exception as e:
            self.logger.warning(f"无法检查依赖文件 {file_path}: {e}")

        return vulnerabilities

    def _count_critical_issues(self, scan_results: Dict[str, List[Dict[str, Any]]]) -> int:
        """统计严重问题数量"""
        count = 0
        for results in scan_results.values():
            for issue in results:
                if issue.get('severity') == 'critical':
                    count += 1
        return count

    def _generate_security_report(self, scan_results: Dict[str, List[Dict[str, Any]]], files: List[str]) -> str:
        """生成安全扫描报告"""
        total_issues = sum(len(results) for results in scan_results.values())

        # 按严重程度统计
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for results in scan_results.values():
            for issue in results:
                severity = issue.get('severity', 'low')
                severity_counts[severity] += 1

        report = f"""
🔒 安全扫描报告
==============
扫描文件: {len(files)}
发现问题: {total_issues}

🚨 问题严重程度分布:
严重: {severity_counts['critical']} | 高级: {severity_counts['high']} | 中级: {severity_counts['medium']} | 轻微: {severity_counts['low']}

📊 扫描类别结果:
"""

        # 各类扫描结果
        scan_categories = {
            'secrets': '🔑 敏感信息泄露',
            'dependencies': '📦 依赖漏洞',
            'permissions': '🔐 权限问题',
            'hardcoded': '💾 硬编码值',
            'injection': '💉 注入风险'
        }

        for category, results in scan_results.items():
            category_name = scan_categories.get(category, category)
            report += f"  {category_name}: {len(results)} 个问题\n"

        # 详细问题列表
        if total_issues > 0:
            report += "\n📋 详细问题:\n"

            for category, results in scan_results.items():
                if results:
                    category_name = scan_categories.get(category, category)
                    report += f"\n{category_name}:\n"

                    for issue in results[:5]:  # 每类最多显示5个问题
                        severity_icon = {
                            'critical': '🔴',
                            'high': '🟠',
                            'medium': '🟡',
                            'low': '🔵'
                        }.get(issue.get('severity', 'low'), '⚪')

                        file_name = os.path.basename(issue.get('file', ''))
                        line = issue.get('line', 0)
                        message = issue.get('message', issue.get('type', ''))

                        report += f"  {severity_icon} {file_name}:{line} - {message}\n"

                    if len(results) > 5:
                        report += f"  ... 还有 {len(results) - 5} 个问题\n"

        return report.strip()