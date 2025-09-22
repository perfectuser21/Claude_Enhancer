-- =====================================================
-- 企业级认证系统完整数据库架构设计
-- 设计理念：安全第一、高性能、高可用、可扩展
-- 支持：RBAC、MFA、OAuth2.0、JWT、审计、黑名单
-- =====================================================

-- 创建专用schema和扩展
CREATE SCHEMA IF NOT EXISTS auth_system;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
SET search_path = auth_system, public;

-- =====================================================
-- 1. 用户表（基本信息、密码、状态）
-- 设计原则：最小化敏感信息泄露、支持软删除、审计友好
-- =====================================================
CREATE TABLE auth_system.users (
    -- 主键和标识
    id BIGSERIAL PRIMARY KEY,
    uuid UUID NOT NULL DEFAULT uuid_generate_v4() UNIQUE,

    -- 登录凭据
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20),

    -- 密码安全 (采用bcrypt + salt)
    password_hash VARCHAR(255) NOT NULL,
    password_salt VARCHAR(64) NOT NULL DEFAULT encode(gen_random_bytes(32), 'hex'),
    password_version INTEGER NOT NULL DEFAULT 1, -- 支持密码算法升级
    password_changed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- 账户状态管理
    status user_status NOT NULL DEFAULT 'pending_verification',
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    phone_verified BOOLEAN NOT NULL DEFAULT FALSE,

    -- 安全锁定机制
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    lock_reason VARCHAR(100),

    -- 验证令牌 (支持多种验证场景)
    email_verification_token VARCHAR(255),
    email_verification_expires TIMESTAMPTZ,
    phone_verification_token VARCHAR(6),
    phone_verification_expires TIMESTAMPTZ,
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMPTZ,

    -- 用户档案信息
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    display_name VARCHAR(200),
    avatar_url TEXT,
    birth_date DATE,
    gender CHAR(1) CHECK (gender IN ('M', 'F', 'O')),

    -- 地区和时区
    country_code VARCHAR(2),
    timezone VARCHAR(50) DEFAULT 'UTC',
    locale VARCHAR(10) DEFAULT 'en_US',
    language VARCHAR(5) DEFAULT 'en',

    -- 隐私和偏好设置
    privacy_settings JSONB DEFAULT '{"profile_public": false, "email_notifications": true}',
    notification_preferences JSONB DEFAULT '{"email": true, "sms": false, "push": true}',

    -- 最后活动追踪
    last_login_at TIMESTAMPTZ,
    last_login_ip INET,
    last_activity_at TIMESTAMPTZ,

    -- 审计字段
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES auth_system.users(id),
    updated_by BIGINT REFERENCES auth_system.users(id),

    -- 软删除
    deleted_at TIMESTAMPTZ,
    deleted_by BIGINT REFERENCES auth_system.users(id),
    deletion_reason TEXT,

    -- 扩展字段 (灵活支持业务扩展)
    attributes JSONB DEFAULT '{}',
    tags TEXT[], -- 用户标签，支持分类和搜索

    -- 数据完整性约束
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_username_format CHECK (username ~* '^[a-zA-Z0-9_.-]{3,50}$'),
    CONSTRAINT users_phone_format CHECK (phone IS NULL OR phone ~* '^\+?[1-9]\d{1,14}$'),
    CONSTRAINT users_birth_date_valid CHECK (birth_date IS NULL OR birth_date < CURRENT_DATE),
    CONSTRAINT users_password_reset_consistency CHECK (
        (password_reset_token IS NULL AND password_reset_expires IS NULL) OR
        (password_reset_token IS NOT NULL AND password_reset_expires IS NOT NULL)
    ),
    CONSTRAINT users_email_verification_consistency CHECK (
        (email_verification_token IS NULL AND email_verification_expires IS NULL) OR
        (email_verification_token IS NOT NULL AND email_verification_expires IS NOT NULL)
    )
);

-- 创建枚举类型
CREATE TYPE user_status AS ENUM (
    'pending_verification',
    'active',
    'inactive',
    'suspended',
    'banned',
    'archived'
);

-- =====================================================
-- 2. 角色权限表（RBAC模型）
-- 设计原则：层级化管理、权限继承、动态权限分配
-- =====================================================

-- 角色表
CREATE TABLE auth_system.roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,

    -- 角色层级和继承
    parent_role_id BIGINT REFERENCES auth_system.roles(id),
    level INTEGER NOT NULL DEFAULT 0,
    hierarchy_path TEXT, -- 用于快速层级查询，如 "/1/3/7/"

    -- 角色类型和范围
    role_type role_type NOT NULL DEFAULT 'custom',
    scope VARCHAR(50) NOT NULL DEFAULT 'global', -- global, organization, department, project
    scope_id BIGINT, -- 对应范围的ID

    -- 权限定义 (支持细粒度控制)
    permissions JSONB NOT NULL DEFAULT '{}',
    restrictions JSONB DEFAULT '{}', -- 权限限制和约束

    -- 角色状态
    status role_status NOT NULL DEFAULT 'active',
    is_system_role BOOLEAN NOT NULL DEFAULT FALSE,
    is_default_role BOOLEAN NOT NULL DEFAULT FALSE,

    -- 权限继承控制
    inherit_permissions BOOLEAN NOT NULL DEFAULT TRUE,
    max_assignable_level INTEGER, -- 该角色最多能分配的权限级别

    -- 有效期管理
    valid_from TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMPTZ,

    -- 审计字段
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES auth_system.users(id),
    updated_by BIGINT REFERENCES auth_system.users(id)
);

CREATE TYPE role_type AS ENUM ('system', 'organization', 'department', 'project', 'custom');
CREATE TYPE role_status AS ENUM ('active', 'inactive', 'deprecated');

