# 🛠️ Claude Enhancer 运维手册

> 日常运维操作指南，确保系统稳定运行

## 📋 运维手册概览

### 🎯 运维目标
- **系统可用性**: 99.9%+
- **响应时间**: < 200ms
- **故障恢复时间**: < 5分钟
- **数据完整性**: 100%

### 👥 运维团队角色
- **运维工程师**: 日常监控和维护
- **SRE 工程师**: 可靠性工程和自动化
- **DBA**: 数据库管理和优化
- **安全工程师**: 安全监控和响应

## 📊 日常运维操作

### 每日检查清单

#### 🌅 晨检 (9:00 AM)
```bash
#!/bin/bash
# 文件: scripts/daily_morning_check.sh

echo "🌅 Claude Enhancer 每日晨检开始..."

# 1. 系统健康检查
echo "🏥 检查系统健康状态..."
curl -f http://localhost:8080/health || echo "❌ 健康检查失败"

# 2. 服务状态检查
echo "🔍 检查所有服务状态..."
docker-compose ps || kubectl get pods -n claude-enhancer

# 3. 数据库连接检查
echo "🗄️ 检查数据库连接..."
psql -h localhost -U postgres -d claude_enhancer -c "SELECT 1;" || echo "❌ 数据库连接失败"

# 4. 缓存服务检查
echo "💾 检查 Redis 缓存..."
redis-cli ping || echo "❌ Redis 连接失败"

# 5. 磁盘空间检查
echo "💽 检查磁盘空间..."
df -h | grep -E '(8[0-9]|9[0-9])%' && echo "⚠️ 磁盘空间不足"

# 6. 内存使用检查
echo "🧠 检查内存使用..."
free -h

# 7. 网络连接检查
echo "🌐 检查网络连接..."
netstat -an | grep :8080

# 8. 错误日志检查
echo "📄 检查昨日错误日志..."
grep ERROR /var/log/perfect21/*.log | tail -20

echo "✅ 每日晨检完成!"
```

#### 🌆 晚检 (6:00 PM)
```bash
#!/bin/bash
# 文件: scripts/daily_evening_check.sh

echo "🌆 Claude Enhancer 每日晚检开始..."

# 1. 性能指标汇总
echo "📊 生成今日性能报告..."
python scripts/generate_daily_report.py

# 2. 备份状态检查
echo "💾 检查今日备份状态..."
ls -la /backups/$(date +%Y%m%d)* || echo "⚠️ 今日备份未找到"

# 3. 安全事件检查
echo "🛡️ 检查今日安全事件..."
grep -i "security\|authentication\|unauthorized" /var/log/perfect21/*.log

# 4. 用户活动统计
echo "👥 统计今日用户活动..."
psql -h localhost -U postgres -d claude_enhancer -c "
SELECT
  COUNT(DISTINCT user_id) as active_users,
  COUNT(*) as total_requests
FROM user_activity
WHERE DATE(created_at) = CURRENT_DATE;"

# 5. 系统资源趋势
echo "📈 分析系统资源趋势..."
top -b -n1 | head -10

echo "✅ 每日晚检完成!"
```

### 每周维护任务

#### 🗓️ 周一：系统优化
```bash
#!/bin/bash
# 文件: scripts/weekly_optimization.sh

echo "🔧 开始每周系统优化..."

# 1. 数据库维护
echo "🗄️ 执行数据库维护..."
psql -h localhost -U postgres -d claude_enhancer << EOF
-- 重建索引
REINDEX DATABASE claude_enhancer;

-- 更新统计信息
ANALYZE;

-- 清理过期数据
DELETE FROM user_sessions WHERE expires_at < NOW() - INTERVAL '7 days';
DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '30 days';
EOF

# 2. 缓存清理和优化
echo "💾 优化 Redis 缓存..."
redis-cli FLUSHEXPIRED
redis-cli MEMORY PURGE

# 3. 日志轮转
echo "📄 执行日志轮转..."
logrotate /etc/logrotate.d/perfect21

# 4. 系统清理
echo "🧹 执行系统清理..."
bash .claude/scripts/cleanup.sh

# 5. 性能基准测试
echo "📊 执行性能基准测试..."
bash .claude/scripts/performance_benchmark.sh

echo "✅ 每周系统优化完成!"
```

