# Perfect21 Operations & Maintenance Guide

## 🎯 Overview

This comprehensive operations guide covers day-to-day management, monitoring, troubleshooting, and maintenance of the Perfect21 (Claude Enhancer) system. It provides detailed procedures for system administrators, DevOps engineers, and on-call personnel.

## 📊 System Monitoring

### Health Check Procedures

#### Daily Health Checks
```bash
#!/bin/bash
# scripts/daily-health-check.sh

echo "=== Perfect21 Daily Health Check ==="
echo "Date: $(date)"
echo "Operator: $(whoami)"
echo

# 1. API Health Check
echo "1. API Health Status:"
HEALTH_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" http://localhost:3000/api/v1/health)
HTTP_CODE=$(echo $HEALTH_RESPONSE | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ API is healthy"
    echo "$HEALTH_RESPONSE" | sed 's/HTTP_CODE:.*//' | jq '.'
else
    echo "❌ API health check failed (HTTP $HTTP_CODE)"
    echo "$HEALTH_RESPONSE"
fi
echo

# 2. Database Connectivity
echo "2. Database Status:"
if psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ Database connection successful"

    # Check database size
    DB_SIZE=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "SELECT pg_size_pretty(pg_database_size(current_database()));")
    echo "   Database size: $DB_SIZE"

    # Check active connections
    ACTIVE_CONN=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';")
    echo "   Active connections: $ACTIVE_CONN"
else
    echo "❌ Database connection failed"
fi
echo

# 3. Redis Status
echo "3. Redis Status:"
if redis-cli -h $REDIS_HOST -p $REDIS_PORT --no-auth-warning -a $REDIS_PASSWORD ping >/dev/null 2>&1; then
    echo "✅ Redis is responding"

    # Check memory usage
    REDIS_MEM=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT --no-auth-warning -a $REDIS_PASSWORD info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
    echo "   Memory usage: $REDIS_MEM"

    # Check key count
    KEY_COUNT=$(redis-cli -h $REDIS_HOST -p $REDIS_PORT --no-auth-warning -a $REDIS_PASSWORD dbsize)
    echo "   Total keys: $KEY_COUNT"
else
    echo "❌ Redis connection failed"
fi
echo

# 4. System Resources
echo "4. System Resources:"
echo "   CPU usage:"
top -bn1 | grep "Cpu(s)" | awk '{print "     " $2 " user, " $4 " system"}'

echo "   Memory usage:"
free -h | awk 'NR==2{printf "     Used: %s/%s (%.2f%%)\n", $3,$2,$3*100/$2 }'

echo "   Disk usage:"
df -h | awk '$NF=="/"{printf "     Root: %d/%dGB (%s)\n", $3,$2,$5}'

echo "   Load average:"
uptime | awk -F'load average:' '{ print "     " $2 }'
echo

# 5. Agent System Status
echo "5. Agent System Status:"
AGENT_STATUS=$(curl -s http://localhost:3000/api/v1/agents/status 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Agent system responsive"
    echo "$AGENT_STATUS" | jq '.data.available_agents // "N/A"' | sed 's/^/     Available agents: /'
    echo "$AGENT_STATUS" | jq '.data.active_tasks // "N/A"' | sed 's/^/     Active tasks: /'
else
    echo "❌ Agent system not responding"
fi
echo

# 6. Recent Error Summary
echo "6. Recent Errors (last 1 hour):"
if [ -f "/var/log/perfect21/app.log" ]; then
    ERROR_COUNT=$(grep -c "ERROR\|error" /var/log/perfect21/app.log | tail -100)
    echo "   Error count: $ERROR_COUNT"

    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "   Recent errors:"
        grep "ERROR\|error" /var/log/perfect21/app.log | tail -5 | sed 's/^/     /'
    fi
else
    echo "   Log file not found"
fi

echo
echo "=== Health Check Complete ==="
```

#### Continuous Monitoring Endpoints

**Primary Health Check**
```bash
# Basic health check
curl -f http://localhost:3000/api/v1/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "4.0.0",
  "uptime": 86400,
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "agents": "healthy"
  }
}
```

**Detailed System Status**
```bash
# Comprehensive system status
curl -f http://localhost:3000/api/v1/system/status

# Expected response:
{
  "system": {
    "status": "operational",
    "agents": {
      "available": 56,
      "active": 3,
      "queued_tasks": 2
    },
    "performance": {
      "avg_response_time": "145ms",
      "success_rate": "99.8%",
      "throughput": "1250 req/min"
    },
    "resources": {
      "cpu_usage": "45%",
      "memory_usage": "67%",
      "disk_usage": "23%"
    }
  }
}
```

### Metrics Collection & Analysis

#### Key Performance Indicators (KPIs)

**System KPIs**
- **Availability**: Target 99.9% uptime
- **Response Time**: P95 < 500ms, P99 < 1000ms
- **Throughput**: Requests per minute
- **Error Rate**: < 0.1% for 5XX errors
- **Agent Utilization**: 70-85% optimal range

**Business KPIs**
- **Task Completion Rate**: > 95%
- **Agent Selection Accuracy**: > 98%
- **Quality Score**: Average > 4.5/5.0
- **User Satisfaction**: Based on task success

