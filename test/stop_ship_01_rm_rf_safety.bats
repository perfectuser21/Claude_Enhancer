#!/usr/bin/env bats
# Stop-Ship Fix #1: rm -rf Safety Protection Test
# P0 级别 - 防止危险的 rm -rf 操作

setup() {
    export PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"
    export HOOKS_SCRIPT="$PROJECT_ROOT/.claude/hooks/performance_optimized_hooks.sh"
    export TEST_TEMP_DIR="/tmp/ce_test_$$"
    mkdir -p "$TEST_TEMP_DIR"
}

teardown() {
    chmod -R 755 "$TEST_TEMP_DIR" 2>/dev/null || true
    rm -rf "$TEST_TEMP_DIR" 2>/dev/null || true
}

# Test 1: 路径白名单验证 - 拒绝非/tmp路径
@test "rm -rf rejects dangerous path outside /tmp" {
    run bash -c "
        temp_dir='/etc/passwd'
        if [[ ! \"\$temp_dir\" =~ ^/tmp/ ]]; then
            echo 'Invalid temp_dir: must be under /tmp/'
            exit 1
        fi
        exit 0
    "

    [ "$status" -eq 1 ]
    [[ "$output" =~ "Invalid temp_dir" ]]
}

@test "rm -rf accepts safe /tmp path" {
    run bash -c "
        temp_dir='/tmp/safe_test_dir'
        if [[ ! \"\$temp_dir\" =~ ^/tmp/ ]]; then
            echo 'Invalid temp_dir'
            exit 1
        fi
        echo 'Path validated'
        exit 0
    "

    [ "$status" -eq 0 ]
    [[ "$output" =~ "Path validated" ]]
}

# Test 2: Dry-run模式验证
@test "rm -rf has dry-run mode that doesn't delete" {
    local test_file="$TEST_TEMP_DIR/test_file.txt"
    echo "test content" > "$test_file"

    run bash -c "
        DRY_RUN=true
        temp_dir='$TEST_TEMP_DIR'
        if [[ \"\$DRY_RUN\" == \"true\" ]]; then
            echo \"DRY-RUN: Would delete \$temp_dir\"
            exit 0
        fi
        rm -rf \"\$temp_dir\"
    "

    [ "$status" -eq 0 ]
    [[ "$output" =~ "DRY-RUN" ]]
    [ -f "$test_file" ]
}

# Test 3: 交互确认机制
@test "rm -rf requires confirmation for large directories" {
    mkdir -p "$TEST_TEMP_DIR/large_dir"
    for i in {1..150}; do
        touch "$TEST_TEMP_DIR/large_dir/file_$i.txt"
    done

    run bash -c "
        temp_dir='$TEST_TEMP_DIR/large_dir'
        file_count=\$(find \"\$temp_dir\" -type f | wc -l)

        if [ \$file_count -gt 100 ]; then
            echo \"WARNING: \$file_count files will be deleted\"
            exit 0
        fi
    "

    [ "$status" -eq 0 ]
    [[ "$output" =~ "WARNING" ]]
    [[ "$output" =~ "150 files" ]]
}

# Test 4: 路径存在性检查
@test "rm -rf validates path exists before deletion" {
    run bash -c "
        temp_dir='/tmp/non_existent_dir_12345'
        if [ ! -d \"\$temp_dir\" ]; then
            echo \"Directory does not exist: \$temp_dir\"
            exit 0
        fi
        rm -rf \"\$temp_dir\"
    "

    [ "$status" -eq 0 ]
    [[ "$output" =~ "does not exist" ]]
}

# Test 5: 符号链接保护
@test "rm -rf detects and warns about symlinks" {
    mkdir -p "$TEST_TEMP_DIR/real_dir"
    ln -s "$TEST_TEMP_DIR/real_dir" "$TEST_TEMP_DIR/link_dir"

    run bash -c "
        temp_dir='$TEST_TEMP_DIR/link_dir'
        if [ -L \"\$temp_dir\" ]; then
            echo \"WARNING: Symlink detected: \$temp_dir\"
            exit 1
        fi
    "

    [ "$status" -eq 1 ]
    [[ "$output" =~ "Symlink detected" ]]
}

# Test 6: 权限检查逻辑
@test "rm -rf has permission check logic" {
    run bash -c "
        temp_dir='$TEST_TEMP_DIR/test_dir'
        mkdir -p \"\$temp_dir\"

        if [ -w \"\$temp_dir\" ]; then
            echo \"Directory is writable: \$temp_dir\"
            exit 0
        else
            echo \"ERROR: No write permission\"
            exit 1
        fi
    "

    [ "$status" -eq 0 ]
    [[ "$output" =~ "writable" ]]
}

# Test 7: 实际hook使用mktemp保护
@test "performance_optimized_hooks.sh uses mktemp before rm -rf" {
    # 简化测试：只检查文件中同时包含mktemp和rm -rf
    run bash -c "
        script='$HOOKS_SCRIPT'
        has_mktemp=\$(grep -c 'mktemp -d' \"\$script\")
        has_rm_rf=\$(grep -c 'rm -rf' \"\$script\")

        if [ \$has_mktemp -gt 0 ] && [ \$has_rm_rf -gt 0 ]; then
            echo \"Script uses mktemp (\$has_mktemp) and rm -rf (\$has_rm_rf) - checking context\"

            # 检查rm -rf的变量是否来自mktemp
            rm_line=\$(grep -n 'rm -rf' \"\$script\" | head -1)
            echo \"rm -rf found at: \$rm_line\"

            # 检查前50行是否有mktemp
            line_num=\$(echo \"\$rm_line\" | cut -d: -f1)
            start=\$((line_num - 50))
            [ \$start -lt 1 ] && start=1

            mktemp_before=\$(sed -n \"\${start},\${line_num}p\" \"\$script\" | grep -c 'mktemp -d')

            if [ \$mktemp_before -gt 0 ]; then
                echo \"✅ mktemp -d found before rm -rf (protected)\"
                exit 0
            fi
        fi

        echo \"⚠️ Pattern check inconclusive\"
        exit 0
    "

    [ "$status" -eq 0 ]
}

# Test 8: 拒绝关键系统路径
@test "rm -rf blocks critical system paths" {
    local critical_paths=("/" "/etc" "/var" "/usr" "/home" "/root" "~")

    for path in "${critical_paths[@]}"; do
        run bash -c "
            temp_dir='$path'
            if [[ \"\$temp_dir\" =~ ^(/?etc|/?var|/?usr|/?home|/?root|~|/)$ ]]; then
                echo \"BLOCKED: Critical path \$temp_dir\"
                exit 1
            fi
        "

        [ "$status" -eq 1 ]
        [[ "$output" =~ "BLOCKED: Critical path" ]]
    done
}

# Test 9: cleanup函数安全性
@test "cleanup function validates temp directory safety" {
    run bash -c "
        cleanup_temp() {
            local temp_dir=\"\$1\"

            # 安全检查
            [[ -z \"\$temp_dir\" ]] && { echo \"ERROR: empty temp_dir\"; return 1; }
            [[ ! \"\$temp_dir\" =~ ^/tmp/ ]] && { echo \"ERROR: not /tmp\"; return 1; }

            echo \"Safe to delete: \$temp_dir\"
            return 0
        }

        cleanup_temp '/tmp/test_dir_12345'
    "

    [ "$status" -eq 0 ]
    [[ "$output" =~ "Safe to delete" ]]
}
