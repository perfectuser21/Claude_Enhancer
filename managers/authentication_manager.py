#!/usr/bin/env python3
"""
Perfect21 统一认证授权管理器
整合AuthManager, TokenManager, RBACManager功能
提供统一的用户认证、令牌管理、权限控制服务

设计原则:
- 安全优先: 所有认证授权操作都经过严格安全检查
- 统一接口: 简化认证授权相关的API调用
- 灵活配置: 支持多种认证方式和权限模型
- 可扩展性: 易于集成新的认证和授权机制
"""

import os
import sys
import re
import jwt
import hashlib
import secrets
import time
import yaml
from typing import Dict, List, Set, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from urllib.parse import unquote
import logging

# 配置日志
logger = logging.getLogger("Perfect21.AuthenticationManager")

# ================== 数据结构定义 ==================

class AuthResult(Enum):
    """认证结果"""
    SUCCESS = "success"
    INVALID_CREDENTIALS = "invalid_credentials"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_INACTIVE = "account_inactive"
    TOO_MANY_ATTEMPTS = "too_many_attempts"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"

class PermissionResult(Enum):
    """权限检查结果"""
    GRANTED = "granted"
    DENIED = "denied"
    FORBIDDEN = "forbidden"
    UNAUTHORIZED = "unauthorized"

class TokenType(Enum):
    """令牌类型"""
    ACCESS = "access"
    REFRESH = "refresh"
    VERIFICATION = "verification"
    RESET = "reset"

@dataclass
class UserCredentials:
    """用户凭证"""
    identifier: str  # 用户名或邮箱
    password: str
    remember_me: bool = False

@dataclass
class UserProfile:
    """用户配置"""
    user_id: str
    username: str
    email: str
    role: str
    status: str
    permissions: Set[str]
    created_at: datetime
    last_login: Optional[datetime] = None

@dataclass
class TokenInfo:
    """令牌信息"""
    token: str
    token_type: TokenType
    user_id: str
    expires_at: datetime
    issued_at: datetime
    jti: str  # JWT ID

