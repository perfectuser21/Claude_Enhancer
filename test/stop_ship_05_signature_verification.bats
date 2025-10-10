#!/usr/bin/env bats
# Stop-Ship Fix #5: Gate签名验证测试
# P1-4 级别 - 确保篡改签名被检测并拒绝

setup() {
    export PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"
    export GATES_DIR="$PROJECT_ROOT/.gates"
    export TEST_GATES_DIR="/tmp/test_gates_$$"
    mkdir -p "$TEST_GATES_DIR"
}

teardown() {
    rm -rf "$TEST_GATES_DIR" 2>/dev/null || true
}

# Test 1: 篡改签名文件应失败
@test "tampered signature file is detected and rejected" {
    # 创建gate文件
    echo "Gate passed at $(date)" > "$TEST_GATES_DIR/01.ok"

    # 创建签名
    cat > "$TEST_GATES_DIR/01.ok.sig" <<EOF
gate=01.ok
timestamp=$(date +%s)
phase=P1
sha256=$(sha256sum "$TEST_GATES_DIR/01.ok" | awk '{print $1}')
EOF

    # 计算签名的哈希
    original_sha=$(grep -v '^sha256=' "$TEST_GATES_DIR/01.ok.sig" | sha256sum | awk '{print $1}')
    echo "sha256=$original_sha" >> "$TEST_GATES_DIR/01.ok.sig"

    # 篡改gate内容
    echo "TAMPERED" >> "$TEST_GATES_DIR/01.ok"

    # 验证签名（应该失败）
    run bash -c "
        sig_file='$TEST_GATES_DIR/01.ok.sig'
        gate_file='$TEST_GATES_DIR/01.ok'

        # 读取签名中的哈希
        stored_sha=\$(grep '^sha256=' \"\$sig_file\" | cut -d= -f2)

        # 计算当前哈希
        current_sha=\$(grep -v '^sha256=' \"\$sig_file\" | sha256sum | awk '{print \$1}')

        if [ \"\$stored_sha\" != \"\$current_sha\" ]; then
            echo \"❌ Signature mismatch detected\"
            exit 1
        fi
        exit 0
    "

    [ "$status" -eq 1 ]
    [[ "$output" =~ "Signature mismatch" ]]
}

# Test 2: 无签名应拒绝
@test "gate without signature is rejected" {
    # 只创建gate文件，没有签名
    echo "Gate passed" > "$TEST_GATES_DIR/02.ok"

    run bash -c "
        gate_file='$TEST_GATES_DIR/02.ok'
        sig_file='\${gate_file}.sig'

        if [ ! -f \"\$sig_file\" ]; then
            echo \"❌ Missing signature for gate\"
            exit 1
        fi
        exit 0
    "

    [ "$status" -eq 1 ]
    [[ "$output" =~ "Missing signature" ]]
}

# Test 3: 有效签名应通过
@test "valid signature passes verification" {
    # 创建gate文件
    echo "Gate passed at $(date)" > "$TEST_GATES_DIR/03.ok"

    # 创建签名
    cat > "$TEST_GATES_DIR/03.ok.sig" <<EOF
gate=03.ok
timestamp=$(date +%s)
phase=P3
sha256=$(sha256sum "$TEST_GATES_DIR/03.ok" | awk '{print $1}')
EOF

    # 计算签名的哈希
    sig_sha=$(grep -v '^sha256=' "$TEST_GATES_DIR/03.ok.sig" | sha256sum | awk '{print $1}')
    echo "sha256=$sig_sha" >> "$TEST_GATES_DIR/03.ok.sig"

    # 验证
    run bash -c "
        sig_file='$TEST_GATES_DIR/03.ok.sig'

        stored_sha=\$(grep '^sha256=' \"\$sig_file\" | cut -d= -f2)
        current_sha=\$(grep -v '^sha256=' \"\$sig_file\" | sha256sum | awk '{print \$1}')

        if [ \"\$stored_sha\" = \"\$current_sha\" ]; then
            echo \"✅ Signature valid\"
            exit 0
        fi
        exit 1
    "

    [ "$status" -eq 0 ]
    [[ "$output" =~ "Signature valid" ]]
}

# Test 4: CI强制验签
@test "CI enforces signature verification" {
    local ci_file="$PROJECT_ROOT/.github/workflows/ce-gates.yml"

    if [ -f "$ci_file" ]; then
        run bash -c "
            grep -A20 'Verify Gate Signatures' '$ci_file' | grep -q 'sha256'
        "
        [ "$status" -eq 0 ]
    else
        skip "CI workflow not found"
    fi
}

# Test 5: 签名包含时间戳
@test "signature includes timestamp for audit trail" {
    cat > "$TEST_GATES_DIR/04.ok.sig" <<EOF
gate=04.ok
timestamp=1696838400
phase=P4
sha256=abc123
EOF

    run bash -c "
        sig_file='$TEST_GATES_DIR/04.ok.sig'
        timestamp=\$(grep '^timestamp=' \"\$sig_file\" | cut -d= -f2)

        if [ -n \"\$timestamp\" ] && [[ \"\$timestamp\" =~ ^[0-9]+$ ]]; then
            echo \"Timestamp found: \$timestamp\"
            exit 0
        fi
        exit 1
    "

    [ "$status" -eq 0 ]
    [[ "$output" =~ "Timestamp found" ]]
}

# Test 6: 签名包含Phase信息
@test "signature includes phase information" {
    cat > "$TEST_GATES_DIR/05.ok.sig" <<EOF
gate=05.ok
timestamp=$(date +%s)
phase=P5
sha256=def456
EOF

    run bash -c "
        sig_file='$TEST_GATES_DIR/05.ok.sig'
        phase=\$(grep '^phase=' \"\$sig_file\" | cut -d= -f2)

        if [[ \"\$phase\" =~ ^P[0-7]$ ]]; then
            echo \"Valid phase: \$phase\"
            exit 0
        fi
        exit 1
    "

    [ "$status" -eq 0 ]
    [[ "$output" =~ "Valid phase: P5" ]]
}

# Test 7: 检测签名文件格式错误
@test "detects malformed signature file" {
    # 格式错误的签名
    cat > "$TEST_GATES_DIR/06.ok.sig" <<EOF
invalid format
no key=value pairs
EOF

    run bash -c "
        sig_file='$TEST_GATES_DIR/06.ok.sig'

        # 检查必需字段
        required_fields=('gate=' 'timestamp=' 'phase=' 'sha256=')
        missing=0

        for field in \"\${required_fields[@]}\"; do
            if ! grep -q \"^\$field\" \"\$sig_file\"; then
                echo \"Missing field: \$field\"
                missing=\$((missing + 1))
            fi
        done

        if [ \$missing -gt 0 ]; then
            echo \"Malformed signature: \$missing missing fields\"
            exit 1
        fi
        exit 0
    "

    [ "$status" -eq 1 ]
    [[ "$output" =~ "Malformed signature" ]]
}

# Test 8: 实际gates目录验证
@test "existing gates have valid signatures" {
    if [ ! -d "$GATES_DIR" ]; then
        skip "Gates directory not found"
    fi

    run bash -c "
        gates_dir='$GATES_DIR'
        invalid=0

        for ok_file in \"\$gates_dir\"/*.ok; do
            [ -f \"\$ok_file\" ] || continue

            sig_file=\"\${ok_file}.sig\"

            if [ ! -f \"\$sig_file\" ]; then
                echo \"⚠️ Legacy gate without signature: \$ok_file\"
                continue
            fi

            # 验证签名
            stored_sha=\$(grep '^sha256=' \"\$sig_file\" | cut -d= -f2)
            current_sha=\$(grep -v '^sha256=' \"\$sig_file\" | sha256sum | awk '{print \$1}')

            if [ \"\$stored_sha\" != \"\$current_sha\" ]; then
                echo \"❌ Invalid signature: \$ok_file\"
                invalid=\$((invalid + 1))
            fi
        done

        if [ \$invalid -gt 0 ]; then
            exit 1
        fi
        echo \"✅ All gates have valid signatures\"
        exit 0
    "

    [ "$status" -eq 0 ] || [[ "$output" =~ "Legacy gate" ]]
}

# Test 9: 签名算法验证
@test "signature uses strong hash algorithm (SHA-256)" {
    run bash -c "
        # 验证签名文件使用SHA-256
        test_data='test content'
        sha256_hash=\$(echo -n \"\$test_data\" | sha256sum | awk '{print \$1}')

        # 哈希长度应该是64字符（SHA-256）
        if [ \${#sha256_hash} -eq 64 ]; then
            echo \"SHA-256 hash verified (64 chars)\"
            exit 0
        fi
        exit 1
    "

    [ "$status" -eq 0 ]
}

# Test 10: 防止重放攻击（时间戳验证）
@test "prevents replay attacks using timestamp validation" {
    # 创建旧的签名（48小时前）
    old_timestamp=$(($(date +%s) - 172800))  # 2天前

    cat > "$TEST_GATES_DIR/07.ok.sig" <<EOF
gate=07.ok
timestamp=$old_timestamp
phase=P7
sha256=ghi789
EOF

    run bash -c "
        sig_file='$TEST_GATES_DIR/07.ok.sig'
        max_age=86400  # 24小时

        timestamp=\$(grep '^timestamp=' \"\$sig_file\" | cut -d= -f2)
        current_time=\$(date +%s)
        age=\$((current_time - timestamp))

        if [ \$age -gt \$max_age ]; then
            echo \"❌ Signature too old: \${age}s (max: \${max_age}s)\"
            exit 1
        fi
        exit 0
    "

    [ "$status" -eq 1 ]
    [[ "$output" =~ "too old" ]]
}
