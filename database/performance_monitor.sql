-- =====================================================
-- 用户认证系统数据库性能监控脚本
-- 用途：实时监控数据库性能，识别潜在问题
-- =====================================================

-- 创建监控专用schema
CREATE SCHEMA IF NOT EXISTS monitoring;

-- =====================================================
-- 1. 性能监控视图
-- =====================================================

-- 实时查询性能监控
CREATE OR REPLACE VIEW monitoring.query_performance AS
SELECT
    query,
    calls,
    total_time,
    round(mean_time::numeric, 2) as avg_time_ms,
    round(stddev_time::numeric, 2) as stddev_time_ms,
    rows,
    round(100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0), 2) AS cache_hit_percent,
    round((total_time / sum(total_time) OVER()) * 100, 2) AS time_percent
FROM pg_stat_statements
WHERE query LIKE '%auth.%'
  AND calls > 10  -- 只显示执行次数超过10次的查询
ORDER BY total_time DESC;

-- 表级性能统计
CREATE OR REPLACE VIEW monitoring.table_performance AS
SELECT
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_tup_hot_upd as hot_updates,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    round(100.0 * n_dead_tup / nullif(n_live_tup + n_dead_tup, 0), 2) as dead_tuple_percent,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze,
    vacuum_count,
    autovacuum_count,
    analyze_count,
    autoanalyze_count
FROM pg_stat_user_tables
WHERE schemaname = 'auth'
ORDER BY n_live_tup DESC;

-- 索引性能监控
CREATE OR REPLACE VIEW monitoring.index_performance AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    CASE
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 100 THEN 'LOW'
        WHEN idx_scan < 1000 THEN 'MEDIUM'
        ELSE 'HIGH'
    END as usage_level,
    CASE
        WHEN idx_tup_read = 0 THEN 0
        ELSE round((idx_tup_fetch::numeric / idx_tup_read) * 100, 2)
    END as selectivity_percent
FROM pg_stat_user_indexes
WHERE schemaname = 'auth'
ORDER BY idx_scan DESC;

-- 连接和锁监控
CREATE OR REPLACE VIEW monitoring.connection_locks AS
SELECT
    pg_stat_activity.pid,
    pg_stat_activity.usename,
    pg_stat_activity.application_name,
    pg_stat_activity.client_addr,
    pg_stat_activity.state,
    pg_stat_activity.query_start,
    pg_stat_activity.state_change,
    EXTRACT(EPOCH FROM (now() - pg_stat_activity.query_start)) as query_duration_seconds,
    pg_locks.mode as lock_mode,
    pg_locks.locktype,
    pg_locks.relation::regclass as locked_relation
FROM pg_stat_activity
LEFT JOIN pg_locks ON pg_stat_activity.pid = pg_locks.pid
WHERE pg_stat_activity.datname = current_database()
  AND pg_stat_activity.state != 'idle'
ORDER BY query_duration_seconds DESC;

-- =====================================================
-- 2. 安全监控视图
-- =====================================================

-- 异常登录活动监控
CREATE OR REPLACE VIEW monitoring.suspicious_logins AS
SELECT
    user_id,
    COUNT(*) as failed_attempts,
    COUNT(DISTINCT ip_address) as distinct_ips,
    MIN(created_at) as first_attempt,
    MAX(created_at) as last_attempt,
    array_agg(DISTINCT ip_address) as ip_addresses
FROM auth.audit_logs
WHERE action = 'login'
  AND status = 'failure'
  AND created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
GROUP BY user_id
HAVING COUNT(*) >= 5  -- 1小时内失败5次以上
ORDER BY failed_attempts DESC;

-- 会话异常监控
CREATE OR REPLACE VIEW monitoring.session_anomalies AS
SELECT
    s.user_id,
    u.username,
    COUNT(*) as concurrent_sessions,
    COUNT(DISTINCT s.ip_address) as distinct_ips,
    COUNT(DISTINCT s.device_fingerprint) as distinct_devices,
    array_agg(DISTINCT s.ip_address) as ip_addresses,
    array_agg(DISTINCT s.session_type) as session_types