### 每月维护任务

#### 📅 月度健康检查
```bash
#!/bin/bash
# 文件: scripts/monthly_health_check.sh

echo "🏥 开始月度健康检查..."

# 1. 深度系统扫描
echo "🔍 执行深度系统扫描..."

# 安全扫描
nmap -sS localhost
lynis audit system

# 性能分析
iostat -x 1 10 > /tmp/iostat_report.txt
sar -u 1 10 > /tmp/cpu_report.txt

# 2. 容量规划分析
echo "📊 执行容量规划分析..."
python scripts/capacity_planning_analysis.py

# 3. 备份完整性验证
echo "💾 验证备份完整性..."
python scripts/backup_integrity_check.py

# 4. 文档更新检查
echo "📚 检查文档更新..."
bash scripts/documentation_sync_check.sh

# 5. 依赖项安全更新
echo "🔒 检查依赖项安全更新..."
npm audit
pip-audit

echo "✅ 月度健康检查完成!"
```

## 🚨 故障响应流程

### 告警响应矩阵

#### 告警级别定义
```yaml
alert_levels:
  P1_CRITICAL:
    description: "系统完全不可用或数据丢失风险"
    response_time: "< 15分钟"
    escalation: "立即通知所有相关人员"
    examples:
      - "系统宕机"
      - "数据库损坏"
      - "安全漏洞被利用"

  P2_HIGH:
    description: "核心功能受影响，用户体验严重下降"
    response_time: "< 1小时"
    escalation: "通知主要响应团队"
    examples:
      - "Agent 系统失效"
      - "性能严重下降"
      - "部分服务不可用"

  P3_MEDIUM:
    description: "非核心功能受影响或性能轻微下降"
    response_time: "< 4小时"
    escalation: "分配给值班工程师"
    examples:
      - "监控告警"
      - "日志错误增加"
      - "资源使用率高"

  P4_LOW:
    description: "潜在问题或维护需求"
    response_time: "< 24小时"
    escalation: "记录到工作队列"
    examples:
      - "磁盘空间预警"
      - "证书即将过期"
      - "性能优化建议"
```

#### 故障响应脚本
```bash
#!/bin/bash
# 文件: scripts/incident_response.sh

set -euo pipefail

INCIDENT_LEVEL="$1"
INCIDENT_DESCRIPTION="$2"
INCIDENT_ID="INC-$(date +%Y%m%d-%H%M%S)"

echo "🚨 故障响应启动: $INCIDENT_ID"
echo "级别: $INCIDENT_LEVEL"
echo "描述: $INCIDENT_DESCRIPTION"

# 创建故障记录
create_incident_record() {
    cat > "/var/log/perfect21/incidents/${INCIDENT_ID}.json" << EOF
{
  "incident_id": "$INCIDENT_ID",
  "level": "$INCIDENT_LEVEL",
  "description": "$INCIDENT_DESCRIPTION",
  "started_at": "$(date -Iseconds)",
  "status": "investigating",
  "assigned_to": "$USER",
  "steps": []
}
EOF
}

# 收集系统信息
collect_system_info() {
    echo "📊 收集系统信息..."

    # 系统状态
    systemctl status docker > "/tmp/${INCIDENT_ID}_docker_status.txt"

    # 容器状态
    docker ps -a > "/tmp/${INCIDENT_ID}_containers.txt"

    # 资源使用
    top -b -n1 > "/tmp/${INCIDENT_ID}_top.txt"
    free -h > "/tmp/${INCIDENT_ID}_memory.txt"
    df -h > "/tmp/${INCIDENT_ID}_disk.txt"

    # 网络状态
    netstat -tlnp > "/tmp/${INCIDENT_ID}_network.txt"

    # 最近日志
    tail -1000 /var/log/perfect21/error.log > "/tmp/${INCIDENT_ID}_error_logs.txt"
}

# 自动修复尝试
attempt_auto_recovery() {
    echo "🔧 尝试自动修复..."

    case "$INCIDENT_LEVEL" in
        "P1"|"P2")
            # 高优先级：重启服务
            echo "重启核心服务..."
            docker-compose restart claude-enhancer
            ;;
        "P3")
            # 中优先级：清理和优化
            echo "执行系统清理..."
            bash .claude/scripts/cleanup.sh
            ;;
        "P4")
            # 低优先级：记录观察
            echo "记录问题，持续观察..."
            ;;
    esac
}

# 发送通知
send_notifications() {
    # Slack 通知
    curl -X POST "$SLACK_WEBHOOK_URL" \
      -H 'Content-type: application/json' \
      --data '{
        "text": "🚨 故障警报",
        "attachments": [
          {
            "color": "danger",
            "fields": [
              {"title": "故障ID", "value": "'$INCIDENT_ID'", "short": true},
              {"title": "级别", "value": "'$INCIDENT_LEVEL'", "short": true},
              {"title": "描述", "value": "'$INCIDENT_DESCRIPTION'", "short": false}
            ]
          }
        ]
      }'

    # 邮件通知（P1/P2）
    if [[ "$INCIDENT_LEVEL" =~ ^P[12]$ ]]; then
        echo "发送紧急邮件通知..."
        echo "故障警报: $INCIDENT_DESCRIPTION" | mail -s "紧急故障: $INCIDENT_ID" ops-team@company.com
    fi
}

# 执行响应流程
main() {
    create_incident_record
    collect_system_info
    attempt_auto_recovery
    send_notifications

    echo "✅ 故障响应完成: $INCIDENT_ID"
    echo "📋 请查看故障记录: /var/log/perfect21/incidents/${INCIDENT_ID}.json"
}

main "$@"
```

