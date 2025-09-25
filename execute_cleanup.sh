#!/bin/bash

# Claude Enhancer 实际清理执行脚本
# 基于预览结果的安全清理操作

set -euo pipefail

# 配置
PROJECT_ROOT="/home/xx/dev/Claude_Enhancer"
TRASH_DIR="${PROJECT_ROOT}/.trash/cleanup_$(date +%Y%m%d_%H%M%S)"
REPORT_FILE="${PROJECT_ROOT}/cleanup_report_$(date +%Y%m%d_%H%M%S).md"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Claude Enhancer 安全清理执行 ===${NC}"
echo "项目路径: $PROJECT_ROOT"
echo "备份路径: $TRASH_DIR"
echo "报告文件: $REPORT_FILE"
echo

# 创建垃圾桶目录
mkdir -p "$TRASH_DIR"/{backup_files,deprecated,config_archive,migration_backup}

# 统计变量
TOTAL_FILES=0
TOTAL_SIZE=0

# 函数：安全移动文件到垃圾桶
safe_move_to_trash() {
    local source="$1"
    local category="$2"
    local dest_dir="$TRASH_DIR/$category"

    if [[ -f "$source" ]]; then
        local filename=$(basename "$source")
        local size=$(stat -c%s "$source" 2>/dev/null || echo 0)

        # 如果文件名重复，添加时间戳
        local dest_file="$dest_dir/$filename"
        if [[ -f "$dest_file" ]]; then
            local timestamp=$(date +%H%M%S)
            dest_file="$dest_dir/${filename}_${timestamp}"
        fi

        cp "$source" "$dest_file"
        echo "  ✓ $source → $dest_file ($(numfmt --to=iec $size))"

        TOTAL_FILES=$((TOTAL_FILES + 1))
        TOTAL_SIZE=$((TOTAL_SIZE + size))

        return 0
    elif [[ -d "$source" ]]; then
        local dirname=$(basename "$source")
        cp -r "$source" "$dest_dir/$dirname"
        local size=$(du -sb "$source" | cut -f1)
        echo "  ✓ $source → $dest_dir/$dirname ($(numfmt --to=iec $size))"

        TOTAL_FILES=$((TOTAL_FILES + 1))
        TOTAL_SIZE=$((TOTAL_SIZE + size))

        return 0
    else
        echo "  ⚠ 跳过不存在的文件: $source"
        return 1
    fi
}

# 开始报告
cat > "$REPORT_FILE" << EOF
# Claude Enhancer 清理报告
生成时间: $(date '+%Y-%m-%d %H:%M:%S')
项目路径: $PROJECT_ROOT
备份路径: $TRASH_DIR

## 清理操作详情

EOF

echo -e "${GREEN}=== 第一步：备份所有目标文件 ===${NC}"

# 1. 备份所有备份文件
echo -e "${BLUE}备份 .bak/.backup 文件...${NC}"
echo "### 备份文件清理" >> "$REPORT_FILE"
backup_files=$(find "$PROJECT_ROOT" -name "*.bak*" -o -name "*.backup*" 2>/dev/null || true)
backup_count=0

if [[ -n "$backup_files" ]]; then
    while IFS= read -r file; do
        if [[ -n "$file" ]]; then
            safe_move_to_trash "$file" "backup_files"
            echo "- \`$file\`" >> "$REPORT_FILE"
            backup_count=$((backup_count + 1))
        fi
    done <<< "$backup_files"
fi

echo

# 2. 备份migration目录
echo -e "${BLUE}备份migration目录...${NC}"
echo "" >> "$REPORT_FILE"
echo "### Migration备份目录清理" >> "$REPORT_FILE"
migration_backup_dir="$PROJECT_ROOT/.claude/config/migration_backup_20250922_230103"
migration_count=0

if [[ -d "$migration_backup_dir" ]]; then
    safe_move_to_trash "$migration_backup_dir" "migration_backup"
    echo "- \`$migration_backup_dir\`" >> "$REPORT_FILE"
    migration_count=1
fi

echo

# 3. 备份deprecated文件
echo -e "${BLUE}备份deprecated文件...${NC}"
echo "" >> "$REPORT_FILE"
echo "### Deprecated文件清理" >> "$REPORT_FILE"
deprecated_dir="$PROJECT_ROOT/.claude/hooks/deprecated"
deprecated_count=0

if [[ -d "$deprecated_dir" ]]; then
    deprecated_files=$(find "$deprecated_dir" -type f)
    if [[ -n "$deprecated_files" ]]; then
        while IFS= read -r file; do
            safe_move_to_trash "$file" "deprecated"
            echo "- \`$(basename "$file")\`" >> "$REPORT_FILE"
            deprecated_count=$((deprecated_count + 1))
        done <<< "$deprecated_files"
    fi
fi

echo

# 4. 备份冗余配置文件
echo -e "${BLUE}备份冗余配置文件...${NC}"
echo "" >> "$REPORT_FILE"
echo "### Config Archive清理" >> "$REPORT_FILE"
config_archive_dir="$PROJECT_ROOT/.claude/config-archive"
archive_count=0