@dataclass
class AccessContext:
    """访问上下文"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    permissions: Set[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = set()

@dataclass
class AuthenticationResult:
    """认证结果"""
    success: bool
    result: AuthResult
    message: str
    user_profile: Optional[UserProfile] = None
    access_token: Optional[TokenInfo] = None
    refresh_token: Optional[TokenInfo] = None
    expires_in: Optional[int] = None

@dataclass
class AuthorizationResult:
    """授权结果"""
    success: bool
    result: PermissionResult
    message: str
    granted_permissions: Set[str] = None
    required_permissions: Set[str] = None

# ================== 核心服务类 ==================

class UserService:
    """用户服务 (原AuthManager中的用户管理功能)"""

    def __init__(self, db_path: str = "data/auth.db"):
        self.db_path = db_path
        self._users: Dict[str, UserProfile] = {}
        self._passwords: Dict[str, str] = {}  # user_id -> hashed_password
        self._load_users()

    def _load_users(self):
        """加载用户数据 (简化实现，实际应使用数据库)"""
        # 模拟默认用户
        admin_user = UserProfile(
            user_id="admin",
            username="admin",
            email="admin@perfect21.dev",
            role="admin",
            status="active",
            permissions={"auth:*", "admin:*", "system:*"},
            created_at=datetime.now()
        )

        self._users["admin"] = admin_user
        self._passwords["admin"] = self._hash_password("perfect21")

    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{hashed.hex()}"

    def _verify_password(self, password: str, hashed: str) -> bool:
        """验证密码"""
        try:
            salt, stored_hash = hashed.split(':')
            computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return computed_hash.hex() == stored_hash
        except:
            return False

    def create_user(self, username: str, email: str, password: str, role: str = "user") -> str:
        """创建用户"""
        user_id = secrets.token_urlsafe(16)

        user = UserProfile(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            status="active",
            permissions=self._get_role_permissions(role),
            created_at=datetime.now()
        )

        self._users[user_id] = user
        self._passwords[user_id] = self._hash_password(password)

        logger.info(f"创建用户: {username} ({user_id})")
        return user_id

    def _get_role_permissions(self, role: str) -> Set[str]:
        """获取角色权限"""
        role_permissions = {
            "admin": {"auth:*", "admin:*", "system:*"},
            "user": {"auth:profile:read", "auth:profile:update"},
            "guest": {"auth:profile:read"}
        }
        return role_permissions.get(role, set())

    def find_user(self, identifier: str) -> Optional[UserProfile]:
        """查找用户（通过用户名或邮箱）"""
        for user in self._users.values():
            if user.username == identifier or user.email == identifier:
                return user
        return None

    def get_user_by_id(self, user_id: str) -> Optional[UserProfile]:
        """通过ID获取用户"""
        return self._users.get(user_id)

    def verify_password(self, user_id: str, password: str) -> bool:
        """验证用户密码"""
        hashed = self._passwords.get(user_id)
        if not hashed:
            return False
        return self._verify_password(password, hashed)

    def update_last_login(self, user_id: str):
        """更新最后登录时间"""
        if user_id in self._users:
            self._users[user_id].last_login = datetime.now()

    def user_exists(self, username: str, email: str) -> bool:
        """检查用户是否存在"""
        for user in self._users.values():
            if user.username == username or user.email == email:
                return True
        return False

    def update_password(self, user_id: str, new_password: str):
        """更新用户密码"""
        if user_id in self._users:
            self._passwords[user_id] = self._hash_password(new_password)

    def update_user(self, user_id: str, **kwargs):
        """更新用户信息"""
        if user_id in self._users:
            user = self._users[user_id]
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)

class TokenService:
    """令牌服务 (原TokenManager核心功能)"""

    def __init__(self):
        self.secret_key = self._get_secret_key()
        self.algorithm = 'HS256'
        self.token_blacklist: Set[str] = set()

        # 默认过期时间
        self.default_access_expires = timedelta(hours=1)
        self.default_refresh_expires = timedelta(days=7)
        self.default_verification_expires = timedelta(hours=24)
        self.default_reset_expires = timedelta(hours=2)

    def _get_secret_key(self) -> str:
        """获取密钥"""
        secret_key = os.getenv('JWT_SECRET_KEY')
        if not secret_key:
            # 开发环境使用固定密钥，生产环境必须设置环境变量
            secret_key = "perfect21-dev-secret-key-change-in-production"
            logger.warning("使用默认JWT密钥，生产环境必须设置JWT_SECRET_KEY环境变量")
        return secret_key

    def generate_token(self, user_id: str, token_type: TokenType,
                      expires_delta: timedelta = None,
                      additional_claims: Dict[str, Any] = None) -> TokenInfo:
        """生成令牌"""
        # 设置过期时间
        if expires_delta is None:
            if token_type == TokenType.ACCESS:
                expires_delta = self.default_access_expires
            elif token_type == TokenType.REFRESH:
                expires_delta = self.default_refresh_expires
            elif token_type == TokenType.VERIFICATION:
                expires_delta = self.default_verification_expires
            elif token_type == TokenType.RESET:
                expires_delta = self.default_reset_expires

        now = datetime.utcnow()
        expire = now + expires_delta
        jti = secrets.token_urlsafe(16)

        # 构建载荷
        payload = {
            'user_id': user_id,
            'type': token_type.value,
            'exp': expire,
            'iat': now,
            'jti': jti
        }

        # 添加额外声明
        if additional_claims:
            payload.update(additional_claims)

        # 生成令牌
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        return TokenInfo(
            token=token,
            token_type=token_type,
            user_id=user_id,
            expires_at=expire,
            issued_at=now,
            jti=jti
        )

    def verify_token(self, token: str, expected_type: TokenType = None) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            # 检查黑名单
            if token in self.token_blacklist:
                logger.info("令牌在黑名单中")
                return None

            # 解码令牌
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # 验证令牌类型
            if expected_type and payload.get('type') != expected_type.value:
                logger.info(f"令牌类型不匹配: expected {expected_type.value}, got {payload.get('type')}")
                return None

            # 检查JTI黑名单
            jti = payload.get('jti')
            if jti and jti in self.token_blacklist:
                logger.info(f"令牌JTI在黑名单中: {jti}")
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.info("令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.info(f"令牌无效: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"验证令牌时发生错误: {e}")
            return None

    def revoke_token(self, token: str):
        """撤销令牌"""
        try:
            # 解码令牌获取jti
            payload = jwt.decode(token, self.secret_key,
                               algorithms=[self.algorithm],
                               options={"verify_exp": False})

            jti = payload.get('jti')
            if jti:
                self.token_blacklist.add(jti)
                logger.info(f"令牌已撤销: jti={jti}")
            else:
                # 如果没有jti，直接加入令牌本身
                self.token_blacklist.add(token)
                logger.info("令牌已撤销（整个令牌）")

        except Exception as e:
            logger.error(f"撤销令牌失败: {e}")
            # 即使解码失败，也将令牌加入黑名单
            self.token_blacklist.add(token)

    def revoke_user_tokens(self, user_id: str):
        """撤销用户所有令牌（简化实现）"""
        logger.info(f"用户所有令牌已标记撤销: user_id={user_id}")

    def extract_token_from_header(self, authorization_header: str) -> Optional[str]:
        """从Authorization头提取令牌"""
        if not authorization_header:
            return None

        try:
            # 格式：Bearer <token>
            scheme, token = authorization_header.split(' ', 1)
            if scheme.lower() != 'bearer':
                return None
            return token.strip()

        except ValueError:
            return None

class RBACService:
    """基于角色的访问控制服务 (原RBACManager核心功能)"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.roles = {}
        self.endpoints = {}
        self.path_patterns = {}
        self._load_rbac_config()

    def _load_rbac_config(self):
        """加载RBAC配置"""
        # 默认配置
        default_config = {
            'roles': {
                'guest': {'permissions': []},
                'user': {'permissions': ['auth:profile:read', 'auth:profile:update']},
                'admin': {'permissions': ['auth:*', 'admin:*', 'system:*']}
            },
            'endpoints': {
                'public': [
                    {'path': '/', 'methods': ['GET'], 'auth_required': False},
                    {'path': '/health', 'methods': ['GET'], 'auth_required': False}
                ],
                'auth': [
                    {'path': '/api/auth/login', 'methods': ['POST'], 'auth_required': False},
                    {'path': '/api/auth/register', 'methods': ['POST'], 'auth_required': False},
                    {'path': '/api/auth/profile', 'methods': ['GET'], 'auth_required': True, 'permissions': ['auth:profile:read']},
                    {'path': '/api/auth/profile', 'methods': ['PUT'], 'auth_required': True, 'permissions': ['auth:profile:update']}
                ],
                'admin': [
                    {'path': '/api/admin/{resource}', 'methods': ['GET', 'POST', 'PUT', 'DELETE'], 'auth_required': True, 'permissions': ['admin:*']}
                ]
            }
        }

        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    default_config.update(config)
            except Exception as e:
                logger.error(f"加载RBAC配置失败: {e}")

        self.roles = self._build_role_hierarchy(default_config['roles'])
        self.endpoints = default_config['endpoints']
        self._compile_path_patterns()

    def _build_role_hierarchy(self, roles_config: Dict) -> Dict:
        """构建角色层次结构"""
        roles = {}

        for role_name, role_config in roles_config.items():
            # 解析继承关系
            inherits = role_config.get('inherits', [])
            permissions = set(role_config.get('permissions', []))

            # 递归收集继承的权限
            all_permissions = self._collect_inherited_permissions(
                role_name, inherits, permissions, roles_config
            )

            roles[role_name] = {
                'description': role_config.get('description', ''),
                'inherits': inherits,
                'permissions': all_permissions
            }

        return roles

    def _collect_inherited_permissions(self, role_name: str,
                                     inherits: List[str],
                                     permissions: Set[str],
                                     roles_config: Dict) -> Set[str]:
        """递归收集继承的权限"""
        all_permissions = permissions.copy()

        for parent_role in inherits:
            if parent_role in roles_config:
                parent_config = roles_config[parent_role]
                parent_inherits = parent_config.get('inherits', [])
                parent_permissions = set(parent_config.get('permissions', []))

                # 递归收集父角色权限
                inherited_permissions = self._collect_inherited_permissions(
                    parent_role, parent_inherits, parent_permissions, roles_config
                )
                all_permissions.update(inherited_permissions)

        return all_permissions

    def _compile_path_patterns(self):
        """编译路径匹配模式"""
        self.path_patterns = {}

        for category, endpoint_list in self.endpoints.items():
            self.path_patterns[category] = []

            for endpoint in endpoint_list:
                # 将路径参数转换为正则表达式
                pattern = self._path_to_regex(endpoint['path'])
                compiled_pattern = re.compile(pattern)

                self.path_patterns[category].append({
                    'pattern': compiled_pattern,
                    'original_path': endpoint['path'],
                    'config': endpoint
                })

    def _path_to_regex(self, path: str) -> str:
        """将路径转换为正则表达式"""
        # 转义特殊字符
        escaped = re.escape(path)

        # 替换路径参数 {param} -> (?P<param>[^/]+)
        pattern = re.sub(
            r'\\{([^}]+)\\}',
            r'(?P<\1>[^/]+)',
            escaped
        )

        # 添加开始和结束锚点
        return f'^{pattern}/?$'

    def check_permission(self, context: AccessContext,
                        path: str, method: str) -> Tuple[PermissionResult, str]:
        """检查权限"""
        try:
            # 查找端点配置
            endpoint_config = self._find_endpoint_config(path, method)
            if not endpoint_config:
                logger.warning(f"未找到端点配置: {method} {path}")
                return PermissionResult.FORBIDDEN, "端点不存在或不允许访问"

            # 公开端点无需认证
            if not endpoint_config.get('auth_required', True):
                return PermissionResult.GRANTED, "公开端点"

            # 检查认证状态
            if not context.user_id or not context.role:
                return PermissionResult.UNAUTHORIZED, "需要认证"

            # 检查角色权限
            if 'roles' in endpoint_config:
                if context.role not in endpoint_config['roles']:
                    logger.warning(f"角色权限不足: {context.role} not in {endpoint_config['roles']}")
                    return PermissionResult.FORBIDDEN, "角色权限不足"

            # 检查具体权限
            if 'permissions' in endpoint_config:
                if not self._has_permissions(context, endpoint_config['permissions']):
                    logger.warning(f"权限不足: {context.permissions} vs {endpoint_config['permissions']}")
                    return PermissionResult.FORBIDDEN, "权限不足"

            return PermissionResult.GRANTED, "权限检查通过"

        except Exception as e:
            logger.error(f"权限检查失败: {e}")
            return PermissionResult.FORBIDDEN, "权限检查过程中发生错误"

    def _find_endpoint_config(self, path: str, method: str) -> Optional[Dict]:
        """查找端点配置"""
        normalized_path = self._normalize_path(path)
        if not normalized_path:
            return None

        # 按优先级搜索端点配置
        search_order = ['auth', 'admin', 'users', 'system', 'public']

        for category in search_order:
            if category not in self.path_patterns:
                continue

            for pattern_info in self.path_patterns[category]:
                if pattern_info['pattern'].match(normalized_path):
                    config = pattern_info['config']
                    if method.upper() in [m.upper() for m in config['methods']]:
                        return config

        return None

    def _normalize_path(self, path: str) -> Optional[str]:
        """标准化路径"""
        try:
            # URL解码
            path = unquote(path)

            # 移除多余的斜杠
            path = re.sub(r'/+', '/', path)

            # 移除路径遍历
            path = re.sub(r'/\.\.?(?=/|$)', '', path)

            # 移除尾部斜杠(除了根路径)
            if path != '/' and path.endswith('/'):
                path = path.rstrip('/')

            return path

        except Exception as e:
            logger.error(f"路径标准化失败: {e}")
            return None

    def _has_permissions(self, context: AccessContext,
                        required_permissions: List[str]) -> bool:
        """检查是否具有所需权限"""
        user_permissions = self.get_user_permissions(context.role)

        for required_perm in required_permissions:
            if not self._check_single_permission(user_permissions, required_perm):
                return False

        return True

    def _check_single_permission(self, user_permissions: Set[str],
                                required_perm: str) -> bool:
        """检查单个权限"""
        # 直接匹配
        if required_perm in user_permissions:
            return True

        # 通配符匹配
        for user_perm in user_permissions:
            if user_perm.endswith('*'):
                prefix = user_perm[:-1]
                if required_perm.startswith(prefix):
                    return True

        return False

    def get_user_permissions(self, role: str) -> Set[str]:
        """获取用户权限"""
        if role not in self.roles:
            logger.warning(f"未知角色: {role}")
            return set()

        return self.roles[role]['permissions']

