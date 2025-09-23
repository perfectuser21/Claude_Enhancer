# Claude Enhancer 用户认证系统架构设计

## 🎯 系统概述

Claude Enhancer用户认证系统是一个现代化、安全、可扩展的身份验证解决方案，采用JWT令牌管理、多层安全防护和灵活的权限控制机制。

### 核心设计理念
- **安全第一**: 多层安全防护，零信任架构
- **用户体验**: 无感知认证，快速响应
- **可扩展性**: 支持微服务，水平扩展
- **标准兼容**: 遵循OAuth 2.0、OpenID Connect标准

## 🏗️ 整体架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   客户端应用     │    │   负载均衡器     │    │   API网关       │
│                │    │                │    │                │
│ ├─ Web App      │    │ ├─ Nginx        │    │ ├─ 路由规则     │
│ ├─ Mobile App   │◄──►│ ├─ SSL终端      │◄──►│ ├─ 限流控制     │
│ └─ Third Party  │    │ └─ 健康检查     │    │ └─ 日志记录     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌─────────────────────────────────┼─────────────────────────────────┐
                       │                                │                                │
          ┌─────────────▼─────────────┐    ┌─────────────▼─────────────┐    ┌─────────────▼─────────────┐
          │     认证服务集群          │    │     用户服务集群          │    │     权限服务集群          │
          │                          │    │                          │    │                          │
          │ ├─ JWT Token管理         │    │ ├─ 用户注册/登录          │    │ ├─ 角色管理              │
          │ ├─ Session管理           │    │ ├─ 用户信息管理           │    │ ├─ 权限验证              │
          │ ├─ 密码加密验证          │    │ ├─ 密码策略管理           │    │ ├─ 资源访问控制          │
          │ └─ 多因子认证            │    │ └─ 用户状态管理           │    │ └─ 权限缓存              │
          └──────────────────────────┘    └──────────────────────────┘    └──────────────────────────┘
                       │                                │                                │
          ┌─────────────▼─────────────┐    ┌─────────────▼─────────────┐    ┌─────────────▼─────────────┐
          │     Redis缓存集群         │    │   PostgreSQL主从集群      │    │     日志监控系统          │
          │                          │    │                          │    │                          │
          │ ├─ Session存储           │    │ ├─ 用户数据存储           │    │ ├─ ELK日志栈             │
          │ ├─ Token黑名单           │    │ ├─ 权限数据存储           │    │ ├─ Prometheus监控        │
          │ ├─ 权限缓存              │    │ ├─ 审计日志存储           │    │ ├─ Grafana仪表板         │
          │ └─ 限流计数器            │    │ └─ 数据备份策略           │    │ └─ 告警通知系统          │
          └──────────────────────────┘    └──────────────────────────┘    └──────────────────────────┘
```

## 🔐 1. JWT Token管理系统

### Token架构设计

#### 双Token策略 (Access Token + Refresh Token)
```javascript
// Access Token结构 (短期，15分钟)
{
  "header": {
    "alg": "RS256",           // 使用RSA-256非对称加密
    "typ": "JWT",
    "kid": "auth-key-2024"    // 密钥ID，支持密钥轮换
  },
  "payload": {
    "iss": "perfect21-auth",   // 发行者
    "sub": "user_12345",       // 用户唯一标识
    "aud": "perfect21-api",    // 目标受众
    "exp": 1640995200,         // 过期时间 (15分钟后)
    "iat": 1640994300,         // 签发时间
    "jti": "token_uuid_123",   // Token唯一标识
    "scope": ["read", "write"], // 权限范围
    "role": "user",            // 用户角色
    "permissions": [           // 具体权限
      "todo:read",
      "todo:create",
      "profile:update"
    ]
  }
}

// Refresh Token结构 (长期，7天)
{
  "header": {
    "alg": "HS256",           // 使用HMAC-256对称加密
    "typ": "JWT"
  },
  "payload": {
    "iss": "perfect21-auth",
    "sub": "user_12345",
    "exp": 1641600000,        // 过期时间 (7天后)
    "iat": 1640994300,
    "jti": "refresh_uuid_456",
    "type": "refresh"         // Token类型标识
  }
}
```

#### Token生命周期管理
```python
class JWTTokenManager:
    def __init__(self):
        self.access_token_ttl = 900      # 15分钟
        self.refresh_token_ttl = 604800  # 7天
        self.key_rotation_interval = 86400  # 24小时轮换密钥

    def generate_token_pair(self, user_id: str, permissions: List[str]):
        """生成访问令牌和刷新令牌对"""
        access_token = self._create_access_token(user_id, permissions)
        refresh_token = self._create_refresh_token(user_id)

        # 存储到Redis用于快速验证和撤销
        self.redis_client.setex(
            f"access_token:{access_token['jti']}",
            self.access_token_ttl,
            json.dumps({"user_id": user_id, "active": True})
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": self.access_token_ttl
        }

    def revoke_token(self, token_jti: str):
        """撤销令牌 - 加入黑名单"""
        self.redis_client.sadd("token_blacklist", token_jti)
        self.redis_client.delete(f"access_token:{token_jti}")

    def rotate_keys(self):
        """定期轮换签名密钥"""
        new_private_key = generate_rsa_key_pair()
        self.key_store.add_key(f"auth-key-{datetime.now().strftime('%Y%m%d')}", new_private_key)
        # 保留旧密钥24小时用于验证现有token
```

### Token安全策略

#### 多层安全防护
1. **密钥管理**:
   - RSA-256非对称加密 (Access Token)
   - 密钥定期轮换 (24小时)
   - 硬件安全模块 (HSM) 存储私钥
   - 密钥版本控制和回滚

2. **Token防护**:
   - 短期有效期 (15分钟)
   - JTI唯一标识防重放
   - 即时撤销机制
   - 黑名单缓存

3. **传输安全**:
   - HTTPS强制加密
   - HTTP Strict Transport Security (HSTS)
   - Content Security Policy (CSP)
   - 安全请求头

## 👤 2. 用户注册/登录流程

### 用户注册流程

```mermaid
sequenceDiagram
    participant C as 客户端
    participant API as API网关
    participant Auth as 认证服务
    participant User as 用户服务
    participant DB as 数据库
    participant Email as 邮件服务

    C->>API: POST /auth/register
    Note over C,API: {email, password, profile}

    API->>Auth: 验证请求格式和频率限制
    Auth->>User: 检查邮箱唯一性
    User->>DB: SELECT user WHERE email = ?
    DB-->>User: 返回查询结果

    alt 邮箱已存在
        User-->>Auth: 邮箱已注册错误
        Auth-->>API: 400 Bad Request
        API-->>C: 注册失败
    else 邮箱可用
        Auth->>Auth: 生成密码哈希 (bcrypt + salt)
        Auth->>Auth: 生成邮箱验证令牌
        Auth->>User: 创建用户记录 (未激活状态)
        User->>DB: INSERT user (email, password_hash, verification_token)
        DB-->>User: 插入成功

        Auth->>Email: 发送验证邮件
        Email-->>Auth: 发送成功

        Auth-->>API: 201 Created
        API-->>C: 注册成功，请验证邮箱
    end
