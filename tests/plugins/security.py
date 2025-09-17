#!/usr/bin/env python3
"""
安全测试插件 - 用于安全漏洞测试
提供SQL注入、XSS、CSRF、认证漏洞等安全测试功能
"""

import re
import time
import hashlib
import secrets
import pytest
from typing import List, Dict, Any, Optional
from urllib.parse import quote, unquote


class SecurityTester:
    """安全测试器"""
    
    def __init__(self):
        self.payloads = self._load_security_payloads()
        self.test_results = {
            'sql_injection': [],
            'xss': [],
            'csrf': [],
            'auth_bypass': [],
            'input_validation': []
        }
    
    def _load_security_payloads(self) -> Dict[str, List[str]]:
        """加载安全测试载荷"""
        return {
            'sql_injection': [
                "'; DROP TABLE users; --",
                "' OR '1'='1",
                "' UNION SELECT * FROM users--",
                "admin'--",
                "' OR 1=1#",
                "'; INSERT INTO users VALUES('hacker','pass')--",
                "' AND (SELECT COUNT(*) FROM users) > 0--",
                "'; EXEC xp_cmdshell('dir')--"
            ],
            'xss': [
                "<script>alert('xss')</script>",
                "<img src=x onerror=alert('xss')>",
                "<svg onload=alert('xss')>",
                "javascript:alert('xss')",
                "<iframe src=javascript:alert('xss')></iframe>",
                "<body onload=alert('xss')>",
                "<div onclick=alert('xss')>click</div>",
                "'><script>alert('xss')</script>"
            ],
            'csrf': [
                "<form action='/api/login' method='post'><input name='email' value='attacker@evil.com'><input type='submit'></form>",
                "<img src='/api/logout'>",
                "<script>fetch('/api/change-password', {method:'POST', body:'newpass=hacked'})</script>"
            ],
            'path_traversal': [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                "....//....//....//etc//passwd"
            ],
            'command_injection': [
                "; cat /etc/passwd",
                "| whoami",
                "& net user",
                "`id`",
                "$(whoami)",
                "; rm -rf /"
            ]
        }
    
    def test_sql_injection(self, test_function, test_params: Dict[str, Any]) -> Dict[str, Any]:
        """测试SQL注入漏洞"""
        results = {
            'vulnerable': False,
            'payloads_tested': 0,
            'successful_payloads': [],
            'errors': []
        }
        
        for payload in self.payloads['sql_injection']:
            try:
                # 在所有字符串参数中注入payload
                modified_params = test_params.copy()
                for key, value in modified_params.items():
                    if isinstance(value, str):
                        modified_params[key] = payload
                        break
                
                result = test_function(**modified_params)
                results['payloads_tested'] += 1
                
                # 检查是否存在明显的SQL错误或异常行为
                if self._is_sql_injection_successful(result, payload):
                    results['vulnerable'] = True
                    results['successful_payloads'].append(payload)
                    
            except Exception as e:
                results['errors'].append({
                    'payload': payload,
                    'error': str(e)
                })
                # 某些错误可能表明存在漏洞
                if 'SQL' in str(e).upper() or 'syntax' in str(e).lower():
                    results['vulnerable'] = True
                    results['successful_payloads'].append(payload)
        
        self.test_results['sql_injection'].append(results)
        return results
    
    def _is_sql_injection_successful(self, result: Any, payload: str) -> bool:
        """判断SQL注入是否成功"""
        if not result:
            return False
            
        result_str = str(result).lower()
        
        # 检查常见的SQL错误模式
        sql_error_patterns = [
            'sql syntax',
            'mysql error',
            'ora-',
            'postgresql error',
            'sqlite error',
            'syntax error',
            'unexpected end of sql',
            'quoted string not properly terminated'
        ]
        
        for pattern in sql_error_patterns:
            if pattern in result_str:
                return True
        
        # 检查数据泄露迹象
        if "union" in payload.lower() and len(result_str) > 1000:
            return True
            
        return False
    
    def test_xss_vulnerability(self, test_function, test_params: Dict[str, Any]) -> Dict[str, Any]:
        """测试XSS漏洞"""
        results = {
            'vulnerable': False,
            'payloads_tested': 0,
            'successful_payloads': [],
            'reflected_payloads': []
        }
        
        for payload in self.payloads['xss']:
            try:
                modified_params = test_params.copy()
                for key, value in modified_params.items():
                    if isinstance(value, str):
                        modified_params[key] = payload
                        break
                
                result = test_function(**modified_params)
                results['payloads_tested'] += 1
                
                # 检查输出中是否包含payload（反射型XSS）
                if self._is_xss_reflected(result, payload):
                    results['vulnerable'] = True
                    results['successful_payloads'].append(payload)
                    results['reflected_payloads'].append(payload)
                    
            except Exception as e:
                # XSS不应该引起异常，如果引起了可能是输入验证问题
                pass
        
        self.test_results['xss'].append(results)
        return results
    
    def _is_xss_reflected(self, result: Any, payload: str) -> bool:
        """判断是否存在反射型XSS"""
        if not result:
            return False
            
        result_str = str(result)
        
        # 检查payload是否被原样返回
        if payload in result_str:
            return True
        
        # 检查HTML编码后的payload
        import html
        encoded_payload = html.escape(payload)
        if encoded_payload != payload and encoded_payload not in result_str:
            # 如果编码后payload不在输出中，说明进行了适当的转义
            return False
            
        return False
    
    def test_authentication_bypass(self, login_function, valid_creds: Dict[str, str]) -> Dict[str, Any]:
        """测试认证绕过漏洞"""
        results = {
            'vulnerable': False,
            'bypass_attempts': [],
            'successful_bypasses': []
        }
        
        bypass_techniques = [
            # SQL注入绕过
            {'email': "admin' OR '1'='1' --", 'password': 'anything'},
            {'email': "' OR 1=1 --", 'password': 'anything'},
            
            # 空密码绕过
            {'email': valid_creds['email'], 'password': ''},
            {'email': valid_creds['email'], 'password': None},
            
            # 特殊字符绕过
            {'email': valid_creds['email'], 'password': '%'},
            {'email': valid_creds['email'], 'password': '*'},
            
            # 默认凭证
            {'email': 'admin', 'password': 'admin'},
            {'email': 'administrator', 'password': 'password'},
            {'email': 'root', 'password': 'root'}
        ]
        
        for attempt in bypass_techniques:
            try:
                result = login_function(**attempt)
                results['bypass_attempts'].append({
                    'credentials': attempt,
                    'result': result
                })
                
                # 检查是否登录成功
                if self._is_login_successful(result):
                    results['vulnerable'] = True
                    results['successful_bypasses'].append(attempt)
                    
            except Exception as e:
                results['bypass_attempts'].append({
                    'credentials': attempt,
                    'error': str(e)
                })
        
        self.test_results['auth_bypass'].append(results)
        return results
    
    def _is_login_successful(self, result: Any) -> bool:
        """判断登录是否成功"""
        if isinstance(result, dict):
            return result.get('success', False) or 'token' in result
        return False
    
    def test_input_validation(self, test_function, field_validations: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """测试输入验证"""
        results = {
            'fields_tested': 0,
            'validation_failures': [],
            'vulnerable_fields': []
        }
        
        for field_name, validation_config in field_validations.items():
            test_cases = self._generate_input_test_cases(validation_config)
            
            for test_case in test_cases:
                try:
                    test_params = {field_name: test_case['value']}
                    result = test_function(**test_params)
                    
                    # 棄查验证是否按预期工作
                    if test_case['should_fail'] and self._is_request_successful(result):
                        results['validation_failures'].append({
                            'field': field_name,
                            'value': test_case['value'],
                            'test_type': test_case['test_type'],
                            'expected': 'rejection',
                            'actual': 'acceptance'
                        })
                        results['vulnerable_fields'].append(field_name)
                        
                except Exception as e:
                    # 异常可能是正常的验证行为
                    if not test_case['should_fail']:
                        results['validation_failures'].append({
                            'field': field_name,
                            'value': test_case['value'],
                            'test_type': test_case['test_type'],
                            'expected': 'acceptance',
                            'actual': f'exception: {str(e)}'
                        })
            
            results['fields_tested'] += 1
        
        self.test_results['input_validation'].append(results)
        return results
    
    def _generate_input_test_cases(self, validation_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成输入测试用例"""
        test_cases = []
        
        # 数据类型测试
        if validation_config.get('type') == 'email':
            test_cases.extend([
                {'value': 'valid@example.com', 'should_fail': False, 'test_type': 'valid_email'},
                {'value': 'invalid-email', 'should_fail': True, 'test_type': 'invalid_email'},
                {'value': '@missing-local.com', 'should_fail': True, 'test_type': 'missing_local'},
                {'value': 'missing-domain@', 'should_fail': True, 'test_type': 'missing_domain'}
            ])
        
        # 长度限制测试
        if 'max_length' in validation_config:
            max_len = validation_config['max_length']
            test_cases.extend([
                {'value': 'a' * max_len, 'should_fail': False, 'test_type': 'max_length_valid'},
                {'value': 'a' * (max_len + 1), 'should_fail': True, 'test_type': 'max_length_exceeded'}
            ])
        
        if 'min_length' in validation_config:
            min_len = validation_config['min_length']
            test_cases.extend([
                {'value': 'a' * min_len, 'should_fail': False, 'test_type': 'min_length_valid'},
                {'value': 'a' * max(0, min_len - 1), 'should_fail': True, 'test_type': 'min_length_not_met'}
            ])
        
        # 特殊字符测试
        special_chars = ['<script>', '"', "'", ';', '--', 'null', 'undefined']
        for char in special_chars:
            test_cases.append({
                'value': char,
                'should_fail': True,
                'test_type': f'special_char_{char}'
            })
        
        return test_cases
    
    def _is_request_successful(self, result: Any) -> bool:
        """判断请求是否成功"""
        if isinstance(result, dict):
            return result.get('success', True)  # 默认认为成功
        return True
    
    def test_timing_attacks(self, test_function, valid_input: Any, invalid_input: Any, iterations: int = 10) -> Dict[str, Any]:
        """测试时序攻击抗性"""
        valid_times = []
        invalid_times = []
        
        # 测试有效输入的响应时间
        for _ in range(iterations):
            start_time = time.perf_counter()
            try:
                test_function(valid_input)
            except:
                pass
            end_time = time.perf_counter()
            valid_times.append((end_time - start_time) * 1000)  # 转换为毫秒
        
        # 测试无效输入的响应时间
        for _ in range(iterations):
            start_time = time.perf_counter()
            try:
                test_function(invalid_input)
            except:
                pass
            end_time = time.perf_counter()
            invalid_times.append((end_time - start_time) * 1000)
        
        # 统计分析
        avg_valid_time = sum(valid_times) / len(valid_times)
        avg_invalid_time = sum(invalid_times) / len(invalid_times)
        time_difference = abs(avg_valid_time - avg_invalid_time)
        
        # 如果时间差异超过50ms，可能存在时序攻击漏洞
        vulnerable = time_difference > 50
        
        return {
            'vulnerable': vulnerable,
            'avg_valid_time_ms': avg_valid_time,
            'avg_invalid_time_ms': avg_invalid_time,
            'time_difference_ms': time_difference,
            'iterations': iterations,
            'all_valid_times': valid_times,
            'all_invalid_times': invalid_times
        }
    
    def generate_security_report(self) -> str:
        """生成安全测试报告"""
        report = """
# 安全测试报告

## SQL注入测试
"""
        
        for result in self.test_results['sql_injection']:
            status = "❌ 存在漏洞" if result['vulnerable'] else "✅ 安全"
            report += f"- {status}: 测试了 {result['payloads_tested']} 个payload\n"
            if result['successful_payloads']:
                report += f"  成功的payload: {result['successful_payloads'][:3]}\n"
        
        report += "\n## XSS漏洞测试\n"
        for result in self.test_results['xss']:
            status = "❌ 存在漏洞" if result['vulnerable'] else "✅ 安全"
            report += f"- {status}: 测试了 {result['payloads_tested']} 个payload\n"
        
        report += "\n## 认证绕过测试\n"
        for result in self.test_results['auth_bypass']:
            status = "❌ 存在漏洞" if result['vulnerable'] else "✅ 安全"
            report += f"- {status}: 测试了 {len(result['bypass_attempts'])} 种绕过方法\n"
        
        return report


class CSRFTester:
    """
CSRF测试器
    """
    
    def __init__(self):
        self.csrf_tokens = set()
    
    def test_csrf_protection(self, request_function, sensitive_operation_params: Dict[str, Any]) -> Dict[str, Any]:
        """测试CSRF防护"""
        results = {
            'protected': True,
            'missing_token_blocked': False,
            'invalid_token_blocked': False,
            'tests_performed': 0
        }
        
        # 测试缺少CSRF token
        try:
            result = request_function(**sensitive_operation_params)
            results['tests_performed'] += 1
            if self._is_operation_successful(result):
                results['protected'] = False
            else:
                results['missing_token_blocked'] = True
        except Exception:
            results['missing_token_blocked'] = True
        
        # 测试无效CSRF token
        try:
            params_with_invalid_token = sensitive_operation_params.copy()
            params_with_invalid_token['csrf_token'] = 'invalid_token_' + secrets.token_hex(16)
            result = request_function(**params_with_invalid_token)
            results['tests_performed'] += 1
            if self._is_operation_successful(result):
                results['protected'] = False
            else:
                results['invalid_token_blocked'] = True
        except Exception:
            results['invalid_token_blocked'] = True
        
        return results
    
    def _is_operation_successful(self, result: Any) -> bool:
        """判断操作是否成功"""
        if isinstance(result, dict):
            return result.get('success', False)
        return False


@pytest.fixture
def security_tester():
    """安全测试器夹具"""
    return SecurityTester()

@pytest.fixture
def csrf_tester():
    """
CSRF测试器夹具
    """
    return CSRFTester()

# Pytest 标记
def pytest_configure(config):
    """注册Pytest标记"""
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )
    config.addinivalue_line(
        "markers", "sql_injection: mark test as SQL injection test"
    )
    config.addinivalue_line(
        "markers", "xss: mark test as XSS test"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication test"
    )
    config.addinivalue_line(
        "markers", "csrf: mark test as CSRF test"
    )
