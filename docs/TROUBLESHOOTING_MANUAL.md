# Perfect21 Troubleshooting Manual

## 🎯 Overview

This comprehensive troubleshooting manual provides step-by-step solutions for common issues encountered with the Perfect21 (Claude Enhancer) system. It covers system-level problems, application-specific issues, performance troubleshooting, and emergency recovery procedures.

## 🔍 Diagnostic Tools

### Quick Diagnostic Commands

```bash
#!/bin/bash
# scripts/quick-diagnostics.sh

echo "🔍 Perfect21 Quick Diagnostics"
echo "============================="
echo "Timestamp: $(date)"
echo "Operator: $(whoami)"
echo

# System health overview
echo "1. 🏥 System Health:"
curl -s http://localhost:3000/api/v1/health | jq '.' 2>/dev/null || echo "❌ API not responding"
echo

# Resource utilization
echo "2. 💻 Resource Usage:"
echo "   CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')"
echo "   Memory: $(free -h | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
echo "   Disk: $(df -h / | awk 'NR==2{print $5}')"
echo "   Load: $(uptime | awk -F'load average:' '{print $2}')"
echo

# Service status
echo "3. 🔄 Service Status:"
if command -v docker >/dev/null 2>&1; then
    echo "   Docker containers:"
    docker ps --filter "name=perfect21" --format "table {{.Names}}\t{{.Status}}"
elif command -v systemctl >/dev/null 2>&1; then
    echo "   System services:"
    systemctl is-active perfect21-api postgresql redis-server nginx
fi
echo

# Network connectivity
echo "4. 🌐 Network Tests:"
echo "   Database: $(timeout 3 bash -c "</dev/tcp/$DB_HOST/$DB_PORT" 2>/dev/null && echo "✅ Connected" || echo "❌ Failed")"
echo "   Redis: $(timeout 3 redis-cli -h $REDIS_HOST -p $REDIS_PORT --no-auth-warning -a $REDIS_PASSWORD ping 2>/dev/null || echo "❌ Failed")"
echo

# Recent errors
echo "5. 🚨 Recent Errors (last 10):"
if [ -f "/var/log/perfect21/app.log" ]; then
    grep -i "error" /var/log/perfect21/app.log | tail -10 | cut -c1-100
else
    echo "   Log file not found"
fi

echo
echo "✅ Quick diagnostics complete"
```

### System Information Gathering

```bash
#!/bin/bash
# scripts/collect-system-info.sh

INFO_DIR="/tmp/perfect21-diagnostics-$(date +%Y%m%d-%H%M%S)"
mkdir -p $INFO_DIR

echo "📊 Collecting system information..."
echo "Output directory: $INFO_DIR"

# System information
echo "System info..."
{
    echo "=== System Information ==="
    uname -a
    cat /etc/os-release
    uptime
    whoami
    pwd
} > $INFO_DIR/system.txt

# Resource usage
echo "Resource usage..."
{
    echo "=== CPU Information ==="
    lscpu
    echo
    echo "=== Memory Information ==="
    free -h
    echo
    echo "=== Disk Information ==="
    df -h
    echo
    echo "=== Network Information ==="
    ip addr show
} > $INFO_DIR/resources.txt

# Process information
echo "Process information..."
{
    echo "=== Running Processes ==="
    ps aux | grep -E "(node|postgres|redis|nginx)"
    echo
    echo "=== Top Processes ==="
    top -bn1 | head -20
} > $INFO_DIR/processes.txt

# Application logs
echo "Application logs..."
if [ -f "/var/log/perfect21/app.log" ]; then
    tail -1000 /var/log/perfect21/app.log > $INFO_DIR/app.log
fi

# System logs
echo "System logs..."
journalctl -u perfect21-api --no-pager -n 100 > $INFO_DIR/service.log 2>/dev/null

# Docker information (if applicable)
if command -v docker >/dev/null 2>&1; then
    echo "Docker information..."
    {
        echo "=== Docker Containers ==="
        docker ps -a
        echo
        echo "=== Docker Images ==="
        docker images
        echo
        echo "=== Docker System Info ==="
        docker system df
    } > $INFO_DIR/docker.txt
fi

# Kubernetes information (if applicable)
if command -v kubectl >/dev/null 2>&1; then
    echo "Kubernetes information..."
    {
        echo "=== Pods ==="
        kubectl get pods -n perfect21
        echo
        echo "=== Services ==="
        kubectl get services -n perfect21
        echo
        echo "=== Events ==="
        kubectl get events -n perfect21 --sort-by='.lastTimestamp'
    } > $INFO_DIR/kubernetes.txt
fi

# Configuration files
echo "Configuration files..."
if [ -f "/app/.env" ]; then
    grep -v -E "(PASSWORD|SECRET|KEY)" /app/.env > $INFO_DIR/config.txt
fi

# Create archive
tar -czf "$INFO_DIR.tar.gz" -C /tmp "$(basename $INFO_DIR)"
rm -rf $INFO_DIR

echo "✅ System information collected: $INFO_DIR.tar.gz"
echo "Share this file with support for detailed analysis"
```

