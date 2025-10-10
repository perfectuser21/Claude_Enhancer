#!/bin/bash
# Gate签名工具 - GPG密码学验签系统
# SECURITY: 使用真实密码学签名，防止伪造
# Version: 2.0.0 (GPG Edition)

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 参数
PHASE="${1:-}"
GATE_NUM="${2:-}"
ACTION="${3:-create}"

if [[ -z "$PHASE" || -z "$GATE_NUM" ]]; then
    echo -e "${RED}Usage: $0 <phase> <gate_num> [create|verify]${NC}"
    echo "Example: $0 P1 01 create"
    exit 1
fi

# GPG配置
GPG_KEY_ID="${CE_GPG_KEY:-}"  # 环境变量指定密钥，否则使用默认
GPG_HOMEDIR="${GNUPGHOME:-$HOME/.gnupg}"

# ═══════════════════════════════════════════════════════════════════
# 安全检查：确保GPG可用
# ═══════════════════════════════════════════════════════════════════
check_gpg_availability() {
    if ! command -v gpg &> /dev/null; then
        echo -e "${RED}❌ ERROR: GPG not installed${NC}"
        echo "Install: sudo apt-get install gnupg  # Debian/Ubuntu"
        echo "        sudo yum install gnupg       # RHEL/CentOS"
        exit 1
    fi
    
    # 检查是否有可用密钥
    if [[ -z "$GPG_KEY_ID" ]]; then
        # 尝试获取默认密钥
        GPG_KEY_ID=$(gpg --list-secret-keys --keyid-format LONG 2>/dev/null | \
                     grep -A1 '^sec' | tail -1 | awk '{print $1}' | head -1)
        
        if [[ -z "$GPG_KEY_ID" ]]; then
            echo -e "${YELLOW}⚠️  No GPG key found. Generating new key...${NC}"
            generate_gpg_key
        fi
    fi
    
    echo -e "${GREEN}✓ GPG available (Key: ${GPG_KEY_ID:0:16}...)${NC}"
}

# ═══════════════════════════════════════════════════════════════════
# 生成GPG密钥（自动化，用于CI/CD）
# ═══════════════════════════════════════════════════════════════════
generate_gpg_key() {
    echo -e "${BLUE}🔑 Generating GPG key for Claude Enhancer...${NC}"
    
    # 生成密钥配置
    cat > /tmp/gpg_gen_key.conf << EOF
%no-protection
Key-Type: RSA
Key-Length: 2048
Subkey-Type: RSA
Subkey-Length: 2048
Name-Real: Claude Enhancer Gate Signer
Name-Email: gates@claude-enhancer.local
Expire-Date: 0
%commit
EOF
    
    # 生成密钥
    gpg --batch --gen-key /tmp/gpg_gen_key.conf 2>&1 | grep -v "^gpg:"
    rm -f /tmp/gpg_gen_key.conf
    
    # 获取生成的密钥ID
    GPG_KEY_ID=$(gpg --list-secret-keys --keyid-format LONG 2>/dev/null | \
                 grep -A1 'Claude Enhancer' | tail -1 | awk '{print $1}')
    
    echo -e "${GREEN}✓ Generated key: $GPG_KEY_ID${NC}"
    echo "export CE_GPG_KEY=$GPG_KEY_ID" >> ~/.bashrc
}