if [[ -d "$config_archive_dir" ]]; then
    # 保留的核心文件
    keep_files=(
        "settings.local.json"
        "settings-performance.json"
        "settings-quality.json"
    )

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
                safe_move_to_trash "$file" "config_archive"
                echo "- \`$filename\`" >> "$REPORT_FILE"
                archive_count=$((archive_count + 1))
            fi
        done <<< "$archive_files"
    fi
fi

echo
echo -e "${YELLOW}备份完成统计：${NC}"
echo "- 备份文件: $backup_count 个"
echo "- Migration备份: $migration_count 个目录"
echo "- Deprecated文件: $deprecated_count 个"
echo "- 冗余Config文件: $archive_count 个"
echo "- 总计已备份: $TOTAL_FILES 项"
echo "- 备份数据大小: $(numfmt --to=iec $TOTAL_SIZE)"

read -p "确认删除原文件？所有文件已安全备份到 $TRASH_DIR (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}操作已取消，文件已备份到 $TRASH_DIR${NC}"
    exit 0
fi

echo
echo -e "${RED}=== 第二步：删除原始文件 ===${NC}"

# 删除备份文件
if [[ -n "$backup_files" ]]; then
    echo -e "${BLUE}删除备份文件...${NC}"
    while IFS= read -r file; do
        if [[ -n "$file" && -e "$file" ]]; then
            echo "删除: $file"
            rm -f "$file"
        fi
    done <<< "$backup_files"
fi

# 删除migration备份目录
if [[ -d "$migration_backup_dir" ]]; then
    echo -e "${BLUE}删除migration备份目录...${NC}"
    echo "删除目录: $migration_backup_dir"
    rm -rf "$migration_backup_dir"
fi

# 删除deprecated文件
if [[ -d "$deprecated_dir" ]]; then
    deprecated_files=$(find "$deprecated_dir" -type f)
    if [[ -n "$deprecated_files" ]]; then
        echo -e "${BLUE}删除deprecated文件...${NC}"
        while IFS= read -r file; do
            echo "删除: $file"
            rm -f "$file"
        done <<< "$deprecated_files"
    fi
fi

# 删除冗余配置文件
if [[ -d "$config_archive_dir" ]]; then
    keep_files=(
        "settings.local.json"
        "settings-performance.json"
        "settings-quality.json"
    )

    archive_files=$(find "$config_archive_dir" -type f -name "*.json")
    if [[ -n "$archive_files" ]]; then
        echo -e "${BLUE}删除冗余配置文件...${NC}"
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
                echo "删除: $file"
                rm -f "$file"
            fi
        done <<< "$archive_files"
    fi
fi

# 完成报告
cat >> "$REPORT_FILE" << EOF

## 清理结果

- 总处理文件数: $TOTAL_FILES
- 总清理大小: $(numfmt --to=iec $TOTAL_SIZE)
- 备份位置: \`$TRASH_DIR\`

## 清理统计

1. ✅ 备份文件清理完成 ($backup_count 个)
2. ✅ Migration备份清理完成 ($migration_count 个目录)
3. ✅ Deprecated文件清理完成 ($deprecated_count 个)
4. ✅ Config归档清理完成 ($archive_count 个)

## 保留的重要文件

Config Archive中保留的核心配置:
- \`settings.local.json\` ✓
- \`settings-performance.json\` ✓
- \`settings-quality.json\` ✓

## 安全恢复

如需恢复任何文件，可从以下位置获取:
\`\`\`bash
# 恢复所有文件
cp -r $TRASH_DIR/* $PROJECT_ROOT/

# 恢复特定类型文件
cp -r $TRASH_DIR/backup_files/* $PROJECT_ROOT/
cp -r $TRASH_DIR/deprecated/* $PROJECT_ROOT/.claude/hooks/deprecated/
cp -r $TRASH_DIR/config_archive/* $PROJECT_ROOT/.claude/config-archive/
cp -r $TRASH_DIR/migration_backup/* $PROJECT_ROOT/.claude/config/
\`\`\`

## 后续建议

1. ✅ 验证系统功能正常
2. ✅ 运行测试确保无影响
3. ⏰ 30天后可删除 .trash 目录

清理完成时间: $(date '+%Y-%m-%d %H:%M:%S')
EOF

echo
echo -e "${GREEN}=== 清理完成 ===${NC}"
echo "清理统计:"
echo "- 总文件数: $TOTAL_FILES"
echo "- 总大小: $(numfmt --to=iec $TOTAL_SIZE)"
echo "- 备份位置: $TRASH_DIR"
echo "- 详细报告: $REPORT_FILE"
echo
echo -e "${YELLOW}建议操作:${NC}"
echo "1. 检查系统功能是否正常"
echo "2. 运行测试验证无影响"
echo "3. 30天后删除 .trash 目录"
echo
echo -e "${BLUE}恢复方法 (如需要):${NC}"
echo "cp -r $TRASH_DIR/* $PROJECT_ROOT/"