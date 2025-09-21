-- =============================================================================
-- High-Performance Authentication Database Schema
-- =============================================================================
-- Database: PostgreSQL 15+ (for advanced features)
-- Purpose: User authentication with role-based access control
-- Performance: Optimized for 100K+ concurrent users
-- =============================================================================

-- Create dedicated schema for authentication
CREATE SCHEMA IF NOT EXISTS auth_system;
SET search_path TO auth_system, public;

-- =============================================================================
-- CORE TABLES
-- =============================================================================

-- 1. Users Table (Core user information)
-- Think of this as the master ID card system
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(320) UNIQUE NOT NULL, -- RFC 5321 max length
    password_hash TEXT NOT NULL, -- bcrypt/argon2 hash
    phone_number VARCHAR(20),

    -- Security fields
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ NULL,

    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMPTZ,
    last_login_ip INET,

    -- Soft delete
    deleted_at TIMESTAMPTZ NULL,

    -- Performance optimization
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT valid_username CHECK (username ~* '^[a-zA-Z0-9_]{3,50}$')
);

-- 2. Roles Table (Authorization roles)
-- Think of this as job titles with specific permissions
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE, -- Prevents deletion of critical roles

    -- Hierarchy support
    parent_role_id UUID REFERENCES roles(id) ON DELETE SET NULL,
    level INTEGER DEFAULT 0, -- For hierarchy queries

    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),

    -- Constraints
    CONSTRAINT valid_role_name CHECK (name ~* '^[a-zA-Z0-9_-]{2,50}$')
);

-- 3. Permissions Table (Granular permissions)
-- Think of this as specific keys for specific doors
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL, -- e.g., 'users', 'orders', 'reports'
    action VARCHAR(30) NOT NULL,   -- e.g., 'read', 'write', 'delete', 'admin'
    description TEXT,

    -- Categorization
    category VARCHAR(50) DEFAULT 'general',
    is_dangerous BOOLEAN DEFAULT FALSE, -- For extra security checks

    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint on resource + action
    UNIQUE(resource, action)
);

-- 4. User Roles (Many-to-Many relationship)
-- Think of this as assigning job titles to employees
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,

    -- Temporal access (optional)
    granted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NULL,
    granted_by UUID REFERENCES users(id),

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Prevent duplicate assignments
    UNIQUE(user_id, role_id)
);

-- 5. Role Permissions (Many-to-Many relationship)
-- Think of this as defining what each job title can do
CREATE TABLE role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,

    -- Audit fields
    granted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    granted_by UUID REFERENCES users(id),

    -- Prevent duplicate assignments
    UNIQUE(role_id, permission_id)
);

-- =============================================================================
-- SECURITY & SESSION TABLES
-- =============================================================================

-- 6. User Sessions (Active login sessions)
-- Think of this as visitor badges that expire
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL, -- JWT jti or session ID
    refresh_token_hash TEXT UNIQUE, -- For refresh token rotation

    -- Session metadata
    ip_address INET,
    user_agent TEXT,
    device_fingerprint TEXT,

    -- Location data (optional)
    country_code CHAR(2),
    city VARCHAR(100),

    -- Timing
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    last_activity_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    revoked_at TIMESTAMPTZ NULL,
    revoked_reason VARCHAR(100),

    -- Performance index hint
    CONSTRAINT valid_expires_at CHECK (expires_at > created_at)
);

-- 7. Security Audit Log (Security events)
-- Think of this as a security camera recording everything important
CREATE TABLE security_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id UUID REFERENCES user_sessions(id) ON DELETE SET NULL,

    -- Event details
    event_type VARCHAR(50) NOT NULL, -- login, logout, password_change, etc.
    event_status VARCHAR(20) NOT NULL, -- success, failure, blocked
    event_description TEXT,

    -- Request metadata
    ip_address INET,
    user_agent TEXT,
    request_id UUID, -- For correlating with application logs

    -- Risk assessment
    risk_score INTEGER DEFAULT 0, -- 0-100 risk score
    is_suspicious BOOLEAN DEFAULT FALSE,

    -- Timing
    occurred_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Partitioning hint (monthly partitions)
    partition_date DATE GENERATED ALWAYS AS (occurred_at::DATE) STORED
) PARTITION BY RANGE (partition_date);

-- 8. Password History (Prevent password reuse)
-- Think of this as keeping track of old passwords to prevent reuse
CREATE TABLE password_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Only keep last 12 passwords per user
    CONSTRAINT max_history_per_user EXCLUDE USING gist (
        user_id WITH =,
        row_number() OVER (PARTITION BY user_id ORDER BY created_at DESC) WITH >
    ) WHERE (row_number() OVER (PARTITION BY user_id ORDER BY created_at DESC) <= 12)
);

-- =============================================================================
-- HIGH-PERFORMANCE OPTIMIZATION TABLES
-- =============================================================================

