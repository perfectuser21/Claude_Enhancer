-- =============================================================================
-- SHARDING AND PARTITIONING STRATEGY
-- =============================================================================
-- Purpose: Scale beyond single database limits (10M+ users)
-- Strategy: Hybrid approach with horizontal and vertical partitioning
-- Target: Support 1M+ concurrent users across multiple database instances
-- =============================================================================

-- =============================================================================
-- 1. HORIZONTAL SHARDING STRATEGY
-- =============================================================================

-- SHARDING PHILOSOPHY:
-- Think of this like dividing a massive library into multiple buildings,
-- where each building (shard) contains a subset of all the books (data)

-- Sharding Key: user_id (UUID)
-- Shards: 16 shards initially (can scale to 64, 256, etc.)
-- Distribution: Consistent hashing based on user_id

-- =============================================================================
-- SHARD CONFIGURATION
-- =============================================================================

-- Shard routing function
CREATE OR REPLACE FUNCTION get_shard_id(user_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
    shard_count INTEGER := 16; -- Current number of shards
    hash_value BIGINT;
BEGIN
    -- Use the first 8 bytes of UUID for consistent hashing
    hash_value := ('x' || substring(user_uuid::TEXT, 1, 8))::bit(32)::BIGINT;
    RETURN (hash_value % shard_count) + 1;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Test the sharding function
SELECT
    'Shard Distribution Test' AS test_name,
    shard_id,
    COUNT(*) as user_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM (
    SELECT get_shard_id(gen_random_uuid()) as shard_id
    FROM generate_series(1, 10000)
) t
GROUP BY shard_id
ORDER BY shard_id;

-- =============================================================================
-- 2. SHARD-AWARE TABLE DEFINITIONS
-- =============================================================================

-- Users table (sharded by user_id)
CREATE TABLE users_shard_template (
    id UUID PRIMARY KEY,
    shard_id INTEGER NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(320) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
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

    -- Sharding constraint
    CONSTRAINT check_shard_id CHECK (shard_id = get_shard_id(id)),
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- User sessions (sharded by user_id)
CREATE TABLE user_sessions_shard_template (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    shard_id INTEGER NOT NULL,
    session_token TEXT UNIQUE NOT NULL,
    refresh_token_hash TEXT UNIQUE,

    -- Session metadata
    ip_address INET,
    user_agent TEXT,
    device_fingerprint TEXT,
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

    -- Foreign key within shard
    FOREIGN KEY (user_id, shard_id) REFERENCES users_shard_template(id, shard_id),
    CONSTRAINT check_session_shard_id CHECK (shard_id = get_shard_id(user_id))
);

-- =============================================================================
-- 3. GLOBAL TABLES (NOT SHARDED)
-- =============================================================================

-- These tables are replicated across all shards or kept in a central location
-- Think of these as reference books that every library building needs a copy of

-- Roles (global - same across all shards)
CREATE TABLE roles_global (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,
    parent_role_id UUID REFERENCES roles_global(id) ON DELETE SET NULL,
    level INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by UUID -- Note: This references users but can't be FK due to sharding
);

-- Permissions (global - same across all shards)
CREATE TABLE permissions_global (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(30) NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'general',
    is_dangerous BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(resource, action)
);

-- Role permissions (global)
CREATE TABLE role_permissions_global (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES roles_global(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions_global(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    granted_by UUID, -- References users but can't be FK due to sharding
    UNIQUE(role_id, permission_id)
);

-- =============================================================================
-- 4. CROSS-SHARD LOOKUP TABLES
-- =============================================================================

-- Email to shard mapping (for login)
-- Think of this as a directory that tells you which building a book is in
CREATE TABLE email_shard_lookup (
    email VARCHAR(320) PRIMARY KEY,
    user_id UUID NOT NULL,
    shard_id INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT check_lookup_shard_id CHECK (shard_id = get_shard_id(user_id))
);

-- Username to shard mapping
CREATE TABLE username_shard_lookup (
    username VARCHAR(50) PRIMARY KEY,
    user_id UUID NOT NULL,
    shard_id INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT check_username_shard_id CHECK (shard_id = get_shard_id(user_id))
);

-- Session token to shard mapping (for session validation)
CREATE TABLE session_shard_lookup (
    session_token TEXT PRIMARY KEY,
    user_id UUID NOT NULL,
    shard_id INTEGER NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT check_session_lookup_shard_id CHECK (shard_id = get_shard_id(user_id))
);

-- =============================================================================
-- 5. SHARD MANAGEMENT FUNCTIONS
-- =============================================================================

-- Function to create a new shard
CREATE OR REPLACE FUNCTION create_shard(shard_number INTEGER)
RETURNS TEXT AS $$
DECLARE
    shard_name TEXT;
    table_name TEXT;
    result TEXT := '';
BEGIN
    shard_name := 'shard_' || shard_number;

    -- Create schema for the shard
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', shard_name);

    -- Create users table for this shard
    table_name := shard_name || '.users';
    EXECUTE format('
        CREATE TABLE %I (LIKE users_shard_template INCLUDING ALL)
    ', table_name);

    -- Add shard-specific constraint
    EXECUTE format('
        ALTER TABLE %I ADD CONSTRAINT shard_constraint
        CHECK (shard_id = %L)
    ', table_name, shard_number);

    -- Create user_sessions table for this shard
    table_name := shard_name || '.user_sessions';
    EXECUTE format('
        CREATE TABLE %I (LIKE user_sessions_shard_template INCLUDING ALL)
    ', table_name);

    -- Add shard-specific constraint
    EXECUTE format('
        ALTER TABLE %I ADD CONSTRAINT shard_constraint
        CHECK (shard_id = %L)
    ', table_name, shard_number);

    -- Create user_roles table for this shard
    table_name := shard_name || '.user_roles';
    EXECUTE format('
        CREATE TABLE %I (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            role_id UUID NOT NULL REFERENCES roles_global(id),
            shard_id INTEGER NOT NULL,
            granted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMPTZ NULL,
            granted_by UUID,
            is_active BOOLEAN DEFAULT TRUE,
            UNIQUE(user_id, role_id),
            CONSTRAINT check_user_roles_shard_id CHECK (shard_id = %L AND shard_id = get_shard_id(user_id))
        )
    ', table_name, shard_number);

    result := 'Shard ' || shard_number || ' created successfully';
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to route queries to the correct shard
CREATE OR REPLACE FUNCTION get_shard_info(user_uuid UUID)
RETURNS TABLE(shard_id INTEGER, schema_name TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT
        get_shard_id(user_uuid) as shard_id,
        'shard_' || get_shard_id(user_uuid) as schema_name;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 6. CROSS-SHARD QUERY FUNCTIONS
-- =============================================================================

-- Function to find user by email (uses lookup table)
CREATE OR REPLACE FUNCTION find_user_by_email(user_email TEXT)
RETURNS TABLE(
    user_id UUID,
    shard_id INTEGER,
    username TEXT,
    email TEXT,
    is_active BOOLEAN
) AS $$
DECLARE
    lookup_record RECORD;
    query_text TEXT;
BEGIN
    -- First, find which shard the user is in
    SELECT esl.user_id, esl.shard_id
    INTO lookup_record
    FROM email_shard_lookup esl
    WHERE esl.email = user_email;

    IF NOT FOUND THEN
        RETURN; -- User not found
    END IF;

    -- Query the appropriate shard
    query_text := format('
        SELECT u.id, %L::INTEGER, u.username, u.email, u.is_active
        FROM shard_%s.users u
        WHERE u.id = %L AND u.deleted_at IS NULL
    ', lookup_record.shard_id, lookup_record.shard_id, lookup_record.user_id);

    RETURN QUERY EXECUTE query_text;
END;
$$ LANGUAGE plpgsql;

-- Function to validate session across shards
CREATE OR REPLACE FUNCTION validate_session(token TEXT)
RETURNS TABLE(
    user_id UUID,
    shard_id INTEGER,
    expires_at TIMESTAMPTZ,
    is_valid BOOLEAN
) AS $$
DECLARE
    lookup_record RECORD;
    query_text TEXT;
BEGIN
    -- Find which shard the session is in
    SELECT ssl.user_id, ssl.shard_id, ssl.expires_at
    INTO lookup_record
    FROM session_shard_lookup ssl
    WHERE ssl.session_token = token;

    IF NOT FOUND THEN
        RETURN; -- Session not found
    END IF;

    -- Validate session in the appropriate shard
    query_text := format('
        SELECT us.user_id, %L::INTEGER, us.expires_at,
               (us.is_active AND us.revoked_at IS NULL AND us.expires_at > CURRENT_TIMESTAMP) as is_valid
        FROM shard_%s.user_sessions us
        WHERE us.session_token = %L
    ', lookup_record.shard_id, lookup_record.shard_id, token);

    RETURN QUERY EXECUTE query_text;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 7. SHARD MAINTENANCE FUNCTIONS
-- =============================================================================

-- Function to rebalance shards (when adding new shards)
CREATE OR REPLACE FUNCTION rebalance_shards(old_shard_count INTEGER, new_shard_count INTEGER)
RETURNS TEXT AS $$
DECLARE
    migration_plan TEXT := '';
    affected_users INTEGER := 0;
BEGIN
    -- This is a complex operation that would typically be done offline
    -- or with careful coordination to avoid downtime

    -- Calculate which users need to move
    WITH user_migrations AS (
        SELECT
            u.id,
            u.shard_id as current_shard,
            get_shard_id(u.id) as target_shard
        FROM (
            -- This would union all user tables from all current shards
            -- Simplified for demonstration
            SELECT id, shard_id FROM shard_1.users
            UNION ALL
            SELECT id, shard_id FROM shard_2.users
            -- ... etc for all shards
        ) u
        WHERE u.shard_id != get_shard_id(u.id)
    )
    SELECT COUNT(*) INTO affected_users FROM user_migrations;

    migration_plan := format('Rebalancing from %s to %s shards would affect %s users',
                           old_shard_count, new_shard_count, affected_users);

    RETURN migration_plan;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 8. MONITORING AND MAINTENANCE
-- =============================================================================

-- Shard statistics view
CREATE OR REPLACE VIEW shard_statistics AS
WITH shard_data AS (
    SELECT 1 as shard_id, COUNT(*) as user_count FROM shard_1.users WHERE deleted_at IS NULL
    UNION ALL
    SELECT 2 as shard_id, COUNT(*) as user_count FROM shard_2.users WHERE deleted_at IS NULL
    -- Add more shards as they're created
)
SELECT
    shard_id,
    user_count,
    ROUND(user_count * 100.0 / SUM(user_count) OVER (), 2) as percentage,
    CASE
        WHEN user_count > (SELECT AVG(user_count) * 1.2 FROM shard_data) THEN 'OVERLOADED'
        WHEN user_count < (SELECT AVG(user_count) * 0.8 FROM shard_data) THEN 'UNDERUTILIZED'
        ELSE 'BALANCED'
    END as status
FROM shard_data
ORDER BY shard_id;

-- =============================================================================
-- 9. VERTICAL PARTITIONING (TIME-BASED)
-- =============================================================================

-- Security audit log partitioned by month
CREATE TABLE security_audit_log_partitioned (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    session_id UUID,
    shard_id INTEGER, -- Include shard info for cross-shard queries

    -- Event details
    event_type VARCHAR(50) NOT NULL,
    event_status VARCHAR(20) NOT NULL,
    event_description TEXT,

    -- Request metadata
    ip_address INET,
    user_agent TEXT,
    request_id UUID,

    -- Risk assessment
    risk_score INTEGER DEFAULT 0,
    is_suspicious BOOLEAN DEFAULT FALSE,

    -- Timing
    occurred_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Partitioning column
    partition_date DATE GENERATED ALWAYS AS (occurred_at::DATE) STORED
) PARTITION BY RANGE (partition_date);

-- Create monthly partitions (automated)
CREATE OR REPLACE FUNCTION create_monthly_audit_partition(target_date DATE)
RETURNS TEXT AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    start_date := date_trunc('month', target_date)::DATE;
    end_date := (start_date + INTERVAL '1 month')::DATE;
    partition_name := 'security_audit_log_' || to_char(start_date, 'YYYY_MM');

    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I PARTITION OF security_audit_log_partitioned
        FOR VALUES FROM (%L) TO (%L)
    ', partition_name, start_date, end_date);

    -- Create indexes on the partition
    EXECUTE format('
        CREATE INDEX IF NOT EXISTS %I ON %I (user_id, occurred_at DESC)
    ', 'idx_' || partition_name || '_user_occurred', partition_name);

    EXECUTE format('
        CREATE INDEX IF NOT EXISTS %I ON %I (event_type, occurred_at DESC)
    ', 'idx_' || partition_name || '_event_occurred', partition_name);

    RETURN 'Partition ' || partition_name || ' created successfully';
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 10. SHARDING SUMMARY AND USAGE
-- =============================================================================

/*
SHARDING STRATEGY SUMMARY:

1. HORIZONTAL SHARDING:
   - 16 shards initially (can scale to 64, 256)
   - Sharded by user_id using consistent hashing
   - Each shard contains complete user data for its subset

2. GLOBAL TABLES:
   - roles_global: All roles replicated
   - permissions_global: All permissions replicated
   - role_permissions_global: Role-permission mappings

3. LOOKUP TABLES:
   - email_shard_lookup: Find user shard by email
   - username_shard_lookup: Find user shard by username
   - session_shard_lookup: Find session shard by token

4. VERTICAL PARTITIONING:
   - security_audit_log: Partitioned by month
   - Large tables split by time dimension

5. CROSS-SHARD OPERATIONS:
   - Use lookup tables for routing
   - Aggregate queries use UNION across shards
   - Global tables for reference data

USAGE EXAMPLES:

-- Login flow:
1. SELECT shard_id FROM email_shard_lookup WHERE email = ?
2. Query shard_X.users for authentication
3. Create session in shard_X.user_sessions
4. Insert into session_shard_lookup

-- Session validation:
1. SELECT shard_id FROM session_shard_lookup WHERE session_token = ?
2. Query shard_X.user_sessions for validation

-- Permission check:
1. Find user shard
2. Query shard_X.user_roles + roles_global + permissions_global
*/

-- Create initial shards
SELECT create_shard(1);
SELECT create_shard(2);
-- Add more as needed: SELECT create_shard(3); etc.

-- Create initial monthly partitions
SELECT create_monthly_audit_partition(CURRENT_DATE);
SELECT create_monthly_audit_partition(CURRENT_DATE + INTERVAL '1 month');

COMMENT ON FUNCTION get_shard_id IS 'Determines which shard a user belongs to based on their UUID';
COMMENT ON FUNCTION create_shard IS 'Creates a new shard with all necessary tables';
COMMENT ON VIEW shard_statistics IS 'Monitor shard balance and utilization';
COMMENT ON FUNCTION create_monthly_audit_partition IS 'Creates monthly partitions for audit log';

-- Final summary
DO $$
BEGIN
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'SHARDING STRATEGY DEPLOYED';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'Initial shards: 2 (can scale to 16, 64, 256)';
    RAISE NOTICE 'Sharding key: user_id (UUID-based consistent hashing)';
    RAISE NOTICE 'Global tables: roles, permissions, role_permissions';
    RAISE NOTICE 'Lookup tables: email, username, session routing';
    RAISE NOTICE 'Partitioning: security_audit_log by month';
    RAISE NOTICE 'Target capacity: 10M+ users, 1M+ concurrent';
    RAISE NOTICE '=============================================================================';
END
$$;