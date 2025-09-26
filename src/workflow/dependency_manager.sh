#!/bin/bash
# Claude Enhancer 5.0 - Dependency Manager
# 任务依赖管理器，支持DAG验证和依赖解析
# Version: 1.0.0

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly TASK_QUEUE_DIR="${PROJECT_ROOT}/.workflow/queue"
readonly DEPENDENCY_GRAPH_FILE="${PROJECT_ROOT}/.workflow/state/dependency_graph.json"

# 日志函数
log_info() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $*"; }
log_error() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*" >&2; }

# 初始化依赖图
init_dependency_graph() {
    mkdir -p "$(dirname "$DEPENDENCY_GRAPH_FILE")"
    if [[ ! -f "$DEPENDENCY_GRAPH_FILE" ]]; then
        echo '{"nodes": {}, "edges": {}, "updated_at": "'$(date -Iseconds)'"}' > "$DEPENDENCY_GRAPH_FILE"
    fi
}

# 添加任务节点
add_task_node() {
    local task_id="$1"
    local task_name="$2"
    local priority="${3:-5}"

    init_dependency_graph

    local temp_file=$(mktemp)
    jq --arg task_id "$task_id" \
       --arg task_name "$task_name" \
       --arg priority "$priority" \
       --arg timestamp "$(date -Iseconds)" \
       '.nodes[$task_id] = {
           "name": $task_name,
           "priority": ($priority | tonumber),
           "status": "pending",
           "dependencies": [],
           "dependents": [],
           "created_at": $timestamp
       } | .updated_at = $timestamp' \
       "$DEPENDENCY_GRAPH_FILE" > "$temp_file"

    mv "$temp_file" "$DEPENDENCY_GRAPH_FILE"
    log_info "添加任务节点: $task_id"
}

# 添加依赖关系
add_dependency() {
    local task_id="$1"
    local dependency_id="$2"

    init_dependency_graph

    # 检查节点是否存在
    if ! jq -e ".nodes[\"$task_id\"]" "$DEPENDENCY_GRAPH_FILE" >/dev/null; then
        log_error "任务不存在: $task_id"
        return 1
    fi

    if ! jq -e ".nodes[\"$dependency_id\"]" "$DEPENDENCY_GRAPH_FILE" >/dev/null; then
        log_error "依赖任务不存在: $dependency_id"
        return 1
    fi

    # 检查循环依赖
    if check_circular_dependency "$task_id" "$dependency_id"; then
        log_error "检测到循环依赖: $task_id -> $dependency_id"
        return 1
    fi

    local temp_file=$(mktemp)
    jq --arg task_id "$task_id" \
       --arg dependency_id "$dependency_id" \
       --arg timestamp "$(date -Iseconds)" \
       '
       # 添加依赖到任务的dependencies列表
       .nodes[$task_id].dependencies += [$dependency_id] |
       .nodes[$task_id].dependencies |= unique |

       # 添加任务到依赖的dependents列表
       .nodes[$dependency_id].dependents += [$task_id] |
       .nodes[$dependency_id].dependents |= unique |

       # 添加边
       .edges[$task_id + "->" + $dependency_id] = {
           "from": $dependency_id,
           "to": $task_id,
           "created_at": $timestamp
       } |
       .updated_at = $timestamp
       ' \
       "$DEPENDENCY_GRAPH_FILE" > "$temp_file"

    mv "$temp_file" "$DEPENDENCY_GRAPH_FILE"
    log_info "添加依赖关系: $task_id -> $dependency_id"
}

# 检查循环依赖（DFS）
check_circular_dependency() {
    local task_id="$1"
    local dependency_id="$2"

    # 使用临时文件存储访问状态
    local visited_file=$(mktemp)
    local rec_stack_file=$(mktemp)

    # 从dependency_id开始DFS，看是否能回到task_id
    if dfs_check_cycle "$dependency_id" "$task_id" "$visited_file" "$rec_stack_file"; then
        rm -f "$visited_file" "$rec_stack_file"
        return 0  # 有循环
    fi

    rm -f "$visited_file" "$rec_stack_file"
    return 1  # 无循环
}

