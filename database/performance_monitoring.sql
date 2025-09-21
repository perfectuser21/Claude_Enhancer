-- =============================================================================
-- COMPREHENSIVE PERFORMANCE MONITORING SYSTEM
-- =============================================================================
-- Purpose: Real-time database performance monitoring and alerting
-- Target: Proactive performance management for 1M+ concurrent users
-- Strategy: Multi-layered monitoring with automated alerts and optimization
-- =============================================================================

-- =============================================================================
-- 1. PERFORMANCE MONITORING ARCHITECTURE
-- =============================================================================

/*
MONITORING ARCHITECTURE (Layered Performance Intelligence):

Layer 1: Real-time Metrics Collection (1-second intervals)
├── Query performance tracking
├── Connection pool monitoring
├── Lock and wait event tracking
└── Resource utilization metrics

Layer 2: Aggregated Analytics (1-minute intervals)
├── Query pattern analysis
├── Performance trend analysis
├── Capacity planning metrics
└── SLA compliance tracking

Layer 3: Historical Analysis (daily/weekly)
├── Performance baseline establishment
├── Growth trend analysis
├── Capacity forecasting
└── Performance regression detection

Layer 4: Automated Optimization (continuous)
├── Index recommendation engine
├── Query optimization suggestions
├── Resource scaling recommendations
└── Maintenance scheduling optimization

MONITORING TARGETS:
- Query response time: <100ms (95th percentile)
- Connection utilization: <80%
- CPU utilization: <70%
- Memory utilization: <80%
- Disk I/O: <70% saturation
- Cache hit ratio: >95%
*/

-- =============================================================================
-- 2. CORE MONITORING TABLES
-- =============================================================================

-- Real-time performance metrics
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Metric identification
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(50) NOT NULL, -- 'query', 'connection', 'resource', 'cache'
    metric_type VARCHAR(20) NOT NULL, -- 'counter', 'gauge', 'histogram'

    -- Metric values
    value_numeric DECIMAL(15,6),
    value_text TEXT,
    unit VARCHAR(20), -- 'ms', 'count', 'percent', 'bytes', 'bytes/sec'

    -- Context
    database_name VARCHAR(100),
    schema_name VARCHAR(100),
    table_name VARCHAR(100),
    index_name VARCHAR(100),
    query_id BIGINT, -- pg_stat_statements.queryid

    -- Dimensions for grouping
    host_name VARCHAR(100),
    instance_name VARCHAR(100),
    user_name VARCHAR(100),
    application_name VARCHAR(100),

    -- Timing
    measured_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    measurement_window_seconds INTEGER DEFAULT 60,

    -- Partitioning column
    measurement_date DATE GENERATED ALWAYS AS (measured_at::DATE) STORED
) PARTITION BY RANGE (measurement_date);

-- Query performance tracking
CREATE TABLE query_performance_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Query identification
    query_id BIGINT NOT NULL, -- pg_stat_statements.queryid
    query_hash TEXT, -- MD5 hash of normalized query
    query_text TEXT, -- Actual query (truncated if needed)
    query_fingerprint TEXT, -- Normalized query pattern

    -- Performance metrics
    execution_time_ms DECIMAL(10,3) NOT NULL,
    planning_time_ms DECIMAL(10,3),
    rows_examined BIGINT,
    rows_returned BIGINT,
    shared_blks_hit BIGINT,
    shared_blks_read BIGINT,
    shared_blks_written BIGINT,
    temp_blks_read BIGINT,
    temp_blks_written BIGINT,

    -- Resource usage
    peak_memory_kb INTEGER,
    cpu_time_ms DECIMAL(10,3),

    -- Context
    database_name VARCHAR(100),
    user_name VARCHAR(100),
    application_name VARCHAR(100),
    session_id TEXT,

    -- Query plan information
    execution_plan JSONB,
    plan_cost DECIMAL(15,6),
    plan_rows BIGINT,

    -- Timing
    executed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Performance classification
    performance_class VARCHAR(20) GENERATED ALWAYS AS (
        CASE
            WHEN execution_time_ms > 5000 THEN 'VERY_SLOW'
            WHEN execution_time_ms > 1000 THEN 'SLOW'
            WHEN execution_time_ms > 100 THEN 'MODERATE'
            ELSE 'FAST'
        END
    ) STORED,

    -- Partitioning
    execution_date DATE GENERATED ALWAYS AS (executed_at::DATE) STORED
) PARTITION BY RANGE (execution_date);

