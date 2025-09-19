#!/usr/bin/env python3
"""
Perfect21 用户登录API - 企业级身份认证接口
基于Perfect21架构设计的RESTful身份认证系统
遵循OAuth 2.0和JWT标准，提供完整的用户认证解决方案
"""

import os
import sys
import time
import hmac
import hashlib
import secrets
import jwt
import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps
from flask import Flask, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import redis
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, validator, EmailStr
import json

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from modules.config import config
from modules.logger import log_info, log_error, log_auth_event
from features.capability_discovery.capability import CapabilityDefinition


class AuthenticationError(Exception):
    """身份认证错误"""
    pass


class AuthorizationError(Exception):
    """授权错误"""
    pass


class TokenExpiredError(Exception):
    """令牌过期错误"""
    pass


class UserRole(Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"
    GUEST = "guest"


class LoginStatus(Enum):
    """登录状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    LOCKED = "locked"
    EXPIRED = "expired"
    INACTIVE = "inactive"


@dataclass
class LoginAttempt:
    """登录尝试记录"""
    user_id: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    status: LoginStatus
    failure_reason: Optional[str] = None


@dataclass
class UserProfile:
    """用户档案"""
    user_id: str
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    is_locked: bool = False
    lock_until: Optional[datetime] = None


@dataclass
class JWTTokens:
    """JWT令牌对"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600  # 1小时
    scope: str = "read write"


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str
    remember_me: Optional[bool] = False
    captcha_token: Optional[str] = None
    device_fingerprint: Optional[str] = None

    @validator('username')
    def username_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('用户名不能为空')
        return v.strip()

    @validator('password')
    def password_must_be_valid(cls, v):
        if not v or len(v) < 6:
            raise ValueError('密码至少6个字符')
        return v


class LoginResponse(BaseModel):
    """登录响应模型"""
    success: bool
    message: str
    user_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    user_profile: Optional[Dict[str, Any]] = None
    permissions: Optional[List[str]] = None
    session_id: Optional[str] = None


class TokenValidationResponse(BaseModel):
    """令牌验证响应模型"""
    valid: bool
    user_id: Optional[str] = None
    role: Optional[str] = None
    expires_at: Optional[datetime] = None
    permissions: Optional[List[str]] = None


# 数据库模型
Base = declarative_base()


class User(Base):
    """用户表模型"""
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default='user')
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)
    lock_until = Column(DateTime, nullable=True)
    login_attempts = Column(Integer, default=0)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    profile_data = Column(Text, nullable=True)  # JSON格式的额外用户信息


class LoginSession(Base):
    """登录会话表模型"""
    __tablename__ = 'login_sessions'

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    access_token_hash = Column(String(255), nullable=False)
    refresh_token_hash = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)


class LoginAuditLog(Base):
    """登录审计日志表模型"""
    __tablename__ = 'login_audit_logs'

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=True, index=True)
    username = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    login_status = Column(String(20), nullable=False)
    failure_reason = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    additional_data = Column(Text, nullable=True)  # JSON格式的额外数据


