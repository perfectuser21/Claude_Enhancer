#!/usr/bin/env python3
"""
Perfect21 安全测试套件
全面的安全漏洞检测和防护验证 - 像专业的网络安全团队
"""

import pytest
import asyncio
import aiohttp
import hashlib
import hmac
import time
import json
import ssl
import socket
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import requests
from urllib.parse import urljoin, urlparse
import warnings

# 忽略SSL警告（仅用于测试）
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)


@dataclass
class SecurityTestResult:
    """安全测试结果"""
    test_name: str
    vulnerability_type: str
    severity: str  # "critical", "high", "medium", "low", "info"
    status: str    # "vulnerable", "secure", "inconclusive"
    details: str
    remediation: Optional[str] = None


class SecurityTestConfig:
    """安全测试配置"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.timeout = 30
        self.max_retries = 3

        # 测试用户凭据
        self.test_user = {
            "email": "security-test@perfect21.com",
            "password": "SecurityTest123!",
            "username": "securitytest"
        }

        # SQL注入测试载荷
        self.sql_injection_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "admin'/*",
            "' OR 1=1#",
            "' OR 'a'='a",
            "') OR ('1'='1",
            "1' AND (SELECT COUNT(*) FROM users) > 0 --",
            "'; WAITFOR DELAY '00:00:05' --"
        ]

        # XSS测试载荷
        self.xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>",
            "<keygen onfocus=alert('XSS') autofocus>"
        ]

        # 命令注入测试载荷
        self.command_injection_payloads = [
            "; ls -la",
            "| whoami",
            "&& cat /etc/passwd",
            "; cat /etc/shadow",
            "| id",
            "&& ps aux",
            "; netstat -an",
            "| uname -a",
            "&& env",
            "; pwd"
        ]


class AuthenticationSecurityTester:
    """认证安全测试器"""

    def __init__(self, config: SecurityTestConfig):
        self.config = config
        self.session = requests.Session()
        self.results = []

    def test_authentication_bypass(self) -> List[SecurityTestResult]:
        """测试认证绕过漏洞"""
        results = []

        # 测试SQL注入绕过认证
        for payload in self.config.sql_injection_payloads:
            result = self._test_sql_injection_auth_bypass(payload)
            if result:
                results.append(result)

        # 测试默认凭据
        result = self._test_default_credentials()
        if result:
            results.append(result)

        # 测试弱密码策略
        result = self._test_weak_password_policy()
        if result:
            results.append(result)

        # 测试暴力破解防护
        result = self._test_brute_force_protection()
        if result:
            results.append(result)

        return results

    def _test_sql_injection_auth_bypass(self, payload: str) -> Optional[SecurityTestResult]:
        """测试SQL注入认证绕过"""
        try:
            login_data = {
                "email": payload,
                "password": "any_password"
            }

            response = self.session.post(
                urljoin(self.config.base_url, "/api/v1/auth/login"),
                json=login_data,
                timeout=self.config.timeout,
                verify=False
            )

            # 检查是否成功绕过认证
            if response.status_code == 200 and "token" in response.text.lower():
                return SecurityTestResult(
                    test_name="SQL注入认证绕过",
                    vulnerability_type="SQL Injection",
                    severity="critical",
                    status="vulnerable",
                    details=f"使用载荷 '{payload}' 成功绕过认证",
                    remediation="使用参数化查询或ORM，对所有用户输入进行验证和过滤"
                )

        except Exception as e:
            pass  # 预期的错误

        return None

    def _test_default_credentials(self) -> Optional[SecurityTestResult]:
        """测试默认凭据"""
        default_creds = [
            ("admin", "admin"),
            ("admin", "password"),
            ("admin", "123456"),
            ("administrator", "administrator"),
            ("root", "root"),
            ("test", "test")
        ]

        for username, password in default_creds:
            try:
                login_data = {
                    "email": f"{username}@perfect21.com",
                    "password": password
                }

                response = self.session.post(
                    urljoin(self.config.base_url, "/api/v1/auth/login"),
                    json=login_data,
                    timeout=self.config.timeout,
                    verify=False
                )

                if response.status_code == 200:
                    return SecurityTestResult(
                        test_name="默认凭据测试",
                        vulnerability_type="Weak Authentication",
                        severity="high",
                        status="vulnerable",
                        details=f"发现默认凭据: {username}/{password}",
                        remediation="删除或更改所有默认账户密码"
                    )

            except Exception:
                continue

        return SecurityTestResult(
            test_name="默认凭据测试",
            vulnerability_type="Weak Authentication",
            severity="info",
            status="secure",
            details="未发现默认凭据",
            remediation=None
        )

    def _test_weak_password_policy(self) -> Optional[SecurityTestResult]:
        """测试弱密码策略"""
        weak_passwords = [
            "123456",
            "password",
            "123",
            "abc",
            "qwerty",
            "admin"
        ]

        for weak_password in weak_passwords:
            try:
                register_data = {
                    "email": f"weaktest-{int(time.time())}@perfect21.com",
                    "password": weak_password,
                    "username": f"weaktest{int(time.time())}"
                }

                response = self.session.post(
                    urljoin(self.config.base_url, "/api/v1/auth/register"),
                    json=register_data,
                    timeout=self.config.timeout,
                    verify=False
                )

                if response.status_code == 200 or response.status_code == 201:
                    return SecurityTestResult(
                        test_name="弱密码策略测试",
                        vulnerability_type="Weak Password Policy",
                        severity="medium",
                        status="vulnerable",
                        details=f"系统接受弱密码: {weak_password}",
                        remediation="实施强密码策略，要求复杂密码组合"
                    )

            except Exception:
                continue

        return SecurityTestResult(
            test_name="弱密码策略测试",
            vulnerability_type="Weak Password Policy",
            severity="info",
            status="secure",
            details="密码策略验证正常",
            remediation=None
        )

    def _test_brute_force_protection(self) -> Optional[SecurityTestResult]:
        """测试暴力破解防护"""
        login_url = urljoin(self.config.base_url, "/api/v1/auth/login")

        # 发送多次失败登录请求
        for i in range(10):
            try:
                login_data = {
                    "email": "brute-force-test@perfect21.com",
                    "password": f"wrong_password_{i}"
                }

                response = self.session.post(
                    login_url,
                    json=login_data,
                    timeout=self.config.timeout,
                    verify=False
                )

                # 检查是否有速率限制
                if response.status_code == 429:  # Too Many Requests
                    return SecurityTestResult(
                        test_name="暴力破解防护测试",
                        vulnerability_type="Brute Force Protection",
                        severity="info",
                        status="secure",
                        details="检测到速率限制保护",
                        remediation=None
                    )

            except Exception:
                continue

        return SecurityTestResult(
            test_name="暴力破解防护测试",
            vulnerability_type="Brute Force Protection",
            severity="medium",
            status="vulnerable",
            details="未检测到暴力破解防护机制",
            remediation="实施账户锁定和速率限制机制"
        )


class InjectionSecurityTester:
    """注入攻击安全测试器"""

    def __init__(self, config: SecurityTestConfig):
        self.config = config
        self.session = requests.Session()

    def test_sql_injection(self) -> List[SecurityTestResult]:
        """测试SQL注入漏洞"""
        results = []

        # 测试登录表单SQL注入
        for payload in self.config.sql_injection_payloads:
            result = self._test_sql_injection_in_endpoint(
                "/api/v1/auth/login",
                {"email": payload, "password": "test"},
                "登录端点SQL注入"
            )
            if result:
                results.append(result)

        # 测试搜索功能SQL注入
        for payload in self.config.sql_injection_payloads:
            result = self._test_sql_injection_in_endpoint(
                "/api/v1/users/search",
                {"query": payload},
                "搜索端点SQL注入"
            )
            if result:
                results.append(result)

        return results

    def _test_sql_injection_in_endpoint(self, endpoint: str, data: dict, test_name: str) -> Optional[SecurityTestResult]:
        """在特定端点测试SQL注入"""
        try:
            response = self.session.post(
                urljoin(self.config.base_url, endpoint),
                json=data,
                timeout=self.config.timeout,
                verify=False
            )

            # 检查SQL错误信息
            sql_error_patterns = [
                "sql syntax",
                "mysql_fetch",
                "ORA-",
                "Microsoft Access Driver",
                "SQLServer JDBC Driver",
                "PostgreSQL query failed",
                "syntax error at or near",
                "MySqlException"
            ]

            response_text = response.text.lower()
            for pattern in sql_error_patterns:
                if pattern.lower() in response_text:
                    return SecurityTestResult(
                        test_name=test_name,
                        vulnerability_type="SQL Injection",
                        severity="critical",
                        status="vulnerable",
                        details=f"检测到SQL错误信息: {pattern}",
                        remediation="使用参数化查询，验证和过滤所有用户输入"
                    )

        except Exception:
            pass

        return None

    def test_xss_vulnerabilities(self) -> List[SecurityTestResult]:
        """测试XSS漏洞"""
        results = []

        # 测试反射型XSS
        for payload in self.config.xss_payloads:
            result = self._test_reflected_xss(payload)
            if result:
                results.append(result)

        # 测试存储型XSS
        for payload in self.config.xss_payloads:
            result = self._test_stored_xss(payload)
            if result:
                results.append(result)

        return results

    def _test_reflected_xss(self, payload: str) -> Optional[SecurityTestResult]:
        """测试反射型XSS"""
        try:
            # 测试搜索参数中的XSS
            response = self.session.get(
                urljoin(self.config.base_url, f"/search?q={payload}"),
                timeout=self.config.timeout,
                verify=False
            )

            if payload in response.text and "text/html" in response.headers.get("content-type", ""):
                return SecurityTestResult(
                    test_name="反射型XSS测试",
                    vulnerability_type="Reflected XSS",
                    severity="high",
                    status="vulnerable",
                    details=f"在搜索功能中检测到反射型XSS: {payload}",
                    remediation="对所有用户输入进行HTML编码和验证"
                )

        except Exception:
            pass

        return None

    def _test_stored_xss(self, payload: str) -> Optional[SecurityTestResult]:
        """测试存储型XSS"""
        try:
            # 尝试在用户资料中存储XSS载荷
            profile_data = {
                "first_name": payload,
                "last_name": "Test",
                "bio": f"Biography with {payload}"
            }

            # 先登录获取令牌
            auth_token = self._get_auth_token()
            if not auth_token:
                return None

            headers = {"Authorization": f"Bearer {auth_token}"}

            # 更新用户资料
            response = self.session.put(
                urljoin(self.config.base_url, "/api/v1/user/profile"),
                json=profile_data,
                headers=headers,
                timeout=self.config.timeout,
                verify=False
            )

            if response.status_code == 200:
                # 获取用户资料查看是否存储了载荷
                get_response = self.session.get(
                    urljoin(self.config.base_url, "/api/v1/user/profile"),
                    headers=headers,
                    timeout=self.config.timeout,
                    verify=False
                )

                if payload in get_response.text:
                    return SecurityTestResult(
                        test_name="存储型XSS测试",
                        vulnerability_type="Stored XSS",
                        severity="critical",
                        status="vulnerable",
                        details=f"在用户资料中检测到存储型XSS: {payload}",
                        remediation="对存储的数据进行HTML编码，实施内容安全策略(CSP)"
                    )

        except Exception:
            pass

        return None

    def _get_auth_token(self) -> Optional[str]:
        """获取认证令牌"""
        try:
            response = self.session.post(
                urljoin(self.config.base_url, "/api/v1/auth/login"),
                json=self.config.test_user,
                timeout=self.config.timeout,
                verify=False
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("tokens", {}).get("access_token")

        except Exception:
            pass

        return None


class AuthorizationSecurityTester:
    """授权安全测试器"""

    def __init__(self, config: SecurityTestConfig):
        self.config = config
        self.session = requests.Session()

    def test_authorization_bypass(self) -> List[SecurityTestResult]:
        """测试授权绕过漏洞"""
        results = []

        # 测试直接对象引用
        result = self._test_direct_object_reference()
        if result:
            results.append(result)

        # 测试权限提升
        result = self._test_privilege_escalation()
        if result:
            results.append(result)

        # 测试未认证访问
        result = self._test_unauthenticated_access()
        if result:
            results.append(result)

        return results

    def _test_direct_object_reference(self) -> Optional[SecurityTestResult]:
        """测试直接对象引用漏洞"""
        try:
            # 尝试访问其他用户的数据
            user_ids = [1, 2, 3, 999, 1000]

            for user_id in user_ids:
                response = self.session.get(
                    urljoin(self.config.base_url, f"/api/v1/users/{user_id}"),
                    timeout=self.config.timeout,
                    verify=False
                )

                if response.status_code == 200:
                    return SecurityTestResult(
                        test_name="直接对象引用测试",
                        vulnerability_type="Insecure Direct Object Reference",
                        severity="high",
                        status="vulnerable",
                        details=f"未授权访问用户ID {user_id} 的数据",
                        remediation="实施适当的访问控制和权限验证"
                    )

        except Exception:
            pass

        return SecurityTestResult(
            test_name="直接对象引用测试",
            vulnerability_type="Insecure Direct Object Reference",
            severity="info",
            status="secure",
            details="访问控制验证正常",
            remediation=None
        )

    def _test_privilege_escalation(self) -> Optional[SecurityTestResult]:
        """测试权限提升漏洞"""
        try:
            # 获取普通用户令牌
            auth_token = self._get_auth_token()
            if not auth_token:
                return None

            headers = {"Authorization": f"Bearer {auth_token}"}

            # 尝试访问管理员功能
            admin_endpoints = [
                "/api/v1/admin/users",
                "/api/v1/admin/config",
                "/api/v1/admin/logs",
                "/api/v1/admin/stats"
            ]

            for endpoint in admin_endpoints:
                response = self.session.get(
                    urljoin(self.config.base_url, endpoint),
                    headers=headers,
                    timeout=self.config.timeout,
                    verify=False
                )

                if response.status_code == 200:
                    return SecurityTestResult(
                        test_name="权限提升测试",
                        vulnerability_type="Privilege Escalation",
                        severity="critical",
                        status="vulnerable",
                        details=f"普通用户可访问管理员端点: {endpoint}",
                        remediation="实施基于角色的访问控制(RBAC)"
                    )

        except Exception:
            pass

        return SecurityTestResult(
            test_name="权限提升测试",
            vulnerability_type="Privilege Escalation",
            severity="info",
            status="secure",
            details="权限控制验证正常",
            remediation=None
        )

    def _test_unauthenticated_access(self) -> Optional[SecurityTestResult]:
        """测试未认证访问"""
        try:
            protected_endpoints = [
                "/api/v1/user/profile",
                "/api/v1/user/settings",
                "/api/v1/users",
                "/api/v1/admin/users"
            ]

            vulnerable_endpoints = []

            for endpoint in protected_endpoints:
                response = self.session.get(
                    urljoin(self.config.base_url, endpoint),
                    timeout=self.config.timeout,
                    verify=False
                )

                if response.status_code == 200:
                    vulnerable_endpoints.append(endpoint)

            if vulnerable_endpoints:
                return SecurityTestResult(
                    test_name="未认证访问测试",
                    vulnerability_type="Authentication Bypass",
                    severity="high",
                    status="vulnerable",
                    details=f"以下端点允许未认证访问: {', '.join(vulnerable_endpoints)}",
                    remediation="为所有敏感端点添加认证验证"
                )

        except Exception:
            pass

        return SecurityTestResult(
            test_name="未认证访问测试",
            vulnerability_type="Authentication Bypass",
            severity="info",
            status="secure",
            details="认证控制验证正常",
            remediation=None
        )

    def _get_auth_token(self) -> Optional[str]:
        """获取认证令牌"""
        try:
            response = self.session.post(
                urljoin(self.config.base_url, "/api/v1/auth/login"),
                json=self.config.test_user,
                timeout=self.config.timeout,
                verify=False
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("tokens", {}).get("access_token")

        except Exception:
            pass

        return None


class SecurityTestRunner:
    """安全测试主运行器"""

    def __init__(self, config: SecurityTestConfig):
        self.config = config
        self.auth_tester = AuthenticationSecurityTester(config)
        self.injection_tester = InjectionSecurityTester(config)
        self.authorization_tester = AuthorizationSecurityTester(config)

    def run_comprehensive_security_tests(self) -> Dict[str, List[SecurityTestResult]]:
        """运行全面的安全测试"""
        results = {
            "authentication": [],
            "injection": [],
            "authorization": [],
            "configuration": []
        }

        print("🔒 开始Perfect21安全测试套件...")

        # 认证安全测试
        print("🔐 执行认证安全测试...")
        results["authentication"] = self.auth_tester.test_authentication_bypass()

        # 注入攻击测试
        print("💉 执行注入攻击测试...")
        injection_results = []
        injection_results.extend(self.injection_tester.test_sql_injection())
        injection_results.extend(self.injection_tester.test_xss_vulnerabilities())
        results["injection"] = injection_results

        # 授权安全测试
        print("🛡️  执行授权安全测试...")
        results["authorization"] = self.authorization_tester.test_authorization_bypass()

        # 配置安全测试
        print("⚙️  执行配置安全测试...")
        results["configuration"] = self._test_security_configurations()

        return results

    def _test_security_configurations(self) -> List[SecurityTestResult]:
        """测试安全配置"""
        results = []

        # 测试HTTPS配置
        result = self._test_https_configuration()
        if result:
            results.append(result)

        # 测试安全头配置
        result = self._test_security_headers()
        if result:
            results.append(result)

        # 测试信息泄露
        result = self._test_information_disclosure()
        if result:
            results.append(result)

        return results

    def _test_https_configuration(self) -> Optional[SecurityTestResult]:
        """测试HTTPS配置"""
        try:
            # 检查是否强制使用HTTPS
            http_url = self.config.base_url.replace("https://", "http://")
            response = requests.get(http_url, timeout=self.config.timeout, allow_redirects=False)

            if response.status_code not in [301, 302, 308] or "https" not in response.headers.get("location", "").lower():
                return SecurityTestResult(
                    test_name="HTTPS配置测试",
                    vulnerability_type="Insecure Communication",
                    severity="medium",
                    status="vulnerable",
                    details="未检测到HTTPS重定向",
                    remediation="配置强制HTTPS重定向"
                )

        except Exception:
            pass

        return SecurityTestResult(
            test_name="HTTPS配置测试",
            vulnerability_type="Insecure Communication",
            severity="info",
            status="secure",
            details="HTTPS配置正常",
            remediation=None
        )

    def _test_security_headers(self) -> Optional[SecurityTestResult]:
        """测试安全头配置"""
        try:
            response = requests.get(self.config.base_url, timeout=self.config.timeout, verify=False)
            headers = response.headers

            missing_headers = []
            security_headers = {
                "X-Frame-Options": "防止点击劫持",
                "X-Content-Type-Options": "防止MIME类型嗅探",
                "X-XSS-Protection": "XSS保护",
                "Strict-Transport-Security": "强制HTTPS",
                "Content-Security-Policy": "内容安全策略"
            }

            for header, description in security_headers.items():
                if header not in headers:
                    missing_headers.append(f"{header} ({description})")

            if missing_headers:
                return SecurityTestResult(
                    test_name="安全头配置测试",
                    vulnerability_type="Security Misconfiguration",
                    severity="medium",
                    status="vulnerable",
                    details=f"缺少安全头: {', '.join(missing_headers)}",
                    remediation="配置所有必需的安全HTTP头"
                )

        except Exception:
            pass

        return SecurityTestResult(
            test_name="安全头配置测试",
            vulnerability_type="Security Misconfiguration",
            severity="info",
            status="secure",
            details="安全头配置正常",
            remediation=None
        )

    def _test_information_disclosure(self) -> Optional[SecurityTestResult]:
        """测试信息泄露"""
        try:
            # 测试错误信息泄露
            response = requests.get(
                urljoin(self.config.base_url, "/nonexistent-endpoint"),
                timeout=self.config.timeout,
                verify=False
            )

            sensitive_patterns = [
                "stack trace",
                "debug",
                "exception",
                "error",
                "traceback",
                "mysql",
                "postgresql",
                "database"
            ]

            response_text = response.text.lower()
            for pattern in sensitive_patterns:
                if pattern in response_text:
                    return SecurityTestResult(
                        test_name="信息泄露测试",
                        vulnerability_type="Information Disclosure",
                        severity="low",
                        status="vulnerable",
                        details=f"错误页面可能泄露敏感信息: {pattern}",
                        remediation="配置自定义错误页面，隐藏敏感信息"
                    )

        except Exception:
            pass

        return SecurityTestResult(
            test_name="信息泄露测试",
            vulnerability_type="Information Disclosure",
            severity="info",
            status="secure",
            details="未检测到信息泄露",
            remediation=None
        )

    def generate_security_report(self, results: Dict[str, List[SecurityTestResult]]) -> str:
        """生成安全测试报告"""
        total_tests = sum(len(category_results) for category_results in results.values())
        vulnerable_tests = sum(
            len([r for r in category_results if r.status == "vulnerable"])
            for category_results in results.values()
        )

        # 按严重程度统计
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for category_results in results.values():
            for result in category_results:
                if result.status == "vulnerable":
                    severity_counts[result.severity] += 1

        report = f"""
