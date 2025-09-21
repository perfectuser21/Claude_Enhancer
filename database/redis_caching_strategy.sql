-- =============================================================================
-- REDIS CACHING STRATEGY FOR HIGH-PERFORMANCE AUTH SYSTEM
-- =============================================================================
-- Purpose: Multi-layer caching to achieve sub-10ms response times
-- Target: 1M+ concurrent users with 99.9% cache hit rate
-- Strategy: Smart caching with TTL optimization and cache warming
-- =============================================================================

-- This file contains SQL functions and Redis strategy documentation
-- The actual Redis commands would be executed by the application layer

-- =============================================================================
-- 1. CACHE LAYER ARCHITECTURE
-- =============================================================================

/*
CACHE ARCHITECTURE (Think of this as a multi-level memory system):

Layer 1: Application Memory Cache (Fastest - 1ms)
├── User permissions (in-memory for current request)
├── Role definitions (static, rarely changes)
└── Permission definitions (static, rarely changes)

Layer 2: Redis Cache (Fast - 2-5ms)
├── User session data
├── User profile cache
├── User permissions cache
├── Security metadata
└── Rate limiting counters

Layer 3: Database (Slower - 10-50ms)
├── Authoritative data source
├── Complex queries
└── Backup when cache misses

CACHE FLOW:
Request → App Memory → Redis → Database → Back-populate caches
*/

-- =============================================================================
-- 2. CACHE KEY STRATEGY
-- =============================================================================

-- PostgreSQL functions to generate consistent cache keys
-- These ensure the application uses the same key format everywhere

