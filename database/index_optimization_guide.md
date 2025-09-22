# 用户认证系统 - 索引优化建议

## 🎯 索引策略概述

这份指南基于数据库专家的最佳实践，为用户认证系统提供详细的索引优化策略。我们的目标是在查询性能和存储空间之间找到最佳平衡。

## 📊 性能基准

### 预期查询模式分析
```sql
-- 高频查询 (每秒100+次)
SELECT * FROM users WHERE email = ? AND deleted_at IS NULL;
SELECT * FROM sessions WHERE session_id = ? AND status = 'active';

-- 中频查询 (每秒10-50次)
SELECT * FROM users WHERE username = ? AND deleted_at IS NULL;
SELECT * FROM sessions WHERE user_id = ? AND status = 'active';

-- 低频查询 (每秒1-10次)
SELECT * FROM audit_logs WHERE user_id = ? AND created_at > ?;
SELECT * FROM user_roles WHERE user_id = ? AND status = 'active';
```

## 🔍 核心表索引策略

### 1. users表索引优化

#### 主要索引
```sql
-- 邮箱登录索引 (最高优先级)
CREATE UNIQUE INDEX CONCURRENTLY idx_users_email_active
ON auth.users(email)
WHERE deleted_at IS NULL;

-- 用户名登录索引
CREATE UNIQUE INDEX CONCURRENTLY idx_users_username_active
ON auth.users(username)
WHERE deleted_at IS NULL;

-- UUID查找索引 (API密钥场景)
CREATE UNIQUE INDEX CONCURRENTLY idx_users_uuid
ON auth.users(uuid);
```

#### 状态和安全索引
```sql
-- 用户状态查询
CREATE INDEX CONCURRENTLY idx_users_status
ON auth.users(status)
WHERE deleted_at IS NULL;

-- 邮箱验证查询
CREATE INDEX CONCURRENTLY idx_users_email_verification
ON auth.users(email_verification_token)
WHERE email_verification_token IS NOT NULL;

-- 密码重置查询
CREATE INDEX CONCURRENTLY idx_users_password_reset
ON auth.users(password_reset_token)
WHERE password_reset_token IS NOT NULL;

-- 锁定用户查询
CREATE INDEX CONCURRENTLY idx_users_locked
ON auth.users(locked_until)
WHERE locked_until IS NOT NULL;
```

#### 复合索引优化
```sql
-- 管理面板用户列表查询
CREATE INDEX CONCURRENTLY idx_users_admin_list
ON auth.users(status, created_at DESC)
WHERE deleted_at IS NULL;

-- MFA用户查询
CREATE INDEX CONCURRENTLY idx_users_mfa_enabled
ON auth.users(mfa_enabled)
WHERE deleted_at IS NULL AND mfa_enabled = TRUE;
```

### 2. sessions表索引优化

#### 核心会话索引
```sql
-- 会话ID查找 (最高频)
CREATE UNIQUE INDEX CONCURRENTLY idx_sessions_session_id
ON auth.sessions(session_id);

-- 用户会话查询
CREATE INDEX CONCURRENTLY idx_sessions_user_id_status
ON auth.sessions(user_id, status)
WHERE status = 'active';

-- 会话清理索引
CREATE INDEX CONCURRENTLY idx_sessions_cleanup
ON auth.sessions(expires_at, last_activity_at)
WHERE status = 'active';
```

#### 安全监控索引
```sql
-- IP地址追踪
CREATE INDEX CONCURRENTLY idx_sessions_ip_monitoring
ON auth.sessions(ip_address, created_at)
WHERE status = 'active';

-- 设备指纹追踪
CREATE INDEX CONCURRENTLY idx_sessions_device_tracking
ON auth.sessions(device_fingerprint, user_id)
WHERE device_fingerprint IS NOT NULL;

-- 可疑活动检测
CREATE INDEX CONCURRENTLY idx_sessions_activity_analysis
ON auth.sessions(user_id, last_activity_at, ip_address);
```

### 3. audit_logs表索引优化 (大数据量优化)