FROM auth.sessions s
JOIN auth.users u ON s.user_id = u.id
WHERE s.status = 'active'
  AND s.expires_at > CURRENT_TIMESTAMP
GROUP BY s.user_id, u.username
HAVING COUNT(*) > 5  -- 超过5个并发会话
   OR COUNT(DISTINCT s.ip_address) > 3  -- 来自超过3个不同IP
ORDER BY concurrent_sessions DESC;

-- 权限变更监控
CREATE OR REPLACE VIEW monitoring.privilege_changes AS
SELECT
    user_id,
    action,
    resource_type,
    resource_id,
    old_values,
    new_values,
    created_at,
    ip_address
FROM auth.audit_logs
WHERE action IN ('role_assign', 'role_revoke', 'permission_grant', 'permission_revoke')
  AND created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- =====================================================
-- 3. 容量规划监控
-- =====================================================

-- 表空间使用情况
CREATE OR REPLACE VIEW monitoring.table_sizes AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as indexes_size,
    pg_total_relation_size(schemaname||'.'||tablename) as bytes_total,
    round(100.0 * pg_total_relation_size(schemaname||'.'||tablename) / pg_database_size(current_database()), 2) as percent_of_db
FROM pg_tables
WHERE schemaname = 'auth'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 数据增长趋势
CREATE OR REPLACE VIEW monitoring.growth_trends AS
SELECT
    tablename,
    n_tup_ins as inserts_today,
    n_tup_del as deletes_today,
    n_live_tup as current_rows,
    CASE
        WHEN n_tup_ins > 0 THEN
            round(n_live_tup::numeric / n_tup_ins * 365, 0)
        ELSE NULL
    END as projected_rows_yearly
FROM pg_stat_user_tables
WHERE schemaname = 'auth'
  AND n_tup_ins > 0
ORDER BY n_tup_ins DESC;

-- =====================================================
-- 4. 性能警报函数
-- =====================================================

