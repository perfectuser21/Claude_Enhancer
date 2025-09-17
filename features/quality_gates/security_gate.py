#!/usr/bin/env python3
"""
Perfect21 安全质量门
===================

执行安全扫描，检测安全漏洞和风险
"""

import asyncio
import json
import subprocess
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .models import GateResult, GateStatus, GateSeverity


class SecurityGate:
    """安全质量门"""

    def __init__(self, project_root: str, config):
        self.project_root = Path(project_root)
        self.config = config

        # 安全风险模式
        self.security_patterns = {
            "hardcoded_secrets": [
                r'(?i)(password|passwd|pwd|secret|key|token|api_key)\s*[:=]\s*["\']([^"\']{8,})["\']',
                r'(?i)(secret|key|token|password).*["\']([a-zA-Z0-9+/]{20,})["\']',
                r'(?i)BEGIN\s+(RSA\s+)?PRIVATE\s+KEY',
                r'(?i)AKIA[0-9A-Z]{16}',  # AWS Access Key
                r'(?i)ghp_[0-9a-zA-Z]{36}',  # GitHub Personal Access Token
            ],
            "sql_injection": [
                r'(?i)SELECT\s+.*\s+FROM\s+.*\s+WHERE\s+.*\+',
                r'(?i)INSERT\s+INTO\s+.*\s+VALUES\s*\([^)]*\+',
                r'(?i)UPDATE\s+.*\s+SET\s+.*\+',
                r'(?i)DELETE\s+FROM\s+.*\s+WHERE\s+.*\+',
                r'cursor\.execute\s*\([^)]*\+',
                r'query\s*\+\s*',
            ],
            "command_injection": [
                r'os\.system\s*\([^)]*\+',
                r'subprocess\.(call|run|Popen)\s*\([^)]*\+',
                r'eval\s*\(',
                r'exec\s*\(',
                r'shell=True.*\+',
            ],
            "path_traversal": [
                r'open\s*\([^)]*\.\./.*\)',
                r'path.*\.\./.*',
                r'filename.*\.\./.*',
                r'file.*\.\./.*',
            ],
            "insecure_random": [
                r'random\.random\(',
                r'random\.randint\(',
                r'random\.choice\(',
                r'random\.uniform\(',
            ],
            "debug_code": [
                r'(?i)debug\s*=\s*True',
                r'(?i)print\s*\([^)]*password',
                r'(?i)print\s*\([^)]*secret',
                r'(?i)print\s*\([^)]*token',
                r'pdb\.set_trace\(',
                r'import\s+pdb',
            ]
        }

    async def check(self, context: str = "commit") -> GateResult:
        """执行安全检查"""
        start_time = datetime.now()
        violations = []
        details = {}
        suggestions = []

        try:
            # 1. Bandit安全扫描
            bandit_result = await self._run_bandit_scan()
            details["bandit"] = bandit_result
            if bandit_result["issues"]:
                for issue in bandit_result["issues"]:
                    if issue["severity"] in ["HIGH", "MEDIUM"]:
                        violations.append({
                            "type": "bandit_security_issue",
                            "message": f"{issue['test_name']}: {issue['issue_text']}",
                            "file": issue["filename"],
                            "line": issue.get("line_number", 0),
                            "severity": issue["severity"].lower(),
                            "confidence": issue["confidence"]
                        })

            # 2. 模式匹配安全检查
            pattern_result = await self._check_security_patterns()
            details["patterns"] = pattern_result
            for category, matches in pattern_result["matches"].items():
                for match in matches:
                    violations.append({
                        "type": f"security_pattern_{category}",
                        "message": f"发现安全风险模式 ({category}): {match['match']}",
                        "file": match["file"],
                        "line": match["line"],
                        "severity": self._get_pattern_severity(category)
                    })

            # 3. 依赖安全检查
            dependency_result = await self._check_dependency_security()
            details["dependencies"] = dependency_result
            if dependency_result["vulnerabilities"]:
                for vuln in dependency_result["vulnerabilities"]:
                    violations.append({
                        "type": "vulnerable_dependency",
                        "message": f"依赖安全漏洞: {vuln['package']} {vuln['version']}",
                        "severity": vuln["severity"],
                        "cve": vuln.get("cve", "")
                    })

            # 4. 敏感文件检查
            sensitive_files_result = await self._check_sensitive_files()
            details["sensitive_files"] = sensitive_files_result
            if sensitive_files_result["files"]:
                violations.append({
                    "type": "sensitive_files",
                    "message": f"发现 {len(sensitive_files_result['files'])} 个敏感文件",
                    "severity": "medium"
                })
                suggestions.append("将敏感文件添加到.gitignore")

            # 5. 权限检查
            permissions_result = await self._check_file_permissions()
            details["permissions"] = permissions_result
            if permissions_result["insecure_permissions"]:
                violations.append({
                    "type": "insecure_permissions",
                    "message": f"发现 {len(permissions_result['insecure_permissions'])} 个权限问题",
                    "severity": "medium"
                })
                suggestions.append("修复文件权限设置")

            # 计算安全分数
            score = self._calculate_security_score(details, violations)

            # 确定状态
            high_critical_issues = len([v for v in violations if v.get("severity") in ["high", "critical"]])
            medium_issues = len([v for v in violations if v.get("severity") == "medium"])

            if high_critical_issues > self.config.max_security_issues:
                status = GateStatus.FAILED
                severity = GateSeverity.CRITICAL
                message = f"发现 {high_critical_issues} 个高危安全问题"
            elif medium_issues > 5:  # 允许少量中等风险
                status = GateStatus.WARNING
                severity = GateSeverity.MEDIUM
                message = f"发现 {medium_issues} 个中等安全风险"
            elif violations:
                status = GateStatus.WARNING
                severity = GateSeverity.LOW
                message = f"发现 {len(violations)} 个安全风险"
            else:
                status = GateStatus.PASSED
                severity = GateSeverity.INFO
                message = "安全检查通过"

            # 添加安全建议
            if violations:
                suggestions.extend([
                    "定期更新依赖包",
                    "使用环境变量存储敏感信息",
                    "启用安全linting工具",
                    "进行代码安全审查"
                ])

            execution_time = (datetime.now() - start_time).total_seconds()

            return GateResult(
                gate_name="security",
                status=status,
                severity=severity,
                score=score,
                message=message,
                details=details,
                violations=violations,
                suggestions=list(set(suggestions)),
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                metadata={"context": context, "files_scanned": details.get("patterns", {}).get("files_scanned", 0)}
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return GateResult(
                gate_name="security",
                status=GateStatus.FAILED,
                severity=GateSeverity.HIGH,
                score=0.0,
                message=f"安全检查失败: {str(e)}",
                details={"error": str(e)},
                violations=[{"type": "check_error", "message": str(e), "severity": "high"}],
                suggestions=["检查安全扫描工具配置"],
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                metadata={"context": context}
            )

    async def _run_bandit_scan(self) -> Dict[str, Any]:
        """运行Bandit安全扫描"""
        try:
            result = subprocess.run([
                'python3', '-m', 'bandit',
                '-r', str(self.project_root),
                '-f', 'json',
                '--exclude', 'venv,__pycache__,.git,core/claude-code-unified-agents',
                '--skip', 'B101'  # 跳过assert语句检查
            ], capture_output=True, text=True, timeout=120)

            if result.returncode == 0 or result.stdout:
                try:
                    data = json.loads(result.stdout)
                    return {
                        "issues": data.get("results", []),
                        "summary": data.get("metrics", {}),
                        "scan_successful": True
                    }
                except json.JSONDecodeError:
                    pass

            return {
                "issues": [],
                "summary": {},
                "scan_successful": False,
                "error": result.stderr if result.stderr else "Bandit扫描失败"
            }

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {
                "issues": [],
                "summary": {},
                "scan_successful": False,
                "error": "Bandit工具未安装或执行超时"
            }

    async def _check_security_patterns(self) -> Dict[str, Any]:
        """检查安全风险模式"""
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if not any(exclude in str(f) for exclude in
                       ['venv', '__pycache__', '.git', 'core/claude-code-unified-agents'])]

        matches = {category: [] for category in self.security_patterns.keys()}

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                file_rel_path = str(py_file.relative_to(self.project_root))

                for category, patterns in self.security_patterns.items():
                    for pattern in patterns:
                        for line_no, line in enumerate(lines, 1):
                            for match in re.finditer(pattern, line):
                                matches[category].append({
                                    "file": file_rel_path,
                                    "line": line_no,
                                    "match": match.group(0),
                                    "context": line.strip()
                                })

            except Exception:
                continue

        total_matches = sum(len(category_matches) for category_matches in matches.values())

        return {
            "matches": matches,
            "total_matches": total_matches,
            "files_scanned": len(python_files)
        }

    async def _check_dependency_security(self) -> Dict[str, Any]:
        """检查依赖安全性"""
        try:
            # 使用safety检查依赖
            result = subprocess.run([
                'python3', '-m', 'safety', 'check', '--json'
            ], capture_output=True, text=True, timeout=60, cwd=str(self.project_root))

            if result.returncode == 0 and result.stdout:
                try:
                    vulnerabilities = json.loads(result.stdout)
                    return {
                        "vulnerabilities": vulnerabilities,
                        "scan_successful": True
                    }
                except json.JSONDecodeError:
                    pass

            # 如果safety不可用，检查requirements.txt中的已知漏洞
            return await self._simple_dependency_check()

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return await self._simple_dependency_check()

    async def _simple_dependency_check(self) -> Dict[str, Any]:
        """简单的依赖检查"""
        vulnerabilities = []
        requirements_file = self.project_root / "requirements.txt"

        if requirements_file.exists():
            try:
                with open(requirements_file, 'r') as f:
                    requirements = f.readlines()

                # 已知有漏洞的包版本（示例）
                known_vulnerable = {
                    "django": ["<3.2.13", "<4.0.4"],
                    "flask": ["<2.0.3"],
                    "requests": ["<2.25.1"],
                    "pillow": ["<8.3.2"],
                    "pyyaml": ["<5.4"]
                }

                for req in requirements:
                    req = req.strip()
                    if '==' in req:
                        package, version = req.split('==')
                        package = package.strip()
                        version = version.strip()

                        if package.lower() in known_vulnerable:
                            vulnerable_versions = known_vulnerable[package.lower()]
                            for vuln_pattern in vulnerable_versions:
                                if version < vuln_pattern.replace('<', ''):
                                    vulnerabilities.append({
                                        "package": package,
                                        "version": version,
                                        "severity": "medium",
                                        "cve": f"known_vulnerable_{package}"
                                    })

            except Exception:
                pass

        return {
            "vulnerabilities": vulnerabilities,
            "scan_successful": True
        }

    async def _check_sensitive_files(self) -> Dict[str, Any]:
        """检查敏感文件"""
        sensitive_patterns = [
            "*.key", "*.pem", "*.p12", "*.pfx",
            "*.env", ".env*",
            "*.secret", "*_secret*",
            "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
            "*.credentials", "*password*", "*passwd*",
            "*.crt", "*.cert",
            "config.json", "secrets.json"
        ]

        sensitive_files = []
        for pattern in sensitive_patterns:
            matches = list(self.project_root.rglob(pattern))
            for match in matches:
                # 排除一些安全目录
                if not any(exclude in str(match) for exclude in
                          ['.git', '__pycache__', '.perfect21', 'venv', 'node_modules']):
                    sensitive_files.append({
                        "file": str(match.relative_to(self.project_root)),
                        "pattern": pattern,
                        "size": match.stat().st_size if match.exists() else 0
                    })

        return {
            "files": sensitive_files,
            "count": len(sensitive_files)
        }

    async def _check_file_permissions(self) -> Dict[str, Any]:
        """检查文件权限"""
        key_files = [
            'main/cli.py',
            'main/perfect21.py',
            'scripts/*.sh'
        ]

        insecure_permissions = []

        for pattern in key_files:
            if '*' in pattern:
                files = list(self.project_root.rglob(pattern))
            else:
                files = [self.project_root / pattern]

            for file_path in files:
                if file_path.exists():
                    try:
                        stat = file_path.stat()
                        mode = oct(stat.st_mode)[-3:]

                        # 检查是否有过宽的权限
                        if mode.endswith('7') or mode.endswith('6'):  # 其他用户有写权限
                            insecure_permissions.append({
                                "file": str(file_path.relative_to(self.project_root)),
                                "mode": mode,
                                "issue": "其他用户有写权限"
                            })

                        # 检查脚本文件权限
                        if file_path.suffix in ['.sh', '.py'] and not mode.startswith('7'):
                            insecure_permissions.append({
                                "file": str(file_path.relative_to(self.project_root)),
                                "mode": mode,
                                "issue": "脚本文件可能缺少执行权限"
                            })

                    except Exception:
                        continue

        return {
            "insecure_permissions": insecure_permissions,
            "files_checked": len([f for pattern in key_files for f in
                                (list(self.project_root.rglob(pattern)) if '*' in pattern
                                 else [self.project_root / pattern]) if f.exists()])
        }

    def _get_pattern_severity(self, category: str) -> str:
        """获取模式的严重程度"""
        severity_map = {
            "hardcoded_secrets": "high",
            "sql_injection": "high",
            "command_injection": "critical",
            "path_traversal": "high",
            "insecure_random": "medium",
            "debug_code": "low"
        }
        return severity_map.get(category, "medium")

    def _calculate_security_score(self, details: Dict[str, Any], violations: List[Dict[str, Any]]) -> float:
        """计算安全分数"""
        base_score = 100.0

        # 根据违规严重程度扣分
        for violation in violations:
            severity = violation.get("severity", "medium")
            if severity == "critical":
                base_score -= 25
            elif severity == "high":
                base_score -= 15
            elif severity == "medium":
                base_score -= 8
            elif severity == "low":
                base_score -= 3

        # Bandit问题扣分
        bandit_data = details.get("bandit", {})
        bandit_issues = bandit_data.get("issues", [])
        for issue in bandit_issues:
            if issue["severity"] == "HIGH":
                base_score -= 10
            elif issue["severity"] == "MEDIUM":
                base_score -= 5
            elif issue["severity"] == "LOW":
                base_score -= 2

        # 敏感文件扣分
        sensitive_files = details.get("sensitive_files", {}).get("count", 0)
        base_score -= min(sensitive_files * 3, 15)

        # 权限问题扣分
        permission_issues = len(details.get("permissions", {}).get("insecure_permissions", []))
        base_score -= min(permission_issues * 2, 10)

        # 确保分数在0-100范围内
        return max(0.0, min(100.0, base_score))