# DFS循环检测
dfs_check_cycle() {
    local current_node="$1"
    local target_node="$2"
    local visited_file="$3"
    local rec_stack_file="$4"

    # 如果当前节点就是目标节点，说明有循环
    if [[ "$current_node" == "$target_node" ]]; then
        return 0
    fi

    # 标记当前节点为已访问和在递归栈中
    echo "$current_node" >> "$visited_file"
    echo "$current_node" >> "$rec_stack_file"

    # 获取当前节点的依赖
    local dependencies=$(jq -r ".nodes[\"$current_node\"].dependencies[]?" "$DEPENDENCY_GRAPH_FILE" 2>/dev/null || echo "")

    while read -r dep; do
        [[ -z "$dep" ]] && continue

        # 如果依赖节点在递归栈中，说明有循环
        if grep -q "^$dep$" "$rec_stack_file"; then
            return 0
        fi

        # 如果依赖节点未访问过，递归检查
        if ! grep -q "^$dep$" "$visited_file"; then
            if dfs_check_cycle "$dep" "$target_node" "$visited_file" "$rec_stack_file"; then
                return 0
            fi
        fi
    done <<< "$dependencies"

    # 从递归栈中移除当前节点
    grep -v "^$current_node$" "$rec_stack_file" > "${rec_stack_file}.tmp" || touch "${rec_stack_file}.tmp"
    mv "${rec_stack_file}.tmp" "$rec_stack_file"

    return 1
}

# 获取任务的直接依赖
get_direct_dependencies() {
    local task_id="$1"

    if ! jq -e ".nodes[\"$task_id\"]" "$DEPENDENCY_GRAPH_FILE" >/dev/null 2>&1; then
        log_error "任务不存在: $task_id"
        return 1
    fi

    jq -r ".nodes[\"$task_id\"].dependencies[]?" "$DEPENDENCY_GRAPH_FILE" 2>/dev/null || echo ""
}

# 获取任务的所有依赖（递归）
get_all_dependencies() {
    local task_id="$1"
    local visited_file=$(mktemp)
    local result_file=$(mktemp)

    get_all_deps_recursive "$task_id" "$visited_file" "$result_file"

    cat "$result_file"
    rm -f "$visited_file" "$result_file"
}

# 递归获取所有依赖
get_all_deps_recursive() {
    local task_id="$1"
    local visited_file="$2"
    local result_file="$3"

    # 如果已访问过，避免循环
    if grep -q "^$task_id$" "$visited_file"; then
        return
    fi

    echo "$task_id" >> "$visited_file"

    # 获取直接依赖
    local direct_deps=$(get_direct_dependencies "$task_id")

    while read -r dep; do
        [[ -z "$dep" ]] && continue

        echo "$dep" >> "$result_file"
        get_all_deps_recursive "$dep" "$visited_file" "$result_file"
    done <<< "$direct_deps"
}

# 拓扑排序
topological_sort() {
    local temp_graph_file=$(mktemp)
    local result_file=$(mktemp)
    local queue_file=$(mktemp)

    # 复制图到临时文件
    cp "$DEPENDENCY_GRAPH_FILE" "$temp_graph_file"

    # 找到所有入度为0的节点
    jq -r '.nodes | to_entries[] | select(.value.dependencies | length == 0) | .key' \
        "$temp_graph_file" > "$queue_file"

    # Kahn算法
    while [[ -s "$queue_file" ]]; do
        local current_node=$(head -n1 "$queue_file")
        tail -n +2 "$queue_file" > "${queue_file}.tmp"
        mv "${queue_file}.tmp" "$queue_file"

        echo "$current_node" >> "$result_file"

        # 获取当前节点的依赖者
        local dependents=$(jq -r ".nodes[\"$current_node\"].dependents[]?" "$temp_graph_file" 2>/dev/null || echo "")

        while read -r dependent; do
            [[ -z "$dependent" ]] && continue

            # 从依赖者的依赖列表中移除当前节点
            jq --arg current "$current_node" --arg dependent "$dependent" \
                '.nodes[$dependent].dependencies = (.nodes[$dependent].dependencies - [$current])' \
                "$temp_graph_file" > "${temp_graph_file}.tmp"
            mv "${temp_graph_file}.tmp" "$temp_graph_file"

            # 如果依赖者的入度变为0，加入队列
            local new_deps_count=$(jq -r ".nodes[\"$dependent\"].dependencies | length" "$temp_graph_file")
            if [[ "$new_deps_count" == "0" ]]; then
                echo "$dependent" >> "$queue_file"
            fi
        done <<< "$dependents"
    done

    # 检查是否有剩余的节点（说明有循环）
    local remaining_nodes=$(jq -r '.nodes | to_entries[] | select(.value.dependencies | length > 0) | .key' "$temp_graph_file")
    if [[ -n "$remaining_nodes" ]]; then
        log_error "检测到循环依赖，无法完成拓扑排序"
        log_error "剩余节点: $remaining_nodes"
        rm -f "$temp_graph_file" "$result_file" "$queue_file"
        return 1
    fi

    cat "$result_file"
    rm -f "$temp_graph_file" "$result_file" "$queue_file"
}

