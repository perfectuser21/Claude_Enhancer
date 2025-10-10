#!/bin/bash
# plan_renderer.sh - 执行计划可视化脚本
# Purpose: 修复CE-ISSUE-004 - 生成Mermaid执行计划图（dry-run可视化）
# Version: 1.0.0
# Created: 2025-10-09

set -euo pipefail

# 颜色定义
readonly CYAN='\033[0;36m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

# 路径定义
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly MANIFEST="${PROJECT_ROOT}/.workflow/manifest.yml"
readonly STAGES="${PROJECT_ROOT}/.workflow/STAGES.yml"

# ==================== 主逻辑 ====================

main() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  Claude Enhancer 工作流执行计划${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # 检查文件存在性
    if [[ ! -f "$MANIFEST" ]]; then
        echo "❌ ERROR: manifest.yml 不存在: $MANIFEST"
        exit 1
    fi

    if [[ ! -f "$STAGES" ]]; then
        echo "⚠️  WARNING: STAGES.yml 不存在，跳过并行组信息"
        STAGES=""
    fi

    # 生成Mermaid流程图
    generate_mermaid_diagram

    echo ""

    # 生成文本执行顺序
    generate_text_plan

    echo ""

    # 生成并行组详情（如果STAGES存在）
    if [[ -n "$STAGES" && -f "$STAGES" ]]; then
        generate_parallel_groups
    fi

    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}执行计划生成完成！${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ==================== Mermaid图生成 ====================

generate_mermaid_diagram() {
    echo "## 工作流可视化（Mermaid）"
    echo ""
    echo '```mermaid'
    echo "graph TD"
    echo ""

    # 使用Python解析manifest.yml生成节点
    python3 << 'EOF'
import yaml
import sys

try:
    with open('.workflow/manifest.yml', 'r') as f:
        data = yaml.safe_load(f)

    phases = data.get('phases', [])

    # 生成节点
    print("  %% Phase节点定义")
    for phase in phases:
        phase_id = phase['id']
        phase_name = phase['name']
        phase_desc = phase.get('description', '')
        is_parallel = phase.get('parallel', False)

        # 根据是否并行使用不同样式
        if is_parallel:
            print(f"  {phase_id}[\"{phase_id}: {phase_name}<br/>(可并行)\"]")
        else:
            print(f"  {phase_id}[\"{phase_id}: {phase_name}\"]")

    print("")
    print("  %% 依赖关系箭头")

    # 生成依赖关系
    for phase in phases:
        phase_id = phase['id']
        depends_on = phase.get('depends_on', [])

        for dep in depends_on:
            print(f"  {dep} --> {phase_id}")

    print("")
    print("  %% 样式定义")

    # 标注并行节点
    for phase in phases:
        phase_id = phase['id']
        is_parallel = phase.get('parallel', False)
        allow_failure = phase.get('allow_failure', False)

        if is_parallel:
            print(f"  style {phase_id} fill:#90EE90,stroke:#006400,stroke-width:3px")
        elif allow_failure:
            print(f"  style {phase_id} fill:#FFD700,stroke:#FF8C00")
        else:
            print(f"  style {phase_id} fill:#87CEEB,stroke:#4682B4")

    # 添加图例
    print("")
    print("  %% 图例")
    print("  legend[\"图例:<br/>🟢 绿色=可并行<br/>🔵 蓝色=串行<br/>🟡 黄色=允许失败\"]")
    print("  style legend fill:#F0F0F0,stroke:#999,stroke-dasharray: 5 5")

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
EOF

    echo '```'
}

# ==================== 文本执行顺序 ====================

generate_text_plan() {
    echo "## 执行顺序详情"
    echo ""

    python3 << 'EOF'
import yaml
import sys

try:
    with open('.workflow/manifest.yml', 'r') as f:
        data = yaml.safe_load(f)

    phases = data.get('phases', [])

    for i, phase in enumerate(phases, 1):
        phase_id = phase['id']
        phase_name = phase['name']
        phase_desc = phase.get('description', '')
        is_parallel = phase.get('parallel', False)
        timeout = phase.get('timeout', 0)
        retry = phase.get('retry', 0)
        max_agents = phase.get('max_parallel_agents', 0)

        parallel_text = "可并行" if is_parallel else "串行"

        print(f"{i}. **{phase_id} - {phase_name}** ({parallel_text})")
        print(f"   - 描述: {phase_desc}")
        print(f"   - 超时: {timeout}秒 (~{timeout//60}分钟)")

        if retry > 0:
            print(f"   - 重试次数: {retry}")

        if is_parallel and max_agents > 0:
            print(f"   - 最大并行Agent: {max_agents}")

        depends_on = phase.get('depends_on', [])
        if depends_on:
            print(f"   - 依赖: {', '.join(depends_on)}")

        print("")

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
EOF
}

# ==================== 并行组详情 ====================

generate_parallel_groups() {
    echo "## 并行组配置详情"
    echo ""
    echo -e "${YELLOW}（来自 STAGES.yml）${NC}"
    echo ""

    python3 << 'EOF'
import yaml
import sys

try:
    with open('.workflow/STAGES.yml', 'r') as f:
        data = yaml.safe_load(f)

    parallel_groups = data.get('parallel_groups', {})

    for phase, groups in parallel_groups.items():
        print(f"### {phase} 并行组:")
        print("")

        if not groups:
            print("  _无并行组定义_")
            print("")
            continue

        for group in groups:
            group_id = group.get('group_id', 'unknown')
            group_name = group.get('name', 'Unknown')
            agents = group.get('agents', [])
            can_parallel = group.get('can_parallel', False)
            max_concurrent = group.get('max_concurrent', 1)

            parallel_status = "✅ 可并行" if can_parallel else "⚠️ 串行"

            print(f"- **{group_id}** - {group_name} ({parallel_status})")
            print(f"  - Agents ({len(agents)}): {', '.join(agents)}")
            print(f"  - 最大并发: {max_concurrent}")
            print("")

except Exception as e:
    print(f"Error parsing STAGES.yml: {e}", file=sys.stderr)
    # 不退出，继续执行
EOF

    echo ""
    echo "### 冲突检测规则"
    echo ""

    python3 << 'EOF'
import yaml
import sys

try:
    with open('.workflow/STAGES.yml', 'r') as f:
        data = yaml.safe_load(f)

    conflict_detection = data.get('conflict_detection', {})
    rules = conflict_detection.get('rules', [])

    if not rules:
        print("  _无冲突检测规则_")
    else:
        for rule in rules:
            name = rule.get('name', 'unknown')
            description = rule.get('description', '')
            action = rule.get('action', 'unknown')
            severity = rule.get('severity', 'UNKNOWN')

            severity_emoji = {
                'FATAL': '🔴',
                'ERROR': '🟠',
                'MAJOR': '🟡',
                'WARNING': '🟢'
            }.get(severity, '⚪')

            print(f"- {severity_emoji} **{name}** ({severity})")
            print(f"  - 描述: {description}")
            print(f"  - 动作: {action}")
            print("")

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
EOF
}

# 执行主函数
main "$@"
