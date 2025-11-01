#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# diagnose-bypass-permissions.sh - 诊断Bypass Permissions配置
# Version: 1.0.0
# Purpose: 检查全局和项目配置，诊断bypass permissions问题
# ═══════════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Bypass Permissions诊断工具${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# 检查1: 全局配置
echo -e "${BLUE}[1/5] 检查全局配置 ~/.claude.json${NC}"
echo "----------------------------------------"

if [ -f ~/.claude.json ]; then
    echo -e "${GREEN}✓${NC} 全局配置存在"

    # 检查permissions字段
    if jq -e '.permissions' ~/.claude.json >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠${NC}  全局配置包含permissions字段"

        perm_value=$(jq '.permissions' ~/.claude.json 2>/dev/null)
        if [ "$perm_value" = "null" ]; then
            echo -e "${RED}✗${NC} permissions = null（会覆盖项目配置！）"
            echo ""
            echo -e "${YELLOW}问题${NC}: 全局配置的permissions: null会覆盖项目配置"
            echo -e "${YELLOW}影响${NC}: Task工具需要用户授权（弹窗）"
            echo ""
            GLOBAL_ISSUE=true
        else
            default_mode=$(jq -r '.permissions.defaultMode // "not_set"' ~/.claude.json 2>/dev/null)
            echo "  defaultMode: $default_mode"
            if [ "$default_mode" = "bypassPermissions" ]; then
                echo -e "${GREEN}✓${NC} 全局配置正确设置bypass"
                GLOBAL_ISSUE=false
            else
                echo -e "${YELLOW}⚠${NC}  全局配置未设置bypassPermissions"
                GLOBAL_ISSUE=true
            fi
        fi
    else
        echo -e "${GREEN}✓${NC} 全局配置没有permissions字段（不会覆盖）"
        GLOBAL_ISSUE=false
    fi
else
    echo -e "${GREEN}✓${NC} 全局配置不存在（不会覆盖）"
    GLOBAL_ISSUE=false
fi

echo ""

# 检查2: 项目配置
echo -e "${BLUE}[2/5] 检查项目配置 .claude/settings.json${NC}"
echo "----------------------------------------"

if [ -f "$PROJECT_ROOT/.claude/settings.json" ]; then
    echo -e "${GREEN}✓${NC} 项目配置存在"

    default_mode=$(jq -r '.permissions.defaultMode // "not_set"' "$PROJECT_ROOT/.claude/settings.json" 2>/dev/null)
    echo "  defaultMode: $default_mode"

    if [ "$default_mode" = "bypassPermissions" ]; then
        echo -e "${GREEN}✓${NC} 项目配置正确设置bypass"
        PROJECT_ISSUE=false
    else
        echo -e "${RED}✗${NC} 项目配置未设置bypassPermissions"
        PROJECT_ISSUE=true
    fi

    # 检查allow列表
    allow_count=$(jq '.permissions.allow | length' "$PROJECT_ROOT/.claude/settings.json" 2>/dev/null || echo "0")
    echo "  allow列表: $allow_count个工具"

    # 检查Task是否在allow列表
    if jq -e '.permissions.allow | index("Task")' "$PROJECT_ROOT/.claude/settings.json" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Task工具在allow列表中"
    else
        echo -e "${RED}✗${NC} Task工具不在allow列表中"
        PROJECT_ISSUE=true
    fi
else
    echo -e "${RED}✗${NC} 项目配置不存在"
    PROJECT_ISSUE=true
fi

echo ""

# 检查3: Claude Code版本
echo -e "${BLUE}[3/5] 检查Claude Code版本${NC}"
echo "----------------------------------------"

# 尝试检测Claude Code版本（如果可能）
echo "  检测方式: 通过配置文件格式推断"
if jq -e '.tengu_disable_bypass_permissions_mode' ~/.claude.json >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 检测到Claude Code v2.0+配置格式"
else
    echo -e "${YELLOW}⚠${NC}  未检测到版本特定字段"
fi

echo ""

# 检查4: 配置优先级
echo -e "${BLUE}[4/5] 分析配置优先级${NC}"
echo "----------------------------------------"

echo "  Claude Code优先级: 全局 > 项目"
echo ""

if [ "$GLOBAL_ISSUE" = true ]; then
    echo -e "${RED}✗${NC} 全局配置有问题，会覆盖项目配置"
    FINAL_VERDICT="FAIL"
elif [ "$PROJECT_ISSUE" = true ]; then
    echo -e "${YELLOW}⚠${NC}  项目配置有问题"
    FINAL_VERDICT="WARN"
else
    echo -e "${GREEN}✓${NC} 配置正确，应该不会弹窗"
    FINAL_VERDICT="PASS"
fi

echo ""

# 检查5: 诊断结论和修复建议
echo -e "${BLUE}[5/5] 诊断结论和修复建议${NC}"
echo "----------------------------------------"

if [ "$FINAL_VERDICT" = "FAIL" ]; then
    echo -e "${RED}✗ 诊断结果: 配置有问题${NC}"
    echo ""
    echo "问题原因:"
    if jq -e '.permissions' ~/.claude.json >/dev/null 2>&1; then
        perm_value=$(jq '.permissions' ~/.claude.json 2>/dev/null)
        if [ "$perm_value" = "null" ]; then
            echo "  - 全局配置 ~/.claude.json 包含 permissions: null"
            echo "  - 这会覆盖项目配置的bypassPermissions设置"
        else
            echo "  - 全局配置存在但未设置bypassPermissions"
        fi
    fi
    echo ""
    echo "修复方法（二选一）:"
    echo ""
    echo "方法1（推荐）: 删除全局配置的permissions字段"
    echo "  1. 编辑 ~/.claude.json"
    echo "  2. 删除整个 \"permissions\": {...} 字段"
    echo "  3. 保存文件"
    echo "  4. 重启Claude Code"
    echo ""
    echo "方法2: 在全局配置中也设置bypass"
    echo "  1. 编辑 ~/.claude.json"
    echo "  2. 将permissions字段改为:"
    echo "     {\"permissions\": {\"defaultMode\": \"bypassPermissions\", \"allow\": [\"*\"]}}"
    echo "  3. 保存文件"
    echo "  4. 重启Claude Code"
    echo ""
elif [ "$FINAL_VERDICT" = "WARN" ]; then
    echo -e "${YELLOW}⚠ 诊断结果: 项目配置需要修复${NC}"
    echo ""
    echo "修复方法:"
    echo "  运行: bash tools/verify-bypass-permissions.sh --fix"
    echo ""
elif [ "$FINAL_VERDICT" = "PASS" ]; then
    echo -e "${GREEN}✓ 诊断结果: 配置正确${NC}"
    echo ""
    echo "如果仍然弹窗，可能的原因:"
    echo "  1. 配置缓存未刷新 - 重启Claude Code"
    echo "  2. 特定工具未在allow列表 - 检查具体是哪个工具弹窗"
    echo "  3. Claude Code版本问题 - 确认使用v2.0.8+"
    echo ""
fi

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# 返回退出码
if [ "$FINAL_VERDICT" = "PASS" ]; then
    exit 0
else
    exit 1
fi