#### 基础查询索引
```sql
-- 用户操作历史
CREATE INDEX CONCURRENTLY idx_audit_logs_user_timeline
ON auth.audit_logs(user_id, created_at DESC);

-- 操作类型分析
CREATE INDEX CONCURRENTLY idx_audit_logs_action_analysis
ON auth.audit_logs(action, created_at DESC);

-- 失败操作监控
CREATE INDEX CONCURRENTLY idx_audit_logs_failures
ON auth.audit_logs(status, created_at DESC)
WHERE status = 'failure';
```

#### 安全分析索引
```sql
-- IP地址安全分析
CREATE INDEX CONCURRENTLY idx_audit_logs_ip_security
ON auth.audit_logs(ip_address, action, created_at);

-- 请求追踪索引
CREATE INDEX CONCURRENTLY idx_audit_logs_request_tracing
ON auth.audit_logs(request_id);

-- 严重性级别索引
CREATE INDEX CONCURRENTLY idx_audit_logs_severity
ON auth.audit_logs(severity_level, created_at DESC)
WHERE severity_level IN ('critical', 'high');
```

### 4. 角色权限索引优化

#### 角色管理索引
```sql
-- 角色名称查找
CREATE UNIQUE INDEX CONCURRENTLY idx_roles_name
ON auth.roles(name);

-- 角色层级查询
CREATE INDEX CONCURRENTLY idx_roles_level_active
ON auth.roles(level, status)
WHERE status = 'active';

-- 默认角色查询
CREATE INDEX CONCURRENTLY idx_roles_default
ON auth.roles(is_default_role)
WHERE is_default_role = TRUE;
```

#### 用户角色关联索引
```sql
-- 用户角色查询
CREATE INDEX CONCURRENTLY idx_user_roles_user_active
ON auth.user_roles(user_id, status)
WHERE status = 'active';

-- 角色用户查询
CREATE INDEX CONCURRENTLY idx_user_roles_role_active
ON auth.user_roles(role_id, status)
WHERE status = 'active';

-- 角色过期监控
CREATE INDEX CONCURRENTLY idx_user_roles_expiry
ON auth.user_roles(expires_at)
WHERE expires_at IS NOT NULL AND status = 'active';
```

## 📈 性能优化建议

### 1. 分区策略

#### audit_logs表月度分区
```sql
-- 创建分区表函数
CREATE OR REPLACE FUNCTION auth.create_audit_partition(
    start_date DATE,
    end_date DATE
) RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
BEGIN
    partition_name := 'audit_logs_' || to_char(start_date, 'YYYY_MM');

    EXECUTE format('
        CREATE TABLE auth.%I PARTITION OF auth.audit_logs
        FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );

    -- 为分区创建索引
    EXECUTE format('
        CREATE INDEX CONCURRENTLY idx_%I_created_at
        ON auth.%I(created_at)',
        partition_name, partition_name
    );
END;
$$ LANGUAGE plpgsql;

-- 自动创建未来3个月的分区
SELECT auth.create_audit_partition(
    date_trunc('month', CURRENT_DATE + interval '1 month'),
    date_trunc('month', CURRENT_DATE + interval '2 months')
);
```

### 2. 查询优化模式

#### 使用覆盖索引
```sql
-- 用户列表查询覆盖索引
CREATE INDEX CONCURRENTLY idx_users_list_covering
ON auth.users(status, created_at)
INCLUDE (id, username, email, first_name, last_name)
WHERE deleted_at IS NULL;

-- 会话验证覆盖索引
CREATE INDEX CONCURRENTLY idx_sessions_validation_covering
ON auth.sessions(session_id)
INCLUDE (user_id, status, expires_at, last_activity_at);
```

#### 表达式索引
```sql
-- 全文搜索索引
CREATE INDEX CONCURRENTLY idx_users_fulltext_search
ON auth.users USING gin(
    to_tsvector('english',
        coalesce(first_name, '') || ' ' ||
        coalesce(last_name, '') || ' ' ||
        coalesce(username, '') || ' ' ||
        coalesce(email, '')
    )
) WHERE deleted_at IS NULL;

-- 邮箱域名分析索引
CREATE INDEX CONCURRENTLY idx_users_email_domain
ON auth.users((split_part(email, '@', 2)))
WHERE deleted_at IS NULL;
```

### 3. 索引维护策略

