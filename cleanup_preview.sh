#!/bin/bash

# Claude Enhancer 冗余文件预览脚本
# 只显示将要清理的文件，不执行实际删除

set -euo pipefail

# 配置
PROJECT_ROOT="/home/xx/dev/Perfect21"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 统计变量
BACKUP_COUNT=0
DEPRECATED_COUNT=0
ARCHIVE_COUNT=0
MIGRATION_COUNT=0
TOTAL_SIZE=0

echo -e "${BLUE}=== Claude Enhancer 冗余文件预览 ===${NC}"
echo "项目路径: $PROJECT_ROOT"
echo

# 函数：计算文件大小
get_file_size() {
    local file="$1"
    if [[ -f "$file" ]]; then
        stat -c%s "$file" 2>/dev/null || echo 0
    elif [[ -d "$file" ]]; then
        du -sb "$file" 2>/dev/null | cut -f1 || echo 0
    else
        echo 0
    fi
}

# 1. 扫描备份文件
echo -e "${YELLOW}1. 备份文件 (.bak, .backup):${NC}"
backup_files=$(find "$PROJECT_ROOT" -name "*.bak*" -o -name "*.backup*" 2>/dev/null || true)

if [[ -n "$backup_files" ]]; then
    while IFS= read -r file; do
        if [[ -n "$file" ]]; then
            size=$(get_file_size "$file")
            TOTAL_SIZE=$((TOTAL_SIZE + size))
            BACKUP_COUNT=$((BACKUP_COUNT + 1))
            echo "  - $(basename "$file") ($(numfmt --to=iec $size))"
        fi
    done <<< "$backup_files"
else
    echo "  - 无备份文件"
fi

echo

# 2. 扫描migration备份目录
echo -e "${YELLOW}2. Migration备份目录:${NC}"
migration_backup_dir="$PROJECT_ROOT/.claude/config/migration_backup_20250922_230103"

if [[ -d "$migration_backup_dir" ]]; then
    size=$(get_file_size "$migration_backup_dir")
    TOTAL_SIZE=$((TOTAL_SIZE + size))
    MIGRATION_COUNT=1
    echo "  - migration_backup_20250922_230103/ ($(numfmt --to=iec $size))"
    echo "    包含文件:"
    ls -1 "$migration_backup_dir" | while read file; do
        echo "    - $file"
    done
else
    echo "  - 无migration备份目录"
fi

echo

# 3. 扫描deprecated目录
echo -e "${YELLOW}3. Deprecated文件:${NC}"
deprecated_dir="$PROJECT_ROOT/.claude/hooks/deprecated"

if [[ -d "$deprecated_dir" ]]; then
    deprecated_files=$(find "$deprecated_dir" -type f)
    if [[ -n "$deprecated_files" ]]; then
        while IFS= read -r file; do
            size=$(get_file_size "$file")
            TOTAL_SIZE=$((TOTAL_SIZE + size))
            DEPRECATED_COUNT=$((DEPRECATED_COUNT + 1))
            echo "  - $(basename "$file") ($(numfmt --to=iec $size))"
        done <<< "$deprecated_files"
    else
        echo "  - deprecated目录为空"
    fi
else
    echo "  - 无deprecated目录"
fi

echo

# 4. 扫描config-archive冗余文件
echo -e "${YELLOW}4. Config Archive冗余文件:${NC}"
config_archive_dir="$PROJECT_ROOT/.claude/config-archive"

if [[ -d "$config_archive_dir" ]]; then
    # 保留的核心文件
    keep_files=(
        "settings.local.json"
        "settings-performance.json"
        "settings-quality.json"
    )

    echo "  冗余文件:"
    archive_files=$(find "$config_archive_dir" -type f -name "*.json")
    if [[ -n "$archive_files" ]]; then
        while IFS= read -r file; do
            filename=$(basename "$file")
            keep_file=false

            for keep in "${keep_files[@]}"; do
                if [[ "$filename" == "$keep" ]]; then
                    keep_file=true
                    break
                fi
            done

            if [[ "$keep_file" == false ]]; then
                size=$(get_file_size "$file")
                TOTAL_SIZE=$((TOTAL_SIZE + size))
                ARCHIVE_COUNT=$((ARCHIVE_COUNT + 1))
                echo "    - $filename ($(numfmt --to=iec $size))"
            fi
        done <<< "$archive_files"
    fi

    echo "  保留文件:"
    for keep in "${keep_files[@]}"; do
        if [[ -f "$config_archive_dir/$keep" ]]; then
            size=$(get_file_size "$config_archive_dir/$keep")
            echo "    ✓ $keep ($(numfmt --to=iec $size))"
        fi
    done
else
    echo "  - 无config-archive目录"
fi

echo

# 5. 总结
echo -e "${GREEN}=== 清理统计 ===${NC}"
echo "备份文件: $BACKUP_COUNT 个"
echo "Migration备份: $MIGRATION_COUNT 个目录"
echo "Deprecated文件: $DEPRECATED_COUNT 个"
echo "冗余Config文件: $ARCHIVE_COUNT 个"
echo "总计将清理: $((BACKUP_COUNT + MIGRATION_COUNT + DEPRECATED_COUNT + ARCHIVE_COUNT)) 项"
echo "预计释放空间: $(numfmt --to=iec $TOTAL_SIZE)"

echo
echo -e "${BLUE}要执行实际清理，请运行:${NC}"
echo "./cleanup_redundant.sh"