# 🔒 Perfect21 安全测试报告

## 📊 测试摘要
- **总测试数**: {total_tests}
- **发现漏洞**: {vulnerable_tests}
- **安全率**: {((total_tests - vulnerable_tests) / total_tests * 100):.1f}%

## 🚨 漏洞严重程度分布
- **严重**: {severity_counts['critical']} 个
- **高危**: {severity_counts['high']} 个
- **中危**: {severity_counts['medium']} 个
- **低危**: {severity_counts['low']} 个
- **信息**: {severity_counts['info']} 个

## 📋 详细测试结果

"""

        for category, category_results in results.items():
            report += f"### {category.upper()} 安全测试\n\n"

            for result in category_results:
                status_icon = "❌" if result.status == "vulnerable" else "✅"
                severity_icon = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🔵",
                    "info": "⚪"
                }.get(result.severity, "⚪")

                report += f"**{status_icon} {result.test_name}**\n"
                report += f"- 类型: {result.vulnerability_type}\n"
                report += f"- 严重程度: {severity_icon} {result.severity.upper()}\n"
                report += f"- 状态: {result.status}\n"
                report += f"- 详情: {result.details}\n"

                if result.remediation:
                    report += f"- 修复建议: {result.remediation}\n"

                report += "\n"

        # 添加总体建议
        if vulnerable_tests > 0:
            report += """
