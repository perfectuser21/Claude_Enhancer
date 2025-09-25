#!/bin/bash
# Claude Enhancer快速文档加载器
# 根据简单参数快速确定需要加载哪些文档

set -e

CLAUDE_DIR="/home/xx/dev/Claude_Enhancer/.claude"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 帮助信息
show_help() {
    echo -e "${BLUE}Claude Enhancer智能文档加载器${NC}"
    echo ""
    echo "用法: $0 [选项] \"任务描述\""
    echo ""
    echo "选项:"
    echo "  -p, --phase PHASE        当前Phase (0-7)"
    echo "  -c, --complexity LEVEL   复杂度 (simple|standard|complex)"
    echo "  -t, --tech STACK         技术栈 (python|react|vue|golang|etc)"
    echo "  -m, --max-tokens NUM     最大Token数 (默认30000)"
    echo "  -v, --verbose           显示详细信息"
    echo "  -d, --dry-run           仅显示加载计划，不实际加载"
    echo "  -h, --help              显示此帮助"
    echo ""
    echo "示例:"
    echo "  $0 \"修复用户登录bug\""
    echo "  $0 -p 3 -t react \"添加用户仪表板\""
    echo "  $0 -c complex \"重构系统架构\""
    echo ""
}

# 默认参数
PHASE=0
COMPLEXITY="standard"
TECH_STACK=""
MAX_TOKENS=30000
VERBOSE=false
DRY_RUN=false
TASK_DESC=""

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--phase)
            PHASE="$2"
            shift 2
            ;;
        -c|--complexity)
            COMPLEXITY="$2"
            shift 2
            ;;
        -t|--tech)
            TECH_STACK="$2"
            shift 2
            ;;
        -m|--max-tokens)
            MAX_TOKENS="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            echo -e "${RED}未知选项: $1${NC}"
            show_help
            exit 1
            ;;
        *)
            TASK_DESC="$1"
            shift
            ;;
    esac
done

# 检查任务描述
if [[ -z "$TASK_DESC" ]]; then
    echo -e "${RED}错误: 请提供任务描述${NC}"
    show_help
    exit 1
fi

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 智能分析任务
analyze_task() {
    local task="$1"
    local task_lower=$(echo "$task" | tr '[:upper:]' '[:lower:]')

    # 任务类型分析
    local task_type="通用开发"
    if [[ "$task_lower" =~ (修复|fix|bug|问题|错误) ]]; then
        task_type="Bug修复"
        COMPLEXITY="simple"
    elif [[ "$task_lower" =~ (新功能|添加|实现|开发|创建) ]]; then
        task_type="新功能开发"
    elif [[ "$task_lower" =~ (重构|优化|改进|重写) ]]; then
        task_type="重构优化"
    elif [[ "$task_lower" =~ (架构|设计|分层|模块) ]]; then
        task_type="架构设计"
        COMPLEXITY="complex"
    elif [[ "$task_lower" =~ (测试|test) ]]; then
        task_type="测试相关"
    elif [[ "$task_lower" =~ (安全|权限|认证|加密) ]]; then
        task_type="安全审计"
    elif [[ "$task_lower" =~ (性能|缓存|慢查询) ]]; then
        task_type="性能优化"
    fi

    # 技术栈检测（如果未指定）
    if [[ -z "$TECH_STACK" ]]; then
        if [[ "$task_lower" =~ (react|jsx) ]]; then
            TECH_STACK="react"
        elif [[ "$task_lower" =~ (vue|vuex) ]]; then
            TECH_STACK="vue"
        elif [[ "$task_lower" =~ (python|django|flask) ]]; then
            TECH_STACK="python"
        elif [[ "$task_lower" =~ (golang|go) ]]; then
            TECH_STACK="golang"
        elif [[ "$task_lower" =~ (数据库|database|sql) ]]; then
            TECH_STACK="database"
        fi
    fi

    echo "$task_type"
}

# 确定需要加载的文档
determine_documents() {
    local task_type="$1"
    local documents=()

    # P0 - 总是加载的核心文档
    documents+=("WORKFLOW.md")
    documents+=("AGENT_STRATEGY.md")
    documents+=("SAFETY_RULES.md")

    # P1 - 高频文档 (Phase >= 1)
    if [[ $PHASE -ge 1 ]]; then
        documents+=("PHASE_AGENT_STRATEGY.md")
        documents+=("SELF_CHECK_MECHANISM.md")
        documents+=("OUTPUT_CONTROL_STRATEGY.md")
    fi

    # P2 - 条件加载
    case "$task_type" in
        "新功能开发"|"架构设计"|"重构优化")
            documents+=("ARCHITECTURE/GROWTH-STRATEGY.md")
            documents+=("ARCHITECTURE/LAYER-DEFINITION.md")
            if [[ "$task_type" == "架构设计" ]]; then
                documents+=("ARCHITECTURE/v2.0-FOUNDATION.md")
                documents+=("ARCHITECTURE/NAMING-CONVENTIONS.md")
            fi
            ;;
        "Bug修复")
            documents+=("ISSUES_AND_SOLUTIONS.md")
            ;;
        "安全审计")
            documents+=("agents/security-auditor.md")
            ;;
    esac

    # 技术栈特定文档
    case "$TECH_STACK" in
        "react")
            documents+=("agents/frontend-engineer.md")
            documents+=("agents/react-pro.md")
            ;;
        "vue")
            documents+=("agents/frontend-engineer.md")
            documents+=("agents/vue-specialist.md")
            ;;
        "python")
            documents+=("agents/backend-engineer.md")
            documents+=("agents/python-pro.md")
            ;;
        "golang")
            documents+=("agents/backend-engineer.md")
            documents+=("agents/golang-pro.md")
            ;;
        "database")
            documents+=("agents/database-specialist.md")
            ;;
    esac

    # Phase特定文档
    if [[ $PHASE -eq 3 ]]; then
        documents+=("agents/test-engineer.md")
    fi

    if [[ $PHASE -eq 0 || $PHASE -eq 5 || $PHASE -eq 7 ]]; then
        if [[ "$COMPLEXITY" == "complex" ]]; then
            documents+=("CLEANUP_STRATEGY.md")
        fi
    fi

    # 去重并返回
    printf '%s\n' "${documents[@]}" | sort -u
}

