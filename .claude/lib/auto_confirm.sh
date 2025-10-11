#!/bin/bash
# Claude Enhancer - 自动确认工具函数
# 提供CE_AUTO_CONFIRM和CE_AUTO_SELECT_DEFAULT功能

# 自动确认函数
# 用法: auto_confirm "提示信息" [默认值]
auto_confirm() {
    local prompt="${1:-Continue?}"
    local default="${2:-y}"
    local response

    # 如果启用自动确认，直接返回默认值
    if [[ "${CE_AUTO_CONFIRM:-false}" == "true" ]]; then
        # 只在非静默模式且紧凑输出关闭时显示
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]] && [[ "${CE_COMPACT_OUTPUT:-false}" != "true" ]]; then
            echo "[AUTO-CONFIRM] $prompt → $default" >&2
        fi
        echo "$default"
        return 0
    fi

    # 否则正常询问用户（除非在静默模式）
    if [[ "${CE_SILENT_MODE:-false}" == "true" ]]; then
        # 静默模式下使用默认值，不询问
        echo "$default"
        return 0
    fi

    read -p "$prompt " response
    echo "${response:-$default}"
}

# 自动选择默认值函数
# 用法: auto_select_default "提示信息" "选项1,选项2,选项3" [默认选项索引]
auto_select_default() {
    local prompt="${1:-Select option:}"
    local options="${2:-}"
    local default_index="${3:-1}"
    local response

    # 将选项字符串转为数组
    IFS=',' read -ra option_array <<< "$options"

    # 如果启用自动选择默认值
    if [[ "${CE_AUTO_SELECT_DEFAULT:-false}" == "true" ]]; then
        local selected="${option_array[$((default_index-1))]}"
        # 只在非静默模式且紧凑输出关闭时显示
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]] && [[ "${CE_COMPACT_OUTPUT:-false}" != "true" ]]; then
            echo "[AUTO-SELECT] $prompt → $selected (option $default_index)" >&2
        fi
        echo "$selected"
        return 0
    fi

    # 静默模式下直接使用默认值
    if [[ "${CE_SILENT_MODE:-false}" == "true" ]]; then
        echo "${option_array[$((default_index-1))]}"
        return 0
    fi

    # 否则显示选项让用户选择
    echo "$prompt" >&2
    local i=1
    for opt in "${option_array[@]}"; do
        echo "  $i) $opt" >&2
        ((i++))
    done

    read -p "选择 (1-${#option_array[@]}) [$default_index]: " response
    response="${response:-$default_index}"

    # 验证输入
    if [[ "$response" =~ ^[0-9]+$ ]] && [ "$response" -ge 1 ] && [ "$response" -le "${#option_array[@]}" ]; then
        echo "${option_array[$((response-1))]}"
    else
        echo "${option_array[$((default_index-1))]}"
    fi
}

# 智能确认函数（根据危险级别决定是否自动确认）
smart_auto_confirm() {
    local prompt="${1:-Continue?}"
    local danger_level="${2:-low}"  # low, medium, high
    local default="${3:-y}"

    # 高危操作永不自动确认（但静默模式下跳过）
    if [[ "$danger_level" == "high" ]]; then
        if [[ "${CE_SILENT_MODE:-false}" == "true" ]]; then
            # 静默模式下高危操作默认拒绝
            echo "n"
            return
        fi
        read -p "⚠️ $prompt (需要手动确认) " response
        echo "${response:-n}"
        return
    fi

    # 中等危险在某些条件下自动确认
    if [[ "$danger_level" == "medium" ]]; then
        if [[ "${CE_AUTO_CONFIRM:-false}" == "true" ]] && [[ "${CE_AUTO_CONFIRM_MEDIUM:-false}" == "true" ]]; then
            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo "[AUTO-CONFIRM-MEDIUM] $prompt → $default" >&2
            fi
            echo "$default"
            return 0
        elif [[ "${CE_SILENT_MODE:-false}" == "true" ]]; then
            # 静默模式但未启用中等危险自动确认，使用默认值
            echo "$default"
            return 0
        else
            read -p "⚠ $prompt " response
            echo "${response:-$default}"
            return
        fi
    fi

    # 低危操作可以自动确认
    auto_confirm "$prompt" "$default"
}

# 导出函数供其他脚本使用
export -f auto_confirm
export -f auto_select_default
export -f smart_auto_confirm