```

#### 注册安全策略
```python
class UserRegistrationService:
    def __init__(self):
        self.password_policy = PasswordPolicy()
        self.rate_limiter = RateLimiter()
        self.email_validator = EmailValidator()

    async def register_user(self, registration_data: UserRegistrationDTO):
        # 1. 频率限制检查
        if not self.rate_limiter.allow_request(
            key=f"register:{registration_data.ip}",
            limit=3,  # 每小时最多3次注册尝试
            window=3600
        ):
            raise TooManyRequestsError("注册尝试过于频繁")

        # 2. 邮箱格式和域名验证
        if not self.email_validator.is_valid(registration_data.email):
            raise ValidationError("邮箱格式无效")

        # 3. 密码强度验证
        if not self.password_policy.validate(registration_data.password):
            raise ValidationError("密码强度不符合要求")

        # 4. 防止用户枚举攻击
        if await self.user_service.email_exists(registration_data.email):
            # 不直接返回邮箱已存在，而是返回通用成功消息
            await self.send_existing_user_notification(registration_data.email)
            return {"message": "注册成功，请查收验证邮件"}

        # 5. 创建用户
        password_hash = await self.hash_password(registration_data.password)
        verification_token = self.generate_verification_token()

        user = await self.user_service.create_user({
            "email": registration_data.email,
            "password_hash": password_hash,
            "verification_token": verification_token,
            "status": UserStatus.PENDING_VERIFICATION,
            "created_at": datetime.utcnow()
        })

        # 6. 发送验证邮件
        await self.email_service.send_verification_email(
            user.email,
            verification_token
        )

        return {"message": "注册成功，请查收验证邮件"}
```

### 用户登录流程

```mermaid
sequenceDiagram
    participant C as 客户端
    participant API as API网关
    participant Auth as 认证服务
    participant Cache as Redis缓存
    participant DB as 数据库
    participant MFA as 多因子认证

    C->>API: POST /auth/login
    Note over C,API: {email, password, device_info}

    API->>Auth: 验证登录请求
    Auth->>Cache: 检查登录频率限制

    alt 超过频率限制
        Cache-->>Auth: 限制标识
        Auth-->>API: 429 Too Many Requests
        API-->>C: 登录尝试过于频繁
    else 允许登录
        Auth->>DB: 根据邮箱查询用户
        DB-->>Auth: 返回用户信息

        alt 用户不存在或密码错误
            Auth->>Auth: 记录失败尝试
            Auth->>Cache: 增加失败计数
            Auth-->>API: 401 Unauthorized
            API-->>C: 用户名或密码错误
        else 密码验证成功
            Auth->>Auth: 检查账户状态

            alt 需要多因子认证
                Auth->>MFA: 生成MFA挑战
                MFA-->>Auth: MFA令牌
                Auth-->>API: 200 + MFA Required
                API-->>C: 需要多因子认证

                C->>API: POST /auth/mfa/verify
                API->>MFA: 验证MFA代码

                alt MFA验证失败
                    MFA-->>Auth: 验证失败
                    Auth-->>API: 401 Unauthorized
                    API-->>C: MFA验证失败
                else MFA验证成功
                    MFA-->>Auth: 验证成功
                    Auth->>Auth: 生成JWT令牌对
                    Auth->>Cache: 存储Session信息
                    Auth-->>API: 200 + Token
                    API-->>C: 登录成功
                end
            else 直接登录成功
                Auth->>Auth: 生成JWT令牌对
                Auth->>Cache: 存储Session信息
                Auth->>DB: 更新最后登录时间
                Auth-->>API: 200 + Token
                API-->>C: 登录成功
            end
        end
    end
```

#### 登录安全策略
```python
class UserLoginService:
    def __init__(self):
        self.max_login_attempts = 5
        self.lockout_duration = 900  # 15分钟
        self.password_hasher = BCryptPasswordHasher()

    async def authenticate_user(self, login_data: UserLoginDTO):
        # 1. IP和用户级别的频率限制
        user_key = f"login_attempts:user:{login_data.email}"
        ip_key = f"login_attempts:ip:{login_data.ip}"

        if await self.is_rate_limited(user_key) or await self.is_rate_limited(ip_key):
            raise RateLimitExceededError("登录尝试过于频繁，请稍后再试")

        # 2. 获取用户信息
        user = await self.user_service.get_user_by_email(login_data.email)
        if not user:
            # 防止用户枚举攻击，执行虚假密码验证消耗相同时间
            await self.fake_password_verification()
            await self.record_failed_attempt(ip_key)
            raise AuthenticationError("用户名或密码错误")

        # 3. 检查账户状态
        if user.status == UserStatus.LOCKED:
            raise AccountLockedError("账户已被锁定，请联系管理员")
        elif user.status == UserStatus.PENDING_VERIFICATION:
            raise AccountNotVerifiedError("请先验证邮箱")

        # 4. 密码验证
        if not await self.password_hasher.verify(login_data.password, user.password_hash):
            await self.record_failed_attempt(user_key)
            await self.record_failed_attempt(ip_key)

            # 检查是否需要锁定账户
            if await self.should_lock_account(user_key):
                await self.user_service.lock_account(user.id)

            raise AuthenticationError("用户名或密码错误")

        # 5. 检查是否需要多因子认证
        if user.mfa_enabled:
            mfa_token = await self.mfa_service.generate_challenge(user.id)
            return {
                "requires_mfa": True,
                "mfa_token": mfa_token,
                "user_id": user.id
            }

        # 6. 生成认证令牌
        token_pair = await self.jwt_manager.generate_token_pair(
            user.id,
            await self.get_user_permissions(user.id)
        )

        # 7. 创建用户会话
        session = await self.session_service.create_session({
            "user_id": user.id,
            "device_info": login_data.device_info,
            "ip_address": login_data.ip,
            "user_agent": login_data.user_agent
        })

        # 8. 清除失败尝试记录
        await self.clear_failed_attempts(user_key)

        # 9. 更新登录统计
        await self.user_service.update_last_login(user.id)

        return {
            "access_token": token_pair["access_token"],
            "refresh_token": token_pair["refresh_token"],
            "expires_in": token_pair["expires_in"],
            "session_id": session.id,
            "user": await self.serialize_user(user)
        }
