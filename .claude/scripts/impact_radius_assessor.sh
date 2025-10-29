#!/bin/bash
# Claude Enhancer - Impact Radius Assessment Tool
# 影响半径评估脚本 - 评估任务的风险、复杂度和影响面
# Version: 1.4.0 (Per-Phase Assessment Support)
# Author: Claude Enhancer DevOps Team

set -euo pipefail

# =============================================================================
# 配置常量
# =============================================================================

readonly VERSION="1.4.0"
readonly STAGES_YML="${STAGES_YML:-.workflow/STAGES.yml}"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly LOG_FILE="${LOG_FILE:-/tmp/impact_radius_assessor.log}"

# 评分权重配置 (PLAN.md v6.5.1 - Weighted Sum Formula)
# Formula: Radius = (Risk × 5) + (Complexity × 3) + (Scope × 2)
# Range: 0-60 points
readonly RISK_MULTIPLIER=5
readonly COMPLEXITY_MULTIPLIER=3
readonly SCOPE_MULTIPLIER=2

# Agent策略阈值 (v1.3 - 4-level system: 0/4/6/8 agents)
# Actual ranges: Low=15, Medium=45, High=70, Very-High=80+
readonly THRESHOLD_VERY_HIGH_RISK=70        # 70+分 → 8 agents (multiple CVEs, core engine)
readonly THRESHOLD_HIGH_RISK=50             # 50-69分 → 6 agents (single CVE, architecture)
readonly THRESHOLD_MEDIUM_RISK=30           # 30-49分 → 4 agents (bugs, optimization)
                                            # 0-29分 → 0 agents (docs, typos, formatting)

# 默认评分（未匹配任何模式时）
readonly DEFAULT_RISK=3
readonly DEFAULT_COMPLEXITY=4
readonly DEFAULT_SCOPE=4

# 性能优化：预编译正则表达式模式（通过数组）
declare -A RISK_PATTERNS=(
    [10]="cve|security|vulnerability|exploit|breach|攻击|漏洞|安全"
    [8]="migrate|migration|database.*change|architect|architecture|refactor.*system|refactor.*auth|distributed|phase|enforcement|mandatory|critical|迁移|架构|分布式|核心|强制|关键|重构.*系统|重构.*认证"
    [5]="small.*bug|minor.*bug|small.*fix|doc.*code|code.*example|example.*code|bug|fix|optimize|improve|修复|优化|改进"
    [2]="todo|spelling|cleanup|clean.*up|variable.*name|doc|typo|comment|rename|formatting|style|文档|注释|重命名|格式|样式|小错误"
)

declare -A COMPLEXITY_PATTERNS=(
    [10]="architecture|workflow|system.*design|全局架构|工作流|系统设计"
    [7]="hook|core|engine|framework|钩子|核心|引擎|框架"
    [4]="function|logic|algorithm|module|函数|逻辑|算法|模块"
    [1]="one.*line|single.*line|typo|readability|better.*name|variable.*name|单行|一行|可读性"
)

declare -A IMPACT_PATTERNS=(
    [10]="all|global|system.*wide|entire|全局|整个系统|所有"
    [7]="multiple|cross|several|many|多个|跨|若干"
    [4]="single|local|one|specific|单个|本地|特定"
    [1]="todo|spelling|cleanup|clean.*up|variable.*name|doc|documentation|readme|comment|typo|formatting|style.*guide|文档|注释|格式|样式"
)

# =============================================================================
# 工具函数
# =============================================================================

# 日志记录函数
log() {
    local level="$1"
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*" >> "$LOG_FILE"
}

# 错误处理
error_exit() {
    echo "ERROR: $1" >&2
    log "ERROR" "$1"
    exit "${2:-1}"
}

