#!/bin/bash
# Gate签名工具 - 防止手工伪造.gates/*.ok文件
# 补丁1实现：为每个gate生成签名文件
# Version: 1.0.0

set -euo pipefail

# 参数
PHASE="${1:-}"
GATE_NUM="${2:-}"

if [[ -z "$PHASE" || -z "$GATE_NUM" ]]; then
    echo "Usage: $0 <phase> <gate_num>"
    echo "Example: $0 P1 01"
    exit 1
fi

# 生成签名
create_gate_signature() {
    local ok_file=".gates/${GATE_NUM}.ok"
    local sig_file="${ok_file}.sig"

    # 创建gate标记
    touch "$ok_file"

    # 生成签名内容
    {
        echo "phase=$PHASE"
        echo "gate=$GATE_NUM"
        echo "head=$(git rev-parse HEAD 2>/dev/null || echo 'no-git')"
        echo "script=$(basename "$0")@v1"
        echo "time=$(date -Iseconds)"
        echo "user=$(whoami)"
    } > "$sig_file"

    # 计算签名哈希
    sha=$(sha256sum "$sig_file" | awk '{print $1}')
    echo "sha256=$sha" >> "$sig_file"

    echo "✅ Gate signed: $ok_file"
    echo "   Signature: $sig_file"
    echo "   SHA256: $sha"
}

# 验证签名
verify_gate_signature() {
    local ok_file=".gates/${GATE_NUM}.ok"
    local sig_file="${ok_file}.sig"

    if [[ ! -f "$sig_file" ]]; then
        echo "❌ Missing signature for $ok_file"
        exit 1
    fi

    # 提取原始哈希
    original_sha=$(grep '^sha256=' "$sig_file" | cut -d= -f2)

    # 临时移除sha256行计算当前哈希
    grep -v '^sha256=' "$sig_file" > "/tmp/gate_verify.tmp"
    current_sha=$(sha256sum "/tmp/gate_verify.tmp" | awk '{print $1}')

    if [[ "$original_sha" != "$current_sha" ]]; then
        echo "❌ Signature hash mismatch for $ok_file"
        echo "   Expected: $original_sha"
        echo "   Got: $current_sha"
        exit 1
    fi

    echo "✅ Signature verified: $ok_file"
}

# 主函数
main() {
    case "${3:-create}" in
        create)
            create_gate_signature
            ;;
        verify)
            verify_gate_signature
            ;;
        *)
            echo "Unknown action: $3"
            exit 1
            ;;
    esac
}

main "$@"