-- 权限资源定义表
CREATE TABLE auth_system.permissions (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,

    -- 权限分类和组织
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    resource_type VARCHAR(50) NOT NULL, -- user, role, session, api, data

    -- 权限级别和约束
    permission_level INTEGER NOT NULL DEFAULT 0,
    requires_mfa BOOLEAN NOT NULL DEFAULT FALSE,

    -- 操作定义
    actions TEXT[] NOT NULL DEFAULT '{}', -- read, write, delete, execute, admin
    resource_pattern VARCHAR(500), -- 资源匹配模式

    -- 条件和约束
    conditions JSONB DEFAULT '{}', -- 执行条件，如时间、IP限制等
    dependencies TEXT[], -- 依赖的其他权限

    -- 权限状态
    status permission_status NOT NULL DEFAULT 'active',
    risk_level risk_level NOT NULL DEFAULT 'low',

    -- 审计
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE permission_status AS ENUM ('active', 'inactive', 'deprecated');
CREATE TYPE risk_level AS ENUM ('critical', 'high', 'medium', 'low');

-- 用户角色分配表
CREATE TABLE auth_system.user_roles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_system.users(id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES auth_system.roles(id) ON DELETE CASCADE,

    -- 分配上下文
    assigned_by BIGINT NOT NULL REFERENCES auth_system.users(id),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assignment_reason TEXT,

    -- 有效期管理
    effective_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ,

    -- 权限覆盖 (针对特定用户的权限调整)
    permission_overrides JSONB DEFAULT '{}',

    -- 状态管理
    status assignment_status NOT NULL DEFAULT 'active',

    -- 审计追踪
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMPTZ,
    revoked_by BIGINT REFERENCES auth_system.users(id),
    revocation_reason TEXT,

    -- 唯一约束 (一个用户在特定范围内只能有一个同类角色)
    UNIQUE(user_id, role_id),

    -- 时间约束
    CONSTRAINT user_roles_valid_period CHECK (
        expires_at IS NULL OR expires_at > effective_from
    )
);

CREATE TYPE assignment_status AS ENUM ('active', 'inactive', 'suspended', 'expired', 'revoked');

-- 角色权限关联表
CREATE TABLE auth_system.role_permissions (
    id BIGSERIAL PRIMARY KEY,
    role_id BIGINT NOT NULL REFERENCES auth_system.roles(id) ON DELETE CASCADE,
    permission_id BIGINT NOT NULL REFERENCES auth_system.permissions(id) ON DELETE CASCADE,

    -- 权限配置
    granted BOOLEAN NOT NULL DEFAULT TRUE, -- 授予还是拒绝
    conditions JSONB DEFAULT '{}', -- 执行条件
    constraints JSONB DEFAULT '{}', -- 权限约束

    -- 审计
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    granted_by BIGINT NOT NULL REFERENCES auth_system.users(id),

    UNIQUE(role_id, permission_id)
);

-- =====================================================
-- 3. 会话表（活跃会话管理）
-- 设计原则：支持多设备、会话隔离、自动清理
-- =====================================================
CREATE TABLE auth_system.sessions (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(128) NOT NULL UNIQUE,
    user_id BIGINT NOT NULL REFERENCES auth_system.users(id) ON DELETE CASCADE,

    -- 会话类型和配置
    session_type session_type NOT NULL DEFAULT 'web',
    client_type client_type NOT NULL DEFAULT 'browser',

    -- 设备和环境信息
    device_id VARCHAR(100), -- 设备唯一标识
    device_name VARCHAR(200),
    device_fingerprint VARCHAR(128),
    user_agent TEXT,
    ip_address INET NOT NULL,

    -- 地理位置信息
    country_code VARCHAR(2),
    region VARCHAR(100),
    city VARCHAR(100),
    timezone VARCHAR(50),

    -- 安全上下文
    is_trusted_device BOOLEAN NOT NULL DEFAULT FALSE,
    requires_mfa BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_verified BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_method VARCHAR(20), -- totp, sms, email, hardware_key

    -- 会话状态和生命周期
    status session_status NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,

    -- 安全检测
    risk_score INTEGER DEFAULT 0 CHECK (risk_score >= 0 AND risk_score <= 100),
    security_flags TEXT[], -- suspicious_ip, unusual_location, etc.

    -- 会话配置
    max_idle_minutes INTEGER DEFAULT 30,
    remember_me BOOLEAN NOT NULL DEFAULT FALSE,
    concurrent_session_limit INTEGER DEFAULT 5,

    -- 扩展属性
    metadata JSONB DEFAULT '{}',

    -- 约束
    CONSTRAINT sessions_valid_expiry CHECK (expires_at > created_at),
    CONSTRAINT sessions_valid_activity CHECK (last_activity_at >= created_at),
    CONSTRAINT sessions_risk_score_valid CHECK (risk_score BETWEEN 0 AND 100)
);

CREATE TYPE session_type AS ENUM ('web', 'mobile', 'api', 'desktop', 'service');
CREATE TYPE client_type AS ENUM ('browser', 'mobile_app', 'desktop_app', 'api_client', 'service');
CREATE TYPE session_status AS ENUM ('active', 'expired', 'revoked', 'invalid', 'suspended');

-- =====================================================
-- 4. MFA表（多因素认证）
-- 设计原则：支持多种MFA方式、备份恢复、安全存储
-- =====================================================

-- MFA设备/方法注册表
CREATE TABLE auth_system.mfa_devices (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_system.users(id) ON DELETE CASCADE,

    -- 设备信息
    device_name VARCHAR(100) NOT NULL,
    device_type mfa_device_type NOT NULL,
    device_identifier VARCHAR(200), -- 设备唯一标识

    -- TOTP密钥 (加密存储)
    secret_key_encrypted TEXT, -- Base32编码的密钥，使用应用密钥加密
    secret_key_algorithm VARCHAR(10) DEFAULT 'SHA1',
    digits INTEGER DEFAULT 6 CHECK (digits IN (6, 8)),
    period INTEGER DEFAULT 30,

    -- SMS/Email配置
    phone_number VARCHAR(20),
    email_address VARCHAR(255),

    -- 硬件密钥信息
    public_key TEXT,
    key_handle TEXT,
    counter BIGINT DEFAULT 0,

    -- 推送通知配置
    push_token TEXT,
    push_service VARCHAR(20), -- fcm, apns

    -- 设备状态
    status mfa_device_status NOT NULL DEFAULT 'pending',
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    is_trusted BOOLEAN NOT NULL DEFAULT FALSE,

    -- 使用统计
    last_used_at TIMESTAMPTZ,
    use_count INTEGER NOT NULL DEFAULT 0,

    -- 安全设置
    max_attempts INTEGER DEFAULT 3,
    lockout_duration_minutes INTEGER DEFAULT 5,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,

    -- 审计
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMPTZ,

    -- 约束
    CONSTRAINT mfa_devices_phone_format CHECK (
        device_type != 'sms' OR phone_number ~* '^\+?[1-9]\d{1,14}$'
    ),
    CONSTRAINT mfa_devices_email_format CHECK (
        device_type != 'email' OR email_address ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    )
);

CREATE TYPE mfa_device_type AS ENUM (
    'totp',           -- Time-based OTP (Google Authenticator, Authy)
    'sms',            -- SMS验证码
    'email',          -- 邮箱验证码
    'hardware_key',   -- 硬件密钥 (YubiKey, etc.)
    'push',           -- 推送通知
    'backup_codes'    -- 备份恢复码
);

CREATE TYPE mfa_device_status AS ENUM ('pending', 'active', 'inactive', 'revoked', 'lost');

-- MFA备份恢复码表
CREATE TABLE auth_system.mfa_backup_codes (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_system.users(id) ON DELETE CASCADE,

    -- 恢复码 (哈希存储)
    code_hash VARCHAR(255) NOT NULL,
    code_partial VARCHAR(4) NOT NULL, -- 显示用的部分码，如 "AB**"

    -- 状态管理
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    used_at TIMESTAMPTZ,
    used_ip INET,

    -- 生成信息
    generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ,

    -- 约束
    CONSTRAINT backup_codes_valid_expiry CHECK (
        expires_at IS NULL OR expires_at > generated_at
    )
);

-- MFA验证日志
CREATE TABLE auth_system.mfa_verifications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_system.users(id) ON DELETE CASCADE,
    mfa_device_id BIGINT REFERENCES auth_system.mfa_devices(id),
    session_id VARCHAR(128) REFERENCES auth_system.sessions(session_id),

    -- 验证详情
    verification_type mfa_verification_type NOT NULL,
    challenge_code VARCHAR(10), -- 发送的挑战码
    submitted_code VARCHAR(10), -- 用户提交的码

    -- 验证结果
    status mfa_verification_status NOT NULL,
    failure_reason VARCHAR(100),

    -- 上下文信息
    ip_address INET,
    user_agent TEXT,

    -- 时间戳
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE TYPE mfa_verification_type AS ENUM ('login', 'transaction', 'settings_change', 'password_reset');
CREATE TYPE mfa_verification_status AS ENUM ('pending', 'success', 'failed', 'expired', 'cancelled');

-- =====================================================
-- 5. OAuth表（客户端、授权码、令牌）
-- 设计原则：OAuth 2.0/OIDC标准合规、安全令牌管理
-- =====================================================

-- OAuth客户端注册表
CREATE TABLE auth_system.oauth_clients (
    id BIGSERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL UNIQUE,
    client_secret_hash VARCHAR(255), -- 机密客户端才有

    -- 客户端基本信息
    name VARCHAR(200) NOT NULL,
    description TEXT,
    website_url VARCHAR(500),
    logo_url VARCHAR(500),

    -- 客户端类型和配置
    client_type oauth_client_type NOT NULL,
    application_type oauth_application_type NOT NULL DEFAULT 'web',

    -- 重定向和CORS配置
    redirect_uris TEXT[] NOT NULL DEFAULT '{}',
    post_logout_redirect_uris TEXT[] DEFAULT '{}',
    allowed_origins TEXT[] DEFAULT '{}',

    -- 授权配置
    grant_types oauth_grant_type[] NOT NULL DEFAULT '{authorization_code}',
    response_types VARCHAR(50)[] NOT NULL DEFAULT '{code}',
    scope TEXT NOT NULL DEFAULT 'openid profile email',

    -- 令牌配置
    access_token_lifetime_seconds INTEGER NOT NULL DEFAULT 3600,
    refresh_token_lifetime_seconds INTEGER NOT NULL DEFAULT 2592000, -- 30天
    id_token_lifetime_seconds INTEGER NOT NULL DEFAULT 3600,
    authorization_code_lifetime_seconds INTEGER NOT NULL DEFAULT 600, -- 10分钟

    -- 安全设置
    require_auth_time BOOLEAN NOT NULL DEFAULT FALSE,
    require_pkce BOOLEAN NOT NULL DEFAULT TRUE, -- 推荐所有客户端启用PKCE
    allow_plain_pkce BOOLEAN NOT NULL DEFAULT FALSE,
    require_consent BOOLEAN NOT NULL DEFAULT TRUE,

    -- 客户端状态
    status oauth_client_status NOT NULL DEFAULT 'pending',
    is_first_party BOOLEAN NOT NULL DEFAULT FALSE, -- 是否为第一方应用

    -- 联系信息
    contact_email VARCHAR(255),
    tos_uri VARCHAR(500),
    policy_uri VARCHAR(500),

    -- 审计
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES auth_system.users(id),

    -- 软删除
    deleted_at TIMESTAMPTZ,

    -- 约束
    CONSTRAINT oauth_clients_redirect_uris_not_empty CHECK (array_length(redirect_uris, 1) > 0),
    CONSTRAINT oauth_clients_grant_types_not_empty CHECK (array_length(grant_types, 1) > 0),
    CONSTRAINT oauth_clients_contact_email_format CHECK (
        contact_email IS NULL OR contact_email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    )
);

CREATE TYPE oauth_client_type AS ENUM ('confidential', 'public');
CREATE TYPE oauth_application_type AS ENUM ('web', 'native', 'spa');
CREATE TYPE oauth_grant_type AS ENUM (
    'authorization_code',
    'client_credentials',
    'refresh_token',
    'password',
    'implicit',
    'device_code'
);
CREATE TYPE oauth_client_status AS ENUM ('pending', 'active', 'suspended', 'revoked');

-- OAuth授权码表
CREATE TABLE auth_system.oauth_authorization_codes (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(255) NOT NULL UNIQUE,
    client_id VARCHAR(255) NOT NULL REFERENCES auth_system.oauth_clients(client_id),
    user_id BIGINT NOT NULL REFERENCES auth_system.users(id) ON DELETE CASCADE,

    -- PKCE支持
    code_challenge VARCHAR(128),
    code_challenge_method VARCHAR(10) CHECK (code_challenge_method IN ('plain', 'S256')),

    -- 授权范围
    scope TEXT NOT NULL,
    redirect_uri VARCHAR(500) NOT NULL,
    state VARCHAR(500),
    nonce VARCHAR(255), -- OIDC nonce

    -- 状态和时间
    status oauth_code_status NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,

    -- 安全上下文
    ip_address INET,
    user_agent TEXT,

    -- 约束
    CONSTRAINT oauth_codes_valid_expiry CHECK (expires_at > created_at),
    CONSTRAINT oauth_codes_pkce_consistency CHECK (
        (code_challenge IS NULL AND code_challenge_method IS NULL) OR
        (code_challenge IS NOT NULL AND code_challenge_method IS NOT NULL)
    )
);

CREATE TYPE oauth_code_status AS ENUM ('active', 'used', 'expired', 'revoked');

-- OAuth访问令牌表
CREATE TABLE auth_system.oauth_access_tokens (
    id BIGSERIAL PRIMARY KEY,
    token_hash VARCHAR(255) NOT NULL UNIQUE, -- SHA256哈希
    token_prefix VARCHAR(10) NOT NULL, -- 用于查找和撤销

    client_id VARCHAR(255) NOT NULL REFERENCES auth_system.oauth_clients(client_id),
    user_id BIGINT REFERENCES auth_system.users(id) ON DELETE CASCADE,

    -- 令牌信息
    scope TEXT NOT NULL,
    token_type VARCHAR(20) NOT NULL DEFAULT 'Bearer',

    -- 关联的授权码或刷新令牌
    authorization_code_id BIGINT REFERENCES auth_system.oauth_authorization_codes(id),
    refresh_token_id BIGINT,

    -- 状态和时间
    status oauth_token_status NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    last_used_at TIMESTAMPTZ,

    -- 使用统计
    use_count INTEGER NOT NULL DEFAULT 0,

    -- 安全上下文
    ip_address INET,
    user_agent TEXT,

    -- 约束
    CONSTRAINT oauth_access_tokens_valid_expiry CHECK (expires_at > created_at)
);

-- OAuth刷新令牌表
CREATE TABLE auth_system.oauth_refresh_tokens (
    id BIGSERIAL PRIMARY KEY,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    token_prefix VARCHAR(10) NOT NULL,

    client_id VARCHAR(255) NOT NULL REFERENCES auth_system.oauth_clients(client_id),
    user_id BIGINT NOT NULL REFERENCES auth_system.users(id) ON DELETE CASCADE,

    -- 令牌族管理 (用于令牌轮换)
    token_family_id UUID NOT NULL DEFAULT uuid_generate_v4(),
    previous_token_id BIGINT REFERENCES auth_system.oauth_refresh_tokens(id),

    -- 令牌信息
    scope TEXT NOT NULL,

    -- 状态和时间
    status oauth_token_status NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    last_used_at TIMESTAMPTZ,
    rotated_at TIMESTAMPTZ,

    -- 使用统计
    use_count INTEGER NOT NULL DEFAULT 0,

    -- 安全上下文
    ip_address INET,
    user_agent TEXT,

    -- 约束
    CONSTRAINT oauth_refresh_tokens_valid_expiry CHECK (expires_at > created_at)
);

CREATE TYPE oauth_token_status AS ENUM ('active', 'expired', 'revoked', 'rotated');

-- OAuth用户授权记录
CREATE TABLE auth_system.oauth_user_consents (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_system.users(id) ON DELETE CASCADE,
    client_id VARCHAR(255) NOT NULL REFERENCES auth_system.oauth_clients(client_id),

    -- 授权范围
    scope TEXT NOT NULL,
    granted_scopes TEXT[] NOT NULL,
    denied_scopes TEXT[] DEFAULT '{}',

    -- 授权状态
    status oauth_consent_status NOT NULL DEFAULT 'granted',

    -- 时间管理
    granted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,

    -- 记录上下文
    ip_address INET,
    user_agent TEXT,

    UNIQUE(user_id, client_id)
);

CREATE TYPE oauth_consent_status AS ENUM ('granted', 'denied', 'revoked', 'expired');

-- =====================================================
-- 6. 审计日志表（分区表设计）
-- 设计原则：高性能写入、历史数据归档、合规审计
-- =====================================================

-- 审计日志主表 (按月分区)
CREATE TABLE auth_system.audit_logs (
    id BIGSERIAL,

    -- 操作主体标识
    user_id BIGINT REFERENCES auth_system.users(id),
    session_id VARCHAR(128) REFERENCES auth_system.sessions(session_id),
    client_id VARCHAR(255) REFERENCES auth_system.oauth_clients(client_id),

    -- 操作分类
    event_category audit_event_category NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_action VARCHAR(50) NOT NULL,

    -- 资源信息
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    resource_name VARCHAR(200),

    -- 操作结果
    status audit_status NOT NULL,
    error_code VARCHAR(50),
    error_message TEXT,

    -- 请求上下文
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    correlation_id VARCHAR(100), -- 用于关联相关操作

    -- 地理位置
    country_code VARCHAR(2),
    region VARCHAR(100),
    city VARCHAR(100),

    -- 变更内容 (敏感信息脱敏)
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],

    -- 风险评估
    risk_score INTEGER DEFAULT 0 CHECK (risk_score >= 0 AND risk_score <= 100),
    security_flags TEXT[],

    -- 合规标记
    compliance_tags TEXT[],
    retention_period_days INTEGER DEFAULT 2555, -- 7年

    -- 时间戳
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 额外上下文
    metadata JSONB DEFAULT '{}',

    -- 分区键
    partition_date DATE NOT NULL GENERATED ALWAYS AS (created_at::DATE) STORED,

    PRIMARY KEY (id, partition_date)
) PARTITION BY RANGE (partition_date);

