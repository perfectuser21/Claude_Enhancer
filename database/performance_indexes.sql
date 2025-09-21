-- =============================================================================
-- HIGH-PERFORMANCE INDEX OPTIMIZATION STRATEGY
-- =============================================================================
-- Purpose: Comprehensive indexing for authentication system
-- Target: 100K+ concurrent users, sub-100ms query response
-- Strategy: Balanced approach considering read/write patterns
-- =============================================================================

SET search_path TO auth_system, public;

-- =============================================================================
-- PRIMARY PERFORMANCE INDEXES
-- =============================================================================

-- 1. USERS TABLE INDEXES
-- Think of these as different ways to quickly find people in a phonebook

-- Fast login lookup (most critical)
CREATE INDEX CONCURRENTLY idx_users_email_active
ON users (email)
WHERE deleted_at IS NULL AND is_active = TRUE;

CREATE INDEX CONCURRENTLY idx_users_username_active
ON users (username)
WHERE deleted_at IS NULL AND is_active = TRUE;

-- Security monitoring indexes
CREATE INDEX CONCURRENTLY idx_users_failed_attempts
ON users (failed_login_attempts, locked_until)
WHERE failed_login_attempts > 0;

-- Phone verification lookup
CREATE INDEX CONCURRENTLY idx_users_phone_verified
ON users (phone_number)
WHERE phone_verified = TRUE AND deleted_at IS NULL;

-- Audit and reporting indexes
CREATE INDEX CONCURRENTLY idx_users_created_at
ON users (created_at DESC);

CREATE INDEX CONCURRENTLY idx_users_last_login
ON users (last_login_at DESC NULLS LAST)
WHERE deleted_at IS NULL;

-- Composite index for admin user management
CREATE INDEX CONCURRENTLY idx_users_status_composite
ON users (is_active, email_verified, created_at DESC)
WHERE deleted_at IS NULL;

-- =============================================================================
-- 2. USER_SESSIONS TABLE INDEXES
-- =============================================================================

-- Most critical: Session validation (happens on every request)
CREATE INDEX CONCURRENTLY idx_sessions_token_active
ON user_sessions (session_token)
WHERE is_active = TRUE AND revoked_at IS NULL;

-- User's active sessions lookup
CREATE INDEX CONCURRENTLY idx_sessions_user_active
ON user_sessions (user_id, is_active, expires_at DESC)
WHERE is_active = TRUE AND revoked_at IS NULL;

-- Session cleanup (for background jobs)
CREATE INDEX CONCURRENTLY idx_sessions_expires_at
ON user_sessions (expires_at)
WHERE is_active = TRUE;

-- Security monitoring: multiple sessions from same IP
CREATE INDEX CONCURRENTLY idx_sessions_ip_active
ON user_sessions (ip_address, created_at DESC)
WHERE is_active = TRUE;

-- Device tracking for security
CREATE INDEX CONCURRENTLY idx_sessions_device_fingerprint
ON user_sessions (device_fingerprint, user_id)
WHERE is_active = TRUE AND device_fingerprint IS NOT NULL;

-- Refresh token lookup
CREATE INDEX CONCURRENTLY idx_sessions_refresh_token
ON user_sessions (refresh_token_hash)
WHERE refresh_token_hash IS NOT NULL AND is_active = TRUE;

-- =============================================================================
-- 3. USER_ROLES TABLE INDEXES
-- =============================================================================

-- Permission checking (critical path)
CREATE INDEX CONCURRENTLY idx_user_roles_user_active
ON user_roles (user_id, is_active)
WHERE is_active = TRUE AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP);

-- Role management queries
CREATE INDEX CONCURRENTLY idx_user_roles_role_active
ON user_roles (role_id, is_active);

-- Temporal role queries
CREATE INDEX CONCURRENTLY idx_user_roles_expires_at
ON user_roles (expires_at)
WHERE expires_at IS NOT NULL;

-- Audit: who granted roles
CREATE INDEX CONCURRENTLY idx_user_roles_granted_by
ON user_roles (granted_by, granted_at DESC);

-- =============================================================================
-- 4. ROLES TABLE INDEXES
-- =============================================================================

-- Role lookup by name (common in APIs)
CREATE INDEX CONCURRENTLY idx_roles_name
ON roles (name);

-- Hierarchy traversal
CREATE INDEX CONCURRENTLY idx_roles_parent
ON roles (parent_role_id, level);

-- System role protection
CREATE INDEX CONCURRENTLY idx_roles_system
ON roles (is_system_role, name)
WHERE is_system_role = TRUE;

-- =============================================================================
-- 5. PERMISSIONS TABLE INDEXES
-- =============================================================================