## 🚨 Common Issues & Solutions

### Application Issues

#### Issue: API Not Responding

**Symptoms:**
- HTTP requests timeout
- Health check endpoint fails
- Application appears frozen

**Diagnosis:**
```bash
# Check if process is running
ps aux | grep -E "node.*perfect21"

# Check port availability
netstat -tlnp | grep :3000

# Check application logs
tail -f /var/log/perfect21/app.log

# Test application directly
curl -v http://localhost:3000/api/v1/health
```

**Solutions:**

1. **Restart Application Service**
```bash
# Docker Compose
docker-compose restart perfect21-api

# Kubernetes
kubectl rollout restart deployment/perfect21-api -n perfect21

# Systemd
sudo systemctl restart perfect21-api
```

2. **Check Resource Constraints**
```bash
# Check memory usage
free -h
docker stats perfect21-api

# Check disk space
df -h

# Check file descriptors
lsof -p $(pgrep -f "node.*perfect21") | wc -l
```

3. **Investigate Application Errors**
```bash
# Check for uncaught exceptions
grep -i "uncaught\|unhandled" /var/log/perfect21/app.log

# Check for memory leaks
curl http://localhost:3000/metrics | grep heap

# Check event loop lag
curl http://localhost:3000/metrics | grep eventloop
```

#### Issue: Agent Selection Failures

**Symptoms:**
```json
{
  "error": {
    "code": "AGENT_SELECTION_FAILED",
    "message": "Unable to select appropriate agents for task"
  }
}
```

**Diagnosis:**
```bash
# Check agent configuration
cat /app/config/agents.yaml

# Verify Claude Enhancer settings
grep CLAUDE_ENHANCER /app/.env

# Check agent status endpoint
curl http://localhost:3000/api/v1/agents/status
```

**Solutions:**

1. **Validate Agent Configuration**
```bash
# Check configuration syntax
yamllint /app/config/agents.yaml

# Validate agent definitions
./scripts/validate-agents.sh

# Reset agent cache
redis-cli -h $REDIS_HOST -p $REDIS_PORT FLUSHDB
```

2. **Update Agent Rules**
```bash
# Reload configuration
kubectl create configmap perfect21-agents --from-file=agents.yaml -n perfect21 --dry-run=client -o yaml | kubectl apply -f -

# Restart application to pick up changes
kubectl rollout restart deployment/perfect21-api -n perfect21
```

3. **Check Task Analysis**
```bash
# Test task analysis endpoint
curl -X POST http://localhost:3000/api/v1/tasks/analyze \
  -H "Content-Type: application/json" \
  -d '{"task": "Create user authentication system"}'
```

#### Issue: High Response Times

**Symptoms:**
- API requests take > 1 second
- User interface feels sluggish
- Timeout errors