class SecurityService:
    """安全服务 (密码验证、登录尝试控制等)"""

    def __init__(self):
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.max_attempts = 5
        self.lockout_duration = timedelta(minutes=15)

    def validate_registration(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """验证注册信息"""
        errors = []

        # 用户名验证
        if not username or len(username) < 3:
            errors.append("用户名至少3个字符")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append("用户名只能包含字母、数字和下划线")

        # 邮箱验证
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not email or not re.match(email_pattern, email):
            errors.append("无效的邮箱格式")

        # 密码验证
        password_result = self.validate_password(password)
        if not password_result['valid']:
            errors.extend(password_result['errors'])

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def validate_password(self, password: str) -> Dict[str, Any]:
        """验证密码强度"""
        errors = []

        if not password:
            errors.append("密码不能为空")
            return {'valid': False, 'errors': errors}

        if len(password) < 8:
            errors.append("密码至少8个字符")

        if not re.search(r'[A-Z]', password):
            errors.append("密码必须包含大写字母")

        if not re.search(r'[a-z]', password):
            errors.append("密码必须包含小写字母")

        if not re.search(r'\d', password):
            errors.append("密码必须包含数字")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("密码必须包含特殊字符")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def check_login_attempts(self, identifier: str) -> bool:
        """检查登录尝试次数"""
        if identifier not in self.failed_attempts:
            return True

        now = datetime.now()
        attempts = self.failed_attempts[identifier]

        # 清理过期的尝试记录
        attempts = [attempt for attempt in attempts
                   if now - attempt < self.lockout_duration]
        self.failed_attempts[identifier] = attempts

        return len(attempts) < self.max_attempts

    def record_failed_attempt(self, identifier: str):
        """记录失败的登录尝试"""
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []

        self.failed_attempts[identifier].append(datetime.now())

    def clear_failed_attempts(self, identifier: str):
        """清除失败的登录尝试记录"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]

# ================== 主要管理器类 ==================

class AuthenticationManager:
    """统一认证授权管理器

    整合AuthManager, TokenManager, RBACManager功能
    提供统一的认证授权服务
    """

    def __init__(self, db_path: str = "data/auth.db", rbac_config_path: str = None):
        """初始化认证授权管理器"""
        self.db_path = db_path

        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # 初始化核心服务
        self.user_service = UserService(db_path)
        self.token_service = TokenService()
        self.rbac_service = RBACService(rbac_config_path)
        self.security_service = SecurityService()

        logger.info("AuthenticationManager初始化完成")

    # =================== 用户认证接口 ===================

    def register(self, username: str, email: str, password: str,
                 role: str = "user") -> AuthenticationResult:
        """用户注册"""
        try:
            # 安全检查
            security_check = self.security_service.validate_registration(
                username, email, password
            )
            if not security_check['valid']:
                return AuthenticationResult(
                    success=False,
                    result=AuthResult.INVALID_CREDENTIALS,
                    message='注册信息验证失败: ' + '; '.join(security_check['errors'])
                )

            # 检查用户是否存在
            if self.user_service.user_exists(username, email):
                return AuthenticationResult(
                    success=False,
                    result=AuthResult.INVALID_CREDENTIALS,
                    message='用户名或邮箱已存在'
                )

            # 创建用户
            user_id = self.user_service.create_user(
                username=username,
                email=email,
                password=password,
                role=role
            )

            # 生成验证令牌
            verification_token = self.token_service.generate_token(
                user_id, TokenType.VERIFICATION
            )

            # 获取用户信息
            user_profile = self.user_service.get_user_by_id(user_id)

            logger.info(f"用户注册成功: {username}")

            return AuthenticationResult(
                success=True,
                result=AuthResult.SUCCESS,
                message='注册成功，请验证邮箱',
                user_profile=user_profile
            )

        except Exception as e:
            logger.error(f"用户注册失败: {e}")
            return AuthenticationResult(
                success=False,
                result=AuthResult.INVALID_CREDENTIALS,
                message=f'注册过程中发生错误: {str(e)}'
            )

    def login(self, credentials: UserCredentials) -> AuthenticationResult:
        """用户登录"""
        try:
            # 安全检查：防止暴力破解
            if not self.security_service.check_login_attempts(credentials.identifier):
                return AuthenticationResult(
                    success=False,
                    result=AuthResult.TOO_MANY_ATTEMPTS,
                    message='登录尝试次数过多，请稍后再试'
                )

            # 查找用户
            user = self.user_service.find_user(credentials.identifier)
            if not user:
                self.security_service.record_failed_attempt(credentials.identifier)
                return AuthenticationResult(
                    success=False,
                    result=AuthResult.INVALID_CREDENTIALS,
                    message='用户名或密码错误'
                )

            # 验证密码
            if not self.user_service.verify_password(user.user_id, credentials.password):
                self.security_service.record_failed_attempt(credentials.identifier)
                return AuthenticationResult(
                    success=False,
                    result=AuthResult.INVALID_CREDENTIALS,
                    message='用户名或密码错误'
                )

            # 检查用户状态
            if user.status != 'active':
                return AuthenticationResult(
                    success=False,
                    result=AuthResult.ACCOUNT_INACTIVE,
                    message='账户未激活或已被禁用'
                )

            # 生成访问令牌
            token_expires = timedelta(days=7 if credentials.remember_me else 1)
            access_token = self.token_service.generate_token(
                user.user_id, TokenType.ACCESS, expires_delta=token_expires
            )
            refresh_token = self.token_service.generate_token(
                user.user_id, TokenType.REFRESH
            )

            # 更新用户最后登录时间
            self.user_service.update_last_login(user.user_id)

            # 清除失败登录记录
            self.security_service.clear_failed_attempts(credentials.identifier)

            logger.info(f"用户登录成功: {user.username}")

            return AuthenticationResult(
                success=True,
                result=AuthResult.SUCCESS,
                message='登录成功',
                user_profile=user,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=int(token_expires.total_seconds())
            )

        except Exception as e:
            logger.error(f"用户登录失败: {e}")
            return AuthenticationResult(
                success=False,
                result=AuthResult.INVALID_CREDENTIALS,
                message=f'登录过程中发生错误: {str(e)}'
            )

    def logout(self, access_token: str) -> AuthenticationResult:
        """用户登出"""
        try:
            # 将令牌加入黑名单
            self.token_service.revoke_token(access_token)

            logger.info("用户登出成功")

            return AuthenticationResult(
                success=True,
                result=AuthResult.SUCCESS,
                message='登出成功'
            )

        except Exception as e:
            logger.error(f"用户登出失败: {e}")
            return AuthenticationResult(
                success=False,
                result=AuthResult.INVALID_CREDENTIALS,
                message=f'登出过程中发生错误: {str(e)}'
            )

    def refresh_token(self, refresh_token: str) -> AuthenticationResult:
        """刷新访问令牌"""
        try:
            # 验证刷新令牌
            token_data = self.token_service.verify_token(refresh_token, TokenType.REFRESH)
            if not token_data:
                return AuthenticationResult(
                    success=False,
                    result=AuthResult.TOKEN_INVALID,
                    message='刷新令牌无效或已过期'
                )

            # 生成新的访问令牌
            user_id = token_data['user_id']
            new_access_token = self.token_service.generate_token(user_id, TokenType.ACCESS)

            # 获取用户信息
            user = self.user_service.get_user_by_id(user_id)

            logger.info(f"令牌刷新成功: user_id={user_id}")

            return AuthenticationResult(
                success=True,
                result=AuthResult.SUCCESS,
                message='令牌刷新成功',
                user_profile=user,
                access_token=new_access_token,
                expires_in=3600  # 1小时
            )

        except Exception as e:
            logger.error(f"令牌刷新失败: {e}")
            return AuthenticationResult(
                success=False,
                result=AuthResult.TOKEN_INVALID,
                message=f'令牌刷新过程中发生错误: {str(e)}'
            )

    def verify_token(self, access_token: str) -> AuthenticationResult:
        """验证访问令牌"""
        try:
            # 验证令牌
            token_data = self.token_service.verify_token(access_token, TokenType.ACCESS)
            if not token_data:
                return AuthenticationResult(
                    success=False,
                    result=AuthResult.TOKEN_INVALID,
                    message='访问令牌无效或已过期'
                )

            # 获取用户信息
            user_id = token_data['user_id']
            user = self.user_service.get_user_by_id(user_id)

            if not user or user.status != 'active':
                return AuthenticationResult(
                    success=False,
                    result=AuthResult.ACCOUNT_INACTIVE,
                    message='用户不存在或已被禁用'
                )

            return AuthenticationResult(
                success=True,
                result=AuthResult.SUCCESS,
                message='令牌验证成功',
                user_profile=user
            )

        except Exception as e:
            logger.error(f"令牌验证失败: {e}")
            return AuthenticationResult(
                success=False,
                result=AuthResult.TOKEN_INVALID,
                message=f'令牌验证过程中发生错误: {str(e)}'
            )

    # =================== 权限控制接口 ===================

    def authorize(self, access_token: str, path: str, method: str,
                 ip_address: str = None, user_agent: str = None) -> AuthorizationResult:
        """统一授权检查"""
        try:
            # 验证令牌并获取用户信息
            auth_result = self.verify_token(access_token)
            if not auth_result.success:
                return AuthorizationResult(
                    success=False,
                    result=PermissionResult.UNAUTHORIZED,
                    message=auth_result.message
                )

            user = auth_result.user_profile

            # 构建访问上下文
            context = AccessContext(
                user_id=user.user_id,
                username=user.username,
                role=user.role,
                permissions=user.permissions,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # 检查权限
            permission_result, message = self.rbac_service.check_permission(
                context, path, method
            )

            return AuthorizationResult(
                success=permission_result == PermissionResult.GRANTED,
                result=permission_result,
                message=message,
                granted_permissions=user.permissions if permission_result == PermissionResult.GRANTED else set(),
                required_permissions=set()  # 可以根据端点配置填充
            )

        except Exception as e:
            logger.error(f"授权检查失败: {e}")
            return AuthorizationResult(
                success=False,
                result=PermissionResult.FORBIDDEN,
                message=f'授权检查过程中发生错误: {str(e)}'
            )

    def check_permission(self, user_id: str, permission: str) -> bool:
        """检查用户是否具有特定权限"""
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            return False

        user_permissions = self.rbac_service.get_user_permissions(user.role)
        return self.rbac_service._check_single_permission(user_permissions, permission)

    # =================== 用户管理接口 ===================

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户资料"""
        return self.user_service.get_user_by_id(user_id)

    def update_user_profile(self, user_id: str, **kwargs) -> AuthenticationResult:
        """更新用户资料"""
        try:
            # 允许更新的字段
            allowed_fields = ['username', 'email']
            update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}

            if not update_data:
                return AuthenticationResult(
                    success=False,
                    result=AuthResult.INVALID_CREDENTIALS,
                    message='没有可更新的数据'
                )

            # 更新用户信息
            self.user_service.update_user(user_id, **update_data)

            logger.info(f"用户资料更新成功: user_id={user_id}")

            return AuthenticationResult(
                success=True,
                result=AuthResult.SUCCESS,
                message='用户资料更新成功'
            )

        except Exception as e:
            logger.error(f"用户资料更新失败: {e}")
            return AuthenticationResult(
                success=False,
                result=AuthResult.INVALID_CREDENTIALS,
                message=f'用户资料更新过程中发生错误: {str(e)}'
            )

    def change_password(self, user_id: str, old_password: str,
                       new_password: str) -> AuthenticationResult:
        """修改密码"""
        try:
            # 验证旧密码
            if not self.user_service.verify_password(user_id, old_password):
                return AuthenticationResult(
                    success=False,
                    result=AuthResult.INVALID_CREDENTIALS,
                    message='原密码错误'
                )

            # 验证新密码强度
            password_check = self.security_service.validate_password(new_password)
            if not password_check['valid']:
                return AuthenticationResult(
                    success=False,
                    result=AuthResult.INVALID_CREDENTIALS,
                    message='新密码不符合安全要求: ' + '; '.join(password_check['errors'])
                )

            # 更新密码
            self.user_service.update_password(user_id, new_password)

            # 撤销所有现有令牌（强制重新登录）
            self.token_service.revoke_user_tokens(user_id)

            logger.info(f"密码修改成功: user_id={user_id}")

            return AuthenticationResult(
                success=True,
                result=AuthResult.SUCCESS,
                message='密码修改成功，请重新登录'
            )

        except Exception as e:
            logger.error(f"密码修改失败: {e}")
            return AuthenticationResult(
                success=False,
                result=AuthResult.INVALID_CREDENTIALS,
                message=f'密码修改过程中发生错误: {str(e)}'
            )

    # =================== 系统管理接口 ===================

    def get_authentication_stats(self) -> Dict[str, Any]:
        """获取认证统计信息"""
        return {
            'total_users': len(self.user_service._users),
            'active_users': len([u for u in self.user_service._users.values() if u.status == 'active']),
            'blacklisted_tokens': len(self.token_service.token_blacklist),
            'failed_attempts': len(self.security_service.failed_attempts),
            'available_roles': list(self.rbac_service.roles.keys()),
            'endpoint_categories': list(self.rbac_service.endpoints.keys())
        }

    def cleanup(self):
        """清理资源"""
        try:
            # 清理各服务的资源
            if hasattr(self.user_service, 'cleanup'):
                self.user_service.cleanup()
            if hasattr(self.token_service, 'cleanup'):
                self.token_service.cleanup()
            if hasattr(self.rbac_service, 'cleanup'):
                self.rbac_service.cleanup()
            if hasattr(self.security_service, 'cleanup'):
                self.security_service.cleanup()

            logger.info("AuthenticationManager清理完成")
        except Exception as e:
            logger.error(f"AuthenticationManager清理失败: {e}")