```

## 🔒 3. 密码加密策略

### 密码存储安全

#### 多层加密策略
```python
import bcrypt
import hashlib
import secrets
from cryptography.fernet import Fernet

class AdvancedPasswordHasher:
    def __init__(self):
        self.bcrypt_rounds = 12  # bcrypt工作因子
        self.pepper = self._load_pepper()  # 应用级密钥
        self.fernet = Fernet(self._load_encryption_key())

    async def hash_password(self, plain_password: str, user_salt: str = None) -> dict:
        """
        多层密码加密策略：
        1. 用户特定盐值 (User Salt)
        2. 应用级胡椒 (Application Pepper)
        3. bcrypt哈希 (Adaptive Hashing)
        4. 可选：对称加密 (Additional Encryption)
        """
        # 1. 生成用户特定盐值
        if not user_salt:
            user_salt = secrets.token_hex(32)

        # 2. 第一层：盐值 + 胡椒预处理
        salted_password = plain_password + user_salt + self.pepper

        # 3. 第二层：SHA-256预哈希（避免bcrypt长度限制）
        pre_hash = hashlib.sha256(salted_password.encode()).hexdigest()

        # 4. 第三层：bcrypt自适应哈希
        bcrypt_hash = bcrypt.hashpw(pre_hash.encode(), bcrypt.gensalt(rounds=self.bcrypt_rounds))

        # 5. 可选第四层：对称加密存储
        encrypted_hash = self.fernet.encrypt(bcrypt_hash)

        return {
            "password_hash": encrypted_hash.decode(),
            "user_salt": user_salt,
            "algorithm": "bcrypt+aes",
            "bcrypt_rounds": self.bcrypt_rounds,
            "created_at": datetime.utcnow().isoformat()
        }

    async def verify_password(self, plain_password: str, stored_hash_data: dict) -> bool:
        """验证密码"""
        try:
            # 1. 解密存储的哈希
            encrypted_hash = stored_hash_data["password_hash"].encode()
            bcrypt_hash = self.fernet.decrypt(encrypted_hash)

            # 2. 重构密码预处理
            salted_password = plain_password + stored_hash_data["user_salt"] + self.pepper
            pre_hash = hashlib.sha256(salted_password.encode()).hexdigest()

            # 3. bcrypt验证
            return bcrypt.checkpw(pre_hash.encode(), bcrypt_hash)

        except Exception as e:
            # 安全日志记录
            await self.security_logger.log_password_verification_error(e)
            return False

    def _load_pepper(self) -> str:
        """加载应用级胡椒密钥"""
        return os.environ.get("PASSWORD_PEPPER", secrets.token_hex(64))

    def _load_encryption_key(self) -> bytes:
        """加载对称加密密钥"""
        key = os.environ.get("PASSWORD_ENCRYPTION_KEY")
        if not key:
            raise SecurityError("密码加密密钥未配置")
        return key.encode()
```

### 密码策略管理

#### 密码复杂度要求
```python
class PasswordPolicy:
    def __init__(self):
        self.min_length = 12
        self.max_length = 128
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_numbers = True
        self.require_special_chars = True
        self.forbidden_patterns = [
            r'(.)\1{3,}',           # 连续相同字符
            r'(012|123|234|345|456|567|678|789|890)',  # 连续数字
            r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # 连续字母
        ]
        self.common_passwords = self._load_common_passwords()

    def validate(self, password: str) -> PasswordValidationResult:
        """验证密码强度"""
        errors = []
        score = 0

        # 1. 长度检查
        if len(password) < self.min_length:
            errors.append(f"密码长度至少{self.min_length}位")
        elif len(password) > self.max_length:
            errors.append(f"密码长度不能超过{self.max_length}位")
        else:
            score += min(len(password) * 2, 20)

        # 2. 字符类型检查
        char_types = 0
        if re.search(r'[a-z]', password):
            char_types += 1
        if re.search(r'[A-Z]', password):
            char_types += 1
        if re.search(r'[0-9]', password):
            char_types += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            char_types += 1

        if char_types < 3:
            errors.append("密码必须包含至少3种字符类型（大写字母、小写字母、数字、特殊字符）")
        else:
            score += char_types * 10

        # 3. 禁用模式检查
        for pattern in self.forbidden_patterns:
            if re.search(pattern, password, re.IGNORECASE):
                errors.append("密码不能包含连续重复的字符或序列")
                break

        # 4. 常见密码检查
        if password.lower() in self.common_passwords:
            errors.append("不能使用常见密码")
            score = 0

        # 5. 熵值计算
        entropy = self._calculate_entropy(password)
        if entropy < 60:
            errors.append("密码复杂度不足，请使用更随机的字符组合")
        else:
            score += min(entropy, 40)

        # 6. 总分评级
        if score >= 80:
            strength = "强"
        elif score >= 60:
            strength = "中等"
        elif score >= 40:
            strength = "弱"
        else:
            strength = "很弱"

        return PasswordValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            strength=strength,
            score=score
        )

    def _calculate_entropy(self, password: str) -> float:
        """计算密码熵值"""
        char_space = 0
        if re.search(r'[a-z]', password):
            char_space += 26
        if re.search(r'[A-Z]', password):
            char_space += 26
        if re.search(r'[0-9]', password):
            char_space += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            char_space += 32

        if char_space == 0:
            return 0

        return len(password) * math.log2(char_space)

    def _load_common_passwords(self) -> set:
        """加载常见密码字典"""
        # 从文件或数据库加载常见密码列表
        common_passwords = {
            "password", "123456", "password123", "admin", "qwerty",
            "letmein", "welcome", "monkey", "dragon", "master",
            # ... 更多常见密码
        }
        return common_passwords