## 🔄 备份和恢复操作

### 自动备份系统

#### 数据库备份脚本
```bash
#!/bin/bash
# 文件: scripts/database_backup.sh

set -euo pipefail

BACKUP_DIR="/backups/database"
DB_HOST="localhost"
DB_NAME="claude_enhancer"
DB_USER="postgres"
RETENTION_DAYS=30

echo "💾 开始数据库备份..."

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 生成备份文件名
BACKUP_FILE="$BACKUP_DIR/claude_enhancer_$(date +%Y%m%d_%H%M%S).sql"
BACKUP_COMPRESSED="$BACKUP_FILE.gz"

# 执行备份
echo "📦 创建数据库备份: $BACKUP_FILE"
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
  --verbose \
  --no-password \
  --format=custom \
  --file="$BACKUP_FILE"

# 压缩备份文件
echo "🗜️ 压缩备份文件..."
gzip "$BACKUP_FILE"

# 验证备份完整性
echo "✅ 验证备份完整性..."
if pg_restore --list "$BACKUP_COMPRESSED" > /dev/null 2>&1; then
    echo "✅ 备份文件完整性验证通过"
else
    echo "❌ 备份文件完整性验证失败"
    exit 1
fi

# 清理过期备份
echo "🧹 清理过期备份..."
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

# 记录备份信息
echo "📝 记录备份信息..."
cat >> "$BACKUP_DIR/backup_log.txt" << EOF
$(date -Iseconds): 备份完成 - $BACKUP_COMPRESSED ($(du -h "$BACKUP_COMPRESSED" | cut -f1))
EOF

echo "✅ 数据库备份完成: $BACKUP_COMPRESSED"
```

#### 应用数据备份脚本
```bash
#!/bin/bash
# 文件: scripts/application_backup.sh

set -euo pipefail

BACKUP_DIR="/backups/application"
APP_DIR="/app"
CONFIG_DIR="/app/.claude"

echo "📂 开始应用数据备份..."

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份配置文件
echo "⚙️ 备份配置文件..."
tar -czf "$BACKUP_DIR/config_$(date +%Y%m%d_%H%M%S).tar.gz" \
  -C "$APP_DIR" \
  .claude/settings.json \
  .claude/config/ \
  .claude/agents/ \
  deployment/

# 备份用户上传文件
echo "📁 备份用户数据..."
if [ -d "$APP_DIR/uploads" ]; then
    tar -czf "$BACKUP_DIR/uploads_$(date +%Y%m%d_%H%M%S).tar.gz" \
      -C "$APP_DIR" uploads/
fi

# 备份日志文件
echo "📄 备份重要日志..."
tar -czf "$BACKUP_DIR/logs_$(date +%Y%m%d_%H%M%S).tar.gz" \
  -C "/var/log" perfect21/

echo "✅ 应用数据备份完成"
```

