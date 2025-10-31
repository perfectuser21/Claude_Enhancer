#!/usr/bin/env bash
# Parallel Task Generator for Subagents
# Version: 2.1.0 (Enhanced STAGES.yml parsing + Better error handling)
# Purpose: 读取STAGES.yml + Per-Phase Impact Assessment → 生成并行Task tool调用建议
# Usage: bash scripts/subagent/parallel_task_generator.sh <phase> <task_description>

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STAGES_FILE="${PROJECT_ROOT}/.workflow/STAGES.yml"
IMPACT_ASSESSOR="${PROJECT_ROOT}/.claude/scripts/impact_radius_assessor.sh"

# ========== 工具检查 ==========
check_dependencies() {
    local missing_tools=()

    # 检查Python3（必需）
    if ! command -v python3 &>/dev/null; then
        missing_tools+=("python3")
    fi

    # 检查yq（可选，有fallback）
    if ! command -v yq &>/dev/null; then
        echo "⚠️  Warning: yq not installed, using Python fallback for YAML parsing" >&2
    fi

    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        echo "❌ ERROR: Missing required tools: ${missing_tools[*]}" >&2
        echo "   Please install: sudo apt-get install ${missing_tools[*]}" >&2
        return 1
    fi

    return 0
}

# ========== 主函数 ==========
main() {
    local phase="${1:-Phase3}"
    local task_desc="${2:-General development task}"

    # 检查依赖
    if ! check_dependencies; then
        exit 1
    fi

    # 检查STAGES.yml存在
    if [[ ! -f "${STAGES_FILE}" ]]; then
        echo "❌ ERROR: STAGES.yml not found at: ${STAGES_FILE}" >&2
        echo "   Please ensure the file exists." >&2
        exit 1
    fi

    echo "# 🚀 Parallel Subagent Execution Plan"
    echo ""
    echo "**Phase**: ${phase}"
    echo "**Task**: ${task_desc}"
    echo ""

    # 1. 运行Per-Phase Impact Assessment
    echo "## Step 1: Per-Phase Impact Assessment"
    echo ""
    local assessment_result=""
    local recommended_agents="6"

    if [[ -f "${IMPACT_ASSESSOR}" ]]; then
        assessment_result=$(echo "${task_desc}" | bash "${IMPACT_ASSESSOR}" --phase "${phase}" --json 2>/dev/null || echo "{}")
        recommended_agents=$(echo "${assessment_result}" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('agent_strategy', {}).get('min_agents', 6))" 2>/dev/null || echo "6")
    else
        echo "⚠️  Warning: Impact assessor not found, using default: 6 agents" >&2
    fi

    echo "- Recommended agents: **${recommended_agents}**"
    echo ""

    # 2. 读取STAGES.yml获取该Phase的并行组
    echo "## Step 2: Read Parallel Groups from STAGES.yml"
    echo ""

    local parallel_groups=$(python3 <<EOF
import yaml
import json
import sys

try:
    with open("${STAGES_FILE}", 'r') as f:
        config = yaml.safe_load(f)

    # 尝试从parallel_groups字段读取（多Agent开发工作流）
    groups = config.get('parallel_groups', {}).get('${phase}', [])

    # 过滤出can_parallel=true的组
    parallel_groups = [g for g in groups if g.get('can_parallel', False)]

    if not parallel_groups:
        print("[]", file=sys.stderr)
        print("⚠️  No parallel groups found for ${phase}", file=sys.stderr)
    else:
        print(f"✓ Found {len(parallel_groups)} parallel groups", file=sys.stderr)

    print(json.dumps(parallel_groups, ensure_ascii=False))
except FileNotFoundError:
    print("[]")
    print("❌ ERROR: Cannot read ${STAGES_FILE}", file=sys.stderr)
except yaml.YAMLError as e:
    print("[]")
    print(f"❌ ERROR: Invalid YAML format: {e}", file=sys.stderr)
except Exception as e:
    print("[]")
    print(f"❌ ERROR: {e}", file=sys.stderr)
EOF
)

    if [[ "${parallel_groups}" == "[]" || -z "${parallel_groups}" ]]; then
        echo "⚠️ No parallel groups found for ${phase}"
        echo ""
        echo "**Recommendation**: Execute serially (no parallel needed)"
        exit 0
    fi

    # 3. 选择最佳agents组合（基于推荐数量）
    echo "## Step 3: Select Best Agent Combination"
    echo ""

    local selected_agents=$(python3 <<EOF
import json

groups = json.loads('''${parallel_groups}''')
task = "${task_desc}".lower()
recommended_count = int("${recommended_agents}")

# 关键词匹配
keyword_map = {
    'backend': ['impl-backend', 'skeleton-structure'],
    'frontend': ['impl-frontend'],
    'api': ['plan-technical', 'impl-backend'],
    'test': ['test-unit', 'test-integration', 'test-performance'],
    'database': ['impl-backend', 'skeleton-config'],
    'security': ['test-security', 'plan-quality'],
}

# 收集相关组
selected_groups = []
for keyword, group_ids in keyword_map.items():
    if keyword in task:
        for group in groups:
            if group['group_id'] in group_ids and group not in selected_groups:
                selected_groups.append(group)

# 如果没匹配到，使用前N个并行组
if not selected_groups:
    selected_groups = groups[:min(3, len(groups))]

# 从选中的组中提取agents
all_agents = []
for group in selected_groups:
    for agent in group.get('agents', []):
        if agent not in all_agents:
            all_agents.append({
                'agent': agent,
                'group_id': group['group_id'],
                'group_name': group.get('name', ''),
                'conflict_paths': group.get('conflict_paths', [])
            })

# 限制数量
selected = all_agents[:recommended_count]

print(json.dumps(selected, ensure_ascii=False, indent=2))
EOF
)

    echo "\`\`\`json"
    echo "${selected_agents}"
    echo "\`\`\`"
    echo ""

    # 4. 生成Task tool调用建议
    echo "## Step 4: Generated Task Tool Invocations"
    echo ""
    echo "**Copy and paste the following into your Claude Code message** (parallel execution):"
    echo ""
    echo "---"
    echo ""

    python3 <<EOF
import json
import sys

try:
    agents = json.loads('''${selected_agents}''')
except json.JSONDecodeError as e:
    print("❌ ERROR: Invalid JSON in selected agents", file=sys.stderr)
    print(f"   Details: {e}", file=sys.stderr)
    exit(1)

if not agents:
    print("❌ No agents selected")
    exit(0)

# 生成AI可直接复制的格式
for i, agent_info in enumerate(agents, 1):
    agent = agent_info['agent']
    group_name = agent_info['group_name']

    print(f"Task {i}/{len(agents)}: {agent} ({group_name})")
    print()
    print("\`\`\`")
    print("Task(")
    print(f"  subagent_type=\"{agent}\",")
    print(f"  description=\"{group_name} - Execute task\",")
    print(f"  prompt=\"\"\"")
    print(f"${task_desc}")
    print()
    print(f"Focus on: {group_name}")
    print("Coordinate with other agents through shared files.")
    print("Report your progress and any blockers.")
    print("  \"\"\"")
    print(")")
    print("\`\`\`")
    print()

print("---")
print()
print(f"**Summary**: {len(agents)} parallel Task tool calls")
print()
print("**Important**: Make all these Task() calls in a SINGLE message for true parallel execution!")
EOF

    echo ""
    echo "## Step 5: Conflict Detection"
    echo ""

    # 5. 冲突检测（跨组检测，同组agents可共享路径）
    local has_conflict=$(python3 <<EOF
import json

agents = json.loads('''${selected_agents}''')

# 按组分组agents
groups = {}
for agent_info in agents:
    group_id = agent_info['group_id']
    if group_id not in groups:
        groups[group_id] = []
    groups[group_id].append(agent_info)

# 跨组冲突检测（只检测不同组之间的冲突）
conflicts = []
group_ids = list(groups.keys())

for i, group1_id in enumerate(group_ids):
    for group2_id in group_ids[i+1:]:
        # 获取两组的conflict_paths
        paths1 = set()
        for agent in groups[group1_id]:
            paths1.update(agent.get('conflict_paths', []))

        paths2 = set()
        for agent in groups[group2_id]:
            paths2.update(agent.get('conflict_paths', []))

        # 检测重叠
        overlaps = paths1 & paths2
        if overlaps:
            conflicts.append({
                'group1': group1_id,
                'group2': group2_id,
                'paths': list(overlaps)
            })

if conflicts:
    print("⚠️ **Cross-group conflicts detected:**")
    for conflict in conflicts:
        print(f"- **{conflict['group1']}** vs **{conflict['group2']}**")
        print(f"  Shared paths: {', '.join(conflict['paths'][:3])}{'...' if len(conflict['paths']) > 3 else ''}")
    print()
    print("**Strategy**: Groups can execute in parallel IF they coordinate on shared paths")
    print("  OR execute groups sequentially (safer)")
else:
    print("✅ No cross-group conflicts - all groups can execute in parallel safely")
    print()
    print("**Note**: Agents within the same group share conflict_paths (expected behavior)")
EOF
)

    echo "${has_conflict}"
    echo ""

    echo "---"
    echo ""
    echo "## Step 6: Next Actions"
    echo ""
    echo "1. Review the generated Task() calls above"
    echo "2. Copy ALL Task() calls"
    echo "3. Paste them into Claude Code in a SINGLE message"
    echo "4. Monitor parallel execution progress"
    echo "5. Review conflict warnings if any"
    echo ""
    echo "**Pro Tip**: For maximum efficiency, ensure all agents execute truly in parallel!"
}

