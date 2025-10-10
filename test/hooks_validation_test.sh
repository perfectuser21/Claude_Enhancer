#!/bin/bash
# Hooks激活验证测试脚本
# 验证所有Claude hooks和Git hooks的真实触发

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/.workflow/logs"
CLAUDE_HOOKS_LOG="$LOG_DIR/claude_hooks.log"
GIT_HOOKS_LOG="$LOG_DIR/hooks.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 创建日志目录
mkdir -p "$LOG_DIR"

# 清空旧日志
echo "$(date +'%F %T') [hooks_validation_test] Test started" > "$CLAUDE_HOOKS_LOG"
echo "$(date +'%F %T') [hooks_validation_test] Test started" > "$GIT_HOOKS_LOG"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Hooks激活验证测试 - 完整触发测试               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo

# ==================== 第一部分：Claude Hooks测试 ====================

echo -e "${YELLOW}[1/3] 测试Claude Hooks触发...${NC}"
echo

declare -a claude_hooks=(
    "workflow_auto_start.sh"
    "workflow_enforcer.sh"
    "smart_agent_selector.sh"
    "gap_scan.sh"
    "branch_helper.sh"
    "quality_gate.sh"
    "auto_cleanup_check.sh"
    "concurrent_optimizer.sh"
    "unified_post_processor.sh"
    "agent_error_recovery.sh"
)

claude_triggered=0
claude_total=${#claude_hooks[@]}

for hook in "${claude_hooks[@]}"; do
    hook_path="$PROJECT_ROOT/.claude/hooks/$hook"

    if [[ ! -f "$hook_path" ]]; then
        echo -e "  ${RED}✗ $hook - 文件不存在${NC}"
        continue
    fi

    if [[ ! -x "$hook_path" ]]; then
        echo -e "  ${YELLOW}⚠ $hook - 无执行权限，正在修复...${NC}"
        chmod +x "$hook_path"
    fi

    echo -e "  ${BLUE}→ 触发 $hook${NC}"

    # 根据hook类型模拟触发
    case "$hook" in
        workflow_auto_start.sh)
            bash "$hook_path" "测试任务：修复hooks验证" 2>/dev/null || true
            ;;
        workflow_enforcer.sh)
            bash "$hook_path" "测试实现功能" 2>/dev/null || true
            ;;
        smart_agent_selector.sh)
            echo '{"prompt":"测试任务"}' | bash "$hook_path" > /dev/null 2>&1 || true
            ;;
        gap_scan.sh)
            bash "$hook_path" 2>/dev/null || true
            ;;
        branch_helper.sh)
            bash "$hook_path" 2>/dev/null || true
            ;;
        quality_gate.sh)
            echo '{"prompt":"测试质量检查"}' | bash "$hook_path" > /dev/null 2>&1 || true
            ;;
        auto_cleanup_check.sh)
            bash "$hook_path" 2>/dev/null || true
            ;;
        concurrent_optimizer.sh)
            bash "$hook_path" 2>/dev/null || true
            ;;
        unified_post_processor.sh)
            echo '{"name":"Test","data":"test"}' | bash "$hook_path" > /dev/null 2>&1 || true
            ;;
        agent_error_recovery.sh)
            echo '{"error":"test error"}' | bash "$hook_path" > /dev/null 2>&1 || true
            ;;
    esac

    sleep 0.1  # 让日志写入完成

    # 检查日志记录
    if grep -q "$(basename $hook .sh)" "$CLAUDE_HOOKS_LOG" 2>/dev/null; then
        echo -e "  ${GREEN}✓ $hook - 成功触发并记录日志${NC}"
        ((claude_triggered++))
    else
        echo -e "  ${RED}✗ $hook - 未在日志中找到记录${NC}"
    fi
done

echo
echo -e "${BLUE}Claude Hooks触发率: $claude_triggered/$claude_total${NC}"
echo

# ==================== 第二部分：Git Hooks测试 ====================

