#!/bin/bash

# Phase Switcher - 安全的Phase切换机制
# 功能：验证当前Phase完成后再切换到下一个Phase
# 版本：1.0.0

set -euo pipefail

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PHASE_FILE="$PROJECT_ROOT/.phase/current"
GATES_DIR="$PROJECT_ROOT/.gates"
GATE_VALIDATOR="$SCRIPT_DIR/gate_validator.sh"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# 显示用法
usage() {
    echo "用法: $0 <target_phase>"
    echo ""
    echo "示例:"
    echo "  $0 P2    # 切换到P2阶段"
    echo "  $0 next  # 切换到下一个Phase"
    echo ""
    echo "Phase顺序: P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7"
    exit 1
}

# 获取当前Phase
get_current_phase() {
    if [[ -f "$PHASE_FILE" ]]; then
        cat "$PHASE_FILE"
    else
        echo "P0"
    fi
}

# 获取下一个Phase
get_next_phase() {
    local current="$1"
    case "$current" in
        P0) echo "P1" ;;
        P1) echo "P2" ;;
        P2) echo "P3" ;;
        P3) echo "P4" ;;
        P4) echo "P5" ;;
        P5) echo "P6" ;;
        P6) echo "P7" ;;
        P7) echo "P1" ;;  # 循环回P1
        *) echo "P1" ;;
    esac
}

# 验证Phase是否合法
validate_phase() {
    local phase="$1"
    if [[ ! "$phase" =~ ^P[0-7]$ ]]; then
        echo -e "${RED}❌ 非法的Phase: $phase${NC}"
        echo "合法Phase: P0, P1, P2, P3, P4, P5, P6, P7"
        return 1
    fi
    return 0
}

# 验证Phase顺序
validate_phase_order() {
    local current="$1"
    local target="$2"

    # 提取数字
    local current_num="${current:1:1}"
    local target_num="${target:1:1}"

    # 允许的切换：
    # 1. 向后切换（+1）
    # 2. P7 → P1（循环）
    # 3. 向前跳转（如果中间的gates都存在）

    if [[ "$current" == "P7" && "$target" == "P1" ]]; then
        # P7循环回P1
        return 0
    elif [[ $target_num -eq $((current_num + 1)) ]]; then
        # 正常递进
        return 0
    elif [[ $target_num -gt $((current_num + 1)) ]]; then
        # 跳跃切换 - 检查中间的gates是否都存在
        echo -e "${YELLOW}⚠️  跳跃切换 $current → $target${NC}"
        echo "检查中间Phase的gates..."

        for ((i=current_num; i<target_num; i++)); do
            gate_file="$GATES_DIR/0${i}.ok"
            if [[ ! -f "$gate_file" ]]; then
                echo -e "${RED}❌ P${i} gate不存在: $gate_file${NC}"
                echo "不能跳过未完成的Phase"
                return 1
            fi
            echo -e "${GREEN}✓ P${i} gate存在${NC}"
        done

        echo -e "${GREEN}✓ 中间Phase都已完成${NC}"
        return 0
    else
        # 向前切换 - 一般不允许
        echo -e "${YELLOW}⚠️  警告: 从 $current 向前切换到 $target${NC}"
        read -p "确认要向前切换吗？(y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            return 0
        else
            return 1
        fi
    fi
}

# 验证当前Phase是否可以结束
validate_phase_completion() {
    local phase="$1"

    echo -e "\n${CYAN}[验证 $phase 完成度]${NC}"

    # 检查gate文件是否存在
    local phase_num="${phase:1:1}"
    local gate_file="$GATES_DIR/0${phase_num}.ok"

    if [[ ! -f "$gate_file" ]]; then
        echo -e "${RED}❌ $phase gate文件不存在: $gate_file${NC}"
        echo ""
        echo "需要完成以下步骤："
        echo "1. 完成所有must_produce要求"
        echo "2. 通过所有gates检查"
        echo "3. 创建gate文件: touch $gate_file"
        return 1
    fi

    echo -e "${GREEN}✓ $phase gate文件存在${NC}"

    # 调用gate_validator进行完整验证
    if [[ -x "$GATE_VALIDATOR" ]]; then
        echo "运行gate_validator..."
        if "$GATE_VALIDATOR" validate "$phase"; then
            echo -e "${GREEN}✓ Gate验证通过${NC}"
            return 0
        else
            echo -e "${RED}❌ Gate验证失败${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  gate_validator不可执行，跳过完整验证${NC}"
        return 0
    fi
}

# 切换Phase
switch_phase() {
    local target="$1"

    # 获取当前Phase
    local current
    current=$(get_current_phase)

    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Phase切换: $current → $target${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # 1. 验证target Phase合法
    if ! validate_phase "$target"; then
        return 1
    fi

    # 2. 如果是同一个Phase，跳过
    if [[ "$current" == "$target" ]]; then
        echo -e "${GREEN}✓ 已经在 $target 阶段${NC}"
        return 0
    fi

    # 3. 验证Phase切换顺序
    if ! validate_phase_order "$current" "$target"; then
        return 1
    fi

    # 4. 验证当前Phase是否完成（除非是P0或向前切换）
    if [[ "$current" != "P0" && "${target:1:1}" -gt "${current:1:1}" ]]; then
        if ! validate_phase_completion "$current"; then
            echo ""
            echo -e "${YELLOW}提示: 你可以强制切换（不推荐）：${NC}"
            echo "  echo \"$target\" > $PHASE_FILE"
            return 1
        fi
    fi

    # 5. 执行切换
    echo ""
    echo -e "${GREEN}✅ 验证通过，切换Phase...${NC}"
    echo "$target" > "$PHASE_FILE"

    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ 成功切换到 $target 阶段${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # 6. 显示新Phase的要求
    echo ""
    echo -e "${CYAN}$target 阶段要求:${NC}"
    grep -A 10 "^  $target:" "$SCRIPT_DIR/gates.yml" | head -15 || true

    return 0
}

# 主函数
main() {
    if [[ $# -eq 0 ]]; then
        usage
    fi

    local target="$1"

    # 处理"next"参数
    if [[ "$target" == "next" ]]; then
        local current
        current=$(get_current_phase)
        target=$(get_next_phase "$current")
        echo -e "${CYAN}下一个Phase: $target${NC}"
    fi

    # 切换Phase
    if switch_phase "$target"; then
        exit 0
    else
        exit 1
    fi
}

main "$@"
