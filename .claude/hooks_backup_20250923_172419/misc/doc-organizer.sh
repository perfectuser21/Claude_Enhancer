#!/bin/bash
# Document Organizer - 自动整理项目文档

PROJECT_ROOT="${CLAUDE_ENHANCER_HOME:-$(pwd)}"
DOCS_DIR="$PROJECT_ROOT/docs"
DATE=$(date +%Y-%m-%d)

# 创建文档目录结构
setup_docs_structure() {
    mkdir -p "$DOCS_DIR"/{architecture,api,guides,testing,decisions,archive}

    # 创建.gitignore防止临时文件提交
    cat > "$DOCS_DIR/.gitignore" << EOF
*.tmp
*.log
.DS_Store
archive/*.old
EOF
}

# 移动并组织现有文档
organize_existing_docs() {
    echo "📁 Organizing documents..."

    # 架构文档
    if [ -f "$PROJECT_ROOT/ARCHITECTURE_ANALYSIS.md" ]; then
        mv "$PROJECT_ROOT/ARCHITECTURE_ANALYSIS.md" "$DOCS_DIR/architecture/$DATE-architecture-analysis.md" 2>/dev/null
        echo "  ✓ Moved architecture analysis"
    fi

    # 测试报告
    for report in "$PROJECT_ROOT"/*TEST*.md "$PROJECT_ROOT"/*test*.json; do
        if [ -f "$report" ]; then
            filename=$(basename "$report")
            mv "$report" "$DOCS_DIR/testing/$DATE-$filename" 2>/dev/null
            echo "  ✓ Moved test report: $filename"
        fi
    done

    # 系统状态报告
    if [ -f "$PROJECT_ROOT/CLAUDE_ENHANCER_SYSTEM_STATUS.md" ]; then
        mv "$PROJECT_ROOT/CLAUDE_ENHANCER_SYSTEM_STATUS.md" "$DOCS_DIR/architecture/system-status.md" 2>/dev/null
        echo "  ✓ Moved system status"
    fi
}

# 清理旧文件
cleanup_old_files() {
    echo "🗑️ Cleaning up old files..."

    # 移动30天前的文档到archive
    find "$DOCS_DIR" -name "*.md" -mtime +30 -exec mv {} "$DOCS_DIR/archive/" \; 2>/dev/null

    # 删除临时文件
    find "$PROJECT_ROOT" -name "*.tmp" -o -name "*.backup.*" -mtime +7 -delete 2>/dev/null

    echo "  ✓ Cleaned old files"
}

# 生成文档索引
generate_index() {
    echo "📝 Generating documentation index..."

    cat > "$DOCS_DIR/INDEX.md" << EOF
# Documentation Index
Generated: $(date)

## Recent Documents

### Architecture
$(ls -t "$DOCS_DIR/architecture/" 2>/dev/null | head -5 | sed 's/^/- /')

### Testing Reports
$(ls -t "$DOCS_DIR/testing/" 2>/dev/null | head -5 | sed 's/^/- /')

### API Documentation
$(ls -t "$DOCS_DIR/api/" 2>/dev/null | head -5 | sed 's/^/- /')

### Guides
$(ls -t "$DOCS_DIR/guides/" 2>/dev/null | head -5 | sed 's/^/- /')

## Statistics
- Total documents: $(find "$DOCS_DIR" -name "*.md" | wc -l)
- Architecture docs: $(find "$DOCS_DIR/architecture" -name "*.md" | wc -l)
- Test reports: $(find "$DOCS_DIR/testing" -name "*.md" -o -name "*.json" | wc -l)
- Archived: $(find "$DOCS_DIR/archive" -name "*" | wc -l)
EOF

    echo "  ✓ Index generated"
}

# 显示文档统计
show_stats() {
    echo ""
    echo "📊 Documentation Statistics:"
    echo "  • Total docs: $(find "$DOCS_DIR" -name "*.md" 2>/dev/null | wc -l)"
    echo "  • Root directory: $(ls "$PROJECT_ROOT"/*.md 2>/dev/null | wc -l) markdown files"
    echo "  • Organized docs: $(find "$DOCS_DIR" -type f 2>/dev/null | wc -l) files"
    echo ""
}

# 主逻辑
main() {
    echo "🗂️ Document Organization Tool"
    echo ""

    case "${1:-help}" in
        organize)
            setup_docs_structure
            organize_existing_docs
            generate_index
            show_stats
            ;;
        clean)
            cleanup_old_files
            show_stats
            ;;
        index)
            generate_index
            ;;
        stats)
            show_stats
            ;;
        *)
            echo "Usage:"
            echo "  organize - Organize all documents"
            echo "  clean    - Clean old files"
            echo "  index    - Generate index"
            echo "  stats    - Show statistics"
            ;;
    esac
}

main "$@"