**Diagnosis:**
```bash
# Check response time metrics
curl http://localhost:3000/metrics | grep http_request_duration

# Monitor live requests
tail -f /var/log/nginx/access.log | awk '{print $7, $NF}'

# Check database performance
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;"
```

**Solutions:**

1. **Database Optimization**
```bash
# Update statistics
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "ANALYZE;"

# Check for missing indexes
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename IN ('users', 'tasks', 'agents');"

# Add missing indexes
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_tasks_status ON tasks(status);
CREATE INDEX CONCURRENTLY idx_tasks_created_at ON tasks(created_at);"
```

2. **Application Performance**
```bash
# Check connection pool
curl http://localhost:3000/metrics | grep pool

# Monitor garbage collection
node --trace-gc /app/server.js > gc.log 2>&1 &

# Profile application
node --prof /app/server.js
```

3. **Infrastructure Scaling**
```bash
# Scale horizontally
kubectl scale deployment perfect21-api --replicas=6 -n perfect21

# Increase resource limits
kubectl patch deployment perfect21-api -n perfect21 -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "perfect21-api",
          "resources": {
            "limits": {"memory": "4Gi", "cpu": "2000m"},
            "requests": {"memory": "2Gi", "cpu": "1000m"}
          }
        }]
      }
    }
  }
}'
```

### Database Issues

#### Issue: Database Connection Refused

**Symptoms:**
```
Error: connect ECONNREFUSED 127.0.0.1:5432
```

**Diagnosis:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql
kubectl get pods -l app=postgres -n perfect21

# Test connectivity
telnet $DB_HOST $DB_PORT
nc -zv $DB_HOST $DB_PORT

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*.log
kubectl logs -f deployment/postgres -n perfect21
```

**Solutions:**

1. **Service Recovery**
```bash
# Restart PostgreSQL service
sudo systemctl restart postgresql

# For containerized deployments
docker-compose restart postgres
kubectl rollout restart deployment/postgres -n perfect21
```

2. **Configuration Check**
```bash
# Verify PostgreSQL configuration
sudo grep -E "(listen_addresses|port)" /etc/postgresql/*/main/postgresql.conf

# Check authentication settings
sudo grep -v "^#" /etc/postgresql/*/main/pg_hba.conf

# Verify firewall settings
sudo ufw status | grep 5432
```

3. **Connection Pool Reset**
```bash
# Restart application to reset connection pool
docker-compose restart perfect21-api

# Check connection count
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT count(*) as connections, state
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY state;"
```

#### Issue: Database Performance Problems

**Symptoms:**
- Slow query execution
- Connection timeouts
- High CPU usage on database server

**Diagnosis:**
```sql
-- Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check database size
SELECT pg_size_pretty(pg_database_size(current_database()));

-- Check table sizes
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC;

-- Check index usage
SELECT
    indexname,
    indexrelname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

**Solutions:**

1. **Query Optimization**
```sql
-- Analyze query plans
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

-- Update table statistics
ANALYZE users;
ANALYZE tasks;
ANALYZE agents;

-- Vacuum tables
VACUUM ANALYZE users;
VACUUM ANALYZE tasks;
```

2. **Index Management**
```sql
-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_users_status ON users(status);
CREATE INDEX CONCURRENTLY idx_tasks_user_id ON tasks(user_id);
CREATE INDEX CONCURRENTLY idx_tasks_created_at ON tasks(created_at);

-- Remove unused indexes
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0;
```

3. **Configuration Tuning**
```sql
-- Increase work memory
ALTER SYSTEM SET work_mem = '256MB';

-- Increase shared buffers
ALTER SYSTEM SET shared_buffers = '512MB';

-- Increase effective cache size
ALTER SYSTEM SET effective_cache_size = '2GB';

-- Reload configuration
SELECT pg_reload_conf();
```

### Redis Issues

#### Issue: Redis Connection Failures