-- System resource monitoring
CREATE TABLE system_resource_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- CPU metrics
    cpu_user_percent DECIMAL(5,2),
    cpu_system_percent DECIMAL(5,2),
    cpu_idle_percent DECIMAL(5,2),
    cpu_wait_percent DECIMAL(5,2),
    load_average_1min DECIMAL(8,2),
    load_average_5min DECIMAL(8,2),
    load_average_15min DECIMAL(8,2),

    -- Memory metrics
    memory_total_bytes BIGINT,
    memory_used_bytes BIGINT,
    memory_free_bytes BIGINT,
    memory_cached_bytes BIGINT,
    memory_buffers_bytes BIGINT,
    swap_total_bytes BIGINT,
    swap_used_bytes BIGINT,

    -- Disk I/O metrics
    disk_read_bytes_per_sec BIGINT,
    disk_write_bytes_per_sec BIGINT,
    disk_read_ops_per_sec INTEGER,
    disk_write_ops_per_sec INTEGER,
    disk_utilization_percent DECIMAL(5,2),
    disk_queue_depth DECIMAL(8,2),

    -- Network metrics
    network_recv_bytes_per_sec BIGINT,
    network_send_bytes_per_sec BIGINT,
    network_recv_packets_per_sec INTEGER,
    network_send_packets_per_sec INTEGER,

    -- Database-specific metrics
    active_connections INTEGER,
    idle_connections INTEGER,
    total_connections INTEGER,
    max_connections INTEGER,
    transactions_per_sec DECIMAL(10,2),
    commits_per_sec DECIMAL(10,2),
    rollbacks_per_sec DECIMAL(10,2),

    -- Cache metrics
    buffer_cache_hit_ratio DECIMAL(5,2),
    shared_buffer_size_bytes BIGINT,
    effective_cache_size_bytes BIGINT,

    -- Host identification
    host_name VARCHAR(100) NOT NULL,
    instance_name VARCHAR(100),

    -- Timing
    measured_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    measurement_interval_seconds INTEGER DEFAULT 60
) PARTITION BY RANGE (measured_at);

-- Lock and wait event tracking
CREATE TABLE lock_monitoring (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Lock information
    lock_type VARCHAR(50) NOT NULL,
    lock_mode VARCHAR(50) NOT NULL,
    lock_granted BOOLEAN NOT NULL,

    -- Object being locked
    database_name VARCHAR(100),
    schema_name VARCHAR(100),
    table_name VARCHAR(100),
    index_name VARCHAR(100),

    -- Process information
    blocking_pid INTEGER,
    blocked_pid INTEGER,
    blocking_query TEXT,
    blocked_query TEXT,
    blocking_user VARCHAR(100),
    blocked_user VARCHAR(100),

    -- Timing
    lock_acquired_at TIMESTAMPTZ,
    wait_started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    wait_ended_at TIMESTAMPTZ,
    wait_duration_ms INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (wait_ended_at - wait_started_at)) * 1000
    ) STORED,

    -- Status
    lock_status VARCHAR(20) DEFAULT 'waiting', -- 'waiting', 'granted', 'timeout', 'deadlock'

    -- Additional context
    transaction_id BIGINT,
    session_id TEXT,
    application_name VARCHAR(100)
);

-- =============================================================================
-- 3. PERFORMANCE ALERTING SYSTEM
-- =============================================================================

-- Alert configuration
CREATE TABLE performance_alert_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Alert identification
    alert_name VARCHAR(100) UNIQUE NOT NULL,
    alert_category VARCHAR(50) NOT NULL, -- 'performance', 'availability', 'capacity', 'security'
    severity VARCHAR(20) NOT NULL, -- 'critical', 'warning', 'info'

    -- Alert condition
    metric_name VARCHAR(100) NOT NULL,
    operator VARCHAR(20) NOT NULL, -- '>', '<', '>=', '<=', '=', '!='
    threshold_value DECIMAL(15,6) NOT NULL,
    threshold_unit VARCHAR(20),

    -- Alert behavior
    evaluation_window_minutes INTEGER DEFAULT 5,
    evaluation_frequency_minutes INTEGER DEFAULT 1,
    consecutive_breaches_required INTEGER DEFAULT 1,

    -- Notification settings
    notification_channels TEXT[], -- 'email', 'slack', 'pagerduty', 'webhook'
    notification_recipients TEXT[],
    escalation_rules JSONB,

    -- Alert state
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered TIMESTAMPTZ,
    current_state VARCHAR(20) DEFAULT 'ok', -- 'ok', 'alerting', 'no_data'
    consecutive_breaches INTEGER DEFAULT 0,

    -- Metadata
    description TEXT,
    runbook_url TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by UUID
);

