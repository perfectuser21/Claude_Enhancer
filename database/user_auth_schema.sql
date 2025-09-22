-- =====================================================
-- 用户认证系统数据库Schema设计
-- 设计理念：安全第一、性能优化、可扩展性
-- =====================================================

-- 创建专用schema
CREATE SCHEMA IF NOT EXISTS auth;
SET search_path = auth, public;

-- =====================================================
-- 1. users表 - 用户基本信息
-- =====================================================
CREATE TABLE auth.users (
    -- 主键和基本信息
    id BIGSERIAL PRIMARY KEY,
    uuid UUID NOT NULL DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,

    -- 安全字段
    password_hash VARCHAR(255) NOT NULL, -- bcrypt hash
    salt VARCHAR(32) NOT NULL DEFAULT encode(gen_random_bytes(16), 'hex'),

    -- 用户状态
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'suspended', 'pending_verification')),
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    email_verification_expires TIMESTAMPTZ,

    -- 密码安全
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,

    -- 用户详细信息
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    locale VARCHAR(10) DEFAULT 'en_US',

    -- MFA (多因子认证)
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret VARCHAR(32), -- TOTP secret
    backup_codes TEXT[], -- 备用恢复码

    -- 审计字段
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES auth.users(id),
    updated_by BIGINT REFERENCES auth.users(id),

    -- 软删除
    deleted_at TIMESTAMPTZ,
    deleted_by BIGINT REFERENCES auth.users(id),

    -- 额外元数据
    metadata JSONB DEFAULT '{}',

    -- 约束
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_username_format CHECK (username ~* '^[a-zA-Z0-9_-]{3,50}$'),
    CONSTRAINT users_password_reset_valid CHECK (
        (password_reset_token IS NULL AND password_reset_expires IS NULL) OR
        (password_reset_token IS NOT NULL AND password_reset_expires IS NOT NULL)
    ),
    CONSTRAINT users_email_verification_valid CHECK (
        (email_verification_token IS NULL AND email_verification_expires IS NULL) OR
        (email_verification_token IS NOT NULL AND email_verification_expires IS NOT NULL)
    )
);

-- 用户表触发器 - 自动更新updated_at
CREATE OR REPLACE FUNCTION auth.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION auth.update_updated_at_column();

-- =====================================================
-- 2. roles表 - 角色权限管理
-- =====================================================
CREATE TABLE auth.roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,

    -- 权限级别
    level INTEGER NOT NULL DEFAULT 0, -- 用于层级权限

    -- 系统角色标识
    is_system_role BOOLEAN NOT NULL DEFAULT FALSE,
    is_default_role BOOLEAN NOT NULL DEFAULT FALSE,

    -- 权限集合 (使用JSONB存储灵活的权限结构)
    permissions JSONB NOT NULL DEFAULT '{}',

    -- 角色状态
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive')),

    -- 审计字段
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES auth.users(id),
    updated_by BIGINT REFERENCES auth.users(id),

    -- 约束
    CONSTRAINT roles_name_format CHECK (name ~* '^[a-zA-Z0-9_-]{2,50}$')
);

-- 角色表触发器
CREATE TRIGGER update_roles_updated_at
    BEFORE UPDATE ON auth.roles
    FOR EACH ROW EXECUTE FUNCTION auth.update_updated_at_column();

-- 用户角色关联表 (多对多关系)
CREATE TABLE auth.user_roles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,

    -- 角色分配详情
    assigned_by BIGINT REFERENCES auth.users(id),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ, -- 角色过期时间

    -- 状态
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'expired')),

    -- 审计
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 唯一约束
    UNIQUE(user_id, role_id)
);

