# 🏗️ Claude Enhancer 企业级认证系统后端架构设计

## 📋 文档信息
- **项目名称**: Claude Enhancer 企业级认证系统
- **架构版本**: v2.0
- **创建日期**: 2025-09-22
- **架构师**: 8-Agent协同设计团队
- **文档状态**: 技术方案

---

## 🎯 1. 架构概览

### 1.1 整体架构图

```mermaid
graph TB
    subgraph "客户端层"
        A[Web应用]
        B[移动应用]
        C[第三方系统]
    end

    subgraph "API网关层"
        D[Kong/Istio网关]
        E[负载均衡器]
        F[SSL终端]
    end

    subgraph "微服务层"
        G[认证服务<br/>FastAPI]
        H[用户服务<br/>FastAPI]
        I[权限服务<br/>FastAPI]
        J[会话服务<br/>Go]
        K[通知服务<br/>Node.js]
    end

    subgraph "中间件层"
        L[Redis集群<br/>缓存/会话]
        M[RabbitMQ<br/>消息队列]
        N[Elasticsearch<br/>日志搜索]
    end

    subgraph "数据存储层"
        O[PostgreSQL主从<br/>用户/权限数据]
        P[MongoDB<br/>审计日志]
        Q[MinIO<br/>文件存储]
    end

    subgraph "基础设施层"
        R[Kubernetes集群]
        S[Prometheus监控]
        T[Grafana仪表板]
        U[Jaeger链路追踪]
    end

    A --> D
    B --> D
    C --> D
    D --> E
    E --> F
    F --> G
    F --> H
    F --> I
    F --> J
    F --> K

    G --> L
    H --> L
    I --> L
    J --> L

    G --> M
    H --> M
    I --> M

    G --> O
    H --> O
    I --> O

    G --> P
    H --> P
    I --> P

    R --> S
    S --> T
    R --> U
```

### 1.2 技术栈选择

| 层级 | 技术选择 | 理由 |
|------|----------|------|
| **API网关** | Kong + Istio | 企业级功能，支持插件扩展 |
| **认证服务** | Python FastAPI | 高性能异步，丰富的安全库 |
| **用户服务** | Python FastAPI | 与认证服务技术栈统一 |
| **权限服务** | Python FastAPI | 复杂权限逻辑，Python生态好 |
| **会话服务** | Go + Gin | 高并发性能，内存管理优秀 |
| **通知服务** | Node.js + Express | 实时通知，WebSocket支持好 |
| **主数据库** | PostgreSQL 15 | ACID事务，JSON支持，成熟稳定 |
| **缓存** | Redis Cluster | 高性能，支持多种数据结构 |
| **消息队列** | RabbitMQ | 可靠消息传递，易于管理 |
| **日志存储** | MongoDB + ELK | 文档存储，搜索性能好 |
| **容器编排** | Kubernetes | 企业级容器管理 |

---

## 🔐 2. 认证服务架构 (Authentication Service)

### 2.1 服务结构

```python
# /auth-service/app/
├── main.py                 # FastAPI应用入口
├── core/
│   ├── config.py          # 配置管理
│   ├── security.py        # 安全工具类
│   ├── dependencies.py    # 依赖注入
│   └── exceptions.py      # 自定义异常
├── models/
│   ├── auth_models.py     # 认证数据模型
│   ├── token_models.py    # Token模型
│   └── session_models.py  # 会话模型
├── schemas/
│   ├── auth_schemas.py    # 认证API模式
│   ├── token_schemas.py   # Token API模式
│   └── mfa_schemas.py     # MFA API模式
├── services/
│   ├── jwt_service.py     # JWT管理服务
│   ├── mfa_service.py     # 多因子认证服务
│   ├── password_service.py # 密码管理服务
│   └── oauth_service.py   # OAuth2服务
├── api/
│   ├── v1/
│   │   ├── auth.py        # 认证API路由
│   │   ├── tokens.py      # Token API路由
│   │   └── mfa.py         # MFA API路由
│   └── __init__.py
├── utils/
│   ├── crypto.py          # 加密工具
│   ├── validators.py      # 验证器
│   └── helpers.py         # 辅助函数
└── tests/
    ├── test_auth.py
    ├── test_tokens.py
    └── test_mfa.py
```

### 2.2 JWT Token管理架构

```python
# auth-service/app/services/jwt_service.py
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import redis
import json
import secrets

class JWTTokenManager:
    """企业级JWT Token管理器"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host='redis-cluster',
            port=6379,
            decode_responses=True,
            health_check_interval=30
        )
        self.access_token_ttl = 900  # 15分钟
        self.refresh_token_ttl = 604800  # 7天
        self.algorithm = "RS256"
        self.issuer = "perfect21-auth"
        self.audience = "perfect21-api"

    async def generate_token_pair(self, user_id: str, permissions: List[str],
                                device_info: Dict[str, Any]) -> Dict[str, Any]:
        """生成访问令牌和刷新令牌对"""

        current_time = datetime.utcnow()
        access_jti = secrets.token_urlsafe(32)
        refresh_jti = secrets.token_urlsafe(32)

        # 访问令牌负载
        access_payload = {
            "iss": self.issuer,
            "aud": self.audience,
            "sub": user_id,
            "iat": current_time,
            "exp": current_time + timedelta(seconds=self.access_token_ttl),
            "jti": access_jti,
            "scope": permissions,
            "device_fingerprint": self._generate_device_fingerprint(device_info),
            "token_type": "access"
        }

        # 刷新令牌负载
        refresh_payload = {
            "iss": self.issuer,
            "aud": self.audience,
            "sub": user_id,
            "iat": current_time,
            "exp": current_time + timedelta(seconds=self.refresh_token_ttl),
            "jti": refresh_jti,
            "token_type": "refresh"
        }

        # 获取当前私钥
        private_key = await self._get_current_private_key()

        # 生成Token
        access_token = jwt.encode(access_payload, private_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, private_key, algorithm=self.algorithm)

        # 存储Token元数据到Redis
        await self._store_token_metadata(access_jti, user_id, "access", self.access_token_ttl)
        await self._store_token_metadata(refresh_jti, user_id, "refresh", self.refresh_token_ttl)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": self.access_token_ttl,
            "scope": permissions
        }

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证Token有效性"""
        try:
            # 解码Token头部获取密钥ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            # 获取对应公钥
            public_key = await self._get_public_key(kid)

            # 验证Token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer
            )

            # 检查Token是否在黑名单
            jti = payload.get("jti")
            if await self._is_token_blacklisted(jti):
                return None

            # 检查Token元数据
            token_metadata = await self._get_token_metadata(jti)
            if not token_metadata or not token_metadata.get("active"):
                return None

            return payload

        except jwt.ExpiredSignatureError:
            await self._cleanup_expired_token(token)
            return None
        except jwt.InvalidTokenError:
            return None

    async def revoke_token(self, jti: str, reason: str = "user_request"):
        """撤销Token"""
        # 添加到黑名单
        await self.redis_client.sadd("token_blacklist", jti)

        # 更新Token元数据
        await self.redis_client.hset(
            f"token_metadata:{jti}",
            mapping={
                "active": "false",
                "revoked_at": datetime.utcnow().isoformat(),
                "revoke_reason": reason
            }
        )

        # 记录撤销事件
        await self._log_token_event("token_revoked", jti, {"reason": reason})

    async def rotate_keys(self):
        """密钥轮换"""
        # 生成新的RSA密钥对
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        # 序列化私钥和公钥
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # 生成密钥ID
        kid = f"key-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # 存储新密钥
        await self.redis_client.hset(
            "jwt_keys",
            mapping={
                f"private:{kid}": private_pem.decode(),
                f"public:{kid}": public_pem.decode(),
                "current_kid": kid
            }
        )

        # 设置旧密钥过期时间（24小时后）
        await self._schedule_key_cleanup(kid)

        await self._log_security_event("key_rotation", {"new_kid": kid})

    def _generate_device_fingerprint(self, device_info: Dict[str, Any]) -> str:
        """生成设备指纹"""
        fingerprint_data = {
            "user_agent": device_info.get("user_agent", ""),
            "screen_resolution": device_info.get("screen_resolution", ""),
            "timezone": device_info.get("timezone", ""),
            "language": device_info.get("language", ""),
            "platform": device_info.get("platform", "")
        }

        import hashlib
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()

    async def _store_token_metadata(self, jti: str, user_id: str,
                                  token_type: str, ttl: int):
        """存储Token元数据"""
        metadata = {
            "jti": jti,
            "user_id": user_id,
            "token_type": token_type,
            "active": "true",
            "created_at": datetime.utcnow().isoformat()
        }

        await self.redis_client.hset(f"token_metadata:{jti}", mapping=metadata)
        await self.redis_client.expire(f"token_metadata:{jti}", ttl)

        # 维护用户Token索引
        await self.redis_client.sadd(f"user_tokens:{user_id}", jti)
        await self.redis_client.expire(f"user_tokens:{user_id}", ttl)

    async def _get_current_private_key(self) -> bytes:
        """获取当前私钥"""
        kid = await self.redis_client.hget("jwt_keys", "current_kid")
        if not kid:
            await self.rotate_keys()
            kid = await self.redis_client.hget("jwt_keys", "current_kid")

        private_key_pem = await self.redis_client.hget("jwt_keys", f"private:{kid}")
        return serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None
        )
```

