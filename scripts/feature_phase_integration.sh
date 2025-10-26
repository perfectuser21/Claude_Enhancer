#!/bin/bash
# Feature Phase Integration - Phase集成机制
# Purpose: 在7-Phase工作流的适当位置调用注册的功能

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly PROJECT_ROOT
REGISTRY="${PROJECT_ROOT}/.claude/FEATURE_REGISTRY.yaml"
readonly REGISTRY
INTEGRATION_LOG="${PROJECT_ROOT}/.temp/feature_integration.log"
readonly INTEGRATION_LOG

# 创建日志目录
mkdir -p "$(dirname "$INTEGRATION_LOG")"

# ============= 核心函数 =============

# 获取指定Phase的所有活跃功能
get_features_for_phase() {
    local phase="${1:-}"
    local hook_point="${2:-}"

    if [[ ! -f "$REGISTRY" ]]; then
        return 0
    fi

    # 获取所有活跃功能
    local features
    features=$(grep "^  [a-z_]*:" "$REGISTRY" | sed 's/://g' | tr -d ' ')

    for feature in $features; do
        # 检查状态是否为active
        local status
        status=$(grep -A20 "^  ${feature}:" "$REGISTRY" | grep "status:" | head -1 | cut -d'"' -f2)
        [[ "$status" != "active" ]] && continue

        # 检查是否配置了该Phase的集成
        local feature_block
        feature_block=$(sed -n "/^  ${feature}:/,/^  [a-z_]*:/p" "$REGISTRY")

        # 检查是否有匹配的phase和hook_point
        if echo "$feature_block" | grep -q "phase: \"$phase\"" || \
           echo "$feature_block" | grep -q "phase: \"all\""; then
            if [[ -z "$hook_point" ]] || \
               echo "$feature_block" | grep -q "hook_point: \"$hook_point\""; then
                echo "$feature"
            fi
        fi
    done
}

# 执行功能
execute_feature() {
    local feature="${1:-}"
    local phase="${2:-}"
    local hook_point="${3:-}"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Executing $feature for Phase $phase at $hook_point" >> "$INTEGRATION_LOG"

    # 获取功能位置
    local location
    location=$(grep -A5 "^  ${feature}:" "$REGISTRY" | grep "location:" | head -1 | cut -d'"' -f2)

    if [[ ! -f "${PROJECT_ROOT}/${location}" ]]; then
        echo "[ERROR] Feature file not found: $location" >> "$INTEGRATION_LOG"
        return 1
    fi

    # 设置环境变量供功能使用
    export FEATURE_PHASE="$phase"
    export FEATURE_HOOK="$hook_point"
    export FEATURE_NAME="$feature"

    # 执行功能
    if bash "${PROJECT_ROOT}/${location}" 2>&1 | tee -a "$INTEGRATION_LOG"; then
        echo "[SUCCESS] $feature executed successfully" >> "$INTEGRATION_LOG"
        return 0
    else
        echo "[FAILED] $feature execution failed" >> "$INTEGRATION_LOG"
        return 1
    fi
}

# Phase 1: Discovery & Planning 集成点
phase1_integration() {
    local hook_point="${1:-pre_discovery}"

    echo "🔧 Phase 1 Integration: $hook_point"

    local features
    features=$(get_features_for_phase "1" "$hook_point")
    for feature in $features; do
        echo "  → Executing: $feature"
        execute_feature "$feature" "1" "$hook_point"
    done
}

# Phase 2: Implementation 集成点
phase2_integration() {
    local hook_point="${1:-pre_implementation}"

    echo "🔧 Phase 2 Integration: $hook_point"

    local features
    features=$(get_features_for_phase "2" "$hook_point")
    for feature in $features; do
        echo "  → Executing: $feature"
        execute_feature "$feature" "2" "$hook_point"
    done
}