# 加载Phase-specific配置（从STAGES.yml）
# 参数: $1 = phase name (Phase2/Phase3/Phase4)
# 返回: 设置全局变量 PHASE_RISK_PATTERNS, PHASE_AGENT_STRATEGY
load_phase_config() {
    local phase="$1"

    # 检查STAGES.yml是否存在
    if [[ ! -f "$STAGES_YML" ]]; then
        log "WARN" "STAGES.yml not found at $STAGES_YML, using global mode"
        return 1
    fi

    # 使用Python解析YAML（如果可用）
    if command -v python3 &>/dev/null; then
        local config
        config=$(python3 <<EOF
import yaml
import json
import sys

try:
    with open("$STAGES_YML", 'r') as f:
        data = yaml.safe_load(f)

    phase_config = data.get('workflow_phase_parallel', {}).get('$phase', {})
    impact_config = phase_config.get('impact_assessment', {})

    if not impact_config.get('enabled', False):
        sys.exit(1)

    # 提取risk_patterns
    patterns = []
    for p in impact_config.get('risk_patterns', []):
        patterns.append({
            'pattern': p.get('pattern', ''),
            'risk': p.get('risk', 3),
            'complexity': p.get('complexity', 4),
            'scope': p.get('scope', 4)
        })

    # 提取agent_strategy
    strategy = impact_config.get('agent_strategy', {})

    print(json.dumps({
        'patterns': patterns,
        'strategy': strategy
    }))
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
EOF
)

        if [[ $? -eq 0 ]] && [[ -n "$config" ]]; then
            # 将配置存储到全局变量
            PHASE_CONFIG="$config"
            return 0
        fi
    fi

    log "WARN" "Failed to load phase config for $phase, using global mode"
    return 1
}

# 使用Phase-specific配置进行评估
# 参数: $1 = task_description, $2 = phase_config (JSON)
# 返回: risk, complexity, scope scores
assess_with_phase_config() {
    local task="$1"
    local config="$2"
    local task_lower
    task_lower=$(echo "$task" | tr '[:upper:]' '[:lower:]')

    local risk=0
    local complexity=0
    local scope=0
    local matched=false

    # 解析patterns并匹配
    local patterns_count
    patterns_count=$(echo "$config" | python3 -c "import json,sys; print(len(json.load(sys.stdin)['patterns']))")

    for ((i=0; i<patterns_count; i++)); do
        local pattern
        local p_risk
        local p_complexity
        local p_scope

        pattern=$(echo "$config" | python3 -c "import json,sys; print(json.load(sys.stdin)['patterns'][$i]['pattern'])")
        p_risk=$(echo "$config" | python3 -c "import json,sys; print(json.load(sys.stdin)['patterns'][$i]['risk'])")
        p_complexity=$(echo "$config" | python3 -c "import json,sys; print(json.load(sys.stdin)['patterns'][$i]['complexity'])")
        p_scope=$(echo "$config" | python3 -c "import json,sys; print(json.load(sys.stdin)['patterns'][$i]['scope'])")

        if echo "$task_lower" | grep -qiE "$pattern"; then
            risk=$p_risk
            complexity=$p_complexity
            scope=$p_scope
            matched=true
            break
        fi
    done

    # 如果没有匹配，使用默认值
    if [[ "$matched" == "false" ]]; then
        risk=$DEFAULT_RISK
        complexity=$DEFAULT_COMPLEXITY
        scope=$DEFAULT_SCOPE
    fi

    echo "$risk $complexity $scope"
}