```

## 🗄️ 4. Session管理系统

### Session架构设计

#### 分布式Session存储
```python
class DistributedSessionManager:
    def __init__(self):
        self.redis_cluster = RedisCluster()
        self.session_ttl = 1800  # 30分钟无活动超时
        self.max_sessions_per_user = 5  # 每用户最大并发会话数
        self.session_encryption = SessionEncryption()

    async def create_session(self, session_data: SessionCreateDTO) -> Session:
        """创建新的用户会话"""
        session_id = self._generate_session_id()

        # 1. 检查用户当前会话数
        user_sessions = await self.get_user_sessions(session_data.user_id)
        if len(user_sessions) >= self.max_sessions_per_user:
            # 删除最旧的会话
            oldest_session = min(user_sessions, key=lambda s: s.created_at)
            await self.destroy_session(oldest_session.id)

        # 2. 创建会话对象
        session = Session(
            id=session_id,
            user_id=session_data.user_id,
            ip_address=session_data.ip_address,
            user_agent=session_data.user_agent,
            device_fingerprint=self._generate_device_fingerprint(session_data),
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            is_active=True
        )

        # 3. 加密敏感信息
        encrypted_session = await self.session_encryption.encrypt_session(session)

        # 4. 存储到Redis集群
        session_key = f"session:{session_id}"
        user_sessions_key = f"user_sessions:{session_data.user_id}"

        await self.redis_cluster.setex(
            session_key,
            self.session_ttl,
            json.dumps(encrypted_session.dict())
        )

        # 5. 维护用户会话索引
        await self.redis_cluster.sadd(user_sessions_key, session_id)
        await self.redis_cluster.expire(user_sessions_key, self.session_ttl)

        # 6. 记录会话创建事件
        await self.audit_logger.log_session_created(session)

        return session

    async def validate_session(self, session_id: str) -> Optional[Session]:
        """验证会话有效性"""
        session_key = f"session:{session_id}"

        # 1. 从Redis获取会话数据
        session_data = await self.redis_cluster.get(session_key)
        if not session_data:
            return None

        # 2. 解密会话信息
        encrypted_session = json.loads(session_data)
        session = await self.session_encryption.decrypt_session(encrypted_session)

        # 3. 检查会话状态
        if not session.is_active:
            await self.destroy_session(session_id)
            return None

        # 4. 检查会话超时
        time_since_activity = datetime.utcnow() - session.last_activity
        if time_since_activity.total_seconds() > self.session_ttl:
            await self.destroy_session(session_id)
            return None

        # 5. 更新最后活动时间
        session.last_activity = datetime.utcnow()
        await self.update_session(session)

        return session

    async def refresh_session(self, session_id: str) -> bool:
        """刷新会话过期时间"""
        session = await self.validate_session(session_id)
        if not session:
            return False

        session_key = f"session:{session_id}"
        await self.redis_cluster.expire(session_key, self.session_ttl)

        return True

    async def destroy_session(self, session_id: str) -> bool:
        """销毁指定会话"""
        session_key = f"session:{session_id}"

        # 1. 获取会话信息用于日志记录
        session_data = await self.redis_cluster.get(session_key)
        if session_data:
            session = json.loads(session_data)

            # 2. 从用户会话索引中移除
            user_sessions_key = f"user_sessions:{session['user_id']}"
            await self.redis_cluster.srem(user_sessions_key, session_id)

            # 3. 删除会话数据
            await self.redis_cluster.delete(session_key)

            # 4. 记录会话销毁事件
            await self.audit_logger.log_session_destroyed(session_id, session['user_id'])

            return True

        return False

    async def destroy_all_user_sessions(self, user_id: str) -> int:
        """销毁用户的所有会话"""
        user_sessions_key = f"user_sessions:{user_id}"
        session_ids = await self.redis_cluster.smembers(user_sessions_key)

        destroyed_count = 0
        for session_id in session_ids:
            if await self.destroy_session(session_id):
                destroyed_count += 1

        await self.redis_cluster.delete(user_sessions_key)

        return destroyed_count

    def _generate_session_id(self) -> str:
        """生成安全的会话ID"""
        # 使用加密安全的随机数生成器
        return secrets.token_urlsafe(32)

    def _generate_device_fingerprint(self, session_data: SessionCreateDTO) -> str:
        """生成设备指纹"""
        fingerprint_data = f"{session_data.user_agent}:{session_data.screen_resolution}:{session_data.timezone}:{session_data.language}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()
```

### Session安全策略

#### 会话劫持防护
```python
class SessionSecurityManager:
    def __init__(self):
        self.ip_change_threshold = 3  # IP变化检测阈值
        self.suspicious_activity_patterns = [
            "rapid_requests",      # 快速连续请求
            "unusual_locations",   # 异常地理位置
            "device_fingerprint_mismatch",  # 设备指纹不匹配
            "concurrent_sessions_exceeded"   # 并发会话超限
        ]

    async def validate_session_security(self, session_id: str, request_context: RequestContext) -> SecurityValidationResult:
        """验证会话安全性"""
        session = await self.session_manager.get_session(session_id)
        if not session:
            return SecurityValidationResult(valid=False, reason="会话不存在")

        security_checks = []

        # 1. IP地址一致性检查
        if session.ip_address != request_context.ip_address:
            ip_change_count = await self.get_ip_change_count(session_id)
            if ip_change_count > self.ip_change_threshold:
                security_checks.append("ip_change_suspicious")
                await self.audit_logger.log_suspicious_activity(
                    session_id,
                    "频繁IP变化",
                    {"original_ip": session.ip_address, "new_ip": request_context.ip_address}
                )

        # 2. 设备指纹验证
        current_fingerprint = self._generate_device_fingerprint(request_context)
        if session.device_fingerprint != current_fingerprint:
            security_checks.append("device_fingerprint_mismatch")

        # 3. 地理位置异常检测
        if await self.is_unusual_location(session.ip_address, request_context.ip_address):
            security_checks.append("unusual_location")

        # 4. 请求频率检查
        if await self.detect_rapid_requests(session_id):
            security_checks.append("rapid_requests")

        # 5. 并发会话检查
        user_sessions = await self.session_manager.get_user_sessions(session.user_id)
        if len(user_sessions) > self.session_manager.max_sessions_per_user:
            security_checks.append("concurrent_sessions_exceeded")

        # 6. 根据风险级别决定处理方式
        if len(security_checks) >= 2:  # 高风险
            await self.handle_high_risk_session(session_id, security_checks)
            return SecurityValidationResult(valid=False, reason="会话安全风险过高")
        elif len(security_checks) == 1:  # 中风险
            await self.handle_medium_risk_session(session_id, security_checks)
            return SecurityValidationResult(valid=True, requires_verification=True)

        return SecurityValidationResult(valid=True)

    async def handle_high_risk_session(self, session_id: str, risk_factors: List[str]):
        """处理高风险会话"""
        # 1. 立即销毁会话
        await self.session_manager.destroy_session(session_id)

        # 2. 发送安全警告邮件给用户
        session = await self.session_manager.get_session(session_id)
        if session:
            await self.notification_service.send_security_alert(
                session.user_id,
                "检测到账户异常活动",
                {"risk_factors": risk_factors, "timestamp": datetime.utcnow()}
            )

        # 3. 记录安全事件
        await self.security_incident_tracker.record_incident({
            "type": "suspicious_session_activity",
            "session_id": session_id,
            "risk_factors": risk_factors,
            "action_taken": "session_destroyed"
        })

    async def handle_medium_risk_session(self, session_id: str, risk_factors: List[str]):
        """处理中风险会话"""
        # 1. 要求额外身份验证
        await self.session_manager.mark_session_requires_verification(session_id)

        # 2. 缩短会话有效期
        await self.session_manager.reduce_session_ttl(session_id, 300)  # 5分钟

        # 3. 记录可疑活动
        await self.audit_logger.log_suspicious_activity(
            session_id,
            "中等风险会话活动",
            {"risk_factors": risk_factors}
        )