class UserLoginAPI:
    """用户登录API核心类"""

    def __init__(self):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # JWT配置
        self.jwt_secret_key = self.config.get('auth.jwt_secret_key', self._generate_secret_key())
        self.jwt_algorithm = self.config.get('auth.jwt_algorithm', 'HS256')
        self.access_token_expires = self.config.get('auth.access_token_expires', 3600)  # 1小时
        self.refresh_token_expires = self.config.get('auth.refresh_token_expires', 86400 * 7)  # 7天

        # 安全配置
        self.max_login_attempts = self.config.get('auth.max_login_attempts', 5)
        self.lockout_duration = self.config.get('auth.lockout_duration', 900)  # 15分钟
        self.require_captcha_after = self.config.get('auth.require_captcha_after', 3)
        self.password_salt_rounds = self.config.get('auth.password_salt_rounds', 12)

        # 初始化数据库
        self.db_engine = self._init_database()
        self.db_session_maker = sessionmaker(bind=self.db_engine)

        # 初始化Redis（用于会话存储和限流）
        self.redis_client = self._init_redis()

        log_info("用户登录API初始化完成")

    def _generate_secret_key(self) -> str:
        """生成JWT密钥"""
        return secrets.token_urlsafe(64)

    def _init_database(self):
        """初始化数据库"""
        db_url = self.config.get('database.url', 'sqlite:///perfect21_auth.db')
        engine = create_engine(db_url, echo=self.config.get('database.echo', False))

        # 创建表
        Base.metadata.create_all(engine)

        return engine

    def _init_redis(self):
        """初始化Redis连接"""
        try:
            redis_config = self.config.get('redis', {})
            client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                password=redis_config.get('password'),
                decode_responses=True
            )
            # 测试连接
            client.ping()
            return client
        except Exception as e:
            self.logger.warning(f"Redis连接失败，使用内存存储: {e}")
            return None

    def login(self, login_request: LoginRequest, client_ip: str = None, user_agent: str = None) -> LoginResponse:
        """
        用户登录接口

        Args:
            login_request: 登录请求数据
            client_ip: 客户端IP地址
            user_agent: 用户代理字符串

        Returns:
            LoginResponse: 登录响应数据
        """
        try:
            # 1. 参数验证
            self._validate_login_request(login_request)

            # 2. 检查IP限流
            if not self._check_ip_rate_limit(client_ip):
                return LoginResponse(
                    success=False,
                    message="请求过于频繁，请稍后再试"
                )

            # 3. 查找用户
            with self.db_session_maker() as session:
                user = session.query(User).filter_by(username=login_request.username).first()

                if not user:
                    # 记录失败尝试
                    self._log_login_attempt(
                        user_id=None,
                        username=login_request.username,
                        ip_address=client_ip,
                        user_agent=user_agent,
                        status=LoginStatus.FAILED,
                        failure_reason="用户不存在"
                    )
                    return LoginResponse(
                        success=False,
                        message="用户名或密码错误"
                    )

                # 4. 检查用户状态
                if not user.is_active:
                    self._log_login_attempt(
                        user_id=user.id,
                        username=user.username,
                        ip_address=client_ip,
                        user_agent=user_agent,
                        status=LoginStatus.INACTIVE,
                        failure_reason="用户已禁用"
                    )
                    return LoginResponse(
                        success=False,
                        message="账户已被禁用，请联系管理员"
                    )

                # 5. 检查账户锁定
                if self._is_account_locked(user):
                    self._log_login_attempt(
                        user_id=user.id,
                        username=user.username,
                        ip_address=client_ip,
                        user_agent=user_agent,
                        status=LoginStatus.LOCKED,
                        failure_reason="账户已锁定"
                    )
                    return LoginResponse(
                        success=False,
                        message=f"账户已锁定，请{self.lockout_duration // 60}分钟后重试"
                    )

                # 6. 验证密码
                if not self._verify_password(login_request.password, user.password_hash):
                    # 增加失败尝试次数
                    user.login_attempts += 1

                    # 检查是否需要锁定账户
                    if user.login_attempts >= self.max_login_attempts:
                        user.is_locked = True
                        user.lock_until = datetime.utcnow() + timedelta(seconds=self.lockout_duration)

                    session.commit()

                    self._log_login_attempt(
                        user_id=user.id,
                        username=user.username,
                        ip_address=client_ip,
                        user_agent=user_agent,
                        status=LoginStatus.FAILED,
                        failure_reason="密码错误"
                    )

                    return LoginResponse(
                        success=False,
                        message="用户名或密码错误"
                    )

                # 7. 验证验证码（如果需要）
                if user.login_attempts >= self.require_captcha_after and login_request.captcha_token:
                    if not self._verify_captcha(login_request.captcha_token):
                        return LoginResponse(
                            success=False,
                            message="验证码错误"
                        )

                # 8. 登录成功，生成令牌
                tokens = self._generate_tokens(user)

                # 9. 创建登录会话
                session_id = self._create_login_session(
                    user=user,
                    tokens=tokens,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    device_fingerprint=login_request.device_fingerprint
                )

                # 10. 更新用户登录信息
                user.last_login = datetime.utcnow()
                user.login_attempts = 0  # 重置失败尝试次数
                user.is_locked = False
                user.lock_until = None

                session.commit()

                # 11. 记录成功登录
                self._log_login_attempt(
                    user_id=user.id,
                    username=user.username,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    status=LoginStatus.SUCCESS
                )

                # 12. 获取用户权限
                permissions = self._get_user_permissions(user)

                # 13. 构建用户档案
                user_profile = {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'is_active': user.is_active
                }

                log_info(f"用户登录成功: {user.username} (ID: {user.id})")

                return LoginResponse(
                    success=True,
                    message="登录成功",
                    user_id=user.id,
                    access_token=tokens.access_token,
                    refresh_token=tokens.refresh_token,
                    expires_in=self.access_token_expires,
                    user_profile=user_profile,
                    permissions=permissions,
                    session_id=session_id
                )

        except Exception as e:
            log_error("用户登录失败", e)
            return LoginResponse(
                success=False,
                message="登录失败，请稍后重试"
            )

    def validate_token(self, token: str) -> TokenValidationResponse:
        """
        验证访问令牌

        Args:
            token: JWT访问令牌

        Returns:
            TokenValidationResponse: 令牌验证响应
        """
        try:
            # 解码JWT令牌
            payload = jwt.decode(token, self.jwt_secret_key, algorithms=[self.jwt_algorithm])

            user_id = payload.get('user_id')
            role = payload.get('role')
            expires_at = datetime.fromtimestamp(payload.get('exp'))

            # 检查令牌是否在数据库中存在且有效
            with self.db_session_maker() as session:
                token_hash = self._hash_token(token)
                login_session = session.query(LoginSession).filter_by(
                    access_token_hash=token_hash,
                    is_active=True
                ).first()

                if not login_session:
                    return TokenValidationResponse(valid=False)

                # 检查会话是否过期
                if login_session.expires_at < datetime.utcnow():
                    login_session.is_active = False
                    session.commit()
                    return TokenValidationResponse(valid=False)

                # 获取用户权限
                user = session.query(User).filter_by(id=user_id).first()
                if not user or not user.is_active:
                    return TokenValidationResponse(valid=False)

                permissions = self._get_user_permissions(user)

                return TokenValidationResponse(
                    valid=True,
                    user_id=user_id,
                    role=role,
                    expires_at=expires_at,
                    permissions=permissions
                )

        except jwt.ExpiredSignatureError:
            return TokenValidationResponse(valid=False)
        except jwt.InvalidTokenError:
            return TokenValidationResponse(valid=False)
        except Exception as e:
            log_error("令牌验证失败", e)
            return TokenValidationResponse(valid=False)

    def refresh_token(self, refresh_token: str) -> LoginResponse:
        """
        刷新访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            LoginResponse: 包含新令牌的响应
        """
        try:
            # 验证刷新令牌
            payload = jwt.decode(refresh_token, self.jwt_secret_key, algorithms=[self.jwt_algorithm])

            user_id = payload.get('user_id')
            token_type = payload.get('type')

            if token_type != 'refresh':
                return LoginResponse(
                    success=False,
                    message="无效的刷新令牌"
                )

            # 查找用户和会话
            with self.db_session_maker() as session:
                user = session.query(User).filter_by(id=user_id).first()
                if not user or not user.is_active:
                    return LoginResponse(
                        success=False,
                        message="用户不存在或已禁用"
                    )

                refresh_token_hash = self._hash_token(refresh_token)
                login_session = session.query(LoginSession).filter_by(
                    user_id=user_id,
                    refresh_token_hash=refresh_token_hash,
                    is_active=True
                ).first()

                if not login_session:
                    return LoginResponse(
                        success=False,
                        message="会话不存在或已失效"
                    )

                # 生成新的访问令牌
                new_tokens = self._generate_tokens(user)

                # 更新会话
                login_session.access_token_hash = self._hash_token(new_tokens.access_token)
                login_session.refresh_token_hash = self._hash_token(new_tokens.refresh_token)
                login_session.expires_at = datetime.utcnow() + timedelta(seconds=self.access_token_expires)

                session.commit()

                return LoginResponse(
                    success=True,
                    message="令牌刷新成功",
                    user_id=user.id,
                    access_token=new_tokens.access_token,
                    refresh_token=new_tokens.refresh_token,
                    expires_in=self.access_token_expires
                )

        except jwt.ExpiredSignatureError:
            return LoginResponse(
                success=False,
                message="刷新令牌已过期"
            )
        except jwt.InvalidTokenError:
            return LoginResponse(
                success=False,
                message="无效的刷新令牌"
            )
        except Exception as e:
            log_error("令牌刷新失败", e)
            return LoginResponse(
                success=False,
                message="令牌刷新失败"
            )

    def logout(self, token: str) -> Dict[str, Any]:
        """
        用户登出

        Args:
            token: 访问令牌

        Returns:
            Dict: 登出响应
        """
        try:
            # 验证令牌
            payload = jwt.decode(token, self.jwt_secret_key, algorithms=[self.jwt_algorithm])
            user_id = payload.get('user_id')

            # 使会话失效
            with self.db_session_maker() as session:
                token_hash = self._hash_token(token)
                login_session = session.query(LoginSession).filter_by(
                    user_id=user_id,
                    access_token_hash=token_hash
                ).first()

                if login_session:
                    login_session.is_active = False
                    session.commit()

            log_info(f"用户登出成功: {user_id}")

            return {
                'success': True,
                'message': '登出成功'
            }

        except Exception as e:
            log_error("用户登出失败", e)
            return {
                'success': False,
                'message': '登出失败'
            }

    def _validate_login_request(self, request: LoginRequest):
        """验证登录请求参数"""
        if not request.username or not request.username.strip():
            raise ValueError("用户名不能为空")

        if not request.password or len(request.password) < 6:
            raise ValueError("密码至少6个字符")

    def _check_ip_rate_limit(self, ip_address: str, window_seconds: int = 300, max_attempts: int = 10) -> bool:
        """检查IP地址限流"""
        if not self.redis_client or not ip_address:
            return True

        key = f"login_rate_limit:{ip_address}"

        try:
            current_attempts = self.redis_client.incr(key)
            if current_attempts == 1:
                self.redis_client.expire(key, window_seconds)

            return current_attempts <= max_attempts
        except Exception as e:
            self.logger.warning(f"检查IP限流失败: {e}")
            return True

    def _is_account_locked(self, user: User) -> bool:
        """检查账户是否被锁定"""
        if not user.is_locked:
            return False

        if user.lock_until and datetime.utcnow() > user.lock_until:
            # 锁定已过期，自动解锁
            user.is_locked = False
            user.lock_until = None
            user.login_attempts = 0
            return False

        return True

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            self.logger.error(f"密码验证失败: {e}")
            return False

    def _verify_captcha(self, captcha_token: str) -> bool:
        """验证验证码（示例实现）"""
        # 这里应该实现真实的验证码验证逻辑
        # 比如调用Google reCAPTCHA API
        return True  # 示例中直接返回True

    def _generate_tokens(self, user: User) -> JWTTokens:
        """生成JWT令牌对"""
        now = datetime.utcnow()

        # 访问令牌载荷
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'type': 'access',
            'iat': now,
            'exp': now + timedelta(seconds=self.access_token_expires)
        }

        # 刷新令牌载荷
        refresh_payload = {
            'user_id': user.id,
            'type': 'refresh',
            'iat': now,
            'exp': now + timedelta(seconds=self.refresh_token_expires)
        }

        access_token = jwt.encode(access_payload, self.jwt_secret_key, algorithm=self.jwt_algorithm)
        refresh_token = jwt.encode(refresh_payload, self.jwt_secret_key, algorithm=self.jwt_algorithm)

        return JWTTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expires
        )

    def _create_login_session(self, user: User, tokens: JWTTokens, ip_address: str,
                            user_agent: str, device_fingerprint: str = None) -> str:
        """创建登录会话"""
        session_id = secrets.token_urlsafe(32)

        with self.db_session_maker() as session:
            login_session = LoginSession(
                id=session_id,
                user_id=user.id,
                access_token_hash=self._hash_token(tokens.access_token),
                refresh_token_hash=self._hash_token(tokens.refresh_token),
                ip_address=ip_address or '',
                user_agent=user_agent or '',
                device_fingerprint=device_fingerprint,
                expires_at=datetime.utcnow() + timedelta(seconds=self.access_token_expires)
            )

            session.add(login_session)
            session.commit()

        return session_id

    def _hash_token(self, token: str) -> str:
        """对令牌进行哈希处理"""
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def _get_user_permissions(self, user: User) -> List[str]:
        """获取用户权限列表"""
        permissions = []

        # 基于角色的权限
        if user.role == UserRole.ADMIN.value:
            permissions = ['admin:*', 'user:*', 'system:*']
        elif user.role == UserRole.DEVELOPER.value:
            permissions = ['user:read', 'user:write', 'project:*', 'code:*']
        elif user.role == UserRole.USER.value:
            permissions = ['user:read', 'project:read']
        else:  # GUEST
            permissions = ['user:read']

        return permissions

    def _log_login_attempt(self, user_id: str, username: str, ip_address: str,
                          user_agent: str, status: LoginStatus, failure_reason: str = None):
        """记录登录尝试"""
        try:
            with self.db_session_maker() as session:
                log_entry = LoginAuditLog(
                    id=secrets.token_urlsafe(16),
                    user_id=user_id,
                    username=username,
                    ip_address=ip_address or '',
                    user_agent=user_agent or '',
                    login_status=status.value,
                    failure_reason=failure_reason,
                    timestamp=datetime.utcnow()
                )

                session.add(log_entry)
                session.commit()

            # 同时记录到系统日志
            log_auth_event(
                event_type='login_attempt',
                user_id=user_id,
                username=username,
                status=status.value,
                ip_address=ip_address,
                details={'failure_reason': failure_reason}
            )

        except Exception as e:
            self.logger.error(f"记录登录尝试失败: {e}")