#### Prometheus Queries

**Response Time Monitoring**
```promql
# 95th percentile response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Average response time by endpoint
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Response time trend (last 24 hours)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1h]))
```

**Error Rate Monitoring**
```promql
# Overall error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Error rate by endpoint
rate(http_requests_total{status=~"5.."}[5m]) by (endpoint)

# Critical error count
increase(http_requests_total{status="500"}[1h])
```

**Agent Performance**
```promql
# Active agents
perfect21_agents_active

# Task completion rate
rate(perfect21_tasks_completed_total{status="success"}[5m]) / rate(perfect21_tasks_completed_total[5m])

# Average task duration
rate(perfect21_task_duration_seconds_sum[5m]) / rate(perfect21_task_duration_seconds_count[5m])
```

**Resource Utilization**
```promql
# CPU usage
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory usage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disk usage
100 - ((node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100)
```

### Alert Configuration

#### Critical Alerts (Immediate Response)

```yaml
# alerting/critical-alerts.yml
groups:
  - name: perfect21_critical
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
          team: devops
        annotations:
          summary: "Service {{ $labels.instance }} is down"
          description: "Service has been down for more than 1 minute"
          runbook_url: "https://docs.perfect21.com/runbooks/service-down"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
          team: engineering
        annotations:
          summary: "High error rate: {{ $value | humanizePercentage }}"
          description: "Error rate is above 5% for 2 minutes"
          runbook_url: "https://docs.perfect21.com/runbooks/high-error-rate"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 30s
        labels:
          severity: critical
          team: dba
        annotations:
          summary: "PostgreSQL database is down"
          description: "Database connection failed"
          runbook_url: "https://docs.perfect21.com/runbooks/database-down"

      - alert: AgentSystemFailure
        expr: perfect21_agents_active == 0
        for: 2m
        labels:
          severity: critical
          team: engineering
        annotations:
          summary: "No agents are active"
          description: "Agent system appears to be down"
          runbook_url: "https://docs.perfect21.com/runbooks/agent-failure"
```

#### Warning Alerts (Monitor & Plan)

```yaml
# alerting/warning-alerts.yml
groups:
  - name: perfect21_warnings
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
          team: engineering
        annotations:
          summary: "High latency detected: {{ $value }}s"
          description: "95th percentile latency is above 500ms"
          runbook_url: "https://docs.perfect21.com/runbooks/high-latency"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 80
        for: 5m
        labels:
          severity: warning
          team: devops
        annotations:
          summary: "High memory usage: {{ $value }}%"
          description: "Memory usage is above 80%"
          runbook_url: "https://docs.perfect21.com/runbooks/high-memory"

      - alert: DiskSpaceWarning
        expr: 100 - ((node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100) > 75
        for: 5m
        labels:
          severity: warning
          team: devops
        annotations:
          summary: "Disk space warning: {{ $value }}% used"
          description: "Disk usage is above 75%"
          runbook_url: "https://docs.perfect21.com/runbooks/disk-space"

      - alert: LowAgentUtilization
        expr: perfect21_agents_active < 3
        for: 10m
        labels:
          severity: warning
          team: engineering
        annotations:
          summary: "Low agent utilization: {{ $value }} active"
          description: "Fewer than 3 agents are active"
          runbook_url: "https://docs.perfect21.com/runbooks/low-utilization"
```

## 🔧 Routine Maintenance

### Daily Operations

#### Morning Checklist
```bash
#!/bin/bash
# scripts/morning-checklist.sh

echo "🌅 Perfect21 Morning Operations Checklist"
echo "========================================="
date
echo

# 1. System health overview
echo "1. 📊 System Health Overview"
./scripts/daily-health-check.sh | grep -E "(✅|❌|ERROR|WARN)"
echo

# 2. Check overnight alerts
echo "2. 🚨 Overnight Alerts"
if command -v amtool >/dev/null 2>&1; then
    ACTIVE_ALERTS=$(amtool alert query --quiet)
    if [ -n "$ACTIVE_ALERTS" ]; then
        echo "   Active alerts found:"
        echo "$ACTIVE_ALERTS" | head -10
    else
        echo "   ✅ No active alerts"
    fi
else
    echo "   Alertmanager CLI not available"
fi
echo

# 3. Performance metrics summary
echo "3. 📈 Performance Summary (Last 24h)"
if command -v promtool >/dev/null 2>&1; then
    echo "   Response Time (P95): $(./scripts/get-metric.sh 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[24h]))')"
    echo "   Error Rate: $(./scripts/get-metric.sh 'rate(http_requests_total{status=~"5.."}[24h]) / rate(http_requests_total[24h])')"
    echo "   Tasks Completed: $(./scripts/get-metric.sh 'increase(perfect21_tasks_completed_total[24h])')"
else
    echo "   Prometheus CLI not available"
fi
echo

# 4. Resource utilization
echo "4. 💻 Resource Utilization"
echo "   CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "   Memory: $(free | grep Mem | awk '{printf("%.1f%%"), $3/$2 * 100.0}')"
echo "   Disk: $(df / | tail -1 | awk '{print $5}')"
echo

# 5. Service status
echo "5. 🔄 Service Status"
if command -v docker >/dev/null 2>&1; then
    echo "   Docker containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep perfect21
elif command -v kubectl >/dev/null 2>&1; then
    echo "   Kubernetes pods:"
    kubectl get pods -n perfect21 --no-headers | awk '{print "     " $1 "\t" $3}'
fi
echo

# 6. Recent deployments
echo "6. 🚀 Recent Deployments"
if [ -f "/var/log/perfect21/deployment.log" ]; then
    echo "   Last deployment:"
    tail -1 /var/log/perfect21/deployment.log | sed 's/^/     /'
else
    echo "   No deployment log found"
fi
echo

echo "✅ Morning checklist complete"
echo "Next: Review any warnings and plan daily tasks"
```

