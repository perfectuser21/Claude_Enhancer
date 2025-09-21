-- =====================================================
-- User Authentication System - PostgreSQL Schema
-- Version: 1.0
-- Created: 2025-09-20
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";

-- Create dedicated schema for authentication
CREATE SCHEMA IF NOT EXISTS auth;

-- Set search path
SET search_path TO auth, public;

-- =====================================================
-- 1. ROLES AND PERMISSIONS ENUM TYPES
-- =====================================================

CREATE TYPE user_role AS ENUM (
    'admin',
    'moderator',
    'user',
    'guest'
);

CREATE TYPE account_status AS ENUM (
    'active',
    'suspended',
    'deactivated',
    'pending_verification'
);

CREATE TYPE login_status AS ENUM (
    'success',
    'failed_password',
    'failed_2fa',
    'blocked_ip',
    'account_locked'
);

CREATE TYPE token_type AS ENUM (
    'access',
    'refresh',
    'email_verification',
    'password_reset',
    '2fa_backup'
);

-- =====================================================
-- 2. CORE USERS TABLE
-- =====================================================

CREATE TABLE users (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Authentication credentials
    email CITEXT UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    -- Account status and verification
    account_status account_status NOT NULL DEFAULT 'pending_verification',
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    email_verified_at TIMESTAMPTZ,

    -- Role and permissions
    role user_role NOT NULL DEFAULT 'user',
    permissions JSONB DEFAULT '{}',

    -- Profile information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone_number VARCHAR(20),
    avatar_url TEXT,

    -- Security settings
    two_factor_enabled BOOLEAN NOT NULL DEFAULT false,
    two_factor_secret VARCHAR(32),
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,

    -- Audit timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Soft delete
    deleted_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_username_format CHECK (username ~* '^[a-zA-Z0-9_]{3,50}$'),
    CONSTRAINT users_failed_attempts_range CHECK (failed_login_attempts >= 0 AND failed_login_attempts <= 10),
    CONSTRAINT users_phone_format CHECK (phone_number IS NULL OR phone_number ~* '^\+?[1-9]\d{1,14}$')
);

-- =====================================================
-- 3. REFRESH TOKENS TABLE
-- =====================================================

CREATE TABLE refresh_tokens (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Token information
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    token_type token_type NOT NULL DEFAULT 'refresh',

    -- User association
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Token lifecycle
    issued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,

    -- Device and session information
    device_id VARCHAR(255),
    device_name VARCHAR(255),
    device_type VARCHAR(50),
    operating_system VARCHAR(100),
    browser VARCHAR(100),
    user_agent TEXT,

    -- Network information
    ip_address INET,
    country_code CHAR(2),
    city VARCHAR(100),

    -- Security metadata
    is_revoked BOOLEAN NOT NULL DEFAULT false,
    revocation_reason VARCHAR(255),

    -- Constraints
    CONSTRAINT refresh_tokens_expires_future CHECK (expires_at > issued_at),
    CONSTRAINT refresh_tokens_device_type_valid CHECK (
        device_type IS NULL OR device_type IN ('mobile', 'tablet', 'desktop', 'tv', 'watch', 'other')
    )
);

-- =====================================================
-- 4. LOGIN HISTORY TABLE
-- =====================================================

CREATE TABLE login_history (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User association (nullable for failed login attempts)
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    email_attempted CITEXT,

    -- Login attempt details
    login_status login_status NOT NULL,
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Device information
    device_id VARCHAR(255),
    device_fingerprint VARCHAR(255),
    user_agent TEXT,

    -- Network information
    ip_address INET NOT NULL,
    country_code CHAR(2),
    city VARCHAR(100),
    timezone VARCHAR(50),

    -- Security analysis
    is_suspicious BOOLEAN NOT NULL DEFAULT false,
    risk_score INTEGER CHECK (risk_score >= 0 AND risk_score <= 100),
    failure_reason TEXT,

    -- Session information
    session_id VARCHAR(255),
    session_duration INTERVAL,

    -- Additional metadata
    metadata JSONB DEFAULT '{}'
);

-- =====================================================
-- 5. PASSWORD RESETS TABLE
-- =====================================================