**Symptoms:**
- Session data lost
- Cache misses
- Authentication failures

**Diagnosis:**
```bash
# Check Redis status
redis-cli -h $REDIS_HOST -p $REDIS_PORT ping
systemctl status redis-server

# Check Redis logs
tail -f /var/log/redis/redis-server.log
kubectl logs -f deployment/redis -n perfect21

# Check memory usage
redis-cli -h $REDIS_HOST -p $REDIS_PORT info memory
```

**Solutions:**

1. **Service Recovery**
```bash
# Restart Redis
sudo systemctl restart redis-server
docker-compose restart redis
kubectl rollout restart deployment/redis -n perfect21

# Clear Redis data (if corrupted)
redis-cli -h $REDIS_HOST -p $REDIS_PORT FLUSHALL
```

2. **Memory Management**
```bash
# Check Redis memory usage
redis-cli -h $REDIS_HOST -p $REDIS_PORT info memory

# Set memory limit
redis-cli -h $REDIS_HOST -p $REDIS_PORT CONFIG SET maxmemory 1gb
redis-cli -h $REDIS_HOST -p $REDIS_PORT CONFIG SET maxmemory-policy allkeys-lru

# Monitor key expiration
redis-cli -h $REDIS_HOST -p $REDIS_PORT info keyspace
```

3. **Connection Pool Tuning**
```javascript
// Update Redis client configuration
const redis = new Redis({
  host: process.env.REDIS_HOST,
  port: process.env.REDIS_PORT,
  password: process.env.REDIS_PASSWORD,
  retryDelayOnFailover: 100,
  maxRetriesPerRequest: 3,
  lazyConnect: true,
  keepAlive: 30000,
  family: 4,
  connectTimeout: 10000,
  commandTimeout: 5000,
});
```

### Authentication & Authorization Issues

#### Issue: JWT Token Errors

**Symptoms:**
```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "JWT token invalid or malformed"
  }
}
```

**Diagnosis:**
```bash
# Check JWT configuration
grep JWT_ /app/.env

# Test token generation
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}'

# Verify token structure
echo "JWT_TOKEN_HERE" | cut -d. -f2 | base64 -d | jq '.'
```

**Solutions:**

1. **Token Configuration**
```bash
# Regenerate JWT secrets
export JWT_ACCESS_SECRET=$(openssl rand -hex 64)
export JWT_REFRESH_SECRET=$(openssl rand -hex 64)

# Update environment
echo "JWT_ACCESS_SECRET=$JWT_ACCESS_SECRET" >> /app/.env
echo "JWT_REFRESH_SECRET=$JWT_REFRESH_SECRET" >> /app/.env

# Restart application
docker-compose restart perfect21-api
```

2. **Clock Synchronization**
```bash
# Check system time
date
timedatectl status

# Synchronize time
sudo ntpdate -s time.nist.gov
sudo systemctl restart ntp
```

3. **Token Validation Testing**
```bash
# Test token with different timestamps
node -e "
const jwt = require('jsonwebtoken');
const token = jwt.sign({userId: 123}, process.env.JWT_ACCESS_SECRET, {expiresIn: '15m'});
console.log('Generated token:', token);
console.log('Decoded:', jwt.verify(token, process.env.JWT_ACCESS_SECRET));
"
```

#### Issue: Session Management Problems

**Symptoms:**
- Users logged out unexpectedly
- Session data not persisting
- Multiple session conflicts

**Diagnosis:**
```bash
# Check session storage
redis-cli -h $REDIS_HOST -p $REDIS_PORT KEYS "session:*" | wc -l

# Check session configuration
grep SESSION_ /app/.env

# Monitor session creation/destruction
redis-cli -h $REDIS_HOST -p $REDIS_PORT MONITOR | grep session
```

**Solutions:**

