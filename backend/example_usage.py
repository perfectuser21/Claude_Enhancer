"""
数据访问层使用示例
==================

演示如何使用Perfect21数据访问层的各种功能:
- 基本CRUD操作
- 事务管理
- 缓存使用
- 分页查询
- 批量操作
- 性能监控
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from backend.db import (
    init_database, close_database, init_cache, close_cache,
    transaction, async_transaction, readonly_transaction,
    get_redis_client, get_async_redis_client
)
from backend.models import User, UserProfile, Session, AuditLog
from backend.db.utils import PaginationHelper, BulkOperator, performance_monitor
from backend.db.cache import CacheOperations, CacheKeyManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserService:
    """
    用户服务示例
    ============

    演示用户相关的数据库操作
    """

    def __init__(self):
        self.cache = None

    async def init_cache(self):
        """初始化缓存客户端"""
        redis_client = await get_async_redis_client()
        self.cache = CacheOperations(redis_client)

    def create_user(self, username: str, email: str, password: str) -> Optional[User]:
        """
        创建用户 (同步版本)

        Args:
            username: 用户名
            email: 邮箱
            password: 密码

        Returns:
            创建的用户对象
        """
        try:
            with transaction() as session:
                # 检查用户是否已存在
                existing_user = session.session.query(User).filter(
                    (User.username == username) | (User.email == email)
                ).first()

                if existing_user:
                    logger.warning(f"用户已存在: {username}")
                    return None

                # 创建新用户
                user = User(
                    username=username,
                    email=email
                )
                user.set_password(password)

                session.add(user)
                session.flush()  # 获取ID

                # 创建用户资料
                profile = UserProfile(
                    user_id=user.id,
                    display_name=username
                )
                session.add(profile)

                # 记录审计日志
                audit_log = AuditLog.create_log(
                    action="CREATE",
                    resource_type="User",
                    description=f"创建用户: {username}",
                    resource_id=str(user.id),
                    user_id=str(user.id)
                )
                session.add(audit_log)

                logger.info(f"用户创建成功: {username}")
                return user

        except Exception as e:
            logger.error(f"用户创建失败: {e}")
            return None

    async def create_user_async(self, username: str, email: str, password: str) -> Optional[User]:
        """
        创建用户 (异步版本)
        """
        try:
            async with async_transaction() as session:
                # 检查用户是否已存在
                from sqlalchemy import select
                result = await session.execute(
                    select(User).where(
                        (User.username == username) | (User.email == email)
                    )
                )
                existing_user = result.scalar_one_or_none()

                if existing_user:
                    logger.warning(f"用户已存在: {username}")
                    return None

                # 创建新用户
                user = User(
                    username=username,
                    email=email
                )
                user.set_password(password)

                session.add(user)
                await session.flush()

                # 创建用户资料
                profile = UserProfile(
                    user_id=user.id,
                    display_name=username
                )
                session.add(profile)

                # 缓存用户信息
                if self.cache:
                    user_key = CacheKeyManager.user_key(str(user.id))
                    await self.cache.set(user_key, user.to_dict(), ttl=1800)

                logger.info(f"异步用户创建成功: {username}")
                return user

        except Exception as e:
            logger.error(f"异步用户创建失败: {e}")
            return None

    async def get_user_cached(self, user_id: str) -> Optional[dict]:
        """
        从缓存获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            用户信息字典
        """
        if not self.cache:
            await self.init_cache()

        try:
            # 先从缓存获取
            user_key = CacheKeyManager.user_key(user_id)
            cached_user = await self.cache.get(user_key)

            if cached_user:
                logger.info(f"从缓存获取用户: {user_id}")
                return cached_user

            # 缓存未命中，从数据库获取
            async with readonly_transaction() as session:
                from sqlalchemy import select
                from sqlalchemy.orm import selectinload

                result = await session.execute(
                    select(User)
                    .options(selectinload(User.profile))
                    .where(User.id == user_id)
                )
                user = result.scalar_one_or_none()

                if user:
                    user_data = user.to_dict()
                    # 加入资料信息
                    if user.profile:
                        user_data['profile'] = user.profile.to_dict()

                    # 缓存用户信息
                    await self.cache.set(user_key, user_data, ttl=1800)

                    logger.info(f"从数据库获取并缓存用户: {user_id}")
                    return user_data

            return None

        except Exception as e:
            logger.error(f"获取用户失败: {e}")
            return None

    def get_users_paginated(self, page: int = 1, per_page: int = 20) -> tuple:
        """
        分页获取用户列表

        Args:
            page: 页码
            per_page: 每页数量

        Returns:
            (用户列表, 分页信息)
        """
        try:
            with readonly_transaction() as session:
                # 构建查询
                query = session.session.query(User).filter(User.is_deleted == False)

                # 分页查询
                users, pagination_info = PaginationHelper.paginate_query(
                    query, page=page, per_page=per_page
                )

                logger.info(f"分页查询用户: 第{page}页，共{pagination_info['total']}条")
                return users, pagination_info

        except Exception as e:
            logger.error(f"分页查询用户失败: {e}")
            return [], {}

    def bulk_create_users(self, users_data: List[dict]) -> int:
        """
        批量创建用户

        Args:
            users_data: 用户数据列表

        Returns:
            创建的用户数量
        """
        try:
            with transaction() as session:
                # 预处理数据
                processed_data = []
                for user_data in users_data:
                    # 设置密码哈希
                    user = User()
                    user.set_password(user_data.get('password', 'default123'))

                    processed_data.append({
                        'username': user_data['username'],
                        'email': user_data['email'],
                        'password_hash': user.password_hash,
                        'password_salt': user.password_salt,
                        'status': 'active',
                        'role': 'user'
                    })

                # 批量插入
                count = BulkOperator.bulk_insert(
                    session.session,
                    User,
                    processed_data,
                    batch_size=500
                )

                logger.info(f"批量创建用户完成: {count}条")
                return count

        except Exception as e:
            logger.error(f"批量创建用户失败: {e}")
            return 0


class SessionService:
    """
    会话服务示例
    ============

    演示会话管理的数据库操作
    """

    def __init__(self):
        self.cache = None

    async def init_cache(self):
        """初始化缓存客户端"""
        redis_client = await get_async_redis_client()
        self.cache = CacheOperations(redis_client)

    async def create_session(
        self,
        user_id: str,
        token: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Optional[Session]:
        """
        创建用户会话

        Args:
            user_id: 用户ID
            token: 会话令牌
            ip_address: IP地址
            user_agent: 用户代理

        Returns:
            创建的会话对象
        """
        try:
            async with async_transaction() as db_session:
                # 创建会话
                session = Session.create_session(
                    user_id=user_id,
                    token=token,
                    expires_in_seconds=3600,  # 1小时
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                db_session.add(session)
                await db_session.flush()

                # 缓存会话信息
                if not self.cache:
                    await self.init_cache()

                session_key = CacheKeyManager.session_key(session.session_id)
                await self.cache.set(
                    session_key,
                    session.to_dict(),
                    ttl=3600
                )

                # 缓存认证令牌映射
                auth_key = CacheKeyManager.auth_key(session.token_hash)
                await self.cache.set(
                    auth_key,
                    session.session_id,
                    ttl=3600
                )

                logger.info(f"会话创建成功: {session.session_id}")
                return session

        except Exception as e:
            logger.error(f"会话创建失败: {e}")
            return None

    async def validate_session(self, token: str) -> Optional[Session]:
        """
        验证会话令牌

        Args:
            token: 会话令牌

        Returns:
            会话对象或None
        """
        try:
            if not self.cache:
                await self.init_cache()

            # 从缓存获取会话ID
            token_hash = Session.generate_token_hash(token)
            auth_key = CacheKeyManager.auth_key(token_hash)
            session_id = await self.cache.get(auth_key)

            if session_id:
                # 从缓存获取会话信息
                session_key = CacheKeyManager.session_key(session_id)
                session_data = await self.cache.get(session_key)

                if session_data:
                    logger.info(f"从缓存验证会话: {session_id}")
                    # 这里可以构造Session对象或返回字典
                    return session_data

            # 缓存未命中，从数据库验证
            async with readonly_transaction() as db_session:
                from sqlalchemy import select

                result = await db_session.execute(
                    select(Session)
                    .where(Session.token_hash == token_hash)
                    .where(Session.status == "active")
                )
                session = result.scalar_one_or_none()

                if session and session.is_active:
                    # 更新缓存
                    session_key = CacheKeyManager.session_key(session.session_id)
                    await self.cache.set(
                        session_key,
                        session.to_dict(),
                        ttl=3600
                    )

                    logger.info(f"从数据库验证会话: {session.session_id}")
                    return session

            return None

        except Exception as e:
            logger.error(f"会话验证失败: {e}")
            return None


async def demo_database_operations():
    """
    演示数据库操作
    """
    logger.info("=== 数据访问层演示开始 ===")

    try:
        # 初始化数据库和缓存
        await init_database()
        await init_cache()

        # 创建服务实例
        user_service = UserService()
        session_service = SessionService()

        # 演示1: 创建用户
        logger.info("\n--- 演示1: 创建用户 ---")
        user = await user_service.create_user_async(
            username="demo_user",
            email="demo@example.com",
            password="demo123456"
        )

        if user:
            logger.info(f"用户创建成功: {user.username} (ID: {user.id})")

            # 演示2: 缓存查询
            logger.info("\n--- 演示2: 缓存查询 ---")
            cached_user = await user_service.get_user_cached(str(user.id))
            if cached_user:
                logger.info(f"缓存查询成功: {cached_user['username']}")

            # 演示3: 创建会话
            logger.info("\n--- 演示3: 创建会话 ---")
            session = await session_service.create_session(
                user_id=str(user.id),
                token="demo_token_123456",
                ip_address="192.168.1.100",
                user_agent="Demo Client 1.0"
            )

            if session:
                logger.info(f"会话创建成功: {session.session_id}")

                # 演示4: 会话验证
                logger.info("\n--- 演示4: 会话验证 ---")
                validated_session = await session_service.validate_session("demo_token_123456")
                if validated_session:
                    logger.info("会话验证成功")

        # 演示5: 分页查询
        logger.info("\n--- 演示5: 分页查询 ---")
        users, pagination = user_service.get_users_paginated(page=1, per_page=10)
        logger.info(f"分页查询结果: {len(users)}条用户，共{pagination.get('total', 0)}条")

        # 演示6: 批量操作
        logger.info("\n--- 演示6: 批量操作 ---")
        bulk_users = [
            {"username": f"bulk_user_{i}", "email": f"bulk{i}@example.com", "password": "bulk123"}
            for i in range(1, 11)
        ]
        count = user_service.bulk_create_users(bulk_users)
        logger.info(f"批量创建用户: {count}条")

        # 演示7: 性能监控
        logger.info("\n--- 演示7: 性能监控 ---")
        metrics = performance_monitor.get_metrics()
        logger.info(f"性能指标: {metrics}")

    except Exception as e:
        logger.error(f"演示过程中出错: {e}")

    finally:
        # 清理资源
        await close_cache()
        await close_database()

    logger.info("=== 数据访问层演示结束 ===")


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_database_operations())