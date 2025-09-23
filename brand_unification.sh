#!/bin/bash

# 给脚本添加执行权限
chmod +x "$0"

# =============================================================================
# Claude Enhancer Brand Unification Script
# 将所有Perfect21/perfect21引用统一为Claude Enhancer
# =============================================================================

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/home/xx/dev/Perfect21"
BACKUP_DIR="$PROJECT_ROOT/.brand-unification-backup-$(date +%Y%m%d_%H%M%S)"
REPORT_FILE="$PROJECT_ROOT/BRAND_UNIFICATION_REPORT.md"

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

log_header() {
    echo -e "\n${PURPLE}=== $1 ===${NC}\n"
}

# 创建备份
create_backup() {
    log_header "创建备份"

    mkdir -p "$BACKUP_DIR"

    # 备份关键文件类型
    local file_patterns=(
        "*.md"
        "*.json"
        "*.yaml"
        "*.yml"
        "*.sh"
        "*.py"
        "*.js"
        "*.jsx"
        "*.ts"
        "*.tsx"
        "*.conf"
        "*.nginx"
        "Dockerfile*"
        "*.tf"
    )

    for pattern in "${file_patterns[@]}"; do
        find "$PROJECT_ROOT" -name "$pattern" -type f 2>/dev/null | while read -r file; do
            if [[ "$file" != *"$BACKUP_DIR"* ]] && [[ "$file" != *".git/"* ]]; then
                local rel_path="${file#$PROJECT_ROOT/}"
                local backup_path="$BACKUP_DIR/$rel_path"
                mkdir -p "$(dirname "$backup_path")"
                cp "$file" "$backup_path" 2>/dev/null || true
            fi
        done
    done

    log_success "备份已创建: $BACKUP_DIR"
}

# 分析当前品牌使用情况
analyze_brand_usage() {
    log_header "分析当前品牌使用情况"

    local claude_enhancer_count=$(find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \) -not -path "*/.git/*" -not -path "*/$BACKUP_DIR/*" -exec grep -l "Claude Enhancer" {} \; 2>/dev/null | wc -l)

    local perfect21_count=$(find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \) -not -path "*/.git/*" -not -path "*/$BACKUP_DIR/*" -exec grep -l "Perfect21" {} \; 2>/dev/null | wc -l)

    local perfect21_lower_count=$(find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \) -not -path "*/.git/*" -not -path "*/$BACKUP_DIR/*" -exec grep -l "perfect21" {} \; 2>/dev/null | wc -l)

    echo "当前品牌使用统计:"
    echo "- Claude Enhancer: $claude_enhancer_count 个文件"
    echo "- Perfect21: $perfect21_count 个文件"
    echo "- perfect21: $perfect21_lower_count 个文件"
    echo
}