# ═══════════════════════════════════════════════════════════════════
# 创建Gate签名（GPG detached signature）
# ═══════════════════════════════════════════════════════════════════
create_gate_signature() {
    local ok_file=".gates/${GATE_NUM}.ok"
    local sig_file="${ok_file}.sig"
    
    # 创建gate标记文件
    {
        echo "phase=$PHASE"
        echo "gate=$GATE_NUM"
        echo "timestamp=$(date -Iseconds)"
        echo "commit=$(git rev-parse HEAD 2>/dev/null || echo 'no-git')"
        echo "user=$(whoami)@$(hostname)"
    } > "$ok_file"
    
    echo -e "${BLUE}📝 Signing gate with GPG...${NC}"
    
    # 使用GPG创建分离签名
    if gpg --default-key "$GPG_KEY_ID" \
           --detach-sign \
           --armor \
           --output "$sig_file" \
           "$ok_file" 2>&1 | grep -v "^gpg:"; then
        
        local sig_fingerprint=$(gpg --verify "$sig_file" "$ok_file" 2>&1 | \
                                grep 'using' | awk '{print $NF}')
        
        echo -e "${GREEN}✅ Gate signed successfully${NC}"
        echo "   Gate:      $ok_file"
        echo "   Signature: $sig_file"
        echo "   Key ID:    ${sig_fingerprint:0:16}..."
        
        # 显示签名摘要
        echo ""
        echo -e "${BLUE}📋 Signature Details:${NC}"
        gpg --verify "$sig_file" "$ok_file" 2>&1 | head -5
        
        return 0
    else
        echo -e "${RED}❌ Failed to sign gate${NC}"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════
# 验证Gate签名（强制密码学验证）
# ═══════════════════════════════════════════════════════════════════
verify_gate_signature() {
    local ok_file=".gates/${GATE_NUM}.ok"
    local sig_file="${ok_file}.sig"
    
    if [[ ! -f "$ok_file" ]]; then
        echo -e "${RED}❌ ERROR: Gate file not found: $ok_file${NC}"
        exit 1
    fi
    
    if [[ ! -f "$sig_file" ]]; then
        echo -e "${RED}❌ ERROR: Signature file not found: $sig_file${NC}"
        echo "   This gate was not properly signed!"
        exit 1
    fi
    
    echo -e "${BLUE}🔍 Verifying GPG signature...${NC}"
    
    # GPG验证（严格模式）
    local verify_output
    verify_output=$(gpg --verify "$sig_file" "$ok_file" 2>&1)
    local verify_status=$?
    
    if [[ $verify_status -eq 0 ]]; then
        # 成功验证
        local signer=$(echo "$verify_output" | grep 'Good signature' | sed 's/.*from "//' | sed 's/".*//')
        local key_id=$(echo "$verify_output" | grep 'using' | awk '{print $NF}')
        local timestamp=$(echo "$verify_output" | grep 'Signature made' | sed 's/.*made //')
        
        echo -e "${GREEN}✅ Signature VALID${NC}"
        echo "   Signer:    $signer"
        echo "   Key ID:    ${key_id:0:16}..."
        echo "   Signed at: $timestamp"
        
        # 验证gate内容
        echo ""
        echo -e "${BLUE}📋 Gate Content:${NC}"
        cat "$ok_file" | while read -r line; do
            echo "   $line"
        done
        
        return 0
    else
        # 验证失败
        echo -e "${RED}❌ Signature INVALID or UNTRUSTED${NC}"
        echo ""
        echo "Verification output:"
        echo "$verify_output" | sed 's/^/   /'
        echo ""
        echo -e "${RED}⚠️  SECURITY WARNING: This gate may have been tampered with!${NC}"
        exit 1
    fi
}

# ═══════════════════════════════════════════════════════════════════
# 批量验证所有gate
# ═══════════════════════════════════════════════════════════════════
verify_all_gates() {
    echo -e "${BLUE}🔍 Verifying all gates...${NC}"
    echo ""
    
    local total=0
    local valid=0
    local invalid=0
    
    for ok_file in .gates/*.ok; do
        [[ ! -f "$ok_file" ]] && continue
        
        ((total++))
        local gate_num=$(basename "$ok_file" .ok)
        local sig_file="${ok_file}.sig"
        
        echo -e "${BLUE}Checking gate $gate_num...${NC}"
        
        if [[ ! -f "$sig_file" ]]; then
            echo -e "${YELLOW}   ⚠️  No signature (legacy gate)${NC}"
            continue
        fi
        
        if gpg --verify "$sig_file" "$ok_file" &>/dev/null; then
            echo -e "${GREEN}   ✓ Valid${NC}"
            ((valid++))
        else
            echo -e "${RED}   ✗ Invalid or untrusted${NC}"
            ((invalid++))
        fi
    done
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Total gates:   $total"
    echo -e "${GREEN}Valid:         $valid${NC}"
    if [[ $invalid -gt 0 ]]; then
        echo -e "${RED}Invalid:       $invalid${NC}"
        exit 1
    else
        echo "Invalid:       $invalid"
    fi
    
    if [[ $invalid -eq 0 && $valid -gt 0 ]]; then
        echo -e "\n${GREEN}✅ All gates verified successfully${NC}"
        return 0
    else
        echo -e "\n${RED}❌ Verification failed${NC}"
        exit 1
    fi
}

# ═══════════════════════════════════════════════════════════════════
# 导出公钥（用于CI/CD）
# ═══════════════════════════════════════════════════════════════════
export_public_key() {
    local output_file="${1:-.gates/trusted.asc}"
    
    echo -e "${BLUE}📤 Exporting public key...${NC}"
    
    gpg --armor --export "$GPG_KEY_ID" > "$output_file"
    
    echo -e "${GREEN}✓ Public key exported to: $output_file${NC}"
    echo "   Import on CI: gpg --import $output_file"
    echo "   Trust key:    echo \"$GPG_KEY_ID:6:\" | gpg --import-ownertrust"
}

# ═══════════════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════════════
main() {
    # 检查GPG可用性
    check_gpg_availability
    
    case "$ACTION" in
        create)
            create_gate_signature
            ;;
        verify)
            verify_gate_signature
            ;;
        verify-all)
            verify_all_gates
            ;;
        export-key)
            export_public_key "$GATE_NUM"
            ;;
        *)
            echo -e "${RED}Unknown action: $ACTION${NC}"
            echo "Valid actions: create, verify, verify-all, export-key"
            exit 1
            ;;
    esac
}

main "$@"