-- =====================================================
-- 3. sessions表 - 会话管理
-- =====================================================
CREATE TABLE auth.sessions (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(128) NOT NULL UNIQUE, -- UUID或安全随机字符串
    user_id BIGINT NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- 会话信息
    user_agent TEXT,
    ip_address INET,
    device_fingerprint VARCHAR(64),

    -- 地理位置信息
    country_code VARCHAR(2),
    city VARCHAR(100),

    -- 会话状态
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'expired', 'revoked', 'invalid')),

    -- 时间管理
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,

    -- 会话类型
    session_type VARCHAR(20) NOT NULL DEFAULT 'web'
        CHECK (session_type IN ('web', 'mobile', 'api', 'desktop')),

    -- 安全标记
    is_trusted_device BOOLEAN NOT NULL DEFAULT FALSE,
    requires_mfa BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_verified BOOLEAN NOT NULL DEFAULT FALSE,

    -- 会话元数据
    metadata JSONB DEFAULT '{}',

    -- 约束
    CONSTRAINT sessions_expires_after_created CHECK (expires_at > created_at),
    CONSTRAINT sessions_last_activity_valid CHECK (last_activity_at >= created_at)
);

-- 会话清理函数
CREATE OR REPLACE FUNCTION auth.cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM auth.sessions
    WHERE expires_at < CURRENT_TIMESTAMP
       OR (last_activity_at < CURRENT_TIMESTAMP - INTERVAL '30 days');

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 4. audit_logs表 - 审计日志
-- =====================================================
CREATE TABLE auth.audit_logs (
    id BIGSERIAL PRIMARY KEY,

    -- 操作主体
    user_id BIGINT REFERENCES auth.users(id),
    session_id VARCHAR(128) REFERENCES auth.sessions(session_id),

    -- 操作详情
    action VARCHAR(50) NOT NULL, -- login, logout, password_change, etc.
    resource_type VARCHAR(50), -- user, role, session, etc.
    resource_id VARCHAR(100), -- 资源ID

    -- 操作结果
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failure', 'partial')),
    error_code VARCHAR(50),
    error_message TEXT,

    -- 请求信息
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100), -- 追踪请求

    -- 变更详情
    old_values JSONB, -- 变更前的值
    new_values JSONB, -- 变更后的值

    -- 时间戳
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 额外上下文
    metadata JSONB DEFAULT '{}',

    -- 安全等级
    severity_level VARCHAR(20) NOT NULL DEFAULT 'info'
        CHECK (severity_level IN ('critical', 'high', 'medium', 'low', 'info'))
);

-- 审计日志分区 (按月分区以提高性能)
CREATE TABLE auth.audit_logs_template (LIKE auth.audit_logs INCLUDING ALL);

-- =====================================================
-- 5. 权限资源表 - 细粒度权限控制
-- =====================================================
CREATE TABLE auth.permissions (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,

    -- 权限分类
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),

    -- 权限级别
    level INTEGER NOT NULL DEFAULT 0,

    -- 资源限制
    resource_pattern VARCHAR(200), -- 可以访问的资源模式

    -- 状态
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'deprecated')),

    -- 审计
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT permissions_name_format CHECK (name ~* '^[a-zA-Z0-9_.-]+$')
);

-- 权限表触发器
CREATE TRIGGER update_permissions_updated_at
    BEFORE UPDATE ON auth.permissions
    FOR EACH ROW EXECUTE FUNCTION auth.update_updated_at_column();

-- 角色权限关联表
CREATE TABLE auth.role_permissions (
    id BIGSERIAL PRIMARY KEY,
    role_id BIGINT NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
    permission_id BIGINT NOT NULL REFERENCES auth.permissions(id) ON DELETE CASCADE,

    -- 权限约束 (如数据范围限制)
    constraints JSONB DEFAULT '{}',

    -- 审计
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    granted_by BIGINT REFERENCES auth.users(id),

    -- 唯一约束
    UNIQUE(role_id, permission_id)
);

-- =====================================================
-- 索引优化策略
-- =====================================================

-- users表索引
CREATE UNIQUE INDEX CONCURRENTLY idx_users_uuid ON auth.users(uuid);
CREATE UNIQUE INDEX CONCURRENTLY idx_users_email_active ON auth.users(email) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX CONCURRENTLY idx_users_username_active ON auth.users(username) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_users_status ON auth.users(status) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_users_created_at ON auth.users(created_at);
CREATE INDEX CONCURRENTLY idx_users_email_verification ON auth.users(email_verification_token) WHERE email_verification_token IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_users_password_reset ON auth.users(password_reset_token) WHERE password_reset_token IS NOT NULL;