-- 9. User Role Cache (Denormalized for performance)
-- Think of this as a quick lookup directory
CREATE MATERIALIZED VIEW user_role_cache AS
SELECT
    u.id as user_id,
    u.username,
    u.email,
    u.is_active as user_active,
    array_agg(DISTINCT r.name ORDER BY r.name) as role_names,
    array_agg(DISTINCT p.name ORDER BY p.name) as permission_names,
    array_agg(DISTINCT p.resource || ':' || p.action ORDER BY p.resource, p.action) as resource_actions,
    COUNT(DISTINCT ur.role_id) as role_count,
    COUNT(DISTINCT rp.permission_id) as permission_count,
    GREATEST(u.updated_at, MAX(ur.granted_at), MAX(rp.granted_at)) as cache_updated_at
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id AND ur.is_active = TRUE
LEFT JOIN roles r ON ur.role_id = r.id
LEFT JOIN role_permissions rp ON r.id = rp.role_id
LEFT JOIN permissions p ON rp.permission_id = p.id
WHERE u.deleted_at IS NULL
GROUP BY u.id, u.username, u.email, u.is_active, u.updated_at;

-- Create unique index for fast lookups
CREATE UNIQUE INDEX idx_user_role_cache_user_id ON user_role_cache (user_id);

-- =============================================================================
-- PARTITIONING (for large-scale systems)
-- =============================================================================

-- Create monthly partitions for security audit log
-- This is like organizing files by month for faster access
CREATE TABLE security_audit_log_2024_01 PARTITION OF security_audit_log
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE security_audit_log_2024_02 PARTITION OF security_audit_log
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Add more partitions as needed...

-- =============================================================================
-- TRIGGERS & FUNCTIONS
-- =============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to refresh user role cache
CREATE OR REPLACE FUNCTION refresh_user_role_cache()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_role_cache;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Refresh cache when user roles change
CREATE TRIGGER refresh_cache_on_user_role_change
    AFTER INSERT OR UPDATE OR DELETE ON user_roles
    FOR EACH STATEMENT EXECUTE FUNCTION refresh_user_role_cache();

-- =============================================================================
-- SEED DATA (Initial system setup)
-- =============================================================================

-- Insert system roles
INSERT INTO roles (name, description, is_system_role, level) VALUES
('super_admin', 'System super administrator with all permissions', true, 0),
('admin', 'Application administrator', true, 1),
('user_manager', 'Can manage users and their roles', true, 2),
('user', 'Standard application user', true, 3),
('guest', 'Limited access user', true, 4);

-- Insert basic permissions
INSERT INTO permissions (name, resource, action, category, description) VALUES
-- User management
('users.read', 'users', 'read', 'user_management', 'View user information'),
('users.write', 'users', 'write', 'user_management', 'Create and update users'),
('users.delete', 'users', 'delete', 'user_management', 'Delete users'),
('users.admin', 'users', 'admin', 'user_management', 'Full user management'),

-- Role management
('roles.read', 'roles', 'read', 'role_management', 'View roles'),
('roles.write', 'roles', 'write', 'role_management', 'Create and update roles'),
('roles.delete', 'roles', 'delete', 'role_management', 'Delete roles'),
('roles.admin', 'roles', 'admin', 'role_management', 'Full role management'),

-- System administration
('system.read', 'system', 'read', 'system', 'View system information'),
('system.write', 'system', 'write', 'system', 'Modify system settings'),
('system.admin', 'system', 'admin', 'system', 'Full system administration');

-- Assign permissions to roles
WITH role_permission_mapping AS (
    SELECT
        r.id as role_id,
        p.id as permission_id
    FROM roles r
    CROSS JOIN permissions p
    WHERE
        -- Super admin gets everything
        (r.name = 'super_admin') OR
        -- Admin gets most things except super admin functions
        (r.name = 'admin' AND p.name NOT LIKE 'system.admin') OR
        -- User manager gets user and role read/write
        (r.name = 'user_manager' AND p.name IN ('users.read', 'users.write', 'roles.read')) OR
        -- Regular user gets basic read access
        (r.name = 'user' AND p.name IN ('users.read')) OR
        -- Guest gets minimal access
        (r.name = 'guest' AND p.name IN ('users.read'))
)
INSERT INTO role_permissions (role_id, permission_id)
SELECT role_id, permission_id FROM role_permission_mapping;

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON SCHEMA auth_system IS 'High-performance authentication and authorization system';
COMMENT ON TABLE users IS 'Core user accounts with security features';
COMMENT ON TABLE roles IS 'Hierarchical role definitions for authorization';
COMMENT ON TABLE permissions IS 'Granular permissions for fine-grained access control';
COMMENT ON TABLE user_roles IS 'Many-to-many mapping between users and roles';
COMMENT ON TABLE role_permissions IS 'Many-to-many mapping between roles and permissions';
COMMENT ON TABLE user_sessions IS 'Active user sessions with security metadata';
COMMENT ON TABLE security_audit_log IS 'Comprehensive security event logging (partitioned)';
COMMENT ON TABLE password_history IS 'Password history to prevent reuse';
COMMENT ON MATERIALIZED VIEW user_role_cache IS 'Denormalized view for fast permission checks';

-- =============================================================================
-- PERFORMANCE STATISTICS
-- =============================================================================

-- Enable query statistics collection
ALTER SYSTEM SET track_activities = on;
ALTER SYSTEM SET track_counts = on;
ALTER SYSTEM SET track_io_timing = on;
ALTER SYSTEM SET track_functions = all;

-- =============================================================================
-- SCHEMA VALIDATION
-- =============================================================================

-- Verify all tables were created successfully
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'auth_system';

    IF table_count >= 8 THEN
        RAISE NOTICE 'SUCCESS: All % tables created successfully', table_count;
    ELSE
        RAISE EXCEPTION 'ERROR: Only % tables created, expected at least 8', table_count;
    END IF;
END
$$;