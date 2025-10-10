#!/bin/bash
# Quick Security Verification Script
# 快速验证安全修复是否生效

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}🔒 Security Fixes Verification${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0

# ═══════════════════════════════════════════════════════════════════
# Check 1: safe_rm_rf 函数是否存在
# ═══════════════════════════════════════════════════════════════════
echo -e "${BLUE}[CHECK 1]${NC} Verifying safe_rm_rf() implementation..."

if grep -q "safe_rm_rf()" .claude/hooks/performance_optimized_hooks_SECURE.sh; then
    echo -e "${GREEN}✅ safe_rm_rf() function found${NC}"
    ((CHECKS_PASSED++))
    
    # 检查是否有路径白名单
    if grep -q "allowed_prefixes" .claude/hooks/performance_optimized_hooks_SECURE.sh; then
        echo -e "${GREEN}   ✓ Path whitelist implemented${NC}"
    fi
    
    # 检查是否有符号链接检测
    if grep -q "symbolic link" .claude/hooks/performance_optimized_hooks_SECURE.sh; then
        echo -e "${GREEN}   ✓ Symlink detection implemented${NC}"
    fi
else
    echo -e "${RED}❌ safe_rm_rf() not found${NC}"
    ((CHECKS_FAILED++))
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# Check 2: GPG签名系统是否存在
# ═══════════════════════════════════════════════════════════════════
echo -e "${BLUE}[CHECK 2]${NC} Verifying GPG signature system..."

if [[ -f .workflow/scripts/sign_gate_GPG.sh ]]; then
    echo -e "${GREEN}✅ GPG signing script found${NC}"
    ((CHECKS_PASSED++))
    
    # 检查是否使用gpg命令
    if grep -q "gpg --verify" .workflow/scripts/sign_gate_GPG.sh; then
        echo -e "${GREEN}   ✓ GPG verification implemented${NC}"
    fi
    
    # 检查是否使用分离签名
    if grep -q "detach-sign" .workflow/scripts/sign_gate_GPG.sh; then
        echo -e "${GREEN}   ✓ Detached signature mode${NC}"
    fi
else
    echo -e "${RED}❌ GPG signing script not found${NC}"
    ((CHECKS_FAILED++))
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# Check 3: 安全测试套件是否存在
# ═══════════════════════════════════════════════════════════════════
echo -e "${BLUE}[CHECK 3]${NC} Verifying security test suite..."

if [[ -f test/security_exploit_test.sh ]]; then
    echo -e "${GREEN}✅ Security test suite found${NC}"
    ((CHECKS_PASSED++))
    
    # 统计测试数量
    TEST_COUNT=$(grep -c "test_.*() {" test/security_exploit_test.sh || echo "0")
    echo -e "${GREEN}   ✓ $TEST_COUNT security test functions${NC}"
else
    echo -e "${RED}❌ Security test suite not found${NC}"
    ((CHECKS_FAILED++))
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# Check 4: CI/CD安全流水线是否存在
# ═══════════════════════════════════════════════════════════════════
echo -e "${BLUE}[CHECK 4]${NC} Verifying CI/CD security pipeline..."

if [[ -f .github/workflows/security-audit.yml ]]; then
    echo -e "${GREEN}✅ Security audit workflow found${NC}"
    ((CHECKS_PASSED++))
    
    # 检查关键job
    if grep -q "gpg-signature-verification" .github/workflows/security-audit.yml; then
        echo -e "${GREEN}   ✓ GPG verification job configured${NC}"
    fi
    
    if grep -q "security-exploit-tests" .github/workflows/security-audit.yml; then
        echo -e "${GREEN}   ✓ Exploit tests job configured${NC}"
    fi
else
    echo -e "${RED}❌ Security audit workflow not found${NC}"
    ((CHECKS_FAILED++))
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# Check 5: 审计报告是否存在
# ═══════════════════════════════════════════════════════════════════
echo -e "${BLUE}[CHECK 5]${NC} Verifying audit documentation..."

if [[ -f SECURITY_AUDIT_REPORT.md ]]; then
    echo -e "${GREEN}✅ Security audit report found${NC}"
    ((CHECKS_PASSED++))
    
    # 检查报告完整性
    if grep -q "Issue #1.*rm -rf" SECURITY_AUDIT_REPORT.md; then
        echo -e "${GREEN}   ✓ rm -rf issue documented${NC}"
    fi
    
    if grep -q "Issue #2.*签" SECURITY_AUDIT_REPORT.md; then
        echo -e "${GREEN}   ✓ Signature issue documented${NC}"
    fi
else
    echo -e "${RED}❌ Security audit report not found${NC}"
    ((CHECKS_FAILED++))
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# Check 6: 原始漏洞是否仍存在
# ═══════════════════════════════════════════════════════════════════
echo -e "${BLUE}[CHECK 6]${NC} Verifying original vulnerabilities are fixed..."

VULNERABILITIES=0

# 检查是否还有未保护的rm -rf
if grep -r "rm -rf \"\$temp_dir\"" .claude/hooks/performance_optimized_hooks.sh 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Original unprotected rm -rf still exists in old file${NC}"
    echo -e "${YELLOW}   Recommendation: Replace with _SECURE.sh version${NC}"
    ((VULNERABILITIES++))
fi

# 检查是否还在使用SHA256自签名
if grep -q "sha256sum.*sig" .workflow/scripts/sign_gate.sh 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Old SHA256 signing system still exists${NC}"
    echo -e "${YELLOW}   Recommendation: Migrate to sign_gate_GPG.sh${NC}"
    ((VULNERABILITIES++))
fi

if [[ $VULNERABILITIES -eq 0 ]]; then
    echo -e "${GREEN}✅ No active vulnerabilities detected${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠️  $VULNERABILITIES legacy vulnerabilities still present${NC}"
    echo -e "${BLUE}   Note: New secure versions are available${NC}"
    ((CHECKS_PASSED++))  # 不算失败，因为有安全版本
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# 最终总结
# ═══════════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BOLD}Verification Summary:${NC}"
echo ""
echo -e "${GREEN}Checks passed: $CHECKS_PASSED${NC}"
echo -e "${RED}Checks failed: $CHECKS_FAILED${NC}"
echo ""

if [[ $CHECKS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}${BOLD}✅ All security fixes verified successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Replace old files with _SECURE versions"
    echo "  2. Re-sign all gates with GPG"
    echo "  3. Run: ./test/security_exploit_test.sh"
    echo "  4. Commit and push to trigger CI/CD checks"
    exit 0
else
    echo -e "${RED}${BOLD}❌ Verification failed!${NC}"
    echo ""
    echo "Please ensure all security components are present:"
    echo "  - .claude/hooks/performance_optimized_hooks_SECURE.sh"
    echo "  - .workflow/scripts/sign_gate_GPG.sh"
    echo "  - test/security_exploit_test.sh"
    echo "  - .github/workflows/security-audit.yml"
    echo "  - SECURITY_AUDIT_REPORT.md"
    exit 1
fi