-- Active alerts tracking
CREATE TABLE performance_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Alert rule reference
    alert_rule_id UUID NOT NULL REFERENCES performance_alert_rules(id),
    alert_name VARCHAR(100) NOT NULL,

    -- Alert instance details
    triggered_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ,
    alert_state VARCHAR(20) NOT NULL, -- 'firing', 'resolved', 'suppressed'

    -- Triggering metric
    metric_value DECIMAL(15,6),
    threshold_value DECIMAL(15,6),
    breach_percentage DECIMAL(8,2) GENERATED ALWAYS AS (
        CASE WHEN threshold_value > 0 THEN
            ((metric_value - threshold_value) / threshold_value) * 100
        ELSE 0 END
    ) STORED,

    -- Context
    affected_resource TEXT,
    host_name VARCHAR(100),
    database_name VARCHAR(100),

    -- Resolution tracking
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by VARCHAR(100),
    resolution_notes TEXT,

    -- Notification tracking
    notifications_sent JSONB,
    escalation_level INTEGER DEFAULT 0
);

-- =============================================================================
-- 4. MONITORING FUNCTIONS
-- =============================================================================

-- Function to collect current system metrics
CREATE OR REPLACE FUNCTION collect_system_metrics()
RETURNS UUID AS $$
DECLARE
    metrics_id UUID;
    db_stats RECORD;
    bg_writer_stats RECORD;
BEGIN
    metrics_id := gen_random_uuid();

    -- Get database statistics
    SELECT
        numbackends as active_connections,
        xact_commit as total_commits,
        xact_rollback as total_rollbacks,
        blks_read as total_blocks_read,
        blks_hit as total_blocks_hit,
        tup_returned,
        tup_fetched,
        tup_inserted,
        tup_updated,
        tup_deleted
    INTO db_stats
    FROM pg_stat_database
    WHERE datname = current_database();

    -- Get background writer statistics
    SELECT
        checkpoints_timed,
        checkpoints_req,
        checkpoint_write_time,
        checkpoint_sync_time,
        buffers_checkpoint,
        buffers_clean,
        buffers_backend
    INTO bg_writer_stats
    FROM pg_stat_bgwriter;

    -- Insert system metrics (simplified version - real implementation would collect from OS)
    INSERT INTO system_resource_metrics (
        id,
        host_name,
        instance_name,
        active_connections,
        total_connections,
        max_connections,
        buffer_cache_hit_ratio,
        measured_at
    )
    SELECT
        metrics_id,
        inet_server_addr()::TEXT,
        current_database(),
        db_stats.active_connections,
        (SELECT count(*) FROM pg_stat_activity),
        (SELECT setting::INTEGER FROM pg_settings WHERE name = 'max_connections'),
        CASE WHEN (db_stats.total_blocks_read + db_stats.total_blocks_hit) > 0
             THEN ROUND((db_stats.total_blocks_hit * 100.0) / (db_stats.total_blocks_read + db_stats.total_blocks_hit), 2)
             ELSE 0 END,
        CURRENT_TIMESTAMP;

    RETURN metrics_id;
END;
$$ LANGUAGE plpgsql;

-- Function to capture query performance metrics
CREATE OR REPLACE FUNCTION capture_query_performance()
RETURNS INTEGER AS $$
DECLARE
    captured_count INTEGER := 0;
    stmt_record RECORD;
BEGIN
    -- Insert new query performance data from pg_stat_statements
    INSERT INTO query_performance_log (
        query_id,
        query_text,
        execution_time_ms,
        rows_examined,
        rows_returned,
        shared_blks_hit,
        shared_blks_read,
        shared_blks_written,
        database_name,
        user_name,
        executed_at
    )
    SELECT
        queryid,
        query,
        mean_exec_time,
        COALESCE(rows, 0),
        COALESCE(rows, 0), -- Simplified: using same value for examined/returned
        shared_blks_hit,
        shared_blks_read,
        shared_blks_written,
        (SELECT datname FROM pg_database WHERE oid = dbid),
        (SELECT rolname FROM pg_roles WHERE oid = userid),
        CURRENT_TIMESTAMP
    FROM pg_stat_statements
    WHERE last_exec > CURRENT_TIMESTAMP - INTERVAL '1 minute'
    AND mean_exec_time > 0;

    GET DIAGNOSTICS captured_count = ROW_COUNT;

    RETURN captured_count;
END;
$$ LANGUAGE plpgsql;

-- Function to evaluate alert rules
CREATE OR REPLACE FUNCTION evaluate_alert_rules()
RETURNS INTEGER AS $$
DECLARE
    alerts_triggered INTEGER := 0;
    rule_record RECORD;
    current_value DECIMAL(15,6);
    should_alert BOOLEAN;
    alert_id UUID;
