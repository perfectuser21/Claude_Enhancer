# 用户认证系统核心架构设计

## 🏗️ 系统架构概览

### 核心组件层次
```
┌─────────────────────────────────────────┐
│           客户端层 (Client Layer)        │
│   Web App / Mobile App / Third Party   │
└─────────────────┬───────────────────────┘
                  │ HTTPS + JWT
┌─────────────────▼───────────────────────┐
│          API网关层 (API Gateway)        │
│    认证中间件 + 路由 + 限流 + 日志      │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         认证服务层 (Auth Service)       │
│  JWT管理 + 密码验证 + 权限控制 + 会话   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         用户服务层 (User Service)       │
│   用户CRUD + 配置管理 + 状态管理       │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          数据层 (Data Layer)           │
│    PostgreSQL + Redis + 审计日志       │
└─────────────────────────────────────────┘
```

## 🔐 认证流程设计

### JWT认证流程
```
用户登录 → 验证凭据 → 生成JWT → 返回Token
    ↓
每次请求 → 携带JWT → 验证Token → 提取用户信息
    ↓
Token刷新 → 验证RefreshToken → 生成新JWT → 更新Token
```

### 核心API端点
```
POST /auth/login          # 用户登录
POST /auth/refresh        # 刷新Token
POST /auth/logout         # 用户登出
GET  /auth/verify         # 验证Token
POST /users/register      # 用户注册
GET  /users/profile       # 获取用户信息
PUT  /users/profile       # 更新用户信息
```

## 🛡️ 安全设计

### JWT安全策略
- **双Token机制**: AccessToken(15分钟) + RefreshToken(7天)
- **签名算法**: RS256 (非对称加密)
- **密钥轮换**: 每24小时自动轮换密钥
- **黑名单机制**: Redis存储已撤销的Token

### 密码安全
- **哈希算法**: bcrypt (成本因子12)
- **密码策略**: 最少8位，包含大小写字母+数字+特殊字符
- **登录保护**: 5次失败后锁定15分钟

## 🗄️ 数据库设计

### 核心表结构
```sql
-- 用户主表
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 用户配置表
CREATE TABLE user_profiles (
    user_id BIGINT REFERENCES users(id),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC'
);

-- 刷新Token表
CREATE TABLE refresh_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE
);
```

### Redis缓存策略
```
user_session:{user_id} → 用户会话信息 (TTL: 24h)
blacklist_token:{jti}  → 黑名单Token (TTL: Token过期时间)
login_attempts:{email} → 登录尝试次数 (TTL: 15min)
```

## 🧪 测试策略

### 测试金字塔
```
           ┌─────┐
          │ E2E  │ 10% - 完整用户流程
         └───────┘
        ┌─────────┐
       │集成测试  │ 30% - API端点 + 数据库
      └───────────┘
     ┌─────────────┐
    │   单元测试   │ 60% - 业务逻辑 + 工具函数
   └───────────────┘
```

### 关键测试场景
- **正常流程**: 注册→登录→访问→刷新→登出
- **安全测试**: SQL注入、XSS、CSRF防护
- **边界测试**: Token过期、并发登录、频率限制
- **错误处理**: 网络异常、数据库故障、无效请求

## 📊 性能指标

### 目标指标
- **登录响应时间**: < 200ms (P95)
- **Token验证**: < 50ms (P95)
- **并发支持**: 1000 req/s
- **可用性**: 99.9%

### 监控指标
- 登录成功率、失败率
- Token验证延迟
- 数据库连接池状态
- Redis命中率

## 🚀 部署架构

### 微服务部署
```
Load Balancer (Nginx)
    ↓
API Gateway (Kong/Envoy)
    ↓
Auth Service (Docker + K8s)
    ↓
Database Cluster (PostgreSQL + Redis)
```

### 环境配置
- **开发环境**: 单实例 + SQLite + 内存Redis
- **测试环境**: 容器化 + PostgreSQL + Redis
- **生产环境**: K8s集群 + 高可用数据库

## 🔧 技术栈建议

### 后端技术
- **框架**: FastAPI (Python) / Express.js (Node.js)
- **数据库**: PostgreSQL 14+
- **缓存**: Redis 7+
- **消息队列**: Redis Pub/Sub

### 开发工具
- **API文档**: OpenAPI/Swagger
- **代码质量**: ESLint/Pylint + Black/Prettier
- **测试框架**: pytest/Jest
- **监控**: Prometheus + Grafana

---

**架构总结**: 这是一个分层设计的认证系统，通过JWT实现无状态认证，使用双Token机制保证安全性，Redis缓存提升性能，PostgreSQL存储持久化数据。整体架构支持水平扩展，安全可靠。