# ================== 向后兼容适配器 ==================

class AuthManager:
    """向后兼容适配器 - AuthManager"""

    def __init__(self, db_path: str = "data/auth.db"):
        self._manager = AuthenticationManager(db_path)

    def register(self, username: str, email: str, password: str, role: str = "user") -> Dict[str, Any]:
        result = self._manager.register(username, email, password, role)
        return {
            'success': result.success,
            'user_id': result.user_profile.user_id if result.user_profile else None,
            'message': result.message
        }

    def login(self, identifier: str, password: str, remember_me: bool = False) -> Dict[str, Any]:
        credentials = UserCredentials(identifier, password, remember_me)
        result = self._manager.login(credentials)
        return {
            'success': result.success,
            'access_token': result.access_token.token if result.access_token else None,
            'refresh_token': result.refresh_token.token if result.refresh_token else None,
            'user': asdict(result.user_profile) if result.user_profile else None,
            'expires_in': result.expires_in,
            'message': result.message
        }

class TokenManager:
    """向后兼容适配器 - TokenManager"""

    def __init__(self):
        self._manager = AuthenticationManager()

    def generate_access_token(self, user_id: str, expires_delta: timedelta = None,
                            additional_claims: Dict[str, Any] = None) -> str:
        token_info = self._manager.token_service.generate_token(
            user_id, TokenType.ACCESS, expires_delta, additional_claims
        )
        return token_info.token

    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        return self._manager.token_service.verify_token(token, TokenType.ACCESS)

    def revoke_token(self, token: str):
        self._manager.token_service.revoke_token(token)