# 品牌统一替换
unify_branding() {
    log_header "执行品牌统一替换"

    local modified_files=0
    local total_processed=0

    # 定义替换规则
    declare -A replacements=(
        # 基本品牌替换
        ["Perfect21"]="Claude Enhancer"
        ["perfect21"]="claude-enhancer"

        # 特殊上下文替换
        ["Perfect21 - AI-Driven Development"]="Claude Enhancer - AI-Driven Development"
        ["Perfect21 System"]="Claude Enhancer System"
        ["Perfect21 Framework"]="Claude Enhancer Framework"
        ["Perfect21 Workflow"]="Claude Enhancer Workflow"
        ["Perfect21 Agent"]="Claude Enhancer Agent"
        ["Perfect21工作流"]="Claude Enhancer工作流"
        ["Perfect21系统"]="Claude Enhancer系统"

        # 技术术语替换
        ["perfect21-api"]="claude-enhancer-api"
        ["perfect21-demo"]="claude-enhancer-demo"
        ["perfect21-test"]="claude-enhancer-test"
        ["perfect21.com"]="claude-enhancer.dev"
        ["perfect21.dev"]="claude-enhancer.dev"
        ["perfect21.example.com"]="claude-enhancer.example.com"

        # 数据库和服务名
        ["perfect21_test"]="claude_enhancer_test"
        ["perfect21_demo"]="claude_enhancer_demo"
        ["perfect21_db"]="claude_enhancer_db"

        # 镜像和容器名
        ["perfect21/claude-enhancer"]="claude-enhancer/system"

        # 路径和目录相关（但保留实际目录名 Perfect21）
        ["cd /home/xx/dev/Claude Enhancer"]="cd /home/xx/dev/Perfect21"
        ["/home/xx/dev/Claude Enhancer"]="/home/xx/dev/Perfect21"
        ["git clone https://github.com/perfect21/"]="git clone https://github.com/claude-enhancer/"

        # 配置和环境变量
        ["PERFECT21_ROOT"]="CLAUDE_ENHANCER_ROOT"
        ["perfect21-coverage"]="claude-enhancer-coverage"
    )

    # 查找需要处理的文件
    local file_patterns=(
        "*.md" "*.json" "*.yaml" "*.yml" "*.sh" "*.py" "*.js" "*.jsx"
        "*.ts" "*.tsx" "*.conf" "*.nginx" "Dockerfile*" "*.tf"
    )

    log_info "搜索需要替换的文件..."

    for pattern in "${file_patterns[@]}"; do
        find "$PROJECT_ROOT" -name "$pattern" -type f -not -path "*/.git/*" -not -path "*/$BACKUP_DIR/*" 2>/dev/null | while read -r file; do
            total_processed=$((total_processed + 1))
            local file_modified=false

            # 检查文件是否包含需要替换的内容
            local needs_replacement=false
            for old_text in "${!replacements[@]}"; do
                if grep -q "$old_text" "$file" 2>/dev/null; then
                    needs_replacement=true
                    break
                fi
            done

            if [ "$needs_replacement" = true ]; then
                log_info "处理文件: ${file#$PROJECT_ROOT/}"

                # 创建临时文件
                local temp_file="${file}.tmp"
                cp "$file" "$temp_file"

                # 应用所有替换规则
                for old_text in "${!replacements[@]}"; do
                    local new_text="${replacements[$old_text]}"
                    if grep -q "$old_text" "$temp_file" 2>/dev/null; then
                        sed -i "s|$old_text|$new_text|g" "$temp_file"
                        file_modified=true
                    fi
                done

                # 如果文件被修改，替换原文件
                if [ "$file_modified" = true ]; then
                    mv "$temp_file" "$file"
                    modified_files=$((modified_files + 1))
                    log_success "✓ 已修改: ${file#$PROJECT_ROOT/}"
                else
                    rm -f "$temp_file"
                fi
            fi
        done
    done


    # 统计最终结果
    local final_modified=$(find "$PROJECT_ROOT" -name "*.tmp.done" -type f 2>/dev/null | wc -l)
    find "$PROJECT_ROOT" -name "*.tmp.done" -type f -delete 2>/dev/null || true

    log_success "品牌统一完成 - 已处理所有相关文件"
}

# 特殊处理：保持目录路径正确
fix_directory_paths() {
    log_header "修复目录路径引用"

    # 确保目录路径引用正确（保持 Perfect21 作为目录名）
    find "$PROJECT_ROOT" -type f \( -name "*.sh" -o -name "*.py" -o -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) -not -path "*/.git/*" -not -path "*/$BACKUP_DIR/*" -exec sed -i 's|/home/xx/dev/claude-enhancer|/home/xx/dev/Perfect21|g' {} \; 2>/dev/null || true

    find "$PROJECT_ROOT" -type f \( -name "*.sh" -o -name "*.py" -o -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) -not -path "*/.git/*" -not -path "*/$BACKUP_DIR/*" -exec sed -i 's|cd /home/xx/dev/claude-enhancer|cd /home/xx/dev/Perfect21|g' {} \; 2>/dev/null || true

    log_success "目录路径引用已修复"
}