CREATE TABLE password_resets (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User association
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email CITEXT NOT NULL,

    -- Reset token
    token_hash VARCHAR(255) NOT NULL UNIQUE,

    -- Lifecycle
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,

    -- Request details
    ip_address INET NOT NULL,
    user_agent TEXT,

    -- Status
    is_used BOOLEAN NOT NULL DEFAULT false,
    is_expired BOOLEAN GENERATED ALWAYS AS (CURRENT_TIMESTAMP > expires_at) STORED,

    -- Constraints
    CONSTRAINT password_resets_expires_future CHECK (expires_at > created_at),
    CONSTRAINT password_resets_used_before_expired CHECK (
        used_at IS NULL OR used_at <= expires_at
    )
);

-- =====================================================
-- 6. EMAIL VERIFICATION TOKENS TABLE
-- =====================================================

CREATE TABLE email_verifications (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User association
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email CITEXT NOT NULL,

    -- Verification token
    token_hash VARCHAR(255) NOT NULL UNIQUE,

    -- Lifecycle
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    verified_at TIMESTAMPTZ,

    -- Request details
    ip_address INET,

    -- Status
    is_verified BOOLEAN NOT NULL DEFAULT false,
    is_expired BOOLEAN GENERATED ALWAYS AS (CURRENT_TIMESTAMP > expires_at) STORED,

    -- Constraints
    CONSTRAINT email_verifications_expires_future CHECK (expires_at > created_at)
);

-- =====================================================
-- 7. USER SESSIONS TABLE (Optional - for detailed session management)
-- =====================================================

CREATE TABLE user_sessions (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User association
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Session information
    session_token VARCHAR(255) NOT NULL UNIQUE,
    refresh_token_id UUID REFERENCES refresh_tokens(id) ON DELETE CASCADE,

    -- Lifecycle
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMPTZ,

    -- Device and network
    ip_address INET NOT NULL,
    user_agent TEXT,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Session data
    session_data JSONB DEFAULT '{}',

    -- Constraints
    CONSTRAINT user_sessions_expires_future CHECK (expires_at > created_at)
);

-- =====================================================
-- 8. AUDIT LOG TABLE
-- =====================================================

CREATE TABLE audit_log (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Event details
    event_type VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    record_id UUID,

    -- User context
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Change details
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],

    -- Context
    ip_address INET,
    user_agent TEXT,

    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Additional metadata
    metadata JSONB DEFAULT '{}'
);

-- =====================================================
-- 9. INDEXES FOR PERFORMANCE OPTIMIZATION
-- =====================================================

-- Users table indexes
CREATE INDEX CONCURRENTLY idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_users_username ON users(username) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_users_role ON users(role) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_users_status ON users(account_status, is_active) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_users_last_login ON users(last_login_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_users_created_at ON users(created_at DESC);

-- Refresh tokens indexes
CREATE INDEX CONCURRENTLY idx_refresh_tokens_user_id ON refresh_tokens(user_id) WHERE is_revoked = false;
CREATE INDEX CONCURRENTLY idx_refresh_tokens_expires ON refresh_tokens(expires_at) WHERE is_revoked = false;
CREATE INDEX CONCURRENTLY idx_refresh_tokens_device ON refresh_tokens(user_id, device_id) WHERE is_revoked = false;
CREATE INDEX CONCURRENTLY idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);

-- Login history indexes
CREATE INDEX CONCURRENTLY idx_login_history_user_id ON login_history(user_id, attempted_at DESC);
CREATE INDEX CONCURRENTLY idx_login_history_ip ON login_history(ip_address, attempted_at DESC);
CREATE INDEX CONCURRENTLY idx_login_history_attempted_at ON login_history(attempted_at DESC);
CREATE INDEX CONCURRENTLY idx_login_history_status ON login_history(login_status, attempted_at DESC);
CREATE INDEX CONCURRENTLY idx_login_history_suspicious ON login_history(is_suspicious) WHERE is_suspicious = true;

