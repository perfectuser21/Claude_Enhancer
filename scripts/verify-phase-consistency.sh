#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Phase一致性验证工具
# Claude Enhancer v7.0.0
# ═══════════════════════════════════════════════════════════════
# 功能：验证SPEC.yaml、manifest.yml、CLAUDE.md的Phase定义一致性
# 用途：防止Phase定义混乱（如8个Phase vs 7个Phase问题）
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ═══════════════════════════════════════════════════════════════
# Phase数量提取函数
# ═══════════════════════════════════════════════════════════════

get_spec_phase_count() {
    local spec="$PROJECT_ROOT/.workflow/SPEC.yaml"
    if [[ ! -f "$spec" ]]; then
        echo "ERROR: SPEC.yaml not found" >&2
        return 1
    fi

    # Extract total_phases value
    grep "total_phases:" "$spec" | awk '{print $2}' | tr -d '#⛔ 不可改：必须个Phase' | xargs
}

get_manifest_phase_count() {
    local manifest="$PROJECT_ROOT/.workflow/manifest.yml"
    if [[ ! -f "$manifest" ]]; then
        echo "ERROR: manifest.yml not found" >&2
        return 1
    fi

    # Count phases array length
    if command -v yq >/dev/null 2>&1; then
        yq '.phases | length' "$manifest" 2>/dev/null || echo "ERROR"
    elif command -v python3 >/dev/null 2>&1; then
        python3 -c "import yaml; print(len(yaml.safe_load(open('$manifest'))['phases']))" 2>/dev/null || echo "ERROR"
    else
        # Fallback: count "- id:" lines
        grep -c "^  - id:" "$manifest" || echo "ERROR"
    fi
}

get_claude_phase_count() {
    local claude="$PROJECT_ROOT/CLAUDE.md"
    if [[ ! -f "$claude" ]]; then
        echo "ERROR: CLAUDE.md not found" >&2
        return 1
    fi

    # Extract from "7-Phase系统" or "7 Phases"
    grep -oP '(\d+)-Phase系统|(\d+) Phases' "$claude" | head -1 | grep -oP '\d+' || echo "ERROR"
}

# ═══════════════════════════════════════════════════════════════
# Phase名称提取函数
# ═══════════════════════════════════════════════════════════════

get_spec_phase_names() {
    local spec="$PROJECT_ROOT/.workflow/SPEC.yaml"
    if [[ ! -f "$spec" ]]; then
        echo "ERROR: SPEC.yaml not found" >&2
        return 1
    fi

    # Extract phase_names list (skip header, take quoted strings)
    awk '/phase_names:/,/^$/ {if ($0 ~ /- "/) print}' "$spec" | \
        sed 's/.*- "\(.*\)"/\1/' || echo "ERROR"
}

get_manifest_phase_ids() {
    local manifest="$PROJECT_ROOT/.workflow/manifest.yml"
    if [[ ! -f "$manifest" ]]; then
        echo "ERROR: manifest.yml not found" >&2
        return 1
    fi

    # Extract phase IDs
    if command -v yq >/dev/null 2>&1; then
        yq '.phases[] | .id' "$manifest" 2>/dev/null || echo "ERROR"
    else
        grep "^  - id:" "$manifest" | awk '{print $3}' || echo "ERROR"
    fi
}

# ═══════════════════════════════════════════════════════════════
# Phase一致性检查
# ═══════════════════════════════════════════════════════════════