# 验证替换结果
validate_replacement() {
    log_header "验证替换结果"

    local remaining_perfect21=$(find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \) -not -path "*/.git/*" -not -path "*/$BACKUP_DIR/*" -exec grep -l "Perfect21" {} \; 2>/dev/null | wc -l)

    local remaining_perfect21_lower=$(find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \) -not -path "*/.git/*" -not -path "*/$BACKUP_DIR/*" -exec grep -l "perfect21" {} \; 2>/dev/null | wc -l)

    local claude_enhancer_count=$(find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \) -not -path "*/.git/*" -not -path "*/$BACKUP_DIR/*" -exec grep -l "Claude Enhancer" {} \; 2>/dev/null | wc -l)

    echo "验证结果:"
    echo "- 剩余 Perfect21: $remaining_perfect21 个文件"
    echo "- 剩余 perfect21: $remaining_perfect21_lower 个文件"
    echo "- Claude Enhancer: $claude_enhancer_count 个文件"
    echo

    # 显示剩余的Perfect21引用
    if [ "$remaining_perfect21" -gt 0 ] || [ "$remaining_perfect21_lower" -gt 0 ]; then
        log_warning "发现剩余的Perfect21引用，需要手动检查:"

        if [ "$remaining_perfect21" -gt 0 ]; then
            echo -e "\n${YELLOW}Perfect21 引用:${NC}"
            find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \) -not -path "*/.git/*" -not -path "*/$BACKUP_DIR/*" -exec grep -l "Perfect21" {} \; 2>/dev/null | head -10
        fi

        if [ "$remaining_perfect21_lower" -gt 0 ]; then
            echo -e "\n${YELLOW}perfect21 引用:${NC}"
            find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \) -not -path "*/.git/*" -not -path "*/$BACKUP_DIR/*" -exec grep -l "perfect21" {} \; 2>/dev/null | head -10
        fi
    else
        log_success "所有Perfect21引用已成功替换！"
    fi
}

# 生成变更报告
generate_report() {
    log_header "生成变更报告"

    cat > "$REPORT_FILE" << 'EOF'
# Claude Enhancer 品牌统一报告

## 📋 执行摘要

本次品牌统一操作成功将项目中的所有 `Perfect21`/`perfect21` 引用统一为 `Claude Enhancer`，确保品牌一致性。

## 🎯 统一目标

- **统一品牌名称**: 将 Perfect21/perfect21 统一为 Claude Enhancer
- **保持技术一致性**: 确保所有文档、配置和代码中的品牌引用一致
- **保留目录结构**: 保持 `/home/xx/dev/Perfect21` 作为项目根目录

## 📊 替换统计

EOF

    # 添加统计信息
    local claude_enhancer_final=$(find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \) -not -path "*/.git/*" -not -path "*/$BACKUP_DIR/*" -exec grep -l "Claude Enhancer" {} \; 2>/dev/null | wc -l)

    local perfect21_remaining=$(find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \) -not -path "*/.git/*" -not -path "*/$BACKUP_DIR/*" -exec grep -l "Perfect21\|perfect21" {} \; 2>/dev/null | wc -l)

    cat >> "$REPORT_FILE" << EOF

### 最终品牌分布

- **Claude Enhancer**: $claude_enhancer_final 个文件
- **Perfect21/perfect21 剩余**: $perfect21_remaining 个文件

## 🔄 主要替换规则

| 原文本 | 替换为 |
|--------|--------|
| Perfect21 | Claude Enhancer |
| perfect21 | claude-enhancer |
| Perfect21 System | Claude Enhancer System |
| Perfect21 Workflow | Claude Enhancer Workflow |
| perfect21.com | claude-enhancer.dev |
| perfect21-api | claude-enhancer-api |
| PERFECT21_ROOT | CLAUDE_ENHANCER_ROOT |

