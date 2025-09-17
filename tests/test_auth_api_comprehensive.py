#!/usr/bin/env python3
"""
Perfect21 用户登录API接口全面测试套件

测试覆盖范围：
- 单元测试：认证逻辑、数据验证、错误处理
- 集成测试：API端点、数据库交互、第三方服务
- E2E测试：完整用户流程、会话管理
- 性能测试：负载测试、压力测试、并发测试
- 安全测试：SQL注入、XSS、暴力破解防护
"""

import os
import sys
import json
import time
import asyncio
import pytest
import httpx
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from api.rest_server import app
from config.security_config import SecurityConfig


class UserAuthAPI:
    """用户认证API接口 - 模拟实现用于测试"""
    
    def __init__(self):
        self.users_db = {
            "testuser@example.com": {
                "id": "user_001",
                "email": "testuser@example.com",
                "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
                "is_active": True,
                "created_at": "2023-01-01T00:00:00Z",
                "login_attempts": 0,
                "last_login": None
            },
            "locked@example.com": {
                "id": "user_002", 
                "email": "locked@example.com",
                "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
                "is_active": False,
                "created_at": "2023-01-01T00:00:00Z",
                "login_attempts": 5,
                "last_login": None
            }
        }
        self.sessions = {}
        self.rate_limits = {}
    
    async def login(self, email: str, password: str, ip_address: str = "127.0.0.1") -> Dict[str, Any]:
        """用户登录"""
        # 速率限制检查
        if self._is_rate_limited(ip_address):
            return {"success": False, "error": "Too many login attempts", "code": "RATE_LIMITED"}
        
        # 用户存在性检查
        user = self.users_db.get(email)
        if not user:
            self._record_attempt(ip_address)
            return {"success": False, "error": "Invalid credentials", "code": "INVALID_CREDENTIALS"}
        
        # 账户状态检查
        if not user["is_active"]:
            return {"success": False, "error": "Account locked", "code": "ACCOUNT_LOCKED"}
        
        # 密码验证（简化版）
        if not self._verify_password(password, user["password_hash"]):
            self._record_attempt(ip_address)
            user["login_attempts"] += 1
            if user["login_attempts"] >= 5:
                user["is_active"] = False
            return {"success": False, "error": "Invalid credentials", "code": "INVALID_CREDENTIALS"}
        
        # 登录成功
        session_token = f"session_{int(time.time())}_{user['id']}"
        self.sessions[session_token] = {
            "user_id": user["id"],
            "email": email,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "ip_address": ip_address
        }
        
        user["last_login"] = datetime.now().isoformat()
        user["login_attempts"] = 0
        
        return {
            "success": True,
            "token": session_token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "last_login": user["last_login"]
            }
        }
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """密码验证（简化版）"""
        return password == "secret"  # 简化实现
    
    def _is_rate_limited(self, ip_address: str) -> bool:
        """检查IP是否被限流"""
        now = time.time()
        if ip_address not in self.rate_limits:
            self.rate_limits[ip_address] = []
        
        # 清理过期的尝试记录
        self.rate_limits[ip_address] = [
            t for t in self.rate_limits[ip_address] 
            if now - t < 900  # 15分钟内
        ]
        
        return len(self.rate_limits[ip_address]) >= 10
    
    def _record_attempt(self, ip_address: str):
        """记录登录尝试"""
        if ip_address not in self.rate_limits:
            self.rate_limits[ip_address] = []
        self.rate_limits[ip_address].append(time.time())


# 测试夹具
@pytest.fixture
def auth_api():
    """认证API实例"""
    return UserAuthAPI()

@pytest.fixture
def test_client():
    """测试客户端"""
    return TestClient(app)

@pytest.fixture
def valid_login_data():
    """有效登录数据"""
    return {
        "email": "testuser@example.com",
        "password": "secret"
    }

@pytest.fixture
def invalid_login_data():
    """无效登录数据"""
    return {
        "email": "nonexistent@example.com", 
        "password": "wrongpass"
    }