echo -e "${YELLOW}[2/3] 测试Git Hooks触发...${NC}"
echo

declare -a git_hooks=(
    "pre-commit"
    "commit-msg"
    "pre-push"
)

git_triggered=0
git_total=${#git_hooks[@]}

for hook in "${git_hooks[@]}"; do
    hook_path="$PROJECT_ROOT/.git/hooks/$hook"

    if [[ ! -f "$hook_path" ]]; then
        echo -e "  ${RED}✗ $hook - 文件不存在${NC}"
        continue
    fi

    if [[ ! -x "$hook_path" ]]; then
        echo -e "  ${YELLOW}⚠ $hook - 无执行权限，正在修复...${NC}"
        chmod +x "$hook_path"
    fi

    echo -e "  ${BLUE}→ 测试 $hook${NC}"

    # 检查hook是否有硬拦截（set -e）
    if grep -q "set -e" "$hook_path"; then
        echo -e "    ${GREEN}✓ 包含硬拦截 (set -e)${NC}"
    else
        echo -e "    ${RED}✗ 缺少硬拦截 (set -e)${NC}"
    fi

    # 检查hook是否写日志
    if grep -q "claude_hooks.log\|hooks.log" "$hook_path"; then
        echo -e "    ${GREEN}✓ 包含日志记录${NC}"
        ((git_triggered++))
    else
        echo -e "    ${YELLOW}⚠ 缺少日志记录${NC}"
    fi
done

echo
echo -e "${BLUE}Git Hooks日志率: $git_triggered/$git_total${NC}"
echo

# ==================== 第三部分：日志分析 ====================

echo -e "${YELLOW}[3/3] 分析hooks日志...${NC}"
echo

if [[ -f "$CLAUDE_HOOKS_LOG" ]]; then
    log_count=$(wc -l < "$CLAUDE_HOOKS_LOG")
    unique_hooks=$(cut -d']' -f1 "$CLAUDE_HOOKS_LOG" | grep -oE '\[[^]]+' | sort | uniq | wc -l)

    echo -e "${BLUE}Claude Hooks日志统计：${NC}"
    echo "  • 日志条目数: $log_count"
    echo "  • 不同hooks数: $unique_hooks"
    echo
    echo -e "${BLUE}最近10条日志：${NC}"
    tail -10 "$CLAUDE_HOOKS_LOG" | while read line; do
        echo "  $line"
    done
else
    echo -e "${RED}✗ Claude hooks日志文件不存在${NC}"
fi

echo

if [[ -f "$GIT_HOOKS_LOG" ]]; then
    git_log_count=$(wc -l < "$GIT_HOOKS_LOG")

    echo -e "${BLUE}Git Hooks日志统计：${NC}"
    echo "  • 日志条目数: $git_log_count"
    echo
    echo -e "${BLUE}最近5条日志：${NC}"
    tail -5 "$GIT_HOOKS_LOG" | while read line; do
        echo "  $line"
    done
else
    echo -e "${YELLOW}⚠ Git hooks日志文件不存在（正常，Git hooks在实际操作时触发）${NC}"
fi

echo

# ==================== 总结 ====================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                     测试结果总结                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo

total_hooks=$((claude_total + git_total))
total_triggered=$((claude_triggered + git_triggered))
activation_rate=$(awk "BEGIN {printf \"%.1f\", ($total_triggered/$total_hooks)*100}")

echo -e "${GREEN}✓ Claude Hooks: $claude_triggered/$claude_total 触发${NC}"
echo -e "${GREEN}✓ Git Hooks: $git_triggered/$git_total 配置日志${NC}"
echo -e "${BLUE}总激活率: $activation_rate% ($total_triggered/$total_hooks)${NC}"
echo

if [[ $total_triggered -ge $((total_hooks * 8 / 10)) ]]; then
    echo -e "${GREEN}🎉 测试通过！Hooks激活率达标 (≥80%)${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ 警告：Hooks激活率低于80%，请检查未触发的hooks${NC}"
    exit 1
fi