### 恢复操作流程

#### 数据库恢复脚本
```bash
#!/bin/bash
# 文件: scripts/database_restore.sh

set -euo pipefail

BACKUP_FILE="$1"
DB_HOST="localhost"
DB_NAME="claude_enhancer"
DB_USER="postgres"

if [ -z "$BACKUP_FILE" ]; then
    echo "使用方法: $0 <backup_file.sql.gz>"
    exit 1
fi

echo "🔄 开始数据库恢复..."
echo "备份文件: $BACKUP_FILE"

# 验证备份文件
echo "✅ 验证备份文件..."
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

# 停止应用服务
echo "⏹️ 停止应用服务..."
docker-compose stop claude-enhancer

# 创建恢复前备份
echo "💾 创建恢复前备份..."
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
  --format=custom \
  --file="/tmp/pre_restore_backup_$(date +%Y%m%d_%H%M%S).sql"

# 删除现有数据库
echo "🗑️ 删除现有数据库..."
psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"

# 创建新数据库
echo "🏗️ 创建新数据库..."
psql -h "$DB_HOST" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;"

# 恢复数据
echo "📥 恢复数据库数据..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | pg_restore -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" --verbose
else
    pg_restore -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" --verbose "$BACKUP_FILE"
fi

# 验证恢复结果
echo "✅ 验证恢复结果..."
TABLE_COUNT=$(psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
echo "恢复后表数量: $TABLE_COUNT"

# 重启应用服务
echo "🚀 重启应用服务..."
docker-compose start claude-enhancer

echo "✅ 数据库恢复完成"
```

## 📊 性能监控和调优

### 实时性能监控

#### 性能监控脚本
```bash
#!/bin/bash
# 文件: scripts/performance_monitor.sh

INTERVAL=10
LOG_FILE="/var/log/perfect21/performance.log"

echo "📊 启动性能监控 (间隔: ${INTERVAL}秒)..."

while true; do
    TIMESTAMP=$(date -Iseconds)

    # CPU 使用率
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)

    # 内存使用率
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')

    # 磁盘使用率
    DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | cut -d'%' -f1)

    # 网络连接数
    CONNECTIONS=$(netstat -an | grep :8080 | wc -l)

    # 应用响应时间
    RESPONSE_TIME=$(curl -w "%{time_total}" -o /dev/null -s http://localhost:8080/health)

    # 记录性能数据
    echo "$TIMESTAMP,CPU:$CPU_USAGE,MEM:$MEM_USAGE,DISK:$DISK_USAGE,CONN:$CONNECTIONS,RT:$RESPONSE_TIME" >> "$LOG_FILE"

    # 检查告警阈值
    if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
        echo "⚠️ CPU 使用率过高: $CPU_USAGE%"
    fi

    if (( $(echo "$MEM_USAGE > 85" | bc -l) )); then
        echo "⚠️ 内存使用率过高: $MEM_USAGE%"
    fi

    if (( DISK_USAGE > 90 )); then
        echo "⚠️ 磁盘使用率过高: $DISK_USAGE%"
    fi

    if (( $(echo "$RESPONSE_TIME > 1.0" | bc -l) )); then
        echo "⚠️ 响应时间过长: ${RESPONSE_TIME}s"
    fi

    sleep $INTERVAL
done
```

### 性能调优操作

#### 数据库性能调优
```sql
-- 文件: scripts/database_tuning.sql

-- 分析慢查询
SELECT
    query,
    mean_time,
    calls,
    total_time,
    (total_time/calls) as avg_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- 检查未使用的索引
SELECT
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_tup_read = 0 AND idx_tup_fetch = 0;

-- 分析表膨胀
SELECT
    schemaname,
    tablename,
    n_dead_tup,
    n_live_tup,
    ROUND((n_dead_tup::numeric / (n_live_tup + n_dead_tup)) * 100, 2) as dead_percentage
FROM pg_stat_user_tables
WHERE n_dead_tup > 0
ORDER BY dead_percentage DESC;

-- 优化建议查询
SELECT
    'VACUUM ANALYZE ' || schemaname || '.' || tablename || ';' as optimization_command
FROM pg_stat_user_tables
WHERE n_dead_tup > n_live_tup * 0.1;
```