# 显示帮助信息
show_help() {
    cat <<EOF
$SCRIPT_NAME v$VERSION - 影响半径评估工具

用法:
    $SCRIPT_NAME [OPTIONS] [TASK_DESCRIPTION]
    echo "task description" | $SCRIPT_NAME

选项:
    -h, --help              显示帮助信息
    -v, --version           显示版本号
    -j, --json              输出JSON格式（默认）
    -p, --pretty            美化输出
    -d, --debug             启用调试模式
    --phase PHASE           使用Phase-specific评估（Phase2/Phase3/Phase4）
    --performance           显示性能统计

示例:
    # 通过参数传入（全局评估）
    $SCRIPT_NAME "Fix security vulnerability in auth module"

    # Per-phase评估
    $SCRIPT_NAME --phase Phase2 "implement user authentication"
    $SCRIPT_NAME --phase Phase3 "test security vulnerabilities"
    $SCRIPT_NAME --phase Phase4 "review authentication code"

    # 通过管道传入
    echo "Refactor global architecture" | $SCRIPT_NAME

    # 美化输出
    $SCRIPT_NAME --pretty "Implement new payment gateway"

评分标准:
    风险评分 (0-10):
        10: 安全漏洞、CVE
        8:  核心功能、强制规则
        5:  Bug修复、优化
        2:  文档、注释
        默认: 3 (未知风险)

    复杂度评分 (0-10):
        10: 架构设计、工作流
        7:  Hook、核心模块
        4:  函数、逻辑
        1:  单行改动
        默认: 4 (标准复杂度)

    影响面评分 (0-10):
        10: 全局、系统级
        7:  多模块、跨功能
        4:  单一模块
        1:  仅文档
        默认: 4 (单模块影响)

Agent策略:
    影响半径 ≥ 7.5: MANDATORY (最少6个Agent)
    影响半径 ≥ 5.0: RECOMMENDED (最少4个Agent)
    影响半径 ≥ 3.0: OPTIONAL (最少3个Agent)
    影响半径 < 3.0: SINGLE (可用1个Agent)

EOF
}

# =============================================================================
# 核心评估函数
# =============================================================================

# 评估风险分数
assess_risk_score() {
    local task="$1"
    local task_lower
    task_lower=$(echo "$task" | tr '[:upper:]' '[:lower:]')

    local max_score=0
    local matched_pattern=""

    # 正确的优先级：高风险优先，让混合任务（如"Fix typo and CVE"）正确分类
    # 检查顺序：[10] Critical → [8] High → [2] Low → [5] Medium
    for score in 10 8 2 5; do
        local pattern="${RISK_PATTERNS[$score]}"
        if echo "$task_lower" | grep -qE "$pattern"; then
            max_score=$score
            matched_pattern="$pattern"
            break  # 使用第一个匹配的模式（最高优先级）
        fi
    done

    # 如果没有匹配，使用默认值
    if [[ $max_score -eq 0 ]]; then
        max_score=$DEFAULT_RISK
        matched_pattern="default"
    fi

    log "DEBUG" "Risk assessment: score=$max_score, pattern=$matched_pattern"
    echo "$max_score"
}

# 评估复杂度分数
assess_complexity_score() {
    local task="$1"
    local task_lower
    task_lower=$(echo "$task" | tr '[:upper:]' '[:lower:]')

    local max_score=0
    local matched_pattern=""

    # 遍历复杂度模式（从高到低）
    for score in 10 7 4 1; do
        local pattern="${COMPLEXITY_PATTERNS[$score]}"
        if echo "$task_lower" | grep -qE "$pattern"; then
            max_score=$score
            matched_pattern="$pattern"
            break
        fi
    done

    # 额外检测：多个关键词组合增加复杂度
    local keyword_count
    keyword_count=$(echo "$task_lower" | grep -oE "refactor|migrate|integrate|redesign" | wc -l)
    if [[ $keyword_count -ge 2 ]] && [[ $max_score -lt 7 ]]; then
        max_score=7
        matched_pattern="multiple_complex_keywords"
    fi

    # 如果没有匹配，使用默认值
    if [[ $max_score -eq 0 ]]; then
        max_score=$DEFAULT_COMPLEXITY
        matched_pattern="default"
    fi

    log "DEBUG" "Complexity assessment: score=$max_score, pattern=$matched_pattern"
    echo "$max_score"
}