-- Permission lookup by name
CREATE INDEX CONCURRENTLY idx_permissions_name
ON permissions (name);

-- Resource-based queries
CREATE INDEX CONCURRENTLY idx_permissions_resource_action
ON permissions (resource, action);

-- Category-based administration
CREATE INDEX CONCURRENTLY idx_permissions_category
ON permissions (category, name);

-- Dangerous permissions (security)
CREATE INDEX CONCURRENTLY idx_permissions_dangerous
ON permissions (is_dangerous, resource, action)
WHERE is_dangerous = TRUE;

-- =============================================================================
-- 6. ROLE_PERMISSIONS TABLE INDEXES
-- =============================================================================

-- Permission resolution (critical for authorization)
CREATE INDEX CONCURRENTLY idx_role_permissions_role
ON role_permissions (role_id, permission_id);

-- Reverse lookup: which roles have this permission
CREATE INDEX CONCURRENTLY idx_role_permissions_permission
ON role_permissions (permission_id, role_id);

-- Audit: when permissions were granted
CREATE INDEX CONCURRENTLY idx_role_permissions_granted_at
ON role_permissions (granted_at DESC);

-- =============================================================================
-- 7. SECURITY_AUDIT_LOG TABLE INDEXES
-- =============================================================================

-- User activity tracking
CREATE INDEX CONCURRENTLY idx_audit_user_occurred
ON security_audit_log (user_id, occurred_at DESC)
WHERE user_id IS NOT NULL;

-- Event type analysis
CREATE INDEX CONCURRENTLY idx_audit_event_type_occurred
ON security_audit_log (event_type, occurred_at DESC);

-- Security incident investigation
CREATE INDEX CONCURRENTLY idx_audit_suspicious
ON security_audit_log (is_suspicious, risk_score DESC, occurred_at DESC)
WHERE is_suspicious = TRUE;

-- IP-based security analysis
CREATE INDEX CONCURRENTLY idx_audit_ip_occurred
ON security_audit_log (ip_address, occurred_at DESC)
WHERE ip_address IS NOT NULL;

-- Failed events monitoring
CREATE INDEX CONCURRENTLY idx_audit_failures
ON security_audit_log (event_status, event_type, occurred_at DESC)
WHERE event_status = 'failure';

-- Session correlation
CREATE INDEX CONCURRENTLY idx_audit_session
ON security_audit_log (session_id, occurred_at DESC)
WHERE session_id IS NOT NULL;

-- =============================================================================
-- 8. PASSWORD_HISTORY TABLE INDEXES
-- =============================================================================

-- User password history lookup
CREATE INDEX CONCURRENTLY idx_password_history_user
ON password_history (user_id, created_at DESC);

-- Cleanup old passwords (background job)
CREATE INDEX CONCURRENTLY idx_password_history_created_at
ON password_history (created_at);

-- =============================================================================
-- ADVANCED PERFORMANCE INDEXES
-- =============================================================================

-- 9. COMPOSITE INDEXES FOR COMPLEX QUERIES

-- Complete user authentication check
CREATE INDEX CONCURRENTLY idx_users_auth_composite
ON users (email, password_hash, is_active, email_verified, failed_login_attempts)
WHERE deleted_at IS NULL;

-- User permission resolution (joins users -> user_roles -> role_permissions)
CREATE INDEX CONCURRENTLY idx_user_permission_path
ON user_roles (user_id, role_id, is_active)
INCLUDE (granted_at, expires_at);

-- Session security check
CREATE INDEX CONCURRENTLY idx_sessions_security_composite
ON user_sessions (user_id, session_token, expires_at, is_active)
WHERE revoked_at IS NULL;

-- =============================================================================
-- 10. PARTIAL INDEXES FOR SPECIFIC USE CASES
-- =============================================================================

-- Only active users (most queries filter by this)
CREATE INDEX CONCURRENTLY idx_users_active_only
ON users (id, username, email, created_at)
WHERE deleted_at IS NULL AND is_active = TRUE;

-- Only verified users
CREATE INDEX CONCURRENTLY idx_users_verified_only
ON users (id, email, last_login_at)
WHERE email_verified = TRUE AND deleted_at IS NULL;

-- Only locked users (for security monitoring)
CREATE INDEX CONCURRENTLY idx_users_locked_only
ON users (id, username, locked_until, failed_login_attempts)
WHERE locked_until IS NOT NULL AND locked_until > CURRENT_TIMESTAMP;