#### Evening Checklist
```bash
#!/bin/bash
# scripts/evening-checklist.sh

echo "🌙 Perfect21 Evening Operations Checklist"
echo "========================================="
date
echo

# 1. Day summary
echo "1. 📋 Daily Summary"
echo "   Tasks processed today: $(./scripts/get-daily-stats.sh tasks)"
echo "   Average response time: $(./scripts/get-daily-stats.sh response_time)"
echo "   Success rate: $(./scripts/get-daily-stats.sh success_rate)"
echo "   Peak concurrent users: $(./scripts/get-daily-stats.sh peak_users)"
echo

# 2. Error analysis
echo "2. 🔍 Error Analysis"
ERROR_COUNT=$(grep -c "ERROR" /var/log/perfect21/app.log 2>/dev/null || echo "0")
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "   Total errors today: $ERROR_COUNT"
    echo "   Top error types:"
    grep "ERROR" /var/log/perfect21/app.log | awk '{print $4}' | sort | uniq -c | sort -nr | head -5 | sed 's/^/     /'
else
    echo "   ✅ No errors detected today"
fi
echo

# 3. Performance trends
echo "3. 📊 Performance Trends"
./scripts/performance-summary.sh daily
echo

# 4. Backup verification
echo "4. 💾 Backup Status"
if [ -f "/backup/status/today.log" ]; then
    echo "   Database backup: $(grep "database" /backup/status/today.log | tail -1)"
    echo "   Config backup: $(grep "config" /backup/status/today.log | tail -1)"
else
    echo "   ⚠️  Backup status file not found"
fi
echo

# 5. Security events
echo "5. 🔒 Security Events"
FAILED_LOGINS=$(grep "authentication failed" /var/log/perfect21/security.log 2>/dev/null | wc -l || echo "0")
RATE_LIMITED=$(grep "rate limit exceeded" /var/log/perfect21/app.log 2>/dev/null | wc -l || echo "0")
echo "   Failed login attempts: $FAILED_LOGINS"
echo "   Rate limit violations: $RATE_LIMITED"
echo

# 6. Tomorrow's preparation
echo "6. 🔮 Tomorrow's Preparation"
echo "   Scheduled maintenance: $(./scripts/check-scheduled-tasks.sh)"
echo "   Resource forecast: $(./scripts/capacity-forecast.sh)"
echo

echo "✅ Evening checklist complete"
echo "System ready for overnight operations"
```

### Weekly Maintenance

#### Database Maintenance
```bash
#!/bin/bash
# scripts/weekly-db-maintenance.sh

echo "🗄️ Weekly Database Maintenance"
echo "============================="
date
echo

# 1. Database statistics update
echo "1. Updating database statistics..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "ANALYZE;"
echo "   ✅ Statistics updated"
echo

# 2. Vacuum database
echo "2. Performing database vacuum..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "VACUUM (ANALYZE, VERBOSE);" > /tmp/vacuum.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Vacuum completed successfully"
    # Check if any tables were skipped
    SKIPPED=$(grep -c "skipping" /tmp/vacuum.log)
    if [ "$SKIPPED" -gt 0 ]; then
        echo "   ⚠️  $SKIPPED tables were skipped (likely due to locks)"
    fi
else
    echo "   ❌ Vacuum failed - check logs"
fi
echo

# 3. Index maintenance
echo "3. Checking index health..."
INDEX_BLOAT=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "
SELECT count(*) FROM (
    SELECT schemaname, tablename, indexname,
           pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
           idx_scan, idx_tup_read, idx_tup_fetch
    FROM pg_stat_user_indexes
    WHERE idx_scan = 0
) unused_indexes;")

echo "   Unused indexes: $INDEX_BLOAT"
if [ "$INDEX_BLOAT" -gt 0 ]; then
    echo "   ⚠️  Consider reviewing unused indexes"
fi
echo

# 4. Database size monitoring
echo "4. Database size report..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT
    pg_size_pretty(pg_database_size(current_database())) as database_size,
    (SELECT count(*) FROM users) as user_count,
    (SELECT count(*) FROM tasks) as task_count,
    (SELECT count(*) FROM agents) as agent_count;
"
echo

# 5. Connection monitoring
echo "5. Connection statistics..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT
    state,
    count(*) as connection_count
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY state
ORDER BY connection_count DESC;
"
echo

# 6. Long-running queries check
echo "6. Checking for long-running queries..."
LONG_QUERIES=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "
SELECT count(*)
FROM pg_stat_activity
WHERE state = 'active'
  AND query_start < now() - interval '5 minutes'
  AND query NOT LIKE '%pg_stat_activity%';")

if [ "$LONG_QUERIES" -gt 0 ]; then
    echo "   ⚠️  $LONG_QUERIES long-running queries detected"
    echo "   Use the following query to investigate:"
    echo "   SELECT pid, now() - query_start as duration, query FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '5 minutes';"
else
    echo "   ✅ No long-running queries detected"
fi

echo
echo "✅ Weekly database maintenance complete"
```