check_phase_consistency() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}🔄 Phase系统一致性检查${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""

    local errors=0

    # ────────────────────────────────────────────────────────────
    # Check 1: Phase数量一致性
    # ────────────────────────────────────────────────────────────

    echo -e "${BOLD}[1/3] Phase数量一致性${NC}"
    echo ""

    local spec_count
    local manifest_count
    local claude_count
    spec_count=$(get_spec_phase_count)
    manifest_count=$(get_manifest_phase_count)
    claude_count=$(get_claude_phase_count)

    echo -e "  ${CYAN}SPEC.yaml:${NC}        $spec_count Phases"
    echo -e "  ${CYAN}manifest.yml:${NC}     $manifest_count Phases"
    echo -e "  ${CYAN}CLAUDE.md:${NC}        $claude_count Phases"
    echo ""

    if [[ "$spec_count" == "$manifest_count" ]] && [[ "$spec_count" == "$claude_count" ]]; then
        echo -e "  ${GREEN}✅ Phase数量一致${NC} - 所有定义都是 ${BOLD}$spec_count Phases${NC}"
    else
        echo -e "  ${RED}❌ Phase数量不一致！${NC}"
        [[ "$spec_count" != "$manifest_count" ]] && \
            echo -e "     SPEC ($spec_count) ≠ manifest ($manifest_count)"
        [[ "$spec_count" != "$claude_count" ]] && \
            echo -e "     SPEC ($spec_count) ≠ CLAUDE.md ($claude_count)"
        errors=$((errors + 1))
    fi
    echo ""

    # ────────────────────────────────────────────────────────────
    # Check 2: Phase ID命名规范
    # ────────────────────────────────────────────────────────────

    echo -e "${BOLD}[2/3] Phase ID命名规范${NC}"
    echo ""

    local manifest_ids
    manifest_ids=$(get_manifest_phase_ids)

    echo -e "  ${CYAN}manifest.yml Phase IDs:${NC}"
    echo "$manifest_ids" | while read -r id; do
        echo "    - $id"
    done
    echo ""

    # Check if IDs follow Phase1-Phase7 pattern
    local expected_pattern="^Phase[1-7]$"
    local invalid_ids=0

    while read -r id; do
        if [[ ! "$id" =~ $expected_pattern ]]; then
            echo -e "  ${RED}❌ 非法Phase ID:${NC} $id (应为Phase1-Phase7)"
            invalid_ids=$((invalid_ids + 1))
        fi
    done <<< "$manifest_ids"

    if [[ $invalid_ids -eq 0 ]]; then
        echo -e "  ${GREEN}✅ Phase ID命名正确${NC} - 符合Phase1-Phase7规范"
    else
        errors=$((errors + 1))
    fi
    echo ""

    # ────────────────────────────────────────────────────────────
    # Check 3: Phase名称映射
    # ────────────────────────────────────────────────────────────

    echo -e "${BOLD}[3/3] Phase名称映射检查${NC}"
    echo ""

    echo -e "  ${CYAN}SPEC.yaml定义的标准Phase名称:${NC}"
    get_spec_phase_names | nl -w2 -s'. ' | sed 's/^/    /'
    echo ""

    # 简化检查：确保manifest中至少有Phase1包含"Discovery & Planning"
    local manifest_phase1_name=""
    if command -v yq >/dev/null 2>&1; then
        manifest_phase1_name=$(yq '.phases[] | select(.id == "Phase1") | .name' "$PROJECT_ROOT/.workflow/manifest.yml" 2>/dev/null)
    else
        manifest_phase1_name=$(awk '/- id: Phase1/,/- id: Phase2/ {if ($0 ~ /name:/) print $2}' "$PROJECT_ROOT/.workflow/manifest.yml" | head -1)
    fi

    if [[ "$manifest_phase1_name" =~ "Discovery" ]] && [[ "$manifest_phase1_name" =~ "Planning" ]]; then
        echo -e "  ${GREEN}✅ Phase名称映射正确${NC} - Phase1包含Discovery & Planning"
    else
        echo -e "  ${YELLOW}⚠️  Phase1名称可能不匹配${NC} - 当前: $manifest_phase1_name"
        echo -e "     (预期包含: Discovery & Planning)"
        # 警告但不算错误
    fi
    echo ""

    # ────────────────────────────────────────────────────────────
    # 最终结果
    # ────────────────────────────────────────────────────────────

    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    if [[ $errors -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}✅ Phase系统一致性检查通过${NC}"
        echo ""
        echo -e "  所有Phase定义一致："
        echo -e "  - Phase数量: ${BOLD}$spec_count Phases${NC}"
        echo -e "  - Phase ID: Phase1-Phase7"
        echo -e "  - 定义文件: SPEC.yaml ⇄ manifest.yml ⇄ CLAUDE.md"
        echo ""
        return 0
    else
        echo -e "${RED}${BOLD}❌ Phase系统一致性检查失败${NC}"
        echo ""
        echo -e "  发现 ${RED}$errors${NC} 个不一致问题"
        echo ""
        echo -e "${BOLD}🔧 修复建议：${NC}"
        echo ""
        echo -e "  1. 统一Phase数量为 ${BOLD}7个Phase${NC}（Phase 1-7）"
        echo -e "  2. 修改manifest.yml使用Phase1-Phase7 ID格式"
        echo -e "  3. 更新CLAUDE.md确保描述为7-Phase系统"
        echo -e "  4. 运行tools/update-lock.sh更新LOCK.json"
        echo ""
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════
# 执行检查
# ═══════════════════════════════════════════════════════════════

check_phase_consistency

exit $?
