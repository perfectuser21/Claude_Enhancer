#!/usr/bin/env python3
"""
Perfect21 Token黑名单管理器
使用Redis持久化存储被撤销的token
"""

import os
import time
import redis
from typing import Optional
from modules.logger import log_info, log_error

class TokenBlacklist:
    """Token黑名单管理器，使用Redis持久化"""

    def __init__(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 3,  # TCP_KEEPINTVL
                    3: 5,  # TCP_KEEPCNT
                },
                connection_pool_kwargs={
                    'max_connections': 50
                }
            )
            # 测试连接
            self.redis_client.ping()
            log_info("Redis token blacklist initialized successfully")
        except redis.ConnectionError as e:
            log_error("Failed to connect to Redis, falling back to in-memory blacklist", e)
            # 如果Redis不可用，使用内存黑名单作为后备
            self.redis_client = None
            self.memory_blacklist = set()

    def add_token(self, token: str, jti: Optional[str] = None, expires_at: Optional[int] = None):
        """
        添加token到黑名单

        Args:
            token: 完整的token字符串
            jti: JWT ID，用于更高效的存储
            expires_at: token过期时间戳，用于自动清理
        """
        try:
            if self.redis_client:
                # 使用jti作为key，如果没有jti则使用token的hash
                key = f"blacklist:{jti}" if jti else f"blacklist:token:{hash(token)}"

                # 计算TTL（Time To Live）
                if expires_at:
                    ttl = expires_at - int(time.time())
                    if ttl > 0:
                        # 设置带过期时间的key
                        self.redis_client.setex(key, ttl, "1")
                        log_info(f"Token added to blacklist with TTL {ttl}s: {key}")
                    else:
                        log_info(f"Token already expired, not adding to blacklist: {key}")
                else:
                    # 没有过期时间，设置默认24小时过期
                    self.redis_client.setex(key, 86400, "1")
                    log_info(f"Token added to blacklist with default 24h TTL: {key}")
            else:
                # Redis不可用，使用内存黑名单
                self.memory_blacklist.add(jti if jti else token)
                log_info(f"Token added to memory blacklist")
        except Exception as e:
            log_error("Failed to add token to blacklist", e)
            # 确保即使出错也能添加到内存黑名单
            if hasattr(self, 'memory_blacklist'):
                self.memory_blacklist.add(jti if jti else token)

    def is_blacklisted(self, token: str, jti: Optional[str] = None) -> bool:
        """
        检查token是否在黑名单中

        Args:
            token: 完整的token字符串
            jti: JWT ID，用于更高效的查询

        Returns:
            bool: True如果token在黑名单中
        """
        try:
            if self.redis_client:
                # 优先使用jti查询
                if jti:
                    if self.redis_client.exists(f"blacklist:{jti}"):
                        return True

                # 使用token hash查询
                if self.redis_client.exists(f"blacklist:token:{hash(token)}"):
                    return True

                return False
            else:
                # Redis不可用，使用内存黑名单
                return (jti in self.memory_blacklist) or (token in self.memory_blacklist)
        except Exception as e:
            log_error("Failed to check blacklist", e)
            # 出错时认为token在黑名单中（安全优先）
            return True

    def remove_token(self, token: str, jti: Optional[str] = None):
        """
        从黑名单中移除token

        Args:
            token: 完整的token字符串
            jti: JWT ID
        """
        try:
            if self.redis_client:
                if jti:
                    self.redis_client.delete(f"blacklist:{jti}")
                self.redis_client.delete(f"blacklist:token:{hash(token)}")
                log_info("Token removed from blacklist")
            else:
                # Redis不可用，从内存黑名单移除
                self.memory_blacklist.discard(jti if jti else token)
                log_info("Token removed from memory blacklist")
        except Exception as e:
            log_error("Failed to remove token from blacklist", e)

    def clear_all(self):
        """清空所有黑名单（谨慎使用）"""
        try:
            if self.redis_client:
                # 获取所有黑名单key
                keys = self.redis_client.keys("blacklist:*")
                if keys:
                    self.redis_client.delete(*keys)
                    log_info(f"Cleared {len(keys)} tokens from blacklist")
            else:
                self.memory_blacklist.clear()
                log_info("Cleared memory blacklist")
        except Exception as e:
            log_error("Failed to clear blacklist", e)

    def get_stats(self) -> dict:
        """获取黑名单统计信息"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys("blacklist:*")
                return {
                    'backend': 'redis',
                    'total_tokens': len(keys),
                    'redis_connected': True
                }
            else:
                return {
                    'backend': 'memory',
                    'total_tokens': len(self.memory_blacklist),
                    'redis_connected': False
                }
        except Exception as e:
            log_error("Failed to get blacklist stats", e)
            return {
                'backend': 'unknown',
                'total_tokens': 0,
                'error': str(e)
            }

    def cleanup_expired(self):
        """
        清理过期的黑名单条目
        Redis会自动清理过期key，这个方法主要用于内存黑名单
        """
        if not self.redis_client and hasattr(self, 'memory_blacklist'):
            # 内存黑名单需要手动清理
            # 这里简化处理，实际应该存储过期时间
            log_info("Memory blacklist cleanup not implemented yet")

    def __del__(self):
        """清理资源"""
        try:
            if self.redis_client:
                self.redis_client.close()
        except Exception:
            pass


# 全局实例
_token_blacklist = None

def get_token_blacklist() -> TokenBlacklist:
    """获取全局Token黑名单实例"""
    global _token_blacklist
    if _token_blacklist is None:
        _token_blacklist = TokenBlacklist()
    return _token_blacklist