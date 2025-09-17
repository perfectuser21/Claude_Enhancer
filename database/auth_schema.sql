-- Perfect21 用户认证系统数据库架构
-- 版本: 1.0.0
-- 创建时间: 2025-09-17
-- 设计原则: 安全性、性能、可扩展性

-- ============================================================================
-- 1. 创建专用模式
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS auth;
SET search_path TO auth, public;

-- ============================================================================
-- 2. 启用必要的扩展
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- 3. 用户主表 (users)
-- ============================================================================

CREATE TABLE auth.users (
    -- 主键使用UUID，提供更好的安全性和分布式支持
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 邮箱，唯一索引，用于登录
    email VARCHAR(255) NOT NULL,

    -- 用户名，可选，唯一
    username VARCHAR(50),

    -- 密码哈希，使用bcrypt或argon2
    password_hash VARCHAR(255) NOT NULL,

    -- 用户状态
    is_active BOOLEAN DEFAULT true NOT NULL,
    is_verified BOOLEAN DEFAULT false NOT NULL,

    -- 安全字段
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMPTZ,
    email_verification_token VARCHAR(255),
    email_verification_expires TIMESTAMPTZ,

    -- 失败登录计数和锁定
    failed_login_count INTEGER DEFAULT 0 NOT NULL,
    locked_until TIMESTAMPTZ,

    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_login_at TIMESTAMPTZ,

    -- 约束
    CONSTRAINT users_email_valid CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_username_valid CHECK (username IS NULL OR (username ~ '^[a-zA-Z0-9_-]{3,50}$')),
    CONSTRAINT users_failed_login_count_valid CHECK (failed_login_count >= 0),
    CONSTRAINT users_password_reset_token_expires CHECK (
        (password_reset_token IS NULL AND password_reset_expires IS NULL) OR
        (password_reset_token IS NOT NULL AND password_reset_expires IS NOT NULL)
    )
);

-- 创建唯一索引
CREATE UNIQUE INDEX idx_users_email_unique ON auth.users(LOWER(email)) WHERE is_active = true;
CREATE UNIQUE INDEX idx_users_username_unique ON auth.users(LOWER(username)) WHERE username IS NOT NULL AND is_active = true;

-- ============================================================================
-- 4. 用户会话表 (sessions)
-- ============================================================================

CREATE TABLE auth.sessions (
    -- 主键
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 外键关联用户
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- 刷新令牌，用于无感知续期
    refresh_token VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255) NOT NULL, -- 存储哈希值

    -- 会话信息
    expires_at TIMESTAMPTZ NOT NULL,

    -- 客户端信息
    ip_address INET,
    user_agent TEXT,
    device_fingerprint VARCHAR(255),

    -- 会话状态
    is_active BOOLEAN DEFAULT true NOT NULL,
    revoked_at TIMESTAMPTZ,
    revoked_reason VARCHAR(100),

    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_used_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- 约束
    CONSTRAINT sessions_expires_future CHECK (expires_at > created_at),
    CONSTRAINT sessions_revoked_logic CHECK (
        (is_active = true AND revoked_at IS NULL) OR
        (is_active = false AND revoked_at IS NOT NULL)
    )
);

-- 创建索引
CREATE INDEX idx_sessions_user_id ON auth.sessions(user_id);
CREATE INDEX idx_sessions_refresh_token_hash ON auth.sessions(refresh_token_hash) WHERE is_active = true;
CREATE INDEX idx_sessions_expires_at ON auth.sessions(expires_at) WHERE is_active = true;
CREATE INDEX idx_sessions_last_used_at ON auth.sessions(last_used_at);

-- ============================================================================
-- 5. 登录尝试记录表 (login_attempts)
-- ============================================================================

CREATE TABLE auth.login_attempts (
    -- 主键
    id BIGSERIAL PRIMARY KEY,

    -- 用户ID（可能为空，针对不存在的邮箱）
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    -- 尝试登录的邮箱
    email VARCHAR(255) NOT NULL,

    -- 客户端信息
    ip_address INET NOT NULL,
    user_agent TEXT,

    -- 尝试结果
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(100), -- 'invalid_credentials', 'account_locked', 'account_inactive', etc.

    -- 时间戳
    attempt_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- 约束
    CONSTRAINT login_attempts_success_logic CHECK (
        (success = true AND failure_reason IS NULL) OR
        (success = false AND failure_reason IS NOT NULL)
    )
);

-- 创建索引
CREATE INDEX idx_login_attempts_user_id ON auth.login_attempts(user_id);
CREATE INDEX idx_login_attempts_email ON auth.login_attempts(LOWER(email));
CREATE INDEX idx_login_attempts_ip_address ON auth.login_attempts(ip_address);
CREATE INDEX idx_login_attempts_attempt_time ON auth.login_attempts(attempt_time);