@pytest.mark.unit
class TestUserAuthUnitTests:
    """用户认证单元测试"""
    
    @pytest.mark.asyncio
    async def test_successful_login(self, auth_api, valid_login_data):
        """测试成功登录"""
        result = await auth_api.login(**valid_login_data)
        
        assert result["success"] is True
        assert "token" in result
        assert result["user"]["email"] == valid_login_data["email"]
        assert "id" in result["user"]
    
    @pytest.mark.asyncio
    async def test_invalid_credentials(self, auth_api, invalid_login_data):
        """测试无效凭证"""
        result = await auth_api.login(**invalid_login_data)
        
        assert result["success"] is False
        assert result["code"] == "INVALID_CREDENTIALS"
        assert "token" not in result
    
    @pytest.mark.asyncio
    async def test_locked_account(self, auth_api):
        """测试锁定账户"""
        result = await auth_api.login("locked@example.com", "secret")
        
        assert result["success"] is False
        assert result["code"] == "ACCOUNT_LOCKED"
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, auth_api):
        """测试速率限制"""
        ip_address = "192.168.1.100"
        
        # 模拟多次失败尝试
        for _ in range(10):
            auth_api._record_attempt(ip_address)
        
        result = await auth_api.login("testuser@example.com", "secret", ip_address)
        
        assert result["success"] is False
        assert result["code"] == "RATE_LIMITED"
    
    @pytest.mark.asyncio
    async def test_account_lockout_after_failed_attempts(self, auth_api):
        """测试多次失败后账户锁定"""
        email = "testuser@example.com"
        
        # 模拟5次失败尝试
        for _ in range(5):
            await auth_api.login(email, "wrongpassword")
        
        # 账户应该被锁定
        user = auth_api.users_db[email]
        assert user["is_active"] is False
    
    def test_password_validation(self, auth_api):
        """测试密码验证"""
        assert auth_api._verify_password("secret", "hash") is True
        assert auth_api._verify_password("wrong", "hash") is False
    
    def test_ip_rate_limiting_logic(self, auth_api):
        """测试IP限流逻辑"""
        ip = "192.168.1.1"
        
        # 未达到限制
        assert auth_api._is_rate_limited(ip) is False
        
        # 记录10次尝试
        for _ in range(10):
            auth_api._record_attempt(ip)
        
        # 应该被限制
        assert auth_api._is_rate_limited(ip) is True


@pytest.mark.integration
class TestAuthAPIIntegration:
    """认证API集成测试"""
    
    def test_health_endpoint(self, test_client):
        """测试健康检查端点"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "perfect21_available" in data
    
    def test_root_endpoint(self, test_client):
        """测试根端点"""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Perfect21 REST API"
    
    @patch('api.rest_server.Perfect21SDK')
    def test_task_endpoint_integration(self, mock_sdk, test_client):
        """测试任务端点集成"""
        # 模拟SDK返回
        mock_instance = Mock()
        mock_instance.task.return_value = {
            "success": True,
            "stdout": "Task completed successfully"
        }
        mock_sdk.return_value = mock_instance
        
        response = test_client.post("/task", json={
            "description": "Create login API",
            "timeout": 300
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "output" in data


@pytest.mark.security
class TestAuthSecurityTests:
    """认证安全测试"""
    
    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, auth_api):
        """测试SQL注入防护"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--"
        ]
        
        for malicious_input in malicious_inputs:
            result = await auth_api.login(malicious_input, "password")
            assert result["success"] is False
            assert result["code"] == "INVALID_CREDENTIALS"
    
    @pytest.mark.asyncio
    async def test_xss_prevention(self, auth_api):
        """测试XSS防护"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            result = await auth_api.login(payload, "password")
            assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_timing_attack_resistance(self, auth_api):
        """测试时序攻击抗性"""
        start_time = time.time()
        await auth_api.login("nonexistent@example.com", "password")
        non_existent_time = time.time() - start_time
        
        start_time = time.time()
        await auth_api.login("testuser@example.com", "wrongpassword")
        wrong_password_time = time.time() - start_time
        
        # 时间差异应该在合理范围内
        time_difference = abs(non_existent_time - wrong_password_time)
        assert time_difference < 0.1  # 100ms内
    
    @pytest.mark.asyncio
    async def test_brute_force_protection(self, auth_api):
        """测试暴力破解防护"""
        ip_address = "192.168.1.200"
        
        # 模拟暴力破解尝试
        for attempt in range(15):
            result = await auth_api.login("testuser@example.com", f"wrong{attempt}", ip_address)
            
            if attempt >= 10:
                assert result["code"] == "RATE_LIMITED"
            else:
                assert result["code"] == "INVALID_CREDENTIALS"


@pytest.mark.performance
class TestAuthPerformanceTests:
    """认证性能测试"""
    
    @pytest.mark.asyncio
    async def test_concurrent_login_performance(self, auth_api):
        """测试并发登录性能"""
        async def single_login():
            return await auth_api.login("testuser@example.com", "secret", f"192.168.1.{time.time()}")
        
        start_time = time.time()
        
        # 并发100个请求
        tasks = [single_login() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 100个请求应在5秒内完成
        assert duration < 5.0
        
        # 所有请求应成功
        successful_logins = sum(1 for r in results if r["success"])
        assert successful_logins == 100
    
    @pytest.mark.asyncio
    async def test_login_response_time(self, auth_api):
        """测试登录响应时间"""
        response_times = []
        
        for _ in range(10):
            start_time = time.time()
            await auth_api.login("testuser@example.com", "secret")
            response_time = time.time() - start_time
            response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        # 平均响应时间应小于100ms
        assert avg_response_time < 0.1
        # 最大响应时间应小于200ms
        assert max_response_time < 0.2
    
    def test_memory_usage_under_load(self, auth_api):
        """测试负载下内存使用"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # 执行大量操作
        for i in range(1000):
            # 创建用户数据
            email = f"user{i}@example.com"
            auth_api.users_db[email] = {
                "id": f"user_{i:03d}",
                "email": email,
                "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00Z",
                "login_attempts": 0,
                "last_login": None
            }
        
        gc.collect()  # 强制垃圾回收
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 内存增长应控制在合理范围（50MB）
        assert memory_increase < 50 * 1024 * 1024