CREATE OR REPLACE FUNCTION get_user_cache_key(user_uuid UUID)
RETURNS TEXT AS $$
BEGIN
    RETURN 'auth:user:' || user_uuid::TEXT;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION get_session_cache_key(session_token TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN 'auth:session:' || session_token;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION get_user_permissions_cache_key(user_uuid UUID)
RETURNS TEXT AS $$
BEGIN
    RETURN 'auth:permissions:' || user_uuid::TEXT;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION get_user_roles_cache_key(user_uuid UUID)
RETURNS TEXT AS $$
BEGIN
    RETURN 'auth:roles:' || user_uuid::TEXT;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION get_rate_limit_key(identifier TEXT, window_type TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN 'auth:ratelimit:' || window_type || ':' || identifier;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Security-related cache keys
CREATE OR REPLACE FUNCTION get_failed_login_key(identifier TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN 'auth:failed_login:' || identifier;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION get_blocked_ip_key(ip_address TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN 'auth:blocked_ip:' || ip_address;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- 3. CACHE DATA STRUCTURES AND TTL STRATEGY
-- =============================================================================

/*
REDIS DATA STRUCTURES AND TTL:

1. USER SESSION CACHE (Hash)
   Key: auth:session:{token}
   TTL: Same as session expiry (typically 24 hours)
   Structure:
   {
     "user_id": "uuid",
     "expires_at": "timestamp",
     "last_activity": "timestamp",
     "ip_address": "ip",
     "user_agent": "string",
     "is_active": "true/false"
   }

2. USER PROFILE CACHE (Hash)
   Key: auth:user:{user_id}
   TTL: 1 hour (refreshed on access)
   Structure:
   {
     "id": "uuid",
     "username": "string",
     "email": "string",
     "is_active": "true/false",
     "email_verified": "true/false",
     "last_login": "timestamp",
     "failed_attempts": "number"
   }

3. USER PERMISSIONS CACHE (Set)
   Key: auth:permissions:{user_id}
   TTL: 30 minutes
   Structure: Set of permission names
   ["users.read", "users.write", "orders.read", ...]

4. USER ROLES CACHE (Set)
   Key: auth:roles:{user_id}
   TTL: 30 minutes
   Structure: Set of role names
   ["admin", "user_manager", ...]

5. RATE LIMITING (String with counter)
   Key: auth:ratelimit:{window}:{identifier}
   TTL: Window duration (1 minute, 5 minutes, 1 hour)
   Structure: Integer counter

6. SECURITY BLACKLISTS (String)
   Key: auth:blocked_ip:{ip}
   TTL: Variable (1 hour to 24 hours based on severity)
   Structure: Reason for blocking

7. GLOBAL REFERENCE DATA (Hash - Long TTL)
   Key: auth:roles:global
   TTL: 24 hours (rarely changes)
   Structure: All role definitions

   Key: auth:permissions:global
   TTL: 24 hours (rarely changes)
   Structure: All permission definitions
*/

-- =============================================================================
-- 4. CACHE WARMING FUNCTIONS
-- =============================================================================

-- Function to prepare user cache data (called when user logs in)
CREATE OR REPLACE FUNCTION prepare_user_cache_data(user_uuid UUID)
RETURNS JSONB AS $$
DECLARE
    user_data RECORD;
    roles_array TEXT[];
    permissions_array TEXT[];
    cache_data JSONB;
BEGIN
    -- Get user basic data
    SELECT u.id, u.username, u.email, u.is_active, u.email_verified,
           u.last_login_at, u.failed_login_attempts
    INTO user_data
    FROM users u
    WHERE u.id = user_uuid AND u.deleted_at IS NULL;

    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    -- Get user roles
    SELECT array_agg(r.name ORDER BY r.name)
    INTO roles_array
    FROM user_roles ur
    JOIN roles r ON ur.role_id = r.id
    WHERE ur.user_id = user_uuid
    AND ur.is_active = TRUE
    AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP);

    -- Get user permissions
    SELECT array_agg(DISTINCT p.name ORDER BY p.name)
    INTO permissions_array
    FROM user_roles ur
    JOIN role_permissions rp ON ur.role_id = rp.role_id
    JOIN permissions p ON rp.permission_id = p.id
    WHERE ur.user_id = user_uuid
    AND ur.is_active = TRUE
    AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP);

    -- Build cache data
    cache_data := jsonb_build_object(
        'user', jsonb_build_object(
            'id', user_data.id,
            'username', user_data.username,
            'email', user_data.email,
            'is_active', user_data.is_active,
            'email_verified', user_data.email_verified,
            'last_login', user_data.last_login_at,
            'failed_attempts', user_data.failed_login_attempts
        ),
        'roles', COALESCE(roles_array, ARRAY[]::TEXT[]),
        'permissions', COALESCE(permissions_array, ARRAY[]::TEXT[]),
        'cache_generated_at', CURRENT_TIMESTAMP
    );

    RETURN cache_data;
END;
$$ LANGUAGE plpgsql;

-- Function to prepare session cache data
CREATE OR REPLACE FUNCTION prepare_session_cache_data(session_token TEXT)
RETURNS JSONB AS $$
DECLARE
    session_data RECORD;
    cache_data JSONB;
BEGIN
    SELECT us.user_id, us.expires_at, us.last_activity_at, us.ip_address,
           us.user_agent, us.is_active, us.device_fingerprint
    INTO session_data
    FROM user_sessions us
    WHERE us.session_token = session_token
    AND us.revoked_at IS NULL;

    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    cache_data := jsonb_build_object(
        'user_id', session_data.user_id,
        'expires_at', session_data.expires_at,
        'last_activity', session_data.last_activity_at,
        'ip_address', session_data.ip_address,
        'user_agent', session_data.user_agent,
        'is_active', session_data.is_active,
        'device_fingerprint', session_data.device_fingerprint,
        'cache_generated_at', CURRENT_TIMESTAMP
    );

    RETURN cache_data;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 5. CACHE INVALIDATION TRIGGERS
-- =============================================================================

-- Function to generate cache invalidation commands
CREATE OR REPLACE FUNCTION generate_cache_invalidation_commands(
    table_name TEXT,
    operation TEXT,
    old_data JSONB DEFAULT NULL,
    new_data JSONB DEFAULT NULL
)
RETURNS TEXT[] AS $$
DECLARE
    commands TEXT[] := ARRAY[]::TEXT[];
    user_id UUID;
BEGIN
    CASE table_name
        WHEN 'users' THEN
            user_id := COALESCE((new_data->>'id')::UUID, (old_data->>'id')::UUID);
            commands := commands || ARRAY[
                'DEL ' || get_user_cache_key(user_id),
                'DEL ' || get_user_permissions_cache_key(user_id),
                'DEL ' || get_user_roles_cache_key(user_id)
            ];

        WHEN 'user_roles' THEN
            user_id := COALESCE((new_data->>'user_id')::UUID, (old_data->>'user_id')::UUID);
            commands := commands || ARRAY[
                'DEL ' || get_user_permissions_cache_key(user_id),
                'DEL ' || get_user_roles_cache_key(user_id)
            ];

        WHEN 'user_sessions' THEN
            IF operation = 'DELETE' OR operation = 'UPDATE' THEN
                commands := commands || ARRAY[
                    'DEL ' || get_session_cache_key(old_data->>'session_token')
                ];
            END IF;

        WHEN 'roles' THEN
            -- Invalidate global roles cache
            commands := commands || ARRAY['DEL auth:roles:global'];

        WHEN 'permissions' THEN
            -- Invalidate global permissions cache
            commands := commands || ARRAY['DEL auth:permissions:global'];

        WHEN 'role_permissions' THEN
            -- Invalidate all user permission caches (expensive but safe)
            commands := commands || ARRAY['EVAL "return redis.call(''DEL'', unpack(redis.call(''KEYS'', ''auth:permissions:*'')))" 0'];
    END CASE;

    RETURN commands;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 6. PERFORMANCE MONITORING FUNCTIONS
-- =============================================================================

-- Cache hit rate tracking table
CREATE TABLE cache_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    cache_layer VARCHAR(50) NOT NULL, -- 'redis', 'application'
    operation_type VARCHAR(50) NOT NULL, -- 'session_validation', 'permission_check', etc.
    hit_count BIGINT DEFAULT 0,
    miss_count BIGINT DEFAULT 0,
    total_requests BIGINT GENERATED ALWAYS AS (hit_count + miss_count) STORED,
    hit_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE WHEN (hit_count + miss_count) = 0 THEN 0
        ELSE ROUND((hit_count * 100.0) / (hit_count + miss_count), 2)
        END
    ) STORED,
    avg_response_time_ms DECIMAL(8,3),
    recorded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    recorded_date DATE GENERATED ALWAYS AS (recorded_at::DATE) STORED
) PARTITION BY RANGE (recorded_date);

