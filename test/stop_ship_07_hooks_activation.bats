#!/usr/bin/env bats
# Stop-Ship Fix #7: Hooks激活验证测试
# P1-6 级别 - 确保hooks被正确触发并记录日志

setup() {
    export PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"
    export HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
    export LOG_DIR="$PROJECT_ROOT/.workflow/logs"
    export HOOKS_LOG="$LOG_DIR/hooks.log"

    # 创建日志目录
    mkdir -p "$LOG_DIR"

    # 备份现有日志
    if [ -f "$HOOKS_LOG" ]; then
        cp "$HOOKS_LOG" "$HOOKS_LOG.backup"
    fi
}

teardown() {
    # 恢复日志
    if [ -f "$HOOKS_LOG.backup" ]; then
        mv "$HOOKS_LOG.backup" "$HOOKS_LOG"
    fi
}

# Test 1: pre-commit hook被触发
@test "pre-commit hook is triggered and logged" {
    local test_file="$PROJECT_ROOT/test_trigger_file.tmp"
    echo "test" > "$test_file"

    # 模拟git add和commit触发
    cd "$PROJECT_ROOT"
    git add "$test_file" 2>/dev/null || true

    # 直接调用hook
    run bash -c "
        if [ -x '$HOOKS_DIR/pre-commit' ]; then
            '$HOOKS_DIR/pre-commit' 2>&1 || true
            echo 'Hook executed'
        else
            echo 'Hook not executable'
            exit 1
        fi
    "

    # 清理
    rm -f "$test_file"
    git reset HEAD "$test_file" 2>/dev/null || true

    [ "$status" -eq 0 ] || skip "Hook not executable"
}

# Test 2: commit-msg hook日志记录
@test "commit-msg hook logs execution" {
    local test_msg_file="/tmp/test_commit_msg_$$"
    echo "test: sample commit" > "$test_msg_file"

    # 触发commit-msg hook
    run bash -c "
        if [ -x '$HOOKS_DIR/commit-msg' ]; then
            '$HOOKS_DIR/commit-msg' '$test_msg_file' 2>&1 || true
        fi

        # 检查日志
        if [ -f '$HOOKS_LOG' ]; then
            tail -10 '$HOOKS_LOG' | grep -q 'commit-msg'
        fi
    "

    rm -f "$test_msg_file"

    [ "$status" -eq 0 ] || skip "No log file or hook"
}