-- sessions表索引
CREATE UNIQUE INDEX CONCURRENTLY idx_sessions_session_id ON auth.sessions(session_id);
CREATE INDEX CONCURRENTLY idx_sessions_user_id ON auth.sessions(user_id);
CREATE INDEX CONCURRENTLY idx_sessions_expires_at ON auth.sessions(expires_at);
CREATE INDEX CONCURRENTLY idx_sessions_last_activity ON auth.sessions(last_activity_at);
CREATE INDEX CONCURRENTLY idx_sessions_status_active ON auth.sessions(status, user_id) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_sessions_cleanup ON auth.sessions(expires_at, last_activity_at) WHERE status = 'active';

-- roles表索引
CREATE UNIQUE INDEX CONCURRENTLY idx_roles_name ON auth.roles(name);
CREATE INDEX CONCURRENTLY idx_roles_status ON auth.roles(status);
CREATE INDEX CONCURRENTLY idx_roles_level ON auth.roles(level);

-- user_roles表索引
CREATE INDEX CONCURRENTLY idx_user_roles_user_id ON auth.user_roles(user_id);
CREATE INDEX CONCURRENTLY idx_user_roles_role_id ON auth.user_roles(role_id);
CREATE INDEX CONCURRENTLY idx_user_roles_status ON auth.user_roles(status);
CREATE INDEX CONCURRENTLY idx_user_roles_expires ON auth.user_roles(expires_at) WHERE expires_at IS NOT NULL;

-- audit_logs表索引 (考虑到大数据量)
CREATE INDEX CONCURRENTLY idx_audit_logs_user_id ON auth.audit_logs(user_id);
CREATE INDEX CONCURRENTLY idx_audit_logs_action ON auth.audit_logs(action);
CREATE INDEX CONCURRENTLY idx_audit_logs_created_at ON auth.audit_logs(created_at);
CREATE INDEX CONCURRENTLY idx_audit_logs_status ON auth.audit_logs(status);
CREATE INDEX CONCURRENTLY idx_audit_logs_resource ON auth.audit_logs(resource_type, resource_id);
CREATE INDEX CONCURRENTLY idx_audit_logs_ip_address ON auth.audit_logs(ip_address);
CREATE INDEX CONCURRENTLY idx_audit_logs_request_id ON auth.audit_logs(request_id);

-- permissions表索引
CREATE UNIQUE INDEX CONCURRENTLY idx_permissions_name ON auth.permissions(name);
CREATE INDEX CONCURRENTLY idx_permissions_category ON auth.permissions(category, subcategory);
CREATE INDEX CONCURRENTLY idx_permissions_status ON auth.permissions(status);

-- role_permissions表索引
CREATE INDEX CONCURRENTLY idx_role_permissions_role_id ON auth.role_permissions(role_id);
CREATE INDEX CONCURRENTLY idx_role_permissions_permission_id ON auth.role_permissions(permission_id);

-- =====================================================
-- 视图定义 - 简化常用查询
-- =====================================================

-- 用户详细信息视图 (包含角色)
CREATE OR REPLACE VIEW auth.user_details AS
SELECT
    u.id,
    u.uuid,
    u.username,
    u.email,
    u.status,
    u.email_verified,
    u.first_name,
    u.last_name,
    u.avatar_url,
    u.mfa_enabled,
    u.created_at,
    u.updated_at,
    u.last_login_at,
    COALESCE(
        JSON_AGG(
            JSON_BUILD_OBJECT(
                'role_id', r.id,
                'role_name', r.name,
                'display_name', r.display_name,
                'level', r.level
            )
        ) FILTER (WHERE r.id IS NOT NULL),
        '[]'::json
    ) AS roles
FROM auth.users u
LEFT JOIN auth.user_roles ur ON u.id = ur.user_id AND ur.status = 'active'
LEFT JOIN auth.roles r ON ur.role_id = r.id AND r.status = 'active'
WHERE u.deleted_at IS NULL
GROUP BY u.id, u.uuid, u.username, u.email, u.status, u.email_verified,
         u.first_name, u.last_name, u.avatar_url, u.mfa_enabled,
         u.created_at, u.updated_at, u.last_login_at;