-- Create daily partitions for metrics
CREATE TABLE cache_performance_metrics_current PARTITION OF cache_performance_metrics
    FOR VALUES FROM (CURRENT_DATE) TO (CURRENT_DATE + INTERVAL '1 day');

-- Function to record cache metrics
CREATE OR REPLACE FUNCTION record_cache_metric(
    p_metric_name TEXT,
    p_cache_layer TEXT,
    p_operation_type TEXT,
    p_was_hit BOOLEAN,
    p_response_time_ms DECIMAL DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO cache_performance_metrics (
        metric_name, cache_layer, operation_type,
        hit_count, miss_count, avg_response_time_ms
    )
    VALUES (
        p_metric_name, p_cache_layer, p_operation_type,
        CASE WHEN p_was_hit THEN 1 ELSE 0 END,
        CASE WHEN p_was_hit THEN 0 ELSE 1 END,
        p_response_time_ms
    )
    ON CONFLICT (metric_name, cache_layer, operation_type, recorded_date)
    DO UPDATE SET
        hit_count = cache_performance_metrics.hit_count + EXCLUDED.hit_count,
        miss_count = cache_performance_metrics.miss_count + EXCLUDED.miss_count,
        avg_response_time_ms = COALESCE(
            (cache_performance_metrics.avg_response_time_ms + COALESCE(EXCLUDED.avg_response_time_ms, 0)) / 2,
            cache_performance_metrics.avg_response_time_ms
        );
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 7. REDIS CONFIGURATION RECOMMENDATIONS
-- =============================================================================

/*
REDIS CONFIGURATION FOR HIGH PERFORMANCE:

1. MEMORY CONFIGURATION:
   maxmemory 8gb
   maxmemory-policy allkeys-lru
   maxmemory-samples 10

2. PERSISTENCE (for session data):
   save 900 1      # Save if at least 1 key changed in 900 seconds
   save 300 10     # Save if at least 10 keys changed in 300 seconds
   save 60 10000   # Save if at least 10000 keys changed in 60 seconds

3. NETWORKING:
   tcp-keepalive 300
   timeout 0
   tcp-backlog 511

4. PERFORMANCE:
   hz 10
   hash-max-ziplist-entries 512
   hash-max-ziplist-value 64
   list-max-ziplist-size -2
   set-max-intset-entries 512
   zset-max-ziplist-entries 128
   zset-max-ziplist-value 64

5. CLUSTER SETUP (for scaling):
   - 3 master nodes + 3 replica nodes
   - Consistent hashing based on cache key
   - Automatic failover enabled

REDIS PIPELINE COMMANDS EXAMPLE:

# Session validation pipeline
PIPELINE
HGETALL auth:session:{token}
HGETALL auth:user:{user_id}
SMEMBERS auth:permissions:{user_id}
INCR auth:ratelimit:1min:{user_id}
EXPIRE auth:ratelimit:1min:{user_id} 60
EXEC

# User login cache warming pipeline
PIPELINE
HMSET auth:user:{user_id} id {id} username {username} email {email} is_active {is_active}
EXPIRE auth:user:{user_id} 3600
SADD auth:roles:{user_id} {role1} {role2} {role3}
EXPIRE auth:roles:{user_id} 1800
SADD auth:permissions:{user_id} {perm1} {perm2} {perm3}
EXPIRE auth:permissions:{user_id} 1800
EXEC
*/

-- =============================================================================
-- 8. APPLICATION INTEGRATION PSEUDOCODE
-- =============================================================================

/*
APPLICATION LAYER CACHING PATTERN:

// Session validation with multi-layer cache
function validateSession(sessionToken) {
    // Layer 1: Check application memory cache
    if (appCache.has('session:' + sessionToken)) {
        recordCacheMetric('session_validation', 'application', true, 1);
        return appCache.get('session:' + sessionToken);
    }

    // Layer 2: Check Redis cache
    const redisKey = getSessionCacheKey(sessionToken);
    const cachedSession = redis.hgetall(redisKey);

    if (cachedSession && cachedSession.user_id) {
        // Update application cache
        appCache.set('session:' + sessionToken, cachedSession, 60); // 1 minute in app cache
        recordCacheMetric('session_validation', 'redis', true, 3);
        return cachedSession;
    }

    // Layer 3: Database fallback
    const sessionData = await database.query(
        'SELECT prepare_session_cache_data($1)', [sessionToken]
    );

    if (sessionData) {
        // Warm both caches
        redis.hmset(redisKey, sessionData);
        redis.expire(redisKey, 86400); // 24 hours
        appCache.set('session:' + sessionToken, sessionData, 60);
        recordCacheMetric('session_validation', 'database', false, 25);
        return sessionData;
    }

    recordCacheMetric('session_validation', 'database', false, 25);
    return null;
}

// Permission checking with cache
function checkPermission(userId, requiredPermission) {
    // Layer 1: Application cache
    const appCacheKey = 'permissions:' + userId;
    if (appCache.has(appCacheKey)) {
        const permissions = appCache.get(appCacheKey);
        return permissions.includes(requiredPermission);
    }

    // Layer 2: Redis cache
    const redisKey = getUserPermissionsCacheKey(userId);
    const permissions = redis.smembers(redisKey);

    if (permissions.length > 0) {
        appCache.set(appCacheKey, permissions, 300); // 5 minutes
        return permissions.includes(requiredPermission);
    }

    // Layer 3: Database + cache warming
    const userData = await database.query(
        'SELECT prepare_user_cache_data($1)', [userId]
    );

    if (userData) {
        // Warm Redis cache
        redis.sadd(redisKey, ...userData.permissions);
        redis.expire(redisKey, 1800); // 30 minutes

        // Warm application cache
        appCache.set(appCacheKey, userData.permissions, 300);

        return userData.permissions.includes(requiredPermission);
    }

    return false;
}

// Rate limiting with Redis
function checkRateLimit(identifier, windowSeconds, maxRequests) {
    const key = getRateLimitKey(identifier, windowSeconds + 's');
    const pipeline = redis.pipeline();

    pipeline.incr(key);
    pipeline.expire(key, windowSeconds);

    const results = await pipeline.exec();
    const currentCount = results[0][1];

    return currentCount <= maxRequests;
}
*/

-- =============================================================================
-- 9. CACHE MONITORING QUERIES
-- =============================================================================

-- Daily cache performance summary
CREATE OR REPLACE VIEW daily_cache_performance AS
SELECT
    recorded_date,
    cache_layer,
    operation_type,
    SUM(hit_count) as total_hits,
    SUM(miss_count) as total_misses,
    SUM(total_requests) as total_requests,
    ROUND(AVG(hit_rate), 2) as avg_hit_rate,
    ROUND(AVG(avg_response_time_ms), 2) as avg_response_time_ms
FROM cache_performance_metrics
WHERE recorded_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY recorded_date, cache_layer, operation_type
ORDER BY recorded_date DESC, cache_layer, operation_type;

-- Cache efficiency alerts
CREATE OR REPLACE VIEW cache_efficiency_alerts AS
SELECT
    metric_name,
    cache_layer,
    operation_type,
    hit_rate,
    avg_response_time_ms,
    total_requests,
    CASE
        WHEN hit_rate < 90 THEN 'LOW_HIT_RATE'
        WHEN avg_response_time_ms > 50 THEN 'HIGH_LATENCY'
        WHEN total_requests > 100000 AND hit_rate < 95 THEN 'HIGH_VOLUME_LOW_EFFICIENCY'
        ELSE 'OK'
    END as alert_type,
    recorded_at
FROM cache_performance_metrics
WHERE recorded_date = CURRENT_DATE
AND (hit_rate < 90 OR avg_response_time_ms > 50)
ORDER BY hit_rate ASC, avg_response_time_ms DESC;

-- =============================================================================
-- 10. SUMMARY AND RECOMMENDATIONS
-- =============================================================================

/*
REDIS CACHING STRATEGY SUMMARY:

1. MULTI-LAYER ARCHITECTURE:
   - Application Memory: 1ms response, 1-minute TTL
   - Redis Cache: 2-5ms response, optimized TTL per data type
   - Database: 10-50ms response, authoritative source

2. KEY BENEFITS:
   - 99.9% cache hit rate target
   - Sub-10ms average response time
   - Automatic cache warming on login
   - Smart invalidation on data changes

3. CACHE TYPES:
   - Session data: 24-hour TTL, Hash structure
   - User profiles: 1-hour TTL, Hash structure
   - Permissions: 30-minute TTL, Set structure
   - Rate limiting: Variable TTL, Counter
   - Global reference: 24-hour TTL, Hash structure

4. MONITORING:
   - Real-time hit rate tracking
   - Performance metrics per operation
   - Automated alerting on low efficiency

5. SCALING:
   - Redis cluster for horizontal scaling
   - Consistent hashing for even distribution
   - Automatic failover for high availability

6. SECURITY:
   - Rate limiting per user/IP
   - Failed login attempt tracking
   - IP blacklisting with TTL
   - Session invalidation support

EXPECTED PERFORMANCE:
- 1M+ concurrent users supported
- <10ms average API response time
- 99.9% uptime with Redis cluster
- <1% cache miss rate after warm-up
*/

-- Create monitoring functions
SELECT 'Cache strategy configured successfully' as status;

COMMENT ON FUNCTION prepare_user_cache_data IS 'Generates complete user cache data for Redis storage';
COMMENT ON FUNCTION prepare_session_cache_data IS 'Generates session cache data for Redis storage';
COMMENT ON FUNCTION generate_cache_invalidation_commands IS 'Creates Redis commands to invalidate relevant caches';
COMMENT ON VIEW daily_cache_performance IS 'Daily summary of cache performance metrics';
COMMENT ON VIEW cache_efficiency_alerts IS 'Alerts for cache performance issues';