# 评估影响面分数
assess_impact_score() {
    local task="$1"
    local task_lower
    task_lower=$(echo "$task" | tr '[:upper:]' '[:lower:]')

    local max_score=0
    local matched_pattern=""

    # 正确的优先级：高影响优先
    # 检查顺序：[10] System-wide → [7] Multiple → [1] Doc-only → [4] Single
    for score in 10 7 1 4; do
        local pattern="${IMPACT_PATTERNS[$score]}"
        if echo "$task_lower" | grep -qE "$pattern"; then
            max_score=$score
            matched_pattern="$pattern"
            break  # 使用第一个匹配的模式（最高优先级）
        fi
    done

    # 如果没有匹配，使用默认值
    if [[ $max_score -eq 0 ]]; then
        max_score=$DEFAULT_SCOPE
        matched_pattern="default"
    fi

    log "DEBUG" "Impact assessment: score=$max_score, pattern=$matched_pattern"
    echo "$max_score"
}

# 计算影响半径（加权求和 - PLAN.md v6.5.1 Formula）
# Formula: Radius = (Risk × 5) + (Complexity × 3) + (Scope × 2)
# Range: 0-60 points
# Rationale:
#   - Risk × 5: Security/stability is highest priority
#   - Complexity × 3: Complex code needs more review
#   - Scope × 2: Wide impact needs more testing
calculate_impact_radius() {
    local risk="$1"
    local complexity="$2"
    local scope="$3"

    # Direct weighted sum (integer arithmetic, no bc needed)
    local radius
    radius=$(( (risk * RISK_MULTIPLIER) + (complexity * COMPLEXITY_MULTIPLIER) + (scope * SCOPE_MULTIPLIER) ))

    log "INFO" "Impact radius calculated: $radius = (${risk}×5) + (${complexity}×3) + (${scope}×2)"
    echo "$radius"
}

# 确定Agent策略 (v1.3 - 4-level system)
# Radius Scale: 0-100 points
# Agent Mapping:
#   70-100 → 8 agents (very-high-risk: multiple CVEs, core engine)
#   50-69  → 6 agents (high-risk: single CVE, architecture)
#   30-49  → 4 agents (medium-risk: bugs, optimization)
#   0-29   → 0 agents (low-risk: docs, typos, formatting)
determine_agent_strategy() {
    local radius="$1"

    # 4-level system based on actual score ranges
    if [ $radius -ge $THRESHOLD_VERY_HIGH_RISK ]; then
        echo "very-high-risk"  # 70+ points: multiple CVEs, core engine, critical architecture
    elif [ $radius -ge $THRESHOLD_HIGH_RISK ]; then
        echo "high-risk"       # 50-69 points: single CVE, new features, security patches
    elif [ $radius -ge $THRESHOLD_MEDIUM_RISK ]; then
        echo "medium-risk"     # 30-49 points: bugs, optimization, refactoring
    else
        echo "low-risk"        # 0-29 points: docs, typos, formatting, comments
    fi
}

# 确定最少Agent数量 (v1.3 - 4-level mapping: 0/4/6/8)
determine_min_agents() {
    local strategy="$1"

    case "$strategy" in
        very-high-risk)
            echo "8"    # Very high-risk: multiple CVEs, core engine, critical architecture
            ;;
        high-risk)
            echo "6"    # High-risk tasks: single CVE, new features, security patches
            ;;
        medium-risk)
            echo "4"    # Medium tasks: bugs, optimization, refactoring
            ;;
        low-risk)
            echo "0"    # Low-risk tasks: docs, typos, formatting
            ;;
        *)
            echo "4"    # Default fallback (conservative)
            ;;
    esac
}

# 生成推理解释
generate_reasoning() {
    local risk="$1"
    local complexity="$2"
    local impact="$3"
    local strategy="$4"

    local risk_level complexity_level impact_level

    # 分类风险等级
    if [[ $risk -ge 8 ]]; then
        risk_level="HIGH"
    elif [[ $risk -ge 5 ]]; then
        risk_level="MEDIUM"
    else
        risk_level="LOW"
    fi

    # 分类复杂度等级
    if [[ $complexity -ge 7 ]]; then
        complexity_level="HIGH"
    elif [[ $complexity -ge 4 ]]; then
        complexity_level="MEDIUM"
    else
        complexity_level="LOW"
    fi

    # 分类影响面等级
    if [[ $impact -ge 7 ]]; then
        impact_level="WIDE"
    elif [[ $impact -ge 4 ]]; then
        impact_level="MODERATE"
    else
        impact_level="NARROW"
    fi

    cat <<EOF
{
    "risk_level": "$risk_level",
    "complexity_level": "$complexity_level",
    "impact_level": "$impact_level",
    "recommendation": "$(get_strategy_recommendation "$strategy")",
    "risk_factors": $(get_risk_factors "$risk"),
    "complexity_factors": $(get_complexity_factors "$complexity"),
    "impact_factors": $(get_impact_factors "$impact")
}
EOF
}