### 2.3 多因子认证架构

```python
# auth-service/app/services/mfa_service.py
import pyotp
import qrcode
import io
import base64
from typing import Dict, List, Optional
import secrets
import hashlib

class MFAService:
    """多因子认证服务"""

    def __init__(self):
        self.redis_client = redis.Redis(host='redis-cluster', port=6379)
        self.issuer = "Claude Enhancer"

    async def enable_totp(self, user_id: str, user_email: str) -> Dict[str, Any]:
        """启用TOTP认证"""

        # 生成共享密钥
        secret = pyotp.random_base32()

        # 创建TOTP对象
        totp = pyotp.TOTP(secret)

        # 生成QR码
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=self.issuer
        )

        # 生成QR码图片
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()

        # 生成备用恢复码
        recovery_codes = [secrets.token_hex(8) for _ in range(10)]

        # 存储MFA配置（待确认状态）
        mfa_config = {
            "user_id": user_id,
            "secret": secret,
            "recovery_codes": recovery_codes,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }

        await self.redis_client.setex(
            f"mfa_setup:{user_id}",
            3600,  # 1小时过期
            json.dumps(mfa_config)
        )

        return {
            "secret": secret,
            "qr_code": f"data:image/png;base64,{img_base64}",
            "recovery_codes": recovery_codes,
            "manual_entry_key": secret
        }

    async def verify_totp_setup(self, user_id: str, verification_code: str) -> bool:
        """验证TOTP设置"""

        # 获取待确认的MFA配置
        mfa_data = await self.redis_client.get(f"mfa_setup:{user_id}")
        if not mfa_data:
            return False

        mfa_config = json.loads(mfa_data)
        secret = mfa_config["secret"]

        # 验证验证码
        totp = pyotp.TOTP(secret)
        if not totp.verify(verification_code):
            return False

        # 保存MFA配置到数据库
        await self._save_mfa_config(user_id, mfa_config)

        # 清除临时配置
        await self.redis_client.delete(f"mfa_setup:{user_id}")

        return True

    async def verify_totp(self, user_id: str, verification_code: str) -> bool:
        """验证TOTP验证码"""

        # 获取用户MFA配置
        mfa_config = await self._get_user_mfa_config(user_id)
        if not mfa_config or not mfa_config.get("totp_enabled"):
            return False

        secret = mfa_config["totp_secret"]
        totp = pyotp.TOTP(secret)

        # 验证验证码（考虑时间偏移）
        for i in range(-1, 2):  # 允许±30秒时间偏移
            if totp.verify(verification_code, valid_window=i):
                return True

        return False

    async def verify_recovery_code(self, user_id: str, recovery_code: str) -> bool:
        """验证恢复码"""

        mfa_config = await self._get_user_mfa_config(user_id)
        if not mfa_config:
            return False

        recovery_codes = mfa_config.get("recovery_codes", [])

        # 哈希验证恢复码
        recovery_code_hash = hashlib.sha256(recovery_code.encode()).hexdigest()

        if recovery_code_hash in recovery_codes:
            # 移除已使用的恢复码
            recovery_codes.remove(recovery_code_hash)
            await self._update_mfa_config(user_id, {"recovery_codes": recovery_codes})
            return True

        return False

    async def send_sms_code(self, user_id: str, phone_number: str) -> bool:
        """发送短信验证码"""

        # 生成6位数字验证码
        verification_code = secrets.randbelow(999999)
        verification_code = f"{verification_code:06d}"

        # 存储验证码
        await self.redis_client.setex(
            f"sms_code:{user_id}",
            300,  # 5分钟过期
            verification_code
        )

        # 发送短信（集成短信服务商）
        sms_result = await self._send_sms(phone_number, verification_code)

        return sms_result

    async def verify_sms_code(self, user_id: str, verification_code: str) -> bool:
        """验证短信验证码"""

        stored_code = await self.redis_client.get(f"sms_code:{user_id}")
        if not stored_code:
            return False

        if stored_code == verification_code:
            # 删除已验证的验证码
            await self.redis_client.delete(f"sms_code:{user_id}")
            return True

        return False
```

---

## 👤 3. 用户服务架构 (User Service)

### 3.1 用户数据模型

```python
# user-service/app/models/user_models.py
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(Text, nullable=False)
    password_salt = Column(String(64), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)

    # 账户状态
    status = Column(String(20), nullable=False, default="pending_verification")
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)

    # MFA配置
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    totp_secret = Column(String(32), nullable=True)
    backup_codes = Column(JSON, nullable=True)

    # 安全信息
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)

    # 个人资料
    profile = Column(JSON, nullable=True)
    preferences = Column(JSON, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # 验证相关
    email_verification_token = Column(String(255), nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False)

    # 设备信息
    device_fingerprint = Column(String(64), nullable=False)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=False)
    location = Column(JSON, nullable=True)

    # 会话状态
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)

class UserLoginHistory(Base):
    __tablename__ = "user_login_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # 登录信息
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    location = Column(JSON, nullable=True)

    # 登录结果
    login_successful = Column(Boolean, nullable=False)
    failure_reason = Column(String(100), nullable=True)
    mfa_used = Column(Boolean, default=False)

    # 风险评估
    risk_score = Column(Float, nullable=True)
    risk_factors = Column(JSON, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

### 3.2 用户服务实现

```python
# user-service/app/services/user_service.py
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import secrets
import hashlib
from datetime import datetime, timedelta

class UserService:
    """用户管理服务"""

    def __init__(self, db: Session):
        self.db = db
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.pepper = "your-application-pepper"  # 从环境变量读取

    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """创建新用户"""

        # 检查邮箱唯一性
        existing_user = await self.get_user_by_email(user_data["email"])
        if existing_user:
            raise ValueError("邮箱已被注册")

        # 生成密码哈希
        salt = secrets.token_hex(32)
        password_hash = await self._hash_password(user_data["password"], salt)

        # 生成验证令牌
        verification_token = secrets.token_urlsafe(32)

        # 创建用户对象
        user = User(
            email=user_data["email"],
            username=user_data.get("username"),
            password_hash=password_hash,
            password_salt=salt,
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            phone_number=user_data.get("phone_number"),
            email_verification_token=verification_token,
            status="pending_verification"
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # 发送验证邮件
        await self._send_verification_email(user.email, verification_token)

        return user

    async def authenticate_user(self, email: str, password: str,
                              login_context: Dict[str, Any]) -> Optional[User]:
        """认证用户"""

        # 获取用户
        user = await self.get_user_by_email(email)
        if not user:
            # 防止用户枚举攻击
            await self._fake_password_verification()
            return None

        # 检查账户状态
        if user.is_locked:
            if user.locked_until and user.locked_until > datetime.utcnow():
                raise ValueError("账户已被锁定")
            else:
                # 解锁过期的账户
                await self.unlock_user(user.id)

        if not user.is_active:
            raise ValueError("账户已禁用")

        if not user.is_verified:
            raise ValueError("邮箱未验证")

        # 验证密码
        if not await self._verify_password(password, user.password_hash, user.password_salt):
            await self._record_failed_login(user, login_context)
            return None

        # 重置失败登录计数
        await self._reset_failed_login_attempts(user.id)

        # 记录成功登录
        await self._record_successful_login(user, login_context)

        return user

    async def change_password(self, user_id: str, old_password: str,
                            new_password: str) -> bool:
        """修改密码"""

        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        # 验证旧密码
        if not await self._verify_password(old_password, user.password_hash, user.password_salt):
            return False

        # 检查密码历史
        if await self._is_password_in_history(user_id, new_password):
            raise ValueError("不能重复使用最近的密码")

        # 生成新的盐值和哈希
        new_salt = secrets.token_hex(32)
        new_password_hash = await self._hash_password(new_password, new_salt)

        # 更新用户密码
        user.password_hash = new_password_hash
        user.password_salt = new_salt
        user.password_changed_at = datetime.utcnow()

        self.db.commit()

        # 保存密码历史
        await self._save_password_history(user_id, new_password_hash)

        # 撤销所有现有会话
        await self._revoke_all_user_sessions(user_id)

        return True

    async def _hash_password(self, password: str, salt: str) -> str:
        """密码哈希"""
        # 添加盐值和胡椒
        salted_password = password + salt + self.pepper

        # 使用bcrypt哈希
        return self.pwd_context.hash(salted_password)

    async def _verify_password(self, password: str, hash_value: str, salt: str) -> bool:
        """验证密码"""
        salted_password = password + salt + self.pepper
        return self.pwd_context.verify(salted_password, hash_value)

    async def _record_failed_login(self, user: User, login_context: Dict[str, Any]):
        """记录失败登录"""
        user.failed_login_attempts += 1

        # 登录失败超过阈值时锁定账户
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.utcnow() + timedelta(hours=1)

        self.db.commit()

        # 记录登录历史
        login_history = UserLoginHistory(
            user_id=user.id,
            ip_address=login_context.get("ip_address"),
            user_agent=login_context.get("user_agent"),
            location=login_context.get("location"),
            login_successful=False,
            failure_reason="invalid_password"
        )

        self.db.add(login_history)
        self.db.commit()
```

---

## 🔐 4. 权限服务架构 (Permission Service)

### 4.1 权限数据模型

```python
# permission-service/app/models/permission_models.py
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

# 用户角色关联表
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow),
    Column('assigned_by', UUID(as_uuid=True), ForeignKey('users.id')),
    Column('expires_at', DateTime, nullable=True)
)

