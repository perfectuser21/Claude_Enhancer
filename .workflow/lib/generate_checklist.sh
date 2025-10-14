#!/bin/bash
# Checklist生成器
# 根据需求对话生成验收清单

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
WORKFLOW_DIR="$PROJECT_ROOT/.workflow"
REQUIREMENTS_FILE="$WORKFLOW_DIR/REQUIREMENTS_DIALOGUE.md"
CHECKLIST_FILE="$WORKFLOW_DIR/CHECKLIST.md"

# 颜色定义
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() {
    echo -e "${CYAN}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*"
}

generate_checklist() {
    local feature_name="${1:-未命名功能}"

    log_info "开始生成验收清单..."

    # 检查需求对话文件是否存在
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        echo "错误：需求对话文件不存在：$REQUIREMENTS_FILE"
        echo "请先完成需求澄清阶段"
        exit 1
    fi

    # 生成Checklist
    cat > "$CHECKLIST_FILE" <<EOF
# ${feature_name} 验收清单

**生成时间**: $(date '+%Y-%m-%d %H:%M:%S')
**基于对话**: .workflow/REQUIREMENTS_DIALOGUE.md
**功能名称**: ${feature_name}

═══════════════════════════════════════════════════════════════

## 📋 功能验收清单

$(extract_functional_checklist)

═══════════════════════════════════════════════════════════════

## 🔍 质量保证清单

### 代码质量
[ ] 代码构建通过（无编译错误）
[ ] 无明显代码坏味道
[ ] 代码符合项目规范
[ ] 无未使用的导入和变量

### 测试覆盖
[ ] 测试覆盖率 ≥ 60%
[ ] 所有单元测试通过
[ ] 关键功能有测试用例
[ ] 边界情况有测试

### 性能
[ ] 无明显性能问题
[ ] 关键操作响应时间 < 500ms
[ ] 无内存泄漏
[ ] 无阻塞主线程的操作

### 安全
[ ] 无明显安全漏洞
[ ] 敏感信息已加密
[ ] 输入已验证
[ ] 无SQL注入风险

═══════════════════════════════════════════════════════════════

**总计**: $(count_checklist_items)项验收标准

**状态**: ⏳ 等待验证

═══════════════════════════════════════════════════════════════

**验证说明**：
- P7阶段会自动验证这个清单的每一项
- 所有项目通过后，会生成验收报告
- 您确认后，即可merge到main分支

═══════════════════════════════════════════════════════════════
EOF

    log_success "验收清单已生成: $CHECKLIST_FILE"

    # 显示统计
    local total_items=$(count_checklist_items)
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 Checklist统计"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  功能验收项: $(grep -c '^\[ \] [0-9]' "$CHECKLIST_FILE" || echo 0)个"
    echo "  质量保证项: $(grep -c '^\[ \] [^0-9]' "$CHECKLIST_FILE" || echo 0)个"
    echo "  总计: ${total_items}个"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

extract_functional_checklist() {
    # 从需求对话中提取功能清单
    # 这个函数会被AI在实际使用时自定义填充

    # 示例结构（AI会根据实际需求对话生成）
    cat <<'ITEMS'
### 1. 核心功能
[ ] 1.1 功能点1（从需求对话中提取）
[ ] 1.2 功能点2
[ ] 1.3 功能点3

### 2. 用户交互
[ ] 2.1 交互点1
[ ] 2.2 交互点2

### 3. 特殊情况处理
[ ] 3.1 边界情况1
[ ] 3.2 边界情况2

### 4. 安全规则
[ ] 4.1 安全规则1
[ ] 4.2 安全规则2
ITEMS
}

count_checklist_items() {
    if [[ -f "$CHECKLIST_FILE" ]]; then
        grep -c '^\[ \]' "$CHECKLIST_FILE" || echo 0
    else
        echo 0
    fi
}

# 保存功能名称供后续使用
save_feature_name() {
    local feature_name="${1:-}"
    echo "$feature_name" > "$WORKFLOW_DIR/FEATURE_NAME.txt"
}

# 主函数
main() {
    local feature_name="${1:-}"

    if [[ -z "$feature_name" ]]; then
        # 尝试从需求文件中提取
        if [[ -f "$REQUIREMENTS_FILE" ]]; then
            feature_name=$(head -n 1 "$REQUIREMENTS_FILE" | sed 's/^# *//' | sed 's/ *$//')
        fi

        if [[ -z "$feature_name" ]]; then
            feature_name="未命名功能"
        fi
    fi

    save_feature_name "$feature_name"
    generate_checklist "$feature_name"
}

# 如果直接执行脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