CREATE TYPE audit_event_category AS ENUM (
    'authentication',  -- 认证相关
    'authorization',   -- 授权相关
    'user_management', -- 用户管理
    'session_management', -- 会话管理
    'mfa',            -- 多因素认证
    'oauth',          -- OAuth操作
    'security',       -- 安全事件
    'system',         -- 系统操作
    'compliance'      -- 合规操作
);

CREATE TYPE audit_status AS ENUM ('success', 'failure', 'partial', 'blocked', 'suspicious');

-- 创建分区表函数
CREATE OR REPLACE FUNCTION auth_system.create_audit_log_partition(start_date DATE, end_date DATE)
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
BEGIN
    partition_name := 'audit_logs_' || to_char(start_date, 'YYYY_MM');

    EXECUTE format('
        CREATE TABLE IF NOT EXISTS auth_system.%I PARTITION OF auth_system.audit_logs
        FOR VALUES FROM (%L) TO (%L)
    ', partition_name, start_date, end_date);

    -- 创建分区索引
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON auth_system.%I (created_at, user_id)',
                   'idx_' || partition_name || '_created_user', partition_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON auth_system.%I (event_category, event_type)',
                   'idx_' || partition_name || '_event', partition_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON auth_system.%I (ip_address)',
                   'idx_' || partition_name || '_ip', partition_name);