1. **Session Store Cleanup**
```bash
# Remove expired sessions
redis-cli -h $REDIS_HOST -p $REDIS_PORT EVAL "
for i, name in ipairs(redis.call('KEYS', 'session:*')) do
  local ttl = redis.call('TTL', name)
  if ttl == -1 then
    redis.call('DEL', name)
  end
end
return 'OK'
" 0

# Set proper TTL for sessions
redis-cli -h $REDIS_HOST -p $REDIS_PORT EVAL "
for i, name in ipairs(redis.call('KEYS', 'session:*')) do
  redis.call('EXPIRE', name, 86400)
end
return 'OK'
" 0
```

2. **Session Configuration**
```javascript
// Update session middleware configuration
app.use(session({
  store: new RedisStore({
    client: redisClient,
    prefix: 'session:',
    ttl: 24 * 60 * 60, // 24 hours
  }),
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  rolling: true,
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
    sameSite: 'strict',
  },
}));
```

### Performance Issues

#### Issue: High CPU Usage

**Symptoms:**
- System becomes unresponsive
- High load average
- CPU usage > 80%

**Diagnosis:**
```bash
# Check CPU usage by process
top -p $(pgrep -f "node.*perfect21")
htop

# Check CPU usage over time
sar -u 1 60

# Profile application CPU usage
node --prof /app/server.js
node --prof-process isolate-*.log > cpu-profile.txt
```

**Solutions:**

1. **Application Optimization**
```bash
# Check for CPU-intensive operations
curl http://localhost:3000/metrics | grep cpu

# Monitor event loop lag
curl http://localhost:3000/metrics | grep eventloop

# Optimize password hashing
# Reduce bcrypt rounds in production
echo "BCRYPT_ROUNDS=10" >> /app/.env
```

2. **Infrastructure Scaling**
```bash
# Scale horizontally
kubectl scale deployment perfect21-api --replicas=4 -n perfect21

# Increase CPU limits
kubectl patch deployment perfect21-api -n perfect21 -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "perfect21-api",
          "resources": {
            "limits": {"cpu": "2000m"},
            "requests": {"cpu": "1000m"}
          }
        }]
      }
    }
  }
}'
```

3. **System Optimization**
```bash
# Adjust system limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize kernel parameters
echo "net.core.somaxconn = 65536" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65536" >> /etc/sysctl.conf
sysctl -p
```

#### Issue: Memory Leaks

**Symptoms:**
- Memory usage constantly increasing
- Application crashes with OOM errors
- Slow performance over time

**Diagnosis:**
```bash
# Monitor memory usage
watch -n 5 "free -h && ps aux --sort=-%mem | head -10"

# Check application memory metrics
curl http://localhost:3000/metrics | grep -E "(heap|memory)"

# Generate heap dump
kill -USR2 $(pgrep -f "node.*perfect21")
# Heap dump saved to /tmp/heapdump-*.heapsnapshot
```

**Solutions:**

1. **Memory Monitoring**
```javascript
// Add memory monitoring to application
const v8 = require('v8');
const heapStats = v8.getHeapStatistics();

setInterval(() => {
  const memUsage = process.memoryUsage();
  console.log('Memory Usage:', {
    rss: Math.round(memUsage.rss / 1024 / 1024) + 'MB',
    heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024) + 'MB',
    heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024) + 'MB',
    external: Math.round(memUsage.external / 1024 / 1024) + 'MB',
  });
}, 30000);
```

2. **Connection Management**
```javascript
// Ensure proper connection cleanup
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, closing connections...');

  // Close database connections
  await db.close();

  // Close Redis connections
  await redis.disconnect();

  // Close HTTP server
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});
```

3. **Memory Limits**
```bash
# Set Node.js memory limits
node --max-old-space-size=2048 /app/server.js

# Set container memory limits
docker run --memory=2g perfect21/api

# Kubernetes memory limits
resources:
  limits:
    memory: "2Gi"
  requests:
    memory: "1Gi"
```

## 🔧 Recovery Procedures

### Emergency Recovery

#### Complete System Recovery