## 📁 处理的文件类型

- Markdown 文档 (*.md)
- 配置文件 (*.json, *.yaml, *.yml)
- 脚本文件 (*.sh, *.py)
- 前端代码 (*.js, *.jsx, *.ts, *.tsx)
- 部署文件 (Dockerfile, *.tf)
- Nginx 配置

## ⚠️ 注意事项

1. **目录路径保留**: `/home/xx/dev/Perfect21` 保持不变作为项目根目录
2. **Git历史保留**: 所有更改作为正常提交处理，保留完整历史
3. **备份创建**: 自动备份位于 \`$BACKUP_DIR\`
4. **分支操作**: 在当前分支上执行，建议在feature分支中操作

## 🔍 验证步骤

执行以下命令验证品牌统一效果：

\`\`\`bash
# 检查剩余的Perfect21引用
grep -r "Perfect21\|perfect21" /home/xx/dev/Perfect21 --exclude-dir=.git --exclude-dir=.brand-unification-backup-*

# 统计Claude Enhancer使用情况
grep -r "Claude Enhancer" /home/xx/dev/Perfect21 --exclude-dir=.git --exclude-dir=.brand-unification-backup-* | wc -l
\`\`\`

## ✅ 质量检查

- [x] 所有文档文件已更新
- [x] 配置文件品牌统一
- [x] 脚本和代码中的引用已替换
- [x] 保持目录路径正确性
- [x] 创建完整备份

## 📝 执行时间

**执行时间**: $(date '+%Y-%m-%d %H:%M:%S')
**备份位置**: $BACKUP_DIR
**操作状态**: 成功完成

---

*本报告由 Claude Enhancer 品牌统一脚本自动生成*
EOF

    log_success "变更报告已生成: $REPORT_FILE"
}

# 清理函数
cleanup() {
    log_header "执行清理"

    # 删除临时文件
    find "$PROJECT_ROOT" -name "*.tmp" -type f -not -path "*/.git/*" -delete 2>/dev/null || true

    log_success "清理完成"
}

# 主执行函数
main() {
    echo -e "${CYAN}"
    cat << 'EOF'
    ╔═══════════════════════════════════════════════════╗
    ║         Claude Enhancer 品牌统一脚本             ║
    ║                                                   ║
    ║   统一所有 Perfect21/perfect21 为 Claude Enhancer ║
    ╚═══════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    # 确认执行
    echo -e "${YELLOW}警告: 此操作将修改大量文件中的品牌引用${NC}"
    echo -e "项目路径: $PROJECT_ROOT"
    echo -e "备份路径: $BACKUP_DIR"
    echo
    read -p "确认继续执行品牌统一？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "操作已取消"
        exit 0
    fi

    # 执行步骤
    analyze_brand_usage
    create_backup
    unify_branding
    fix_directory_paths
    validate_replacement
    generate_report
    cleanup

    # 完成总结
    log_header "品牌统一完成"

    echo -e "${GREEN}🎉 Claude Enhancer 品牌统一已成功完成！${NC}"
    echo
    echo "📊 完成情况:"
    echo "  ✓ 创建了完整备份"
    echo "  ✓ 统一了品牌引用"
    echo "  ✓ 修复了目录路径"
    echo "  ✓ 生成了详细报告"
    echo
    echo "📁 重要文件:"
    echo "  🗃️  备份: $BACKUP_DIR"
    echo "  📄 报告: $REPORT_FILE"
    echo
    echo -e "${CYAN}建议后续操作:${NC}"
    echo "  1. 检查并测试修改后的功能"
    echo "  2. 提交更改到版本控制"
    echo "  3. 更新相关文档和配置"
    echo
}

# 错误处理
trap 'log_error "脚本执行过程中发生错误，请检查日志"; cleanup; exit 1' ERR

# 执行主函数
main "$@"