#### 应用性能调优
```python
# 文件: scripts/application_tuning.py

import psutil
import asyncio
import aiohttp
from typing import Dict, List

class PerformanceTuner:
    """应用性能调优器"""

    def __init__(self):
        self.optimization_recommendations = []

    async def analyze_performance(self) -> Dict[str, any]:
        """分析应用性能"""

        # CPU 分析
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_cores = psutil.cpu_count()

        # 内存分析
        memory = psutil.virtual_memory()

        # 磁盘 I/O 分析
        disk_io = psutil.disk_io_counters()

        # 网络分析
        network_io = psutil.net_io_counters()

        # 应用响应时间分析
        response_times = await self.measure_response_times()

        analysis = {
            'cpu': {
                'usage_percent': cpu_percent,
                'cores': cpu_cores,
                'load_average': psutil.getloadavg()
            },
            'memory': {
                'usage_percent': memory.percent,
                'available_gb': memory.available / (1024**3),
                'used_gb': memory.used / (1024**3)
            },
            'disk_io': {
                'read_mb_per_sec': disk_io.read_bytes / (1024**2),
                'write_mb_per_sec': disk_io.write_bytes / (1024**2)
            },
            'network_io': {
                'sent_mb': network_io.bytes_sent / (1024**2),
                'recv_mb': network_io.bytes_recv / (1024**2)
            },
            'response_times': response_times
        }

        # 生成优化建议
        self.generate_recommendations(analysis)

        return analysis

    async def measure_response_times(self) -> Dict[str, float]:
        """测量各个端点的响应时间"""
        endpoints = [
            'http://localhost:8080/health',
            'http://localhost:8080/api/agents/status',
            'http://localhost:8080/api/workflow/status'
        ]

        response_times = {}

        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    start_time = asyncio.get_event_loop().time()
                    async with session.get(endpoint) as response:
                        await response.text()
                    end_time = asyncio.get_event_loop().time()

                    response_times[endpoint] = end_time - start_time
                except Exception as e:
                    response_times[endpoint] = float('inf')

        return response_times

    def generate_recommendations(self, analysis: Dict[str, any]) -> None:
        """生成性能优化建议"""

        # CPU 优化建议
        if analysis['cpu']['usage_percent'] > 80:
            self.optimization_recommendations.append({
                'type': 'cpu',
                'severity': 'high',
                'message': f"CPU 使用率过高 ({analysis['cpu']['usage_percent']}%)",
                'suggestions': [
                    '考虑增加服务器 CPU 核心数',
                    '优化应用代码，减少 CPU 密集型操作',
                    '启用应用缓存减少计算负荷'
                ]
            })

        # 内存优化建议
        if analysis['memory']['usage_percent'] > 85:
            self.optimization_recommendations.append({
                'type': 'memory',
                'severity': 'high',
                'message': f"内存使用率过高 ({analysis['memory']['usage_percent']}%)",
                'suggestions': [
                    '增加服务器内存',
                    '检查内存泄漏',
                    '优化数据结构和算法'
                ]
            })

        # 响应时间优化建议
        slow_endpoints = [
            endpoint for endpoint, time in analysis['response_times'].items()
            if time > 1.0
        ]

        if slow_endpoints:
            self.optimization_recommendations.append({
                'type': 'response_time',
                'severity': 'medium',
                'message': f"发现 {len(slow_endpoints)} 个慢响应端点",
                'suggestions': [
                    '优化数据库查询',
                    '添加适当的索引',
                    '启用应用层缓存',
                    '考虑使用 CDN'
                ]
            })

# 使用示例
async def main():
    tuner = PerformanceTuner()
    analysis = await tuner.analyze_performance()

    print("📊 性能分析结果:")
    print(f"CPU: {analysis['cpu']['usage_percent']}%")
    print(f"内存: {analysis['memory']['usage_percent']}%")

    print("\n💡 优化建议:")
    for rec in tuner.optimization_recommendations:
        print(f"- {rec['message']}")
        for suggestion in rec['suggestions']:
            print(f"  • {suggestion}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔒 安全运维操作

### 安全监控脚本

#### 安全事件监控
```bash
#!/bin/bash
# 文件: scripts/security_monitor.sh

SECURITY_LOG="/var/log/perfect21/security.log"
ALERT_EMAIL="security@company.com"

