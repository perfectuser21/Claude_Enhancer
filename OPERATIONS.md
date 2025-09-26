# 🔧 Claude Enhancer 5.1 - 运维操作手册

## 📚 手册概述

本运维手册为Claude Enhancer 5.1系统提供完整的日常运维指导，涵盖监控、维护、故障处理和性能优化等核心运维工作。

### 🎯 运维目标
- **可用性目标**: 99.9% SLA（每月停机时间 < 43分钟）
- **性能目标**: API响应时间 < 500ms (P95)
- **错误率目标**: 错误率 < 0.1%
- **恢复目标**: MTTR < 15分钟

### 🏗️ 系统架构概览

```
┌─────────────────────────────────────────────────────────┐
│                 Claude Enhancer 5.1                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Phase     │  │   Agent     │  │    Hook     │     │
│  │  Manager    │  │  Manager    │  │   System    │     │
│  │  (8-Phase)  │  │  (61-Agent) │  │ (Quality)   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│           智能加载策略 + 缓存系统 + 配置管理             │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Logging   │  │ Monitoring  │  │   Security  │     │
│  │   System    │  │    Stack    │  │   Module    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## 🔍 系统监控

### 关键指标监控

#### 1. 系统健康指标

**API健康检查**
```bash
# 基础健康检查
curl -f http://localhost:8080/health || echo "API健康检查失败"

# 详细健康状态
curl -s http://localhost:8080/health | jq '
{
  status: .status,
  version: .version,
  uptime: .uptime,
  components: .components | keys
}'

# 就绪状态检查
curl -f http://localhost:8080/ready || echo "系统未就绪"
```

**系统资源监控**
```bash
#!/bin/bash
# system_monitor.sh

echo "🔍 Claude Enhancer 5.1 系统资源监控"
echo "=================================="

# CPU使用率
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
echo "CPU使用率: ${CPU_USAGE}%"

# 内存使用率
MEM_USAGE=$(free | grep Mem | awk '{printf("%.1f"), $3/$2 * 100.0}')
echo "内存使用率: ${MEM_USAGE}%"

# 磁盘使用率
DISK_USAGE=$(df -h / | awk 'NR==2{printf "%s", $5}')
echo "磁盘使用率: ${DISK_USAGE}"

# 进程状态
PROCESS_COUNT=$(ps aux | grep claude_enhancer | grep -v grep | wc -l)
echo "Claude进程数: ${PROCESS_COUNT}"

# 端口状态
PORT_STATUS=$(netstat -tlnp | grep :8080 | wc -l)
if [ $PORT_STATUS -gt 0 ]; then
    echo "API端口状态: ✅ 正常监听"
else
    echo "API端口状态: ❌ 未监听"
fi

# 日志文件大小
LOG_SIZE=$(du -sh ./logs/ 2>/dev/null | cut -f1 || echo "0B")
echo "日志文件大小: ${LOG_SIZE}"
```

#### 2. 性能指标监控

**响应时间监控**
```bash
#!/bin/bash
# response_time_monitor.sh

echo "⚡ 响应时间监控报告"
echo "====================="