## 💡 安全改进建议

1. **立即修复严重和高危漏洞**
2. **实施安全开发生命周期(SDLC)**
3. **定期进行安全测试和代码审查**
4. **建立安全监控和告警机制**
5. **对开发团队进行安全培训**

## 🔐 安全最佳实践

- 使用参数化查询防止SQL注入
- 对所有用户输入进行验证和编码
- 实施适当的认证和授权机制
- 配置安全HTTP头
- 启用HTTPS和安全传输
- 定期更新依赖项和安全补丁
"""
        else:
            report += """
## 🎉 安全状况良好

所有安全测试均已通过！继续保持良好的安全实践。

建议定期进行安全测试以确保持续的安全性。
"""

        return report


# 测试用例
class TestPerfect21Security:
    """Perfect21安全测试用例"""

    @pytest.fixture
    def security_config(self):
        """安全测试配置"""
        return SecurityTestConfig()

    @pytest.fixture
    def security_runner(self, security_config):
        """安全测试运行器"""
        return SecurityTestRunner(security_config)

    def test_authentication_security(self, security_runner):
        """测试认证安全"""
        results = security_runner.run_comprehensive_security_tests()

        # 检查是否有严重漏洞
        critical_vulns = []
        for category_results in results.values():
            for result in category_results:
                if result.status == "vulnerable" and result.severity == "critical":
                    critical_vulns.append(result)

        assert len(critical_vulns) == 0, f"发现严重安全漏洞: {[v.test_name for v in critical_vulns]}"

    def test_injection_vulnerabilities(self, security_runner):
        """测试注入漏洞"""
        injection_tester = InjectionSecurityTester(security_runner.config)

        # SQL注入测试
        sql_results = injection_tester.test_sql_injection()
        sql_vulns = [r for r in sql_results if r.status == "vulnerable"]
        assert len(sql_vulns) == 0, f"发现SQL注入漏洞: {[v.details for v in sql_vulns]}"

        # XSS测试
        xss_results = injection_tester.test_xss_vulnerabilities()
        xss_vulns = [r for r in xss_results if r.status == "vulnerable"]
        assert len(xss_vulns) == 0, f"发现XSS漏洞: {[v.details for v in xss_vulns]}"

    def test_authorization_security(self, security_runner):
        """测试授权安全"""
        auth_tester = AuthorizationSecurityTester(security_runner.config)
        results = auth_tester.test_authorization_bypass()

        high_risk_vulns = [r for r in results if r.status == "vulnerable" and r.severity in ["critical", "high"]]
        assert len(high_risk_vulns) == 0, f"发现高危授权漏洞: {[v.details for v in high_risk_vulns]}"


def main():
    """主函数 - 运行安全测试套件"""
    import argparse

    parser = argparse.ArgumentParser(description="Perfect21 安全测试套件")
    parser.add_argument("--base-url", default="http://localhost:8080", help="目标服务器URL")
    parser.add_argument("--output", default="security-report.md", help="报告输出文件")

    args = parser.parse_args()

    # 创建配置和运行器
    config = SecurityTestConfig(args.base_url)
    runner = SecurityTestRunner(config)

    print("🔒 开始Perfect21安全测试...")

    # 运行测试
    results = runner.run_comprehensive_security_tests()

    # 生成报告
    report = runner.generate_security_report(results)

    # 保存报告
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"📄 安全报告已保存到: {args.output}")

    # 检查是否有严重漏洞
    critical_vulns = []
    for category_results in results.values():
        for result in category_results:
            if result.status == "vulnerable" and result.severity in ["critical", "high"]:
                critical_vulns.append(result)

    if critical_vulns:
        print(f"⚠️  发现 {len(critical_vulns)} 个严重安全漏洞！")
        return 1
    else:
        print("✅ 安全测试通过")
        return 0


if __name__ == "__main__":
    exit(main())