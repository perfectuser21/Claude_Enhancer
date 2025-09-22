#!/usr/bin/env python3
"""
JWT Service Unit Tests
====================

测试JWT令牌管理服务的核心功能：
- 令牌生成和验证
- 令牌过期处理
- 令牌撤销机制
- 刷新令牌流程
- 安全性验证

作者: Claude Code AI Testing Team
版本: 1.0.0
创建时间: 2025-09-22
"""

import pytest
import jwt
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List


# 假设的JWT管理器类（基于之前看到的代码结构）
class JWTTokenManager:
    """JWT令牌管理器 - 用于测试"""

    def __init__(self, secret_key: str = "test-secret-key", algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.revoked_tokens = set()  # 简单的内存撤销列表

    def generate_token_pair(
        self,
        user_id: str,
        permissions: List[str] = None,
        device_info: Dict = None,
        ip_address: str = None,
        remember_me: bool = False,
    ) -> Dict[str, Any]:
        """生成JWT令牌对"""
        now = datetime.utcnow()
        access_exp = now + timedelta(hours=1)
        refresh_exp = now + timedelta(days=30 if remember_me else 7)

        # 访问令牌载荷
        access_payload = {
            "sub": user_id,
            "type": "access",
            "iat": now.timestamp(),
            "exp": access_exp.timestamp(),
            "permissions": permissions or [],
            "device_info": device_info or {},
            "ip_address": ip_address,
        }

        # 刷新令牌载荷
        refresh_payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": now.timestamp(),
            "exp": refresh_exp.timestamp(),
            "device_info": device_info or {},
            "ip_address": ip_address,
        }

        access_token = jwt.encode(
            access_payload, self.secret_key, algorithm=self.algorithm
        )
        refresh_token = jwt.encode(
            refresh_payload, self.secret_key, algorithm=self.algorithm
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 3600,
            "token_type": "Bearer",
        }

    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # 检查令牌类型
            if payload.get("type") != token_type:
                raise jwt.InvalidTokenError(f"Expected {token_type} token")

            # 检查是否被撤销
            if token in self.revoked_tokens:
                raise jwt.InvalidTokenError("Token has been revoked")

            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise e

    def refresh_token(
        self, refresh_token: str, client_ip: str = None, device_info: Dict = None
    ) -> Dict[str, Any]:
        """刷新访问令牌"""
        # 验证刷新令牌
        payload = self.verify_token(refresh_token, "refresh")
        user_id = payload["sub"]

        # 撤销旧的刷新令牌
        self.revoked_tokens.add(refresh_token)

        # 生成新的令牌对
        return self.generate_token_pair(
            user_id=user_id, device_info=device_info, ip_address=client_ip
        )

    def revoke_token(self, token: str, reason: str = None) -> bool:
        """撤销令牌"""
        self.revoked_tokens.add(token)
        return True

    def get_user_permissions(self, token: str) -> List[str]:
        """从令牌中获取用户权限"""
        payload = self.verify_token(token)
        return payload.get("permissions", [])