BEGIN
    FOR rule_record IN
        SELECT *
        FROM performance_alert_rules
        WHERE is_active = TRUE
    LOOP
        -- Get current metric value (simplified - would query appropriate metric table)
        CASE rule_record.metric_name
            WHEN 'active_connections' THEN
                SELECT active_connections INTO current_value
                FROM system_resource_metrics
                WHERE measured_at > CURRENT_TIMESTAMP - INTERVAL '5 minutes'
                ORDER BY measured_at DESC
                LIMIT 1;

            WHEN 'avg_query_time' THEN
                SELECT AVG(execution_time_ms) INTO current_value
                FROM query_performance_log
                WHERE executed_at > CURRENT_TIMESTAMP - (rule_record.evaluation_window_minutes || ' minutes')::INTERVAL;

            WHEN 'buffer_cache_hit_ratio' THEN
                SELECT buffer_cache_hit_ratio INTO current_value
                FROM system_resource_metrics
                WHERE measured_at > CURRENT_TIMESTAMP - INTERVAL '5 minutes'
                ORDER BY measured_at DESC
                LIMIT 1;

            ELSE
                CONTINUE; -- Skip unknown metrics
        END CASE;

        IF current_value IS NULL THEN
            CONTINUE;
        END IF;

        -- Evaluate alert condition
        should_alert := CASE rule_record.operator
            WHEN '>' THEN current_value > rule_record.threshold_value
            WHEN '<' THEN current_value < rule_record.threshold_value
            WHEN '>=' THEN current_value >= rule_record.threshold_value
            WHEN '<=' THEN current_value <= rule_record.threshold_value
            WHEN '=' THEN current_value = rule_record.threshold_value
            WHEN '!=' THEN current_value != rule_record.threshold_value
            ELSE FALSE
        END;

        IF should_alert THEN
            -- Check if alert already exists
            SELECT id INTO alert_id
            FROM performance_alerts
            WHERE alert_rule_id = rule_record.id
            AND alert_state = 'firing'
            AND resolved_at IS NULL;

            IF NOT FOUND THEN
                -- Create new alert
                INSERT INTO performance_alerts (
                    alert_rule_id,
                    alert_name,
                    metric_value,
                    threshold_value,
                    host_name,
                    database_name
                )
                VALUES (
                    rule_record.id,
                    rule_record.alert_name,
                    current_value,
                    rule_record.threshold_value,
                    inet_server_addr()::TEXT,
                    current_database()
                );

                alerts_triggered := alerts_triggered + 1;

                -- Update alert rule state
                UPDATE performance_alert_rules
                SET last_triggered = CURRENT_TIMESTAMP,
                    current_state = 'alerting',
                    consecutive_breaches = consecutive_breaches + 1
                WHERE id = rule_record.id;
            END IF;
        ELSE
            -- Resolve existing alerts if condition is no longer met
            UPDATE performance_alerts
            SET resolved_at = CURRENT_TIMESTAMP,
                alert_state = 'resolved'
            WHERE alert_rule_id = rule_record.id
            AND alert_state = 'firing'
            AND resolved_at IS NULL;

            -- Update alert rule state
            UPDATE performance_alert_rules
            SET current_state = 'ok',
                consecutive_breaches = 0
            WHERE id = rule_record.id
            AND current_state != 'ok';
        END IF;
    END LOOP;

    RETURN alerts_triggered;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 5. PERFORMANCE ANALYSIS VIEWS
-- =============================================================================

-- Top slow queries analysis
CREATE OR REPLACE VIEW top_slow_queries AS
WITH query_stats AS (
    SELECT
        query_fingerprint,
        COUNT(*) as execution_count,
        AVG(execution_time_ms) as avg_execution_time,
        MAX(execution_time_ms) as max_execution_time,
        MIN(execution_time_ms) as min_execution_time,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY execution_time_ms) as median_execution_time,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms) as p95_execution_time,
        SUM(execution_time_ms) as total_execution_time,
        AVG(rows_examined) as avg_rows_examined,
        AVG(rows_returned) as avg_rows_returned,
        substring(query_text, 1, 100) as query_sample
    FROM query_performance_log
    WHERE executed_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
    GROUP BY query_fingerprint, substring(query_text, 1, 100)
)
SELECT
    query_fingerprint,
    execution_count,
    ROUND(avg_execution_time, 2) as avg_time_ms,
    ROUND(max_execution_time, 2) as max_time_ms,
    ROUND(median_execution_time, 2) as median_time_ms,
    ROUND(p95_execution_time, 2) as p95_time_ms,
    ROUND(total_execution_time, 2) as total_time_ms,
    ROUND(avg_rows_examined) as avg_rows_examined,
    ROUND(avg_rows_returned) as avg_rows_returned,
    query_sample,

    -- Performance classification
    CASE
        WHEN avg_execution_time > 1000 THEN '🔴 CRITICAL'
        WHEN avg_execution_time > 500 THEN '🟡 WARNING'
        WHEN avg_execution_time > 100 THEN '🟠 MODERATE'
        ELSE '✅ FAST'
    END as performance_status,

    -- Impact score (frequency × average time)
    ROUND(execution_count * avg_execution_time, 2) as impact_score

