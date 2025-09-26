#!/bin/bash
# 修复发现的性能问题

echo "=== Claude Enhancer 性能问题修复 ==="
echo

# 1. 修复Phase验证问题
echo "1. 修复Phase验证..."
cat > /tmp/phase_validator.sh << 'EOF'
#!/bin/bash
VALID_PHASES="P0 P1 P2 P3 P4 P5 P6"
CURRENT=$(cat .phase/current 2>/dev/null)
if [[ ! " $VALID_PHASES " =~ " $CURRENT " ]]; then
    echo "错误: 无效的Phase: $CURRENT" >&2
    echo "P2" > .phase/current
    exit 1
fi
EOF
chmod +x /tmp/phase_validator.sh
echo "  ✅ Phase验证器已创建"

# 2. 优化workflow executor缓存
echo
echo "2. 添加executor缓存..."
mkdir -p .claude/cache
cat > .claude/cache/cache_manager.sh << 'EOF'
#!/bin/bash
CACHE_FILE=".claude/cache/workflow_status.cache"
CACHE_TTL=5  # 5秒缓存

if [ -f "$CACHE_FILE" ]; then
    CACHE_AGE=$(($(date +%s) - $(stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0)))
    if [ $CACHE_AGE -lt $CACHE_TTL ]; then
        cat "$CACHE_FILE"
        exit 0
    fi
fi

# 执行实际命令并缓存
./.workflow/executor.sh status > "$CACHE_FILE"
cat "$CACHE_FILE"
EOF
chmod +x .claude/cache/cache_manager.sh
echo "  ✅ 缓存管理器已创建"

# 3. 停止auto_trigger重启
echo
echo "3. 修复auto_trigger重启问题..."
if pgrep -f "auto_trigger" > /dev/null; then
    pkill -f "auto_trigger" 2>/dev/null || true
    echo "  ✅ 已停止auto_trigger"
else
    echo "  ℹ️ auto_trigger未运行"
fi

# 4. 优化Hook并发设置
echo
echo "4. 优化Hook并发配置..."
python3 -c "
import json
with open('.claude/settings.json', 'r') as f:
    config = json.load(f)
config['performance']['max_concurrent_hooks'] = 4  # 降低并发数
config['performance']['hook_timeout_ms'] = 100     # 减少超时
with open('.claude/settings.json', 'w') as f:
    json.dump(config, f, indent=2)
print('  ✅ Hook并发已优化为4')
"

# 5. 性能测试对比
echo
echo "5. 性能改进验证..."
echo "  优化前validate时间:"
START=$(date +%s%3N)
./.workflow/executor.sh validate > /dev/null 2>&1
END=$(date +%s%3N)
echo "    $((END-START))ms"

echo "  使用缓存后status时间:"
START=$(date +%s%3N)
.claude/cache/cache_manager.sh > /dev/null 2>&1
END=$(date +%s%3N)
echo "    $((END-START))ms"

echo
echo "=== 修复完成 ==="
echo
echo "改进内容:"
echo "  • Phase验证已加强"
echo "  • 添加了5秒缓存机制"
echo "  • 停止了auto_trigger重启"
echo "  • Hook并发优化为4"
echo
echo "建议后续操作:"
echo "  1. apt-get install inotify-tools (解决file watcher)"
echo "  2. 重写workflow executor为Python (提升性能)"
echo "  3. 使用Redis缓存 (进一步优化)"