#### Security Updates
```bash
#!/bin/bash
# scripts/weekly-security-updates.sh

echo "🔒 Weekly Security Maintenance"
echo "============================="
date
echo

# 1. System package updates
echo "1. Checking system package updates..."
apt list --upgradable 2>/dev/null | wc -l | awk '{print "   Available updates: " $1-1}'

echo "   Installing security updates..."
sudo apt update
sudo apt upgrade -y --only-upgrade $(apt list --upgradable 2>/dev/null | grep -i security | cut -d'/' -f1)
echo "   ✅ Security updates applied"
echo

# 2. Node.js dependency audit
echo "2. Node.js security audit..."
cd /app
npm audit --audit-level high
if [ $? -eq 0 ]; then
    echo "   ✅ No high-severity vulnerabilities found"
else
    echo "   ⚠️  High-severity vulnerabilities detected"
    echo "   Run 'npm audit fix' to resolve"
fi
echo

# 3. Docker image updates
echo "3. Checking Docker image updates..."
if command -v docker >/dev/null 2>&1; then
    echo "   Pulling latest base images..."
    docker pull node:18-alpine
    docker pull postgres:15-alpine
    docker pull redis:7-alpine
    echo "   ✅ Base images updated"
fi
echo

# 4. SSL certificate check
echo "4. SSL certificate validation..."
CERT_EXPIRY=$(echo | openssl s_client -connect api.perfect21.com:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
CERT_DAYS=$(( ($(date -d "$CERT_EXPIRY" +%s) - $(date +%s)) / 86400 ))

echo "   Certificate expires: $CERT_EXPIRY"
echo "   Days remaining: $CERT_DAYS"

if [ "$CERT_DAYS" -lt 30 ]; then
    echo "   ⚠️  Certificate expires in less than 30 days"
    echo "   Schedule renewal soon"
elif [ "$CERT_DAYS" -lt 7 ]; then
    echo "   🚨 Certificate expires in less than 7 days - URGENT"
else
    echo "   ✅ Certificate expiry is acceptable"
fi
echo

# 5. Access log analysis
echo "5. Security log analysis..."
if [ -f "/var/log/nginx/access.log" ]; then
    # Check for suspicious activity
    SUSPICIOUS_IPS=$(awk '$9 ~ /^4[0-9][0-9]$/ {print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr | head -5)
    echo "   Top failed request sources:"
    echo "$SUSPICIOUS_IPS" | sed 's/^/     /'

    # Check for common attack patterns
    ATTACK_ATTEMPTS=$(grep -E "(sql|script|union|select|drop|delete|insert|update)" /var/log/nginx/access.log | wc -l)
    echo "   Potential attack attempts: $ATTACK_ATTEMPTS"
else
    echo "   ⚠️  Access log not found"
fi
echo

# 6. Generate security report
echo "6. Generating security report..."
cat > /tmp/security-report.txt << EOF
Weekly Security Report - $(date)
================================

System Updates: $(apt list --upgradable 2>/dev/null | wc -l | awk '{print $1-1}') available
NPM Vulnerabilities: $(npm audit --json 2>/dev/null | jq '.metadata.vulnerabilities.high // 0')
SSL Certificate Days: $CERT_DAYS
Attack Attempts: $ATTACK_ATTEMPTS

Action Items:
- Review and apply any remaining updates
- Monitor certificate expiry
- Investigate any suspicious activity
EOF

echo "   ✅ Security report saved to /tmp/security-report.txt"

echo
echo "✅ Weekly security maintenance complete"
```

### Monthly Maintenance