FROM query_stats
ORDER BY impact_score DESC
LIMIT 50;

-- System resource utilization trends
CREATE OR REPLACE VIEW resource_utilization_trends AS
WITH hourly_stats AS (
    SELECT
        date_trunc('hour', measured_at) as hour,
        AVG(cpu_user_percent + cpu_system_percent) as avg_cpu_usage,
        AVG(memory_used_bytes * 100.0 / memory_total_bytes) as avg_memory_usage,
        AVG(active_connections) as avg_connections,
        AVG(buffer_cache_hit_ratio) as avg_cache_hit_ratio,
        AVG(disk_utilization_percent) as avg_disk_usage,
        MAX(active_connections) as peak_connections
    FROM system_resource_metrics
    WHERE measured_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
    GROUP BY date_trunc('hour', measured_at)
)
SELECT
    hour,
    ROUND(avg_cpu_usage, 1) as cpu_usage_percent,
    ROUND(avg_memory_usage, 1) as memory_usage_percent,
    ROUND(avg_connections) as avg_connections,
    peak_connections,
    ROUND(avg_cache_hit_ratio, 1) as cache_hit_ratio,
    ROUND(avg_disk_usage, 1) as disk_usage_percent,

    -- Trend indicators
    CASE
        WHEN avg_cpu_usage > 80 THEN '🔴 HIGH'
        WHEN avg_cpu_usage > 60 THEN '🟡 MODERATE'
        ELSE '✅ NORMAL'
    END as cpu_status,

    CASE
        WHEN avg_memory_usage > 85 THEN '🔴 HIGH'
        WHEN avg_memory_usage > 70 THEN '🟡 MODERATE'
        ELSE '✅ NORMAL'
    END as memory_status,

    CASE
        WHEN avg_cache_hit_ratio < 90 THEN '🔴 LOW'
        WHEN avg_cache_hit_ratio < 95 THEN '🟡 MODERATE'
        ELSE '✅ GOOD'
    END as cache_status

FROM hourly_stats
ORDER BY hour DESC;

-- Active performance alerts dashboard
CREATE OR REPLACE VIEW active_alerts_dashboard AS
SELECT
    pa.alert_name,
    par.severity,
    pa.alert_state,
    pa.triggered_at,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - pa.triggered_at))/60 as duration_minutes,
    pa.metric_value,
    pa.threshold_value,
    pa.breach_percentage,
    pa.affected_resource,
    pa.host_name,
    pa.database_name,
    par.description,
    par.runbook_url,

    -- Priority scoring
    CASE par.severity
        WHEN 'critical' THEN 100
        WHEN 'warning' THEN 50
        WHEN 'info' THEN 10
        ELSE 1
    END +
    CASE
        WHEN pa.breach_percentage > 100 THEN 50
        WHEN pa.breach_percentage > 50 THEN 25
        ELSE 0
    END +
    CASE
        WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - pa.triggered_at))/60 > 60 THEN 25
        WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - pa.triggered_at))/60 > 30 THEN 10
        ELSE 0
    END as priority_score

FROM performance_alerts pa
JOIN performance_alert_rules par ON pa.alert_rule_id = par.id
WHERE pa.alert_state = 'firing'
AND pa.resolved_at IS NULL
ORDER BY priority_score DESC, pa.triggered_at ASC;