class TestJWTTokenManager:
    """JWT令牌管理器测试套件"""

    @pytest.fixture
    def jwt_manager(self):
        """创建JWT管理器实例"""
        return JWTTokenManager()

    @pytest.fixture
    def sample_user_data(self):
        """示例用户数据"""
        return {
            "user_id": "user_12345",
            "permissions": ["read:profile", "write:profile"],
            "device_info": {
                "device_type": "web",
                "browser": "Chrome",
                "os": "Windows 10",
            },
            "ip_address": "192.168.1.100",
        }

    def test_generate_token_pair_success(self, jwt_manager, sample_user_data):
        """测试成功生成令牌对"""
        # 执行
        result = jwt_manager.generate_token_pair(
            user_id=sample_user_data["user_id"],
            permissions=sample_user_data["permissions"],
            device_info=sample_user_data["device_info"],
            ip_address=sample_user_data["ip_address"],
        )

        # 验证
        assert "access_token" in result
        assert "refresh_token" in result
        assert "expires_in" in result
        assert "token_type" in result

        assert result["token_type"] == "Bearer"
        assert result["expires_in"] == 3600
        assert isinstance(result["access_token"], str)
        assert isinstance(result["refresh_token"], str)

    def test_generate_token_pair_remember_me(self, jwt_manager, sample_user_data):
        """测试记住我功能的令牌生成"""
        # 执行
        result = jwt_manager.generate_token_pair(
            user_id=sample_user_data["user_id"], remember_me=True
        )

        # 验证刷新令牌有更长的过期时间
        refresh_payload = jwt.decode(
            result["refresh_token"],
            jwt_manager.secret_key,
            algorithms=[jwt_manager.algorithm],
        )

        # 刷新令牌应该有30天的过期时间
        exp_time = datetime.fromtimestamp(refresh_payload["exp"])
        now = datetime.utcnow()
        time_diff = exp_time - now

        assert time_diff.days >= 29  # 至少29天（考虑执行时间）

    def test_verify_access_token_success(self, jwt_manager, sample_user_data):
        """测试成功验证访问令牌"""
        # 准备
        tokens = jwt_manager.generate_token_pair(
            user_id=sample_user_data["user_id"],
            permissions=sample_user_data["permissions"],
            device_info=sample_user_data["device_info"],
            ip_address=sample_user_data["ip_address"],
        )

        # 执行
        payload = jwt_manager.verify_token(tokens["access_token"], "access")

        # 验证
        assert payload["sub"] == sample_user_data["user_id"]
        assert payload["type"] == "access"
        assert payload["permissions"] == sample_user_data["permissions"]
        assert payload["device_info"] == sample_user_data["device_info"]
        assert payload["ip_address"] == sample_user_data["ip_address"]

    def test_verify_refresh_token_success(self, jwt_manager, sample_user_data):
        """测试成功验证刷新令牌"""
        # 准备
        tokens = jwt_manager.generate_token_pair(
            user_id=sample_user_data["user_id"],
            device_info=sample_user_data["device_info"],
            ip_address=sample_user_data["ip_address"],
        )

        # 执行
        payload = jwt_manager.verify_token(tokens["refresh_token"], "refresh")

        # 验证
        assert payload["sub"] == sample_user_data["user_id"]
        assert payload["type"] == "refresh"
        assert payload["device_info"] == sample_user_data["device_info"]
        assert payload["ip_address"] == sample_user_data["ip_address"]

    def test_verify_token_wrong_type(self, jwt_manager, sample_user_data):
        """测试使用错误类型验证令牌"""
        # 准备
        tokens = jwt_manager.generate_token_pair(user_id=sample_user_data["user_id"])

        # 执行 & 验证
        with pytest.raises(jwt.InvalidTokenError, match="Expected refresh token"):
            jwt_manager.verify_token(tokens["access_token"], "refresh")

        with pytest.raises(jwt.InvalidTokenError, match="Expected access token"):
            jwt_manager.verify_token(tokens["refresh_token"], "access")

    def test_verify_expired_token(self, jwt_manager, sample_user_data):
        """测试验证过期令牌"""
        # 准备 - 创建已过期的令牌
        past_time = datetime.utcnow() - timedelta(hours=2)
        expired_payload = {
            "sub": sample_user_data["user_id"],
            "type": "access",
            "iat": past_time.timestamp(),
            "exp": (past_time + timedelta(hours=1)).timestamp(),
        }

        expired_token = jwt.encode(
            expired_payload, jwt_manager.secret_key, algorithm=jwt_manager.algorithm
        )

        # 执行 & 验证
        with pytest.raises(jwt.InvalidTokenError, match="Token has expired"):
            jwt_manager.verify_token(expired_token)

    def test_verify_invalid_token(self, jwt_manager):
        """测试验证无效令牌"""
        invalid_tokens = [
            "invalid.token.format",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature",
            "",
            "not-a-jwt-token",
        ]

        for invalid_token in invalid_tokens:
            with pytest.raises(jwt.InvalidTokenError):
                jwt_manager.verify_token(invalid_token)

    def test_verify_revoked_token(self, jwt_manager, sample_user_data):
        """测试验证已撤销令牌"""
        # 准备
        tokens = jwt_manager.generate_token_pair(user_id=sample_user_data["user_id"])
        access_token = tokens["access_token"]

        # 撤销令牌
        jwt_manager.revoke_token(access_token)

        # 执行 & 验证
        with pytest.raises(jwt.InvalidTokenError, match="Token has been revoked"):
            jwt_manager.verify_token(access_token)

    def test_refresh_token_success(self, jwt_manager, sample_user_data):
        """测试成功刷新令牌"""
        # 准备
        original_tokens = jwt_manager.generate_token_pair(
            user_id=sample_user_data["user_id"]
        )

        # 执行
        new_tokens = jwt_manager.refresh_token(
            refresh_token=original_tokens["refresh_token"], client_ip="192.168.1.200"
        )

        # 验证
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["access_token"] != original_tokens["access_token"]
        assert new_tokens["refresh_token"] != original_tokens["refresh_token"]

        # 验证新的访问令牌有效
        new_payload = jwt_manager.verify_token(new_tokens["access_token"])
        assert new_payload["sub"] == sample_user_data["user_id"]

        # 验证旧的刷新令牌已被撤销
        with pytest.raises(jwt.InvalidTokenError, match="Token has been revoked"):
            jwt_manager.verify_token(original_tokens["refresh_token"], "refresh")

    def test_refresh_token_with_invalid_refresh_token(self, jwt_manager):
        """测试使用无效刷新令牌刷新"""
        invalid_tokens = [
            "invalid.refresh.token",
            "",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature",
        ]

        for invalid_token in invalid_tokens:
            with pytest.raises(jwt.InvalidTokenError):
                jwt_manager.refresh_token(invalid_token)

    def test_refresh_token_with_access_token(self, jwt_manager, sample_user_data):
        """测试使用访问令牌进行刷新（应该失败）"""
        # 准备
        tokens = jwt_manager.generate_token_pair(user_id=sample_user_data["user_id"])

        # 执行 & 验证
        with pytest.raises(jwt.InvalidTokenError, match="Expected refresh token"):
            jwt_manager.refresh_token(tokens["access_token"])

    def test_revoke_token_success(self, jwt_manager, sample_user_data):
        """测试成功撤销令牌"""
        # 准备
        tokens = jwt_manager.generate_token_pair(user_id=sample_user_data["user_id"])
        access_token = tokens["access_token"]

        # 验证令牌initially有效
        payload = jwt_manager.verify_token(access_token)
        assert payload["sub"] == sample_user_data["user_id"]

        # 执行撤销
        result = jwt_manager.revoke_token(access_token, "user_logout")
        assert result is True

        # 验证令牌已被撤销
        with pytest.raises(jwt.InvalidTokenError, match="Token has been revoked"):
            jwt_manager.verify_token(access_token)

    def test_get_user_permissions_success(self, jwt_manager, sample_user_data):
        """测试获取用户权限"""
        # 准备
        tokens = jwt_manager.generate_token_pair(
            user_id=sample_user_data["user_id"],
            permissions=sample_user_data["permissions"],
        )

        # 执行
        permissions = jwt_manager.get_user_permissions(tokens["access_token"])

        # 验证
        assert permissions == sample_user_data["permissions"]

    def test_get_user_permissions_no_permissions(self, jwt_manager, sample_user_data):
        """测试获取没有权限的用户权限"""
        # 准备
        tokens = jwt_manager.generate_token_pair(user_id=sample_user_data["user_id"])

        # 执行
        permissions = jwt_manager.get_user_permissions(tokens["access_token"])

        # 验证
        assert permissions == []

    def test_get_user_permissions_invalid_token(self, jwt_manager):
        """测试使用无效令牌获取权限"""
        with pytest.raises(jwt.InvalidTokenError):
            jwt_manager.get_user_permissions("invalid.token")

    def test_token_payload_structure(self, jwt_manager, sample_user_data):
        """测试令牌载荷结构"""
        # 执行
        tokens = jwt_manager.generate_token_pair(
            user_id=sample_user_data["user_id"],
            permissions=sample_user_data["permissions"],
            device_info=sample_user_data["device_info"],
            ip_address=sample_user_data["ip_address"],
        )

        # 验证访问令牌载荷
        access_payload = jwt.decode(
            tokens["access_token"],
            jwt_manager.secret_key,
            algorithms=[jwt_manager.algorithm],
        )

        required_fields = [
            "sub",
            "type",
            "iat",
            "exp",
            "permissions",
            "device_info",
            "ip_address",
        ]
        for field in required_fields:
            assert field in access_payload

        assert access_payload["type"] == "access"

        # 验证刷新令牌载荷
        refresh_payload = jwt.decode(
            tokens["refresh_token"],
            jwt_manager.secret_key,
            algorithms=[jwt_manager.algorithm],
        )

        required_refresh_fields = [
            "sub",
            "type",
            "iat",
            "exp",
            "device_info",
            "ip_address",
        ]
        for field in required_refresh_fields:
            assert field in refresh_payload

        assert refresh_payload["type"] == "refresh"

    def test_concurrent_token_operations(self, jwt_manager, sample_user_data):
        """测试并发令牌操作"""
        import threading
        import time

        results = []
        errors = []

        def generate_and_verify():
            try:
                tokens = jwt_manager.generate_token_pair(
                    user_id=f"user_{threading.current_thread().ident}"
                )
                payload = jwt_manager.verify_token(tokens["access_token"])
                results.append(payload["sub"])
            except Exception as e:
                errors.append(str(e))

        # 创建多个线程
        threads = []
        for i in range(10):
            thread = threading.Thread(target=generate_and_verify)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        assert len(set(results)) == 10  # 所有用户ID应该不同

    def test_token_timing_attacks_resistance(self, jwt_manager):
        """测试令牌时序攻击抵抗性"""
        # 生成有效令牌
        tokens = jwt_manager.generate_token_pair(user_id="user_123")
        valid_token = tokens["access_token"]

        # 生成多个无效令牌
        invalid_tokens = [
            "invalid.token.1",
            "invalid.token.2",
            "invalid.token.3",
            valid_token + "modified",
            valid_token[:-5] + "xxxxx",
        ]

        # 测量验证时间
        times = []

        for token in invalid_tokens:
            start_time = time.time()
            try:
                jwt_manager.verify_token(token)
            except jwt.InvalidTokenError:
                pass
            end_time = time.time()
            times.append(end_time - start_time)

        # 验证时间差异不会太大（简单的时序攻击检测）
        if len(times) > 1:
            max_time = max(times)
            min_time = min(times)
            # 时间差异不应该超过10倍（这是一个简单的阈值）
            assert max_time / min_time < 10, "Potential timing attack vulnerability"