```bash
#!/bin/bash
# scripts/emergency-recovery.sh

echo "🚑 Perfect21 Emergency Recovery"
echo "==============================="
echo "Starting emergency recovery at $(date)"

# 1. Stop all services
echo "1. Stopping all services..."
docker-compose down 2>/dev/null
kubectl scale deployment --all --replicas=0 -n perfect21 2>/dev/null
sudo systemctl stop perfect21-api postgresql redis-server nginx 2>/dev/null

# 2. Check system resources
echo "2. Checking system resources..."
echo "   Disk space: $(df -h / | awk 'NR==2{print $5}')"
echo "   Memory: $(free -h | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
echo "   Load: $(uptime | awk -F'load average:' '{print $2}')"

# 3. Clean up if needed
echo "3. Cleaning up resources..."
# Clean Docker if needed
docker system prune -f 2>/dev/null

# Clean logs if disk space is low
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "   High disk usage detected, cleaning logs..."
    find /var/log -name "*.log.*" -mtime +7 -delete
    journalctl --vacuum-time=7d
fi

# 4. Restore from backup if needed
if [ "$1" = "--restore-backup" ]; then
    echo "4. Restoring from backup..."
    LATEST_BACKUP=$(ls -t /backup/daily/database_daily_*.sql.gz | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        echo "   Restoring database from: $LATEST_BACKUP"
        zcat "$LATEST_BACKUP" | psql -h $DB_HOST -U $DB_USER -d $DB_NAME
    fi
fi

# 5. Start core services
echo "5. Starting core services..."
sudo systemctl start postgresql redis-server
sleep 10

# 6. Verify database connectivity
echo "6. Verifying database..."
if psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1;" >/dev/null 2>&1; then
    echo "   ✅ Database accessible"
else
    echo "   ❌ Database connection failed"
    exit 1
fi

# 7. Start application
echo "7. Starting application..."
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose up -d
elif command -v kubectl >/dev/null 2>&1; then
    kubectl scale deployment --all --replicas=3 -n perfect21
else
    sudo systemctl start perfect21-api nginx
fi

# 8. Wait and verify
echo "8. Verifying recovery..."
sleep 30
for i in {1..5}; do
    if curl -f http://localhost:3000/api/v1/health >/dev/null 2>&1; then
        echo "   ✅ Application responding"
        break
    else
        echo "   ⏳ Waiting for application... ($i/5)"
        sleep 10
    fi
done

# 9. Final verification
echo "9. Final system check..."
./scripts/quick-diagnostics.sh

echo
echo "✅ Emergency recovery completed at $(date)"
echo "Monitor system closely for next 30 minutes"
```

#### Database Emergency Recovery

```bash
#!/bin/bash
# scripts/emergency-db-recovery.sh

echo "🗄️ Database Emergency Recovery"
echo "============================="

# 1. Check database status
if psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ Database is accessible"
    echo "This script is for emergency recovery only"
    read -p "Continue anyway? (yes/no): " confirm
    [ "$confirm" != "yes" ] && exit 1
else
    echo "❌ Database not accessible - proceeding with recovery"
fi

# 2. Stop application
echo "Stopping application services..."
docker-compose stop perfect21-api 2>/dev/null
kubectl scale deployment perfect21-api --replicas=0 -n perfect21 2>/dev/null

# 3. Check PostgreSQL service
echo "Checking PostgreSQL service..."
if ! systemctl is-active postgresql >/dev/null 2>&1; then
    echo "Starting PostgreSQL..."
    sudo systemctl start postgresql
    sleep 10
fi

# 4. Try to repair database
echo "Attempting database repair..."
sudo -u postgres pg_resetwal -f /var/lib/postgresql/*/main/ 2>/dev/null || true

# 5. Create new database if needed
echo "Checking database existence..."
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "Creating new database..."
    sudo -u postgres createdb $DB_NAME
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
fi

# 6. Restore from latest backup
echo "Finding latest backup..."
LATEST_BACKUP=$(ls -t /backup/*/database_*_*.sql.gz 2>/dev/null | head -1)
if [ -n "$LATEST_BACKUP" ]; then
    echo "Restoring from: $LATEST_BACKUP"
    zcat "$LATEST_BACKUP" | psql -h $DB_HOST -U $DB_USER -d $DB_NAME
    echo "✅ Database restored"
else
    echo "❌ No backup found - initializing empty database"
    # Apply schema
    if [ -f "/app/database/schema.sql" ]; then
        psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f /app/database/schema.sql
    fi
fi

# 7. Verify recovery
echo "Verifying database recovery..."
TABLE_COUNT=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "
SELECT count(*)
FROM information_schema.tables
WHERE table_schema = 'public';" 2>/dev/null || echo "0")

echo "Tables found: $TABLE_COUNT"
if [ "$TABLE_COUNT" -gt 0 ]; then
    echo "✅ Database recovery successful"
else
    echo "❌ Database recovery failed"
    exit 1
fi

# 8. Restart application
echo "Restarting application..."
docker-compose start perfect21-api 2>/dev/null
kubectl scale deployment perfect21-api --replicas=3 -n perfect21 2>/dev/null

echo "✅ Database emergency recovery completed"
```