-- 活跃会话视图
CREATE OR REPLACE VIEW auth.active_sessions AS
SELECT
    s.session_id,
    s.user_id,
    u.username,
    u.email,
    s.ip_address,
    s.user_agent,
    s.device_fingerprint,
    s.created_at,
    s.last_activity_at,
    s.expires_at,
    s.session_type,
    s.is_trusted_device
FROM auth.sessions s
JOIN auth.users u ON s.user_id = u.id
WHERE s.status = 'active'
  AND s.expires_at > CURRENT_TIMESTAMP
  AND u.deleted_at IS NULL;

-- =====================================================
-- 存储过程和函数
-- =====================================================

-- 用户登录验证函数
CREATE OR REPLACE FUNCTION auth.authenticate_user(
    p_username_or_email VARCHAR,
    p_password VARCHAR,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
) RETURNS TABLE (
    user_id BIGINT,
    username VARCHAR,
    email VARCHAR,
    status VARCHAR,
    mfa_enabled BOOLEAN,
    requires_mfa BOOLEAN
) AS $$
DECLARE
    v_user_record RECORD;
    v_password_valid BOOLEAN := FALSE;
BEGIN
    -- 查找用户
    SELECT u.id, u.username, u.email, u.password_hash, u.salt, u.status,
           u.mfa_enabled, u.failed_login_attempts, u.locked_until
    INTO v_user_record
    FROM auth.users u
    WHERE (u.username = p_username_or_email OR u.email = p_username_or_email)
      AND u.deleted_at IS NULL;

    -- 检查用户是否存在
    IF NOT FOUND THEN
        -- 记录失败尝试
        INSERT INTO auth.audit_logs (action, status, ip_address, user_agent, error_code)
        VALUES ('login', 'failure', p_ip_address, p_user_agent, 'USER_NOT_FOUND');
        RETURN;
    END IF;

    -- 检查账户锁定状态
    IF v_user_record.locked_until IS NOT NULL AND v_user_record.locked_until > CURRENT_TIMESTAMP THEN
        INSERT INTO auth.audit_logs (user_id, action, status, ip_address, user_agent, error_code)
        VALUES (v_user_record.id, 'login', 'failure', p_ip_address, p_user_agent, 'ACCOUNT_LOCKED');
        RETURN;
    END IF;

    -- 验证密码 (在实际应用中，这应该在应用层使用bcrypt进行)
    -- 这里只是示例逻辑
    IF v_user_record.password_hash = crypt(p_password, v_user_record.password_hash) THEN
        v_password_valid := TRUE;
    END IF;

    IF v_password_valid THEN
        -- 密码正确，重置失败计数
        UPDATE auth.users
        SET failed_login_attempts = 0,
            locked_until = NULL,
            last_login_at = CURRENT_TIMESTAMP
        WHERE id = v_user_record.id;

        -- 记录成功登录
        INSERT INTO auth.audit_logs (user_id, action, status, ip_address, user_agent)
        VALUES (v_user_record.id, 'login', 'success', p_ip_address, p_user_agent);

        -- 返回用户信息
        RETURN QUERY SELECT
            v_user_record.id,
            v_user_record.username,
            v_user_record.email,
            v_user_record.status,
            v_user_record.mfa_enabled,
            v_user_record.mfa_enabled; -- 如果启用MFA则需要验证
    ELSE
        -- 密码错误，增加失败计数
        UPDATE auth.users
        SET failed_login_attempts = failed_login_attempts + 1,
            locked_until = CASE
                WHEN failed_login_attempts >= 4 THEN CURRENT_TIMESTAMP + INTERVAL '30 minutes'
                ELSE locked_until
            END
        WHERE id = v_user_record.id;

        -- 记录失败登录
        INSERT INTO auth.audit_logs (user_id, action, status, ip_address, user_agent, error_code)
        VALUES (v_user_record.id, 'login', 'failure', p_ip_address, p_user_agent, 'INVALID_PASSWORD');
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 创建会话函数
CREATE OR REPLACE FUNCTION auth.create_session(
    p_user_id BIGINT,
    p_ip_address INET,
    p_user_agent TEXT,
    p_session_type VARCHAR DEFAULT 'web',
    p_expires_hours INTEGER DEFAULT 24
) RETURNS VARCHAR AS $$
DECLARE
    v_session_id VARCHAR(128);
    v_expires_at TIMESTAMPTZ;
