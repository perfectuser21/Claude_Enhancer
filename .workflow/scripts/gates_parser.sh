#!/bin/bash

# Gates Parser - 共享的gates.yml解析函数
# 用于本地pre-commit和CI工作流
# Version: 1.0.0

set -euo pipefail

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GATES_FILE="$PROJECT_ROOT/.workflow/gates.yml"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 获取指定Phase的allow_paths
# 参数: $1 = phase (P0, P1, etc.)
# 返回: 路径列表（每行一个）
get_allow_paths() {
    local phase="$1"

    if [ ! -f "$GATES_FILE" ]; then
        echo "**" # 如果没有gates.yml，默认允许所有
        return
    fi

    # 使用awk解析YAML中的allow_paths（JSON数组格式）
    awk -v phase="$phase" '
        /^  [A-Z0-9]+:/ { current_phase = substr($1, 1, length($1)-1) }
        current_phase == phase && /^    allow_paths: \[/ {
            # JSON数组格式: allow_paths: ["item1", "item2"]
            line = $0
            sub(/.*allow_paths: \[/, "", line)
            sub(/\].*/, "", line)
            # 分割引号内的元素
            gsub(/"/, "", line)
            n = split(line, items, ", ")
            for (i = 1; i <= n; i++) {
                print items[i]
            }
        }
    ' "$GATES_FILE"
}

# 匹配glob模式
# 参数: $1 = file, $2 = pattern (注意参数顺序与pre-commit一致)
# 返回: 0 (匹配) 或 1 (不匹配)
match_glob() {
    local file="$1"
    local pattern="$2"

    if [ "$pattern" = "**" ]; then
        return 0  # 匹配所有
    fi

    # 转换glob模式为正则表达式
    # 关键：先用占位符替换**，避免被后续的*替换影响
    local regex_pattern="$pattern"
    regex_pattern="${regex_pattern//\*\*/__DOUBLESTAR__}"  # ** -> 占位符
    regex_pattern="${regex_pattern//\*/[^/]*}"             # * -> [^/]*
    regex_pattern="${regex_pattern//__DOUBLESTAR__/.*}"    # 占位符 -> .*
    regex_pattern="^${regex_pattern}$"

    if echo "$file" | grep -qE "$regex_pattern"; then
        return 0
    else
        return 1
    fi
}

# 获取指定Phase的must_produce
# 参数: $1 = phase
# 返回: 产出列表（每行一个，格式：file_path: description）
get_must_produce() {
    local phase="$1"

    if [ ! -f "$GATES_FILE" ]; then
        return
    fi

    awk -v phase="$phase" '
        /^  [A-Z0-9]+:/ { current_phase = substr($1, 1, length($1)-1) }
        current_phase == phase && /^    must_produce:/ { in_produce = 1; next }
        in_produce && /^      - / {
            rule = substr($0, 9)
            gsub(/^"/, "", rule)
            gsub(/"$/, "", rule)
            print rule
        }
        in_produce && /^    [a-z_]+:/ { in_produce = 0 }
    ' "$GATES_FILE"
}

# 获取Phase名称
# 参数: $1 = phase
# 返回: Phase的名称
get_phase_name() {
    local phase="$1"

    if [ ! -f "$GATES_FILE" ]; then
        echo ""
        return
    fi

    awk -v phase="$phase" '
        /^  [A-Z0-9]+:/ { p = substr($1, 1, length($1)-1) }
        p == phase && /^    name:/ {
            name = substr($0, index($0, "\"") + 1)
            name = substr(name, 1, index(name, "\"") - 1)
            if (name == "") {
                name = substr($0, 11)
                gsub(/^[ \t]+|[ \t]+$/, "", name)
            }
            print name
            exit
        }
    ' "$GATES_FILE"
}

# 验证路径是否在白名单中
# 参数: $1 = phase, $2 = file_path
# 返回: 0 (允许) 或 1 (拒绝)
validate_path() {
    local phase="$1"
    local file_path="$2"

    local allow_paths
    allow_paths=$(get_allow_paths "$phase")

    # 如果没有配置，默认拒绝
    if [ -z "$allow_paths" ]; then
        return 1
    fi

    # 遍历allow_paths，使用match_glob检查
    while IFS= read -r pattern; do
        if match_glob "$file_path" "$pattern"; then
            return 0  # 匹配成功
        fi
    done <<< "$allow_paths"

    return 1  # 未匹配任何模式
}

# 验证must_produce是否满足
# 参数: $1 = phase, $2 = is_phase_ending (true/false)
# 返回: 0 (满足) 或 1 (不满足)
validate_must_produce() {
    local phase="$1"
    local is_phase_ending="${2:-false}"

    local must_produce
    must_produce=$(get_must_produce "$phase")

    if [ -z "$must_produce" ]; then
        return 0  # 没有must_produce要求
    fi

    local missing_count=0

    while IFS= read -r rule; do
        # 提取文件路径（冒号前的部分）
        local file_path="${rule%%:*}"

        if [ ! -f "$PROJECT_ROOT/$file_path" ] && [ ! -d "$PROJECT_ROOT/$file_path" ]; then
            if [ "$is_phase_ending" = "true" ]; then
                echo -e "${RED}❌ 缺少必须产出: $file_path${NC}" >&2
            else
                echo -e "${YELLOW}⚠️  待完成: $file_path${NC}" >&2
            fi
            ((missing_count++))
        fi
    done <<< "$must_produce"

    if [ $missing_count -gt 0 ] && [ "$is_phase_ending" = "true" ]; then
        return 1  # Phase结束时强制要求
    fi

    return 0  # 非Phase结束时仅警告
}

# 主函数（用于测试）
main() {
    if [[ $# -lt 1 ]]; then
        echo "用法: $0 <command> [args...]"
        echo "命令:"
        echo "  get_allow_paths <phase>"
        echo "  get_must_produce <phase>"
        echo "  get_phase_name <phase>"
        echo "  match_glob <file> <pattern>"
        echo "  validate_path <phase> <file_path>"
        echo "  validate_must_produce <phase> <is_phase_ending>"
        exit 1
    fi

    local command="$1"
    shift

    case "$command" in
        get_allow_paths)
            get_allow_paths "$@"
            ;;
        get_must_produce)
            get_must_produce "$@"
            ;;
        get_phase_name)
            get_phase_name "$@"
            ;;
        match_glob)
            match_glob "$@"
            ;;
        validate_path)
            validate_path "$@"
            if [ $? -eq 0 ]; then
                echo "✓ Path allowed"
            else
                echo "✗ Path rejected"
            fi
            ;;
        validate_must_produce)
            validate_must_produce "$@"
            if [ $? -eq 0 ]; then
                echo "✓ Must produce satisfied"
            else
                echo "✗ Must produce not satisfied"
            fi
            ;;
        *)
            echo "未知命令: $command"
            exit 1
            ;;
    esac
}

# 如果直接执行脚本（非source）
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