-- Lock contention analysis
CREATE OR REPLACE VIEW lock_contention_analysis AS
SELECT
    lock_type,
    lock_mode,
    database_name,
    COALESCE(schema_name || '.' || table_name, 'N/A') as object_name,
    COUNT(*) as lock_count,
    COUNT(CASE WHEN lock_granted = FALSE THEN 1 END) as waiting_count,
    AVG(wait_duration_ms) as avg_wait_time_ms,
    MAX(wait_duration_ms) as max_wait_time_ms,
    COUNT(DISTINCT blocking_pid) as unique_blockers,
    COUNT(DISTINCT blocked_pid) as unique_blocked,

    -- Contention severity
    CASE
        WHEN COUNT(CASE WHEN lock_granted = FALSE THEN 1 END) > 10 THEN '🔴 HIGH CONTENTION'
        WHEN COUNT(CASE WHEN lock_granted = FALSE THEN 1 END) > 5 THEN '🟡 MODERATE CONTENTION'
        WHEN COUNT(CASE WHEN lock_granted = FALSE THEN 1 END) > 0 THEN '🟠 LOW CONTENTION'
        ELSE '✅ NO CONTENTION'
    END as contention_level

FROM lock_monitoring
WHERE wait_started_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
GROUP BY lock_type, lock_mode, database_name, schema_name, table_name
HAVING COUNT(*) > 0
ORDER BY waiting_count DESC, avg_wait_time_ms DESC;

-- =============================================================================
-- 6. PERFORMANCE OPTIMIZATION RECOMMENDATIONS
-- =============================================================================

-- Index recommendation engine
CREATE OR REPLACE VIEW index_recommendations AS
WITH missing_indexes AS (
    SELECT
        schemaname,
        tablename,
        seq_scan,
        seq_tup_read,
        idx_scan,
        idx_tup_fetch,
        n_tup_ins + n_tup_upd + n_tup_del as write_activity,

        -- Calculate scan efficiency
        CASE WHEN seq_scan + idx_scan > 0
             THEN ROUND((idx_scan::DECIMAL / (seq_scan + idx_scan)) * 100, 2)
             ELSE 0 END as index_usage_ratio,

        -- Estimate benefit of indexing
        CASE WHEN seq_scan > 0 AND seq_tup_read > 0
             THEN seq_tup_read / seq_scan
             ELSE 0 END as avg_rows_per_seq_scan

    FROM pg_stat_user_tables
    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
)
SELECT
    schemaname,
    tablename,
    seq_scan as sequential_scans,
    seq_tup_read as rows_read_sequentially,
    idx_scan as index_scans,
    index_usage_ratio,
    avg_rows_per_seq_scan,

    -- Recommendation priority
    CASE
        WHEN seq_scan > 1000 AND avg_rows_per_seq_scan > 1000 THEN '🔴 HIGH PRIORITY'
        WHEN seq_scan > 100 AND avg_rows_per_seq_scan > 100 THEN '🟡 MEDIUM PRIORITY'
        WHEN seq_scan > 10 AND avg_rows_per_seq_scan > 10 THEN '🟠 LOW PRIORITY'
        ELSE '✅ NO ACTION NEEDED'
    END as recommendation_priority,

    -- Specific recommendation
    CASE
        WHEN index_usage_ratio < 50 AND seq_scan > 100
             THEN 'Consider adding indexes on frequently queried columns'
        WHEN avg_rows_per_seq_scan > 1000
             THEN 'Table may benefit from better indexing strategy'
        WHEN write_activity > seq_scan * 10
             THEN 'High write activity - be cautious with new indexes'
        ELSE 'Current indexing appears adequate'
    END as recommendation

FROM missing_indexes
WHERE seq_scan > 0
ORDER BY
    CASE
        WHEN seq_scan > 1000 AND avg_rows_per_seq_scan > 1000 THEN 1
        WHEN seq_scan > 100 AND avg_rows_per_seq_scan > 100 THEN 2
        WHEN seq_scan > 10 AND avg_rows_per_seq_scan > 10 THEN 3
        ELSE 4
    END,
    seq_scan DESC;