BEGIN
    -- 生成会话ID
    v_session_id := encode(gen_random_bytes(64), 'hex');
    v_expires_at := CURRENT_TIMESTAMP + (p_expires_hours || ' hours')::INTERVAL;

    -- 插入会话记录
    INSERT INTO auth.sessions (
        session_id, user_id, ip_address, user_agent,
        session_type, expires_at
    ) VALUES (
        v_session_id, p_user_id, p_ip_address, p_user_agent,
        p_session_type, v_expires_at
    );

    -- 记录会话创建
    INSERT INTO auth.audit_logs (user_id, action, status, ip_address, user_agent)
    VALUES (p_user_id, 'session_create', 'success', p_ip_address, p_user_agent);

    RETURN v_session_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 初始数据插入
-- =====================================================

-- 插入默认角色
INSERT INTO auth.roles (name, display_name, description, level, is_system_role, is_default_role, permissions) VALUES
('super_admin', 'Super Administrator', 'Full system access', 100, TRUE, FALSE,
 '{"all": true}'::jsonb),
('admin', 'Administrator', 'Administrative access', 80, TRUE, FALSE,
 '{"users": {"read": true, "write": true}, "roles": {"read": true, "write": true}}'::jsonb),
('user', 'Regular User', 'Standard user access', 10, TRUE, TRUE,
 '{"profile": {"read": true, "write": true}}'::jsonb),
('guest', 'Guest User', 'Limited access', 0, TRUE, FALSE,
 '{"public": {"read": true}}'::jsonb);

-- 插入基础权限
INSERT INTO auth.permissions (name, display_name, description, category) VALUES
('users.read', 'Read Users', 'View user information', 'users'),
('users.write', 'Write Users', 'Create and modify users', 'users'),
('users.delete', 'Delete Users', 'Delete user accounts', 'users'),
('roles.read', 'Read Roles', 'View role information', 'roles'),
('roles.write', 'Write Roles', 'Create and modify roles', 'roles'),
('roles.delete', 'Delete Roles', 'Delete roles', 'roles'),
('sessions.read', 'Read Sessions', 'View session information', 'sessions'),
('sessions.manage', 'Manage Sessions', 'Create and revoke sessions', 'sessions'),
('audit.read', 'Read Audit Logs', 'View audit logs', 'audit'),
('system.admin', 'System Administration', 'Full system administration', 'system');

-- =====================================================
-- 安全策略
-- =====================================================

-- 启用行级安全
ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth.audit_logs ENABLE ROW LEVEL SECURITY;

-- 用户只能访问自己的信息 (示例策略)
CREATE POLICY users_own_data ON auth.users
    FOR ALL TO authenticated_user
    USING (id = current_user_id());

-- 会话访问策略
CREATE POLICY sessions_own_data ON auth.sessions
    FOR ALL TO authenticated_user
    USING (user_id = current_user_id());

-- =====================================================
-- 维护和监控
-- =====================================================

-- 定期清理过期会话 (可设置为定时任务)
-- SELECT auth.cleanup_expired_sessions();

-- 监控查询性能
COMMENT ON TABLE auth.users IS '用户基本信息表 - 核心用户数据存储';
COMMENT ON TABLE auth.sessions IS '会话管理表 - 用户登录会话跟踪';
COMMENT ON TABLE auth.roles IS '角色管理表 - 基于角色的访问控制';
COMMENT ON TABLE auth.audit_logs IS '审计日志表 - 安全审计和操作追踪';
COMMENT ON TABLE auth.permissions IS '权限管理表 - 细粒度权限控制';

-- 性能监控视图
CREATE OR REPLACE VIEW auth.performance_stats AS
SELECT
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'auth';

-- 结束
-- =====================================================