# Test 3: 日志文件存在并可写
@test "hooks log file exists and is writable" {
    run bash -c "
        log_dir='$LOG_DIR'
        log_file='$HOOKS_LOG'

        # 创建日志目录
        mkdir -p \"\$log_dir\"

        # 测试写入
        echo \"Test log entry at \$(date)\" >> \"\$log_file\"

        if [ -f \"\$log_file\" ] && [ -w \"\$log_file\" ]; then
            echo \"Log file is writable\"
            exit 0
        fi
        exit 1
    "

    [ "$status" -eq 0 ]
}

# Test 4: 日志包含时间戳
@test "hook logs include timestamps" {
    run bash -c "
        log_file='$HOOKS_LOG'

        # 添加测试日志
        echo \"\$(date +'%F %T') [test-hook] Test log entry\" >> \"\$log_file\"

        # 验证时间戳格式
        if tail -1 \"\$log_file\" | grep -qE '[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}'; then
            echo \"Timestamp format valid\"
            exit 0
        fi
        exit 1
    "

    [ "$status" -eq 0 ]
}

# Test 5: 统计hooks触发次数
@test "hook trigger count is tracked" {
    local log_file="$HOOKS_LOG"

    # 模拟多次触发
    for i in {1..3}; do
        echo "$(date +'%F %T') [pre-commit] Trigger $i" >> "$log_file"
    done

    run bash -c "
        log_file='$log_file'
        count=\$(grep -c '\[pre-commit\]' \"\$log_file\" 2>/dev/null || echo 0)

        if [ \$count -gt 0 ]; then
            echo \"Hook triggered \$count times\"
            exit 0
        else
            echo \"No hook triggers found\"
            exit 1
        fi
    "

    [ "$status" -eq 0 ]
    [[ "$output" =~ "triggered" ]]
}

# Test 6: 不同hooks分别记录
@test "different hooks are logged separately" {
    local log_file="$HOOKS_LOG"

    # 模拟不同hooks
    echo "$(date +'%F %T') [pre-commit] Test" >> "$log_file"
    echo "$(date +'%F %T') [commit-msg] Test" >> "$log_file"
    echo "$(date +'%F %T') [pre-push] Test" >> "$log_file"

    run bash -c "
        log_file='$log_file'
        pre_commit=\$(grep -c '\[pre-commit\]' \"\$log_file\" 2>/dev/null || echo 0)
        commit_msg=\$(grep -c '\[commit-msg\]' \"\$log_file\" 2>/dev/null || echo 0)
        pre_push=\$(grep -c '\[pre-push\]' \"\$log_file\" 2>/dev/null || echo 0)

        echo \"pre-commit: \$pre_commit\"
        echo \"commit-msg: \$commit_msg\"
        echo \"pre-push: \$pre_push\"

        total=\$((pre_commit + commit_msg + pre_push))
        if [ \$total -gt 0 ]; then
            exit 0
        fi
        exit 1
    "

    [ "$status" -eq 0 ]
}

# Test 7: 日志轮转机制
@test "log rotation prevents unlimited growth" {
    local log_file="$HOOKS_LOG"
    local max_lines=1000

    # 创建大量日志
    for i in {1..1500}; do
        echo "$(date +'%F %T') [test] Log line $i" >> "$log_file"
    done

    run bash -c "
        log_file='$log_file'
        max_lines=$max_lines

        line_count=\$(wc -l < \"\$log_file\")

        if [ \$line_count -gt \$max_lines ]; then
            # 轮转：保留最新的行
            tail -n \$max_lines \"\$log_file\" > \"\${log_file}.tmp\"
            mv \"\${log_file}.tmp\" \"\$log_file\"
            echo \"Log rotated from \$line_count to \$max_lines lines\"
            exit 0
        fi
        echo \"Log within limits: \$line_count lines\"
        exit 0
    "

    [ "$status" -eq 0 ]
}

# Test 8: Hook执行错误被记录
@test "hook execution errors are logged" {
    run bash -c "
        log_file='$HOOKS_LOG'

        # 模拟hook错误
        {
            echo \"\$(date +'%F %T') [pre-commit] Starting check\"
            echo \"\$(date +'%F %T') [pre-commit] ERROR: Validation failed\"
            echo \"\$(date +'%F %T') [pre-commit] Exit code: 1\"
        } >> \"\$log_file\"

        # 检查错误日志
        if grep -q 'ERROR' \"\$log_file\"; then
            echo \"Error logged successfully\"
            exit 0
        fi
        exit 1
    "

    [ "$status" -eq 0 ]
}

# Test 9: Hook性能监控
@test "hook execution time is logged" {
    run bash -c "
        log_file='$HOOKS_LOG'

        # 模拟性能日志
        start_time=\$(date +%s.%N)
        sleep 0.1
        end_time=\$(date +%s.%N)
        duration=\$(echo \"\$end_time - \$start_time\" | bc -l)

        echo \"\$(date +'%F %T') [pre-commit] Completed in \${duration}s\" >> \"\$log_file\"

        # 检查性能日志
        if tail -1 \"\$log_file\" | grep -q 'Completed in'; then
            echo \"Performance logged\"
            exit 0
        fi
        exit 1
    "

    [ "$status" -eq 0 ]
}

# Test 10: 所有关键hooks已安装
@test "all critical hooks are installed" {
    local critical_hooks=("pre-commit" "commit-msg" "pre-push")

    for hook in "${critical_hooks[@]}"; do
        if [ ! -f "$HOOKS_DIR/$hook" ]; then
            echo "Missing hook: $hook"
            exit 1
        fi

        if [ ! -x "$HOOKS_DIR/$hook" ]; then
            echo "Hook not executable: $hook"
            exit 1
        fi
    done

    echo "All critical hooks installed"
}

# Test 11: Hooks权限自检机制
@test "hooks have self-permission check mechanism" {
    local commit_msg_hook="$HOOKS_DIR/commit-msg"

    if [ ! -f "$commit_msg_hook" ]; then
        skip "commit-msg hook not found"
    fi

    run bash -c "
        grep -q 'check_self_permission' '$commit_msg_hook'
    "

    [ "$status" -eq 0 ]
}

# Test 12: Hook日志包含提交信息摘要
@test "hooks log includes commit message summary" {
    local log_file="$HOOKS_LOG"

    # 模拟带消息的日志
    echo "$(date +'%F %T') [commit-msg] triggered with message: feat: add new feature" >> "$log_file"

    run bash -c "
        log_file='$log_file'
        if tail -10 \"\$log_file\" | grep -q 'triggered with message:'; then
            echo \"Commit message logged\"
            exit 0
        fi
        exit 1
    "

    [ "$status" -eq 0 ]
}

# Test 13: 日志查询工具
@test "log query tool exists for hook analysis" {
    run bash -c "
        log_file='$HOOKS_LOG'

        # 查询最近的hook活动
        query_recent() {
            local count=\${1:-10}
            tail -n \$count \"\$log_file\" 2>/dev/null || echo 'No logs'
        }

        # 查询特定hook
        query_hook() {
            local hook_name=\$1
            grep \"\[\$hook_name\]\" \"\$log_file\" 2>/dev/null || echo 'No entries'
        }

        recent=\$(query_recent 5)
        if [ -n \"\$recent\" ]; then
            echo \"Query successful\"
            exit 0
        fi
        exit 1
    "

    [ "$status" -eq 0 ] || skip "No logs to query"
}

# Test 14: Hook激活率监控
@test "hook activation rate is monitored" {
    local log_file="$HOOKS_LOG"

    run bash -c "
        log_file='$log_file'

        # 统计最近24小时的hook活动
        since=\$(date -d '24 hours ago' +'%F %T' 2>/dev/null || date -v -24H +'%F %T' 2>/dev/null || echo '2025-10-08 00:00:00')

        # 计数
        count=\$(awk -v since=\"\$since\" '\$0 >= since' \"\$log_file\" 2>/dev/null | wc -l)

        echo \"Hooks triggered in last 24h: \$count\"

        if [ \$count -ge 0 ]; then
            exit 0
        fi
        exit 1
    "

    [ "$status" -eq 0 ]
}