```

## 🔐 5. 权限控制机制 (RBAC + ABAC)

### 权限模型设计

#### 基于角色的访问控制 (RBAC)
```sql
-- 权限数据库设计
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource VARCHAR(100) NOT NULL,        -- 资源类型 (如: todo, user, admin)
    action VARCHAR(50) NOT NULL,           -- 操作类型 (如: read, write, delete)
    scope VARCHAR(100) DEFAULT 'all',      -- 权限范围 (如: own, team, all)
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by UUID REFERENCES users(id),
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES users(id),
    expires_at TIMESTAMP,                  -- 可选的角色过期时间
    PRIMARY KEY (user_id, role_id)
);

-- 基础角色数据
INSERT INTO roles (name, description, is_system_role) VALUES
('super_admin', '超级管理员 - 拥有所有权限', TRUE),
('admin', '管理员 - 系统管理权限', TRUE),
('user_manager', '用户管理员 - 用户管理权限', TRUE),
('regular_user', '普通用户 - 基础功能权限', TRUE),
('readonly_user', '只读用户 - 只读权限', TRUE);

-- 基础权限数据
INSERT INTO permissions (resource, action, scope, description) VALUES
-- 用户相关权限
('user', 'read', 'own', '查看自己的用户信息'),
('user', 'read', 'all', '查看所有用户信息'),
('user', 'write', 'own', '修改自己的用户信息'),
('user', 'write', 'all', '修改所有用户信息'),
('user', 'delete', 'own', '删除自己的账户'),
('user', 'delete', 'all', '删除任意用户账户'),

-- Todo相关权限
('todo', 'read', 'own', '查看自己的待办事项'),
('todo', 'read', 'team', '查看团队的待办事项'),
('todo', 'read', 'all', '查看所有待办事项'),
('todo', 'write', 'own', '创建/修改自己的待办事项'),
('todo', 'write', 'team', '创建/修改团队的待办事项'),
('todo', 'write', 'all', '创建/修改所有待办事项'),
('todo', 'delete', 'own', '删除自己的待办事项'),
('todo', 'delete', 'team', '删除团队的待办事项'),
('todo', 'delete', 'all', '删除所有待办事项'),

-- 系统管理权限
('system', 'read', 'all', '查看系统配置和状态'),
('system', 'write', 'all', '修改系统配置'),
('admin_panel', 'access', 'all', '访问管理面板');
```

#### 基于属性的访问控制 (ABAC)
```python
from typing import Dict, Any, List
from enum import Enum

class AccessDecision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    NOT_APPLICABLE = "not_applicable"

class ABACPolicy:
    """基于属性的访问控制策略"""

    def __init__(self):
        self.policy_engine = PolicyEngine()
        self.attribute_provider = AttributeProvider()

    async def evaluate_access(self,
                            subject: Dict[str, Any],
                            resource: Dict[str, Any],
                            action: str,
                            environment: Dict[str, Any]) -> AccessDecision:
        """
        评估访问控制决策

        Args:
            subject: 主体属性 (用户信息、角色等)
            resource: 资源属性 (资源类型、所有者等)
            action: 操作类型 (read, write, delete等)
            environment: 环境属性 (时间、地点、设备等)
        """

        # 1. 收集所有相关属性
        context = await self._build_evaluation_context(subject, resource, action, environment)

        # 2. 执行策略评估
        policies = await self.policy_engine.get_applicable_policies(context)

        final_decision = AccessDecision.DENY  # 默认拒绝

        for policy in policies:
            decision = await policy.evaluate(context)

            if decision == AccessDecision.ALLOW:
                # 找到允许策略，但继续检查是否有拒绝策略
                final_decision = AccessDecision.ALLOW
            elif decision == AccessDecision.DENY:
                # 拒绝策略优先级最高
                return AccessDecision.DENY

        return final_decision

    async def _build_evaluation_context(self, subject, resource, action, environment) -> Dict[str, Any]:
        """构建策略评估上下文"""
        return {
            "subject": {
                "user_id": subject.get("user_id"),
                "roles": await self.attribute_provider.get_user_roles(subject.get("user_id")),
                "department": subject.get("department"),
                "security_clearance": subject.get("security_clearance"),
                "employment_status": subject.get("employment_status")
            },
            "resource": {
                "type": resource.get("type"),
                "owner_id": resource.get("owner_id"),
                "team_id": resource.get("team_id"),
                "classification": resource.get("classification"),
                "created_at": resource.get("created_at")
            },
            "action": action,
            "environment": {
                "time": environment.get("time", datetime.utcnow()),
                "location": environment.get("location"),
                "ip_address": environment.get("ip_address"),
                "device_type": environment.get("device_type"),
                "network_zone": await self._get_network_zone(environment.get("ip_address"))
            }
        }