-- Password resets indexes
CREATE INDEX CONCURRENTLY idx_password_resets_user_id ON password_resets(user_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_password_resets_token ON password_resets(token_hash) WHERE is_used = false;
CREATE INDEX CONCURRENTLY idx_password_resets_expires ON password_resets(expires_at) WHERE is_used = false;

-- Email verification indexes
CREATE INDEX CONCURRENTLY idx_email_verifications_user_id ON email_verifications(user_id);
CREATE INDEX CONCURRENTLY idx_email_verifications_token ON email_verifications(token_hash) WHERE is_verified = false;

-- User sessions indexes
CREATE INDEX CONCURRENTLY idx_user_sessions_user_id ON user_sessions(user_id, last_activity_at DESC) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_user_sessions_token ON user_sessions(session_token) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_user_sessions_expires ON user_sessions(expires_at) WHERE is_active = true;

-- Audit log indexes
CREATE INDEX CONCURRENTLY idx_audit_log_user_id ON audit_log(user_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_audit_log_table_record ON audit_log(table_name, record_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_audit_log_event_type ON audit_log(event_type, created_at DESC);

-- =====================================================
-- 10. TRIGGERS FOR AUTOMATED UPDATES
-- =====================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to users table
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function for audit logging
CREATE OR REPLACE FUNCTION audit_table_changes()
RETURNS TRIGGER AS $$
DECLARE
    old_record JSONB;
    new_record JSONB;
    changed_fields TEXT[];
BEGIN
    -- Handle different trigger events
    IF TG_OP = 'DELETE' THEN
        old_record = to_jsonb(OLD);
        INSERT INTO audit_log (event_type, table_name, record_id, old_values, user_id)
        VALUES ('DELETE', TG_TABLE_NAME, OLD.id, old_record, OLD.id);
        RETURN OLD;
    ELSIF TG_OP = 'INSERT' THEN
        new_record = to_jsonb(NEW);
        INSERT INTO audit_log (event_type, table_name, record_id, new_values, user_id)
        VALUES ('INSERT', TG_TABLE_NAME, NEW.id, new_record, NEW.id);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        old_record = to_jsonb(OLD);
        new_record = to_jsonb(NEW);

        -- Find changed fields
        SELECT array_agg(key) INTO changed_fields
        FROM jsonb_each(old_record)
        WHERE value != new_record->key;

        INSERT INTO audit_log (event_type, table_name, record_id, old_values, new_values, changed_fields, user_id)
        VALUES ('UPDATE', TG_TABLE_NAME, NEW.id, old_record, new_record, changed_fields, NEW.id);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to important tables
CREATE TRIGGER trigger_users_audit
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW
    EXECUTE FUNCTION audit_table_changes();

-- =====================================================
-- 11. FUNCTIONS AND PROCEDURES
-- =====================================================

-- Function to clean expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Clean expired refresh tokens
    DELETE FROM refresh_tokens
    WHERE expires_at < CURRENT_TIMESTAMP
    AND is_revoked = true;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Clean expired password reset tokens
    DELETE FROM password_resets
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '24 hours';

    -- Clean expired email verification tokens
    DELETE FROM email_verifications
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '24 hours';

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to check user account status
CREATE OR REPLACE FUNCTION is_user_account_accessible(user_uuid UUID)
RETURNS BOOLEAN AS $$
DECLARE
    user_record RECORD;
BEGIN
    SELECT account_status, is_active, locked_until, deleted_at
    INTO user_record
    FROM users
    WHERE id = user_uuid;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    -- Check if account is deleted
    IF user_record.deleted_at IS NOT NULL THEN
        RETURN FALSE;
    END IF;

    -- Check if account is active
    IF NOT user_record.is_active THEN
        RETURN FALSE;
    END IF;

    -- Check if account is locked
    IF user_record.locked_until IS NOT NULL AND user_record.locked_until > CURRENT_TIMESTAMP THEN
        RETURN FALSE;
    END IF;

    -- Check account status
    IF user_record.account_status IN ('suspended', 'deactivated') THEN
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 12. ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Enable RLS on sensitive tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE login_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE password_resets ENABLE ROW LEVEL SECURITY;

-- Create policies for different user roles
-- Users can only see their own data
CREATE POLICY users_self_access ON users
    FOR ALL
    USING (id = current_setting('app.current_user_id')::UUID);

-- Admins can see all users
CREATE POLICY users_admin_access ON users
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE id = current_setting('app.current_user_id')::UUID
            AND role = 'admin'
        )
    );

-- =====================================================
-- 13. VIEWS FOR COMMON QUERIES
-- =====================================================

-- Active users view
CREATE VIEW active_users AS
SELECT
    id,
    email,
    username,
    first_name,
    last_name,
    role,
    account_status,
    is_verified,
    two_factor_enabled,
    created_at,
    last_login_at
FROM users
WHERE deleted_at IS NULL
AND is_active = true;

-- User session summary view
CREATE VIEW user_session_summary AS
SELECT
    u.id as user_id,
    u.email,
    u.username,
    COUNT(ut.id) as active_tokens,
    MAX(ut.last_used_at) as last_token_used,
    COUNT(us.id) as active_sessions,
    MAX(us.last_activity_at) as last_session_activity
FROM users u
LEFT JOIN refresh_tokens ut ON u.id = ut.user_id AND ut.is_revoked = false AND ut.expires_at > CURRENT_TIMESTAMP
LEFT JOIN user_sessions us ON u.id = us.user_id AND us.is_active = true AND us.expires_at > CURRENT_TIMESTAMP
WHERE u.deleted_at IS NULL
GROUP BY u.id, u.email, u.username;

-- Login attempts summary view
CREATE VIEW login_attempts_summary AS
SELECT
    COALESCE(user_id, uuid_nil()) as user_id,
    email_attempted,
    ip_address,
    DATE(attempted_at) as attempt_date,
    COUNT(*) as total_attempts,
    COUNT(*) FILTER (WHERE login_status = 'success') as successful_attempts,
    COUNT(*) FILTER (WHERE login_status != 'success') as failed_attempts,
    MAX(attempted_at) as last_attempt
FROM login_history
WHERE attempted_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY user_id, email_attempted, ip_address, DATE(attempted_at);

-- =====================================================
-- 14. COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON SCHEMA auth IS 'Authentication and user management schema';

COMMENT ON TABLE users IS 'Core user accounts table with authentication and profile data';
COMMENT ON COLUMN users.id IS 'Primary key - UUID for better security and distribution';
COMMENT ON COLUMN users.email IS 'User email address - case insensitive, used for login';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt hashed password - never store plaintext';
COMMENT ON COLUMN users.failed_login_attempts IS 'Counter for consecutive failed login attempts';
COMMENT ON COLUMN users.locked_until IS 'Account lockout expiration timestamp';

COMMENT ON TABLE refresh_tokens IS 'JWT refresh tokens for session management';
COMMENT ON COLUMN refresh_tokens.token_hash IS 'Hashed refresh token - never store plaintext tokens';
COMMENT ON COLUMN refresh_tokens.device_id IS 'Unique identifier for user device';

COMMENT ON TABLE login_history IS 'Audit trail of all login attempts (successful and failed)';
COMMENT ON COLUMN login_history.risk_score IS 'Security risk assessment score (0-100)';
COMMENT ON COLUMN login_history.is_suspicious IS 'Flag for potentially fraudulent login attempts';

COMMENT ON TABLE password_resets IS 'Password reset tokens with expiration and usage tracking';
COMMENT ON TABLE email_verifications IS 'Email verification tokens for account activation';

COMMENT ON TABLE audit_log IS 'System-wide audit trail for security and compliance';

-- =====================================================
-- 15. INITIAL DATA AND ROLES
-- =====================================================

-- Create database roles for application
CREATE ROLE app_read;
CREATE ROLE app_write;
CREATE ROLE app_admin;

-- Grant appropriate permissions
GRANT USAGE ON SCHEMA auth TO app_read, app_write, app_admin;
GRANT SELECT ON ALL TABLES IN SCHEMA auth TO app_read;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA auth TO app_write;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO app_admin;

-- Grant sequence permissions
GRANT USAGE ON ALL SEQUENCES IN SCHEMA auth TO app_write, app_admin;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT SELECT ON TABLES TO app_read;
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT SELECT, INSERT, UPDATE ON TABLES TO app_write;
ALTER DEFAULT PRIVILEGES IN SCHEMA auth GRANT ALL PRIVILEGES ON TABLES TO app_admin;

-- =====================================================
-- END OF SCHEMA DEFINITION
-- =====================================================