# Phase 3: Testing 集成点
phase3_integration() {
    local hook_point="${1:-pre_test}"

    echo "🔧 Phase 3 Integration: $hook_point"

    local features
    features=$(get_features_for_phase "3" "$hook_point")

    # 特殊处理：replace_test类型
    if [[ "$hook_point" == "replace_test" ]] && [[ -n "$features" ]]; then
        echo "  → Replacing default test with custom features"
        for feature in $features; do
            execute_feature "$feature" "3" "$hook_point"
        done
        return 0  # 跳过默认测试
    fi

    # 普通集成
    for feature in $features; do
        echo "  → Executing: $feature"
        execute_feature "$feature" "3" "$hook_point"
    done
}

# Phase 4: Review 集成点
phase4_integration() {
    local hook_point="${1:-pre_review}"

    echo "🔧 Phase 4 Integration: $hook_point"

    local features
    features=$(get_features_for_phase "4" "$hook_point")

    # 特殊处理：replace_review类型（如parallel_review）
    if [[ "$hook_point" == "replace_review" ]] && [[ -n "$features" ]]; then
        echo "  → Replacing default review with custom features"
        for feature in $features; do
            execute_feature "$feature" "4" "$hook_point"
        done
        return 0  # 跳过默认审查
    fi

    for feature in $features; do
        echo "  → Executing: $feature"
        execute_feature "$feature" "4" "$hook_point"
    done
}

# Phase 5: Release 集成点
phase5_integration() {
    local hook_point="${1:-pre_release}"

    echo "🔧 Phase 5 Integration: $hook_point"

    local features
    features=$(get_features_for_phase "5" "$hook_point")
    for feature in $features; do
        echo "  → Executing: $feature"
        execute_feature "$feature" "5" "$hook_point"
    done
}

# Phase 6: Acceptance 集成点
phase6_integration() {
    local hook_point="${1:-validation_check}"

    echo "🔧 Phase 6 Integration: $hook_point"

    local features
    features=$(get_features_for_phase "6" "$hook_point")
    for feature in $features; do
        echo "  → Executing: $feature"
        execute_feature "$feature" "6" "$hook_point"
    done
}

# Phase 7: Closure 集成点
phase7_integration() {
    local hook_point="${1:-cleanup_hook}"

    echo "🔧 Phase 7 Integration: $hook_point"

    local features
    features=$(get_features_for_phase "7" "$hook_point")
    for feature in $features; do
        echo "  → Executing: $feature"
        execute_feature "$feature" "7" "$hook_point"
    done
}

# 通用集成点（所有Phase）
all_phases_integration() {
    local hook_point="${1:-pre_execution}"

    echo "🔧 All Phases Integration: $hook_point"

    local features
    features=$(get_features_for_phase "all" "$hook_point")
    for feature in $features; do
        echo "  → Executing: $feature"
        execute_feature "$feature" "all" "$hook_point"
    done
}

# ============= 使用示例 =============

# 这个脚本应该被各个Phase脚本source并调用
# 例如在Phase 3脚本中：
#
# source scripts/feature_phase_integration.sh
#
# # 测试前
# phase3_integration "pre_test"
#
# # 运行测试
# run_tests
#
# # 测试后
# phase3_integration "post_test"

# 如果直接运行，显示帮助
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Feature Phase Integration System"
    echo "================================"
    echo ""
    echo "This script provides integration points for the 7-Phase workflow."
    echo ""
    echo "Usage:"
    echo "  Source this script in your Phase scripts:"
    echo "  source $(basename "$0")"
    echo ""
    echo "Available functions:"
    echo "  phase1_integration <hook_point>  - Phase 1 hooks"
    echo "  phase2_integration <hook_point>  - Phase 2 hooks"
    echo "  phase3_integration <hook_point>  - Phase 3 hooks"
    echo "  phase4_integration <hook_point>  - Phase 4 hooks"
    echo "  phase5_integration <hook_point>  - Phase 5 hooks"
    echo "  phase6_integration <hook_point>  - Phase 6 hooks"
    echo "  phase7_integration <hook_point>  - Phase 7 hooks"
    echo "  all_phases_integration <hook>    - All phases hooks"
    echo ""
    echo "Hook points:"
    echo "  pre_*     - Before phase execution"
    echo "  post_*    - After phase execution"
    echo "  replace_* - Replace default implementation"
    echo ""
    echo "Integration log: $INTEGRATION_LOG"
fi