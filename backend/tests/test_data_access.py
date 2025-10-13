"""
数据访问层测试
==============

测试数据访问层的各项功能:
- 数据库连接
- ORM模型
- 事务管理
- 缓存操作
- 查询优化
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Generator
import uuid

from backend.db import (
    init_database,
    close_database,
    init_cache,
    close_cache,
    transaction,
    async_transaction,
    readonly_transaction,
    get_redis_client,
    get_async_redis_client,
)
from backend.models import User, UserProfile, Session, AuditLog
from backend.db.utils import PaginationHelper, BulkOperator
from backend.db.cache import CacheOperations, CacheKeyManager
from backend.db.config import get_database_config, get_cache_config


class TestDatabaseConnection:
    """测试数据库连接"""

    @pytest.mark.asyncio
    async def test_database_initialization(self):
        """测试数据库初始化"""
        await init_database()

        # 测试配置
        config = get_database_config()
        assert config.host is not None
        assert config.port > 0
        assert config.database is not None

        await close_database()

    @pytest.mark.asyncio
    async def test_cache_initialization(self):
        """测试缓存初始化"""
        await init_cache()

        # 测试配置
        config = get_cache_config()
        assert config.host is not None
        assert config.port > 0

        await close_cache()


class TestUserModel:
    """测试用户模型"""

    @pytest.fixture(autouse=True)
    async def setup_database(self):
        """设置测试数据库"""
        await init_database()
        yield
        await close_database()

    def test_user_creation(self):
        """测试用户创建"""
        with transaction() as session:
            user = User(username="test_user", email="test@example.com")
            user.set_password("test123456")

            session.add(user)
            session.flush()

            assert user.id is not None
            assert user.username == "test_user"
            assert user.email == "test@example.com"
            assert user.verify_password("test123456")
            assert not user.verify_password("wrong_password")

    def test_user_password_validation(self):
        """测试密码验证"""
        user = User()
        user.set_password("secure_password")

        assert user.verify_password("secure_password")
        assert not user.verify_password("wrong_password")
        assert user.password_hash is not None
        assert user.password_salt is not None

    def test_user_validation(self):
        """测试用户数据验证"""
        user = User()

        # 测试用户名验证
        with pytest.raises(ValueError):
            user.username = "ab"  # 太短

        with pytest.raises(ValueError):
            user.username = "a" * 51  # 太长

        with pytest.raises(ValueError):
            user.username = "user@name"  # 包含非法字符

        # 测试邮箱验证
        with pytest.raises(ValueError):
            user.email = "invalid_email"

        # 正确的验证
        user.username = "valid_user"
        user.email = "valid@example.com"

    def test_user_relationships(self):
        """测试用户关联关系"""
        with transaction() as session:
            pass  # Auto-fixed empty block
            # 创建用户
            user = User(username="relation_user", email="relation@example.com")
            user.set_password("test123")
            session.add(user)
            session.flush()

            # 创建用户资料
            profile = UserProfile(
                user_id=user.id, display_name="Test User", bio="Test bio"
            )
            session.add(profile)
            session.flush()

            # 测试关联关系
            assert user.profile is not None
            assert user.profile.display_name == "Test User"
            assert profile.user.username == "relation_user"


class TestSessionModel:
    """测试会话模型"""

    @pytest.fixture(autouse=True)
    async def setup_database(self):
        """设置测试数据库"""
        await init_database()
        yield
        await close_database()

    def test_session_creation(self):
        """测试会话创建"""
        with transaction() as session_db:
            pass  # Auto-fixed empty block
            # 先创建用户
            user = User(username="session_user", email="session@example.com")
            user.set_password("test123")
            session_db.add(user)
            session_db.flush()

            # 创建会话
            token = "test_token_123456"
            session = Session.create_session(
                user_id=str(user.id),
                token=token,
                expires_in_seconds=3600,
                ip_address="192.168.1.1",
                user_agent="Test Client",
            )

            session_db.add(session)
            session_db.flush()

            assert session.session_id is not None
            assert session.verify_token(token)
            assert not session.verify_token("wrong_token")
            assert session.is_active
            assert not session.is_expired

    def test_session_expiration(self):
        """测试会话过期"""
        with transaction() as session_db:
            pass  # Auto-fixed empty block
            # 创建用户
            user = User(username="expire_user", email="expire@example.com")
            user.set_password("test123")
            session_db.add(user)
            session_db.flush()

            # 创建已过期的会话
            session = Session.create_session(
                user_id=str(user.id), token="expire_token", expires_in_seconds=-1  # 已过期
            )

            session_db.add(session)
            session_db.flush()

            assert session.is_expired
            assert not session.is_active


class TestTransactionManagement:
    """测试事务管理"""

    @pytest.fixture(autouse=True)
    async def setup_database(self):
        """设置测试数据库"""
        await init_database()
        yield
        await close_database()

    def test_transaction_commit(self):
        """测试事务提交"""
        user_id = None

        # 创建用户
        with transaction() as session:
            user = User(username="commit_user", email="commit@example.com")
            user.set_password("test123")
            session.add(user)
            session.flush()
            user_id = user.id

        # 验证用户已保存
        with readonly_transaction() as session:
            user = session.session.query(User).filter(User.id == user_id).first()
            assert user is not None
            assert user.username == "commit_user"

    def test_transaction_rollback(self):
        """测试事务回滚"""
        user_id = None

        try:
            with transaction() as session:
                user = User(username="rollback_user", email="rollback@example.com")
                user.set_password("test123")
                session.add(user)
                session.flush()
                user_id = user.id

                # 故意引发错误
                raise Exception("Test rollback")

        except Exception:
            pass  # 忽略预期的错误

        # 验证用户未保存（已回滚）
        with readonly_transaction() as session:
            user = session.session.query(User).filter(User.id == user_id).first()
            assert user is None

    @pytest.mark.asyncio
    async def test_async_transaction(self):
        """测试异步事务"""
        user_id = None

        # 创建用户
        async with async_transaction() as session:
            user = User(username="async_user", email="async@example.com")
            user.set_password("test123")
            session.add(user)
            await session.flush()
            user_id = user.id

        # 验证用户已保存
        from sqlalchemy import select

        async with readonly_transaction() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            assert user is not None
            assert user.username == "async_user"


class TestCacheOperations:
    """测试缓存操作"""

    @pytest.fixture(autouse=True)
    async def setup_cache(self):
        """设置测试缓存"""
        await init_cache()
        yield
        await close_cache()

    @pytest.mark.asyncio
    async def test_cache_basic_operations(self):
        """测试基本缓存操作"""
        redis_client = await get_async_redis_client()
        cache = CacheOperations(redis_client)

        # 测试设置和获取
        key = "test:key"
        value = {"name": "test", "value": 123}

        await cache.set(key, value, ttl=60)
        retrieved_value = await cache.get(key)

        assert retrieved_value == value

        # 测试键存在性
        exists = await cache.exists(key)
        assert exists == 1

        # 测试删除
        deleted = await cache.delete(key)
        assert deleted == 1

        # 验证已删除
        retrieved_value = await cache.get(key)
        assert retrieved_value is None

    @pytest.mark.asyncio
    async def test_cache_key_manager(self):
        """测试缓存键管理器"""
        user_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())

        # 测试键生成
        user_key = CacheKeyManager.user_key(user_id)
        session_key = CacheKeyManager.session_key(session_id)
        custom_key = CacheKeyManager.custom_key("test", "cache", "key")

        assert user_key == f"claude-enhancer:user:{user_id}"
        assert session_key == f"claude-enhancer:session:{session_id}"
        assert custom_key == "claude-enhancer:test:cache:key"

    @pytest.mark.asyncio
    async def test_cache_serialization(self):
        """测试缓存序列化"""
        redis_client = await get_async_redis_client()
        cache = CacheOperations(redis_client)

        # 测试JSON序列化
        json_data = {"name": "json_test", "items": [1, 2, 3]}
        await cache.set("json:test", json_data, serializer="json")
        retrieved_json = await cache.get("json:test", serializer="json")
        assert retrieved_json == json_data

        # 测试Pickle序列化
        pickle_data = {"complex": datetime.now(), "set": {1, 2, 3}}
        await cache.set("pickle:test", pickle_data, serializer="pickle")
        retrieved_pickle = await cache.get("pickle:test", serializer="pickle")
        assert retrieved_pickle["set"] == pickle_data["set"]


class TestQueryOperations:
    """测试查询操作"""

    @pytest.fixture(autouse=True)
    async def setup_database(self):
        """设置测试数据库"""
        await init_database()
        yield
        await close_database()

    def test_pagination(self):
        """测试分页查询"""
        # 创建测试数据
        with transaction() as session:
            users = []
            for i in range(25):  # 创建25个用户
                user = User(username=f"page_user_{i}", email=f"page{i}@example.com")
                user.set_password("test123")
                users.append(user)
                session.add(user)

        # 测试分页
        with readonly_transaction() as session:
            query = (
                session.session.query(User)
                .filter(User.username.like("page_user_%"))
                .order_by(User.created_at)
            )

            # 第一页
            users_page1, pagination1 = PaginationHelper.paginate_query(
                query, page=1, per_page=10
            )

            assert len(users_page1) == 10
            assert pagination1["page"] == 1
            assert pagination1["total"] == 25
            assert pagination1["total_pages"] == 3
            assert pagination1["has_next"] == True
            assert pagination1["has_prev"] == False

            # 第二页
            users_page2, pagination2 = PaginationHelper.paginate_query(
                query, page=2, per_page=10
            )

            assert len(users_page2) == 10
            assert pagination2["page"] == 2
            assert pagination2["has_next"] == True
            assert pagination2["has_prev"] == True

            # 最后一页
            users_page3, pagination3 = PaginationHelper.paginate_query(
                query, page=3, per_page=10
            )

            assert len(users_page3) == 5  # 剩余5个
            assert pagination3["page"] == 3
            assert pagination3["has_next"] == False
            assert pagination3["has_prev"] == True

    def test_bulk_operations(self):
        """测试批量操作"""
        # 准备批量数据
        users_data = []
        for i in range(50):
            users_data.append(
                {
                    "username": f"bulk_user_{i}",
                    "email": f"bulk{i}@example.com",
                    "status": "active",
                    "role": "user",
                }
            )

        # 批量插入
        with transaction() as session:
            count = BulkOperator.bulk_insert(
                session.session, User, users_data, batch_size=20
            )

            assert count == 50

        # 验证插入结果
        with readonly_transaction() as session:
            bulk_users = (
                session.session.query(User)
                .filter(User.username.like("bulk_user_%"))
                .all()
            )

            assert len(bulk_users) == 50


class TestAuditLog:
    """测试审计日志"""

    @pytest.fixture(autouse=True)
    async def setup_database(self):
        """设置测试数据库"""
        await init_database()
        yield
        await close_database()

    def test_audit_log_creation(self):
        """测试审计日志创建"""
        with transaction() as session:
            pass  # Auto-fixed empty block
            # 创建用户
            user = User(username="audit_user", email="audit@example.com")
            user.set_password("test123")
            session.add(user)
            session.flush()

            # 创建审计日志
            audit_log = AuditLog.create_log(
                action="CREATE",
                resource_type="User",
                description="创建测试用户",
                user_id=str(user.id),
                resource_id=str(user.id),
                ip_address="192.168.1.1",
                success=True,
            )

            session.add(audit_log)
            session.flush()

            assert audit_log.id is not None
            assert audit_log.action.value == "CREATE"
            assert audit_log.resource_type == "User"
            assert audit_log.success == True


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