#### Capacity Planning
```bash
#!/bin/bash
# scripts/monthly-capacity-planning.sh

echo "📊 Monthly Capacity Planning Report"
echo "=================================="
date
echo

# 1. Growth trends
echo "1. 📈 Growth Trends (Last 30 days)"
echo "   User growth:"
USER_GROWTH=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "
SELECT
    (SELECT count(*) FROM users WHERE created_at >= now() - interval '30 days') as new_users,
    (SELECT count(*) FROM users) as total_users;
")
echo "$USER_GROWTH" | awk '{printf "     New users: %d, Total: %d\n", $1, $2}'

echo "   Task volume:"
TASK_GROWTH=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "
SELECT
    (SELECT count(*) FROM tasks WHERE created_at >= now() - interval '30 days') as recent_tasks,
    (SELECT count(*) FROM tasks) as total_tasks;
")
echo "$TASK_GROWTH" | awk '{printf "     Recent tasks: %d, Total: %d\n", $1, $2}'
echo

# 2. Resource utilization trends
echo "2. 💻 Resource Utilization Trends"
echo "   Average CPU usage: $(./scripts/get-monthly-average.sh cpu)%"
echo "   Average memory usage: $(./scripts/get-monthly-average.sh memory)%"
echo "   Peak concurrent users: $(./scripts/get-monthly-peak.sh users)"
echo "   Average response time: $(./scripts/get-monthly-average.sh response_time)ms"
echo

# 3. Database growth
echo "3. 🗄️ Database Growth Analysis"
DB_SIZES=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) AS size,
    pg_total_relation_size(tablename::regclass) AS size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC
LIMIT 10;
")
echo "$DB_SIZES"
echo

# 4. Performance analysis
echo "4. 🚀 Performance Analysis"
echo "   Top slow queries:"
SLOW_QUERIES=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 5;
")
echo "$SLOW_QUERIES"
echo

# 5. Capacity recommendations
echo "5. 💡 Capacity Recommendations"

# Calculate current utilization
CPU_AVG=$(./scripts/get-monthly-average.sh cpu 2>/dev/null || echo "50")
MEM_AVG=$(./scripts/get-monthly-average.sh memory 2>/dev/null || echo "60")
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')

echo "   Current resource utilization:"
echo "     CPU: ${CPU_AVG}%"
echo "     Memory: ${MEM_AVG}%"
echo "     Disk: ${DISK_USAGE}%"
echo

echo "   Recommendations:"
if [ "$CPU_AVG" -gt 70 ]; then
    echo "     🔴 CPU: Consider scaling up (current: ${CPU_AVG}%)"
elif [ "$CPU_AVG" -gt 50 ]; then
    echo "     🟡 CPU: Monitor closely (current: ${CPU_AVG}%)"
else
    echo "     🟢 CPU: Utilization healthy (current: ${CPU_AVG}%)"
fi

if [ "$MEM_AVG" -gt 80 ]; then
    echo "     🔴 Memory: Scale up recommended (current: ${MEM_AVG}%)"
elif [ "$MEM_AVG" -gt 60 ]; then
    echo "     🟡 Memory: Monitor closely (current: ${MEM_AVG}%)"
else
    echo "     🟢 Memory: Utilization healthy (current: ${MEM_AVG}%)"
fi

if [ "$DISK_USAGE" -gt 75 ]; then
    echo "     🔴 Disk: Storage expansion needed (current: ${DISK_USAGE}%)"
elif [ "$DISK_USAGE" -gt 50 ]; then
    echo "     🟡 Disk: Plan for expansion (current: ${DISK_USAGE}%)"
else
    echo "     🟢 Disk: Storage adequate (current: ${DISK_USAGE}%)"
fi
echo

# 6. Cost optimization
echo "6. 💰 Cost Optimization Opportunities"
echo "   Unused indexes: $(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "SELECT count(*) FROM pg_stat_user_indexes WHERE idx_scan = 0;")"
echo "   Old backup files: $(find /backup -name "*.gz" -mtime +90 | wc -l)"
echo "   Log file size: $(du -sh /var/log/perfect21/ | cut -f1)"
echo

echo "✅ Monthly capacity planning report complete"
echo "Next: Review recommendations and plan for next month"
```

## 🚨 Incident Response

### Incident Classification

#### Severity Levels

**Severity 1 - Critical (< 15 minutes response)**
- Complete system outage
- Data loss or corruption
- Security breach
- Database unavailable

**Severity 2 - High (< 30 minutes response)**
- Partial system functionality impaired
- Significant performance degradation
- Authentication failures
- Agent system down

**Severity 3 - Medium (< 2 hours response)**
- Minor functionality issues
- Performance degradation
- Individual agent failures
- Configuration issues

**Severity 4 - Low (< 24 hours response)**
- Cosmetic issues
- Documentation updates
- Enhancement requests
- Non-critical monitoring alerts

### Incident Response Procedures

#### Emergency Response Runbook

