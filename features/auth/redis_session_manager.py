#!/usr/bin/env python3
"""
Perfect21 Redis会话管理器
基于Redis的高性能会话存储和管理
"""

import os
import sys
import json
import redis
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from modules.logger import log_info, log_error, log_warning

class RedisSessionManager:
    """Redis会话管理器"""

    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379,
                 redis_db: int = 2, redis_password: str = None):
        """初始化Redis会话管理器"""
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            # 测试连接
            self.redis_client.ping()
            self.use_redis = True
            log_info("Redis会话管理器初始化成功")
        except redis.ConnectionError as e:
            log_error("Redis连接失败，使用内存存储", e)
            self.use_redis = False
            self.memory_sessions = {}

        # 默认配置
        self.default_session_ttl = 24 * 60 * 60  # 24小时
        self.refresh_session_ttl = 7 * 24 * 60 * 60  # 7天
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"

    def create_session(self, user_id: str, session_data: Dict[str, Any],
                      ttl: int = None, remember_me: bool = False) -> str:
        """创建会话"""
        try:
            session_id = secrets.token_urlsafe(32)

            # 设置TTL
            if ttl is None:
                ttl = self.refresh_session_ttl if remember_me else self.default_session_ttl

            # 准备会话数据
            session_info = {
                'session_id': session_id,
                'user_id': user_id,
                'created_at': datetime.now().isoformat(),
                'last_access': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(seconds=ttl)).isoformat(),
                'remember_me': remember_me,
                'data': session_data
            }

            if self.use_redis:
                # 存储会话信息
                session_key = f"{self.session_prefix}{session_id}"
                self.redis_client.setex(
                    session_key,
                    ttl,
                    json.dumps(session_info)
                )

                # 将会话ID添加到用户会话列表
                user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
                self.redis_client.sadd(user_sessions_key, session_id)
                self.redis_client.expire(user_sessions_key, ttl)

                log_info(f"会话创建成功: {session_id} for user {user_id}")
            else:
                # 内存存储
                self.memory_sessions[session_id] = session_info
                log_warning(f"会话创建（内存）: {session_id} for user {user_id}")

            return session_id

        except Exception as e:
            log_error("创建会话失败", e)
            raise

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        try:
            if self.use_redis:
                session_key = f"{self.session_prefix}{session_id}"
                session_data = self.redis_client.get(session_key)

                if session_data:
                    session_info = json.loads(session_data)

                    # 检查是否过期
                    expires_at = datetime.fromisoformat(session_info['expires_at'])
                    if datetime.now() > expires_at:
                        self.delete_session(session_id)
                        return None

                    # 更新最后访问时间
                    session_info['last_access'] = datetime.now().isoformat()
                    self.redis_client.setex(
                        session_key,
                        self.redis_client.ttl(session_key),
                        json.dumps(session_info)
                    )

                    return session_info
                return None
            else:
                # 内存存储
                if session_id in self.memory_sessions:
                    session_info = self.memory_sessions[session_id]
                    expires_at = datetime.fromisoformat(session_info['expires_at'])
                    if datetime.now() > expires_at:
                        del self.memory_sessions[session_id]
                        return None

                    session_info['last_access'] = datetime.now().isoformat()
                    return session_info
                return None

        except Exception as e:
            log_error("获取会话失败", e)
            return None

    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """更新会话数据"""
        try:
            session_info = self.get_session(session_id)
            if not session_info:
                return False

            # 更新数据
            session_info['data'].update(data)
            session_info['last_access'] = datetime.now().isoformat()

            if self.use_redis:
                session_key = f"{self.session_prefix}{session_id}"
                ttl = self.redis_client.ttl(session_key)
                self.redis_client.setex(
                    session_key,
                    ttl if ttl > 0 else self.default_session_ttl,
                    json.dumps(session_info)
                )
            else:
                self.memory_sessions[session_id] = session_info

            log_info(f"会话更新成功: {session_id}")
            return True

        except Exception as e:
            log_error("更新会话失败", e)
            return False

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            if self.use_redis:
                session_key = f"{self.session_prefix}{session_id}"

                # 获取会话信息以获取用户ID
                session_data = self.redis_client.get(session_key)
                if session_data:
                    session_info = json.loads(session_data)
                    user_id = session_info.get('user_id')

                    # 从用户会话列表中移除
                    if user_id:
                        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
                        self.redis_client.srem(user_sessions_key, session_id)

                # 删除会话
                result = self.redis_client.delete(session_key)
                log_info(f"会话删除: {session_id}, 结果: {result}")
                return result > 0
            else:
                if session_id in self.memory_sessions:
                    del self.memory_sessions[session_id]
                    log_info(f"会话删除（内存）: {session_id}")
                    return True
                return False

        except Exception as e:
            log_error("删除会话失败", e)
            return False

    def delete_user_sessions(self, user_id: str) -> int:
        """删除用户的所有会话"""
        try:
            deleted_count = 0

            if self.use_redis:
                user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
                session_ids = self.redis_client.smembers(user_sessions_key)

                for session_id in session_ids:
                    if self.delete_session(session_id):
                        deleted_count += 1

                # 清空用户会话列表
                self.redis_client.delete(user_sessions_key)
            else:
                # 内存存储
                sessions_to_delete = []
                for session_id, session_info in self.memory_sessions.items():
                    if session_info.get('user_id') == user_id:
                        sessions_to_delete.append(session_id)

                for session_id in sessions_to_delete:
                    del self.memory_sessions[session_id]
                    deleted_count += 1

            log_info(f"用户会话删除: user_id={user_id}, 删除数量={deleted_count}")
            return deleted_count

        except Exception as e:
            log_error("删除用户会话失败", e)
            return 0

    def extend_session(self, session_id: str, additional_ttl: int = None) -> bool:
        """延长会话有效期"""
        try:
            if additional_ttl is None:
                additional_ttl = self.default_session_ttl

            if self.use_redis:
                session_key = f"{self.session_prefix}{session_id}"
                if self.redis_client.exists(session_key):
                    current_ttl = self.redis_client.ttl(session_key)
                    new_ttl = max(current_ttl, 0) + additional_ttl
                    self.redis_client.expire(session_key, new_ttl)

                    # 更新会话信息中的过期时间
                    session_data = self.redis_client.get(session_key)
                    if session_data:
                        session_info = json.loads(session_data)
                        session_info['expires_at'] = (
                            datetime.now() + timedelta(seconds=new_ttl)
                        ).isoformat()
                        self.redis_client.setex(session_key, new_ttl, json.dumps(session_info))

                    log_info(f"会话延期成功: {session_id}, 新TTL: {new_ttl}")
                    return True
                return False
            else:
                if session_id in self.memory_sessions:
                    session_info = self.memory_sessions[session_id]
                    current_expires = datetime.fromisoformat(session_info['expires_at'])
                    new_expires = max(current_expires, datetime.now()) + timedelta(seconds=additional_ttl)
                    session_info['expires_at'] = new_expires.isoformat()
                    return True
                return False

        except Exception as e:
            log_error("延长会话失败", e)
            return False

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有活跃会话"""
        try:
            sessions = []

            if self.use_redis:
                user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
                session_ids = self.redis_client.smembers(user_sessions_key)

                for session_id in session_ids:
                    session_info = self.get_session(session_id)
                    if session_info:
                        sessions.append(session_info)
            else:
                for session_info in self.memory_sessions.values():
                    if session_info.get('user_id') == user_id:
                        expires_at = datetime.fromisoformat(session_info['expires_at'])
                        if datetime.now() <= expires_at:
                            sessions.append(session_info)

            return sessions

        except Exception as e:
            log_error("获取用户会话失败", e)
            return []

    def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        try:
            cleaned_count = 0

            if self.use_redis:
                # Redis会自动处理过期键，这里只需要清理用户会话列表
                # 扫描所有用户会话列表键
                for key in self.redis_client.scan_iter(f"{self.user_sessions_prefix}*"):
                    user_id = key.replace(self.user_sessions_prefix, "")
                    session_ids = list(self.redis_client.smembers(key))

                    for session_id in session_ids:
                        session_key = f"{self.session_prefix}{session_id}"
                        if not self.redis_client.exists(session_key):
                            self.redis_client.srem(key, session_id)
                            cleaned_count += 1
            else:
                # 内存存储清理
                current_time = datetime.now()
                expired_sessions = []

                for session_id, session_info in self.memory_sessions.items():
                    expires_at = datetime.fromisoformat(session_info['expires_at'])
                    if current_time > expires_at:
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    del self.memory_sessions[session_id]
                    cleaned_count += 1

            log_info(f"过期会话清理完成，清理数量: {cleaned_count}")
            return cleaned_count

        except Exception as e:
            log_error("清理过期会话失败", e)
            return 0

    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        try:
            if self.use_redis:
                # 统计Redis中的会话数量
                session_count = 0
                for key in self.redis_client.scan_iter(f"{self.session_prefix}*"):
                    session_count += 1

                # 统计用户数量
                user_count = 0
                for key in self.redis_client.scan_iter(f"{self.user_sessions_prefix}*"):
                    user_count += 1

                return {
                    'total_sessions': session_count,
                    'active_users': user_count,
                    'storage_type': 'redis',
                    'redis_info': {
                        'connected': True,
                        'db_size': self.redis_client.dbsize()
                    }
                }
            else:
                active_sessions = 0
                current_time = datetime.now()
                users = set()

                for session_info in self.memory_sessions.values():
                    expires_at = datetime.fromisoformat(session_info['expires_at'])
                    if current_time <= expires_at:
                        active_sessions += 1
                        users.add(session_info['user_id'])

                return {
                    'total_sessions': len(self.memory_sessions),
                    'active_sessions': active_sessions,
                    'active_users': len(users),
                    'storage_type': 'memory',
                    'redis_info': {
                        'connected': False
                    }
                }

        except Exception as e:
            log_error("获取会话统计失败", e)
            return {}

    def cleanup(self):
        """清理资源"""
        try:
            if self.use_redis:
                self.redis_client.close()
            else:
                self.memory_sessions.clear()
            log_info("Redis会话管理器清理完成")
        except Exception as e:
            log_error("Redis会话管理器清理失败", e)