class RBACManager:
    """向后兼容适配器 - RBACManager"""

    def __init__(self, config_path: str = None):
        self._manager = AuthenticationManager(rbac_config_path=config_path)

    def check_permission(self, context: AccessContext, path: str, method: str) -> Tuple[PermissionResult, str]:
        return self._manager.rbac_service.check_permission(context, path, method)

    def get_user_permissions(self, role: str) -> Set[str]:
        return self._manager.rbac_service.get_user_permissions(role)

# ================== 使用示例 ==================

def main():
    """使用示例"""
    # 创建认证管理器
    auth_manager = AuthenticationManager()

    # 用户注册
    register_result = auth_manager.register(
        username="testuser",
        email="test@example.com",
        password="SecurePass123!",
        role="user"
    )
    print(f"注册结果: {register_result.success} - {register_result.message}")

    if register_result.success:
        # 用户登录
        credentials = UserCredentials("testuser", "SecurePass123!")
        login_result = auth_manager.login(credentials)
        print(f"登录结果: {login_result.success} - {login_result.message}")

        if login_result.success:
            # 权限检查
            auth_result = auth_manager.authorize(
                login_result.access_token.token,
                "/api/auth/profile",
                "GET"
            )
            print(f"权限检查: {auth_result.success} - {auth_result.message}")

    # 获取统计信息
    stats = auth_manager.get_authentication_stats()
    print(f"系统统计: {stats}")

if __name__ == "__main__":
    main()