-- Only current sessions (most session queries)
CREATE INDEX CONCURRENTLY idx_sessions_current_only
ON user_sessions (user_id, session_token, last_activity_at)
WHERE is_active = TRUE AND expires_at > CURRENT_TIMESTAMP AND revoked_at IS NULL;

-- =============================================================================
-- 11. FULL-TEXT SEARCH INDEXES (for user search)
-- =============================================================================

-- User search by name/email (admin interface)
CREATE INDEX CONCURRENTLY idx_users_search
ON users USING gin(to_tsvector('english', coalesce(username, '') || ' ' || coalesce(email, '')))
WHERE deleted_at IS NULL;

-- =============================================================================
-- 12. COVERING INDEXES (PostgreSQL INCLUDE clause)
-- =============================================================================

-- User login with all needed data in one index
CREATE INDEX CONCURRENTLY idx_users_login_covering
ON users (email)
INCLUDE (id, password_hash, is_active, email_verified, failed_login_attempts, locked_until)
WHERE deleted_at IS NULL;

-- Session validation with user data
CREATE INDEX CONCURRENTLY idx_sessions_user_covering
ON user_sessions (session_token)
INCLUDE (user_id, expires_at, is_active, last_activity_at)
WHERE is_active = TRUE AND revoked_at IS NULL;

-- =============================================================================
-- INDEX MONITORING QUERIES
-- =============================================================================

-- Monitor index usage (run periodically)
CREATE OR REPLACE VIEW index_usage_stats AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    CASE
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 100 THEN 'LOW_USAGE'
        WHEN idx_scan < 1000 THEN 'MEDIUM_USAGE'
        ELSE 'HIGH_USAGE'
    END as usage_category
FROM pg_stat_user_indexes
WHERE schemaname = 'auth_system'
ORDER BY idx_scan DESC;

-- Index maintenance recommendations
CREATE OR REPLACE VIEW index_maintenance_recommendations AS
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as current_size,
    CASE
        WHEN idx_scan = 0 THEN 'Consider dropping - unused index'
        WHEN pg_relation_size(indexrelid) > 100 * 1024 * 1024 AND idx_scan < 1000
            THEN 'Consider dropping - large but rarely used'
        WHEN n_tup_upd + n_tup_ins > idx_scan * 10
            THEN 'Consider rebuilding - high write vs read ratio'
        ELSE 'OK'
    END as recommendation
FROM pg_stat_user_indexes sui
JOIN pg_stat_user_tables sut ON sui.relid = sut.relid
WHERE schemaname = 'auth_system'
ORDER BY pg_relation_size(indexrelid) DESC;

-- =============================================================================
-- INDEX CREATION SUMMARY
-- =============================================================================

-- Count total indexes created
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'auth_system'
    AND indexname NOT LIKE '%_pkey'; -- Exclude primary keys

    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'INDEX CREATION COMPLETE';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'Total indexes created: %', index_count;
    RAISE NOTICE 'Schema: auth_system';
    RAISE NOTICE 'Target performance: 100K+ concurrent users';
    RAISE NOTICE 'Expected query response time: <100ms';
    RAISE NOTICE '=============================================================================';
END
$$;

-- =============================================================================
-- MAINTENANCE REMINDERS
-- =============================================================================

COMMENT ON VIEW index_usage_stats IS 'Monitor index usage patterns - run weekly';
COMMENT ON VIEW index_maintenance_recommendations IS 'Index maintenance suggestions - run monthly';

-- Create a function to refresh index statistics
CREATE OR REPLACE FUNCTION refresh_index_stats()
RETURNS TEXT AS $$
BEGIN
    -- Reset statistics to get fresh data
    SELECT pg_stat_reset();
    RETURN 'Index statistics reset. Monitor usage over the next week.';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_index_stats IS 'Reset index statistics for fresh monitoring data';

-- =============================================================================
-- PERFORMANCE TESTING QUERIES
-- =============================================================================

-- Test critical path queries with EXPLAIN ANALYZE
/*
Example usage:

-- Test user login performance
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, password_hash, is_active, failed_login_attempts
FROM users
WHERE email = 'test@example.com' AND deleted_at IS NULL;

-- Test session validation performance
EXPLAIN (ANALYZE, BUFFERS)
SELECT us.user_id, us.expires_at, u.is_active
FROM user_sessions us
JOIN users u ON us.user_id = u.id
WHERE us.session_token = 'sample_token'
AND us.is_active = TRUE
AND us.revoked_at IS NULL;

-- Test permission checking performance
EXPLAIN (ANALYZE, BUFFERS)
SELECT DISTINCT p.name
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN role_permissions rp ON ur.role_id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE u.id = 'sample_user_id'
AND ur.is_active = TRUE
AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP);
*/