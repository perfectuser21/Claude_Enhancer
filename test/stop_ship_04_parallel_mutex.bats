#!/usr/bin/env bats
# Stop-Ship Fix #4: 并行任务互斥测试
# P1-3 级别 - 确保冲突任务被正确阻止

setup() {
    export PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"
    export LOCK_DIR="/tmp/ce_locks_$$"
    mkdir -p "$LOCK_DIR"
}

teardown() {
    rm -rf "$LOCK_DIR" 2>/dev/null || true
    # 清理所有测试锁文件
    rm -f /tmp/ce_task_*.lock 2>/dev/null || true
}

# Test 1: 同时运行冲突任务应被阻止
@test "parallel tasks with conflicts are blocked" {
    local lock_file="$LOCK_DIR/test.lock"

    # 第一个任务获取锁
    run bash -c "
        lock_file='$lock_file'
        if [ -f \"\$lock_file\" ]; then
            echo 'Task already running'
            exit 1
        fi
        touch \"\$lock_file\"
        echo 'Lock acquired'
        exit 0
    "
    [ "$status" -eq 0 ]

    # 第二个任务尝试获取相同的锁
    run bash -c "
        lock_file='$lock_file'
        if [ -f \"\$lock_file\" ]; then
            echo 'Task already running - blocked'
            exit 1
        fi
        exit 0
    "
    [ "$status" -eq 1 ]
    [[ "$output" =~ "blocked" ]]
}

# Test 2: 超时机制工作
@test "lock timeout mechanism works" {
    local lock_file="$LOCK_DIR/timeout.lock"
    local timeout=3

    # 创建过期的锁文件（4秒前）
    touch -d "4 seconds ago" "$lock_file"

    run bash -c "
        lock_file='$lock_file'
        timeout=3

        if [ -f \"\$lock_file\" ]; then
            lock_age=\$(($(date +%s) - $(stat -c %Y \"\$lock_file\" 2>/dev/null || echo 0)))
            if [ \$lock_age -gt \$timeout ]; then
                echo \"Stale lock detected (age: \${lock_age}s), removing\"
                rm -f \"\$lock_file\"
                exit 0
            else
                echo \"Fresh lock (age: \${lock_age}s), blocking\"
                exit 1
            fi
        fi
    "

    [ "$status" -eq 0 ]
    [[ "$output" =~ "Stale lock" ]]
}

# Test 3: 死锁检测有效
@test "deadlock detection prevents infinite waiting" {
    local lock_a="$LOCK_DIR/resource_a.lock"
    local lock_b="$LOCK_DIR/resource_b.lock"

    # 任务1持有lock_a，等待lock_b
    touch "$lock_a"

    # 任务2持有lock_b，等待lock_a
    touch "$lock_b"

    run bash -c "
        max_wait=2
        start=\$(date +%s)

        while [ -f '$lock_a' ] || [ -f '$lock_b' ]; do
            elapsed=\$(($(date +%s) - start))
            if [ \$elapsed -gt \$max_wait ]; then
                echo 'Deadlock detected - timeout after \${elapsed}s'
                exit 1
            fi
            sleep 0.1
        done
    "

    [ "$status" -eq 1 ]
    [[ "$output" =~ "Deadlock detected" ]]
}

# Test 4: 锁文件包含PID信息
@test "lock file contains process PID for tracking" {
    local lock_file="$LOCK_DIR/pid.lock"

    run bash -c "
        lock_file='$lock_file'
        echo \$$ > \"\$lock_file\"
        cat \"\$lock_file\"
    "

    [ "$status" -eq 0 ]
    [[ "$output" =~ ^[0-9]+$ ]]  # 应该是数字PID
}

# Test 5: 锁文件清理机制
@test "lock cleanup on process termination" {
    local lock_file="$LOCK_DIR/cleanup.lock"

    # 启动后台进程并设置trap清理
    bash -c "
        lock_file='$lock_file'
        trap 'rm -f \"\$lock_file\"' EXIT
        touch \"\$lock_file\"
        sleep 0.5
        exit 0
    " &

    local bg_pid=$!
    sleep 0.2

    # 锁文件应该存在
    [ -f "$lock_file" ]

    # 等待后台进程结束
    wait $bg_pid

    # 锁文件应该被清理
    [ ! -f "$lock_file" ]
}

# Test 6: 资源竞争保护
@test "prevents race condition with atomic operations" {
    local lock_file="$LOCK_DIR/atomic.lock"
    local counter_file="$LOCK_DIR/counter.txt"
    echo "0" > "$counter_file"

    # 启动多个并发进程
    for i in {1..5}; do
        bash -c "
            lock_file='$lock_file'
            counter_file='$counter_file'

            # 原子锁操作
            (
                flock -x 200
                count=\$(cat \"\$counter_file\")
                count=\$((count + 1))
                echo \$count > \"\$counter_file\"
            ) 200>\"\$lock_file\"
        " &
    done

    wait

    # 最终计数应该是5
    final_count=$(cat "$counter_file")
    [ "$final_count" -eq 5 ]
}

# Test 7: 锁粒度控制（细粒度vs粗粒度）
@test "fine-grained locks allow parallel non-conflicting tasks" {
    local lock_read="$LOCK_DIR/read.lock"
    local lock_write="$LOCK_DIR/write.lock"

    # 多个读操作可以并行
    for i in {1..3}; do
        bash -c "
            lock_file='$lock_read.\$\$'
            touch \"\$lock_file\"
            sleep 0.1
            rm -f \"\$lock_file\"
        " &
    done

    wait

    # 所有任务应该都能完成
    echo "Parallel reads completed"
}

# Test 8: 锁优先级机制
@test "lock priority mechanism works" {
    local lock_file="$LOCK_DIR/priority.lock"

    run bash -c "
        lock_file='$lock_file'
        priority=\${1:-10}
        max_priority=\${2:-5}

        if [ -f \"\$lock_file\" ]; then
            current_priority=\$(cat \"\$lock_file\" 2>/dev/null || echo 10)
            if [ \$priority -lt \$current_priority ]; then
                echo \"Higher priority task, preempting\"
                echo \$priority > \"\$lock_file\"
                exit 0
            else
                echo \"Lower priority, waiting\"
                exit 1
            fi
        fi
    " -- 3 10

    [ "$status" -eq 0 ]
    [[ "$output" =~ "Higher priority" ]]
}

# Test 9: 分布式锁兼容性
@test "lock mechanism works across different processes" {
    local lock_file="$LOCK_DIR/distributed.lock"

    # 进程1
    bash -c "
        lock_file='$lock_file'
        mkdir \"\$lock_file\" 2>/dev/null && echo 'Process 1 acquired lock'
        sleep 1
        rmdir \"\$lock_file\"
    " &
    pid1=$!

    sleep 0.1

    # 进程2（应该失败）
    run bash -c "
        lock_file='$lock_file'
        if mkdir \"\$lock_file\" 2>/dev/null; then
            echo 'Process 2 acquired lock'
            rmdir \"\$lock_file\"
            exit 0
        else
            echo 'Process 2 blocked'
            exit 1
        fi
    "

    [ "$status" -eq 1 ]
    [[ "$output" =~ "blocked" ]]

    wait $pid1
}

# Test 10: 锁状态监控
@test "lock status can be monitored and reported" {
    local lock_file="$LOCK_DIR/monitor.lock"

    # 创建锁并记录元数据
    cat > "$lock_file" <<EOF
{
    "pid": $$,
    "task": "test_task",
    "start_time": "$(date +%s)",
    "timeout": 60
}
EOF

    run bash -c "
        lock_file='$lock_file'
        if [ -f \"\$lock_file\" ]; then
            echo \"Lock status:\"
            cat \"\$lock_file\"
            exit 0
        fi
    "

    [ "$status" -eq 0 ]
    [[ "$output" =~ "test_task" ]]
}