# 获取策略推荐 (PLAN.md v6.5.1)
get_strategy_recommendation() {
    local strategy="$1"

    case "$strategy" in
        high-risk)
            echo "High-risk task requiring comprehensive review (6 specialized agents)"
            ;;
        medium-risk)
            echo "Medium-risk task requiring focused review (3 specialized agents)"
            ;;
        low-risk)
            echo "Low-risk task suitable for autonomous execution (no agents required)"
            ;;
        *)
            echo "Task with standard risk level (3 specialized agents)"
            ;;
    esac
}

# 获取风险因素
get_risk_factors() {
    local risk="$1"

    if [[ $risk -ge 8 ]]; then
        echo '["security_critical", "requires_expert_review", "high_impact_on_users"]'
    elif [[ $risk -ge 5 ]]; then
        echo '["bug_fix", "requires_testing", "moderate_user_impact"]'
    else
        echo '["low_risk", "minimal_user_impact", "cosmetic_changes"]'
    fi
}

# 获取复杂度因素
get_complexity_factors() {
    local complexity="$1"

    if [[ $complexity -ge 7 ]]; then
        echo '["architectural_changes", "multiple_components", "requires_design_review"]'
    elif [[ $complexity -ge 4 ]]; then
        echo '["logic_changes", "single_component", "standard_complexity"]'
    else
        echo '["trivial_changes", "minimal_logic", "straightforward"]'
    fi
}

# 获取影响面因素
get_impact_factors() {
    local impact="$1"

    if [[ $impact -ge 7 ]]; then
        echo '["system_wide", "affects_multiple_modules", "cross_cutting_concern"]'
    elif [[ $impact -ge 4 ]]; then
        echo '["module_specific", "contained_changes", "limited_scope"]'
    else
        echo '["isolated_changes", "single_file", "no_dependencies"]'
    fi
}

# =============================================================================
# 输出函数
# =============================================================================

# 生成JSON输出
generate_json_output() {
    local task="$1"
    local risk="$2"
    local complexity="$3"
    local impact="$4"
    local radius="$5"
    local strategy="$6"
    local min_agents="$7"
    local pretty="${8:-false}"
    local phase="${9:-}"

    local reasoning
    reasoning=$(generate_reasoning "$risk" "$complexity" "$impact" "$strategy")

    # 构建JSON (根据是否有phase字段选择不同模板)
    local json
    if [[ -n "$phase" ]]; then
        json=$(cat <<EOF
{
    "version": "$VERSION",
    "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
    "phase": "$phase",
    "task_description": $(echo "$task" | jq -Rs .),
    "scores": {
        "risk_score": $risk,
        "complexity_score": $complexity,
        "impact_score": $impact,
        "impact_radius": $radius
    },
    "multipliers": {
        "risk_multiplier": $RISK_MULTIPLIER,
        "complexity_multiplier": $COMPLEXITY_MULTIPLIER,
        "scope_multiplier": $SCOPE_MULTIPLIER
    },
    "agent_strategy": {
        "strategy": "$strategy",
        "min_agents": $min_agents,
        "thresholds": {
            "high_risk": $THRESHOLD_HIGH_RISK,
            "medium_risk": $THRESHOLD_MEDIUM_RISK
        }
    },
    "reasoning": $reasoning
}
EOF
)
    else
        json=$(cat <<EOF
{
    "version": "$VERSION",
    "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
    "task_description": $(echo "$task" | jq -Rs .),
    "scores": {
        "risk_score": $risk,
        "complexity_score": $complexity,
        "impact_score": $impact,
        "impact_radius": $radius
    },
    "multipliers": {
        "risk_multiplier": $RISK_MULTIPLIER,
        "complexity_multiplier": $COMPLEXITY_MULTIPLIER,
        "scope_multiplier": $SCOPE_MULTIPLIER
    },
    "agent_strategy": {
        "strategy": "$strategy",
        "min_agents": $min_agents,
        "thresholds": {
            "high_risk": $THRESHOLD_HIGH_RISK,
            "medium_risk": $THRESHOLD_MEDIUM_RISK
        }
    },
    "reasoning": $reasoning
}
EOF
)
    fi

    if [[ "$pretty" == "true" ]]; then
        echo "$json" | jq .
    else
        echo "$json" | jq -c .
    fi
}