### Data Recovery Procedures

#### Log Analysis for Issue Investigation

```bash
#!/bin/bash
# scripts/analyze-issue.sh

ISSUE_TYPE=$1
TIME_RANGE=${2:-"1 hour ago"}

echo "🔍 Perfect21 Issue Analysis"
echo "=========================="
echo "Issue Type: $ISSUE_TYPE"
echo "Time Range: $TIME_RANGE"
echo "Analysis Time: $(date)"
echo

case $ISSUE_TYPE in
    "performance")
        echo "📊 Performance Issue Analysis"
        echo "============================"

        # Response time analysis
        echo "1. Response Time Analysis:"
        if [ -f "/var/log/nginx/access.log" ]; then
            awk -v since="$(date -d "$TIME_RANGE" +%s)" '
            {
                time_str = $4
                gsub(/\[|\//, " ", time_str)
                cmd = "date -d \"" time_str "\" +%s"
                cmd | getline epoch
                close(cmd)

                if (epoch >= since) {
                    response_time = $NF
                    if (response_time ~ /^[0-9.]+$/) {
                        total += response_time
                        count++
                        if (response_time > max) max = response_time
                        if (min == 0 || response_time < min) min = response_time
                    }
                }
            }
            END {
                if (count > 0) {
                    print "   Total requests: " count
                    print "   Average response time: " total/count "s"
                    print "   Min response time: " min "s"
                    print "   Max response time: " max "s"
                } else {
                    print "   No data found for time range"
                }
            }' /var/log/nginx/access.log
        fi
        echo

        # Database performance
        echo "2. Database Performance:"
        psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
        SELECT
            query,
            calls,
            total_time,
            mean_time,
            rows
        FROM pg_stat_statements
        WHERE last_call >= NOW() - INTERVAL '$TIME_RANGE'
        ORDER BY mean_time DESC
        LIMIT 10;"
        ;;

    "errors")
        echo "🚨 Error Analysis"
        echo "================="

        # Application errors
        echo "1. Application Errors:"
        if [ -f "/var/log/perfect21/app.log" ]; then
            SINCE_TIMESTAMP=$(date -d "$TIME_RANGE" '+%Y-%m-%d %H:%M:%S')
            awk -v since="$SINCE_TIMESTAMP" '
            /ERROR|error/ && $0 >= since {
                print "   " $0
            }' /var/log/perfect21/app.log | tail -20
        fi
        echo

        # System errors
        echo "2. System Errors:"
        journalctl --since "$TIME_RANGE" --priority=err --no-pager | head -20
        ;;

    "authentication")
        echo "🔐 Authentication Issue Analysis"
        echo "==============================="

        # Failed authentication attempts
        echo "1. Failed Authentications:"
        grep -E "authentication.*failed|invalid.*credentials" /var/log/perfect21/app.log | \
        awk -v since="$(date -d "$TIME_RANGE" +%s)" '
        {
            time_str = $1 " " $2
            cmd = "date -d \"" time_str "\" +%s"
            cmd | getline epoch
            close(cmd)

            if (epoch >= since) {
                print "   " $0
            }
        }' | tail -20
        echo

        # Token-related errors
        echo "2. Token Errors:"
        grep -E "token.*invalid|jwt.*error" /var/log/perfect21/app.log | tail -10
        ;;

    *)
        echo "Unknown issue type. Available types:"
        echo "  - performance"
        echo "  - errors"
        echo "  - authentication"
        exit 1
        ;;
esac

echo
echo "✅ Analysis complete"
echo "Review the output above for insights into the issue"
```