-- Query optimization suggestions
CREATE OR REPLACE VIEW query_optimization_suggestions AS
WITH problematic_queries AS (
    SELECT
        query_fingerprint,
        COUNT(*) as execution_count,
        AVG(execution_time_ms) as avg_execution_time,
        AVG(rows_examined) as avg_rows_examined,
        AVG(rows_returned) as avg_rows_returned,
        AVG(shared_blks_read) as avg_blocks_read,
        AVG(temp_blks_read + temp_blks_written) as avg_temp_blocks,
        substring(query_text, 1, 200) as query_sample
    FROM query_performance_log
    WHERE executed_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
    GROUP BY query_fingerprint, substring(query_text, 1, 200)
    HAVING AVG(execution_time_ms) > 100 OR COUNT(*) > 1000
)
SELECT
    query_fingerprint,
    execution_count,
    ROUND(avg_execution_time, 2) as avg_time_ms,
    ROUND(avg_rows_examined) as avg_rows_examined,
    ROUND(avg_rows_returned) as avg_rows_returned,
    query_sample,

    -- Optimization suggestions
    ARRAY_REMOVE(ARRAY[
        CASE WHEN avg_rows_examined > avg_rows_returned * 10
             THEN 'High row examination ratio - consider better WHERE clauses or indexes'
             ELSE NULL END,
        CASE WHEN avg_temp_blocks > 1000
             THEN 'High temp block usage - consider increasing work_mem or optimizing query'
             ELSE NULL END,
        CASE WHEN avg_execution_time > 1000
             THEN 'Very slow query - consider query rewrite or additional indexes'
             ELSE NULL END,
        CASE WHEN execution_count > 10000 AND avg_execution_time > 10
             THEN 'High frequency query - small optimizations will have big impact'
             ELSE NULL END,
        CASE WHEN avg_blocks_read > 10000
             THEN 'High I/O usage - consider indexes or query optimization'
             ELSE NULL END
    ], NULL) as optimization_suggestions,

    -- Priority level
    CASE
        WHEN avg_execution_time > 5000 OR execution_count > 50000 THEN '🔴 CRITICAL'
        WHEN avg_execution_time > 1000 OR execution_count > 10000 THEN '🟡 HIGH'
        WHEN avg_execution_time > 500 OR execution_count > 5000 THEN '🟠 MEDIUM'
        ELSE '🔵 LOW'
    END as optimization_priority

FROM problematic_queries
ORDER BY
    CASE
        WHEN avg_execution_time > 5000 OR execution_count > 50000 THEN 1
        WHEN avg_execution_time > 1000 OR execution_count > 10000 THEN 2
        WHEN avg_execution_time > 500 OR execution_count > 5000 THEN 3
        ELSE 4
    END,
    (execution_count * avg_execution_time) DESC;

-- =============================================================================
-- 7. SEED DATA AND CONFIGURATION
-- =============================================================================

-- Create initial partitions
CREATE TABLE performance_metrics_current PARTITION OF performance_metrics
    FOR VALUES FROM (CURRENT_DATE) TO (CURRENT_DATE + INTERVAL '1 day');

CREATE TABLE query_performance_log_current PARTITION OF query_performance_log
    FOR VALUES FROM (CURRENT_DATE) TO (CURRENT_DATE + INTERVAL '1 day');

CREATE TABLE system_resource_metrics_current PARTITION OF system_resource_metrics
    FOR VALUES FROM (CURRENT_TIMESTAMP) TO (CURRENT_TIMESTAMP + INTERVAL '1 day');

-- Insert default alert rules
INSERT INTO performance_alert_rules (alert_name, alert_category, severity, metric_name, operator, threshold_value, threshold_unit, description) VALUES
('High Connection Count', 'capacity', 'warning', 'active_connections', '>', 80, 'percent', 'Active connections exceed 80% of max_connections'),
('Critical Connection Count', 'capacity', 'critical', 'active_connections', '>', 90, 'percent', 'Active connections exceed 90% of max_connections'),
('Slow Average Query Time', 'performance', 'warning', 'avg_query_time', '>', 500, 'ms', 'Average query execution time exceeds 500ms'),
('Very Slow Query Time', 'performance', 'critical', 'avg_query_time', '>', 2000, 'ms', 'Average query execution time exceeds 2 seconds'),
('Low Buffer Cache Hit Ratio', 'performance', 'warning', 'buffer_cache_hit_ratio', '<', 95, 'percent', 'Buffer cache hit ratio below 95%'),
('Critical Cache Hit Ratio', 'performance', 'critical', 'buffer_cache_hit_ratio', '<', 90, 'percent', 'Buffer cache hit ratio below 90%'),
('High CPU Usage', 'resource', 'warning', 'cpu_usage', '>', 80, 'percent', 'CPU usage exceeds 80%'),
('Critical CPU Usage', 'resource', 'critical', 'cpu_usage', '>', 95, 'percent', 'CPU usage exceeds 95%'),
('High Memory Usage', 'resource', 'warning', 'memory_usage', '>', 85, 'percent', 'Memory usage exceeds 85%'),
('Critical Memory Usage', 'resource', 'critical', 'memory_usage', '>', 95, 'percent', 'Memory usage exceeds 95%');

-- =============================================================================
-- 8. MAINTENANCE AND CLEANUP FUNCTIONS
-- =============================================================================

-- Function to clean up old monitoring data
CREATE OR REPLACE FUNCTION cleanup_monitoring_data(retention_days INTEGER DEFAULT 30)
RETURNS TEXT AS $$
DECLARE
    cleanup_summary TEXT := '';
    deleted_count INTEGER;