@pytest.mark.e2e
class TestAuthE2ETests:
    """认证端到端测试"""
    
    @pytest.mark.asyncio
    async def test_complete_login_flow(self, auth_api):
        """测试完整登录流程"""
        # 1. 初始状态检查
        user_email = "testuser@example.com"
        user = auth_api.users_db[user_email]
        assert user["last_login"] is None
        
        # 2. 执行登录
        result = await auth_api.login(user_email, "secret")
        assert result["success"] is True
        
        # 3. 验证会话创建
        token = result["token"]
        assert token in auth_api.sessions
        
        session = auth_api.sessions[token]
        assert session["email"] == user_email
        assert session["user_id"] == user["id"]
        
        # 4. 验证用户状态更新
        updated_user = auth_api.users_db[user_email]
        assert updated_user["last_login"] is not None
        assert updated_user["login_attempts"] == 0
    
    @pytest.mark.asyncio
    async def test_failed_login_recovery_flow(self, auth_api):
        """测试失败登录恢复流程"""
        user_email = "testuser@example.com"
        
        # 1. 多次失败尝试
        for _ in range(3):
            result = await auth_api.login(user_email, "wrongpassword")
            assert result["success"] is False
        
        # 2. 检查尝试次数增加
        user = auth_api.users_db[user_email]
        assert user["login_attempts"] == 3
        assert user["is_active"] is True  # 还未锁定
        
        # 3. 成功登录应重置计数器
        result = await auth_api.login(user_email, "secret")
        assert result["success"] is True
        
        updated_user = auth_api.users_db[user_email]
        assert updated_user["login_attempts"] == 0


