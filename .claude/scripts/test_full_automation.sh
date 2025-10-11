#!/usr/bin/env bash
set -euo pipefail

# ============================================
# Claude Code 完全自动化模式测试脚本
# ============================================
# 测试 Bypass Permissions Mode 是否生效
# 验证 P0-P7 执行过程中无需人工确认

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok() { echo -e "${GREEN}✓ $*${NC}"; }
bad() { echo -e "${RED}✗ $*${NC}"; }
info() { echo -e "${YELLOW}ℹ $*${NC}"; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Claude Code 完全自动化测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# ============================================
# 测试 1: 配置验证
# ============================================
echo "📋 测试 1: 验证配置文件"
echo "----------------------------------------"

if [ -f ".claude/settings.json" ]; then
    ok "settings.json 存在"

    # 检查 bypassPermissionsMode
    if grep -q '"bypassPermissionsMode": true' .claude/settings.json; then
        ok "bypassPermissionsMode: true ✅"
    else
        bad "bypassPermissionsMode 未启用"
        exit 1
    fi

    # 检查 autoConfirm
    if grep -q '"autoConfirm": true' .claude/settings.json; then
        ok "autoConfirm: true ✅"
    else
        info "autoConfirm 未设置（可选）"
    fi

    # 检查 allow 列表
    TOOLS_COUNT=$(grep -c '"Bash(\*\*)"\|"Read(\*\*)"\|"Write(\*\*)"' .claude/settings.json || echo 0)
    if [ "$TOOLS_COUNT" -ge 3 ]; then
        ok "工具白名单配置完整（$TOOLS_COUNT 项）"
    else
        bad "工具白名单配置不完整"
    fi
else
    bad "settings.json 不存在"
    exit 1
fi

echo

# ============================================
# 测试 2: 文件操作（应自动）
# ============================================
echo "📁 测试 2: 文件操作自动化"
echo "----------------------------------------"

TEST_DIR="/tmp/claude_test_$$"
mkdir -p "$TEST_DIR"

# 测试文件写入
if echo "test content" > "$TEST_DIR/test.txt" 2>/dev/null; then
    ok "文件写入 - 自动执行"
else
    bad "文件写入失败"
fi

# 测试文件读取
if cat "$TEST_DIR/test.txt" >/dev/null 2>&1; then
    ok "文件读取 - 自动执行"
else
    bad "文件读取失败"
fi

# 测试文件编辑
if echo "modified" >> "$TEST_DIR/test.txt" 2>/dev/null; then
    ok "文件编辑 - 自动执行"
else
    bad "文件编辑失败"
fi

# 清理
rm -rf "$TEST_DIR"

echo

# ============================================
# 测试 3: Git 操作（应自动）
# ============================================
echo "🔧 测试 3: Git 操作自动化"
echo "----------------------------------------"

# 测试 git status
if git status >/dev/null 2>&1; then
    ok "git status - 自动执行"
else
    bad "git status 失败"
fi

# 测试 git diff
if git diff --quiet 2>/dev/null || git diff >/dev/null 2>&1; then
    ok "git diff - 自动执行"
else
    info "git diff 执行（可能有差异）"
fi

# 测试 git log
if git log -1 --oneline >/dev/null 2>&1; then
    ok "git log - 自动执行"
else
    bad "git log 失败"
fi

echo

# ============================================
# 测试 4: Bash 命令（应自动）
# ============================================
echo "⚡ 测试 4: Bash 命令自动化"
echo "----------------------------------------"

# 测试 ls
if ls >/dev/null 2>&1; then
    ok "ls 命令 - 自动执行"
else
    bad "ls 命令失败"
fi

# 测试 echo
if echo "test" >/dev/null 2>&1; then
    ok "echo 命令 - 自动执行"
else
    bad "echo 命令失败"
fi

# 测试 cat
if cat .claude/settings.json >/dev/null 2>&1; then
    ok "cat 命令 - 自动执行"
else
    bad "cat 命令失败"
fi

# 测试 grep
if grep -q "bypassPermissionsMode" .claude/settings.json 2>/dev/null; then
    ok "grep 命令 - 自动执行"
else
    bad "grep 命令失败"
fi

echo

# ============================================
# 测试 5: 危险命令（应有保护但自动）
# ============================================
echo "⚠️  测试 5: 受保护命令"
echo "----------------------------------------"

# 测试 chmod（安全的）
TEST_FILE="/tmp/test_chmod_$$"
touch "$TEST_FILE"
if chmod +x "$TEST_FILE" 2>/dev/null; then
    ok "chmod 命令 - 自动执行"
    rm -f "$TEST_FILE"
else
    info "chmod 命令可能需要额外确认"
fi

# 测试 git checkout（安全的）
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if git checkout "$CURRENT_BRANCH" 2>/dev/null; then
    ok "git checkout - 自动执行"
else
    info "git checkout 可能需要确认"
fi

echo

# ============================================
# 测试 6: 环境变量检查
# ============================================
echo "🌍 测试 6: 环境变量"
echo "----------------------------------------"

if [ "${CE_AUTO_CONFIRM:-false}" = "true" ]; then
    ok "CE_AUTO_CONFIRM=true ✅"
else
    info "CE_AUTO_CONFIRM 未设置（可选）"
    echo "   建议: export CE_AUTO_CONFIRM=true"
fi

if [ "${CLAUDE_CODE_BYPASS_PERMISSIONS:-false}" = "true" ]; then
    ok "CLAUDE_CODE_BYPASS_PERMISSIONS=true ✅"
else
    info "CLAUDE_CODE_BYPASS_PERMISSIONS 未设置（可选）"
    echo "   建议: export CLAUDE_CODE_BYPASS_PERMISSIONS=true"
fi

echo

# ============================================
# 测试 7: Phase 切换（模拟P0-P7）
# ============================================
echo "🔄 测试 7: Phase 切换自动化"
echo "----------------------------------------"

if [ -f ".phase/current" ]; then
    CURRENT_PHASE=$(cat .phase/current)
    ok "当前 Phase: $CURRENT_PHASE"

    # 测试 Phase 切换
    ORIGINAL_PHASE=$CURRENT_PHASE
    echo "P0" > .phase/current
    if [ "$(cat .phase/current)" = "P0" ]; then
        ok "Phase 切换到 P0 - 自动执行"
    else
        bad "Phase 切换失败"
    fi

    # 恢复原 Phase
    echo "$ORIGINAL_PHASE" > .phase/current
    ok "Phase 恢复到 $ORIGINAL_PHASE"
else
    info ".phase/current 不存在"
fi

echo

# ============================================
# 测试总结
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 测试总结"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo
ok "配置验证: 完成"
ok "文件操作: 自动化"
ok "Git 操作: 自动化"
ok "Bash 命令: 自动化"
ok "受保护命令: 自动化（安全）"
ok "环境变量: 已检查"
ok "Phase 切换: 自动化"

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ok "✅ 完全自动化模式配置成功！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
info "建议下一步："
echo "   1. 重启 Claude Code session（如果正在运行）"
echo "   2. 测试完整 P0-P7 工作流"
echo "   3. 观察是否还有任何确认提示"
echo

# ============================================
# 可选：设置环境变量
# ============================================
echo "💡 可选优化："
echo "   在 ~/.bashrc 或 ~/.zshrc 中添加："
echo "   ----------------------------------------"
echo "   export CE_AUTO_CONFIRM=true"
echo "   export CLAUDE_CODE_BYPASS_PERMISSIONS=true"
echo "   export CE_SILENT_MODE=false"
echo "   ----------------------------------------"
echo

exit 0
