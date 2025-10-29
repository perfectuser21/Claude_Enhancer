#!/usr/bin/env bash
# Parallel Task Generator for Subagents
# Version: 2.0.0 (Per-Phase Assessment Support)
# Purpose: 读取STAGES.yml + Per-Phase Impact Assessment → 生成并行Task tool调用建议
# Usage: bash scripts/subagent/parallel_task_generator.sh <phase> <task_description>

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STAGES_FILE="${PROJECT_ROOT}/.workflow/STAGES.yml"
IMPACT_ASSESSOR="${PROJECT_ROOT}/.claude/scripts/impact_radius_assessor.sh"

# ========== 主函数 ==========
main() {
    local phase="${1:-Phase3}"
    local task_desc="${2:-General development task}"

    echo "# 🚀 Parallel Subagent Execution Plan"
    echo ""
    echo "**Phase**: ${phase}"
    echo "**Task**: ${task_desc}"
    echo ""

    # 1. 运行Per-Phase Impact Assessment
    echo "## Step 1: Per-Phase Impact Assessment"
    echo ""
    local assessment_result=$(echo "${task_desc}" | bash "${IMPACT_ASSESSOR}" --phase "${phase}" --json 2>/dev/null || echo "{}")
    local recommended_agents=$(echo "${assessment_result}" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('agent_strategy', {}).get('min_agents', 6))" 2>/dev/null || echo "6")

    echo "- Recommended agents: **${recommended_agents}**"
    echo ""

    # 2. 读取STAGES.yml获取该Phase的并行组
    echo "## Step 2: Read Parallel Groups from STAGES.yml"
    echo ""

    local parallel_groups=$(python3 <<EOF
import yaml
import json

try:
    with open("${STAGES_FILE}", 'r') as f:
        config = yaml.safe_load(f)

    groups = config.get('parallel_groups', {}).get('${phase}', [])

    # 过滤出can_parallel=true的组
    parallel_groups = [g for g in groups if g.get('can_parallel', False)]

    print(json.dumps(parallel_groups, ensure_ascii=False))
except Exception as e:
    print("[]")
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
    echo "**You should make the following Task tool calls in a SINGLE message** (parallel execution):"
    echo ""

    python3 <<EOF
import json

agents = json.loads('''${selected_agents}''')

if not agents:
    print("❌ No agents selected")
    exit(0)

print("\`\`\`")
for i, agent_info in enumerate(agents, 1):
    agent = agent_info['agent']
    group_name = agent_info['group_name']

    print(f"# Task {i}: {agent}")
    print(f"Task(")
    print(f"  subagent_type=\"{agent}\",")
    print(f"  description=\"{group_name} - Execute task\",")
    print(f"  prompt=\"\"\"")
    print(f"  ${task_desc}")
    print(f"  ")
    print(f"  Focus on your expertise area ({group_name}).")
    print(f"  Coordinate with other agents through shared files.")
    print(f"  \"\"\"")
    print(f")")
    print()

print("\`\`\`")
print()
print(f"**Total**: {len(agents)} parallel subagent calls")
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
    echo "**Next Action**: Copy the Task tool invocations above and execute them in parallel."
}

main "$@"