# 额外的集成测试
class TestJWTIntegration:
    """JWT集成测试"""

    @pytest.fixture
    def jwt_manager(self):
        return JWTTokenManager()

    def test_complete_authentication_flow(self, jwt_manager):
        """测试完整的认证流程"""
        user_id = "integration_user_123"
        permissions = ["read:data", "write:data"]

        # 1. 生成初始令牌对
        tokens = jwt_manager.generate_token_pair(
            user_id=user_id, permissions=permissions
        )

        # 2. 验证访问令牌
        access_payload = jwt_manager.verify_token(tokens["access_token"])
        assert access_payload["sub"] == user_id
        assert access_payload["permissions"] == permissions

        # 3. 使用刷新令牌获取新的令牌对
        new_tokens = jwt_manager.refresh_token(tokens["refresh_token"])

        # 4. 验证新的访问令牌
        new_access_payload = jwt_manager.verify_token(new_tokens["access_token"])
        assert new_access_payload["sub"] == user_id

        # 5. 撤销新的访问令牌
        jwt_manager.revoke_token(new_tokens["access_token"])

        # 6. 验证令牌已被撤销
        with pytest.raises(jwt.InvalidTokenError):
            jwt_manager.verify_token(new_tokens["access_token"])

    def test_token_lifecycle_management(self, jwt_manager):
        """测试令牌生命周期管理"""
        user_id = "lifecycle_user_456"

        # 生成多个令牌对
        token_pairs = []
        for i in range(3):
            tokens = jwt_manager.generate_token_pair(user_id=f"{user_id}_{i}")
            token_pairs.append(tokens)

        # 验证所有令牌都有效
        for tokens in token_pairs:
            payload = jwt_manager.verify_token(tokens["access_token"])
            assert payload["type"] == "access"

        # 撤销第一个和第三个令牌
        jwt_manager.revoke_token(token_pairs[0]["access_token"])
        jwt_manager.revoke_token(token_pairs[2]["access_token"])

        # 验证撤销状态
        with pytest.raises(jwt.InvalidTokenError):
            jwt_manager.verify_token(token_pairs[0]["access_token"])

        # 第二个令牌应该仍然有效
        payload = jwt_manager.verify_token(token_pairs[1]["access_token"])
        assert payload["type"] == "access"

        with pytest.raises(jwt.InvalidTokenError):
            jwt_manager.verify_token(token_pairs[2]["access_token"])


if __name__ == "__main__":
    # 运行测试
    pytest.main(["-v", __file__])