```bash
#!/bin/bash
# scripts/incident-response.sh

SEVERITY=$1
DESCRIPTION="$2"

echo "🚨 Perfect21 Incident Response"
echo "============================="
echo "Severity: $SEVERITY"
echo "Description: $DESCRIPTION"
echo "Time: $(date)"
echo "Operator: $(whoami)"
echo

case $SEVERITY in
    "1"|"critical")
        echo "🔴 CRITICAL INCIDENT - Immediate action required"
        echo

        # 1. Assess system status
        echo "1. 🔍 System Assessment:"
        ./scripts/emergency-health-check.sh
        echo

        # 2. Notify stakeholders
        echo "2. 📢 Notifications:"
        echo "   - On-call team alerted"
        echo "   - Status page updated"
        echo "   - Management notified"

        # 3. Begin immediate mitigation
        echo "3. 🛠️ Immediate Actions:"
        echo "   - Check for recent deployments"
        echo "   - Review error logs"
        echo "   - Verify external dependencies"
        echo "   - Consider rollback if needed"

        # 4. Start incident log
        mkdir -p /var/log/incidents
        INCIDENT_LOG="/var/log/incidents/incident-$(date +%Y%m%d-%H%M%S).log"
        cat > $INCIDENT_LOG << EOF
Incident Start: $(date)
Severity: Critical
Description: $DESCRIPTION
Operator: $(whoami)

Timeline:
$(date) - Incident detected
$(date) - Emergency response initiated
EOF
        echo "   - Incident log started: $INCIDENT_LOG"
        ;;

    "2"|"high")
        echo "🟡 HIGH SEVERITY - Urgent attention required"
        echo

        # Similar structure but less urgent
        echo "1. 📊 Status Check:"
        ./scripts/health-check.sh
        echo

        echo "2. 🔍 Investigation:"
        echo "   - Check application logs"
        echo "   - Monitor system metrics"
        echo "   - Verify agent performance"
        echo

        echo "3. 📋 Next Steps:"
        echo "   - Create incident ticket"
        echo "   - Begin detailed analysis"
        echo "   - Plan remediation"
        ;;

    *)
        echo "ℹ️  Standard incident response"
        echo "   - Create ticket in issue tracker"
        echo "   - Assign to appropriate team"
        echo "   - Set appropriate priority"
        ;;
esac

echo
echo "✅ Initial response complete"
echo "Continue with incident-specific procedures"
```

#### Common Incident Scenarios

**Database Connection Failure**
```bash
#!/bin/bash
# runbooks/database-connection-failure.sh

echo "🗄️ Database Connection Failure Runbook"
echo "======================================"

# 1. Verify database status
echo "1. Database Status Check:"
systemctl status postgresql || kubectl get pods -l app=postgres
echo

# 2. Check network connectivity
echo "2. Network Connectivity:"
telnet $DB_HOST $DB_PORT
echo

# 3. Check connection pool
echo "3. Connection Pool Status:"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT * FROM pg_stat_activity;" 2>/dev/null || echo "Connection failed"
echo

# 4. Recovery actions
echo "4. Recovery Actions:"
echo "   Option A: Restart database service"
echo "   sudo systemctl restart postgresql"
echo
echo "   Option B: Restart application (to reset connection pool)"
echo "   docker-compose restart perfect21-api"
echo
echo "   Option C: Check and increase connection limits"
echo "   ALTER SYSTEM SET max_connections = 200;"
echo

# 5. Verification
echo "5. Verification Steps:"
echo "   - Test database connection"
echo "   - Verify application health"
echo "   - Monitor connection count"
echo "   - Check for connection leaks"
```

**High Memory Usage**
```bash
#!/bin/bash
# runbooks/high-memory-usage.sh

echo "💾 High Memory Usage Runbook"
echo "============================"

# 1. Current memory status
echo "1. Memory Status:"
free -h
echo
echo "Top memory consumers:"
ps aux --sort=-%mem | head -10
echo

# 2. Check for memory leaks
echo "2. Memory Leak Detection:"
if command -v pmap >/dev/null 2>&1; then
    NODE_PID=$(pgrep -f "node.*perfect21")
    if [ -n "$NODE_PID" ]; then
        echo "   Node.js memory map:"
        pmap -d $NODE_PID | tail -1
    fi
fi
echo

# 3. Application-specific checks
echo "3. Application Memory Analysis:"
curl -s http://localhost:3000/metrics | grep -E "(heap|memory)" | head -10
echo

# 4. Immediate actions
echo "4. Immediate Actions:"
echo "   Option A: Restart application"
echo "   docker-compose restart perfect21-api"
echo
echo "   Option B: Scale horizontally"
echo "   kubectl scale deployment perfect21-api --replicas=6"
echo
echo "   Option C: Clear caches"
echo "   redis-cli -h $REDIS_HOST -p $REDIS_PORT FLUSHDB"
echo

# 5. Long-term solutions
echo "5. Long-term Solutions:"
echo "   - Review connection pool settings"
echo "   - Implement memory monitoring"
echo "   - Consider memory limits"
echo "   - Profile application for leaks"
```

### Post-Incident Analysis

#### Incident Post-Mortem Template
```markdown
# Incident Post-Mortem

## Incident Summary
- **Date**: YYYY-MM-DD
- **Duration**: X hours Y minutes
- **Severity**: [1-4]
- **Impact**: Brief description of user impact
- **Root Cause**: Brief summary of what went wrong

## Timeline
| Time | Event |
|------|-------|
| HH:MM | Incident detected |
| HH:MM | Initial response started |
| HH:MM | Root cause identified |
| HH:MM | Fix implemented |
| HH:MM | Service restored |
| HH:MM | Incident closed |

## Root Cause Analysis
### What Happened
Detailed explanation of the technical issue

### Why It Happened
- Primary cause
- Contributing factors
- Why existing safeguards didn't prevent it

### How We Detected It
- Monitoring alerts
- User reports
- Internal discovery

## Impact Assessment
### User Impact
- Number of affected users
- Duration of impact
- Functionality affected

### Business Impact
- Revenue impact (if applicable)
- Reputation impact
- Compliance implications

## Response Evaluation
### What Went Well
- Effective monitoring
- Quick response time
- Good communication

### What Could Be Improved
- Detection time
- Communication clarity
- Recovery speed

## Action Items
| Action | Owner | Due Date | Priority |
|--------|-------|----------|----------|
| Improve monitoring | DevOps | YYYY-MM-DD | High |
| Update runbook | SRE | YYYY-MM-DD | Medium |
| Add automated tests | Engineering | YYYY-MM-DD | High |

## Lessons Learned
Key takeaways for future prevention
```