echo "🛡️ 启动安全监控..."

# 监控登录异常
monitor_login_anomalies() {
    # 检查短时间内的多次失败登录
    FAILED_LOGINS=$(grep "authentication failed" /var/log/perfect21/auth.log | grep "$(date +%Y-%m-%d)" | wc -l)

    if [ "$FAILED_LOGINS" -gt 10 ]; then
        echo "$(date -Iseconds): 检测到异常登录尝试: $FAILED_LOGINS 次失败" >> "$SECURITY_LOG"

        # 发送告警
        echo "安全告警: 检测到 $FAILED_LOGINS 次失败登录尝试" | \
            mail -s "安全告警: 异常登录活动" "$ALERT_EMAIL"
    fi
}

# 监控文件完整性
monitor_file_integrity() {
    # 检查关键配置文件的变更
    CRITICAL_FILES=(
        "/app/.claude/settings.json"
        "/app/.claude/config/main.yaml"
        "/etc/passwd"
        "/etc/shadow"
    )

    for file in "${CRITICAL_FILES[@]}"; do
        if [ -f "$file" ]; then
            CURRENT_HASH=$(sha256sum "$file" | cut -d' ' -f1)
            STORED_HASH_FILE="/var/lib/perfect21/hashes/$(basename "$file").hash"

            if [ -f "$STORED_HASH_FILE" ]; then
                STORED_HASH=$(cat "$STORED_HASH_FILE")

                if [ "$CURRENT_HASH" != "$STORED_HASH" ]; then
                    echo "$(date -Iseconds): 文件完整性告警: $file 已被修改" >> "$SECURITY_LOG"

                    # 更新存储的哈希值
                    echo "$CURRENT_HASH" > "$STORED_HASH_FILE"
                fi
            else
                # 首次运行，创建哈希文件
                mkdir -p "$(dirname "$STORED_HASH_FILE")"
                echo "$CURRENT_HASH" > "$STORED_HASH_FILE"
            fi
        fi
    done
}

# 监控网络异常
monitor_network_anomalies() {
    # 检查异常的网络连接
    SUSPICIOUS_CONNECTIONS=$(netstat -an | grep -E ":(22|23|3389|4444|5555)" | grep ESTABLISHED | wc -l)

    if [ "$SUSPICIOUS_CONNECTIONS" -gt 0 ]; then
        echo "$(date -Iseconds): 检测到可疑网络连接: $SUSPICIOUS_CONNECTIONS 个" >> "$SECURITY_LOG"
    fi
}

# 主监控循环
while true; do
    monitor_login_anomalies
    monitor_file_integrity
    monitor_network_anomalies

    sleep 60  # 每分钟检查一次
done
```

### 安全加固操作

#### 系统安全加固脚本
```bash
#!/bin/bash
# 文件: scripts/security_hardening.sh

set -euo pipefail

echo "🔒 开始系统安全加固..."

# 1. 更新系统和软件包
echo "📦 更新系统软件包..."
apt update && apt upgrade -y

# 2. 配置防火墙
echo "🛡️ 配置防火墙规则..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# 允许必要的端口
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8080/tcp  # 应用端口

ufw --force enable

# 3. 配置 SSH 安全
echo "🔐 配置 SSH 安全..."
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

systemctl restart sshd

# 4. 配置自动安全更新
echo "🔄 配置自动安全更新..."
apt install -y unattended-upgrades
echo 'Unattended-Upgrade::Automatic-Reboot "false";' >> /etc/apt/apt.conf.d/50unattended-upgrades

# 5. 安装和配置 fail2ban
echo "🚫 安装和配置 fail2ban..."
apt install -y fail2ban

cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log

[claude-enhancer]
enabled = true
port = 8080
filter = claude-enhancer
logpath = /var/log/perfect21/access.log
maxretry = 5
EOF

# 创建 Claude Enhancer fail2ban 过滤器
cat > /etc/fail2ban/filter.d/claude-enhancer.conf << EOF
[Definition]
failregex = ^.*authentication failed.*<HOST>.*$
            ^.*unauthorized access.*<HOST>.*$
ignoreregex =
EOF

systemctl restart fail2ban