END;
$$ LANGUAGE plpgsql;

-- 自动创建分区的函数
CREATE OR REPLACE FUNCTION auth_system.ensure_audit_log_partitions()
RETURNS VOID AS $$
DECLARE
    current_month DATE;
    next_month DATE;
BEGIN
    -- 创建当前月份和未来3个月的分区
    FOR i IN 0..3 LOOP
        current_month := date_trunc('month', CURRENT_DATE + (i || ' months')::INTERVAL)::DATE;
        next_month := current_month + INTERVAL '1 month';

        PERFORM auth_system.create_audit_log_partition(current_month, next_month);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 初始化分区
SELECT auth_system.ensure_audit_log_partitions();

-- =====================================================
-- 7. 黑名单表（token、IP、设备）
-- 设计原则：快速查询、自动清理、分层防护
-- =====================================================

-- IP黑名单表
CREATE TABLE auth_system.ip_blacklist (
    id BIGSERIAL PRIMARY KEY,
    ip_address INET NOT NULL,
    ip_range CIDR, -- 支持IP段封禁

    -- 封禁原因和类型
    block_type ip_block_type NOT NULL,
    reason VARCHAR(200) NOT NULL,
    severity block_severity NOT NULL DEFAULT 'medium',

    -- 检测信息
    detection_method VARCHAR(50), -- manual, auto_bruteforce, auto_geo, etc.
    detection_details JSONB DEFAULT '{}',

    -- 影响范围
    affects_services TEXT[] DEFAULT '{}', -- 可以指定只影响特定服务

    -- 时间管理
    blocked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ,
    last_attempt_at TIMESTAMPTZ,

    -- 统计信息
    attempt_count INTEGER NOT NULL DEFAULT 0,

    -- 状态
    status blacklist_status NOT NULL DEFAULT 'active',

    -- 审计
    created_by BIGINT REFERENCES auth_system.users(id),
    updated_by BIGINT REFERENCES auth_system.users(id),

    -- 约束
    CONSTRAINT ip_blacklist_valid_expiry CHECK (
        expires_at IS NULL OR expires_at > blocked_at
    ),
    CONSTRAINT ip_blacklist_ip_specification CHECK (
        ip_address IS NOT NULL OR ip_range IS NOT NULL
    )
);

CREATE TYPE ip_block_type AS ENUM (
    'brute_force',     -- 暴力破解
    'suspicious',      -- 可疑活动
    'malicious',       -- 恶意行为
    'compliance',      -- 合规要求
    'manual',          -- 手动封禁
    'geographic'       -- 地理位置限制
);

CREATE TYPE block_severity AS ENUM ('critical', 'high', 'medium', 'low');
CREATE TYPE blacklist_status AS ENUM ('active', 'inactive', 'expired', 'whitelist_override');

-- 令牌黑名单表 (撤销的JWT/OAuth令牌)
CREATE TABLE auth_system.token_blacklist (
    id BIGSERIAL PRIMARY KEY,
    token_id VARCHAR(255) NOT NULL UNIQUE, -- JWT的jti或OAuth token的ID
    token_type token_blacklist_type NOT NULL,
    token_hash VARCHAR(255), -- 用于快速查找

    -- 令牌信息
    user_id BIGINT REFERENCES auth_system.users(id),
    client_id VARCHAR(255) REFERENCES auth_system.oauth_clients(client_id),
    issued_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,

    -- 撤销信息
    revoked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_by BIGINT REFERENCES auth_system.users(id),
    revocation_reason VARCHAR(200),

    -- 撤销类型
    revocation_type token_revocation_type NOT NULL DEFAULT 'manual',

    -- 索引字段 (用于快速查询)
    partition_date DATE NOT NULL GENERATED ALWAYS AS (revoked_at::DATE) STORED
) PARTITION BY RANGE (partition_date);

CREATE TYPE token_blacklist_type AS ENUM ('jwt_access', 'jwt_refresh', 'oauth_access', 'oauth_refresh', 'session');
CREATE TYPE token_revocation_type AS ENUM (
    'manual',          -- 手动撤销
    'logout',          -- 登出撤销
    'password_change', -- 密码变更撤销
    'security_breach', -- 安全事件撤销
    'admin_action',    -- 管理员操作
    'expiry'          -- 过期清理
);

-- 设备黑名单表
CREATE TABLE auth_system.device_blacklist (
    id BIGSERIAL PRIMARY KEY,
    device_fingerprint VARCHAR(128) NOT NULL UNIQUE,
    device_id VARCHAR(100),

    -- 设备信息
    device_name VARCHAR(200),
    user_agent TEXT,
    last_seen_ip INET,

    -- 封禁信息
    blocked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    block_reason VARCHAR(200) NOT NULL,
    block_type device_block_type NOT NULL,

    -- 关联用户
    associated_user_ids BIGINT[] DEFAULT '{}',

    -- 状态
    status blacklist_status NOT NULL DEFAULT 'active',
    expires_at TIMESTAMPTZ,

    -- 审计
    created_by BIGINT REFERENCES auth_system.users(id),
    last_activity_at TIMESTAMPTZ
);

CREATE TYPE device_block_type AS ENUM ('malware', 'stolen', 'compromised', 'policy_violation', 'manual');