# 角色权限关联表
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True),
    Column('granted_at', DateTime, default=datetime.utcnow),
    Column('granted_by', UUID(as_uuid=True), ForeignKey('users.id'))
)

class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 角色属性
    is_system_role = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # 角色优先级

    # 角色层级
    parent_role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'), nullable=True)
    parent_role = relationship("Role", remote_side=[id])

    # 角色配置
    config = Column(JSON, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 权限标识
    resource = Column(String(100), nullable=False)  # 资源类型
    action = Column(String(50), nullable=False)     # 操作类型
    scope = Column(String(100), default="all")      # 权限范围

    # 权限描述
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 权限配置
    conditions = Column(JSON, nullable=True)  # ABAC条件
    is_active = Column(Boolean, default=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 策略规则
    rule_type = Column(String(50), nullable=False)  # time_based, location_based, etc.
    conditions = Column(JSON, nullable=False)
    effect = Column(String(10), nullable=False)  # allow, deny
    priority = Column(Integer, default=0)

    # 状态
    is_active = Column(Boolean, default=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 4.2 权限服务实现

```python
# permission-service/app/services/permission_service.py
from typing import List, Dict, Any, Optional
from enum import Enum
import json
from datetime import datetime

class AccessDecision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    NOT_APPLICABLE = "not_applicable"

class PermissionService:
    """权限管理服务"""

    def __init__(self, db: Session, redis_client):
        self.db = db
        self.redis_client = redis_client
        self.cache_ttl = 300  # 5分钟缓存

    async def check_permission(self, user_id: str, resource: str,
                             action: str, context: Dict[str, Any] = None) -> bool:
        """检查用户权限"""

        # 1. 检查缓存
        cache_key = f"permission:{user_id}:{resource}:{action}"
        cached_result = await self.redis_client.get(cache_key)
        if cached_result is not None:
            return json.loads(cached_result)

        # 2. RBAC权限检查
        rbac_result = await self._check_rbac_permission(user_id, resource, action)

        # 3. ABAC策略评估
        if context:
            abac_result = await self._evaluate_abac_policies(user_id, resource, action, context)
            final_result = rbac_result and (abac_result == AccessDecision.ALLOW)
        else:
            final_result = rbac_result

        # 4. 缓存结果
        await self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(final_result))

        # 5. 记录权限检查日志
        await self._log_permission_check(user_id, resource, action, final_result, context)

        return final_result

    async def _check_rbac_permission(self, user_id: str, resource: str, action: str) -> bool:
        """RBAC权限检查"""

        # 获取用户角色
        user_roles = await self._get_user_roles(user_id)

        # 检查每个角色的权限
        for role in user_roles:
            role_permissions = await self._get_role_permissions(role.id)

            for permission in role_permissions:
                if (permission.resource == resource and
                    permission.action == action and
                    permission.is_active):
                    return True

        return False

    async def _evaluate_abac_policies(self, user_id: str, resource: str,
                                    action: str, context: Dict[str, Any]) -> AccessDecision:
        """ABAC策略评估"""

        # 获取用户属性
        user_attributes = await self._get_user_attributes(user_id)

        # 获取资源属性
        resource_attributes = await self._get_resource_attributes(resource, context)

        # 获取环境属性
        environment_attributes = await self._get_environment_attributes(context)

        # 构建评估上下文
        evaluation_context = {
            "subject": user_attributes,
            "resource": resource_attributes,
            "action": action,
            "environment": environment_attributes
        }

        # 获取适用的策略规则
        applicable_policies = await self._get_applicable_policies(evaluation_context)

        # 评估策略
        final_decision = AccessDecision.DENY  # 默认拒绝

        for policy in applicable_policies:
            decision = await self._evaluate_policy(policy, evaluation_context)

            if decision == AccessDecision.DENY:
                # 拒绝策略优先级最高
                return AccessDecision.DENY
            elif decision == AccessDecision.ALLOW:
                final_decision = AccessDecision.ALLOW

        return final_decision

    async def assign_role_to_user(self, user_id: str, role_id: str,
                                assigned_by: str, expires_at: Optional[datetime] = None):
        """为用户分配角色"""

        # 检查角色是否存在
        role = await self._get_role_by_id(role_id)
        if not role:
            raise ValueError("角色不存在")

        # 检查是否已分配
        existing_assignment = await self._get_user_role_assignment(user_id, role_id)
        if existing_assignment:
            raise ValueError("角色已分配")

        # 创建角色分配
        assignment = UserRole(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            expires_at=expires_at
        )

        self.db.add(assignment)
        self.db.commit()

        # 清除用户权限缓存
        await self._invalidate_user_permission_cache(user_id)

        # 记录审计日志
        await self._log_role_assignment(user_id, role_id, assigned_by, "assign")

    async def revoke_role_from_user(self, user_id: str, role_id: str, revoked_by: str):
        """撤销用户角色"""

        assignment = await self._get_user_role_assignment(user_id, role_id)
        if not assignment:
            raise ValueError("角色分配不存在")

        self.db.delete(assignment)
        self.db.commit()

        # 清除用户权限缓存
        await self._invalidate_user_permission_cache(user_id)

        # 记录审计日志
        await self._log_role_assignment(user_id, role_id, revoked_by, "revoke")

class TimeBasedPolicy:
    """基于时间的访问策略"""

    async def evaluate(self, context: Dict[str, Any]) -> AccessDecision:
        current_time = context["environment"]["time"]
        user_roles = context["subject"]["roles"]

        # 管理员24/7访问
        if "admin" in user_roles or "super_admin" in user_roles:
            return AccessDecision.ALLOW

        # 工作时间访问控制
        if 9 <= current_time.hour <= 18:
            return AccessDecision.ALLOW

        # 非工作时间特殊权限
        if "after_hours_access" in user_roles:
            return AccessDecision.ALLOW

        return AccessDecision.DENY

class LocationBasedPolicy:
    """基于地理位置的访问策略"""

    def __init__(self):
        self.allowed_countries = ["CN", "US", "CA", "GB"]
        self.restricted_ips = set()

    async def evaluate(self, context: Dict[str, Any]) -> AccessDecision:
        ip_address = context["environment"]["ip_address"]
        location = context["environment"]["location"]

        # IP黑名单检查
        if ip_address in self.restricted_ips:
            return AccessDecision.DENY

        # 地理位置检查
        if location and location.get("country_code") not in self.allowed_countries:
            return AccessDecision.DENY

        return AccessDecision.NOT_APPLICABLE
```

---

## 🔄 5. 会话服务架构 (Session Service) - Go实现

### 5.1 会话服务结构

```go
// session-service/main.go
package main

import (
    "log"
    "os"

    "github.com/gin-gonic/gin"
    "github.com/perfect21/session-service/internal/config"
    "github.com/perfect21/session-service/internal/handler"
    "github.com/perfect21/session-service/internal/middleware"
    "github.com/perfect21/session-service/internal/service"
    "github.com/perfect21/session-service/internal/storage"
)

func main() {
    // 加载配置
    cfg := config.Load()

    // 初始化存储
    redisClient := storage.NewRedisClient(cfg.Redis)
    sessionStore := storage.NewSessionStore(redisClient)

    // 初始化服务
    sessionService := service.NewSessionService(sessionStore, cfg)

    // 初始化处理器
    sessionHandler := handler.NewSessionHandler(sessionService)

    // 初始化路由
    router := gin.New()
    router.Use(gin.Logger(), gin.Recovery())
    router.Use(middleware.CORS())
    router.Use(middleware.RateLimit())

    v1 := router.Group("/api/v1")
    {
        sessions := v1.Group("/sessions")
        {
            sessions.POST("/", sessionHandler.CreateSession)
            sessions.GET("/:sessionId", sessionHandler.GetSession)
            sessions.PUT("/:sessionId", sessionHandler.UpdateSession)
            sessions.DELETE("/:sessionId", sessionHandler.DeleteSession)
            sessions.POST("/:sessionId/validate", sessionHandler.ValidateSession)
        }

        users := v1.Group("/users")
        {
            users.GET("/:userId/sessions", sessionHandler.GetUserSessions)
            users.DELETE("/:userId/sessions", sessionHandler.DeleteUserSessions)
        }
    }

    // 启动服务器
    port := os.Getenv("PORT")
    if port == "" {
        port = "8083"
    }

    log.Printf("Session service starting on port %s", port)
    log.Fatal(router.Run(":" + port))
}
```

### 5.2 会话模型和服务

```go
// session-service/internal/model/session.go
package model

import (
    "time"
    "github.com/google/uuid"
)

type Session struct {
    ID               string                 `json:"id" redis:"id"`
    UserID           string                 `json:"user_id" redis:"user_id"`
    DeviceFingerprint string                `json:"device_fingerprint" redis:"device_fingerprint"`
    IPAddress        string                 `json:"ip_address" redis:"ip_address"`
    UserAgent        string                 `json:"user_agent" redis:"user_agent"`
    Location         map[string]interface{} `json:"location" redis:"location"`
    IsActive         bool                   `json:"is_active" redis:"is_active"`
    CreatedAt        time.Time              `json:"created_at" redis:"created_at"`
    LastActivity     time.Time              `json:"last_activity" redis:"last_activity"`
    ExpiresAt        time.Time              `json:"expires_at" redis:"expires_at"`
    Metadata         map[string]interface{} `json:"metadata" redis:"metadata"`
}

type SessionCreateRequest struct {
    UserID           string                 `json:"user_id" binding:"required"`
    IPAddress        string                 `json:"ip_address" binding:"required"`
    UserAgent        string                 `json:"user_agent"`
    DeviceInfo       map[string]interface{} `json:"device_info"`
    Location         map[string]interface{} `json:"location"`
}

type SessionValidationResult struct {
    Valid       bool                   `json:"valid"`
    Session     *Session               `json:"session,omitempty"`
    Warnings    []string               `json:"warnings,omitempty"`
    RiskFactors []string               `json:"risk_factors,omitempty"`
}

// session-service/internal/service/session_service.go
package service

import (
    "context"
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "time"

    "github.com/google/uuid"
    "github.com/perfect21/session-service/internal/config"
    "github.com/perfect21/session-service/internal/model"
    "github.com/perfect21/session-service/internal/storage"
)

type SessionService struct {
    store  storage.SessionStore
    config *config.Config
}

func NewSessionService(store storage.SessionStore, cfg *config.Config) *SessionService {
    return &SessionService{
        store:  store,
        config: cfg,
    }
}

func (s *SessionService) CreateSession(ctx context.Context, req *model.SessionCreateRequest) (*model.Session, error) {
    // 检查用户当前会话数
    userSessions, err := s.store.GetUserSessions(ctx, req.UserID)
    if err != nil {
        return nil, fmt.Errorf("failed to get user sessions: %w", err)
    }

    // 超过最大会话数，删除最旧的会话
    if len(userSessions) >= s.config.MaxSessionsPerUser {
        oldestSession := s.findOldestSession(userSessions)
        if oldestSession != nil {
            s.store.DeleteSession(ctx, oldestSession.ID)
        }
    }

    // 生成设备指纹
    deviceFingerprint := s.generateDeviceFingerprint(req.DeviceInfo, req.UserAgent)

    // 创建新会话
    session := &model.Session{
        ID:               uuid.New().String(),
        UserID:           req.UserID,
        DeviceFingerprint: deviceFingerprint,
        IPAddress:        req.IPAddress,
        UserAgent:        req.UserAgent,
        Location:         req.Location,
        IsActive:         true,
        CreatedAt:        time.Now(),
        LastActivity:     time.Now(),
        ExpiresAt:        time.Now().Add(time.Duration(s.config.SessionTTL) * time.Second),
    }

    // 存储会话
    err = s.store.CreateSession(ctx, session)
    if err != nil {
        return nil, fmt.Errorf("failed to create session: %w", err)
    }

    return session, nil
}

func (s *SessionService) ValidateSession(ctx context.Context, sessionID string,
                                        currentContext *model.RequestContext) (*model.SessionValidationResult, error) {
    // 获取会话
    session, err := s.store.GetSession(ctx, sessionID)
    if err != nil {
        return &model.SessionValidationResult{Valid: false}, nil
    }

    if session == nil || !session.IsActive {
        return &model.SessionValidationResult{Valid: false}, nil
    }

    // 检查会话是否过期
    if time.Now().After(session.ExpiresAt) {
        s.store.DeleteSession(ctx, sessionID)
        return &model.SessionValidationResult{Valid: false}, nil
    }

    // 安全验证
    result := &model.SessionValidationResult{
        Valid:   true,
        Session: session,
    }

    // IP地址检查
    if session.IPAddress != currentContext.IPAddress {
        result.Warnings = append(result.Warnings, "IP address changed")
        result.RiskFactors = append(result.RiskFactors, "ip_change")
    }

    // 设备指纹检查
    currentFingerprint := s.generateDeviceFingerprint(currentContext.DeviceInfo, currentContext.UserAgent)
    if session.DeviceFingerprint != currentFingerprint {
        result.Warnings = append(result.Warnings, "Device fingerprint mismatch")
        result.RiskFactors = append(result.RiskFactors, "device_mismatch")
    }

    // 地理位置异常检查
    if s.isUnusualLocation(session.Location, currentContext.Location) {
        result.Warnings = append(result.Warnings, "Unusual location detected")
        result.RiskFactors = append(result.RiskFactors, "unusual_location")
    }

    // 高风险会话处理
    if len(result.RiskFactors) >= 2 {
        s.store.DeleteSession(ctx, sessionID)
        result.Valid = false
        return result, nil
    }

    // 更新最后活动时间
    session.LastActivity = time.Now()
    s.store.UpdateSession(ctx, session)

    return result, nil
}

func (s *SessionService) generateDeviceFingerprint(deviceInfo map[string]interface{}, userAgent string) string {
    fingerprintData := map[string]interface{}{
        "user_agent": userAgent,
        "device_info": deviceInfo,
    }

    data, _ := json.Marshal(fingerprintData)
    hash := sha256.Sum256(data)
    return hex.EncodeToString(hash[:])
}

func (s *SessionService) isUnusualLocation(sessionLocation, currentLocation map[string]interface{}) bool {
    if sessionLocation == nil || currentLocation == nil {
        return false
    }

    sessionCountry, ok1 := sessionLocation["country_code"].(string)
    currentCountry, ok2 := currentLocation["country_code"].(string)

    if !ok1 || !ok2 {
        return false
    }

    return sessionCountry != currentCountry
}

func (s *SessionService) findOldestSession(sessions []*model.Session) *model.Session {
    if len(sessions) == 0 {
        return nil
    }

    oldest := sessions[0]
    for _, session := range sessions[1:] {
        if session.CreatedAt.Before(oldest.CreatedAt) {
            oldest = session
        }
    }

    return oldest
}
```

---

## 📧 6. 通知服务架构 (Notification Service) - Node.js实现

### 6.1 通知服务结构

```javascript
// notification-service/src/app.js
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { createServer } = require('http');
const { Server } = require('socket.io');

const notificationRoutes = require('./routes/notifications');
const emailService = require('./services/emailService');
const smsService = require('./services/smsService');
const websocketService = require('./services/websocketService');
const config = require('./config');

const app = express();
const server = createServer(app);
const io = new Server(server, {
    cors: {
        origin: config.cors.origins,
        methods: ["GET", "POST"]
    }
});

// 中间件
app.use(helmet());
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// 速率限制
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15分钟
    max: 100 // 每个IP最多100个请求
});
app.use(limiter);

// 路由
app.use('/api/v1/notifications', notificationRoutes);

// WebSocket连接处理
websocketService.initialize(io);

// 错误处理
app.use((error, req, res, next) => {
    console.error('Error:', error);
    res.status(500).json({ error: 'Internal server error' });
});

const PORT = process.env.PORT || 8084;
server.listen(PORT, () => {
    console.log(`Notification service running on port ${PORT}`);
});

// notification-service/src/services/emailService.js
const nodemailer = require('nodemailer');
const handlebars = require('handlebars');
const fs = require('fs').promises;
const path = require('path');
const config = require('../config');

class EmailService {
    constructor() {
        this.transporter = nodemailer.createTransporter({
            host: config.email.smtp.host,
            port: config.email.smtp.port,
            secure: config.email.smtp.secure,
            auth: {
                user: config.email.smtp.user,
                pass: config.email.smtp.password
            }
        });

        this.templates = new Map();
        this.loadTemplates();
    }

    async loadTemplates() {
        const templatesDir = path.join(__dirname, '../templates');
        const templateFiles = [
            'email-verification.hbs',
            'password-reset.hbs',
            'security-alert.hbs',
            'mfa-setup.hbs',
            'login-notification.hbs'
        ];

        for (const file of templateFiles) {
            try {
                const templateContent = await fs.readFile(
                    path.join(templatesDir, file),
                    'utf8'
                );
                const templateName = file.replace('.hbs', '');
                this.templates.set(templateName, handlebars.compile(templateContent));
            } catch (error) {
                console.error(`Error loading template ${file}:`, error);
            }
        }
    }

    async sendEmailVerification(email, verificationToken, userInfo) {
        const template = this.templates.get('email-verification');
        if (!template) {
            throw new Error('Email verification template not found');
        }

        const verificationUrl = `${config.frontend.url}/verify-email?token=${verificationToken}`;

        const html = template({
            userName: userInfo.firstName || userInfo.email,
            verificationUrl,
            companyName: 'Claude Enhancer',
            supportEmail: config.email.supportAddress
        });

        const mailOptions = {
            from: config.email.fromAddress,
            to: email,
            subject: 'Claude Enhancer - 请验证您的邮箱地址',
            html
        };

        return await this.transporter.sendMail(mailOptions);
    }

    async sendPasswordResetEmail(email, resetToken, userInfo) {
        const template = this.templates.get('password-reset');
        if (!template) {
            throw new Error('Password reset template not found');
        }

        const resetUrl = `${config.frontend.url}/reset-password?token=${resetToken}`;

        const html = template({
            userName: userInfo.firstName || userInfo.email,
            resetUrl,
            expirationTime: '1小时',
            companyName: 'Claude Enhancer',
            supportEmail: config.email.supportAddress
        });

        const mailOptions = {
            from: config.email.fromAddress,
            to: email,
            subject: 'Claude Enhancer - 密码重置请求',
            html
        };

        return await this.transporter.sendMail(mailOptions);
    }

    async sendSecurityAlert(email, alertInfo, userInfo) {
        const template = this.templates.get('security-alert');
        if (!template) {
            throw new Error('Security alert template not found');
        }

        const html = template({
            userName: userInfo.firstName || userInfo.email,
            alertType: alertInfo.type,
            alertMessage: alertInfo.message,
            timestamp: new Date(alertInfo.timestamp).toLocaleString('zh-CN'),
            ipAddress: alertInfo.ipAddress,
            location: alertInfo.location,
            deviceInfo: alertInfo.deviceInfo,
            actionUrl: `${config.frontend.url}/security`,
            companyName: 'Claude Enhancer',
            supportEmail: config.email.supportAddress
        });

        const mailOptions = {
            from: config.email.fromAddress,
            to: email,
            subject: 'Claude Enhancer - 安全警告',
            html,
            priority: 'high'
        };

        return await this.transporter.sendMail(mailOptions);
    }

    async sendLoginNotification(email, loginInfo, userInfo) {
        const template = this.templates.get('login-notification');
        if (!template) {
            throw new Error('Login notification template not found');
        }

        const html = template({
            userName: userInfo.firstName || userInfo.email,
            loginTime: new Date(loginInfo.timestamp).toLocaleString('zh-CN'),
            ipAddress: loginInfo.ipAddress,
            location: loginInfo.location,
            deviceInfo: loginInfo.deviceInfo,
            wasSuccessful: loginInfo.successful,
            actionUrl: `${config.frontend.url}/security`,
            companyName: 'Claude Enhancer'
        });

        const subject = loginInfo.successful
            ? 'Claude Enhancer - 登录通知'
            : 'Claude Enhancer - 登录尝试失败警告';

        const mailOptions = {
            from: config.email.fromAddress,
            to: email,
            subject,
            html
        };

        return await this.transporter.sendMail(mailOptions);
    }
}

module.exports = new EmailService();

// notification-service/src/services/websocketService.js
const jwt = require('jsonwebtoken');
const config = require('../config');

class WebSocketService {
    constructor() {
        this.connectedUsers = new Map(); // userId -> Set of socket IDs
        this.userSockets = new Map();    // socketId -> userId
    }

    initialize(io) {
        this.io = io;

        // WebSocket认证中间件
        io.use(async (socket, next) => {
            try {
                const token = socket.handshake.auth.token;
                if (!token) {
                    return next(new Error('No token provided'));
                }

                const decoded = jwt.verify(token, config.jwt.publicKey, {
                    algorithms: ['RS256']
                });

                socket.userId = decoded.sub;
                next();
            } catch (error) {
                next(new Error('Invalid token'));
            }
        });

        io.on('connection', (socket) => {
            this.handleConnection(socket);
        });
    }

    handleConnection(socket) {
        const userId = socket.userId;

        // 添加到用户连接映射
        if (!this.connectedUsers.has(userId)) {
            this.connectedUsers.set(userId, new Set());
        }
        this.connectedUsers.get(userId).add(socket.id);
        this.userSockets.set(socket.id, userId);

        console.log(`User ${userId} connected with socket ${socket.id}`);

        // 加入用户房间
        socket.join(`user:${userId}`);

        // 处理断开连接
        socket.on('disconnect', () => {
            this.handleDisconnection(socket);
        });

        // 处理心跳
        socket.on('ping', () => {
            socket.emit('pong');
        });

        // 发送欢迎消息
        socket.emit('connected', {
            message: 'Connected to Claude Enhancer notification service',
            timestamp: new Date().toISOString()
        });
    }

    handleDisconnection(socket) {
        const userId = this.userSockets.get(socket.id);

        if (userId && this.connectedUsers.has(userId)) {
            this.connectedUsers.get(userId).delete(socket.id);

            // 如果用户没有其他连接，移除用户记录
            if (this.connectedUsers.get(userId).size === 0) {
                this.connectedUsers.delete(userId);
            }
        }

        this.userSockets.delete(socket.id);
        console.log(`Socket ${socket.id} disconnected`);
    }

    // 发送实时通知给特定用户
    sendNotificationToUser(userId, notification) {
        this.io.to(`user:${userId}`).emit('notification', {
            id: notification.id,
            type: notification.type,
            title: notification.title,
            message: notification.message,
            data: notification.data,
            timestamp: notification.timestamp,
            priority: notification.priority
        });
    }

    // 发送系统广播
    sendSystemBroadcast(notification) {
        this.io.emit('system_notification', {
            type: notification.type,
            message: notification.message,
            timestamp: notification.timestamp
        });
    }

    // 发送安全警告
    sendSecurityAlert(userId, alert) {
        this.io.to(`user:${userId}`).emit('security_alert', {
            id: alert.id,
            type: alert.type,
            severity: alert.severity,
            message: alert.message,
            details: alert.details,
            timestamp: alert.timestamp,
            actionRequired: alert.actionRequired
        });
    }

    // 获取在线用户数量
    getOnlineUserCount() {
        return this.connectedUsers.size;
    }

    // 检查用户是否在线
    isUserOnline(userId) {
        return this.connectedUsers.has(userId) &&
               this.connectedUsers.get(userId).size > 0;
    }
}

module.exports = new WebSocketService();
```

---

## 🗄️ 7. 数据存储架构

### 7.1 PostgreSQL数据库设计

```sql
-- 创建数据库和用户
CREATE DATABASE perfect21_auth;
CREATE USER perfect21_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE perfect21_auth TO perfect21_user;

-- 连接到数据库
\c perfect21_auth;

-- 启用UUID扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    password_hash TEXT NOT NULL,
    password_salt VARCHAR(64) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone_number VARCHAR(20),

    -- 账户状态
    status VARCHAR(20) NOT NULL DEFAULT 'pending_verification',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,

    -- MFA配置
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    totp_secret VARCHAR(32),
    backup_codes JSONB,

    -- 安全信息
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    password_changed_at TIMESTAMP,
    last_login_at TIMESTAMP,
    last_login_ip INET,

    -- 个人资料
    profile JSONB,
    preferences JSONB,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,

    -- 验证相关
    email_verification_token VARCHAR(255),
    email_verified_at TIMESTAMP,
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP
);

-- 角色表
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    parent_role_id UUID REFERENCES roles(id),
    config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 权限表
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    scope VARCHAR(100) DEFAULT 'all',
    name VARCHAR(200) NOT NULL,
    description TEXT,
    conditions JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(resource, action, scope)
);

-- 用户角色关联表
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES users(id),
    expires_at TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

-- 角色权限关联表
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by UUID REFERENCES users(id),
    PRIMARY KEY (role_id, permission_id)
);

-- 用户会话表
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    device_fingerprint VARCHAR(64) NOT NULL,
    user_agent TEXT,
    ip_address INET NOT NULL,
    location JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

-- 登录历史表
CREATE TABLE user_login_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    ip_address INET NOT NULL,
    user_agent TEXT,
    location JSONB,
    login_successful BOOLEAN NOT NULL,
    failure_reason VARCHAR(100),
    mfa_used BOOLEAN DEFAULT FALSE,
    risk_score FLOAT,
    risk_factors JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 审计日志表
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id VARCHAR(50) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    user_id UUID,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    action VARCHAR(100),
    result VARCHAR(20),
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    severity VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 密码历史表
CREATE TABLE password_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 策略规则表
CREATE TABLE policy_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    rule_type VARCHAR(50) NOT NULL,
    conditions JSONB NOT NULL,
    effect VARCHAR(10) NOT NULL CHECK (effect IN ('allow', 'deny')),
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_last_login ON users(last_login_at);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_active ON user_sessions(is_active);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);

CREATE INDEX idx_login_history_user_id ON user_login_history(user_id);
CREATE INDEX idx_login_history_created ON user_login_history(created_at);
CREATE INDEX idx_login_history_ip ON user_login_history(ip_address);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_category ON audit_logs(category);

CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX idx_user_roles_expires ON user_roles(expires_at);

CREATE INDEX idx_permissions_resource_action ON permissions(resource, action);

-- 插入系统角色
INSERT INTO roles (name, display_name, description, is_system_role, priority) VALUES
('super_admin', '超级管理员', '拥有所有系统权限', TRUE, 1000),
('admin', '系统管理员', '系统管理权限', TRUE, 900),
('user_manager', '用户管理员', '用户管理权限', TRUE, 800),
('regular_user', '普通用户', '基础功能权限', TRUE, 100),
('readonly_user', '只读用户', '只读权限', TRUE, 50);

-- 插入基础权限
INSERT INTO permissions (resource, action, scope, name, description) VALUES
-- 用户权限
('user', 'read', 'own', '查看自己信息', '用户可以查看自己的个人信息'),
('user', 'read', 'all', '查看所有用户', '管理员可以查看所有用户信息'),
('user', 'write', 'own', '修改自己信息', '用户可以修改自己的个人信息'),
('user', 'write', 'all', '修改所有用户', '管理员可以修改所有用户信息'),
('user', 'delete', 'own', '删除自己账户', '用户可以删除自己的账户'),
('user', 'delete', 'all', '删除任意用户', '管理员可以删除任意用户账户'),

-- 系统权限
('system', 'read', 'all', '查看系统配置', '查看系统配置和状态'),
('system', 'write', 'all', '修改系统配置', '修改系统配置'),
('admin_panel', 'access', 'all', '访问管理面板', '访问系统管理面板');

-- 分配权限给角色
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'regular_user'
AND p.resource = 'user'
AND p.scope = 'own';
```

### 7.2 Redis缓存架构

```yaml
# redis-cluster.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
data:
  redis.conf: |
    # Redis集群配置
    cluster-enabled yes
    cluster-config-file nodes.conf
    cluster-node-timeout 5000
    appendonly yes

    # 安全配置
    requirepass ${REDIS_PASSWORD}
    masterauth ${REDIS_PASSWORD}

    # 内存配置
    maxmemory 2gb
    maxmemory-policy allkeys-lru

    # 网络配置
    tcp-keepalive 60
    timeout 300

    # 日志配置
    loglevel notice
    logfile ""

    # 持久化配置
    save 900 1
    save 300 10
    save 60 10000
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
spec:
  serviceName: redis-cluster
  replicas: 6
  selector:
    matchLabels:
      app: redis-cluster
  template:
    metadata:
      labels:
        app: redis-cluster
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        - containerPort: 16379
        command:
        - redis-server
        - /etc/redis/redis.conf
        volumeMounts:
        - name: redis-config
          mountPath: /etc/redis
        - name: redis-data
          mountPath: /data
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: password
      volumes:
      - name: redis-config
        configMap:
          name: redis-config
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

---

## 🚀 8. 部署和运维架构

### 8.1 Kubernetes部署配置

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: perfect21-auth
  labels:
    name: perfect21-auth

---
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: perfect21-secrets
  namespace: perfect21-auth
type: Opaque
stringData:
  database-url: "postgresql://perfect21_user:secure_password@postgres:5432/perfect21_auth"
  redis-password: "redis_secure_password"
  jwt-private-key: |
    -----BEGIN PRIVATE KEY-----
    # JWT私钥内容
    -----END PRIVATE KEY-----
  jwt-public-key: |
    -----BEGIN PUBLIC KEY-----
    # JWT公钥内容
    -----END PUBLIC KEY-----
  email-smtp-password: "smtp_password"
  sms-api-key: "sms_api_key"

---
# k8s/auth-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  namespace: perfect21-auth
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
      - name: auth-service
        image: perfect21/auth-service:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: perfect21-secrets
              key: database-url
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: perfect21-secrets
              key: redis-password
        - name: JWT_PRIVATE_KEY
          valueFrom:
            secretKeyRef:
              name: perfect21-secrets
              key: jwt-private-key
        - name: JWT_PUBLIC_KEY
          valueFrom:
            secretKeyRef:
              name: perfect21-secrets
              key: jwt-public-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: auth-service
  namespace: perfect21-auth
spec:
  selector:
    app: auth-service
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP

---
# k8s/api-gateway.yaml
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: perfect21-gateway
  namespace: perfect21-auth
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: perfect21-tls
    hosts:
    - api.perfect21.com
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - api.perfect21.com
    redirect:
      httpsRedirect: true

---
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: perfect21-vs
  namespace: perfect21-auth
spec:
  hosts:
  - api.perfect21.com
  gateways:
  - perfect21-gateway
  http:
  - match:
    - uri:
        prefix: /api/auth/
    route:
    - destination:
        host: auth-service.perfect21-auth.svc.cluster.local
        port:
          number: 80
    timeout: 30s
    retries:
      attempts: 3
      perTryTimeout: 10s
  - match:
    - uri:
        prefix: /api/users/
    route:
    - destination:
        host: user-service.perfect21-auth.svc.cluster.local
        port:
          number: 80
  - match:
    - uri:
        prefix: /api/permissions/
    route:
    - destination:
        host: permission-service.perfect21-auth.svc.cluster.local
        port:
          number: 80
  - match:
    - uri:
        prefix: /api/sessions/
    route:
    - destination:
        host: session-service.perfect21-auth.svc.cluster.local
        port:
          number: 80
```

### 8.2 监控和日志架构

```yaml
# monitoring/prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    rule_files:
      - "auth_alerts.yml"

    scrape_configs:
    - job_name: 'auth-service'
      static_configs:
      - targets: ['auth-service.perfect21-auth:8080']
      metrics_path: /metrics
      scrape_interval: 10s

    - job_name: 'user-service'
      static_configs:
      - targets: ['user-service.perfect21-auth:8080']

    - job_name: 'permission-service'
      static_configs:
      - targets: ['permission-service.perfect21-auth:8080']

    - job_name: 'session-service'
      static_configs:
      - targets: ['session-service.perfect21-auth:8083']

    - job_name: 'redis'
      static_configs:
      - targets: ['redis-exporter.perfect21-auth:9121']

    - job_name: 'postgres'
      static_configs:
      - targets: ['postgres-exporter.perfect21-auth:9187']

  auth_alerts.yml: |
    groups:
    - name: authentication_alerts
      rules:
      - alert: HighFailedLoginRate
        expr: rate(auth_failed_logins_total[5m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High failed login rate detected"
          description: "Failed login rate is {{ $value }} per second"

      - alert: AuthServiceDown
        expr: up{job="auth-service"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Authentication service is down"
          description: "Auth service has been down for more than 1 minute"

      - alert: TokenValidationLatencyHigh
        expr: histogram_quantile(0.95, auth_token_validation_duration_seconds) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Token validation latency is high"
          description: "95th percentile latency is {{ $value }}s"

      - alert: SuspiciousActivityDetected
        expr: rate(auth_suspicious_activity_total[10m]) > 5
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Suspicious activity detected"
          description: "Suspicious activity rate: {{ $value }} events per second"

---
# monitoring/grafana-dashboard.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: auth-dashboard
  namespace: monitoring
data:
  dashboard.json: |
    {
      "dashboard": {
        "title": "Claude Enhancer Authentication System",
        "panels": [
          {
            "title": "Login Success Rate",
            "type": "stat",
            "targets": [
              {
                "expr": "rate(auth_login_attempts_total{result=\"success\"}[5m]) / rate(auth_login_attempts_total[5m]) * 100"
              }
            ]
          },
          {
            "title": "Token Generation Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(auth_token_generated_total[1m])"
              }
            ]
          },
          {
            "title": "Active Sessions",
            "type": "stat",
            "targets": [
              {
                "expr": "session_active_total"
              }
            ]
          },
          {
            "title": "Failed Login Attempts by IP",
            "type": "table",
            "targets": [
              {
                "expr": "topk(10, sum by (ip_address) (rate(auth_failed_logins_total[1h])))"
              }
            ]
          },
          {
            "title": "Permission Check Latency",
            "type": "graph",
            "targets": [
              {
                "expr": "histogram_quantile(0.50, permission_check_duration_seconds)"
              },
              {
                "expr": "histogram_quantile(0.95, permission_check_duration_seconds)"
              },
              {
                "expr": "histogram_quantile(0.99, permission_check_duration_seconds)"
              }
            ]
          },
          {
            "title": "Security Events",
            "type": "logs",
            "targets": [
              {
                "expr": "{job=\"auth-service\", level=\"error\"} |= \"security\""
              }
            ]
          }
        ]
      }
    }
```

---

## 📊 9. 性能优化策略

### 9.1 缓存策略实现

```python
# shared/cache/cache_manager.py
from typing import Any, Optional, List, Dict
import json
import hashlib
from datetime import timedelta
import redis
from functools import wraps

class CacheManager:
    """多层缓存管理器"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host='redis-cluster',
            port=6379,
            decode_responses=True
        )
        self.local_cache = {}  # 进程内缓存
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'local_hits': 0,
            'redis_hits': 0
        }

    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = f"{prefix}:{':'.join(map(str, args))}"
        if kwargs:
            key_data += f":{hashlib.md5(json.dumps(kwargs, sort_keys=True).encode()).hexdigest()}"
        return key_data

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        # 1. 检查本地缓存
        if key in self.local_cache:
            self.cache_stats['hits'] += 1
            self.cache_stats['local_hits'] += 1
            return self.local_cache[key]['value']

        # 2. 检查Redis缓存
        try:
            value = await self.redis_client.get(key)
            if value is not None:
                self.cache_stats['hits'] += 1
                self.cache_stats['redis_hits'] += 1

                # 反序列化并回填本地缓存
                deserialized_value = json.loads(value)
                self.local_cache[key] = {
                    'value': deserialized_value,
                    'timestamp': time.time()
                }
                return deserialized_value
        except Exception as e:
            print(f"Redis cache error: {e}")

        self.cache_stats['misses'] += 1
        return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存值"""
        serialized_value = json.dumps(value)

        # 设置Redis缓存
        try:
            await self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            print(f"Redis cache set error: {e}")

        # 设置本地缓存（较短TTL）
        self.local_cache[key] = {
            'value': value,
            'timestamp': time.time(),
            'ttl': min(ttl, 60)  # 本地缓存最多1分钟
        }

    async def delete(self, key: str):
        """删除缓存"""
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            print(f"Redis cache delete error: {e}")

        self.local_cache.pop(key, None)

    async def delete_pattern(self, pattern: str):
        """批量删除缓存"""
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Redis pattern delete error: {e}")

        # 清理本地缓存
        keys_to_remove = [k for k in self.local_cache.keys() if pattern.replace('*', '') in k]
        for key in keys_to_remove:
            del self.local_cache[key]

# 缓存装饰器
def cached(ttl: int = 300, key_prefix: str = ""):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_manager = CacheManager()

            # 生成缓存键
            cache_key = cache_manager.cache_key(
                key_prefix or func.__name__,
                *args, **kwargs
            )

            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator

# 权限缓存服务
class PermissionCacheService:
    """权限缓存服务"""

    def __init__(self):
        self.cache_manager = CacheManager()
        self.permission_ttl = 300  # 5分钟
        self.role_ttl = 600  # 10分钟

    @cached(ttl=300, key_prefix="user_permissions")
    async def get_user_permissions(self, user_id: str) -> List[Dict]:
        """获取用户权限（带缓存）"""
        # 这里调用实际的数据库查询
        return await self._fetch_user_permissions_from_db(user_id)

    @cached(ttl=600, key_prefix="user_roles")
    async def get_user_roles(self, user_id: str) -> List[Dict]:
        """获取用户角色（带缓存）"""
        return await self._fetch_user_roles_from_db(user_id)

    async def invalidate_user_cache(self, user_id: str):
        """使用户相关缓存失效"""
        patterns = [
            f"user_permissions:{user_id}:*",
            f"user_roles:{user_id}:*",
            f"permission:{user_id}:*"
        ]

        for pattern in patterns:
            await self.cache_manager.delete_pattern(pattern)

    async def warm_up_cache(self, user_ids: List[str]):
        """预热缓存"""
        for user_id in user_ids:
            # 并发预加载用户权限和角色
            await asyncio.gather(
                self.get_user_permissions(user_id),
                self.get_user_roles(user_id)
            )
```

### 9.2 数据库优化策略

```python
# shared/database/connection_pool.py
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import asyncpg
import asyncio
from typing import Optional

class DatabaseManager:
    """数据库连接管理器"""

    def __init__(self, database_url: str):
        # PostgreSQL连接池配置
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=20,  # 基础连接数
            max_overflow=30,  # 最大额外连接数
            pool_timeout=30,  # 获取连接超时时间
            pool_recycle=3600,  # 连接回收时间（1小时）
            pool_pre_ping=True,  # 连接前ping检查
            echo=False,  # 生产环境关闭SQL日志
        )

        # 配置连接池事件
        event.listen(
            self.engine,
            "connect",
            self._set_connection_options
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        # 异步连接池
        self.async_pool = None
        self._init_async_pool(database_url)

    def _set_connection_options(self, dbapi_connection, connection_record):
        """设置连接选项"""
        with dbapi_connection.cursor() as cursor:
            # 设置查询超时
            cursor.execute("SET statement_timeout = '30s'")
            # 设置空闲连接超时
            cursor.execute("SET idle_in_transaction_session_timeout = '5min'")
            # 启用并行查询
            cursor.execute("SET max_parallel_workers_per_gather = 4")

    async def _init_async_pool(self, database_url: str):
        """初始化异步连接池"""
        self.async_pool = await asyncpg.create_pool(
            database_url,
            min_size=10,
            max_size=50,
            max_queries=50000,
            max_inactive_connection_lifetime=300.0,
            command_timeout=30.0
        )

    def get_session(self):
        """获取同步数据库会话"""
        return self.SessionLocal()

    async def get_async_connection(self):
        """获取异步数据库连接"""
        return await self.async_pool.acquire()

    async def execute_query(self, query: str, *args):
        """执行异步查询"""
        async with self.async_pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def execute_transaction(self, queries: List[tuple]):
        """执行事务"""
        async with self.async_pool.acquire() as connection:
            async with connection.transaction():
                results = []
                for query, args in queries:
                    result = await connection.fetch(query, *args)
                    results.append(result)
                return results

# 查询优化器
class QueryOptimizer:
    """查询优化器"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def optimize_user_permission_query(self, user_id: str) -> List[Dict]:
        """优化的用户权限查询"""
        # 使用JOIN和子查询优化
        query = """
        WITH user_roles_cte AS (
            SELECT ur.role_id, r.priority
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = $1
            AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
            AND r.is_active = true
        ),
        role_permissions_cte AS (
            SELECT DISTINCT p.resource, p.action, p.scope, p.name, p.description
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            JOIN user_roles_cte urc ON rp.role_id = urc.role_id
            WHERE p.is_active = true
        )
        SELECT * FROM role_permissions_cte
        ORDER BY resource, action, scope;
        """

        return await self.db_manager.execute_query(query, user_id)

    async def batch_permission_check(self, checks: List[tuple]) -> Dict[str, bool]:
        """批量权限检查"""
        # 构建批量查询以减少数据库往返
        user_ids = list(set(check[0] for check in checks))

        # 一次性获取所有用户的权限
        user_permissions = {}
        for user_id in user_ids:
            permissions = await self.optimize_user_permission_query(user_id)
            user_permissions[user_id] = {
                f"{p['resource']}:{p['action']}:{p['scope']}": True
                for p in permissions
            }

        # 检查每个权限
        results = {}
        for user_id, resource, action, scope in checks:
            key = f"{user_id}:{resource}:{action}:{scope}"
            permission_key = f"{resource}:{action}:{scope}"
            results[key] = user_permissions.get(user_id, {}).get(permission_key, False)

        return results

# 读写分离配置
class ReadWriteDbManager:
    """读写分离数据库管理器"""

    def __init__(self, master_url: str, slave_urls: List[str]):
        self.master_db = DatabaseManager(master_url)
        self.slave_dbs = [DatabaseManager(url) for url in slave_urls]
        self.current_slave_index = 0

    def get_write_session(self):
        """获取写数据库会话"""
        return self.master_db.get_session()

    def get_read_session(self):
        """获取读数据库会话（负载均衡）"""
        if not self.slave_dbs:
            return self.master_db.get_session()

        slave_db = self.slave_dbs[self.current_slave_index]
        self.current_slave_index = (self.current_slave_index + 1) % len(self.slave_dbs)
        return slave_db.get_session()

    async def get_read_connection(self):
        """获取异步读连接"""
        if not self.slave_dbs:
            return await self.master_db.get_async_connection()

        slave_db = self.slave_dbs[self.current_slave_index]
        self.current_slave_index = (self.current_slave_index + 1) % len(self.slave_dbs)
        return await slave_db.get_async_connection()
```

---

## 🛡️ 10. 安全最佳实践

### 10.1 安全中间件

```python
# shared/middleware/security_middleware.py
from typing import Dict, Any, Optional
import time
import hashlib
import hmac
from datetime import datetime, timedelta
import ipaddress
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class SecurityMiddleware:
    """安全中间件"""

    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.ip_whitelist = set()
        self.ip_blacklist = set()
        self.security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }

    async def __call__(self, request: Request, call_next):
        # 1. IP检查
        client_ip = self._get_client_ip(request)
        if await self._is_ip_blocked(client_ip):
            raise HTTPException(status_code=403, detail="IP address blocked")

        # 2. 速率限制
        if not await self.rate_limiter.allow_request(client_ip):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        # 3. 请求大小限制
        if await self._is_request_too_large(request):
            raise HTTPException(status_code=413, detail="Request too large")

        # 4. 请求头验证
        if not await self._validate_headers(request):
            raise HTTPException(status_code=400, detail="Invalid headers")

        # 处理请求
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # 5. 添加安全头
        for header, value in self.security_headers.items():
            response.headers[header] = value

        # 6. 添加性能头
        response.headers["X-Process-Time"] = str(process_time)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP"""
        # 检查反向代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host

    async def _is_ip_blocked(self, ip: str) -> bool:
        """检查IP是否被阻止"""
        # 检查黑名单
        if ip in self.ip_blacklist:
            return True

        # 检查动态黑名单（Redis）
        # 这里可以集成动态IP阻止逻辑

        return False

    async def _is_request_too_large(self, request: Request) -> bool:
        """检查请求大小"""
        content_length = request.headers.get("content-length")
        if content_length:
            return int(content_length) > 10 * 1024 * 1024  # 10MB限制
        return False

    async def _validate_headers(self, request: Request) -> bool:
        """验证请求头"""
        # 检查必需的安全头
        user_agent = request.headers.get("user-agent")
        if not user_agent or len(user_agent) > 1000:
            return False

        # 检查可疑的头
        suspicious_headers = ["x-forwarded-host", "x-rewrite-url"]
        for header in suspicious_headers:
            if header in request.headers:
                return False

        return True

class RateLimiter:
    """速率限制器"""

    def __init__(self):
        self.redis_client = redis.Redis(host='redis-cluster', port=6379)
        self.limits = {
            'default': {'requests': 100, 'window': 60},  # 每分钟100请求
            'auth': {'requests': 10, 'window': 60},      # 认证接口每分钟10请求
            'login': {'requests': 5, 'window': 300},     # 登录每5分钟5次
        }

    async def allow_request(self, client_ip: str, endpoint: str = 'default') -> bool:
        """检查是否允许请求"""
        limit_config = self.limits.get(endpoint, self.limits['default'])

        key = f"rate_limit:{endpoint}:{client_ip}"
        current_time = int(time.time())
        window_start = current_time - limit_config['window']

        # 使用Redis Sorted Set实现滑动窗口
        pipe = self.redis_client.pipeline()

        # 移除过期的请求记录
        pipe.zremrangebyscore(key, 0, window_start)

        # 添加当前请求
        pipe.zadd(key, {str(current_time): current_time})

        # 获取当前窗口内的请求数
        pipe.zcard(key)

        # 设置key过期时间
        pipe.expire(key, limit_config['window'])

        results = pipe.execute()
        request_count = results[2]

        return request_count <= limit_config['requests']

class JWTSecurityHandler(HTTPBearer):
    """JWT安全处理器"""

    def __init__(self):
        super().__init__(auto_error=False)
        self.jwt_service = JWTTokenManager()

    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        credentials = await super().__call__(request)

        if not credentials:
            return None

        # 验证Token
        payload = await self.jwt_service.validate_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )

        # 检查Token类型
        if payload.get("token_type") != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid token type"
            )

        # 设备指纹验证
        device_fingerprint = payload.get("device_fingerprint")
        current_fingerprint = self._generate_device_fingerprint(request)

        if device_fingerprint != current_fingerprint:
            # 记录可疑活动
            await self._log_suspicious_activity(
                payload.get("sub"),
                "device_fingerprint_mismatch",
                {
                    "expected": device_fingerprint,
                    "actual": current_fingerprint,
                    "ip": request.client.host
                }
            )

            raise HTTPException(
                status_code=401,
                detail="Device fingerprint mismatch"
            )

        # 将用户信息添加到请求上下文
        request.state.user_id = payload.get("sub")
        request.state.permissions = payload.get("scope", [])
        request.state.token_jti = payload.get("jti")

        return credentials

    def _generate_device_fingerprint(self, request: Request) -> str:
        """生成设备指纹"""
        fingerprint_data = {
            "user_agent": request.headers.get("user-agent", ""),
            "accept_language": request.headers.get("accept-language", ""),
            "accept_encoding": request.headers.get("accept-encoding", "")
        }

        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
```

### 10.2 输入验证和SQL注入防护

```python
# shared/validators/security_validators.py
import re
import html
import bleach
from typing import Any, Dict, List
from pydantic import BaseModel, validator
import sqlparse

class InputValidator:
    """输入验证器"""

    # 危险的SQL关键字
    SQL_INJECTION_PATTERNS = [
        r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b',
        r'[\'\"]\s*;\s*',
        r'--',
        r'/\*.*?\*/',
        r'\bor\s+1\s*=\s*1\b',
        r'\band\s+1\s*=\s*1\b'
    ]

    # XSS攻击模式
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*='
    ]

    @classmethod
    def validate_sql_injection(cls, value: str) -> bool:
        """检查SQL注入"""
        if not isinstance(value, str):
            return True

        value_lower = value.lower()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return False

        return True

    @classmethod
    def validate_xss(cls, value: str) -> bool:
        """检查XSS攻击"""
        if not isinstance(value, str):
            return True

        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return False

        return True

    @classmethod
    def sanitize_html(cls, value: str) -> str:
        """清理HTML内容"""
        if not isinstance(value, str):
            return value

        # 允许的HTML标签和属性
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
        allowed_attributes = {}

        # 使用bleach清理HTML
        cleaned = bleach.clean(
            value,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )

        # HTML转义
        return html.escape(cleaned)

    @classmethod
    def validate_file_path(cls, path: str) -> bool:
        """验证文件路径"""
        if not isinstance(path, str):
            return False

        # 检查路径遍历攻击
        dangerous_patterns = ['../', '..\\', './', '.\\']
        for pattern in dangerous_patterns:
            if pattern in path:
                return False

        # 检查绝对路径
        if path.startswith('/') or (len(path) > 1 and path[1] == ':'):
            return False

        return True

class SecureBaseModel(BaseModel):
    """安全的基础模型"""

    @validator('*', pre=True)
    def validate_input_security(cls, v):
        """通用输入安全验证"""
        if isinstance(v, str):
            # SQL注入检查
            if not InputValidator.validate_sql_injection(v):
                raise ValueError("Potential SQL injection detected")

            # XSS检查
            if not InputValidator.validate_xss(v):
                raise ValueError("Potential XSS attack detected")

            # 长度限制
            if len(v) > 10000:  # 10KB限制
                raise ValueError("Input too long")

        return v

# 安全的查询构建器
class SecureQueryBuilder:
    """安全的查询构建器"""

    def __init__(self, connection):
        self.connection = connection

    async def execute_safe_query(self, query: str, params: Dict[str, Any]) -> List[Dict]:
        """执行安全查询"""
        # 解析SQL查询
        parsed = sqlparse.parse(query)
        if len(parsed) != 1:
            raise ValueError("Multiple statements not allowed")

        statement = parsed[0]

        # 检查查询类型
        if not self._is_safe_query_type(statement):
            raise ValueError("Unsafe query type")

        # 验证参数
        self._validate_query_params(params)

        # 执行参数化查询
        return await self.connection.fetch(query, **params)

    def _is_safe_query_type(self, statement) -> bool:
        """检查查询类型是否安全"""
        # 只允许SELECT查询
        first_token = statement.tokens[0]
        return first_token.ttype == sqlparse.tokens.Keyword and \
               first_token.value.upper() == 'SELECT'

    def _validate_query_params(self, params: Dict[str, Any]):
        """验证查询参数"""
        for key, value in params.items():
            if isinstance(value, str):
                if not InputValidator.validate_sql_injection(value):
                    raise ValueError(f"Unsafe parameter value: {key}")
```

---

## 📋 总结

这个企业级认证系统后端架构采用了现代化的微服务设计，具备以下核心特性：

### 🎯 架构优势

1. **微服务架构**: 服务解耦，独立部署和扩展
2. **多层安全防护**: JWT + Session + RBAC + ABAC + 多因子认证
3. **高性能设计**: 多级缓存 + 读写分离 + 连接池优化
4. **企业级监控**: Prometheus + Grafana + ELK + 分布式链路追踪
5. **容器化部署**: Kubernetes + Istio + 自动扩缩容
6. **全面安全策略**: 输入验证 + SQL注入防护 + XSS防护 + 速率限制

### 🔧 技术栈总结

| 组件类型 | 技术选择 | 部署规模 |
|----------|----------|----------|
| **认证服务** | Python FastAPI | 3 实例 |
| **用户服务** | Python FastAPI | 3 实例 |
| **权限服务** | Python FastAPI | 3 实例 |
| **会话服务** | Go + Gin | 3 实例 |
| **通知服务** | Node.js + Express | 2 实例 |
| **数据库** | PostgreSQL 主从 | 1主2从 |
| **缓存** | Redis Cluster | 6节点集群 |
| **消息队列** | RabbitMQ | 3节点集群 |
| **API网关** | Kong + Istio | 高可用 |

### 📊 性能指标

- **认证响应时间**: < 100ms (95%请求)
- **权限检查**: < 50ms (99%请求)
- **并发用户**: 10,000+
- **TPS**: 5,000 tokens/秒生成
- **可用性**: 99.9%
- **扩展能力**: 支持水平扩展到100万用户

这个架构设计确保了Claude Enhancer认证系统能够满足企业级的安全性、性能和可扩展性要求，为现代应用提供可靠的身份认证和授权服务。