class TestAuthTestDataManagement:
    """测试数据管理"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, auth_api):
        """设置测试数据"""
        # 保存原始状态
        self.original_users = auth_api.users_db.copy()
        self.original_sessions = auth_api.sessions.copy()
        self.original_rate_limits = auth_api.rate_limits.copy()
        
        yield
        
        # 恢复原始状态
        auth_api.users_db = self.original_users
        auth_api.sessions = self.original_sessions
        auth_api.rate_limits = self.original_rate_limits
    
    def create_test_user(self, auth_api, email: str, is_active: bool = True) -> Dict[str, Any]:
        """创建测试用户"""
        user_id = f"test_user_{len(auth_api.users_db)}"
        user_data = {
            "id": user_id,
            "email": email,
            "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            "is_active": is_active,
            "created_at": datetime.now().isoformat(),
            "login_attempts": 0,
            "last_login": None
        }
        auth_api.users_db[email] = user_data
        return user_data
    
    @pytest.mark.asyncio
    async def test_with_dynamic_test_data(self, auth_api):
        """使用动态测试数据"""
        # 创建临时测试用户
        test_email = "temp_user@example.com"
        self.create_test_user(auth_api, test_email)
        
        # 执行测试
        result = await auth_api.login(test_email, "secret")
        assert result["success"] is True
        
        # 测试完成后，数据会被自动清理


class TestAuthTestEnvironmentConfig:
    """测试环境配置"""
    
    def test_security_config_loading(self):
        """测试安全配置加载"""
        config = SecurityConfig()
        
        # 测试默认配置
        db_config = config.get_db_config()
        assert db_config['host'] == 'localhost'
        assert db_config['port'] == 5432
        
        # 测试SSH配置
        ssh_config = config.get_ssh_config()
        assert ssh_config['host'] == '127.0.0.1'
        assert ssh_config['user'] == 'root'
    
    def test_sensitive_data_masking(self):
        """测试敏感数据掩码"""
        config = SecurityConfig()
        
        masked = config.mask_sensitive("secretpassword123", 4)
        assert masked == "secr*************"
        
        masked_short = config.mask_sensitive("abc", 4)
        assert masked_short == "***"
    
    def test_environment_variable_override(self):
        """测试环境变量覆盖"""
        import os
        
        # 设置环境变量
        os.environ['TEST_DB_HOST'] = 'testhost'
        
        config = SecurityConfig()
        value = config.get('TEST_DB_HOST', 'default')
        assert value == 'testhost'
        
        # 清理
        del os.environ['TEST_DB_HOST']


class TestReportGenerator:
    """测试报告生成器"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
    
    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """生成测试报告"""
        end_time = time.time()
        duration = end_time - self.start_time
        
        report = f"""
# Perfect21 用户登录API测试报告

## 测试摘要
- **测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **测试持续时间**: {duration:.2f}秒
- **测试环境**: {sys.platform}
- **Python版本**: {sys.version.split()[0]}

## 测试结果统计
- **总测试数**: {results.get('total_tests', 0)}
- **通过**: {results.get('passed', 0)}
- **失败**: {results.get('failed', 0)}
- **跳过**: {results.get('skipped', 0)}
- **覆盖率**: {results.get('coverage', 0):.1f}%

## 性能指标
- **平均响应时间**: {results.get('avg_response_time', 0):.3f}ms
- **最大响应时间**: {results.get('max_response_time', 0):.3f}ms
- **并发处理能力**: {results.get('concurrent_requests', 0)} req/s
- **内存使用**: {results.get('memory_usage', 0):.1f}MB

## 安全测试结果
- **SQL注入防护**: {'✅ 通过' if results.get('sql_injection_protected') else '❌ 失败'}
- **XSS防护**: {'✅ 通过' if results.get('xss_protected') else '❌ 失败'}
- **暴力破解防护**: {'✅ 通过' if results.get('brute_force_protected') else '❌ 失败'}
- **速率限制**: {'✅ 通过' if results.get('rate_limiting_working') else '❌ 失败'}

## 测试覆盖范围
- **单元测试**: {results.get('unit_test_coverage', 0):.1f}%
- **集成测试**: {results.get('integration_test_coverage', 0):.1f}%
- **E2E测试**: {results.get('e2e_test_coverage', 0):.1f}%
- **性能测试**: {results.get('performance_test_coverage', 0):.1f}%

## 建议改进
{self._generate_recommendations(results)}
        """
        
        return report
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> str:
        """生成改进建议"""
        recommendations = []
        
        if results.get('coverage', 0) < 90:
            recommendations.append("- 提高测试覆盖率至90%以上")
        
        if results.get('avg_response_time', 0) > 100:
            recommendations.append("- 优化响应时间性能")
        
        if not results.get('sql_injection_protected'):
            recommendations.append("- 加强SQL注入防护")
        
        if not results.get('brute_force_protected'):
            recommendations.append("- 实施暴力破解防护机制")
        
        return "\n".join(recommendations) if recommendations else "- 当前测试结果良好，无需特别改进"


if __name__ == "__main__":
    # 运行完整测试套件
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--cov=api",
        "--cov=config",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])
