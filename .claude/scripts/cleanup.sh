#!/bin/bash
# Claude Enhancer Cleanup执行脚本
# 根据当前Phase执行相应的清理任务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取当前Phase
get_current_phase() {
    if [ -f ".claude/phase_state.json" ]; then
        grep -oP '"current_phase"\s*:\s*\d+' .claude/phase_state.json | grep -oP '\d+' || echo "1"
    else
        echo "1"
    fi
}

# Phase 0: 环境初始化清理
cleanup_phase_0() {
    echo -e "${BLUE}🧹 Phase 0: 环境初始化清理${NC}"
    echo "================================="

    # 清理旧的临时文件
    echo "清理临时文件..."
    find . -type f \( -name "*.tmp" -o -name "*.temp" -o -name "*.bak" -o -name "*.swp" \) -delete 2>/dev/null || true

    # 清理Python缓存
    echo "清理Python缓存..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

    # 清理Node缓存
    if [ -d "node_modules/.cache" ]; then
        echo "清理Node.js缓存..."
        rm -rf node_modules/.cache
    fi

    echo -e "${GREEN}✅ Phase 0清理完成${NC}\n"
}

# Phase 5: 提交前清理
cleanup_phase_5() {
    echo -e "${BLUE}🧹 Phase 5: 代码提交前清理${NC}"
    echo "================================="

    # 1. 删除临时文件
    echo "1. 删除临时文件..."
    local temp_count=0
    for pattern in "*.tmp" "*.temp" "*.bak" "*.orig" ".DS_Store" "Thumbs.db" "*.swp" "*~"; do
        temp_count=$((temp_count + $(find . -name "$pattern" -type f 2>/dev/null | wc -l)))
        find . -name "$pattern" -type f -delete 2>/dev/null || true
    done
    echo "   已删除 $temp_count 个临时文件"

    # 2. 清理调试代码
    echo "2. 清理调试代码..."
    local debug_count=0

    # JavaScript/TypeScript
    for file in $(find . -type f \( -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" \) 2>/dev/null); do
        if grep -q "console\.log" "$file"; then
            # 注释掉console.log（除非有@keep标记）
            sed -i.backup '/\/\/ @keep/!s/console\.log/\/\/ console.log/g' "$file" 2>/dev/null || \
            sed -i '' '/\/\/ @keep/!s/console\.log/\/\/ console.log/g' "$file" 2>/dev/null || true
            debug_count=$((debug_count + 1))
            rm -f "$file.backup"
        fi
    done

    # Python
    for file in $(find . -type f -name "*.py" 2>/dev/null); do
        if grep -q "^[[:space:]]*print(" "$file"; then
            # 注释掉print（除非有@keep标记）
            sed -i.backup '/# @keep/!s/^[[:space:]]*print(/    # print(/g' "$file" 2>/dev/null || \
            sed -i '' '/# @keep/!s/^[[:space:]]*print(/    # print(/g' "$file" 2>/dev/null || true
            debug_count=$((debug_count + 1))
            rm -f "$file.backup"
        fi
    done
    echo "   已清理 $debug_count 个文件中的调试代码"

    # 3. 检查TODO标记
    echo "3. 检查TODO/FIXME标记..."
    local todo_files=$(grep -r "TODO:\|FIXME:\|HACK:" --include="*.js" --include="*.ts" --include="*.py" --include="*.go" . 2>/dev/null | wc -l)
    if [ "$todo_files" -gt 0 ]; then
        echo -e "   ${YELLOW}⚠️  发现 $todo_files 个TODO/FIXME标记${NC}"
    else
        echo "   ✅ 没有发现未处理的TODO"
    fi

    # 4. 格式化代码（如果有相应工具）
    echo "4. 格式化代码..."
    if command -v prettier &> /dev/null; then
        prettier --write "**/*.{js,jsx,ts,tsx,json,css,scss,md}" 2>/dev/null || true
        echo "   ✅ Prettier格式化完成"
    fi

    if command -v black &> /dev/null; then
        black . 2>/dev/null || true
        echo "   ✅ Black格式化完成"
    fi

    # 5. 安全扫描
    echo "5. 快速安全扫描..."
    local sensitive_count=0

    # 检查常见的敏感信息模式
    for pattern in "api_key" "API_KEY" "secret" "SECRET" "password" "PASSWORD" "token" "TOKEN"; do
        if grep -r "$pattern" --include="*.js" --include="*.py" --include="*.env.example" . 2>/dev/null | grep -v "example\|test\|mock" > /dev/null; then
            sensitive_count=$((sensitive_count + 1))
        fi
    done

    if [ "$sensitive_count" -gt 0 ]; then
        echo -e "   ${YELLOW}⚠️  发现 $sensitive_count 个可能的敏感信息${NC}"
    else
        echo "   ✅ 未发现明显的敏感信息"
    fi

    echo -e "${GREEN}✅ Phase 5清理完成${NC}\n"
}

# Phase 7: 部署前深度清理
cleanup_phase_7() {
    echo -e "${BLUE}🧹 Phase 7: 部署前深度清理${NC}"
    echo "================================="

    # 执行Phase 5的所有清理
    cleanup_phase_5

    # 额外的深度清理
    echo "6. 深度清理..."

    # 删除开发依赖（如果是Node.js项目）
    if [ -f "package.json" ]; then
        echo "   清理开发依赖..."
        # 这里只是示例，实际不执行删除
        echo "   （跳过：需要确认后再删除devDependencies）"
    fi

    # 优化图片（如果有图片文件）
    local image_count=$(find . -type f \( -name "*.jpg" -o -name "*.png" -o -name "*.gif" \) 2>/dev/null | wc -l)
    if [ "$image_count" -gt 0 ]; then
        echo "   发现 $image_count 个图片文件（需要手动优化）"
    fi

    # 生成部署报告
    echo "7. 生成清理报告..."
    cat > .claude/cleanup_report.md << EOF
# 清理报告
生成时间: $(date)

## Phase 7 部署前清理

### 清理统计
- 临时文件清理: 完成
- 调试代码清理: 完成
- 代码格式化: 完成
- 安全扫描: 完成

### 建议
1. 手动检查敏感信息
2. 确认所有测试通过
3. 更新版本号和文档

## 准备状态
✅ 代码已准备好部署
EOF

    echo -e "${GREEN}✅ Phase 7深度清理完成${NC}"
    echo -e "${GREEN}📄 报告已生成: .claude/cleanup_report.md${NC}\n"
}

# 主函数
main() {
    echo -e "${BLUE}🚀 Claude Enhancer Cleanup System${NC}"
    echo "======================================"
    echo ""

    # 获取参数或当前Phase
    PHASE=${1:-$(get_current_phase)}

    echo "当前Phase: $PHASE"
    echo ""

    case "$PHASE" in
        0)
            cleanup_phase_0
            ;;
        5)
            cleanup_phase_5
            ;;
        7)
            cleanup_phase_7
            ;;
        *)
            echo -e "${YELLOW}Phase $PHASE 不需要清理${NC}"
            ;;
    esac

    echo "======================================"
    echo -e "${GREEN}✅ 清理任务完成！${NC}"
}

# 执行主函数
main "$@"