# 检查任务是否可以执行
can_execute_task() {
    local task_id="$1"

    # 获取任务的直接依赖
    local dependencies=$(get_direct_dependencies "$task_id")

    # 检查每个依赖是否已完成
    while read -r dep_id; do
        [[ -z "$dep_id" ]] && continue

        # 检查依赖任务是否在completed队列中
        if [[ ! -f "${TASK_QUEUE_DIR}/completed/${dep_id}.json" ]]; then
            log_info "任务 $task_id 的依赖 $dep_id 未完成"
            return 1
        fi
    done <<< "$dependencies"

    return 0
}

# 更新任务状态
update_task_status() {
    local task_id="$1"
    local new_status="$2"

    init_dependency_graph

    if ! jq -e ".nodes[\"$task_id\"]" "$DEPENDENCY_GRAPH_FILE" >/dev/null; then
        log_error "任务不存在: $task_id"
        return 1
    fi

    local temp_file=$(mktemp)
    jq --arg task_id "$task_id" \
       --arg status "$new_status" \
       --arg timestamp "$(date -Iseconds)" \
       '.nodes[$task_id].status = $status |
        .nodes[$task_id].updated_at = $timestamp |
        .updated_at = $timestamp' \
       "$DEPENDENCY_GRAPH_FILE" > "$temp_file"

    mv "$temp_file" "$DEPENDENCY_GRAPH_FILE"
    log_info "更新任务状态: $task_id -> $new_status"
}

# 获取就绪任务列表
get_ready_tasks() {
    local ready_tasks=()

    # 检查所有pending状态的任务
    local pending_tasks=$(jq -r '.nodes | to_entries[] | select(.value.status == "pending") | .key' "$DEPENDENCY_GRAPH_FILE" 2>/dev/null || echo "")

    while read -r task_id; do
        [[ -z "$task_id" ]] && continue

        if can_execute_task "$task_id"; then
            ready_tasks+=("$task_id")
        fi
    done <<< "$pending_tasks"

    # 按优先级排序
    for task_id in "${ready_tasks[@]}"; do
        local priority=$(jq -r ".nodes[\"$task_id\"].priority" "$DEPENDENCY_GRAPH_FILE")
        echo "$priority $task_id"
    done | sort -n | cut -d' ' -f2
}

# 可视化依赖图
visualize_dependency_graph() {
    local output_format="${1:-text}"

    init_dependency_graph

    case "$output_format" in
        "text")
            visualize_text
            ;;
        "dot")
            visualize_dot
            ;;
        "json")
            cat "$DEPENDENCY_GRAPH_FILE"
            ;;
        *)
            log_error "不支持的输出格式: $output_format"
            return 1
            ;;
    esac
}

# 文本格式可视化
visualize_text() {
    echo "依赖关系图:"
    echo "============"

    # 显示所有节点
    jq -r '.nodes | to_entries[] | "\(.key): \(.value.name) (\(.value.status)) [优先级: \(.value.priority)]"' \
        "$DEPENDENCY_GRAPH_FILE"

    echo
    echo "依赖关系:"
    echo "--------"

    # 显示所有边
    jq -r '.edges | to_entries[] | "\(.value.from) -> \(.value.to)"' \
        "$DEPENDENCY_GRAPH_FILE"
}

# DOT格式可视化（用于Graphviz）
visualize_dot() {
    echo "digraph DependencyGraph {"
    echo "  rankdir=TB;"
    echo "  node [shape=box, style=rounded];"

    # 添加节点
    jq -r '.nodes | to_entries[] |
           "  \"" + .key + "\" [label=\"" + .value.name + "\\n(" + .value.status + ")\\nP:" + (.value.priority|tostring) + "\", color=" +
           (if .value.status == "completed" then "green"
            elif .value.status == "running" then "yellow"
            elif .value.status == "failed" then "red"
            else "lightblue" end) + "];"' \
        "$DEPENDENCY_GRAPH_FILE"

    echo

    # 添加边
    jq -r '.edges | to_entries[] | "  \"" + .value.from + "\" -> \"" + .value.to + "\";"' \
        "$DEPENDENCY_GRAPH_FILE"

    echo "}"
}

