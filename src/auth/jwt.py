"""
JWT Token管理模块
实现JWT token的生成、验证、刷新等功能
包含安全配置和防护机制
"""

import jwt
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Union
from functools import wraps


class JWTTokenManager:
    """JWT Token管理器"""

    def __init__(
        self,
        secret_key: str = "your-super-secret-key-change-in-production",
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7,
    ):
        """
        初始化JWT管理器

        Args:
            secret_key: JWT签名密钥
            algorithm: 加密算法
            access_token_expire_minutes: 访问令牌过期时间(分钟)
            refresh_token_expire_days: 刷新令牌过期时间(天)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

        # 黑名单存储（生产环境应使用Redis等持久化存储）
        self.blacklisted_tokens = set()

        # 刷新令牌存储（生产环境应使用数据库）
        self.refresh_tokens = {}

    def generate_access_token(self, user_data: Dict[str, Any]) -> str:
        """
        生成访问令牌

        Args:
            user_data: 用户数据字典，包含user_id, username, roles等

        Returns:
            str: JWT访问令牌
        """
        now = datetime.utcnow()
        payload = {
            "user_id": user_data.get("user_id"),
            "username": user_data.get("username"),
            "email": user_data.get("email"),
            "roles": user_data.get("roles", ["user"]),
            "permissions": user_data.get("permissions", []),
            "iat": now,  # 签发时间
            "exp": now + timedelta(minutes=self.access_token_expire_minutes),  # 过期时间
            "type": "access",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def generate_refresh_token(self, user_id: int) -> str:
        """
        生成刷新令牌

        Args:
            user_id: 用户ID

        Returns:
            str: JWT刷新令牌
        """
        now = datetime.utcnow()
        payload = {
            "user_id": user_id,
            "iat": now,
            "exp": now + timedelta(days=self.refresh_token_expire_days),
            "type": "refresh",
        }

        refresh_token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        # 存储刷新令牌
        self.refresh_tokens[user_id] = {
            "token": refresh_token,
            "created_at": now,
            "expires_at": now + timedelta(days=self.refresh_token_expire_days),
        }

        return refresh_token

    def verify_token(
        self, token: str, token_type: str = "access"
    ) -> Optional[Dict[str, Any]]:
        """
        验证JWT令牌

        Args:
            token: JWT令牌字符串
            token_type: 令牌类型 ('access' 或 'refresh')

        Returns:
            Dict: 解码后的payload，验证失败返回None
        """
        try:
            # 检查黑名单
            if token in self.blacklisted_tokens:
                return None

            # 解码验证
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # 检查令牌类型
            if payload.get("type") != token_type:
                return None

            # 检查过期时间
            if datetime.utcnow().timestamp() > payload.get("exp", 0):
                return None

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None

    def refresh_access_token(
        self, refresh_token: str, user_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        使用刷新令牌生成新的访问令牌

        Args:
            refresh_token: 刷新令牌
            user_data: 最新的用户数据

        Returns:
            str: 新的访问令牌，失败返回None
        """
        # 验证刷新令牌
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None

        user_id = payload.get("user_id")

        # 检查刷新令牌是否在存储中
        stored_token = self.refresh_tokens.get(user_id)
        if not stored_token or stored_token["token"] != refresh_token:
            return None

        # 生成新的访问令牌
        return self.generate_access_token(user_data)

    def revoke_token(self, token: str) -> bool:
        """
        撤销令牌（加入黑名单）

        Args:
            token: 要撤销的令牌

        Returns:
            bool: 撤销成功返回True
        """
        try:
            self.blacklisted_tokens.add(token)
            return True
        except Exception:
            return False

    def revoke_user_tokens(self, user_id: int) -> bool:
        """
        撤销用户的所有令牌

        Args:
            user_id: 用户ID

        Returns:
            bool: 撤销成功返回True
        """
        try:
            # 移除刷新令牌
            if user_id in self.refresh_tokens:
                refresh_token = self.refresh_tokens[user_id]["token"]
                self.blacklisted_tokens.add(refresh_token)
                del self.refresh_tokens[user_id]

            return True
        except Exception:
            return False

    def decode_token_without_verification(self, token: str) -> Optional[Dict[str, Any]]:
        """
        不验证签名直接解码令牌（用于获取过期令牌信息）

        Args:
            token: JWT令牌

        Returns:
            Dict: 解码后的payload
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            return None

    def get_token_info(self, token: str) -> Dict[str, Any]:
        """
        获取令牌详细信息

        Args:
            token: JWT令牌

        Returns:
            Dict: 令牌信息
        """
        payload = self.decode_token_without_verification(token)
        if not payload:
            return {"valid": False, "error": "Invalid token format"}

        now = datetime.utcnow().timestamp()
        exp = payload.get("exp", 0)
        iat = payload.get("iat", 0)

        return {
            "valid": token not in self.blacklisted_tokens and now < exp,
            "expired": now >= exp,
            "blacklisted": token in self.blacklisted_tokens,
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "roles": payload.get("roles", []),
            "type": payload.get("type"),
            "issued_at": datetime.fromtimestamp(iat).isoformat() if iat else None,
            "expires_at": datetime.fromtimestamp(exp).isoformat() if exp else None,
            "time_to_expire": max(0, exp - now) if exp else 0,
        }


class TokenBlacklist:
    """令牌黑名单管理"""

    def __init__(self):
        self.blacklisted_tokens = set()
        self.blacklist_reasons = {}

    def add_token(self, token: str, reason: str = "User logout") -> bool:
        """添加令牌到黑名单"""
        try:
            self.blacklisted_tokens.add(token)
            self.blacklist_reasons[token] = {
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
            }
            return True
        except Exception:
            return False

    def is_blacklisted(self, token: str) -> bool:
        """检查令牌是否在黑名单中"""
        return token in self.blacklisted_tokens

    def remove_token(self, token: str) -> bool:
        """从黑名单移除令牌"""
        try:
            self.blacklisted_tokens.discard(token)
            self.blacklist_reasons.pop(token, None)
            return True
        except Exception:
            return False

    def cleanup_expired_tokens(self, jwt_manager: JWTTokenManager) -> int:
        """清理已过期的黑名单令牌"""
        expired_tokens = []

        for token in self.blacklisted_tokens:
            payload = jwt_manager.decode_token_without_verification(token)
            if payload:
                exp = payload.get("exp", 0)
                if datetime.utcnow().timestamp() > exp:
                    expired_tokens.append(token)

        for token in expired_tokens:
            self.remove_token(token)

        return len(expired_tokens)


# 全局JWT管理器实例
jwt_manager = JWTTokenManager()
token_blacklist = TokenBlacklist()


def require_token(token_type: str = "access"):
    """
    需要令牌的装饰器

    Args:
        token_type: 令牌类型 ('access' 或 'refresh')
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 这里应该从请求头获取token
            # 示例实现，实际使用时需要根据框架调整
            token = (
                kwargs.get("token") or getattr(args[0], "token", None) if args else None
            )

            if not token:
                return {"error": "Token required", "code": 401}

            payload = jwt_manager.verify_token(token, token_type)
            if not payload:
                return {"error": "Invalid or expired token", "code": 401}

            # 将用户信息添加到参数中
            kwargs["current_user"] = payload
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(required_roles: Union[str, list]):
    """
    需要特定角色的装饰器

    Args:
        required_roles: 需要的角色，可以是字符串或列表
    """
    if isinstance(required_roles, str):
        required_roles = [required_roles]

    def decorator(func):
        @wraps(func)
        @require_token()
        def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user", {})
            user_roles = current_user.get("roles", [])

            # 检查用户是否有任一需要的角色
            if not any(role in user_roles for role in required_roles):
                return {"error": "Insufficient permissions", "code": 403}

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_permission(required_permissions: Union[str, list]):
    """
    需要特定权限的装饰器

    Args:
        required_permissions: 需要的权限，可以是字符串或列表
    """
    if isinstance(required_permissions, str):
        required_permissions = [required_permissions]

    def decorator(func):
        @wraps(func)
        @require_token()
        def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user", {})
            user_permissions = current_user.get("permissions", [])

            # 检查用户是否有所有需要的权限
            if not all(perm in user_permissions for perm in required_permissions):
                return {"error": "Insufficient permissions", "code": 403}

            return func(*args, **kwargs)

        return wrapper

    return decorator