## 🔄 Backup & Recovery

### Backup Strategies

#### Automated Backup System
```bash
#!/bin/bash
# scripts/automated-backup.sh

BACKUP_TYPE=$1  # daily, weekly, monthly
BACKUP_BASE="/backup"
DATE=$(date +%Y%m%d_%H%M%S)
S3_BUCKET="perfect21-backups"

echo "🗄️ Perfect21 Automated Backup"
echo "============================="
echo "Type: $BACKUP_TYPE"
echo "Date: $DATE"
echo

case $BACKUP_TYPE in
    "daily")
        RETENTION_DAYS=7
        BACKUP_DIR="$BACKUP_BASE/daily"
        ;;
    "weekly")
        RETENTION_DAYS=30
        BACKUP_DIR="$BACKUP_BASE/weekly"
        ;;
    "monthly")
        RETENTION_DAYS=365
        BACKUP_DIR="$BACKUP_BASE/monthly"
        ;;
    *)
        echo "Usage: $0 {daily|weekly|monthly}"
        exit 1
        ;;
esac

mkdir -p $BACKUP_DIR

# 1. Database backup
echo "1. 🗄️ Database Backup"
DB_BACKUP="$BACKUP_DIR/database_${BACKUP_TYPE}_${DATE}.sql"
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $DB_BACKUP

if [ $? -eq 0 ]; then
    gzip $DB_BACKUP
    echo "   ✅ Database backup completed: $DB_BACKUP.gz"

    # Verify backup
    if zcat $DB_BACKUP.gz | head -10 | grep -q "PostgreSQL database dump"; then
        echo "   ✅ Backup verification passed"
    else
        echo "   ❌ Backup verification failed"
        exit 1
    fi
else
    echo "   ❌ Database backup failed"
    exit 1
fi
echo

# 2. Configuration backup
echo "2. ⚙️ Configuration Backup"
CONFIG_BACKUP="$BACKUP_DIR/config_${BACKUP_TYPE}_${DATE}.tar.gz"
tar -czf $CONFIG_BACKUP \
    /app/.env \
    /app/config/ \
    /app/k8s/ \
    /app/docker-compose.yml \
    /etc/nginx/ \
    2>/dev/null

echo "   ✅ Configuration backup completed: $CONFIG_BACKUP"
echo

# 3. Application data backup
echo "3. 📁 Application Data Backup"
if [ -d "/app/uploads" ]; then
    DATA_BACKUP="$BACKUP_DIR/data_${BACKUP_TYPE}_${DATE}.tar.gz"
    tar -czf $DATA_BACKUP /app/uploads/ /app/logs/ 2>/dev/null
    echo "   ✅ Application data backup completed: $DATA_BACKUP"
fi
echo

# 4. Upload to cloud storage
echo "4. ☁️ Cloud Storage Upload"
if command -v aws >/dev/null 2>&1 && [ -n "$S3_BUCKET" ]; then
    aws s3 sync $BACKUP_DIR s3://$S3_BUCKET/$BACKUP_TYPE/ --exclude "*" --include "*${DATE}*"
    echo "   ✅ Backups uploaded to S3"
else
    echo "   ⚠️ AWS CLI not configured or S3 bucket not set"
fi
echo

# 5. Cleanup old backups
echo "5. 🧹 Cleanup Old Backups"
find $BACKUP_DIR -name "*${BACKUP_TYPE}*" -mtime +$RETENTION_DAYS -delete
DELETED_COUNT=$(find $BACKUP_DIR -name "*${BACKUP_TYPE}*" -mtime +$RETENTION_DAYS 2>/dev/null | wc -l)
echo "   ✅ Cleaned up old backups (retention: $RETENTION_DAYS days)"
echo

# 6. Backup report
echo "6. 📊 Backup Report"
BACKUP_SIZE=$(du -sh $BACKUP_DIR/*${DATE}* | awk '{total+=$1} END {print total}')
echo "   Total backup size: $BACKUP_SIZE"
echo "   Files created: $(ls -1 $BACKUP_DIR/*${DATE}* | wc -l)"
echo "   Storage location: $BACKUP_DIR"
if [ -n "$S3_BUCKET" ]; then
    echo "   Cloud backup: s3://$S3_BUCKET/$BACKUP_TYPE/"
fi

# Log backup completion
echo "$(date): $BACKUP_TYPE backup completed successfully" >> /var/log/perfect21/backup.log

echo
echo "✅ Backup process completed successfully"
```