# 估算Token使用
estimate_tokens() {
    local documents=("$@")
    local total_tokens=0

    # 文档大小估算 (Token数)
    declare -A doc_sizes=(
        ["WORKFLOW.md"]=2000
        ["AGENT_STRATEGY.md"]=1500
        ["SAFETY_RULES.md"]=1200
        ["PHASE_AGENT_STRATEGY.md"]=1800
        ["SELF_CHECK_MECHANISM.md"]=1000
        ["OUTPUT_CONTROL_STRATEGY.md"]=800
        ["ARCHITECTURE/v2.0-FOUNDATION.md"]=3000
        ["ARCHITECTURE/LAYER-DEFINITION.md"]=2500
        ["ARCHITECTURE/GROWTH-STRATEGY.md"]=2000
        ["ARCHITECTURE/NAMING-CONVENTIONS.md"]=1500
        ["ISSUES_AND_SOLUTIONS.md"]=1800
        ["CLEANUP_STRATEGY.md"]=1200
    )

    # Agent文档通常较小
    for doc in "${documents[@]}"; do
        if [[ "$doc" =~ ^agents/ ]]; then
            total_tokens=$((total_tokens + 800))
        else
            local size=${doc_sizes[$doc]:-1000}
            total_tokens=$((total_tokens + size))
        fi
    done

    echo $total_tokens
}

# 检查文档是否存在
check_documents_exist() {
    local documents=("$@")
    local missing_docs=()

    for doc in "${documents[@]}"; do
        if [[ ! -f "$CLAUDE_DIR/$doc" ]]; then
            missing_docs+=("$doc")
        fi
    done

    if [[ ${#missing_docs[@]} -gt 0 ]]; then
        log_warning "以下文档不存在:"
        printf '  - %s\n' "${missing_docs[@]}"
    fi
}

# 主要执行逻辑
main() {
    log_info "分析任务: \"$TASK_DESC\""

    # 任务分析
    local task_type=$(analyze_task "$TASK_DESC")

    if [[ "$VERBOSE" == true ]]; then
        echo ""
        echo -e "${BLUE}=== 任务分析结果 ===${NC}"
        echo "任务类型: $task_type"
        echo "复杂度: $COMPLEXITY"
        echo "当前Phase: $PHASE"
        echo "技术栈: ${TECH_STACK:-'未检测到'}"
        echo "最大Token: $MAX_TOKENS"
    fi

    # 确定文档列表
    log_info "确定需要加载的文档..."
    local documents
    readarray -t documents < <(determine_documents "$task_type")

    # 估算Token使用
    local estimated_tokens=$(estimate_tokens "${documents[@]}")

    # 检查Token限制
    if [[ $estimated_tokens -gt $MAX_TOKENS ]]; then
        log_warning "预估Token ($estimated_tokens) 超过限制 ($MAX_TOKENS)"
        log_info "建议减少复杂度或增加Token限制"
    fi

    # 显示加载计划
    echo ""
    echo -e "${BLUE}=== 文档加载计划 ===${NC}"
    echo "任务类型: $task_type"
    echo "Agent策略: ${COMPLEXITY} ($(case $COMPLEXITY in simple) echo "4个Agent" ;; standard) echo "6个Agent" ;; complex) echo "8个Agent" ;; esac))"
    echo "预估Token: $estimated_tokens / $MAX_TOKENS"
    echo "文档数量: ${#documents[@]}"

    if [[ "$VERBOSE" == true ]]; then
        echo ""
        echo "文档列表:"
        printf '  ✓ %s\n' "${documents[@]}"

        # 检查文档存在性
        check_documents_exist "${documents[@]}"
    fi

    # 如果是dry-run，到此结束
    if [[ "$DRY_RUN" == true ]]; then
        log_info "Dry-run模式，不执行实际加载"
        return 0
    fi

    # 实际加载文档（这里可以调用Python脚本或其他处理）
    echo ""
    log_info "执行文档加载..."

    # 这里可以集成实际的文档加载逻辑
    # 例如调用Python脚本或直接处理

    log_success "文档加载计划已生成"

    # 输出建议的下一步操作
    echo ""
    echo -e "${BLUE}=== 建议的下一步操作 ===${NC}"
    case "$task_type" in
        "Bug修复")
            echo "1. 重现问题和错误"
            echo "2. 分析错误日志"
            echo "3. 定位问题代码"
            echo "4. 修复并测试"
            ;;
        "新功能开发")
            echo "1. 确认功能需求"
            echo "2. 设计API和数据结构"
            echo "3. 选择合适的技术栈"
            echo "4. 开始编码实现"
            ;;
        "架构设计")
            echo "1. 分析现有架构"
            echo "2. 确定改进目标"
            echo "3. 设计新的架构方案"
            echo "4. 制定迁移计划"
            ;;
        *)
            echo "1. 详细分析任务需求"
            echo "2. 制定实施计划"
            echo "3. 选择合适的Agent"
            echo "4. 开始执行开发"
            ;;
    esac
}

# 执行主逻辑
main "$@"