# 清理完成的依赖关系
cleanup_completed_dependencies() {
    local retention_days="${1:-7}"
    local cutoff_date=$(date -d "$retention_days days ago" +%s)

    init_dependency_graph

    local temp_file=$(mktemp)

    # 移除过期的已完成任务节点
    jq --arg cutoff "$cutoff_date" '
        .nodes = (.nodes | with_entries(
            select(
                .value.status != "completed" or
                (.value.updated_at // .value.created_at | fromdateiso8601) >= ($cutoff | tonumber)
            )
        )) |
        # 同时清理相关的边
        .edges = (.edges | with_entries(
            select(
                .value.from as $from | .value.to as $to |
                (.nodes[$from] and .nodes[$to])
            )
        )) |
        .updated_at = "'$(date -Iseconds)'"
    ' "$DEPENDENCY_GRAPH_FILE" > "$temp_file"

    mv "$temp_file" "$DEPENDENCY_GRAPH_FILE"
    log_info "清理了${retention_days}天前的已完成依赖关系"
}

# 依赖统计
show_dependency_stats() {
    init_dependency_graph

    echo "依赖关系统计:"
    echo "=============="

    local total_nodes=$(jq '.nodes | length' "$DEPENDENCY_GRAPH_FILE")
    local total_edges=$(jq '.edges | length' "$DEPENDENCY_GRAPH_FILE")

    echo "总任务数: $total_nodes"
    echo "依赖关系数: $total_edges"
    echo

    # 按状态统计
    echo "任务状态分布:"
    jq -r '.nodes | group_by(.status) | .[] | "\(.[0].status): \(length)"' "$DEPENDENCY_GRAPH_FILE"

    echo

    # 依赖复杂度统计
    echo "依赖复杂度:"
    local max_deps=$(jq '.nodes | to_entries | map(.value.dependencies | length) | max' "$DEPENDENCY_GRAPH_FILE")
    local avg_deps=$(jq '.nodes | to_entries | map(.value.dependencies | length) | add / length' "$DEPENDENCY_GRAPH_FILE")

    echo "最大依赖数: $max_deps"
    echo "平均依赖数: $avg_deps"
}

# 主函数
main() {
    case "${1:-}" in
        "init")
            init_dependency_graph
            ;;
        "add-node")
            if [[ $# -lt 3 ]]; then
                echo "用法: $0 add-node <task_id> <task_name> [priority]"
                exit 1
            fi
            add_task_node "$2" "$3" "${4:-5}"
            ;;
        "add-dep")
            if [[ $# -lt 3 ]]; then
                echo "用法: $0 add-dep <task_id> <dependency_id>"
                exit 1
            fi
            add_dependency "$2" "$3"
            ;;
        "check-ready")
            get_ready_tasks
            ;;
        "can-execute")
            if [[ $# -lt 2 ]]; then
                echo "用法: $0 can-execute <task_id>"
                exit 1
            fi
            if can_execute_task "$2"; then
                echo "可以执行"
                exit 0
            else
                echo "不能执行"
                exit 1
            fi
            ;;
        "update-status")
            if [[ $# -lt 3 ]]; then
                echo "用法: $0 update-status <task_id> <status>"
                exit 1
            fi
            update_task_status "$2" "$3"
            ;;
        "topo-sort")
            topological_sort
            ;;
        "visualize")
            visualize_dependency_graph "${2:-text}"
            ;;
        "stats")
            show_dependency_stats
            ;;
        "cleanup")
            cleanup_completed_dependencies "${2:-7}"
            ;;
        *)
            echo "用法: $0 {init|add-node|add-dep|check-ready|can-execute|update-status|topo-sort|visualize|stats|cleanup}"
            echo
            echo "命令说明:"
            echo "  init                                    - 初始化依赖图"
            echo "  add-node <task_id> <name> [priority]    - 添加任务节点"
            echo "  add-dep <task_id> <dependency_id>       - 添加依赖关系"
            echo "  check-ready                             - 获取就绪任务列表"
            echo "  can-execute <task_id>                   - 检查任务是否可执行"
            echo "  update-status <task_id> <status>        - 更新任务状态"
            echo "  topo-sort                               - 拓扑排序"
            echo "  visualize [format]                      - 可视化依赖图 (text/dot/json)"
            echo "  stats                                   - 显示依赖统计"
            echo "  cleanup [days]                          - 清理完成的依赖关系"
            exit 1
            ;;
    esac
}

# 如果直接执行脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi