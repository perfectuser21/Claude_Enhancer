#!/usr/bin/env python3
"""
Session Management Unit Tests
============================

测试会话管理系统的所有核心功能：
- 会话创建和验证
- 会话过期处理
- 刷新令牌管理
- 会话撤销机制
- 设备指纹管理
- 安全特性测试

作者: Claude Code AI Testing Team
版本: 1.0.0
创建时间: 2025-09-22
"""

import pytest
import asyncio
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, Optional, List, Tuple
import uuid
from enum import Enum


# 会话状态枚举
class SessionStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALID = "invalid"


# 设备类型枚举
class DeviceType(Enum):
    WEB = "web"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    API = "api"
    UNKNOWN = "unknown"


class Session:
    """会话模型模拟"""

    def __init__(
        self,
        id: str = None,
        user_id: str = None,
        session_id: str = None,
        token_hash: str = None,
        status: SessionStatus = SessionStatus.ACTIVE,
        expires_at: datetime = None,
        last_activity_at: datetime = None,
        device_type: DeviceType = DeviceType.UNKNOWN,
        device_id: str = None,
        device_name: str = None,
        user_agent: str = None,
        ip_address: str = None,
        csrf_token: str = None,
        is_trusted_device: bool = False,
        risk_score: int = 0,
        metadata: Dict = None,
        **kwargs,
    ):
        self.id = id or str(uuid.uuid4())
        self.user_id = user_id
        self.session_id = session_id or self.generate_session_id()
        self.token_hash = token_hash
        self.status = status
        self.expires_at = expires_at or (datetime.utcnow() + timedelta(hours=1))
        self.last_activity_at = last_activity_at or datetime.utcnow()
        self.device_type = device_type
        self.device_id = device_id
        self.device_name = device_name
        self.user_agent = user_agent
        self.ip_address = ip_address
        self.csrf_token = csrf_token
        self.is_trusted_device = is_trusted_device
        self.risk_score = risk_score
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.is_deleted = False

        # 额外属性
        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    def generate_session_id() -> str:
        """生成会话 ID"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_token_hash(token: str) -> str:
        """生成令牌哈希"""
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def create_session(
        cls,
        user_id: str,
        token: str,
        expires_in_seconds: int = 3600,
        device_type: DeviceType = DeviceType.UNKNOWN,
        ip_address: str = None,
        user_agent: str = None,
        **kwargs,
    ) -> "Session":
        """创建新会话"""
        now = datetime.utcnow()

        session = cls(
            user_id=user_id,
            session_id=cls.generate_session_id(),
            token_hash=cls.generate_token_hash(token),
            status=SessionStatus.ACTIVE,
            expires_at=now + timedelta(seconds=expires_in_seconds),
            last_activity_at=now,
            device_type=device_type,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs,
        )

        return session

    def verify_token(self, token: str) -> bool:
        """验证令牌"""
        return self.token_hash == self.generate_token_hash(token)

    @property
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_active(self) -> bool:
        """检查会话是否活跃"""
        return (
            self.status == SessionStatus.ACTIVE
            and not self.is_expired
            and not self.is_deleted
        )

    def extend_session(self, seconds: int = 3600) -> None:
        """延长会话有效期"""
        if self.is_active:
            self.expires_at = datetime.utcnow() + timedelta(seconds=seconds)
            self.last_activity_at = datetime.utcnow()

    def revoke(self, reason: str = None) -> None:
        """撤销会话"""
        self.status = SessionStatus.REVOKED
        if reason:
            self.metadata["revocation_reason"] = reason

    def update_activity(self, ip_address: str = None) -> None:
        """更新活动时间"""
        self.last_activity_at = datetime.utcnow()
        if ip_address:
            self.ip_address = ip_address


class RefreshToken:
    """刷新令牌模型模拟"""

    def __init__(
        self,
        id: str = None,
        session_id: str = None,
        token_hash: str = None,
        token_family: str = None,
        expires_at: datetime = None,
        used_count: int = 0,
        max_uses: int = 1,
        last_used_at: datetime = None,
        is_revoked: bool = False,
        **kwargs,
    ):
        self.id = id or str(uuid.uuid4())
        self.session_id = session_id
        self.token_hash = token_hash
        self.token_family = token_family or secrets.token_urlsafe(16)
        self.expires_at = expires_at or (datetime.utcnow() + timedelta(days=30))
        self.used_count = used_count
        self.max_uses = max_uses
        self.last_used_at = last_used_at
        self.is_revoked = is_revoked
        self.created_at = datetime.utcnow()
        self.is_deleted = False

        # 额外属性
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def create_refresh_token(
        cls, session_id: str, token: str, expires_in_days: int = 30, max_uses: int = 1
    ) -> "RefreshToken":
        """创建刷新令牌"""
        return cls(
            session_id=session_id,
            token_hash=Session.generate_token_hash(token),
            token_family=secrets.token_urlsafe(16),
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            max_uses=max_uses,
        )

    def verify_token(self, token: str) -> bool:
        """验证刷新令牌"""
        return self.token_hash == Session.generate_token_hash(token)

    @property
    def is_valid(self) -> bool:
        """检查令牌是否有效"""
        return (
            not self.is_revoked
            and not self.is_deleted
            and datetime.utcnow() < self.expires_at
            and self.used_count < self.max_uses
        )

    def use_token(self) -> bool:
        """使用令牌"""
        if not self.is_valid:
            return False

        self.used_count += 1
        self.last_used_at = datetime.utcnow()

        # 如果达到最大使用次数，标记为已撤销
        if self.used_count >= self.max_uses:
            self.is_revoked = True

        return True


class SessionManager:
    """会话管理器模拟"""

    def __init__(self):
        self.sessions = {}  # session_id -> Session
        self.refresh_tokens = {}  # token_hash -> RefreshToken
        self.user_sessions = {}  # user_id -> [session_ids]
        self.device_fingerprints = {}  # device_fingerprint -> device_info

    async def create_session(
        self,
        user_id: str,
        token: str,
        device_info: Dict = None,
        ip_address: str = None,
        user_agent: str = None,
        expires_in_seconds: int = 3600,
        **kwargs,
    ) -> Session:
        """创建新会话"""
        # 创建会话
        session = Session.create_session(
            user_id=user_id,
            token=token,
            expires_in_seconds=expires_in_seconds,
            device_type=device_info.get("device_type", DeviceType.UNKNOWN)
            if device_info
            else DeviceType.UNKNOWN,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs,
        )

        # 存储会话
        self.sessions[session.session_id] = session

        # 更新用户会话列表
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session.session_id)

        # 处理设备指纹
        if device_info and "device_fingerprint" in device_info:
            self.device_fingerprints[device_info["device_fingerprint"]] = {
                "device_info": device_info,
                "created_at": datetime.utcnow(),
                "session_id": session.session_id,
            }

        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self.sessions.get(session_id)

    async def verify_session(self, session_id: str, token: str) -> Optional[Session]:
        """验证会话"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        if not session.is_active:
            return None

        if not session.verify_token(token):
            return None

        # 更新活动时间
        session.update_activity()

        return session

    async def extend_session(self, session_id: str, seconds: int = 3600) -> bool:
        """延长会话有效期"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        session.extend_session(seconds)
        return True

    async def revoke_session(self, session_id: str, reason: str = None) -> bool:
        """撤销会话"""
        session = self.sessions.get(session_id)
        if not session:
            return False

        session.revoke(reason)
        return True

    async def revoke_all_user_sessions(self, user_id: str, reason: str = None) -> int:
        """撤销用户所有会话"""
        if user_id not in self.user_sessions:
            return 0

        revoked_count = 0
        for session_id in self.user_sessions[user_id]:
            session = self.sessions.get(session_id)
            if session and session.is_active:
                session.revoke(reason)
                revoked_count += 1

        return revoked_count

    async def get_user_sessions(
        self, user_id: str, active_only: bool = True
    ) -> List[Session]:
        """获取用户所有会话"""
        if user_id not in self.user_sessions:
            return []

        sessions = []
        for session_id in self.user_sessions[user_id]:
            session = self.sessions.get(session_id)
            if session:
                if not active_only or session.is_active:
                    sessions.append(session)

        return sessions

    async def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        expired_count = 0

        for session_id, session in list(self.sessions.items()):
            if session.is_expired and session.status == SessionStatus.ACTIVE:
                session.status = SessionStatus.EXPIRED
                expired_count += 1

        return expired_count

    async def create_refresh_token(
        self, session_id: str, token: str, expires_in_days: int = 30, max_uses: int = 1
    ) -> RefreshToken:
        """创建刷新令牌"""
        refresh_token = RefreshToken.create_refresh_token(
            session_id=session_id,
            token=token,
            expires_in_days=expires_in_days,
            max_uses=max_uses,
        )

        self.refresh_tokens[refresh_token.token_hash] = refresh_token

        return refresh_token

    async def verify_refresh_token(self, token: str) -> Optional[RefreshToken]:
        """验证刷新令牌"""
        token_hash = Session.generate_token_hash(token)
        refresh_token = self.refresh_tokens.get(token_hash)

        if not refresh_token or not refresh_token.is_valid:
            return None

        return refresh_token

    async def use_refresh_token(self, token: str) -> Optional[Session]:
        """使用刷新令牌"""
        refresh_token = await self.verify_refresh_token(token)
        if not refresh_token:
            return None

        # 使用令牌
        if not refresh_token.use_token():
            return None

        # 获取关联的会话
        session = self.sessions.get(refresh_token.session_id)
        return session

    async def revoke_refresh_token(self, token: str) -> bool:
        """撤销刷新令牌"""
        token_hash = Session.generate_token_hash(token)
        refresh_token = self.refresh_tokens.get(token_hash)

        if not refresh_token:
            return False

        refresh_token.is_revoked = True
        return True

    async def get_session_by_device_fingerprint(
        self, device_fingerprint: str
    ) -> Optional[Session]:
        """根据设备指纹获取会话"""
        device_data = self.device_fingerprints.get(device_fingerprint)
        if not device_data:
            return None

        session_id = device_data["session_id"]
        return self.sessions.get(session_id)

    async def get_session_statistics(self, user_id: str = None) -> Dict[str, Any]:
        """获取会话统计信息"""
        if user_id:
            sessions = await self.get_user_sessions(user_id, active_only=False)
        else:
            sessions = list(self.sessions.values())

        stats = {
            "total_sessions": len(sessions),
            "active_sessions": len([s for s in sessions if s.is_active]),
            "expired_sessions": len([s for s in sessions if s.is_expired]),
            "revoked_sessions": len(
                [s for s in sessions if s.status == SessionStatus.REVOKED]
            ),
            "device_types": {},
            "average_session_duration": 0,
        }

        # 设备类型统计
        for session in sessions:
            device_type = session.device_type.value
            stats["device_types"][device_type] = (
                stats["device_types"].get(device_type, 0) + 1
            )

        # 平均会话时长（简化计算）
        if sessions:
            total_duration = sum(
                (s.last_activity_at - s.created_at).total_seconds()
                for s in sessions
                if s.last_activity_at
            )
            stats["average_session_duration"] = total_duration / len(sessions)

        return stats


class TestSessionCreation:
    """会话创建测试套件"""

    @pytest.fixture
    def session_manager(self):
        return SessionManager()

    @pytest.fixture
    def user_id(self):
        return "user_123"

    @pytest.fixture
    def device_info(self):
        return {
            "device_type": DeviceType.WEB,
            "device_fingerprint": "fp_abc123",
            "browser": "Chrome",
            "os": "Windows 10",
        }

    @pytest.mark.asyncio
    async def test_create_session_success(self, session_manager, user_id, device_info):
        """测试成功创建会话"""
        token = "test_session_token"
        ip_address = "192.168.1.100"
        user_agent = "Mozilla/5.0 Test"

        # 创建会话
        session = await session_manager.create_session(
            user_id=user_id,
            token=token,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # 验证会话属性
        assert session.user_id == user_id
        assert session.device_type == DeviceType.WEB
        assert session.ip_address == ip_address
        assert session.user_agent == user_agent
        assert session.status == SessionStatus.ACTIVE
        assert session.is_active
        assert session.verify_token(token)

        # 验证会话被存储
        assert session.session_id in session_manager.sessions
        assert user_id in session_manager.user_sessions
        assert session.session_id in session_manager.user_sessions[user_id]

    @pytest.mark.asyncio
    async def test_create_session_with_custom_expiry(self, session_manager, user_id):
        """测试创建带自定义过期时间的会话"""
        token = "test_token"
        expires_in_seconds = 7200  # 2小时

        session = await session_manager.create_session(
            user_id=user_id, token=token, expires_in_seconds=expires_in_seconds
        )

        # 检查过期时间
        expected_expiry = datetime.utcnow() + timedelta(seconds=expires_in_seconds)
        time_diff = abs((session.expires_at - expected_expiry).total_seconds())
        assert time_diff < 5  # 允许5秒误差

    @pytest.mark.asyncio
    async def test_create_multiple_sessions_same_user(self, session_manager, user_id):
        """测试同一用户创建多个会话"""
        sessions = []
        for i in range(3):
            session = await session_manager.create_session(
                user_id=user_id,
                token=f"token_{i}",
                device_info={"device_type": DeviceType.WEB},
            )
            sessions.append(session)

        # 验证所有会话都被创建
        assert len(sessions) == 3
        assert len(session_manager.user_sessions[user_id]) == 3

        # 验证每个会话都有唯一ID
        session_ids = [s.session_id for s in sessions]
        assert len(set(session_ids)) == 3

    @pytest.mark.asyncio
    async def test_create_session_with_device_fingerprint(
        self, session_manager, user_id, device_info
    ):
        """测试创建带设备指纹的会话"""
        token = "fingerprint_token"
        device_fingerprint = device_info["device_fingerprint"]

        session = await session_manager.create_session(
            user_id=user_id, token=token, device_info=device_info
        )

        # 验证设备指纹被存储
        assert device_fingerprint in session_manager.device_fingerprints

        device_data = session_manager.device_fingerprints[device_fingerprint]
        assert device_data["session_id"] == session.session_id
        assert device_data["device_info"] == device_info

    @pytest.mark.asyncio
    async def test_session_id_uniqueness(self, session_manager):
        """测试会话 ID 唯一性"""
        session_ids = set()

        # 创建100个会话
        for i in range(100):
            session = await session_manager.create_session(
                user_id=f"user_{i}", token=f"token_{i}"
            )
            session_ids.add(session.session_id)

        # 所有ID应该都不同
        assert len(session_ids) == 100


class TestSessionVerification:
    """会话验证测试套件"""

    @pytest.fixture
    def session_manager(self):
        return SessionManager()

    @pytest.fixture
    async def active_session(self, session_manager):
        return await session_manager.create_session(
            user_id="test_user", token="test_token"
        )

    @pytest.mark.asyncio
    async def test_verify_session_success(self, session_manager, active_session):
        """测试成功验证会话"""
        # 验证会话
        verified_session = await session_manager.verify_session(
            session_id=active_session.session_id, token="test_token"
        )

        # 验证结果
        assert verified_session is not None
        assert verified_session.id == active_session.id
        assert verified_session.user_id == active_session.user_id

    @pytest.mark.asyncio
    async def test_verify_session_wrong_token(self, session_manager, active_session):
        """测试使用错误令牌验证"""
        verified_session = await session_manager.verify_session(
            session_id=active_session.session_id, token="wrong_token"
        )

        assert verified_session is None

    @pytest.mark.asyncio
    async def test_verify_session_nonexistent(self, session_manager):
        """测试验证不存在的会话"""
        verified_session = await session_manager.verify_session(
            session_id="nonexistent_session", token="any_token"
        )

        assert verified_session is None

    @pytest.mark.asyncio
    async def test_verify_expired_session(self, session_manager):
        """测试验证过期会话"""
        # 创建一个已过期的会话
        expired_session = await session_manager.create_session(
            user_id="test_user",
            token="expired_token",
            expires_in_seconds=-3600,  # 过去的时间
        )

        # 尝试验证
        verified_session = await session_manager.verify_session(
            session_id=expired_session.session_id, token="expired_token"
        )

        assert verified_session is None

    @pytest.mark.asyncio
    async def test_verify_revoked_session(self, session_manager, active_session):
        """测试验证已撤销的会话"""
        # 撤销会话
        await session_manager.revoke_session(
            active_session.session_id, "test_revocation"
        )

        # 尝试验证
        verified_session = await session_manager.verify_session(
            session_id=active_session.session_id, token="test_token"
        )

        assert verified_session is None

    @pytest.mark.asyncio
    async def test_verify_session_updates_activity(
        self, session_manager, active_session
    ):
        """测试验证会话时更新活动时间"""
        original_activity = active_session.last_activity_at

        # 等待一小段时间
        await asyncio.sleep(0.1)

        # 验证会话
        verified_session = await session_manager.verify_session(
            session_id=active_session.session_id, token="test_token"
        )

        # 检查活动时间是否更新
        assert verified_session.last_activity_at > original_activity


class TestSessionExtension:
    """会话延长测试套件"""

    @pytest.fixture
    def session_manager(self):
        return SessionManager()

    @pytest.fixture
    async def active_session(self, session_manager):
        return await session_manager.create_session(
            user_id="test_user", token="test_token"
        )

    @pytest.mark.asyncio
    async def test_extend_session_success(self, session_manager, active_session):
        """测试成功延长会话"""
        original_expiry = active_session.expires_at
        extension_seconds = 3600

        # 延长会话
        result = await session_manager.extend_session(
            session_id=active_session.session_id, seconds=extension_seconds
        )

        # 验证结果
        assert result is True
        assert active_session.expires_at > original_expiry

        # 检查延长时间
        expected_expiry = datetime.utcnow() + timedelta(seconds=extension_seconds)
        time_diff = abs((active_session.expires_at - expected_expiry).total_seconds())
        assert time_diff < 5  # 允许5秒误差

    @pytest.mark.asyncio
    async def test_extend_nonexistent_session(self, session_manager):
        """测试延长不存在的会话"""
        result = await session_manager.extend_session(
            session_id="nonexistent_session", seconds=3600
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_extend_session_updates_activity(
        self, session_manager, active_session
    ):
        """测试延长会话时更新活动时间"""
        original_activity = active_session.last_activity_at

        await asyncio.sleep(0.1)

        # 延长会话
        await session_manager.extend_session(
            session_id=active_session.session_id, seconds=3600
        )

        # 检查活动时间是否更新
        assert active_session.last_activity_at > original_activity


class TestSessionRevocation:
    """会话撤销测试套件"""

    @pytest.fixture
    def session_manager(self):
        return SessionManager()

    @pytest.fixture
    async def active_session(self, session_manager):
        return await session_manager.create_session(
            user_id="test_user", token="test_token"
        )

    @pytest.mark.asyncio
    async def test_revoke_session_success(self, session_manager, active_session):
        """测试成功撤销会话"""
        reason = "user_logout"

        # 撤销会话
        result = await session_manager.revoke_session(
            session_id=active_session.session_id, reason=reason
        )

        # 验证结果
        assert result is True
        assert active_session.status == SessionStatus.REVOKED
        assert not active_session.is_active
        assert active_session.metadata.get("revocation_reason") == reason

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_session(self, session_manager):
        """测试撤销不存在的会话"""
        result = await session_manager.revoke_session(
            session_id="nonexistent_session", reason="test"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_revoke_all_user_sessions(self, session_manager):
        """测试撤销用户所有会话"""
        user_id = "multi_session_user"
        sessions = []

        # 创建多个会话
        for i in range(3):
            session = await session_manager.create_session(
                user_id=user_id, token=f"token_{i}"
            )
            sessions.append(session)

        # 撤销所有会话
        revoked_count = await session_manager.revoke_all_user_sessions(
            user_id=user_id, reason="security_incident"
        )

        # 验证结果
        assert revoked_count == 3
        for session in sessions:
            assert session.status == SessionStatus.REVOKED
            assert not session.is_active

    @pytest.mark.asyncio
    async def test_revoke_all_sessions_nonexistent_user(self, session_manager):
        """测试撤销不存在用户的会话"""
        revoked_count = await session_manager.revoke_all_user_sessions(
            user_id="nonexistent_user", reason="test"
        )

        assert revoked_count == 0


class TestRefreshTokenManagement:
    """刷新令牌管理测试套件"""

    @pytest.fixture
    def session_manager(self):
        return SessionManager()

    @pytest.fixture
    async def active_session(self, session_manager):
        return await session_manager.create_session(
            user_id="test_user", token="test_token"
        )

    @pytest.mark.asyncio
    async def test_create_refresh_token(self, session_manager, active_session):
        """测试创建刷新令牌"""
        refresh_token_value = "refresh_token_123"

        # 创建刷新令牌
        refresh_token = await session_manager.create_refresh_token(
            session_id=active_session.session_id,
            token=refresh_token_value,
            expires_in_days=30,
            max_uses=1,
        )

        # 验证属性
        assert refresh_token.session_id == active_session.session_id
        assert refresh_token.verify_token(refresh_token_value)
        assert refresh_token.is_valid
        assert refresh_token.max_uses == 1
        assert refresh_token.used_count == 0

        # 验证存储
        token_hash = Session.generate_token_hash(refresh_token_value)
        assert token_hash in session_manager.refresh_tokens

    @pytest.mark.asyncio
    async def test_verify_refresh_token_success(self, session_manager, active_session):
        """测试成功验证刷新令牌"""
        refresh_token_value = "valid_refresh_token"

        # 创建刷新令牌
        await session_manager.create_refresh_token(
            session_id=active_session.session_id, token=refresh_token_value
        )

        # 验证刷新令牌
        verified_token = await session_manager.verify_refresh_token(refresh_token_value)

        assert verified_token is not None
        assert verified_token.session_id == active_session.session_id
        assert verified_token.is_valid

    @pytest.mark.asyncio
    async def test_verify_refresh_token_invalid(self, session_manager):
        """测试验证无效刷新令牌"""
        # 验证不存在的令牌
        verified_token = await session_manager.verify_refresh_token("nonexistent_token")
        assert verified_token is None

    @pytest.mark.asyncio
    async def test_use_refresh_token_success(self, session_manager, active_session):
        """测试成功使用刷新令牌"""
        refresh_token_value = "usable_refresh_token"

        # 创建刷新令牌
        refresh_token = await session_manager.create_refresh_token(
            session_id=active_session.session_id, token=refresh_token_value, max_uses=1
        )

        # 使用刷新令牌
        session = await session_manager.use_refresh_token(refresh_token_value)

        # 验证结果
        assert session is not None
        assert session.session_id == active_session.session_id

        # 检查令牌状态
        assert refresh_token.used_count == 1
        assert refresh_token.is_revoked  # 达到最大使用次数后应该被撤销
        assert not refresh_token.is_valid

    @pytest.mark.asyncio
    async def test_use_refresh_token_multiple_times(
        self, session_manager, active_session
    ):
        """测试多次使用刷新令牌"""
        refresh_token_value = "multi_use_token"

        # 创建允许多次使用的刷新令牌
        refresh_token = await session_manager.create_refresh_token(
            session_id=active_session.session_id, token=refresh_token_value, max_uses=3
        )

        # 使用两次
        for i in range(2):
            session = await session_manager.use_refresh_token(refresh_token_value)
            assert session is not None
            assert refresh_token.used_count == i + 1
            assert not refresh_token.is_revoked

        # 第三次使用后应该被撤销
        session = await session_manager.use_refresh_token(refresh_token_value)
        assert session is not None
        assert refresh_token.used_count == 3
        assert refresh_token.is_revoked

        # 第四次使用应该失败
        session = await session_manager.use_refresh_token(refresh_token_value)
        assert session is None

    @pytest.mark.asyncio
    async def test_revoke_refresh_token(self, session_manager, active_session):
        """测试撤销刷新令牌"""
        refresh_token_value = "revokable_token"

        # 创建刷新令牌
        refresh_token = await session_manager.create_refresh_token(
            session_id=active_session.session_id, token=refresh_token_value
        )

        # 撤销令牌
        result = await session_manager.revoke_refresh_token(refresh_token_value)

        # 验证结果
        assert result is True
        assert refresh_token.is_revoked
        assert not refresh_token.is_valid

        # 尝试使用已撤销的令牌
        session = await session_manager.use_refresh_token(refresh_token_value)
        assert session is None

    @pytest.mark.asyncio
    async def test_refresh_token_expiration(self, session_manager, active_session):
        """测试刷新令牌过期"""
        refresh_token_value = "expiring_token"

        # 创建已过期的刷新令牌
        refresh_token = await session_manager.create_refresh_token(
            session_id=active_session.session_id,
            token=refresh_token_value,
            expires_in_days=-1,  # 过去的时间
        )

        # 尝试验证过期令牌
        verified_token = await session_manager.verify_refresh_token(refresh_token_value)
        assert verified_token is None

        # 尝试使用过期令牌
        session = await session_manager.use_refresh_token(refresh_token_value)
        assert session is None


class TestSessionCleanup:
    """会话清理测试套件"""

    @pytest.fixture
    def session_manager(self):
        return SessionManager()

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, session_manager):
        """测试清理过期会话"""
        # 创建正常会话
        active_session = await session_manager.create_session(
            user_id="active_user", token="active_token"
        )

        # 创建过期会话
        expired_session = await session_manager.create_session(
            user_id="expired_user",
            token="expired_token",
            expires_in_seconds=-3600,  # 过去的时间
        )

        # 执行清理
        cleaned_count = await session_manager.cleanup_expired_sessions()

        # 验证结果
        assert cleaned_count == 1
        assert active_session.status == SessionStatus.ACTIVE
        assert expired_session.status == SessionStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_cleanup_no_expired_sessions(self, session_manager):
        """测试没有过期会话时的清理"""
        # 创建多个活跃会话
        for i in range(3):
            await session_manager.create_session(
                user_id=f"user_{i}", token=f"token_{i}"
            )

        # 执行清理
        cleaned_count = await session_manager.cleanup_expired_sessions()

        # 不应该有任何会话被清理
        assert cleaned_count == 0


class TestDeviceFingerprintManagement:
    """设备指纹管理测试套件"""

    @pytest.fixture
    def session_manager(self):
        return SessionManager()

    @pytest.fixture
    def device_info(self):
        return {
            "device_fingerprint": "unique_device_123",
            "device_type": DeviceType.WEB,
            "browser": "Chrome",
            "os": "Windows 10",
            "screen_resolution": "1920x1080",
        }

    @pytest.mark.asyncio
    async def test_get_session_by_device_fingerprint(
        self, session_manager, device_info
    ):
        """测试根据设备指纹获取会话"""
        # 创建带设备指纹的会话
        session = await session_manager.create_session(
            user_id="fingerprint_user",
            token="fingerprint_token",
            device_info=device_info,
        )

        # 根据设备指纹查找会话
        found_session = await session_manager.get_session_by_device_fingerprint(
            device_info["device_fingerprint"]
        )

        # 验证结果
        assert found_session is not None
        assert found_session.session_id == session.session_id
        assert found_session.user_id == session.user_id

    @pytest.mark.asyncio
    async def test_get_session_by_unknown_fingerprint(self, session_manager):
        """测试查找不存在的设备指纹"""
        found_session = await session_manager.get_session_by_device_fingerprint(
            "unknown_fingerprint"
        )

        assert found_session is None

    @pytest.mark.asyncio
    async def test_device_fingerprint_uniqueness(self, session_manager):
        """测试设备指纹唯一性"""
        fingerprint = "shared_fingerprint"

        # 创建第一个会话
        session1 = await session_manager.create_session(
            user_id="user1",
            token="token1",
            device_info={"device_fingerprint": fingerprint},
        )

        # 创建第二个会话（相同指纹）
        session2 = await session_manager.create_session(
            user_id="user2",
            token="token2",
            device_info={"device_fingerprint": fingerprint},
        )

        # 最后一个会话应该覆盖前一个
        found_session = await session_manager.get_session_by_device_fingerprint(
            fingerprint
        )
        assert found_session.session_id == session2.session_id


class TestSessionStatistics:
    """会话统计测试套件"""

    @pytest.fixture
    def session_manager(self):
        return SessionManager()

    @pytest.mark.asyncio
    async def test_get_session_statistics_empty(self, session_manager):
        """测试空会话统计"""
        stats = await session_manager.get_session_statistics()

        assert stats["total_sessions"] == 0
        assert stats["active_sessions"] == 0
        assert stats["expired_sessions"] == 0
        assert stats["revoked_sessions"] == 0
        assert stats["device_types"] == {}
        assert stats["average_session_duration"] == 0

    @pytest.mark.asyncio
    async def test_get_session_statistics_with_data(self, session_manager):
        """测试带数据的会话统计"""
        user_id = "stats_user"

        # 创建不同类型的会话
        active_session = await session_manager.create_session(
            user_id=user_id,
            token="active_token",
            device_info={"device_type": DeviceType.WEB},
        )

        expired_session = await session_manager.create_session(
            user_id=user_id,
            token="expired_token",
            device_info={"device_type": DeviceType.MOBILE},
            expires_in_seconds=-3600,
        )

        revoked_session = await session_manager.create_session(
            user_id=user_id,
            token="revoked_token",
            device_info={"device_type": DeviceType.DESKTOP},
        )
        await session_manager.revoke_session(revoked_session.session_id)

        # 获取统计
        stats = await session_manager.get_session_statistics(user_id)

        # 验证统计数据
        assert stats["total_sessions"] == 3
        assert stats["active_sessions"] == 1
        assert stats["expired_sessions"] == 1
        assert stats["revoked_sessions"] == 1

        # 验证设备类型统计
        assert stats["device_types"]["web"] == 1
        assert stats["device_types"]["mobile"] == 1
        assert stats["device_types"]["desktop"] == 1

    @pytest.mark.asyncio
    async def test_get_user_sessions(self, session_manager):
        """测试获取用户会话列表"""
        user_id = "multi_session_user"

        # 创建多个会话
        sessions = []
        for i in range(3):
            session = await session_manager.create_session(
                user_id=user_id, token=f"token_{i}"
            )
            sessions.append(session)

        # 撤销一个会话
        await session_manager.revoke_session(sessions[1].session_id)

        # 获取活跃会话
        active_sessions = await session_manager.get_user_sessions(
            user_id, active_only=True
        )
        assert len(active_sessions) == 2

        # 获取所有会话
        all_sessions = await session_manager.get_user_sessions(
            user_id, active_only=False
        )
        assert len(all_sessions) == 3

    @pytest.mark.asyncio
    async def test_get_sessions_nonexistent_user(self, session_manager):
        """测试获取不存在用户的会话"""
        sessions = await session_manager.get_user_sessions("nonexistent_user")
        assert sessions == []


class TestSessionManagerIntegration:
    """会话管理器集成测试"""

    @pytest.fixture
    def session_manager(self):
        return SessionManager()

    @pytest.mark.asyncio
    async def test_complete_session_lifecycle(self, session_manager):
        """测试完整的会话生命周期"""
        user_id = "lifecycle_user"
        session_token = "lifecycle_token"
        refresh_token_value = "lifecycle_refresh"

        # 1. 创建会话
        session = await session_manager.create_session(
            user_id=user_id,
            token=session_token,
            device_info={"device_type": DeviceType.WEB},
            ip_address="192.168.1.100",
        )

        assert session.is_active

        # 2. 创建刷新令牌
        refresh_token = await session_manager.create_refresh_token(
            session_id=session.session_id, token=refresh_token_value
        )

        assert refresh_token.is_valid

        # 3. 验证会话
        verified_session = await session_manager.verify_session(
            session.session_id, session_token
        )
        assert verified_session is not None

        # 4. 延长会话
        extend_result = await session_manager.extend_session(session.session_id, 7200)
        assert extend_result is True

        # 5. 使用刷新令牌
        refreshed_session = await session_manager.use_refresh_token(refresh_token_value)
        assert refreshed_session is not None

        # 6. 获取统计信息
        stats = await session_manager.get_session_statistics(user_id)
        assert stats["total_sessions"] == 1
        assert stats["active_sessions"] == 1

        # 7. 撤销会话
        revoke_result = await session_manager.revoke_session(
            session.session_id, "user_logout"
        )
        assert revoke_result is True
        assert not session.is_active

        # 8. 清理过期会话
        cleaned_count = await session_manager.cleanup_expired_sessions()
        # 会话被撤销而不是过期，所以清理数量为0
        assert cleaned_count == 0

    @pytest.mark.asyncio
    async def test_concurrent_session_operations(self, session_manager):
        """测试并发会话操作"""
        import asyncio

        user_id = "concurrent_user"

        async def create_session(session_id):
            return await session_manager.create_session(
                user_id=user_id, token=f"token_{session_id}"
            )

        # 并发创建多个会话
        tasks = [create_session(i) for i in range(10)]
        sessions = await asyncio.gather(*tasks)

        # 验证所有会话都被成功创建
        assert len(sessions) == 10
        assert len(session_manager.user_sessions[user_id]) == 10

        # 验证每个会话都有唯一ID
        session_ids = [s.session_id for s in sessions]
        assert len(set(session_ids)) == 10

    @pytest.mark.asyncio
    async def test_session_security_features(self, session_manager):
        """测试会话安全特性"""
        user_id = "security_user"

        # 创建高风险会话
        high_risk_session = await session_manager.create_session(
            user_id=user_id,
            token="high_risk_token",
            risk_score=85,
            is_trusted_device=False,
            device_info={
                "device_type": DeviceType.UNKNOWN,
                "device_fingerprint": "suspicious_device",
            },
        )

        # 创建低风险会话
        low_risk_session = await session_manager.create_session(
            user_id=user_id,
            token="low_risk_token",
            risk_score=10,
            is_trusted_device=True,
            device_info={
                "device_type": DeviceType.WEB,
                "device_fingerprint": "trusted_device",
            },
        )

        # 验证风险评分
        assert high_risk_session.risk_score == 85
        assert not high_risk_session.is_trusted_device

        assert low_risk_session.risk_score == 10
        assert low_risk_session.is_trusted_device

        # 模拟安全事件：撤销高风险会话
        await session_manager.revoke_session(
            high_risk_session.session_id, "high_risk_detected"
        )

        assert high_risk_session.status == SessionStatus.REVOKED
        assert high_risk_session.metadata["revocation_reason"] == "high_risk_detected"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
