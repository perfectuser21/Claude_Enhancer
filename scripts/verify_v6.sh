#!/bin/bash
# Claude Enhancer v6.0 完整性验证脚本

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 计数器
PASS=0
FAIL=0
WARN=0

echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Claude Enhancer v6.0 Verification Tool  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo

# 函数：检查并报告
check() {
    local name="$1"
    local command="$2"
    local expected="$3"

    echo -n "Checking $name... "

    result=$(eval "$command" 2>/dev/null || echo "FAILED")

    if [[ "$result" == "$expected" ]]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASS++))
    elif [[ "$result" == "FAILED" ]]; then
        echo -e "${RED}❌ FAIL${NC}"
        ((FAIL++))
        echo "  Expected: $expected"
        echo "  Got: Command failed"
    else
        echo -e "${YELLOW}⚠️ WARN${NC}"
        ((WARN++))
        echo "  Expected: $expected"
        echo "  Got: $result"
    fi
}

# 1. 版本一致性检查
echo -e "${BLUE}═══ Version Consistency ═══${NC}"
check "VERSION file" "cat VERSION 2>/dev/null" "6.0.0"
check "settings.json" "python3 -c \"import json; print(json.load(open('.claude/settings.json'))['version'])\"" "6.0.0"
check "manifest.yml" "python3 -c \"import yaml; print(yaml.safe_load(open('.workflow/manifest.yml'))['version'])\"" "6.0.0"
check "config.yml" "python3 -c \"import yaml; print(yaml.safe_load(open('.claude/config.yml'))['version'])\"" "6.0.0"
echo

# 2. 文档组织检查
echo -e "${BLUE}═══ Document Organization ═══${NC}"
check "Root MD files" "ls -1 *.md 2>/dev/null | wc -l" "3"
check "Archive v5.3" "ls archive/v5.3/*.md 2>/dev/null | wc -l | xargs -I {} test {} -gt 0 && echo YES || echo NO" "YES"
check "Archive v5.5" "ls archive/v5.5/*.md 2>/dev/null | wc -l | xargs -I {} test {} -gt 0 && echo YES || echo NO" "YES"
check "Archive legacy" "ls archive/legacy/*.md 2>/dev/null | wc -l | xargs -I {} test {} -gt 0 && echo YES || echo NO" "YES"
echo

# 3. CI/CD精简检查
echo -e "${BLUE}═══ CI/CD Simplification ═══${NC}"
check "CI workflows count" "ls -1 .github/workflows/*.yml 2>/dev/null | wc -l" "5"
check "ce-unified-gates.yml" "test -f .github/workflows/ce-unified-gates.yml && echo EXISTS || echo MISSING" "EXISTS"
check "test-suite.yml" "test -f .github/workflows/test-suite.yml && echo EXISTS || echo MISSING" "EXISTS"
check "security-scan.yml" "test -f .github/workflows/security-scan.yml && echo EXISTS || echo MISSING" "EXISTS"
check "bp-guard.yml" "test -f .github/workflows/bp-guard.yml && echo EXISTS || echo MISSING" "EXISTS"
check "release.yml" "test -f .github/workflows/release.yml && echo EXISTS || echo MISSING" "EXISTS"
echo

# 4. Hooks完整性检查
echo -e "${BLUE}═══ Hooks Integrity ═══${NC}"
check "Total hooks" "ls -1 .claude/hooks/*.sh 2>/dev/null | wc -l" "27"
check "Silent mode coverage" "grep -l CE_SILENT_MODE .claude/hooks/*.sh 2>/dev/null | wc -l" "27"
check "Compact mode hooks" "grep -l CE_COMPACT_OUTPUT .claude/hooks/*.sh 2>/dev/null | wc -l | xargs -I {} test {} -gt 20 && echo GOOD || echo LOW" "GOOD"
echo

# 5. Git Hooks检查
echo -e "${BLUE}═══ Git Hooks ═══${NC}"
check "pre-commit" "test -f .git/hooks/pre-commit && echo EXISTS || echo MISSING" "EXISTS"
check "commit-msg" "test -f .git/hooks/commit-msg && echo EXISTS || echo MISSING" "EXISTS"
check "pre-push" "test -f .git/hooks/pre-push && echo EXISTS || echo MISSING" "EXISTS"
echo