#### Recovery Procedures
```bash
#!/bin/bash
# scripts/disaster-recovery.sh

RECOVERY_TYPE=$1
BACKUP_DATE=$2

echo "🚑 Perfect21 Disaster Recovery"
echo "=============================="
echo "Recovery Type: $RECOVERY_TYPE"
echo "Backup Date: $BACKUP_DATE"
echo "Start Time: $(date)"
echo

case $RECOVERY_TYPE in
    "database")
        echo "🗄️ Database Recovery Procedure"
        echo "==============================="

        # 1. Confirm operation
        read -p "⚠️  This will replace the current database. Continue? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo "Operation cancelled"
            exit 1
        fi

        # 2. Stop application
        echo "1. Stopping application..."
        docker-compose stop perfect21-api
        echo "   ✅ Application stopped"

        # 3. Backup current database
        echo "2. Creating safety backup..."
        SAFETY_BACKUP="/backup/safety/database_$(date +%Y%m%d_%H%M%S).sql"
        mkdir -p /backup/safety
        pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $SAFETY_BACKUP
        gzip $SAFETY_BACKUP
        echo "   ✅ Safety backup created: $SAFETY_BACKUP.gz"

        # 4. Restore from backup
        echo "3. Restoring database..."
        RESTORE_FILE="/backup/daily/database_daily_${BACKUP_DATE}.sql.gz"
        if [ -f "$RESTORE_FILE" ]; then
            # Drop and recreate database
            psql -h $DB_HOST -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
            psql -h $DB_HOST -U postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

            # Restore data
            zcat $RESTORE_FILE | psql -h $DB_HOST -U $DB_USER -d $DB_NAME
            echo "   ✅ Database restored from: $RESTORE_FILE"
        else
            echo "   ❌ Backup file not found: $RESTORE_FILE"
            exit 1
        fi

        # 5. Start application
        echo "4. Starting application..."
        docker-compose start perfect21-api
        sleep 30

        # 6. Verify recovery
        echo "5. Verifying recovery..."
        if curl -f http://localhost:3000/api/v1/health >/dev/null 2>&1; then
            echo "   ✅ Application health check passed"
        else
            echo "   ❌ Application health check failed"
            exit 1
        fi
        ;;

    "full")
        echo "🏗️ Full System Recovery Procedure"
        echo "================================="

        # This would include database, configuration, and data recovery
        echo "1. Restoring configuration..."
        ./scripts/disaster-recovery.sh config $BACKUP_DATE

        echo "2. Restoring database..."
        ./scripts/disaster-recovery.sh database $BACKUP_DATE

        echo "3. Restoring application data..."
        ./scripts/disaster-recovery.sh data $BACKUP_DATE

        echo "4. Restarting all services..."
        docker-compose down
        docker-compose up -d
        ;;

    *)
        echo "Usage: $0 {database|config|data|full} BACKUP_DATE"
        echo "Example: $0 database 20240115_093000"
        exit 1
        ;;
esac

echo
echo "✅ Recovery completed at $(date)"
echo "Please verify system functionality"
```

## 📞 Support & Escalation

### On-Call Procedures

#### Alert Response Matrix

| Alert Type | Severity | Response Time | Escalation |
|------------|----------|---------------|------------|
| Service Down | Critical | 5 minutes | Immediate |
| Database Down | Critical | 5 minutes | Immediate |
| High Error Rate | High | 15 minutes | 30 minutes |
| High Latency | Medium | 30 minutes | 2 hours |
| Disk Space | Medium | 1 hour | 4 hours |
| Certificate Expiry | Low | 24 hours | 72 hours |

#### Contact Information

**Primary On-Call**
- Phone: +1-555-ONCALL1
- Email: oncall-primary@perfect21.com
- Slack: @oncall-primary

**Secondary On-Call**
- Phone: +1-555-ONCALL2
- Email: oncall-secondary@perfect21.com
- Slack: @oncall-secondary

**Engineering Manager**
- Phone: +1-555-ENG-MGR
- Email: eng-manager@perfect21.com
- Slack: @eng-manager

**DevOps Lead**
- Phone: +1-555-DEVOPS
- Email: devops-lead@perfect21.com
- Slack: @devops-lead

### Communication Templates

#### Status Page Update
```
Investigating - We are currently investigating reports of [ISSUE DESCRIPTION].
We will provide updates as we learn more.

Update - We have identified the cause of [ISSUE DESCRIPTION] as [ROOT CAUSE].
Our team is working on a fix.

Resolved - The issue with [ISSUE DESCRIPTION] has been resolved.
All systems are now operating normally.
```

#### Incident Communication
```
Subject: [SEVERITY] Perfect21 Incident - [BRIEF DESCRIPTION]

Team,

We are experiencing [DESCRIPTION] starting at [TIME].

Impact: [USER/BUSINESS IMPACT]
Current Status: [INVESTIGATING/MITIGATING/RESOLVED]
ETA for Resolution: [TIME ESTIMATE]
Next Update: [TIME]

Actions Being Taken:
- [ACTION 1]
- [ACTION 2]

For updates, monitor #incidents channel.

[YOUR NAME]
On-Call Engineer
```

---

**Perfect21 Operations Guide** - Complete operational procedures for maintaining and monitoring the AI-driven development workflow system.

*Last updated: 2024-01-15*
*Version: 4.0.0*