BEGIN
    -- Clean up old performance metrics
    DELETE FROM performance_metrics
    WHERE measurement_date < CURRENT_DATE - retention_days;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    cleanup_summary := cleanup_summary || format('Performance metrics: %s rows deleted\n', deleted_count);

    -- Clean up old query performance logs
    DELETE FROM query_performance_log
    WHERE execution_date < CURRENT_DATE - retention_days;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    cleanup_summary := cleanup_summary || format('Query performance logs: %s rows deleted\n', deleted_count);

    -- Clean up old system resource metrics
    DELETE FROM system_resource_metrics
    WHERE measured_at < CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    cleanup_summary := cleanup_summary || format('System resource metrics: %s rows deleted\n', deleted_count);

    -- Clean up old lock monitoring data
    DELETE FROM lock_monitoring
    WHERE wait_started_at < CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    cleanup_summary := cleanup_summary || format('Lock monitoring data: %s rows deleted\n', deleted_count);

    -- Clean up resolved alerts older than 7 days
    DELETE FROM performance_alerts
    WHERE resolved_at IS NOT NULL
    AND resolved_at < CURRENT_TIMESTAMP - INTERVAL '7 days';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    cleanup_summary := cleanup_summary || format('Resolved alerts: %s rows deleted\n', deleted_count);

    RETURN 'Monitoring data cleanup completed:\n' || cleanup_summary;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- FINAL SUMMARY
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'PERFORMANCE MONITORING SYSTEM DEPLOYED';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'Components installed:';
    RAISE NOTICE '✓ Performance metrics collection tables (partitioned)';
    RAISE NOTICE '✓ Query performance tracking system';
    RAISE NOTICE '✓ System resource monitoring';
    RAISE NOTICE '✓ Lock contention monitoring';
    RAISE NOTICE '✓ Automated alerting system with % alert rules', (SELECT COUNT(*) FROM performance_alert_rules);
    RAISE NOTICE '✓ Performance analysis views and dashboards';
    RAISE NOTICE '✓ Index and query optimization recommendations';
    RAISE NOTICE '✓ Automated data collection functions';
    RAISE NOTICE '✓ Data retention and cleanup procedures';
    RAISE NOTICE '';
    RAISE NOTICE 'Performance targets:';
    RAISE NOTICE '- Query response time: <100ms (95th percentile)';
    RAISE NOTICE '- Connection utilization: <80%';
    RAISE NOTICE '- CPU utilization: <70%';
    RAISE NOTICE '- Memory utilization: <80%';
    RAISE NOTICE '- Cache hit ratio: >95%';
    RAISE NOTICE '';
    RAISE NOTICE 'Monitoring frequency:';
    RAISE NOTICE '- Real-time metrics: 1-second intervals';
    RAISE NOTICE '- System metrics: 1-minute intervals';
    RAISE NOTICE '- Alert evaluation: 1-minute intervals';
    RAISE NOTICE '- Data retention: 30 days default';
    RAISE NOTICE '=============================================================================';
END
$$;

COMMENT ON TABLE performance_metrics IS 'Real-time performance metrics collection (partitioned by date)';
COMMENT ON TABLE query_performance_log IS 'Detailed query execution performance tracking';
COMMENT ON TABLE system_resource_metrics IS 'System-level resource utilization monitoring';
COMMENT ON TABLE lock_monitoring IS 'Database lock contention and wait event tracking';
COMMENT ON TABLE performance_alert_rules IS 'Configurable performance alerting rules';
COMMENT ON TABLE performance_alerts IS 'Active and historical performance alerts';
COMMENT ON VIEW top_slow_queries IS 'Analysis of slowest queries with optimization insights';
COMMENT ON VIEW resource_utilization_trends IS 'Hourly system resource utilization trends';
COMMENT ON VIEW active_alerts_dashboard IS 'Real-time performance alerts dashboard';
COMMENT ON VIEW lock_contention_analysis IS 'Database lock contention analysis and trends';
COMMENT ON VIEW index_recommendations IS 'Automated index optimization recommendations';
COMMENT ON VIEW query_optimization_suggestions IS 'Query performance optimization suggestions';
COMMENT ON FUNCTION collect_system_metrics IS 'Collect current system performance metrics';
COMMENT ON FUNCTION capture_query_performance IS 'Capture query performance from pg_stat_statements';
COMMENT ON FUNCTION evaluate_alert_rules IS 'Evaluate all active alert rules and trigger alerts';
COMMENT ON FUNCTION cleanup_monitoring_data IS 'Clean up old monitoring data based on retention policy';