# 6. 核心文件检查
echo -e "${BLUE}═══ Core Files ═══${NC}"
check "README.md" "test -f README.md && echo EXISTS || echo MISSING" "EXISTS"
check "CHANGELOG.md" "test -f CHANGELOG.md && echo EXISTS || echo MISSING" "EXISTS"
check "LICENSE" "test -f LICENSE && echo EXISTS || echo MISSING" "EXISTS"
check "CLAUDE.md" "test -f CLAUDE.md && echo EXISTS || echo MISSING" "EXISTS"
check "VERSION" "test -f VERSION && echo EXISTS || echo MISSING" "EXISTS"
echo

# 7. 工作流配置检查
echo -e "${BLUE}═══ Workflow Configuration ═══${NC}"
check "gates.yml" "test -f .workflow/gates.yml && echo EXISTS || echo MISSING" "EXISTS"
check "manifest.yml" "test -f .workflow/manifest.yml && echo EXISTS || echo MISSING" "EXISTS"
check "config.yml" "test -f .claude/config.yml && echo EXISTS || echo MISSING" "EXISTS"
echo

# 8. 新文档检查
echo -e "${BLUE}═══ New Documentation ═══${NC}"
check "SYSTEM_OVERVIEW.md" "test -f docs/SYSTEM_OVERVIEW.md && echo EXISTS || echo MISSING" "EXISTS"
check "WORKFLOW_GUIDE.md" "test -f docs/WORKFLOW_GUIDE.md && echo EXISTS || echo MISSING" "EXISTS"
echo

# 9. 环境变量检查
echo -e "${BLUE}═══ Environment Variables ═══${NC}"
if [ -f .claude/config.yml ]; then
    check "CE_AUTO_MODE config" "grep -q 'CE_AUTO_MODE: true' .claude/config.yml && echo SET || echo UNSET" "SET"
    check "CE_SILENT_MODE config" "grep -q 'CE_SILENT_MODE:' .claude/config.yml && echo SET || echo UNSET" "SET"
    check "CE_AUTO_CREATE_BRANCH config" "grep -q 'CE_AUTO_CREATE_BRANCH: true' .claude/config.yml && echo SET || echo UNSET" "SET"
fi
echo

# 10. Branch Protection配置检查
echo -e "${BLUE}═══ Branch Protection ═══${NC}"
check "Protection script" "test -f scripts/setup_v6_protection.sh && echo EXISTS || echo MISSING" "EXISTS"
check "BP snapshot" "test -L .workflow/backups/bp_snapshot_latest.json && echo EXISTS || echo MISSING" "EXISTS"
echo

# 总结
echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║             Verification Summary          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo
echo -e "  ${GREEN}✅ Passed:${NC} $PASS"
echo -e "  ${YELLOW}⚠️ Warnings:${NC} $WARN"
echo -e "  ${RED}❌ Failed:${NC} $FAIL"
echo

# 计算总分
TOTAL=$((PASS + WARN + FAIL))
if [ $TOTAL -gt 0 ]; then
    SCORE=$((PASS * 100 / TOTAL))
    echo -e "  📊 Score: ${SCORE}%"
    echo

    if [ $SCORE -eq 100 ]; then
        echo -e "${GREEN}🎉 Perfect! Claude Enhancer v6.0 is fully verified!${NC}"
    elif [ $SCORE -ge 90 ]; then
        echo -e "${GREEN}✅ Excellent! System is production ready.${NC}"
    elif [ $SCORE -ge 80 ]; then
        echo -e "${YELLOW}⚠️ Good, but some issues need attention.${NC}"
    else
        echo -e "${RED}❌ Critical issues found. Please fix before using.${NC}"
    fi
fi

# 详细问题报告
if [ $FAIL -gt 0 ] || [ $WARN -gt 0 ]; then
    echo
    echo -e "${BLUE}═══ Recommended Actions ═══${NC}"

    if [ $FAIL -gt 0 ]; then
        echo -e "${RED}Critical Issues:${NC}"
        echo "  1. Run: ./scripts/setup_v6_protection.sh"
        echo "  2. Check version consistency"
        echo "  3. Verify file locations"
    fi

    if [ $WARN -gt 0 ]; then
        echo -e "${YELLOW}Warnings:${NC}"
        echo "  1. Some optional features may not be configured"
        echo "  2. Review .claude/config.yml settings"
    fi
fi

exit $([ $FAIL -eq 0 ] && echo 0 || echo 1)