# API响应时间测试
for endpoint in "/health" "/api/v1/phases" "/api/v1/agents" "/api/v1/hooks/status"
do
    START=$(date +%s%N | cut -b1-13)
    HTTP_CODE=$(curl -o /dev/null -s -w "%{http_code}" http://localhost:8080${endpoint})
    END=$(date +%s%N | cut -b1-13)
    RESPONSE_TIME=$((END - START))

    if [ $HTTP_CODE -eq 200 ]; then
        STATUS="✅"
    else
        STATUS="❌"
    fi

    printf "%-20s %s %4dms (HTTP %d)\n" "${endpoint}" "${STATUS}" "${RESPONSE_TIME}" "${HTTP_CODE}"
done

# 数据库响应时间（如果使用）
if command -v psql &> /dev/null; then
    START=$(date +%s%N | cut -b1-13)
    psql -h localhost -U claude -d claude_enhancer -c "SELECT 1;" &>/dev/null
    END=$(date +%s%N | cut -b1-13)
    DB_RESPONSE_TIME=$((END - START))
    echo "数据库响应时间:      ✅ ${DB_RESPONSE_TIME}ms"
fi
```

**吞吐量监控**
```bash
#!/bin/bash
# throughput_monitor.sh

echo "📊 吞吐量监控报告"
echo "=================="

# 分析访问日志中的QPS
if [ -f "./logs/access.log" ]; then
    CURRENT_TIME=$(date +%s)
    MINUTE_AGO=$((CURRENT_TIME - 60))

    QPS=$(awk -v start="$MINUTE_AGO" '$4 > start {count++} END {print count/60}' ./logs/access.log)
    echo "当前QPS: ${QPS:-0} req/s"

    # 按状态码统计
    echo "状态码分布:"
    tail -1000 ./logs/access.log | awk '{print $9}' | sort | uniq -c | sort -nr | head -5
fi

# Phase执行统计
if [ -f "./.claude/logs/phase_execution.log" ]; then
    echo -e "\nPhase执行统计 (最近1小时):"
    grep "$(date -d '1 hour ago' +%Y-%m-%d)" ./.claude/logs/phase_execution.log | \
    awk '{print $5}' | sort | uniq -c | sort -nr
fi
```

#### 3. Agent系统监控

**Agent状态检查**
```bash
#!/bin/bash
# agent_monitor.sh

echo "🤖 Agent系统监控报告"
echo "===================="

# Agent文件完整性检查
TOTAL_AGENTS=61
ACTUAL_AGENTS=$(find .claude/agents -name "*.py" -type f | wc -l)

echo "Agent文件统计:"
echo "  预期数量: ${TOTAL_AGENTS}"
echo "  实际数量: ${ACTUAL_AGENTS}"

if [ $ACTUAL_AGENTS -eq $TOTAL_AGENTS ]; then
    echo "  状态: ✅ 完整"
else
    echo "  状态: ❌ 不完整 (缺失 $((TOTAL_AGENTS - ACTUAL_AGENTS)) 个)"
fi

# Agent性能统计
echo -e "\nAgent性能统计:"
if [ -f "./.claude/logs/agent_performance.log" ]; then
    echo "  最活跃的Agent (最近24小时):"
    grep "$(date +%Y-%m-%d)" ./.claude/logs/agent_performance.log | \
    awk '{print $6}' | sort | uniq -c | sort -nr | head -5 | \
    while read count agent; do
        printf "    %-20s %3d次调用\n" "$agent" "$count"
    done

    echo "  平均Agent执行时间:"
    grep "$(date +%Y-%m-%d)" ./.claude/logs/agent_performance.log | \
    awk '{sum+=$8; count++} END {printf "    %.2f秒\n", sum/count}'
fi

# Agent选择策略统计
echo -e "\nAgent选择策略:"
API_RESPONSE=$(curl -s http://localhost:8080/api/v1/agents/strategy)
echo "$API_RESPONSE" | jq -r '
"  当前策略: \(.current_strategy)",
"  4-Agent任务: \(.stats.tasks_4_agents)次",
"  6-Agent任务: \(.stats.tasks_6_agents)次",
"  8-Agent任务: \(.stats.tasks_8_agents)次"
' 2>/dev/null || echo "  API响应异常"
```

#### 4. 缓存系统监控

**缓存性能监控**
```bash
#!/bin/bash
# cache_monitor.sh

echo "🗄️ 缓存系统监控报告"
echo "==================="

# 缓存命中率
CACHE_STATS=$(curl -s http://localhost:8080/api/v1/cache/stats)
echo "$CACHE_STATS" | jq -r '
"缓存统计:",
"  总请求数: \(.total_requests)",
"  命中次数: \(.cache_hits)",
"  命中率: \(.hit_rate * 100)%",
"  缓存大小: \(.cache_size)MB",
"  条目数量: \(.entry_count)"
' 2>/dev/null || echo "缓存API响应异常"

# 缓存清理统计
if [ -f "./.claude/cache/cleanup.log" ]; then
    echo -e "\n缓存清理记录 (最近5次):"
    tail -5 ./.claude/cache/cleanup.log | while read line; do
        echo "  $line"
    done
fi

# 智能加载缓存
echo -e "\n智能加载缓存:"
SMART_LOADING_STATS=$(curl -s http://localhost:8080/api/v1/smart-loading/stats)
echo "$SMART_LOADING_STATS" | jq -r '
"  文档缓存数: \(.cached_documents)",
"  预加载命中: \(.preload_hits)",
"  延迟加载: \(.lazy_loads)",
"  平均加载时间: \(.avg_load_time)ms"
' 2>/dev/null || echo "  智能加载API响应异常"
```

### 5. Hook系统监控

**Hook执行监控**
```bash
#!/bin/bash
# hook_monitor.sh

echo "🎣 Hook系统监控报告"
echo "=================="

# Hook配置状态
echo "Hook配置状态:"
HOOK_CONFIG=$(curl -s http://localhost:8080/api/v1/hooks/config)
echo "$HOOK_CONFIG" | jq -r '.hooks[] | "  \(.name): \(if .enabled then "✅ 启用" else "❌ 禁用" end)"' 2>/dev/null

# Hook执行统计
echo -e "\nHook执行统计 (最近24小时):"
if [ -f "./.claude/logs/hooks.log" ]; then
    grep "$(date +%Y-%m-%d)" ./.claude/logs/hooks.log | \
    awk '{print $5}' | sort | uniq -c | sort -nr | \
    while read count hook; do
        printf "  %-25s %3d次\n" "$hook" "$count"
    done
fi

# Hook性能分析
echo -e "\nHook性能分析:"
if [ -f "./.claude/logs/hook_performance.log" ]; then
    grep "$(date +%Y-%m-%d)" ./.claude/logs/hook_performance.log | \
    awk '{
        hook=$5; time=$7
        sum[hook]+=time; count[hook]++
    } END {
        for (h in sum) printf "  %-25s 平均耗时: %6.2fms\n", h, sum[h]/count[h]
    }' | sort -k4 -nr
fi

# Hook错误统计
ERROR_COUNT=$(grep -c "ERROR.*hook" ./.claude/logs/hooks.log 2>/dev/null || echo "0")
echo -e "\nHook错误统计: ${ERROR_COUNT}次"
if [ $ERROR_COUNT -gt 0 ]; then
    echo "最近错误:"
    grep "ERROR.*hook" ./.claude/logs/hooks.log | tail -3 | \
    while read line; do
        echo "  $line"
    done
fi
```

## 🛠️ 日常维护

### 日志管理

#### 日志轮转配置

**Logrotate配置**
```bash
# /etc/logrotate.d/claude-enhancer
/home/xx/dev/Claude\ Enhancer\ 5.0/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 claude claude
    postrotate
        pkill -USR1 claude_enhancer || true
    endscript
}
```

**自定义日志清理脚本**
```bash
#!/bin/bash
# log_cleanup.sh

LOG_DIR="./logs"
RETENTION_DAYS=30
MAX_SIZE="10G"

echo "🧹 Claude Enhancer 5.1 日志清理"
echo "==============================="

# 按时间清理
echo "1. 清理${RETENTION_DAYS}天前的日志..."
find $LOG_DIR -name "*.log" -mtime +$RETENTION_DAYS -delete
DELETED_BY_TIME=$(find $LOG_DIR -name "*.log.gz" -mtime +$RETENTION_DAYS -print | wc -l)
find $LOG_DIR -name "*.log.gz" -mtime +$RETENTION_DAYS -delete
echo "   删除了 ${DELETED_BY_TIME} 个过期日志文件"

# 按大小清理
echo "2. 检查日志目录大小..."
CURRENT_SIZE=$(du -sb $LOG_DIR | cut -f1)
MAX_SIZE_BYTES=$(echo $MAX_SIZE | sed 's/G/*1024*1024*1024/g' | bc)

if [ $CURRENT_SIZE -gt $MAX_SIZE_BYTES ]; then
    echo "   ⚠️ 日志目录超过限制，清理最旧的文件"
    find $LOG_DIR -type f -printf '%T@ %p\n' | sort -n | head -n 10 | cut -d' ' -f2- | xargs rm -f
else
    echo "   ✅ 日志目录大小正常 ($(du -sh $LOG_DIR | cut -f1))"
fi

# 压缩当前日志
echo "3. 压缩历史日志..."
find $LOG_DIR -name "*.log" -mtime +1 -not -name "*$(date +%Y-%m-%d)*" -exec gzip {} \;
COMPRESSED_COUNT=$(find $LOG_DIR -name "*.log.gz" -mtime -1 | wc -l)
echo "   压缩了 ${COMPRESSED_COUNT} 个日志文件"

echo "==============================="
echo "🎉 日志清理完成"
```

#### 日志监控脚本

```bash
#!/bin/bash
# log_monitor.sh

echo "📋 日志监控报告"
echo "==============="

LOG_DIR="./logs"

# 日志文件统计
echo "日志文件统计:"
echo "  普通日志: $(find $LOG_DIR -name "*.log" | wc -l) 个"
echo "  压缩日志: $(find $LOG_DIR -name "*.log.gz" | wc -l) 个"
echo "  总大小: $(du -sh $LOG_DIR | cut -f1)"

# 错误日志分析
echo -e "\n错误日志分析 (最近24小时):"
ERROR_TYPES=(
    "ERROR"
    "CRITICAL"
    "FATAL"
    "Exception"
)

for error_type in "${ERROR_TYPES[@]}"; do
    COUNT=$(find $LOG_DIR -name "*.log" -exec grep -c "$error_type" {} \; | awk '{sum+=$1} END {print sum+0}')
    echo "  $error_type: $COUNT 次"
done

# 最新错误
echo -e "\n最新错误 (最近10条):"
find $LOG_DIR -name "*.log" -exec grep -H "ERROR\|CRITICAL\|Exception" {} \; | \
    sort -t: -k2 | tail -10 | \
    while IFS=: read -r file timestamp level message; do
        echo "  $(basename $file): $level $message"
    done

# 日志增长趋势
echo -e "\n日志增长趋势:"
HOUR_AGO_SIZE=$(find $LOG_DIR -name "*.log" -newermt "1 hour ago" -exec ls -l {} \; | awk '{sum+=$5} END {print sum/1024/1024}')
echo "  最近1小时新增: ${HOUR_AGO_SIZE:-0} MB"
```

### 配置管理

#### 配置备份与恢复

**配置备份脚本**
```bash
#!/bin/bash
# config_backup.sh

BACKUP_DIR="./backups/config"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="claude_config_${DATE}"

mkdir -p $BACKUP_DIR

echo "💾 Claude Enhancer 5.1 配置备份"
echo "==============================="

# 创建备份目录
CURRENT_BACKUP="${BACKUP_DIR}/${BACKUP_NAME}"
mkdir -p $CURRENT_BACKUP

# 备份主配置文件
echo "1. 备份主配置..."
cp .claude/config/config.yaml $CURRENT_BACKUP/
cp .env $CURRENT_BACKUP/
echo "   ✅ 主配置备份完成"

# 备份Hook配置
echo "2. 备份Hook配置..."
cp -r .claude/hooks/config.yaml $CURRENT_BACKUP/
cp -r .claude/hooks/*.sh $CURRENT_BACKUP/ 2>/dev/null || true
echo "   ✅ Hook配置备份完成"

# 备份Agent配置
echo "3. 备份Agent配置..."
mkdir -p $CURRENT_BACKUP/agents
cp .claude/agents.config $CURRENT_BACKUP/agents/ 2>/dev/null || true
echo "   ✅ Agent配置备份完成"

# 备份设置文件
echo "4. 备份系统设置..."
cp .claude/settings.json $CURRENT_BACKUP/
cp .claude/settings.local.json $CURRENT_BACKUP/ 2>/dev/null || true
echo "   ✅ 系统设置备份完成"

# 创建压缩包
echo "5. 创建压缩包..."
tar -czf "${CURRENT_BACKUP}.tar.gz" -C $BACKUP_DIR $BACKUP_NAME
rm -rf $CURRENT_BACKUP
echo "   ✅ 压缩包创建完成: ${BACKUP_NAME}.tar.gz"

# 清理旧备份（保留最近7天）
echo "6. 清理旧备份..."
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
REMAINING=$(find $BACKUP_DIR -name "*.tar.gz" | wc -l)
echo "   ✅ 保留 ${REMAINING} 个备份文件"

echo "==============================="
echo "🎉 配置备份完成!"
echo "备份文件: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
```

**配置恢复脚本**
```bash
#!/bin/bash
# config_restore.sh

if [ $# -ne 1 ]; then
    echo "使用方法: $0 <备份文件名>"
    echo "可用备份:"
    ls -1 ./backups/config/*.tar.gz 2>/dev/null | xargs -I {} basename {} .tar.gz || echo "  无可用备份"
    exit 1
fi

BACKUP_FILE="./backups/config/$1.tar.gz"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

echo "🔄 Claude Enhancer 5.1 配置恢复"
echo "==============================="
echo "恢复文件: $BACKUP_FILE"
echo ""

read -p "⚠️  这将覆盖当前配置，确认继续? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消恢复操作"
    exit 1
fi

# 先备份当前配置
echo "1. 备份当前配置..."
./config_backup.sh
echo "   ✅ 当前配置已备份"

# 解压恢复文件
echo "2. 解压恢复文件..."
TEMP_DIR="/tmp/claude_restore_$$"
mkdir -p $TEMP_DIR
tar -xzf "$BACKUP_FILE" -C $TEMP_DIR
RESTORE_DIR=$(find $TEMP_DIR -name "claude_config_*" -type d)
echo "   ✅ 文件解压完成"

# 恢复配置文件
echo "3. 恢复配置文件..."
cp $RESTORE_DIR/config.yaml .claude/config/
cp $RESTORE_DIR/.env ./
cp $RESTORE_DIR/config.yaml .claude/hooks/ 2>/dev/null || true
cp $RESTORE_DIR/*.sh .claude/hooks/ 2>/dev/null || true
cp $RESTORE_DIR/agents/* .claude/agents/ 2>/dev/null || true
cp $RESTORE_DIR/settings.json .claude/
cp $RESTORE_DIR/settings.local.json .claude/ 2>/dev/null || true
echo "   ✅ 配置文件恢复完成"

# 清理临时文件
rm -rf $TEMP_DIR

# 验证配置
echo "4. 验证配置..."
python -c "
import yaml
try:
    with open('.claude/config/config.yaml', 'r') as f:
        yaml.safe_load(f)
    print('   ✅ 配置文件格式正确')
except Exception as e:
    print('   ❌ 配置文件格式错误:', e)
    exit(1)
"

echo "==============================="
echo "🎉 配置恢复完成!"
echo "⚠️  请重启Claude Enhancer 5.1以使配置生效"
```

#### 配置验证

**配置完整性检查**
```bash
#!/bin/bash
# config_validate.sh

echo "🔍 Claude Enhancer 5.1 配置验证"
echo "==============================="

EXIT_CODE=0

# 检查主配置文件
echo "1. 检查主配置文件..."
if [ -f ".claude/config/config.yaml" ]; then
    python -c "
import yaml
import sys
try:
    with open('.claude/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 检查必需字段
    required_fields = ['system', 'workflow', 'agents', 'performance']
    missing = [field for field in required_fields if field not in config]

    if missing:
        print(f'   ❌ 缺失必需字段: {missing}')
        sys.exit(1)
    else:
        print('   ✅ 主配置文件正确')
except Exception as e:
    print(f'   ❌ 配置文件错误: {e}')
    sys.exit(1)
" || EXIT_CODE=1
else
    echo "   ❌ 主配置文件不存在"
    EXIT_CODE=1
fi

# 检查环境变量文件
echo "2. 检查环境变量文件..."
if [ -f ".env" ]; then
    # 检查必需的环境变量
    REQUIRED_VARS=("CLAUDE_VERSION" "CLAUDE_ENV" "LOG_LEVEL")
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^${var}=" .env; then
            echo "   ✅ $var 已定义"
        else
            echo "   ❌ $var 未定义"
            EXIT_CODE=1
        fi
    done
else
    echo "   ❌ 环境变量文件不存在"
    EXIT_CODE=1
fi

# 检查Hook配置
echo "3. 检查Hook配置..."
if [ -f ".claude/hooks/config.yaml" ]; then
    python -c "
import yaml
try:
    with open('.claude/hooks/config.yaml', 'r') as f:
        hooks = yaml.safe_load(f)
    print('   ✅ Hook配置文件正确')
except Exception as e:
    print(f'   ❌ Hook配置文件错误: {e}')
    exit(1)
" || EXIT_CODE=1
else
    echo "   ❌ Hook配置文件不存在"
    EXIT_CODE=1
fi

# 检查Agent系统
echo "4. 检查Agent系统..."
EXPECTED_AGENTS=61
ACTUAL_AGENTS=$(find .claude/agents -name "*.py" -type f | wc -l)

if [ $ACTUAL_AGENTS -eq $EXPECTED_AGENTS ]; then
    echo "   ✅ Agent系统完整 ($ACTUAL_AGENTS/$EXPECTED_AGENTS)"
else
    echo "   ⚠️  Agent系统不完整 ($ACTUAL_AGENTS/$EXPECTED_AGENTS)"
    # 这里不设置为错误，因为某些环境可能不需要全部Agent
fi

# 检查目录结构
echo "5. 检查目录结构..."
REQUIRED_DIRS=(
    ".claude"
    ".claude/config"
    ".claude/hooks"
    ".claude/agents"
    ".claude/cache"
    "./logs"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "   ✅ $dir 存在"
    else
        echo "   ❌ $dir 不存在"
        EXIT_CODE=1
    fi
done

echo "==============================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "🎉 配置验证通过"
else
    echo "❌ 配置验证失败"
fi

exit $EXIT_CODE
```

### 性能调优

#### CPU和内存优化

**系统资源监控脚本**
```bash
#!/bin/bash
# resource_optimizer.sh

echo "⚡ Claude Enhancer 5.1 性能优化"
echo "=============================="

# CPU使用率分析
echo "1. CPU使用率分析..."
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
CPU_THRESHOLD=80

echo "   当前CPU使用率: ${CPU_USAGE}%"
if (( $(echo "$CPU_USAGE > $CPU_THRESHOLD" | bc -l) )); then
    echo "   ⚠️  CPU使用率过高，建议调整配置:"
    echo "      - 减少并行Agent数量"
    echo "      - 增加任务排队机制"
    echo "      - 考虑水平扩展"
else
    echo "   ✅ CPU使用率正常"
fi

# 内存使用分析
echo -e "\n2. 内存使用分析..."
MEM_INFO=$(free -m)
MEM_TOTAL=$(echo "$MEM_INFO" | awk 'NR==2{print $2}')
MEM_USED=$(echo "$MEM_INFO" | awk 'NR==2{print $3}')
MEM_USAGE=$((MEM_USED * 100 / MEM_TOTAL))

echo "   总内存: ${MEM_TOTAL}MB"
echo "   已使用: ${MEM_USED}MB (${MEM_USAGE}%)"

if [ $MEM_USAGE -gt 85 ]; then
    echo "   ⚠️  内存使用率过高，建议优化:"
    echo "      - 清理缓存"
    echo "      - 调整智能加载配置"
    echo "      - 增加虚拟内存"
elif [ $MEM_USAGE -gt 70 ]; then
    echo "   ⚠️  内存使用率较高，监控中..."
else
    echo "   ✅ 内存使用率正常"
fi

# 磁盘I/O分析
echo -e "\n3. 磁盘I/O分析..."
if command -v iostat &> /dev/null; then
    DISK_UTIL=$(iostat -x 1 2 | tail -n +4 | awk 'END{print $10}')
    echo "   磁盘利用率: ${DISK_UTIL}%"

    if (( $(echo "$DISK_UTIL > 80" | bc -l) )); then
        echo "   ⚠️  磁盘I/O过高，建议优化:"
        echo "      - 使用SSD存储"
        echo "      - 优化日志写入频率"
        echo "      - 分离日志和缓存存储"
    else
        echo "   ✅ 磁盘I/O正常"
    fi
else
    echo "   ⚠️  无法获取磁盘I/O信息（需安装sysstat）"
fi

# 生成优化建议
echo -e "\n4. 优化建议配置..."
cat > /tmp/performance_config.yaml << EOF
# Claude Enhancer 5.1 性能优化配置
performance:
  # 根据系统资源调整
  max_workers: $(( $(nproc) * 2 ))
  memory_limit: "${MEM_TOTAL}MB"

  # 缓存优化
  cache:
    max_size: "$((MEM_TOTAL / 4))MB"
    ttl: 3600
    cleanup_interval: 300

  # Agent并发控制
  agents:
    parallel_limit: $(( $(nproc) + 2 ))
    queue_size: 100
    timeout: 300

  # I/O优化
  logging:
    buffer_size: "64MB"
    flush_interval: 5
    async_write: true
EOF

echo "   ✅ 优化配置已生成: /tmp/performance_config.yaml"
echo "      请根据实际情况合并到主配置文件中"
```

#### 数据库优化（如使用）

**数据库维护脚本**
```bash
#!/bin/bash
# database_maintenance.sh

# 检查是否使用数据库
if ! command -v psql &> /dev/null || ! grep -q "DB_HOST" .env; then
    echo "ℹ️  未检测到数据库配置，跳过数据库维护"
    exit 0
fi

source .env

echo "🗃️ 数据库维护操作"
echo "=================="

# 连接测试
echo "1. 数据库连接测试..."
if psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT version();" &>/dev/null; then
    echo "   ✅ 数据库连接正常"
else
    echo "   ❌ 数据库连接失败"
    exit 1
fi

# 数据库统计
echo -e "\n2. 数据库统计信息..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows
FROM pg_stat_user_tables;
"

# VACUUM操作
echo -e "\n3. 执行VACUUM清理..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "VACUUM ANALYZE;"
echo "   ✅ VACUUM操作完成"

# 索引重建（如果需要）
echo -e "\n4. 检查索引使用情况..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE idx_scan < 100;  -- 很少使用的索引
"

echo "=================="
echo "🎉 数据库维护完成"
```

## 🚨 告警配置

### 系统告警

**告警规则配置**
```yaml
# alerts.yaml
alert_rules:
  - name: "API健康检查失败"
    condition: "api_health_check_failed"
    threshold: 1
    duration: "1m"
    severity: "critical"
    message: "Claude Enhancer API健康检查连续失败"

  - name: "高CPU使用率"
    condition: "cpu_usage > 85"
    threshold: 85
    duration: "5m"
    severity: "warning"
    message: "系统CPU使用率超过85%"

  - name: "高内存使用率"
    condition: "memory_usage > 90"
    threshold: 90
    duration: "3m"
    severity: "critical"
    message: "系统内存使用率超过90%"

  - name: "磁盘空间不足"
    condition: "disk_usage > 85"
    threshold: 85
    duration: "1m"
    severity: "warning"
    message: "磁盘使用率超过85%"

  - name: "高错误率"
    condition: "error_rate > 5"
    threshold: 5
    duration: "2m"
    severity: "critical"
    message: "系统错误率超过5%"

  - name: "响应时间过慢"
    condition: "avg_response_time > 2000"
    threshold: 2000
    duration: "3m"
    severity: "warning"
    message: "平均响应时间超过2秒"

  - name: "Agent执行失败"
    condition: "agent_failure_rate > 10"
    threshold: 10
    duration: "1m"
    severity: "warning"
    message: "Agent执行失败率超过10%"

  - name: "Hook系统异常"
    condition: "hook_errors > 5"
    threshold: 5
    duration: "5m"
    severity: "warning"
    message: "Hook系统5分钟内错误超过5次"

notification_channels:
  - name: "email"
    type: "email"
    config:
      smtp_server: "smtp.company.com"
      recipients: ["admin@company.com", "dev-team@company.com"]

  - name: "slack"
    type: "slack"
    config:
      webhook_url: "https://hooks.slack.com/services/xxx/yyy/zzz"
      channel: "#claude-alerts"

  - name: "sms"
    type: "sms"
    config:
      provider: "twilio"
      recipients: ["+1234567890"]
```

**告警处理脚本**
```bash
#!/bin/bash
# alert_handler.sh

ALERT_TYPE="$1"
ALERT_MESSAGE="$2"
ALERT_SEVERITY="$3"

echo "🚨 Claude Enhancer 5.1 告警处理"
echo "==============================="
echo "告警类型: $ALERT_TYPE"
echo "告警级别: $ALERT_SEVERITY"
echo "告警消息: $ALERT_MESSAGE"
echo "时间: $(date)"

# 根据告警类型执行不同的处理逻辑
case $ALERT_TYPE in
    "api_health_check_failed")
        echo "执行API服务重启..."
        systemctl restart claude-enhancer
        ;;

    "high_cpu_usage")
        echo "启动CPU使用率分析..."
        top -bn1 | head -20 > /tmp/cpu_analysis.txt
        echo "CPU分析结果已保存到 /tmp/cpu_analysis.txt"
        ;;

    "high_memory_usage")
        echo "执行内存清理..."
        curl -X POST http://localhost:8080/api/v1/cache/clear
        echo "缓存已清理"
        ;;

    "disk_space_low")
        echo "执行磁盘清理..."
        ./log_cleanup.sh
        ;;

    "high_error_rate")
        echo "分析错误日志..."
        tail -100 ./logs/error.log > /tmp/recent_errors.txt
        echo "最近错误已保存到 /tmp/recent_errors.txt"
        ;;

    *)
        echo "未知告警类型，执行通用处理..."
        ;;
esac

# 发送通知
if command -v mail &> /dev/null; then
    echo "$ALERT_MESSAGE" | mail -s "Claude Enhancer Alert: $ALERT_TYPE" admin@company.com
fi

# 记录告警历史
echo "$(date): $ALERT_TYPE - $ALERT_SEVERITY - $ALERT_MESSAGE" >> ./logs/alerts.log

echo "==============================="
echo "🎉 告警处理完成"
```

## 📊 性能基准

### 基准测试

**性能基准测试脚本**
```bash
#!/bin/bash
# benchmark.sh

echo "📊 Claude Enhancer 5.1 性能基准测试"
echo "=================================="

RESULTS_FILE="benchmark_results_$(date +%Y%m%d_%H%M%S).json"

# 初始化结果文件
cat > $RESULTS_FILE << EOF
{
    "test_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "5.1.0",
    "system_info": {
        "cpu_cores": $(nproc),
        "memory_gb": $(($(free -b | awk 'NR==2{print $2}') / 1024 / 1024 / 1024)),
        "os": "$(uname -s) $(uname -r)"
    },
    "test_results": {
EOF

# 1. API响应时间测试
echo "1. API响应时间测试..."
echo '        "api_response_time": {' >> $RESULTS_FILE

ENDPOINTS=("/health" "/api/v1/phases" "/api/v1/agents" "/api/v1/hooks/status")
for i, endpoint in enumerate("${ENDPOINTS[@]}"); do
    TOTAL_TIME=0
    SUCCESS_COUNT=0

    for j in {1..100}; do
        START=$(date +%s%N | cut -b1-13)
        HTTP_CODE=$(curl -o /dev/null -s -w "%{http_code}" http://localhost:8080$endpoint)
        END=$(date +%s%N | cut -b1-13)
        RESPONSE_TIME=$((END - START))

        if [ $HTTP_CODE -eq 200 ]; then
            TOTAL_TIME=$((TOTAL_TIME + RESPONSE_TIME))
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        fi
    done

    if [ $SUCCESS_COUNT -gt 0 ]; then
        AVG_TIME=$((TOTAL_TIME / SUCCESS_COUNT))
    else
        AVG_TIME=0
    fi

    # 写入结果
    if [ $i -gt 0 ]; then echo ',' >> $RESULTS_FILE; fi
    echo "            \"$endpoint\": {\"avg_ms\": $AVG_TIME, \"success_rate\": $((SUCCESS_COUNT * 100 / 100))}" >> $RESULTS_FILE
done

echo '        },' >> $RESULTS_FILE

# 2. 并发性能测试
echo "2. 并发性能测试..."
echo '        "concurrent_performance": {' >> $RESULTS_FILE

CONCURRENT_LEVELS=(1 5 10 20 50)
for i, level in enumerate("${CONCURRENT_LEVELS[@]}"); do
    echo "   测试并发级别: $level"

    START_TIME=$(date +%s)

    # 使用GNU parallel或xargs模拟并发
    seq 1 100 | xargs -n 1 -P $level -I {} curl -s http://localhost:8080/health > /dev/null

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    THROUGHPUT=$((100 / DURATION))

    if [ $i -gt 0 ]; then echo ',' >> $RESULTS_FILE; fi
    echo "            \"level_$level\": {\"duration_s\": $DURATION, \"throughput_rps\": $THROUGHPUT}" >> $RESULTS_FILE
done

echo '        },' >> $RESULTS_FILE

# 3. Agent系统性能测试
echo "3. Agent系统性能测试..."
echo '        "agent_performance": {' >> $RESULTS_FILE

# 模拟Agent选择测试
AGENT_STRATEGIES=("smart" "balanced" "manual")
for i, strategy in enumerate("${AGENT_STRATEGIES[@]}"); do
    START_TIME=$(date +%s%N | cut -b1-13)

    # 模拟API调用
    RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/agents/select \
        -H "Content-Type: application/json" \
        -d "{\"strategy\": \"$strategy\", \"task_type\": \"test\", \"agent_count\": 6}")

    END_TIME=$(date +%s%N | cut -b1-13)
    SELECTION_TIME=$((END_TIME - START_TIME))

    if [ $i -gt 0 ]; then echo ',' >> $RESULTS_FILE; fi
    echo "            \"$strategy\": {\"selection_time_ms\": $SELECTION_TIME}" >> $RESULTS_FILE
done

echo '        },' >> $RESULTS_FILE

# 4. 缓存性能测试
echo "4. 缓存性能测试..."
echo '        "cache_performance": {' >> $RESULTS_FILE

# 缓存命中率测试
CACHE_STATS=$(curl -s http://localhost:8080/api/v1/cache/stats)
HIT_RATE=$(echo "$CACHE_STATS" | jq -r '.hit_rate // 0')
CACHE_SIZE=$(echo "$CACHE_STATS" | jq -r '.cache_size // 0')

echo "            \"hit_rate\": $HIT_RATE," >> $RESULTS_FILE
echo "            \"cache_size_mb\": $CACHE_SIZE" >> $RESULTS_FILE
echo '        },' >> $RESULTS_FILE

# 5. 内存使用测试
echo "5. 内存使用测试..."
echo '        "memory_usage": {' >> $RESULTS_FILE

# 获取进程内存使用
PID=$(pgrep -f claude_enhancer | head -1)
if [ ! -z "$PID" ]; then
    MEMORY_KB=$(ps -p $PID -o rss= 2>/dev/null)
    MEMORY_MB=$((MEMORY_KB / 1024))
else
    MEMORY_MB=0
fi

echo "            \"process_memory_mb\": $MEMORY_MB," >> $RESULTS_FILE
echo "            \"system_memory_usage_percent\": $(free | grep Mem | awk '{printf("%.1f"), $3/$2 * 100.0}')" >> $RESULTS_FILE
echo '        }' >> $RESULTS_FILE

# 结束JSON
echo '    }' >> $RESULTS_FILE
echo '}' >> $RESULTS_FILE

echo "=================================="
echo "🎉 性能基准测试完成"
echo "结果文件: $RESULTS_FILE"

# 生成性能报告
python -c "
import json

with open('$RESULTS_FILE', 'r') as f:
    results = json.load(f)

print('\\n📊 性能测试总结:')
print('================')
print(f'测试时间: {results[\"test_date\"]}')
print(f'系统配置: {results[\"system_info\"][\"cpu_cores\"]}核 CPU, {results[\"system_info\"][\"memory_gb\"]}GB 内存')
print()

# API性能
api_results = results['test_results']['api_response_time']
avg_response = sum([api_results[ep]['avg_ms'] for ep in api_results]) / len(api_results)
print(f'API平均响应时间: {avg_response:.1f}ms')

# 内存使用
memory_usage = results['test_results']['memory_usage']
print(f'进程内存使用: {memory_usage[\"process_memory_mb\"]}MB')
print(f'系统内存使用率: {memory_usage[\"system_memory_usage_percent\"]}%')

# 缓存性能
cache_perf = results['test_results']['cache_performance']
print(f'缓存命中率: {cache_perf[\"hit_rate\"] * 100:.1f}%')
"
```

## 🔄 自动化运维

### 系统自检脚本

```bash
#!/bin/bash
# auto_health_check.sh

LOG_FILE="./logs/health_check.log"
ALERT_THRESHOLD=3  # 连续失败3次后告警

echo "🔄 自动健康检查开始 - $(date)" | tee -a $LOG_FILE

# 检查计数器文件
COUNTER_FILE="/tmp/claude_health_check_failures"
if [ ! -f "$COUNTER_FILE" ]; then
    echo "0" > "$COUNTER_FILE"
fi

FAILURE_COUNT=$(cat "$COUNTER_FILE")
CURRENT_FAILURES=0

# 1. API健康检查
echo "检查API健康状态..." | tee -a $LOG_FILE
if ! curl -f -s http://localhost:8080/health > /dev/null; then
    echo "❌ API健康检查失败" | tee -a $LOG_FILE
    CURRENT_FAILURES=$((CURRENT_FAILURES + 1))
else
    echo "✅ API健康正常" | tee -a $LOG_FILE
fi

# 2. 系统资源检查
echo "检查系统资源..." | tee -a $LOG_FILE
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
MEM_USAGE=$(free | grep Mem | awk '{printf("%.1f"), $3/$2 * 100.0}')

if (( $(echo "$CPU_USAGE > 90" | bc -l) )); then
    echo "❌ CPU使用率过高: ${CPU_USAGE}%" | tee -a $LOG_FILE
    CURRENT_FAILURES=$((CURRENT_FAILURES + 1))
else
    echo "✅ CPU使用率正常: ${CPU_USAGE}%" | tee -a $LOG_FILE
fi

if (( $(echo "$MEM_USAGE > 95" | bc -l) )); then
    echo "❌ 内存使用率过高: ${MEM_USAGE}%" | tee -a $LOG_FILE
    CURRENT_FAILURES=$((CURRENT_FAILURES + 1))
else
    echo "✅ 内存使用率正常: ${MEM_USAGE}%" | tee -a $LOG_FILE
fi

# 3. 日志错误检查
echo "检查错误日志..." | tee -a $LOG_FILE
RECENT_ERRORS=$(find ./logs -name "*.log" -mmin -5 -exec grep -c "ERROR\|CRITICAL" {} \; | awk '{sum+=$1} END {print sum+0}')

if [ $RECENT_ERRORS -gt 10 ]; then
    echo "❌ 最近5分钟内错误过多: ${RECENT_ERRORS}条" | tee -a $LOG_FILE
    CURRENT_FAILURES=$((CURRENT_FAILURES + 1))
else
    echo "✅ 错误日志正常: ${RECENT_ERRORS}条" | tee -a $LOG_FILE
fi

# 4. 更新失败计数器
if [ $CURRENT_FAILURES -gt 0 ]; then
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
else
    FAILURE_COUNT=0
fi
echo "$FAILURE_COUNT" > "$COUNTER_FILE"

# 5. 告警处理
if [ $FAILURE_COUNT -ge $ALERT_THRESHOLD ]; then
    echo "🚨 连续$FAILURE_COUNT次健康检查失败，触发告警" | tee -a $LOG_FILE
    ./alert_handler.sh "health_check_failed" "连续$FAILURE_COUNT次健康检查失败" "critical"

    # 尝试自动恢复
    echo "🔄 尝试自动恢复..." | tee -a $LOG_FILE
    systemctl restart claude-enhancer 2>/dev/null || ./restart.sh

    # 重置计数器
    echo "0" > "$COUNTER_FILE"
fi

echo "🔄 自动健康检查完成 - $(date)" | tee -a $LOG_FILE
echo "----------------------------------------" | tee -a $LOG_FILE
```

### Cron任务配置

```bash
# Claude Enhancer 5.1 Cron任务配置
# 编辑: crontab -e

# 每5分钟执行健康检查
*/5 * * * * /home/xx/dev/Claude\ Enhancer\ 5.0/auto_health_check.sh

# 每小时执行性能监控
0 * * * * /home/xx/dev/Claude\ Enhancer\ 5.0/resource_optimizer.sh >> /home/xx/dev/Claude\ Enhancer\ 5.0/logs/performance.log

# 每天凌晨2点执行日志清理
0 2 * * * /home/xx/dev/Claude\ Enhancer\ 5.0/log_cleanup.sh

# 每天凌晨3点执行配置备份
0 3 * * * /home/xx/dev/Claude\ Enhancer\ 5.0/config_backup.sh

# 每周日凌晨4点执行完整系统检查
0 4 * * 0 /home/xx/dev/Claude\ Enhancer\ 5.0/full_system_check.sh

# 每月1日执行性能基准测试
0 6 1 * * /home/xx/dev/Claude\ Enhancer\ 5.0/benchmark.sh

# 每15分钟检查磁盘空间
*/15 * * * * df -h / | awk 'NR==2{if($5+0 > 85) system("echo 磁盘空间不足: "$5" | logger -t claude-enhancer")}'
```

---

**📋 运维检查清单**

### 日常运维检查清单

**每日检查** ✅
- [ ] API健康状态检查
- [ ] 系统资源使用率检查
- [ ] 错误日志审查
- [ ] 备份状态确认
- [ ] 关键指标监控

**每周检查** ✅
- [ ] 完整系统性能分析
- [ ] 日志文件清理和轮转
- [ ] 配置文件完整性检查
- [ ] 安全更新检查
- [ ] 告警规则验证

**每月检查** ✅
- [ ] 性能基准测试
- [ ] 容量规划评估
- [ ] 监控数据分析
- [ ] 灾难恢复演练
- [ ] 文档更新

**📞 紧急联系方式**
- 技术负责人: xxx-xxxx-xxxx
- 运维团队: ops@company.com
- 24/7支持: support@company.com

**🔗 相关文档**
- [部署指南 DEPLOYMENT.md](DEPLOYMENT.md)
- [故障排除 TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [版本发布说明 RELEASE_NOTES.md](RELEASE_NOTES.md)

---

**💡 最佳实践**

1. **预防性维护** - 定期执行系统检查，预防问题发生
2. **自动化优先** - 尽可能自动化重复性运维任务
3. **监控驱动** - 基于监控数据进行运维决策
4. **文档化** - 记录所有运维操作和变更
5. **持续改进** - 定期评估和优化运维流程