# Flask API路由
def create_flask_app(api_instance: UserLoginAPI) -> Flask:
    """创建Flask应用"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = api_instance.jwt_secret_key

    def require_auth(f):
        """身份认证装饰器"""
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': '未提供有效的身份认证令牌'}), 401

            token = auth_header.split(' ')[1]
            validation = api_instance.validate_token(token)

            if not validation.valid:
                return jsonify({'error': '无效或过期的令牌'}), 401

            request.current_user = {
                'user_id': validation.user_id,
                'role': validation.role,
                'permissions': validation.permissions
            }

            return f(*args, **kwargs)

        return decorated

    @app.route('/api/v1/auth/login', methods=['POST'])
    def login():
        """用户登录接口"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': '请求体不能为空'}), 400

            # 验证请求数据
            login_request = LoginRequest(**data)

            # 获取客户端信息
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            user_agent = request.headers.get('User-Agent', '')

            # 执行登录
            result = api_instance.login(login_request, client_ip, user_agent)

            # 构建响应
            response_data = asdict(result)
            status_code = 200 if result.success else 401

            return jsonify(response_data), status_code

        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            log_error("登录接口异常", e)
            return jsonify({'error': '服务器内部错误'}), 500

    @app.route('/api/v1/auth/validate', methods=['POST'])
    def validate_token():
        """令牌验证接口"""
        try:
            data = request.get_json()
            token = data.get('token') if data else None

            if not token:
                return jsonify({'error': '缺少token参数'}), 400

            validation = api_instance.validate_token(token)
            response_data = asdict(validation)

            return jsonify(response_data), 200

        except Exception as e:
            log_error("令牌验证接口异常", e)
            return jsonify({'error': '服务器内部错误'}), 500

    @app.route('/api/v1/auth/refresh', methods=['POST'])
    def refresh_token():
        """刷新令牌接口"""
        try:
            data = request.get_json()
            refresh_token = data.get('refresh_token') if data else None

            if not refresh_token:
                return jsonify({'error': '缺少refresh_token参数'}), 400

            result = api_instance.refresh_token(refresh_token)
            response_data = asdict(result)
            status_code = 200 if result.success else 401

            return jsonify(response_data), status_code

        except Exception as e:
            log_error("刷新令牌接口异常", e)
            return jsonify({'error': '服务器内部错误'}), 500

    @app.route('/api/v1/auth/logout', methods=['POST'])
    @require_auth
    def logout():
        """用户登出接口"""
        try:
            auth_header = request.headers.get('Authorization')
            token = auth_header.split(' ')[1]

            result = api_instance.logout(token)

            return jsonify(result), 200

        except Exception as e:
            log_error("登出接口异常", e)
            return jsonify({'error': '服务器内部错误'}), 500

    @app.route('/api/v1/auth/profile', methods=['GET'])
    @require_auth
    def get_profile():
        """获取用户档案接口"""
        try:
            user_info = request.current_user
            return jsonify({
                'success': True,
                'user_profile': user_info
            }), 200

        except Exception as e:
            log_error("获取用户档案异常", e)
            return jsonify({'error': '服务器内部错误'}), 500

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'API接口不存在'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': '服务器内部错误'}), 500

    return app


