#!/usr/bin/env python3
"""
JWT令牌管理器 - RS256算法
负责生成、验证、刷新JWT令牌
"""

import os
import uuid
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
import redis
from dataclasses import dataclass

from backend.core.config import get_settings
from backend.core.exceptions import AuthenticationError, TokenExpiredError

@dataclass
class TokenPayload:
    """令牌负载数据类"""
    user_id: str
    username: str
    role: str
    jti: str
    token_type: str
    issued_at: datetime
    expires_at: datetime

class JWTManager:
    """JWT令牌管理器"""

    def __init__(self):
        self.settings = get_settings()
        self.redis_client = redis.Redis(
            host=self.settings.REDIS_HOST,
            port=self.settings.REDIS_PORT,
            db=self.settings.REDIS_DB,
            password=self.settings.REDIS_PASSWORD,
            decode_responses=True
        )

        # 令牌配置
        self.ACCESS_TOKEN_EXPIRE = timedelta(minutes=15)  # 15分钟
        self.REFRESH_TOKEN_EXPIRE = timedelta(days=7)     # 7天
        self.ALGORITHM = "RS256"

        # 加载或生成RSA密钥对
        self.private_key, self.public_key = self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        """加载或生成RSA密钥对"""
        private_key_path = self.settings.JWT_PRIVATE_KEY_PATH
        public_key_path = self.settings.JWT_PUBLIC_KEY_PATH

        # 尝试加载现有密钥
        if os.path.exists(private_key_path) and os.path.exists(public_key_path):
            try:
                with open(private_key_path, 'rb') as f:
                    private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None
                    )

                with open(public_key_path, 'rb') as f:
                    public_key = serialization.load_pem_public_key(f.read())

                return private_key, public_key
            except Exception as e:
                print(f"密钥加载失败，将生成新密钥: {e}")

        # 生成新的RSA密钥对
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()

        # 保存密钥到文件
        os.makedirs(os.path.dirname(private_key_path), exist_ok=True)

        # 保存私钥
        with open(private_key_path, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

        # 保存公钥
        with open(public_key_path, 'wb') as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

        # 设置适当的文件权限
        os.chmod(private_key_path, 0o600)
        os.chmod(public_key_path, 0o644)

        print("新的RSA密钥对生成完成")
        return private_key, public_key

    def generate_access_token(
        self,
        user_id: str,
        username: str,
        role: str,
        session_id: str
    ) -> str:
        """生成访问令牌"""
        now = datetime.now(timezone.utc)
        expires_at = now + self.ACCESS_TOKEN_EXPIRE
        jti = str(uuid.uuid4())

        payload = {
            'sub': user_id,           # Subject (用户ID)
            'username': username,     # 用户名
            'role': role,            # 用户角色
            'session_id': session_id, # 会话ID
            'jti': jti,              # JWT ID (用于撤销)
            'type': 'access',        # 令牌类型
            'iat': int(now.timestamp()),        # Issued at
            'exp': int(expires_at.timestamp()), # Expires at
            'iss': self.settings.JWT_ISSUER,    # Issuer
            'aud': self.settings.JWT_AUDIENCE,  # Audience
        }

        # 生成令牌
        token = jwt.encode(
            payload,
            self.private_key,
            algorithm=self.ALGORITHM
        )

        # 将JTI存储到Redis（用于令牌撤销检查）
        self.redis_client.setex(
            f"access_token:{jti}",
            int(self.ACCESS_TOKEN_EXPIRE.total_seconds()),
            json.dumps({
                'user_id': user_id,
                'session_id': session_id,
                'created_at': now.isoformat()
            })
        )

        return token

    def generate_refresh_token(
        self,
        user_id: str,
        username: str,
        session_id: str
    ) -> str:
        """生成刷新令牌"""
        now = datetime.now(timezone.utc)
        expires_at = now + self.REFRESH_TOKEN_EXPIRE
        jti = str(uuid.uuid4())

        payload = {
            'sub': user_id,
            'username': username,
            'session_id': session_id,
            'jti': jti,
            'type': 'refresh',
            'iat': int(now.timestamp()),
            'exp': int(expires_at.timestamp()),
            'iss': self.settings.JWT_ISSUER,
            'aud': self.settings.JWT_AUDIENCE,
        }

        token = jwt.encode(
            payload,
            self.private_key,
            algorithm=self.ALGORITHM
        )

        # 将刷新令牌存储到Redis
        self.redis_client.setex(
            f"refresh_token:{jti}",
            int(self.REFRESH_TOKEN_EXPIRE.total_seconds()),
            json.dumps({
                'user_id': user_id,
                'session_id': session_id,
                'created_at': now.isoformat()
            })
        )

        return token

    def verify_token(self, token: str, expected_type: str = 'access') -> TokenPayload:
        """验证令牌"""
        try:
            # 解码令牌
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.ALGORITHM],
                issuer=self.settings.JWT_ISSUER,
                audience=self.settings.JWT_AUDIENCE
            )

            # 检查令牌类型
            if payload.get('type') != expected_type:
                raise AuthenticationError(f"无效的令牌类型: {payload.get('type')}")

            jti = payload.get('jti')
            if not jti:
                raise AuthenticationError("令牌缺少JTI")

            # 检查令牌是否被撤销
            token_key = f"{expected_type}_token:{jti}"
            if not self.redis_client.exists(token_key):
                raise AuthenticationError("令牌已被撤销或不存在")

            # 构建令牌负载对象
            return TokenPayload(
                user_id=payload['sub'],
                username=payload.get('username', ''),
                role=payload.get('role', 'user'),
                jti=jti,
                token_type=payload['type'],
                issued_at=datetime.fromtimestamp(payload['iat'], timezone.utc),
                expires_at=datetime.fromtimestamp(payload['exp'], timezone.utc)
            )

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("令牌已过期")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"无效令牌: {str(e)}")
        except Exception as e:
            raise AuthenticationError(f"令牌验证失败: {str(e)}")

    def revoke_token(self, token: str) -> bool:
        """撤销单个令牌"""
        try:
            # 解码令牌获取JTI（不验证过期时间）
            unverified_payload = jwt.decode(
                token,
                options={"verify_exp": False, "verify_signature": False}
            )

            jti = unverified_payload.get('jti')
            token_type = unverified_payload.get('type', 'access')

            if jti:
                # 从Redis中删除令牌
                token_key = f"{token_type}_token:{jti}"
                self.redis_client.delete(token_key)
                return True

        except Exception:
            # 忽略解码错误，令牌可能已经无效
            pass

        return False

    def revoke_user_tokens(self, user_id: str, exclude_session: Optional[str] = None) -> int:
        """撤销用户的所有令牌（可排除指定会话）"""
        revoked_count = 0

        # 获取所有访问令牌
        access_pattern = "access_token:*"
        refresh_pattern = "refresh_token:*"

        for pattern in [access_pattern, refresh_pattern]:
            for key in self.redis_client.scan_iter(match=pattern):
                try:
                    token_data = self.redis_client.get(key)
                    if token_data:
                        data = json.loads(token_data)
                        if (data.get('user_id') == user_id and
                            data.get('session_id') != exclude_session):
                            self.redis_client.delete(key)
                            revoked_count += 1
                except Exception:
                    continue

        return revoked_count

    def revoke_session_tokens(self, session_id: str) -> int:
        """撤销指定会话的所有令牌"""
        revoked_count = 0

        for pattern in ["access_token:*", "refresh_token:*"]:
            for key in self.redis_client.scan_iter(match=pattern):
                try:
                    token_data = self.redis_client.get(key)
                    if token_data:
                        data = json.loads(token_data)
                        if data.get('session_id') == session_id:
                            self.redis_client.delete(key)
                            revoked_count += 1
                except Exception:
                    continue

        return revoked_count

    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """获取令牌信息（不验证有效性）"""
        try:
            payload = jwt.decode(
                token,
                options={"verify_exp": False, "verify_signature": False}
            )
            return {
                'user_id': payload.get('sub'),
                'username': payload.get('username'),
                'role': payload.get('role'),
                'jti': payload.get('jti'),
                'type': payload.get('type'),
                'issued_at': datetime.fromtimestamp(payload.get('iat', 0), timezone.utc),
                'expires_at': datetime.fromtimestamp(payload.get('exp', 0), timezone.utc),
                'session_id': payload.get('session_id')
            }
        except Exception:
            return None

    def cleanup_expired_tokens(self) -> int:
        """清理过期的令牌（Redis TTL会自动处理，这里主要用于统计）"""
        cleaned = 0
        current_time = datetime.now(timezone.utc)

        for pattern in ["access_token:*", "refresh_token:*"]:
            for key in self.redis_client.scan_iter(match=pattern):
                try:
                    ttl = self.redis_client.ttl(key)
                    if ttl == -2:  # 键不存在
                        cleaned += 1
                except Exception:
                    continue

        return cleaned

    def get_active_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的活跃会话"""
        sessions = []

        for key in self.redis_client.scan_iter(match="refresh_token:*"):
            try:
                token_data = self.redis_client.get(key)
                if token_data:
                    data = json.loads(token_data)
                    if data.get('user_id') == user_id:
                        sessions.append({
                            'session_id': data.get('session_id'),
                            'created_at': data.get('created_at'),
                            'ttl': self.redis_client.ttl(key)
                        })
            except Exception:
                continue

        return sessions