-- 复合索引用于安全检查
CREATE INDEX idx_login_attempts_ip_time ON auth.login_attempts(ip_address, attempt_time) WHERE success = false;
CREATE INDEX idx_login_attempts_email_time ON auth.login_attempts(LOWER(email), attempt_time) WHERE success = false;

-- ============================================================================
-- 6. 用户角色和权限表（可选扩展）
-- ============================================================================

CREATE TABLE auth.roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE auth.permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT permissions_unique_resource_action UNIQUE(resource, action)
);

CREATE TABLE auth.role_permissions (
    role_id INTEGER NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES auth.permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,

    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE auth.user_roles (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    granted_by UUID REFERENCES auth.users(id),

    PRIMARY KEY (user_id, role_id)
);

-- ============================================================================
-- 7. 审计日志表
-- ============================================================================

CREATE TABLE auth.audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 创建索引
CREATE INDEX idx_audit_logs_user_id ON auth.audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON auth.audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON auth.audit_logs(created_at);
CREATE INDEX idx_audit_logs_resource ON auth.audit_logs(resource_type, resource_id);

-- ============================================================================
-- 8. 触发器和函数
-- ============================================================================

-- 更新updated_at字段的函数
CREATE OR REPLACE FUNCTION auth.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为users表创建触发器
CREATE TRIGGER users_update_updated_at
    BEFORE UPDATE ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION auth.update_updated_at_column();

-- 审计触发器函数
CREATE OR REPLACE FUNCTION auth.audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO auth.audit_logs (
            user_id, action, resource_type, resource_id, new_values, ip_address
        ) VALUES (
            NEW.id,
            TG_OP,
            TG_TABLE_NAME,
            NEW.id::text,
            to_jsonb(NEW),
            inet_client_addr()
        );
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO auth.audit_logs (
            user_id, action, resource_type, resource_id, old_values, new_values, ip_address
        ) VALUES (
            NEW.id,
            TG_OP,
            TG_TABLE_NAME,
            NEW.id::text,
            to_jsonb(OLD),
            to_jsonb(NEW),
            inet_client_addr()
        );
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO auth.audit_logs (
            user_id, action, resource_type, resource_id, old_values, ip_address
        ) VALUES (
            OLD.id,
            TG_OP,
            TG_TABLE_NAME,
            OLD.id::text,
            to_jsonb(OLD),
            inet_client_addr()
        );
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 为用户表创建审计触发器
CREATE TRIGGER users_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION auth.audit_trigger_function();

-- ============================================================================
-- 9. 视图定义
-- ============================================================================

-- 活跃用户视图
CREATE VIEW auth.active_users AS
SELECT
    id,
    email,
    username,
    is_verified,
    created_at,
    last_login_at,
    failed_login_count
FROM auth.users
WHERE is_active = true AND (locked_until IS NULL OR locked_until < CURRENT_TIMESTAMP);

-- 用户会话统计视图
CREATE VIEW auth.user_session_stats AS
SELECT
    u.id,
    u.email,
    COUNT(s.id) as active_sessions,
    MAX(s.last_used_at) as last_session_activity
FROM auth.users u
LEFT JOIN auth.sessions s ON u.id = s.user_id AND s.is_active = true AND s.expires_at > CURRENT_TIMESTAMP
GROUP BY u.id, u.email;

-- ============================================================================
-- 10. 安全配置和策略
-- ============================================================================

-- 行级安全策略
ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth.login_attempts ENABLE ROW LEVEL SECURITY;

-- 用户只能访问自己的数据
CREATE POLICY users_self_access ON auth.users
    FOR ALL
    USING (id = current_setting('auth.user_id')::uuid);

CREATE POLICY sessions_self_access ON auth.sessions
    FOR ALL
    USING (user_id = current_setting('auth.user_id')::uuid);

-- 登录尝试只能查看，不能修改
CREATE POLICY login_attempts_read_only ON auth.login_attempts
    FOR SELECT
    USING (user_id = current_setting('auth.user_id')::uuid);

-- ============================================================================
-- 11. 创建角色和权限
-- ============================================================================

-- 创建数据库角色
CREATE ROLE auth_app_user;
CREATE ROLE auth_admin;

-- 授予基础权限
GRANT USAGE ON SCHEMA auth TO auth_app_user;
GRANT SELECT, INSERT, UPDATE ON auth.users TO auth_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON auth.sessions TO auth_app_user;
GRANT INSERT ON auth.login_attempts TO auth_app_user;
GRANT SELECT ON auth.login_attempts TO auth_app_user;

-- 授予序列权限
GRANT USAGE ON ALL SEQUENCES IN SCHEMA auth TO auth_app_user;

-- 管理员权限
GRANT ALL PRIVILEGES ON SCHEMA auth TO auth_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO auth_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth TO auth_admin;

-- ============================================================================
-- 12. 插入初始数据
-- ============================================================================

-- 插入默认角色
INSERT INTO auth.roles (name, description) VALUES
('admin', '系统管理员'),
('user', '普通用户'),
('guest', '访客用户');

-- 插入基础权限
INSERT INTO auth.permissions (name, resource, action, description) VALUES
('user.read', 'user', 'read', '读取用户信息'),
('user.update', 'user', 'update', '更新用户信息'),
('user.delete', 'user', 'delete', '删除用户'),
('session.manage', 'session', 'manage', '管理用户会话'),
('admin.access', 'admin', 'access', '访问管理面板');

-- 角色权限关联
INSERT INTO auth.role_permissions (role_id, permission_id) VALUES
((SELECT id FROM auth.roles WHERE name = 'user'), (SELECT id FROM auth.permissions WHERE name = 'user.read')),
((SELECT id FROM auth.roles WHERE name = 'user'), (SELECT id FROM auth.permissions WHERE name = 'user.update')),
((SELECT id FROM auth.roles WHERE name = 'user'), (SELECT id FROM auth.permissions WHERE name = 'session.manage')),
((SELECT id FROM auth.roles WHERE name = 'admin'), (SELECT id FROM auth.permissions WHERE name = 'user.read')),
((SELECT id FROM auth.roles WHERE name = 'admin'), (SELECT id FROM auth.permissions WHERE name = 'user.update')),
((SELECT id FROM auth.roles WHERE name = 'admin'), (SELECT id FROM auth.permissions WHERE name = 'user.delete')),
((SELECT id FROM auth.roles WHERE name = 'admin'), (SELECT id FROM auth.permissions WHERE name = 'session.manage')),
((SELECT id FROM auth.roles WHERE name = 'admin'), (SELECT id FROM auth.permissions WHERE name = 'admin.access'));

-- ============================================================================
-- 13. 性能优化建议
-- ============================================================================

/*
索引策略说明：

1. 主键索引：所有表都有自动创建的主键索引
2. 唯一索引：email和username的唯一性约束
3. 外键索引：提高JOIN查询性能
4. 复合索引：针对常见查询模式优化
5. 部分索引：只为活跃数据创建索引，节省空间

查询优化建议：

1. 使用prepared statements防止SQL注入
2. 限制查询结果集大小，使用分页
3. 定期清理过期的会话和登录记录
4. 监控慢查询日志
5. 定期更新表统计信息

分区策略（大数据量时）：

1. login_attempts表可按时间分区
2. audit_logs表可按月份分区
3. sessions表可按用户ID哈希分区
*/

-- ============================================================================
-- 14. 维护任务
-- ============================================================================

-- 清理过期会话的函数
CREATE OR REPLACE FUNCTION auth.cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM auth.sessions
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    INSERT INTO auth.audit_logs (action, resource_type, new_values)
    VALUES ('cleanup', 'sessions', jsonb_build_object('deleted_count', deleted_count));

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 清理过期登录记录的函数
CREATE OR REPLACE FUNCTION auth.cleanup_old_login_attempts()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM auth.login_attempts
    WHERE attempt_time < CURRENT_TIMESTAMP - INTERVAL '90 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    INSERT INTO auth.audit_logs (action, resource_type, new_values)
    VALUES ('cleanup', 'login_attempts', jsonb_build_object('deleted_count', deleted_count));

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 重置用户锁定状态的函数
CREATE OR REPLACE FUNCTION auth.reset_user_locks()
RETURNS INTEGER AS $$
DECLARE
    reset_count INTEGER;
BEGIN
    UPDATE auth.users
    SET
        failed_login_count = 0,
        locked_until = NULL
    WHERE locked_until < CURRENT_TIMESTAMP;

    GET DIAGNOSTICS reset_count = ROW_COUNT;

    RETURN reset_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 15. 安全配置
-- ============================================================================

/*
数据库级安全配置：

1. 启用SSL连接
2. 配置防火墙规则
3. 定期备份数据
4. 启用查询日志
5. 限制连接数
6. 使用连接池
7. 定期更新数据库版本

应用级安全配置：

1. 密码使用bcrypt或argon2哈希
2. 实现速率限制
3. 使用HTTPS
4. 实现CSRF保护
5. 验证所有输入
6. 使用参数化查询
7. 实现会话管理
8. 定期轮换密钥
*/

COMMENT ON SCHEMA auth IS 'Perfect21用户认证系统模式';
COMMENT ON TABLE auth.users IS '用户主表，存储用户基本信息和安全相关字段';
COMMENT ON TABLE auth.sessions IS '用户会话表，支持多设备登录和会话管理';
COMMENT ON TABLE auth.login_attempts IS '登录尝试记录表，用于安全审计和防暴力破解';
COMMENT ON TABLE auth.roles IS '用户角色表';
COMMENT ON TABLE auth.permissions IS '权限表';
COMMENT ON TABLE auth.audit_logs IS '审计日志表，记录所有重要操作';

-- 完成消息
SELECT 'Perfect21认证系统数据库架构创建完成！' AS status;