## 📞 Support Escalation

### Support Levels

#### Level 1 - Self-Service
- **Response Time**: Immediate
- **Resources**:
  - This troubleshooting guide
  - Quick diagnostic scripts
  - System monitoring dashboards
  - Knowledge base articles

#### Level 2 - Community Support
- **Response Time**: 4-8 hours
- **Resources**:
  - Community forums
  - Discord support channel
  - GitHub issues
  - Stack Overflow (tag: perfect21)

#### Level 3 - Professional Support
- **Response Time**: 2-4 hours (business hours)
- **Contact**: support@perfect21.com
- **Include**:
  - System diagnostic output
  - Relevant log files
  - Steps already attempted
  - Business impact assessment

#### Level 4 - Emergency Support
- **Response Time**: 30 minutes (24/7)
- **Contact**: +1-555-PERFECT21
- **Criteria**:
  - Complete system outage
  - Data loss risk
  - Security incidents
  - Business-critical issues

### Information to Gather Before Contacting Support

#### System Information
```bash
# Run diagnostics
./scripts/collect-system-info.sh

# Include output of:
uname -a
docker --version
kubectl version --client
node --version
psql --version
redis-cli --version
```

#### Problem Description
- **When did the issue start?**
- **What changed recently?** (deployments, configuration, etc.)
- **What is the exact error message?**
- **What steps reproduce the issue?**
- **What is the business impact?**

#### Logs to Include
```bash
# Application logs (last 1000 lines)
tail -1000 /var/log/perfect21/app.log

# System logs
journalctl -u perfect21-api --no-pager -n 100

# Database logs
sudo tail -100 /var/log/postgresql/postgresql-*.log

# Web server logs
tail -100 /var/log/nginx/error.log
```

### Emergency Contact Template

```
Subject: [URGENT] Perfect21 Production Issue - [Brief Description]

Priority: [Critical/High/Medium/Low]
Environment: [Production/Staging/Development]
Started: [Date/Time]
Impact: [User/Business Impact]

Problem Summary:
[Brief description of the issue]

Current Status:
[What's working/not working]

Steps Already Taken:
1. [Action taken]
2. [Action taken]
3. [Action taken]

System Information:
- Version: [Perfect21 version]
- Infrastructure: [Docker/Kubernetes/Bare metal]
- Database: [PostgreSQL version]
- Users Affected: [Number/percentage]

Error Messages:
[Exact error messages or symptoms]

Business Impact:
[Revenue, user, or operational impact]

Contact Information:
- Name: [Your name]
- Phone: [Phone number]
- Email: [Email address]
- Preferred contact method: [Phone/Email/Slack]

Attachments:
- System diagnostics: system-info-YYYYMMDD-HHMMSS.tar.gz
- Application logs: app.log
- Error screenshots: [if applicable]
```

---

**Perfect21 Troubleshooting Manual** - Complete diagnostic and recovery procedures for the AI-driven development workflow system.

*Last updated: 2024-01-15*
*Version: 4.0.0*

*For additional support, visit: https://docs.perfect21.com/support*