-- 用户黑名单表 (账户封禁记录)
CREATE TABLE auth_system.user_blacklist (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_system.users(id),

    -- 封禁信息
    block_type user_block_type NOT NULL,
    block_reason VARCHAR(500) NOT NULL,
    severity block_severity NOT NULL DEFAULT 'medium',

    -- 时间管理
    blocked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ,

    -- 影响范围
    blocked_services TEXT[] DEFAULT '{}', -- 可以部分服务封禁

    -- 状态
    status blacklist_status NOT NULL DEFAULT 'active',

    -- 审计
    blocked_by BIGINT NOT NULL REFERENCES auth_system.users(id),
    review_required BOOLEAN NOT NULL DEFAULT FALSE,
    last_reviewed_at TIMESTAMPTZ,
    reviewed_by BIGINT REFERENCES auth_system.users(id),

    -- 申诉信息
    appeal_submitted BOOLEAN NOT NULL DEFAULT FALSE,
    appeal_details TEXT,
    appeal_status VARCHAR(20) DEFAULT 'none' CHECK (appeal_status IN ('none', 'pending', 'approved', 'denied'))
);

CREATE TYPE user_block_type AS ENUM (
    'policy_violation',
    'security_breach',
    'fraud',
    'abuse',
    'spam',
    'legal_requirement',
    'manual'
);

-- =====================================================
-- 8. 索引优化策略
-- 设计原则：读写平衡、查询模式优化、分区感知
-- =====================================================

-- users表索引策略
CREATE UNIQUE INDEX CONCURRENTLY idx_users_uuid ON auth_system.users(uuid) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX CONCURRENTLY idx_users_email_active ON auth_system.users(email) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX CONCURRENTLY idx_users_username_active ON auth_system.users(username) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_users_phone_active ON auth_system.users(phone) WHERE phone IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_users_status_active ON auth_system.users(status) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_users_last_login ON auth_system.users(last_login_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_users_created_at ON auth_system.users(created_at);
CREATE INDEX CONCURRENTLY idx_users_tags ON auth_system.users USING GIN(tags) WHERE deleted_at IS NULL;

-- 验证令牌快速查找索引
CREATE INDEX CONCURRENTLY idx_users_email_verification_token ON auth_system.users(email_verification_token)
    WHERE email_verification_token IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_users_password_reset_token ON auth_system.users(password_reset_token)
    WHERE password_reset_token IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_users_phone_verification_token ON auth_system.users(phone_verification_token)
    WHERE phone_verification_token IS NOT NULL;

-- roles和权限索引
CREATE UNIQUE INDEX CONCURRENTLY idx_roles_name ON auth_system.roles(name);
CREATE INDEX CONCURRENTLY idx_roles_level_status ON auth_system.roles(level, status);
CREATE INDEX CONCURRENTLY idx_roles_parent ON auth_system.roles(parent_role_id) WHERE parent_role_id IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_roles_scope ON auth_system.roles(scope, scope_id);
CREATE INDEX CONCURRENTLY idx_roles_hierarchy_path ON auth_system.roles USING GIST(hierarchy_path);

CREATE UNIQUE INDEX CONCURRENTLY idx_permissions_name ON auth_system.permissions(name);
CREATE INDEX CONCURRENTLY idx_permissions_category ON auth_system.permissions(category, subcategory);
CREATE INDEX CONCURRENTLY idx_permissions_resource_type ON auth_system.permissions(resource_type);

-- user_roles关联索引
CREATE INDEX CONCURRENTLY idx_user_roles_user_active ON auth_system.user_roles(user_id, status) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_user_roles_role_active ON auth_system.user_roles(role_id, status) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_user_roles_expires ON auth_system.user_roles(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_user_roles_effective ON auth_system.user_roles(effective_from, expires_at);

-- sessions表高性能索引
CREATE UNIQUE INDEX CONCURRENTLY idx_sessions_session_id ON auth_system.sessions(session_id);
CREATE INDEX CONCURRENTLY idx_sessions_user_active ON auth_system.sessions(user_id, status) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_sessions_expires ON auth_system.sessions(expires_at) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_sessions_last_activity ON auth_system.sessions(last_activity_at) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_sessions_cleanup ON auth_system.sessions(status, expires_at, last_activity_at);
CREATE INDEX CONCURRENTLY idx_sessions_device ON auth_system.sessions(device_fingerprint) WHERE device_fingerprint IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_sessions_ip_user ON auth_system.sessions(ip_address, user_id);

-- MFA相关索引
CREATE INDEX CONCURRENTLY idx_mfa_devices_user_active ON auth_system.mfa_devices(user_id, status) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_mfa_devices_type_status ON auth_system.mfa_devices(device_type, status);
CREATE INDEX CONCURRENTLY idx_mfa_devices_primary ON auth_system.mfa_devices(user_id) WHERE is_primary = true;

CREATE INDEX CONCURRENTLY idx_mfa_backup_codes_user_unused ON auth_system.mfa_backup_codes(user_id) WHERE NOT is_used;
CREATE INDEX CONCURRENTLY idx_mfa_backup_codes_hash ON auth_system.mfa_backup_codes(code_hash);

CREATE INDEX CONCURRENTLY idx_mfa_verifications_user_recent ON auth_system.mfa_verifications(user_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_mfa_verifications_session ON auth_system.mfa_verifications(session_id) WHERE session_id IS NOT NULL;

-- OAuth相关索引
CREATE UNIQUE INDEX CONCURRENTLY idx_oauth_clients_client_id ON auth_system.oauth_clients(client_id) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_oauth_clients_status ON auth_system.oauth_clients(status) WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX CONCURRENTLY idx_oauth_auth_codes_code ON auth_system.oauth_authorization_codes(code);
CREATE INDEX CONCURRENTLY idx_oauth_auth_codes_client_user ON auth_system.oauth_authorization_codes(client_id, user_id);
CREATE INDEX CONCURRENTLY idx_oauth_auth_codes_expires ON auth_system.oauth_authorization_codes(expires_at) WHERE status = 'active';

CREATE UNIQUE INDEX CONCURRENTLY idx_oauth_access_tokens_hash ON auth_system.oauth_access_tokens(token_hash);
CREATE INDEX CONCURRENTLY idx_oauth_access_tokens_prefix ON auth_system.oauth_access_tokens(token_prefix);
CREATE INDEX CONCURRENTLY idx_oauth_access_tokens_client_user ON auth_system.oauth_access_tokens(client_id, user_id);
CREATE INDEX CONCURRENTLY idx_oauth_access_tokens_expires ON auth_system.oauth_access_tokens(expires_at) WHERE status = 'active';

CREATE UNIQUE INDEX CONCURRENTLY idx_oauth_refresh_tokens_hash ON auth_system.oauth_refresh_tokens(token_hash);
CREATE INDEX CONCURRENTLY idx_oauth_refresh_tokens_family ON auth_system.oauth_refresh_tokens(token_family_id);
CREATE INDEX CONCURRENTLY idx_oauth_refresh_tokens_user_client ON auth_system.oauth_refresh_tokens(user_id, client_id);

-- 黑名单表快速查询索引
CREATE INDEX CONCURRENTLY idx_ip_blacklist_ip ON auth_system.ip_blacklist(ip_address) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_ip_blacklist_range ON auth_system.ip_blacklist USING GIST(ip_range) WHERE status = 'active' AND ip_range IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_ip_blacklist_expires ON auth_system.ip_blacklist(expires_at) WHERE expires_at IS NOT NULL;

CREATE UNIQUE INDEX CONCURRENTLY idx_token_blacklist_token_id ON auth_system.token_blacklist(token_id);
CREATE INDEX CONCURRENTLY idx_token_blacklist_hash ON auth_system.token_blacklist(token_hash) WHERE token_hash IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_token_blacklist_user ON auth_system.token_blacklist(user_id) WHERE user_id IS NOT NULL;

CREATE UNIQUE INDEX CONCURRENTLY idx_device_blacklist_fingerprint ON auth_system.device_blacklist(device_fingerprint) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_device_blacklist_expires ON auth_system.device_blacklist(expires_at) WHERE expires_at IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_user_blacklist_user_active ON auth_system.user_blacklist(user_id, status) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_user_blacklist_expires ON auth_system.user_blacklist(expires_at) WHERE expires_at IS NOT NULL;

-- 复合索引用于常见查询模式
CREATE INDEX CONCURRENTLY idx_sessions_user_device_active ON auth_system.sessions(user_id, device_fingerprint, status)
    WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_oauth_tokens_client_scope ON auth_system.oauth_access_tokens(client_id, scope)
    WHERE status = 'active';

-- =====================================================
-- 9. 视图和存储过程
-- 设计原则：简化复杂查询、数据安全、性能优化
-- =====================================================

-- 用户完整信息视图 (包含角色和权限)
CREATE OR REPLACE VIEW auth_system.user_complete_profile AS
SELECT
    u.id,
    u.uuid,
    u.username,
    u.email,
    u.phone,
    u.status,
    u.email_verified,
    u.phone_verified,
    u.first_name,
    u.last_name,
    u.display_name,
    u.avatar_url,
    u.last_login_at,
    u.last_activity_at,
    u.created_at,
    u.timezone,
    u.locale,

    -- MFA状态
    EXISTS(SELECT 1 FROM auth_system.mfa_devices md WHERE md.user_id = u.id AND md.status = 'active') as mfa_enabled,

    -- 角色聚合
    COALESCE(
        JSON_AGG(
            JSON_BUILD_OBJECT(
                'role_id', r.id,
                'role_name', r.name,
                'display_name', r.display_name,
                'level', r.level,
                'assigned_at', ur.assigned_at,
                'expires_at', ur.expires_at
            ) ORDER BY r.level DESC
        ) FILTER (WHERE r.id IS NOT NULL),
        '[]'::json
    ) as roles,

    -- 最高权限级别
    COALESCE(MAX(r.level), 0) as max_permission_level,

    -- 活跃会话数
    (SELECT COUNT(*) FROM auth_system.sessions s
     WHERE s.user_id = u.id AND s.status = 'active' AND s.expires_at > CURRENT_TIMESTAMP) as active_sessions_count

FROM auth_system.users u
LEFT JOIN auth_system.user_roles ur ON u.id = ur.user_id AND ur.status = 'active'
    AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
LEFT JOIN auth_system.roles r ON ur.role_id = r.id AND r.status = 'active'
WHERE u.deleted_at IS NULL
GROUP BY u.id, u.uuid, u.username, u.email, u.phone, u.status, u.email_verified,
         u.phone_verified, u.first_name, u.last_name, u.display_name, u.avatar_url,
         u.last_login_at, u.last_activity_at, u.created_at, u.timezone, u.locale;

-- 活跃会话监控视图
CREATE OR REPLACE VIEW auth_system.active_sessions_monitor AS
SELECT
    s.session_id,
    s.user_id,
    u.username,
    u.email,
    s.ip_address,
    s.country_code,
    s.city,
    s.device_fingerprint,
    s.device_name,
    s.session_type,
    s.client_type,
    s.is_trusted_device,
    s.created_at,
    s.last_activity_at,
    s.expires_at,
    s.risk_score,
    s.security_flags,

    -- 会话持续时间
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - s.created_at))/3600 as session_hours,

    -- 空闲时间
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - s.last_activity_at))/60 as idle_minutes,

    -- 地理位置异常检测
    CASE
        WHEN s.country_code != u.country_code THEN true
        ELSE false
    END as location_anomaly