#### 自动索引监控
```sql
-- 索引使用情况监控视图
CREATE OR REPLACE VIEW auth.index_usage_stats AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan,
    CASE
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 100 THEN 'LOW_USAGE'
        WHEN idx_scan < 1000 THEN 'MEDIUM_USAGE'
        ELSE 'HIGH_USAGE'
    END as usage_level
FROM pg_stat_user_indexes
WHERE schemaname = 'auth'
ORDER BY idx_scan DESC;

-- 索引膨胀监控
CREATE OR REPLACE VIEW auth.index_bloat_stats AS
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    pg_size_pretty(pg_relation_size(tablename::regclass)) as table_size
FROM pg_stat_user_indexes
WHERE schemaname = 'auth'
ORDER BY pg_relation_size(indexrelid) DESC;
```

#### 索引重建策略
```sql
-- 定期重建索引的存储过程
CREATE OR REPLACE FUNCTION auth.rebuild_indexes()
RETURNS TEXT AS $$
DECLARE
    index_record RECORD;
    result_text TEXT := '';
BEGIN
    FOR index_record IN
        SELECT indexname
        FROM pg_stat_user_indexes
        WHERE schemaname = 'auth'
          AND idx_scan > 1000  -- 只重建使用频繁的索引
    LOOP
        EXECUTE 'REINDEX INDEX CONCURRENTLY auth.' || index_record.indexname;
        result_text := result_text || 'Rebuilt: ' || index_record.indexname || E'\n';
    END LOOP;

    RETURN result_text;
END;
$$ LANGUAGE plpgsql;
```

## 🔧 监控和调优

### 1. 性能监控查询

#### 慢查询识别
```sql
-- 识别需要索引的慢查询
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
WHERE query LIKE '%auth.%'
  AND mean_time > 100  -- 超过100ms的查询
ORDER BY mean_time DESC
LIMIT 10;
```

#### 索引命中率监控
```sql
-- 索引命中率检查
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    CASE
        WHEN idx_tup_read = 0 THEN 0
        ELSE round((idx_tup_fetch::numeric / idx_tup_read) * 100, 2)
    END as hit_rate_percent
FROM pg_stat_user_indexes
WHERE schemaname = 'auth'
  AND idx_scan > 0
ORDER BY hit_rate_percent DESC;
```

### 2. 自动优化建议

#### 缺失索引检测
```sql
-- 检测可能需要索引的查询模式
CREATE OR REPLACE FUNCTION auth.suggest_missing_indexes()
RETURNS TABLE(
    table_name TEXT,
    column_suggestion TEXT,
    query_pattern TEXT,
    estimated_benefit TEXT
) AS $$
BEGIN
    -- 基于查询模式的索引建议逻辑
    RETURN QUERY
    SELECT
        'users'::TEXT,
        'Consider: CREATE INDEX ON users(last_login_at) WHERE deleted_at IS NULL'::TEXT,
        'WHERE last_login_at conditions'::TEXT,
        'HIGH - frequently used in user activity queries'::TEXT
    WHERE NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'users'
        AND indexdef LIKE '%last_login_at%'
    );
END;
$$ LANGUAGE plpgsql;
```

## 📝 最佳实践总结

### 1. 索引设计原则
- **选择性优先**: 优先为高选择性列创建索引
- **复合索引顺序**: 最选择性的列放在前面
- **部分索引**: 使用WHERE子句过滤不需要的行
- **覆盖索引**: 包含查询所需的所有列

### 2. 维护建议
- **定期监控**: 每周检查索引使用情况
- **自动清理**: 设置定时任务清理过期数据
- **性能测试**: 在生产环境变更前进行压力测试
- **备份策略**: 索引重建前确保有数据备份

### 3. 扩展性考虑
- **水平分区**: 大表按时间或ID范围分区
- **读写分离**: 读查询使用只读副本
- **缓存层**: 高频查询结果缓存到Redis
- **连接池**: 使用pgbouncer等连接池工具

## 🚀 实施步骤

1. **第一阶段**: 创建核心索引 (users, sessions)
2. **第二阶段**: 添加安全监控索引 (audit_logs)
3. **第三阶段**: 实施分区策略 (大表优化)
4. **第四阶段**: 部署监控和自动化维护

每个阶段完成后都要进行性能测试，确保索引带来预期的性能提升。