# 6. 设置文件权限
echo "📁 设置安全文件权限..."
chmod 600 /app/.claude/settings.json
chmod 700 /app/.claude/config/
chown -R app:app /app/.claude/

# 7. 配置审计日志
echo "📋 配置审计日志..."
apt install -y auditd
systemctl enable auditd

# 8. 配置安全内核参数
echo "⚙️ 配置安全内核参数..."
cat >> /etc/sysctl.conf << EOF
# 网络安全参数
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.ip_forward = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# 防止 SYN flood 攻击
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5
EOF

sysctl -p

echo "✅ 系统安全加固完成!"
```

## 📈 容量规划和扩展

### 容量监控脚本
```python
# 文件: scripts/capacity_planning.py

import psutil
import psycopg2
import redis
import json
import datetime
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class CapacityMetrics:
    """容量指标数据类"""
    timestamp: datetime.datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    database_size: float
    active_connections: int
    cache_usage: float

class CapacityPlanner:
    """容量规划分析器"""

    def __init__(self):
        self.db_connection = psycopg2.connect(
            host="localhost",
            database="claude_enhancer",
            user="postgres",
            password="password"
        )
        self.redis_connection = redis.Redis(host="localhost", port=6379, db=0)

    def collect_current_metrics(self) -> CapacityMetrics:
        """收集当前容量指标"""

        # 系统资源指标
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()

        # 数据库指标
        with self.db_connection.cursor() as cursor:
            cursor.execute("SELECT pg_database_size('claude_enhancer');")
            db_size = cursor.fetchone()[0] / (1024**3)  # GB

            cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active';")
            active_connections = cursor.fetchone()[0]

        # Redis 指标
        redis_info = self.redis_connection.info()
        cache_usage = redis_info['used_memory'] / (1024**2)  # MB

        return CapacityMetrics(
            timestamp=datetime.datetime.now(),
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            disk_usage=(disk.used / disk.total) * 100,
            network_io={
                'bytes_sent': network.bytes_sent / (1024**2),
                'bytes_recv': network.bytes_recv / (1024**2)
            },
            database_size=db_size,
            active_connections=active_connections,
            cache_usage=cache_usage
        )

    def analyze_growth_trend(self, historical_data: List[CapacityMetrics]) -> Dict[str, float]:
        """分析增长趋势"""
        if len(historical_data) < 2:
            return {}

        # 计算各项指标的增长率
        first_metric = historical_data[0]
        last_metric = historical_data[-1]
        time_diff = (last_metric.timestamp - first_metric.timestamp).days

        if time_diff == 0:
            return {}

        growth_rates = {
            'cpu_growth_rate': (last_metric.cpu_usage - first_metric.cpu_usage) / time_diff,
            'memory_growth_rate': (last_metric.memory_usage - first_metric.memory_usage) / time_diff,
            'disk_growth_rate': (last_metric.disk_usage - first_metric.disk_usage) / time_diff,
            'database_growth_rate': (last_metric.database_size - first_metric.database_size) / time_diff,
            'connection_growth_rate': (last_metric.active_connections - first_metric.active_connections) / time_diff
        }

        return growth_rates

    def predict_capacity_needs(self, growth_rates: Dict[str, float], days_ahead: int = 90) -> Dict[str, any]:
        """预测容量需求"""
        current_metrics = self.collect_current_metrics()

        predictions = {}

        # CPU 预测
        predicted_cpu = current_metrics.cpu_usage + (growth_rates.get('cpu_growth_rate', 0) * days_ahead)
        if predicted_cpu > 80:
            predictions['cpu'] = {
                'status': 'warning',
                'predicted_usage': predicted_cpu,
                'recommendation': '考虑升级 CPU 或优化应用性能'
            }

        # 内存预测
        predicted_memory = current_metrics.memory_usage + (growth_rates.get('memory_growth_rate', 0) * days_ahead)
        if predicted_memory > 85:
            predictions['memory'] = {
                'status': 'warning',
                'predicted_usage': predicted_memory,
                'recommendation': '考虑增加内存或优化内存使用'
            }

        # 磁盘预测
        predicted_disk = current_metrics.disk_usage + (growth_rates.get('disk_growth_rate', 0) * days_ahead)
        if predicted_disk > 90:
            predictions['disk'] = {
                'status': 'critical',
                'predicted_usage': predicted_disk,
                'recommendation': '紧急扩展磁盘空间'
            }

        # 数据库预测
        predicted_db_size = current_metrics.database_size + (growth_rates.get('database_growth_rate', 0) * days_ahead)
        predictions['database'] = {
            'status': 'info',
            'predicted_size_gb': predicted_db_size,
            'recommendation': f'预计数据库大小将达到 {predicted_db_size:.2f} GB'
        }

        return predictions

    def generate_capacity_report(self) -> str:
        """生成容量规划报告"""
        current_metrics = self.collect_current_metrics()

        # 这里应该从历史数据存储中获取数据
        # 为了示例，我们使用当前指标
        growth_rates = {
            'cpu_growth_rate': 0.1,  # 示例值
            'memory_growth_rate': 0.2,
            'disk_growth_rate': 0.05,
            'database_growth_rate': 0.01,
            'connection_growth_rate': 0.5
        }

        predictions = self.predict_capacity_needs(growth_rates)

        report = f"""
# Claude Enhancer 容量规划报告

## 当前资源使用情况
- CPU 使用率: {current_metrics.cpu_usage:.1f}%
- 内存使用率: {current_metrics.memory_usage:.1f}%
- 磁盘使用率: {current_metrics.disk_usage:.1f}%
- 数据库大小: {current_metrics.database_size:.2f} GB
- 活跃连接数: {current_metrics.active_connections}
- 缓存使用: {current_metrics.cache_usage:.1f} MB

## 90天容量预测
"""

        for resource, prediction in predictions.items():
            report += f"\n### {resource.upper()}\n"
            report += f"- 状态: {prediction['status']}\n"
            report += f"- 建议: {prediction['recommendation']}\n"

        return report