FROM auth_system.sessions s
JOIN auth_system.users u ON s.user_id = u.id
WHERE s.status = 'active'
  AND s.expires_at > CURRENT_TIMESTAMP
  AND u.deleted_at IS NULL;

-- OAuth客户端权限视图
CREATE OR REPLACE VIEW auth_system.oauth_client_permissions AS
SELECT
    oc.client_id,
    oc.name as client_name,
    oc.status,
    oc.client_type,
    oc.grant_types,
    oc.scope as default_scope,

    -- 用户授权统计
    COUNT(DISTINCT ouc.user_id) as authorized_users_count,

    -- 活跃令牌统计
    COUNT(DISTINCT oat.id) FILTER (WHERE oat.status = 'active' AND oat.expires_at > CURRENT_TIMESTAMP) as active_tokens_count,

    -- 最近使用时间
    MAX(oat.last_used_at) as last_token_used_at

FROM auth_system.oauth_clients oc
LEFT JOIN auth_system.oauth_user_consents ouc ON oc.client_id = ouc.client_id AND ouc.status = 'granted'
LEFT JOIN auth_system.oauth_access_tokens oat ON oc.client_id = oat.client_id
WHERE oc.deleted_at IS NULL
GROUP BY oc.client_id, oc.name, oc.status, oc.client_type, oc.grant_types, oc.scope;

-- 安全风险监控视图
CREATE OR REPLACE VIEW auth_system.security_risk_monitor AS
SELECT
    'failed_logins' as risk_type,
    COUNT(*) as event_count,
    COUNT(DISTINCT ip_address) as unique_ips,
    COUNT(DISTINCT user_id) as affected_users,
    'high' as severity
FROM auth_system.audit_logs
WHERE event_action = 'login'
  AND status = 'failure'
  AND created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
  AND error_code IN ('INVALID_PASSWORD', 'ACCOUNT_LOCKED')

UNION ALL

SELECT
    'suspicious_locations' as risk_type,
    COUNT(*) as event_count,
    COUNT(DISTINCT ip_address) as unique_ips,
    COUNT(DISTINCT user_id) as affected_users,
    'medium' as severity
FROM auth_system.audit_logs
WHERE event_action = 'login'
  AND status = 'success'
  AND 'unusual_location' = ANY(security_flags)
  AND created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'

UNION ALL

SELECT
    'multiple_device_logins' as risk_type,
    COUNT(*) as event_count,
    COUNT(DISTINCT ip_address) as unique_ips,
    COUNT(DISTINCT user_id) as affected_users,
    'medium' as severity