class PolicyEngine:
    """策略引擎"""

    def __init__(self):
        self.policies = []
        self._load_policies()

    def _load_policies(self):
        """加载访问控制策略"""

        # 策略1: 工作时间访问控制
        self.policies.append(TimeBasedAccessPolicy())

        # 策略2: 地理位置访问控制
        self.policies.append(LocationBasedAccessPolicy())

        # 策略3: 资源所有者访问控制
        self.policies.append(OwnershipBasedAccessPolicy())

        # 策略4: 团队协作访问控制
        self.policies.append(TeamBasedAccessPolicy())

        # 策略5: 数据分类访问控制
        self.policies.append(ClassificationBasedAccessPolicy())

class TimeBasedAccessPolicy:
    """基于时间的访问控制策略"""

    async def evaluate(self, context: Dict[str, Any]) -> AccessDecision:
        current_time = context["environment"]["time"]
        user_roles = context["subject"]["roles"]

        # 管理员24/7访问
        if "admin" in user_roles or "super_admin" in user_roles:
            return AccessDecision.ALLOW

        # 普通用户工作时间访问 (9:00-18:00)
        if 9 <= current_time.hour <= 18:
            return AccessDecision.ALLOW

        # 非工作时间需要特殊权限
        if "after_hours_access" in user_roles:
            return AccessDecision.ALLOW

        return AccessDecision.DENY

class LocationBasedAccessPolicy:
    """基于地理位置的访问控制策略"""

    def __init__(self):
        self.allowed_countries = ["CN", "US", "CA", "GB"]  # 允许的国家代码
        self.restricted_ips = set()  # 受限IP地址

    async def evaluate(self, context: Dict[str, Any]) -> AccessDecision:
        ip_address = context["environment"]["ip_address"]
        location = context["environment"]["location"]

        # 检查IP是否在黑名单
        if ip_address in self.restricted_ips:
            return AccessDecision.DENY

        # 检查地理位置
        if location and location.get("country_code") not in self.allowed_countries:
            return AccessDecision.DENY

        return AccessDecision.NOT_APPLICABLE

class OwnershipBasedAccessPolicy:
    """基于所有权的访问控制策略"""

    async def evaluate(self, context: Dict[str, Any]) -> AccessDecision:
        user_id = context["subject"]["user_id"]
        resource_owner = context["resource"]["owner_id"]
        action = context["action"]

        # 资源所有者拥有完全访问权限
        if user_id == resource_owner:
            return AccessDecision.ALLOW

        # 非所有者只能读取（需要其他策略补充写权限）
        if action == "read":
            return AccessDecision.NOT_APPLICABLE

        return AccessDecision.NOT_APPLICABLE