# ========== 帮助文档 ==========
show_help() {
    cat <<EOF
Parallel Task Generator for Subagents v2.1.0

用途：
  根据STAGES.yml配置和任务描述，智能生成并行Task tool调用建议

用法：
  $0 <phase> [task_description]

参数：
  phase              - Phase名称（如Phase1, Phase2, Phase3）
  task_description   - 任务描述（可选，默认为"General development task"）

示例：
  # 基础用法
  $0 Phase3

  # 带任务描述
  $0 Phase3 "Implement user authentication system"

  # Phase 2 实现阶段
  $0 Phase2 "Build backend API endpoints"

  # Phase 4 测试阶段
  $0 Phase4 "Run comprehensive test suite"

输出：
  - Step 1: 影响评估（推荐agent数量）
  - Step 2: 读取并行组配置
  - Step 3: 选择最佳agent组合
  - Step 4: 生成Task tool调用代码
  - Step 5: 冲突检测报告
  - Step 6: 后续操作指引

依赖：
  - python3（必需）- YAML解析和JSON处理
  - yq（可选）- 如无则使用Python fallback

配置文件：
  - .workflow/STAGES.yml - 并行组定义
  - .claude/scripts/impact_radius_assessor.sh - 影响评估脚本

更多信息：
  - 详细文档: docs/PARALLEL_SUBAGENT_STRATEGY.md
  - STAGES配置: .workflow/STAGES.yml
EOF
}

# ========== 入口点 ==========
if [[ $# -eq 0 ]] || [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    show_help
    exit 0
fi

main "$@"