FROM auth_system.sessions s
WHERE s.status = 'active'
  AND s.created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
  AND (SELECT COUNT(DISTINCT device_fingerprint)
       FROM auth_system.sessions s2
       WHERE s2.user_id = s.user_id
         AND s2.status = 'active'
         AND s2.created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours') > 3;

-- =====================================================
-- 存储过程：用户认证
-- =====================================================
CREATE OR REPLACE FUNCTION auth_system.authenticate_user(
    p_login_identifier VARCHAR, -- 用户名、邮箱或手机号
    p_password VARCHAR,
    p_ip_address INET,
    p_user_agent TEXT DEFAULT NULL,
    p_device_fingerprint VARCHAR DEFAULT NULL
) RETURNS TABLE (
    success BOOLEAN,
    user_id BIGINT,
    username VARCHAR,
    email VARCHAR,
    status VARCHAR,
    requires_mfa BOOLEAN,
    mfa_methods TEXT[],
    session_token VARCHAR,
    error_code VARCHAR,
    error_message TEXT
) AS $$
DECLARE
    v_user_record RECORD;
    v_password_valid BOOLEAN := FALSE;
    v_session_id VARCHAR(128);
    v_max_attempts CONSTANT INTEGER := 5;
    v_lockout_duration CONSTANT INTERVAL := '30 minutes';
    v_mfa_methods TEXT[] := '{}';
BEGIN
    -- 查找用户
    SELECT u.id, u.username, u.email, u.password_hash, u.password_salt,
           u.status, u.failed_login_attempts, u.locked_until
    INTO v_user_record
    FROM auth_system.users u
    WHERE (u.username = p_login_identifier
           OR u.email = p_login_identifier
           OR u.phone = p_login_identifier)
      AND u.deleted_at IS NULL;

    -- 检查用户是否存在
    IF NOT FOUND THEN
        -- 记录失败尝试
        INSERT INTO auth_system.audit_logs (
            event_category, event_type, event_action, status, error_code,
            ip_address, user_agent, metadata
        ) VALUES (
            'authentication', 'login', 'attempt', 'failure', 'USER_NOT_FOUND',
            p_ip_address, p_user_agent,
            jsonb_build_object('login_identifier', p_login_identifier)
        );

        RETURN QUERY SELECT
            FALSE, NULL::BIGINT, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR,
            FALSE, '{}'::TEXT[], NULL::VARCHAR, 'USER_NOT_FOUND', 'User not found';
        RETURN;
    END IF;

    -- 检查IP黑名单
    IF EXISTS(SELECT 1 FROM auth_system.ip_blacklist
              WHERE status = 'active'
                AND (ip_address = p_ip_address OR p_ip_address << ip_range)
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)) THEN

        INSERT INTO auth_system.audit_logs (
            user_id, event_category, event_type, event_action, status, error_code,
            ip_address, user_agent
        ) VALUES (
            v_user_record.id, 'security', 'login', 'blocked', 'failure', 'IP_BLACKLISTED',
            p_ip_address, p_user_agent
        );

        RETURN QUERY SELECT
            FALSE, NULL::BIGINT, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR,
            FALSE, '{}'::TEXT[], NULL::VARCHAR, 'IP_BLACKLISTED', 'Access denied from this location';
        RETURN;
    END IF;

    -- 检查用户状态
    IF v_user_record.status != 'active' THEN
        INSERT INTO auth_system.audit_logs (
            user_id, event_category, event_type, event_action, status, error_code,
            ip_address, user_agent
        ) VALUES (
            v_user_record.id, 'authentication', 'login', 'attempt', 'failure', 'ACCOUNT_INACTIVE',
            p_ip_address, p_user_agent
        );

        RETURN QUERY SELECT
            FALSE, v_user_record.id, v_user_record.username, v_user_record.email, v_user_record.status,
            FALSE, '{}'::TEXT[], NULL::VARCHAR, 'ACCOUNT_INACTIVE', 'Account is not active';
        RETURN;
    END IF;

    -- 检查账户锁定
    IF v_user_record.locked_until IS NOT NULL AND v_user_record.locked_until > CURRENT_TIMESTAMP THEN
        INSERT INTO auth_system.audit_logs (
            user_id, event_category, event_type, event_action, status, error_code,
            ip_address, user_agent
        ) VALUES (
            v_user_record.id, 'authentication', 'login', 'attempt', 'failure', 'ACCOUNT_LOCKED',
            p_ip_address, p_user_agent
        );

        RETURN QUERY SELECT
            FALSE, v_user_record.id, v_user_record.username, v_user_record.email, v_user_record.status,
            FALSE, '{}'::TEXT[], NULL::VARCHAR, 'ACCOUNT_LOCKED',
            'Account is temporarily locked. Try again later.';
        RETURN;
    END IF;

    -- 验证密码 (在实际环境中应该使用bcrypt)
    IF v_user_record.password_hash = crypt(p_password, v_user_record.password_hash) THEN
        v_password_valid := TRUE;
    END IF;

    IF v_password_valid THEN
        -- 获取用户的MFA方法
        SELECT ARRAY_AGG(device_type::TEXT)
        INTO v_mfa_methods
        FROM auth_system.mfa_devices
        WHERE user_id = v_user_record.id AND status = 'active';

        v_mfa_methods := COALESCE(v_mfa_methods, '{}');

        -- 创建会话
        SELECT auth_system.create_user_session(
            v_user_record.id, p_ip_address, p_user_agent,
            p_device_fingerprint, 'web'
        ) INTO v_session_id;

        -- 重置失败计数并更新最后登录
        UPDATE auth_system.users
        SET failed_login_attempts = 0,
            locked_until = NULL,
            last_login_at = CURRENT_TIMESTAMP,
            last_login_ip = p_ip_address,
            last_activity_at = CURRENT_TIMESTAMP
        WHERE id = v_user_record.id;

        -- 记录成功登录
        INSERT INTO auth_system.audit_logs (
            user_id, session_id, event_category, event_type, event_action, status,
            ip_address, user_agent, metadata
        ) VALUES (
            v_user_record.id, v_session_id, 'authentication', 'login', 'success', 'success',
            p_ip_address, p_user_agent,
            jsonb_build_object('mfa_required', array_length(v_mfa_methods, 1) > 0)
        );

        RETURN QUERY SELECT
            TRUE, v_user_record.id, v_user_record.username, v_user_record.email, v_user_record.status,
            array_length(v_mfa_methods, 1) > 0, v_mfa_methods, v_session_id, NULL::VARCHAR, NULL::TEXT;
    ELSE
        -- 增加失败计数
        UPDATE auth_system.users
        SET failed_login_attempts = failed_login_attempts + 1,
            locked_until = CASE
                WHEN failed_login_attempts + 1 >= v_max_attempts
                THEN CURRENT_TIMESTAMP + v_lockout_duration
                ELSE locked_until
            END
        WHERE id = v_user_record.id;

        -- 记录失败登录
        INSERT INTO auth_system.audit_logs (
            user_id, event_category, event_type, event_action, status, error_code,
            ip_address, user_agent, metadata
        ) VALUES (
            v_user_record.id, 'authentication', 'login', 'attempt', 'failure', 'INVALID_CREDENTIALS',
            p_ip_address, p_user_agent,
            jsonb_build_object('failed_attempts', v_user_record.failed_login_attempts + 1)
        );

        RETURN QUERY SELECT
            FALSE, v_user_record.id, v_user_record.username, v_user_record.email, v_user_record.status,
            FALSE, '{}'::TEXT[], NULL::VARCHAR, 'INVALID_CREDENTIALS', 'Invalid username or password';
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 存储过程：创建用户会话
-- =====================================================
CREATE OR REPLACE FUNCTION auth_system.create_user_session(
    p_user_id BIGINT,
    p_ip_address INET,
    p_user_agent TEXT,
    p_device_fingerprint VARCHAR DEFAULT NULL,
    p_session_type VARCHAR DEFAULT 'web',
    p_expires_hours INTEGER DEFAULT 24
) RETURNS VARCHAR AS $$
DECLARE
    v_session_id VARCHAR(128);
    v_expires_at TIMESTAMPTZ;
    v_device_trusted BOOLEAN := FALSE;
    v_requires_mfa BOOLEAN := FALSE;
    v_geo_info RECORD;
BEGIN
    -- 生成会话ID
    v_session_id := encode(gen_random_bytes(64), 'hex');
    v_expires_at := CURRENT_TIMESTAMP + (p_expires_hours || ' hours')::INTERVAL;

    -- 检查设备是否可信
    IF p_device_fingerprint IS NOT NULL THEN
        SELECT COUNT(*) > 0 INTO v_device_trusted
        FROM auth_system.sessions
        WHERE user_id = p_user_id
          AND device_fingerprint = p_device_fingerprint
          AND is_trusted_device = TRUE
          AND created_at > CURRENT_TIMESTAMP - INTERVAL '30 days';
    END IF;

    -- 检查是否需要MFA (基于风险评估)
    v_requires_mfa := NOT v_device_trusted OR
                     EXISTS(SELECT 1 FROM auth_system.mfa_devices
                            WHERE user_id = p_user_id AND status = 'active');

    -- 模拟地理位置信息获取 (在实际应用中会调用地理位置服务)
    SELECT 'US' as country, 'California' as region, 'San Francisco' as city, 'America/Los_Angeles' as tz
    INTO v_geo_info;

    -- 插入会话记录
    INSERT INTO auth_system.sessions (
        session_id, user_id, session_type, client_type,
        device_fingerprint, user_agent, ip_address,
        country_code, region, city, timezone,
        is_trusted_device, requires_mfa, expires_at
    ) VALUES (
        v_session_id, p_user_id, p_session_type::session_type, 'browser'::client_type,
        p_device_fingerprint, p_user_agent, p_ip_address,
        v_geo_info.country, v_geo_info.region, v_geo_info.city, v_geo_info.tz,
        v_device_trusted, v_requires_mfa, v_expires_at
    );

    -- 清理该用户的过期会话
    DELETE FROM auth_system.sessions
    WHERE user_id = p_user_id
      AND (expires_at < CURRENT_TIMESTAMP
           OR last_activity_at < CURRENT_TIMESTAMP - INTERVAL '7 days');

    RETURN v_session_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 定期维护任务