-- 检查慢查询
CREATE OR REPLACE FUNCTION monitoring.check_slow_queries(
    threshold_ms NUMERIC DEFAULT 1000
) RETURNS TABLE (
    alert_level TEXT,
    query_snippet TEXT,
    avg_time_ms NUMERIC,
    calls BIGINT,
    total_time_ms NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        CASE
            WHEN mean_time > threshold_ms * 5 THEN 'CRITICAL'
            WHEN mean_time > threshold_ms * 2 THEN 'HIGH'
            WHEN mean_time > threshold_ms THEN 'MEDIUM'
            ELSE 'LOW'
        END as alert_level,
        LEFT(query, 100) || '...' as query_snippet,
        round(mean_time::numeric, 2) as avg_time_ms,
        calls,
        round(total_time::numeric, 2) as total_time_ms
    FROM pg_stat_statements
    WHERE query LIKE '%auth.%'
      AND mean_time > threshold_ms
    ORDER BY mean_time DESC;
END;
$$ LANGUAGE plpgsql;

-- 检查索引膨胀
CREATE OR REPLACE FUNCTION monitoring.check_index_bloat()
RETURNS TABLE (
    schema_name TEXT,
    table_name TEXT,
    index_name TEXT,
    bloat_ratio NUMERIC,
    wasted_space TEXT,
    recommendation TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.nspname::TEXT as schema_name,
        c.relname::TEXT as table_name,
        i.relname::TEXT as index_name,
        round((pg_relation_size(i.oid)::numeric / nullif(pg_relation_size(c.oid), 0)) * 100, 2) as bloat_ratio,
        pg_size_pretty(pg_relation_size(i.oid)) as wasted_space,
        CASE
            WHEN pg_relation_size(i.oid) > 100 * 1024 * 1024 THEN 'Consider REINDEX'  -- > 100MB
            WHEN pg_relation_size(i.oid) > 10 * 1024 * 1024 THEN 'Monitor closely'   -- > 10MB
            ELSE 'OK'
        END as recommendation
    FROM pg_class c
    JOIN pg_namespace n ON c.relnamespace = n.oid
    JOIN pg_index idx ON c.oid = idx.indrelid
    JOIN pg_class i ON idx.indexrelid = i.oid
    WHERE n.nspname = 'auth'
      AND c.relkind = 'r'  -- 只查看表
      AND i.relkind = 'i'  -- 只查看索引
    ORDER BY pg_relation_size(i.oid) DESC;
END;
$$ LANGUAGE plpgsql;

-- 检查连接池状态
CREATE OR REPLACE FUNCTION monitoring.check_connection_health()
RETURNS TABLE (
    metric TEXT,
    current_value BIGINT,
    max_value BIGINT,
    usage_percent NUMERIC,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        'Active Connections'::TEXT as metric,
        count(*)::BIGINT as current_value,
        current_setting('max_connections')::BIGINT as max_value,
        round((count(*)::numeric / current_setting('max_connections')::numeric) * 100, 2) as usage_percent,
        CASE
            WHEN count(*) > current_setting('max_connections')::INTEGER * 0.8 THEN 'WARNING'
            WHEN count(*) > current_setting('max_connections')::INTEGER * 0.9 THEN 'CRITICAL'
            ELSE 'OK'
        END as status
    FROM pg_stat_activity
    WHERE state = 'active';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 5. 自动化监控报告
-- =====================================================

-- 生成每日性能报告
CREATE OR REPLACE FUNCTION monitoring.daily_performance_report()
RETURNS TEXT AS $$
DECLARE
    report_text TEXT := '';
    rec RECORD;
BEGIN
    report_text := report_text || '=== Daily Performance Report - ' || CURRENT_DATE || E' ===\n\n';

    -- 查询性能摘要
    report_text := report_text || '🔍 TOP 5 SLOWEST QUERIES:\n';
    FOR rec IN
        SELECT query_snippet, avg_time_ms, calls
        FROM monitoring.check_slow_queries(100)
        LIMIT 5
    LOOP
        report_text := report_text || format('- %s (%.2fms, %s calls)\n',
            rec.query_snippet, rec.avg_time_ms, rec.calls);
    END LOOP;

    -- 表增长情况
    report_text := report_text || E'\n📊 TABLE GROWTH:\n';
    FOR rec IN
        SELECT tablename, inserts_today, current_rows
        FROM monitoring.growth_trends
        WHERE inserts_today > 0
        LIMIT 5
    LOOP
        report_text := report_text || format('- %s: +%s rows (total: %s)\n',
            rec.tablename, rec.inserts_today, rec.current_rows);
    END LOOP;

    -- 安全事件
    report_text := report_text || E'\n🚨 SECURITY ALERTS:\n';
    FOR rec IN
        SELECT user_id, failed_attempts, distinct_ips
        FROM monitoring.suspicious_logins
        LIMIT 3
    LOOP
        report_text := report_text || format('- User %s: %s failed logins from %s IPs\n',
            rec.user_id, rec.failed_attempts, rec.distinct_ips);
    END LOOP;

    IF NOT FOUND THEN
        report_text := report_text || '- No security alerts\n';
    END IF;

    -- 系统健康状况
    report_text := report_text || E'\n💓 SYSTEM HEALTH:\n';
    FOR rec IN
        SELECT metric, usage_percent, status
        FROM monitoring.check_connection_health()
    LOOP
        report_text := report_text || format('- %s: %.1f%% (%s)\n',
            rec.metric, rec.usage_percent, rec.status);
    END LOOP;

    RETURN report_text;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 6. 实时监控仪表板查询
-- =====================================================

-- 系统概览仪表板
CREATE OR REPLACE VIEW monitoring.system_dashboard AS
SELECT
    'Database Size' as metric,
    pg_size_pretty(pg_database_size(current_database())) as value,
    'info' as level
UNION ALL
SELECT
    'Active Connections',
    count(*)::TEXT,
    CASE
        WHEN count(*) > 50 THEN 'warning'
        WHEN count(*) > 80 THEN 'critical'
        ELSE 'info'
    END
FROM pg_stat_activity
WHERE state != 'idle'
UNION ALL
SELECT
    'Cache Hit Ratio',
    round(100.0 * sum(blks_hit) / nullif(sum(blks_hit + blks_read), 0), 2)::TEXT || '%',
    CASE
        WHEN round(100.0 * sum(blks_hit) / nullif(sum(blks_hit + blks_read), 0), 2) < 95 THEN 'warning'
        ELSE 'info'
    END
FROM pg_stat_database
WHERE datname = current_database();

-- 认证系统特定监控
CREATE OR REPLACE VIEW monitoring.auth_system_health AS
SELECT
    'Active Sessions' as metric,
    count(*)::TEXT as value,
    'info' as level
FROM auth.sessions
WHERE status = 'active' AND expires_at > CURRENT_TIMESTAMP
UNION ALL
SELECT
    'Users Today',
    count(DISTINCT user_id)::TEXT,
    'info'
FROM auth.audit_logs
WHERE action = 'login'
  AND status = 'success'
  AND created_at > CURRENT_DATE
UNION ALL
SELECT
    'Failed Logins (1h)',
    count(*)::TEXT,
    CASE
        WHEN count(*) > 100 THEN 'warning'
        WHEN count(*) > 500 THEN 'critical'
        ELSE 'info'
    END
FROM auth.audit_logs
WHERE action = 'login'
  AND status = 'failure'
  AND created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour';

-- =====================================================
-- 7. 定期维护任务
-- =====================================================

-- 清理过期数据
CREATE OR REPLACE FUNCTION monitoring.cleanup_old_data()
RETURNS TEXT AS $$
DECLARE
    cleanup_report TEXT := '';
    deleted_sessions INTEGER;
    deleted_audit_logs INTEGER;
BEGIN
    -- 清理过期会话
    DELETE FROM auth.sessions
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
       OR (status != 'active' AND created_at < CURRENT_TIMESTAMP - INTERVAL '30 days');

    GET DIAGNOSTICS deleted_sessions = ROW_COUNT;

    -- 清理旧审计日志 (保留1年)
    DELETE FROM auth.audit_logs
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 year';

    GET DIAGNOSTICS deleted_audit_logs = ROW_COUNT;

    cleanup_report := format('Cleanup completed: %s old sessions, %s old audit logs removed',
        deleted_sessions, deleted_audit_logs);

    -- 记录清理操作
    INSERT INTO auth.audit_logs (action, status, metadata)
    VALUES ('system_cleanup', 'success',
        jsonb_build_object('deleted_sessions', deleted_sessions, 'deleted_audit_logs', deleted_audit_logs));

    RETURN cleanup_report;
END;
$$ LANGUAGE plpgsql;

-- 更新表统计信息
CREATE OR REPLACE FUNCTION monitoring.update_statistics()
RETURNS TEXT AS $$
DECLARE
    table_rec RECORD;
    update_count INTEGER := 0;
BEGIN
    FOR table_rec IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'auth'
    LOOP
        EXECUTE 'ANALYZE auth.' || table_rec.tablename;
        update_count := update_count + 1;
    END LOOP;

    RETURN format('Updated statistics for %s tables', update_count);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 使用说明和示例
-- =====================================================

/*
使用示例：

1. 查看当前性能状况：
   SELECT * FROM monitoring.system_dashboard;
   SELECT * FROM monitoring.auth_system_health;

2. 检查慢查询：
   SELECT * FROM monitoring.check_slow_queries(500);  -- 检查超过500ms的查询

3. 生成每日报告：
   SELECT monitoring.daily_performance_report();

4. 检查安全威胁：
   SELECT * FROM monitoring.suspicious_logins;
   SELECT * FROM monitoring.session_anomalies;

5. 执行维护任务：
   SELECT monitoring.cleanup_old_data();
   SELECT monitoring.update_statistics();

6. 监控索引性能：
   SELECT * FROM monitoring.index_performance WHERE usage_level = 'UNUSED';

建议设置定期任务：
- 每小时执行一次：monitoring.check_slow_queries()
- 每天执行一次：monitoring.daily_performance_report(), monitoring.cleanup_old_data()
- 每周执行一次：monitoring.update_statistics()
*/