# 美化输出
generate_pretty_output() {
    local task="$1"
    local risk="$2"
    local complexity="$3"
    local impact="$4"
    local radius="$5"
    local strategy="$6"
    local min_agents="$7"

    cat <<EOF

╔════════════════════════════════════════════════════════════════╗
║          Impact Radius Assessment Report v$VERSION              ║
╚════════════════════════════════════════════════════════════════╝

📝 Task Description:
   $(echo "$task" | fold -w 60 | sed 's/^/   /')

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Assessment Scores:

   Risk Score:        [$risk/10]  $(get_score_bar "$risk")
   Complexity Score:  [$complexity/10]  $(get_score_bar "$complexity")
   Impact Score:      [$impact/10]  $(get_score_bar "$impact")

   ┌──────────────────────────────────────────────────┐
   │  Impact Radius: $radius/10                        │
   └──────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 Agent Strategy: $strategy

   Minimum Agents Required: $min_agents

   $(get_strategy_description "$strategy")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Recommendation:
   $(get_strategy_recommendation "$strategy" | fold -w 60 | sed 's/^/   /')

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF
}

# 获取分数条形图
get_score_bar() {
    local score="$1"
    local filled=$((score))
    local empty=$((10 - filled))

    printf "["
    printf '█%.0s' $(seq 1 $filled)
    printf '░%.0s' $(seq 1 $empty)
    printf "]"
}

# 获取策略描述 (Simplified 3-level system)
get_strategy_description() {
    local strategy="$1"

    case "$strategy" in
        high-risk)
            echo "   ⚠️  HIGH RISK: Critical task requiring"
            echo "   comprehensive review by 6 specialized agents."
            ;;
        medium-risk)
            echo "   ⚡ MEDIUM RISK: Standard task requiring"
            echo "   focused review by 3 specialized agents."
            ;;
        low-risk)
            echo "   ✓  LOW RISK: Low-impact task suitable for"
            echo "   autonomous execution (no agents required)."
            ;;
        *)
            echo "   ○  STANDARD: Default task level"
            echo "   (3 specialized agents)."
            ;;
    esac
}

# =============================================================================
# 主函数
# =============================================================================