-- =====================================================

-- 清理过期会话
CREATE OR REPLACE FUNCTION auth_system.cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    -- 删除过期的会话
    DELETE FROM auth_system.sessions
    WHERE status = 'active'
      AND (expires_at < CURRENT_TIMESTAMP
           OR last_activity_at < CURRENT_TIMESTAMP - INTERVAL '30 days');

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

    -- 记录清理操作
    INSERT INTO auth_system.audit_logs (
        event_category, event_type, event_action, status,
        metadata
    ) VALUES (
        'system', 'maintenance', 'session_cleanup', 'success',
        jsonb_build_object('deleted_sessions', v_deleted_count)
    );

    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 清理过期令牌
CREATE OR REPLACE FUNCTION auth_system.cleanup_expired_tokens()
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    -- 清理过期的OAuth访问令牌
    DELETE FROM auth_system.oauth_access_tokens
    WHERE status = 'active' AND expires_at < CURRENT_TIMESTAMP;

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

    -- 清理过期的刷新令牌
    DELETE FROM auth_system.oauth_refresh_tokens
    WHERE status = 'active' AND expires_at < CURRENT_TIMESTAMP;

    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 清理过期黑名单条目
CREATE OR REPLACE FUNCTION auth_system.cleanup_expired_blacklist()
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    -- 更新过期的黑名单条目状态
    UPDATE auth_system.ip_blacklist
    SET status = 'expired'
    WHERE status = 'active'
      AND expires_at IS NOT NULL
      AND expires_at < CURRENT_TIMESTAMP;

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

    -- 类似地处理其他黑名单表
    UPDATE auth_system.device_blacklist
    SET status = 'expired'
    WHERE status = 'active'
      AND expires_at IS NOT NULL
      AND expires_at < CURRENT_TIMESTAMP;

    UPDATE auth_system.user_blacklist
    SET status = 'expired'
    WHERE status = 'active'
      AND expires_at IS NOT NULL
      AND expires_at < CURRENT_TIMESTAMP;

    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 触发器设置
-- =====================================================

-- 自动更新 updated_at 字段的通用函数
CREATE OR REPLACE FUNCTION auth_system.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为所有相关表添加更新时间触发器
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON auth_system.users
    FOR EACH ROW EXECUTE FUNCTION auth_system.update_updated_at_column();

CREATE TRIGGER trg_roles_updated_at
    BEFORE UPDATE ON auth_system.roles
    FOR EACH ROW EXECUTE FUNCTION auth_system.update_updated_at_column();

CREATE TRIGGER trg_permissions_updated_at
    BEFORE UPDATE ON auth_system.permissions
    FOR EACH ROW EXECUTE FUNCTION auth_system.update_updated_at_column();

CREATE TRIGGER trg_oauth_clients_updated_at
    BEFORE UPDATE ON auth_system.oauth_clients
    FOR EACH ROW EXECUTE FUNCTION auth_system.update_updated_at_column();

CREATE TRIGGER trg_mfa_devices_updated_at
    BEFORE UPDATE ON auth_system.mfa_devices
    FOR EACH ROW EXECUTE FUNCTION auth_system.update_updated_at_column();

-- =====================================================
-- 初始化数据
-- =====================================================

-- 插入系统角色
INSERT INTO auth_system.roles (name, display_name, description, level, role_type, is_system_role, permissions) VALUES
('system_admin', 'System Administrator', 'Full system access with all privileges', 1000, 'system', TRUE,
 '{"system": {"admin": true}, "users": {"read": true, "write": true, "delete": true}, "roles": {"read": true, "write": true, "delete": true}}'::jsonb),
('organization_admin', 'Organization Administrator', 'Organization-level administrative access', 800, 'organization', TRUE,
 '{"organization": {"admin": true}, "users": {"read": true, "write": true}, "roles": {"read": true, "write": true}}'::jsonb),
('user_manager', 'User Manager', 'User management and support', 600, 'custom', TRUE,
 '{"users": {"read": true, "write": true}, "sessions": {"read": true, "manage": true}}'::jsonb),
('regular_user', 'Regular User', 'Standard user access', 100, 'custom', TRUE,
 '{"profile": {"read": true, "write": true}, "sessions": {"read": true}}'::jsonb),
('guest', 'Guest User', 'Limited guest access', 10, 'custom', TRUE,
 '{"public": {"read": true}}'::jsonb);

-- 插入基础权限
INSERT INTO auth_system.permissions (name, display_name, description, category, resource_type, actions, permission_level) VALUES
('system.admin', 'System Administration', 'Full system administrative access', 'system', 'system', '{admin}', 1000),
('users.read', 'Read Users', 'View user information and profiles', 'users', 'user', '{read}', 100),
('users.write', 'Write Users', 'Create and modify user accounts', 'users', 'user', '{write}', 200),
('users.delete', 'Delete Users', 'Delete user accounts', 'users', 'user', '{delete}', 300),
('roles.read', 'Read Roles', 'View role information', 'roles', 'role', '{read}', 100),
('roles.write', 'Write Roles', 'Create and modify roles', 'roles', 'role', '{write}', 200),
('roles.delete', 'Delete Roles', 'Delete roles', 'roles', 'role', '{delete}', 300),
('sessions.read', 'Read Sessions', 'View session information', 'sessions', 'session', '{read}', 100),
('sessions.manage', 'Manage Sessions', 'Create and revoke sessions', 'sessions', 'session', '{write,delete}', 200),
('audit.read', 'Read Audit Logs', 'View audit logs and security events', 'audit', 'audit_log', '{read}', 150),
('mfa.manage', 'Manage MFA', 'Configure multi-factor authentication', 'security', 'mfa', '{read,write,delete}', 200),
('oauth.manage', 'Manage OAuth', 'Manage OAuth clients and tokens', 'oauth', 'oauth', '{read,write,delete}', 250);

-- 创建默认超级管理员用户 (需要在应用层设置密码)
INSERT INTO auth_system.users (
    username, email, password_hash, password_salt, status, email_verified,
    first_name, last_name, display_name
) VALUES (
    'admin', 'admin@system.local',
    crypt('admin123', gen_salt('bf', 12)), -- 临时密码，应在首次登录时更改
    encode(gen_random_bytes(32), 'hex'),
    'active', TRUE,
    'System', 'Administrator', 'System Administrator'
);

-- 分配超级管理员角色
INSERT INTO auth_system.user_roles (user_id, role_id, assigned_by, assignment_reason)
SELECT u.id, r.id, u.id, 'Initial system setup'
FROM auth_system.users u, auth_system.roles r
WHERE u.username = 'admin' AND r.name = 'system_admin';

-- =====================================================
-- 性能监控和维护
-- =====================================================

-- 创建性能监控视图
CREATE OR REPLACE VIEW auth_system.table_performance_stats AS
SELECT
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    seq_scan as sequential_scans,
    seq_tup_read as sequential_reads,
    idx_scan as index_scans,
    idx_tup_fetch as index_reads,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'auth_system'
ORDER BY tablename;

-- 索引使用情况监控
CREATE OR REPLACE VIEW auth_system.index_usage_stats AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'auth_system'
ORDER BY idx_scan DESC;

-- =====================================================
-- 完成标记
-- =====================================================

COMMENT ON SCHEMA auth_system IS '企业级认证系统 - 完整数据库架构 v1.0';

-- 提交事务
COMMIT;

-- 输出完成信息
SELECT 'Auth System Database Schema Created Successfully!' as status,
       COUNT(*) as total_tables
FROM information_schema.tables
WHERE table_schema = 'auth_system';