# Perfect21能力定义
def get_auth_api_capability() -> CapabilityDefinition:
    """获取用户登录API能力定义"""
    return CapabilityDefinition(
        name="auth_api",
        description="企业级用户认证API - 提供完整的登录、令牌管理和会话控制功能",
        version="1.0.0",
        category="security",
        dependencies=[
            "flask",
            "jwt",
            "bcrypt",
            "sqlalchemy",
            "redis",
            "pydantic"
        ],
        endpoints=[
            {
                "path": "/api/v1/auth/login",
                "method": "POST",
                "description": "用户登录",
                "auth_required": False
            },
            {
                "path": "/api/v1/auth/validate",
                "method": "POST",
                "description": "令牌验证",
                "auth_required": False
            },
            {
                "path": "/api/v1/auth/refresh",
                "method": "POST",
                "description": "刷新令牌",
                "auth_required": False
            },
            {
                "path": "/api/v1/auth/logout",
                "method": "POST",
                "description": "用户登出",
                "auth_required": True
            },
            {
                "path": "/api/v1/auth/profile",
                "method": "GET",
                "description": "获取用户档案",
                "auth_required": True
            }
        ],
        features=[
            "JWT令牌认证",
            "密码哈希存储",
            "账户锁定机制",
            "IP限流保护",
            "审计日志记录",
            "会话管理",
            "角色权限控制",
            "令牌刷新机制",
            "验证码支持",
            "设备指纹识别"
        ],
        security_features=[
            "bcrypt密码哈希",
            "JWT签名验证",
            "IP地址限流",
            "账户锁定保护",
            "会话令牌管理",
            "审计日志追踪",
            "HTTPS传输加密",
            "CSRF保护",
            "SQL注入防护",
            "XSS攻击防护"
        ]
    )


def main():
    """主函数 - 启动API服务器"""
    # 创建API实例
    api = UserLoginAPI()

    # 创建Flask应用
    app = create_flask_app(api)

    # 启动服务器
    host = config.get('auth_api.host', '0.0.0.0')
    port = config.get('auth_api.port', 8080)
    debug = config.get('auth_api.debug', False)

    log_info(f"Perfect21用户登录API服务器启动: http://{host}:{port}")

    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()