# 使用示例
def main():
    planner = CapacityPlanner()

    # 收集当前指标
    current_metrics = planner.collect_current_metrics()
    print(f"当前 CPU 使用率: {current_metrics.cpu_usage:.1f}%")

    # 生成容量报告
    report = planner.generate_capacity_report()
    print(report)

    # 保存报告
    with open(f"/var/log/perfect21/capacity_report_{datetime.date.today()}.txt", "w") as f:
        f.write(report)

if __name__ == "__main__":
    main()
```

## 📋 运维检查清单

### 每日运维检查清单
- [ ] **系统健康检查**
  - [ ] 应用服务状态正常
  - [ ] 数据库连接正常
  - [ ] 缓存服务可用
  - [ ] 磁盘空间充足 (< 80%)
  - [ ] 内存使用正常 (< 85%)
  - [ ] CPU 负载合理 (< 80%)

- [ ] **安全状态检查**
  - [ ] 无安全告警
  - [ ] 防火墙状态正常
  - [ ] SSL 证书有效
  - [ ] 访问日志正常
  - [ ] 无异常登录尝试

- [ ] **备份状态检查**
  - [ ] 数据库备份完成
  - [ ] 应用配置备份完成
  - [ ] 备份文件完整性验证
  - [ ] 远程备份同步正常

### 每周运维检查清单
- [ ] **性能分析**
  - [ ] 响应时间趋势分析
  - [ ] 错误率统计
  - [ ] 用户活跃度分析
  - [ ] 资源使用趋势

- [ ] **系统维护**
  - [ ] 数据库性能调优
  - [ ] 日志文件轮转
  - [ ] 临时文件清理
  - [ ] 缓存优化

- [ ] **安全审计**
  - [ ] 安全日志审查
  - [ ] 用户权限审查
  - [ ] 系统漏洞扫描
  - [ ] 配置安全检查

### 每月运维检查清单
- [ ] **容量规划**
  - [ ] 资源使用趋势分析
  - [ ] 容量预测报告
  - [ ] 扩容需求评估
  - [ ] 成本优化建议

- [ ] **灾难恢复测试**
  - [ ] 备份恢复测试
  - [ ] 故障切换测试
  - [ ] 恢复时间验证
  - [ ] 应急流程演练

---

**📞 紧急联系方式**:
- **运维值班**: [电话号码]
- **技术负责人**: [电话号码]
- **系统管理员**: [电话号码]

**🎯 运维目标**: 确保 Claude Enhancer 系统 7x24 小时稳定运行，为用户提供可靠的服务