main() {
    local task_description=""
    local output_format="json"
    local pretty_print="false"
    local debug_mode="false"
    local show_performance="false"
    local phase_name=""
    local use_phase_config="false"
    local start_time
    start_time=$(date +%s%N)

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--version)
                echo "$SCRIPT_NAME version $VERSION"
                exit 0
                ;;
            -j|--json)
                output_format="json"
                shift
                ;;
            -p|--pretty)
                pretty_print="true"
                shift
                ;;
            -d|--debug)
                debug_mode="true"
                set -x
                shift
                ;;
            --phase)
                phase_name="$2"
                use_phase_config="true"
                shift 2
                ;;
            --performance)
                show_performance="true"
                shift
                ;;
            -*)
                error_exit "Unknown option: $1"
                ;;
            *)
                task_description="$1"
                shift
                ;;
        esac
    done

    # 如果没有通过参数提供任务描述，尝试从stdin读取
    if [[ -z "$task_description" ]]; then
        if [[ -p /dev/stdin ]] || [[ ! -t 0 ]]; then
            task_description=$(cat)
        else
            error_exit "No task description provided. Use -h for help."
        fi
    fi

    # 验证输入
    if [[ -z "$task_description" ]]; then
        error_exit "Task description cannot be empty"
    fi

    log "INFO" "Starting assessment for task: ${task_description:0:100}"

    # 执行评估
    local risk_score complexity_score impact_score impact_radius agent_strategy min_agents

    # Per-phase评估模式
    if [[ "$use_phase_config" == "true" ]] && [[ -n "$phase_name" ]]; then
        log "INFO" "Using per-phase assessment for $phase_name"

        # 加载Phase配置
        if load_phase_config "$phase_name"; then
            # 使用Phase-specific配置评估
            local scores
            scores=$(assess_with_phase_config "$task_description" "$PHASE_CONFIG")
            read -r risk_score complexity_score impact_score <<< "$scores"

            # 计算影响半径
            impact_radius=$(calculate_impact_radius "$risk_score" "$complexity_score" "$impact_score")

            # 使用Phase-specific agent策略
            local strategy_json
            strategy_json=$(echo "$PHASE_CONFIG" | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin)['strategy']))")

            # 根据risk_score确定agent数量
            if [[ $risk_score -ge 8 ]]; then
                min_agents=$(echo "$strategy_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('very_high_risk', 4))")
                agent_strategy="very-high-risk"
            elif [[ $risk_score -ge 6 ]]; then
                min_agents=$(echo "$strategy_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('high_risk', 3))")
                agent_strategy="high-risk"
            elif [[ $risk_score -ge 4 ]]; then
                min_agents=$(echo "$strategy_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('medium_risk', 2))")
                agent_strategy="medium-risk"
            else
                min_agents=$(echo "$strategy_json" | python3 -c "import json,sys; print(json.load(sys.stdin).get('low_risk', 1))")
                agent_strategy="low-risk"
            fi

            log "INFO" "Per-phase assessment: phase=$phase_name, risk=$risk_score, agents=$min_agents"
        else
            # Fallback到全局模式
            log "WARN" "Failed to load phase config, using global mode"
            risk_score=$(assess_risk_score "$task_description")
            complexity_score=$(assess_complexity_score "$task_description")
            impact_score=$(assess_impact_score "$task_description")
            impact_radius=$(calculate_impact_radius "$risk_score" "$complexity_score" "$impact_score")
            agent_strategy=$(determine_agent_strategy "$impact_radius")
            min_agents=$(determine_min_agents "$agent_strategy")
        fi
    else
        # 全局评估模式（向后兼容）
        log "INFO" "Using global assessment mode"
        risk_score=$(assess_risk_score "$task_description")
        complexity_score=$(assess_complexity_score "$task_description")
        impact_score=$(assess_impact_score "$task_description")
        impact_radius=$(calculate_impact_radius "$risk_score" "$complexity_score" "$impact_score")
        agent_strategy=$(determine_agent_strategy "$impact_radius")
        min_agents=$(determine_min_agents "$agent_strategy")
    fi

    # 生成输出
    if [[ "$pretty_print" == "true" ]]; then
        generate_pretty_output "$task_description" "$risk_score" "$complexity_score" \
            "$impact_score" "$impact_radius" "$agent_strategy" "$min_agents"
    else
        generate_json_output "$task_description" "$risk_score" "$complexity_score" \
            "$impact_score" "$impact_radius" "$agent_strategy" "$min_agents" "false" "$phase_name"
    fi

    # 性能统计
    if [[ "$show_performance" == "true" ]]; then
        local end_time
        end_time=$(date +%s%N)
        local elapsed_ms=$(( (end_time - start_time) / 1000000 ))
        echo "" >&2
        echo "⏱️  Performance: ${elapsed_ms}ms" >&2
    fi

    log "INFO" "Assessment completed: strategy=$agent_strategy, radius=$impact_radius"

    exit 0
}

# =============================================================================
# 执行主函数
# =============================================================================

main "$@"