class PermissionService:
    """权限服务"""

    def __init__(self):
        self.rbac_service = RBACService()
        self.abac_policy = ABACPolicy()
        self.permission_cache = PermissionCache()

    async def check_permission(self, user_id: str, resource_type: str, action: str, resource_context: Dict = None) -> bool:
        """检查用户权限"""

        # 1. 快速缓存检查
        cache_key = f"perm:{user_id}:{resource_type}:{action}"
        cached_result = await self.permission_cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # 2. RBAC权限检查
        rbac_allowed = await self.rbac_service.has_permission(user_id, resource_type, action)

        # 3. ABAC策略评估
        if resource_context:
            subject = await self._get_subject_attributes(user_id)
            resource = await self._get_resource_attributes(resource_type, resource_context)
            environment = await self._get_environment_attributes()

            abac_decision = await self.abac_policy.evaluate_access(
                subject, resource, action, environment
            )

            # 4. 综合决策：RBAC和ABAC都必须允许
            final_decision = rbac_allowed and (abac_decision == AccessDecision.ALLOW)
        else:
            final_decision = rbac_allowed

        # 5. 缓存结果 (短期缓存，5分钟)
        await self.permission_cache.set(cache_key, final_decision, ttl=300)

        return final_decision

    async def get_user_permissions(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有权限"""

        # 1. 获取用户角色
        user_roles = await self.rbac_service.get_user_roles(user_id)

        # 2. 获取角色权限
        permissions = []
        for role in user_roles:
            role_permissions = await self.rbac_service.get_role_permissions(role.id)
            permissions.extend(role_permissions)

        # 3. 去重并格式化
        unique_permissions = {}
        for perm in permissions:
            key = f"{perm.resource}:{perm.action}:{perm.scope}"
            if key not in unique_permissions:
                unique_permissions[key] = perm

        return list(unique_permissions.values())

    async def _get_subject_attributes(self, user_id: str) -> Dict[str, Any]:
        """获取主体属性"""
        user = await self.user_service.get_user(user_id)
        return {
            "user_id": user_id,
            "department": user.department,
            "security_clearance": user.security_clearance,
            "employment_status": user.employment_status
        }
```

## 📊 6. 系统监控和安全审计

### 安全事件监控

#### 实时安全监控
```python
class SecurityMonitor:
    def __init__(self):
        self.event_processor = SecurityEventProcessor()
        self.threat_detector = ThreatDetector()
        self.alert_manager = AlertManager()

    async def monitor_authentication_events(self):
        """监控认证相关安全事件"""

        security_events = [
            "login_attempt",
            "login_success",
            "login_failure",
            "password_change",
            "account_lockout",
            "suspicious_activity",
            "token_generation",
            "token_validation",
            "session_creation",
            "session_destruction"
        ]

        for event_type in security_events:
            await self.event_processor.register_handler(event_type, self._handle_security_event)

    async def _handle_security_event(self, event: SecurityEvent):
        """处理安全事件"""

        # 1. 记录事件
        await self.audit_logger.log_security_event(event)

        # 2. 威胁检测
        threat_level = await self.threat_detector.analyze_event(event)

        # 3. 根据威胁级别采取行动
        if threat_level == ThreatLevel.CRITICAL:
            await self._handle_critical_threat(event)
        elif threat_level == ThreatLevel.HIGH:
            await self._handle_high_threat(event)
        elif threat_level == ThreatLevel.MEDIUM:
            await self._handle_medium_threat(event)

    async def _handle_critical_threat(self, event: SecurityEvent):
        """处理严重威胁"""

        # 1. 立即锁定相关账户
        if event.user_id:
            await self.user_service.lock_account(event.user_id, reason="Critical security threat detected")

        # 2. 销毁所有相关会话
        if event.user_id:
            await self.session_manager.destroy_all_user_sessions(event.user_id)

        # 3. 发送紧急警报
        await self.alert_manager.send_critical_alert(
            f"Critical security threat detected: {event.event_type}",
            event.to_dict()
        )

        # 4. 自动创建安全事件工单
        await self.incident_manager.create_security_incident(event)

class ThreatDetector:
    """威胁检测器"""

    def __init__(self):
        self.ml_model = SecurityMLModel()
        self.rules_engine = SecurityRulesEngine()

    async def analyze_event(self, event: SecurityEvent) -> ThreatLevel:
        """分析安全事件威胁级别"""

        # 1. 基于规则的检测
        rule_based_score = await self.rules_engine.evaluate(event)

        # 2. 基于机器学习的检测
        ml_score = await self.ml_model.predict_threat_score(event)

        # 3. 综合评分
        combined_score = (rule_based_score * 0.6) + (ml_score * 0.4)

        # 4. 威胁级别分类
        if combined_score >= 0.9:
            return ThreatLevel.CRITICAL
        elif combined_score >= 0.7:
            return ThreatLevel.HIGH
        elif combined_score >= 0.4:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW

class SecurityRulesEngine:
    """安全规则引擎"""

    def __init__(self):
        self.rules = self._load_security_rules()

    async def evaluate(self, event: SecurityEvent) -> float:
        """评估事件的威胁评分"""
        total_score = 0.0
        applicable_rules = 0

        for rule in self.rules:
            if await rule.is_applicable(event):
                score = await rule.evaluate(event)
                total_score += score
                applicable_rules += 1

        return total_score / applicable_rules if applicable_rules > 0 else 0.0

    def _load_security_rules(self) -> List[SecurityRule]:
        """加载安全规则"""
        return [
            BruteForceDetectionRule(),
            AnomalousLocationRule(),
            UnusualTimeAccessRule(),
            MultipleFailedLoginsRule(),
            PrivilegeEscalationRule(),
            SuspiciousUserAgentRule()
        ]

class BruteForceDetectionRule(SecurityRule):
    """暴力破解检测规则"""

    async def is_applicable(self, event: SecurityEvent) -> bool:
        return event.event_type in ["login_failure", "login_attempt"]

    async def evaluate(self, event: SecurityEvent) -> float:
        # 检查短时间内的失败尝试次数
        time_window = timedelta(minutes=5)
        failed_attempts = await self.get_failed_attempts_count(
            event.ip_address,
            event.timestamp - time_window,
            event.timestamp
        )

        if failed_attempts >= 10:
            return 1.0  # 极高威胁
        elif failed_attempts >= 5:
            return 0.8  # 高威胁
        elif failed_attempts >= 3:
            return 0.5  # 中等威胁
        else:
            return 0.1  # 低威胁
```

### 审计日志系统

#### 完整审计跟踪
```python
class AuditLogger:
    """审计日志记录器"""

    def __init__(self):
        self.log_storage = AuditLogStorage()
        self.log_formatter = AuditLogFormatter()
        self.encryption = AuditLogEncryption()

    async def log_authentication_event(self, event_type: str, user_id: str, details: Dict[str, Any]):
        """记录认证事件"""

        audit_log = AuditLog(
            event_id=self._generate_event_id(),
            event_type=event_type,
            category="authentication",
            user_id=user_id,
            timestamp=datetime.utcnow(),
            ip_address=details.get("ip_address"),
            user_agent=details.get("user_agent"),
            details=details,
            severity=self._determine_severity(event_type)
        )

        await self._store_audit_log(audit_log)

    async def log_authorization_event(self, user_id: str, resource: str, action: str, result: bool, context: Dict):
        """记录授权事件"""

        audit_log = AuditLog(
            event_id=self._generate_event_id(),
            event_type="authorization_check",
            category="authorization",
            user_id=user_id,
            timestamp=datetime.utcnow(),
            resource=resource,
            action=action,
            result="allowed" if result else "denied",
            details=context,
            severity="medium" if not result else "low"
        )

        await self._store_audit_log(audit_log)

    async def log_security_incident(self, incident_type: str, details: Dict[str, Any]):
        """记录安全事件"""

        audit_log = AuditLog(
            event_id=self._generate_event_id(),
            event_type=incident_type,
            category="security_incident",
            user_id=details.get("user_id"),
            timestamp=datetime.utcnow(),
            ip_address=details.get("ip_address"),
            details=details,
            severity="high"
        )

        await self._store_audit_log(audit_log)

    async def _store_audit_log(self, audit_log: AuditLog):
        """存储审计日志"""

        # 1. 格式化日志
        formatted_log = await self.log_formatter.format(audit_log)

        # 2. 加密敏感信息
        encrypted_log = await self.encryption.encrypt_sensitive_fields(formatted_log)

        # 3. 存储到多个位置
        await asyncio.gather(
            self.log_storage.store_to_database(encrypted_log),
            self.log_storage.store_to_elasticsearch(encrypted_log),
            self.log_storage.store_to_file(encrypted_log)
        )

        # 4. 实时告警检查
        await self._check_for_alerts(audit_log)

class ComplianceReporter:
    """合规性报告生成器"""

    async def generate_security_report(self, start_date: datetime, end_date: datetime) -> SecurityReport:
        """生成安全报告"""

        # 1. 认证统计
        auth_stats = await self._get_authentication_statistics(start_date, end_date)

        # 2. 权限变更记录
        permission_changes = await self._get_permission_changes(start_date, end_date)

        # 3. 安全事件汇总
        security_incidents = await self._get_security_incidents(start_date, end_date)

        # 4. 合规性检查结果
        compliance_checks = await self._run_compliance_checks()

        return SecurityReport(
            period={"start": start_date, "end": end_date},
            authentication_statistics=auth_stats,
            permission_changes=permission_changes,
            security_incidents=security_incidents,
            compliance_status=compliance_checks,
            generated_at=datetime.utcnow()
        )
```

## 🚀 7. 部署和运维

### 容器化部署
```yaml
# docker-compose.yml
version: '3.8'

services:
  auth-service:
    build: ./auth-service
    environment:
      - DATABASE_URL=postgresql://perfect21:password@postgres:5432/perfect21_auth
      - REDIS_URL=redis://redis:6379
      - JWT_PRIVATE_KEY_PATH=/secrets/jwt_private_key.pem
      - JWT_PUBLIC_KEY_PATH=/secrets/jwt_public_key.pem
    volumes:
      - ./secrets:/secrets:ro
    depends_on:
      - postgres
      - redis
    networks:
      - perfect21-network

  user-service:
    build: ./user-service
    environment:
      - DATABASE_URL=postgresql://perfect21:password@postgres:5432/perfect21_users
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    networks:
      - perfect21-network

  permission-service:
    build: ./permission-service
    environment:
      - DATABASE_URL=postgresql://perfect21:password@postgres:5432/perfect21_permissions
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    networks:
      - perfect21-network

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=perfect21
      - POSTGRES_USER=perfect21
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    networks:
      - perfect21-network

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass redis_password
    volumes:
      - redis_data:/data
    networks:
      - perfect21-network

  api-gateway:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - auth-service
      - user-service
      - permission-service
    networks:
      - perfect21-network

volumes:
  postgres_data:
  redis_data:

networks:
  perfect21-network:
    driver: bridge
```

### Kubernetes部署配置
```yaml
# k8s/auth-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: perfect21-auth-service
  namespace: perfect21
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
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: perfect21-secrets
              key: redis-url
        - name: JWT_PRIVATE_KEY
          valueFrom:
            secretKeyRef:
              name: jwt-keys
              key: private-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
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
  namespace: perfect21
spec:
  selector:
    app: auth-service
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

## 📈 8. 性能优化策略

### 缓存策略
```python
class AuthenticationCache:
    """认证系统缓存管理"""

    def __init__(self):
        self.redis_client = RedisCluster()
        self.local_cache = LRUCache(maxsize=1000)

    async def cache_user_permissions(self, user_id: str, permissions: List[Permission], ttl: int = 3600):
        """缓存用户权限"""
        cache_key = f"user_permissions:{user_id}"
        permission_data = [perm.dict() for perm in permissions]

        # Redis缓存 (分布式)
        await self.redis_client.setex(
            cache_key,
            ttl,
            json.dumps(permission_data)
        )

        # 本地缓存 (更快访问)
        self.local_cache[cache_key] = permission_data

    async def get_cached_permissions(self, user_id: str) -> Optional[List[Permission]]:
        """获取缓存的用户权限"""
        cache_key = f"user_permissions:{user_id}"

        # 先检查本地缓存
        if cache_key in self.local_cache:
            permission_data = self.local_cache[cache_key]
            return [Permission(**perm) for perm in permission_data]

        # 再检查Redis缓存
        cached_data = await self.redis_client.get(cache_key)
        if cached_data:
            permission_data = json.loads(cached_data)
            # 回填本地缓存
            self.local_cache[cache_key] = permission_data
            return [Permission(**perm) for perm in permission_data]

        return None

    async def invalidate_user_cache(self, user_id: str):
        """使用户缓存失效"""
        patterns = [
            f"user_permissions:{user_id}",
            f"user_roles:{user_id}",
            f"user_sessions:{user_id}",
            f"perm:{user_id}:*"
        ]

        for pattern in patterns:
            # 清除Redis缓存
            if '*' in pattern:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            else:
                await self.redis_client.delete(pattern)

            # 清除本地缓存
            if '*' in pattern:
                prefix = pattern.replace('*', '')
                keys_to_remove = [key for key in self.local_cache.keys() if key.startswith(prefix)]
                for key in keys_to_remove:
                    del self.local_cache[key]
            else:
                self.local_cache.pop(pattern, None)

class PerformanceOptimizer:
    """性能优化器"""

    async def optimize_database_queries(self):
        """优化数据库查询"""

        # 1. 创建必要的索引
        await self._create_performance_indexes()

        # 2. 实现查询优化
        await self._implement_query_optimizations()

        # 3. 配置连接池
        await self._configure_connection_pooling()

    async def _create_performance_indexes(self):
        """创建性能索引"""
        indexes = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_status ON users(status)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_created_at ON user_sessions(created_at)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_permissions_resource_action ON permissions(resource, action)"
        ]

        for index_sql in indexes:
            await self.database.execute(index_sql)
```

## 🔒 9. 安全最佳实践总结

### 安全检查清单

#### 身份认证安全 ✅
- [ ] 强密码策略实施
- [ ] 多因子认证 (MFA) 支持
- [ ] 账户锁定机制
- [ ] 密码哈希使用bcrypt + 盐值
- [ ] 登录频率限制
- [ ] 会话超时管理

#### Token安全 ✅
- [ ] JWT使用RS256非对称加密
- [ ] Token短期有效 (15分钟)
- [ ] Refresh Token机制
- [ ] Token撤销/黑名单
- [ ] 密钥定期轮换

#### 传输安全 ✅
- [ ] HTTPS强制加密
- [ ] HSTS安全头
- [ ] CSP内容安全策略
- [ ] 安全Cookie设置

#### 数据保护 ✅
- [ ] 敏感数据加密存储
- [ ] 数据库连接加密
- [ ] 审计日志完整性
- [ ] 备份数据加密

#### 访问控制 ✅
- [ ] 最小权限原则
- [ ] 基于角色的访问控制 (RBAC)
- [ ] 基于属性的访问控制 (ABAC)
- [ ] 权限实时验证

---

## 📋 结论

Claude Enhancer用户认证系统采用现代化的安全架构设计，结合了以下核心特性：

### 🎯 核心优势
1. **多层安全防护**: JWT + Session + RBAC + ABAC
2. **高可用性**: 微服务架构，支持水平扩展
3. **实时监控**: 完整的安全事件监控和威胁检测
4. **合规性**: 满足行业安全标准和审计要求
5. **用户体验**: 无感知认证，快速响应

### 🔧 技术栈
- **后端**: Python FastAPI / Node.js Express
- **数据库**: PostgreSQL + Redis
- **缓存**: Redis Cluster
- **消息队列**: RabbitMQ / Kafka
- **监控**: ELK Stack + Prometheus + Grafana
- **部署**: Docker + Kubernetes

### 📊 性能指标
- **认证响应时间**: < 100ms
- **并发用户支持**: 10,000+
- **可用性**: 99.9%
- **安全事件响应**: < 5秒

该架构为Claude Enhancer项目提供了企业级的用户认证解决方案，确保系统安全性、可扩展性和高性能。

---

*文档版本: v1.0*
*生成时间: 2025-09-21*
*架构师: Claude Enhancer Team*