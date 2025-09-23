#!/bin/bash

# Claude Enhancer 冗余文件安全清理脚本
# 作为cleanup-specialist，专门处理系统优化后的冗余文件清理

set -euo pipefail

# 配置
PROJECT_ROOT="/home/xx/dev/Perfect21"
TRASH_DIR="${PROJECT_ROOT}/.trash/cleanup_$(date +%Y%m%d_%H%M%S)"
REPORT_FILE="${PROJECT_ROOT}/cleanup_report_$(date +%Y%m%d_%H%M%S).md"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 统计变量
TOTAL_FILES=0
TOTAL_SIZE=0
BACKUP_COUNT=0
DEPRECATED_COUNT=0
ARCHIVE_COUNT=0
MIGRATION_COUNT=0

echo -e "${BLUE}=== Claude Enhancer 冗余文件清理工具 ===${NC}"
echo "项目路径: $PROJECT_ROOT"
echo "备份路径: $TRASH_DIR"
echo "报告文件: $REPORT_FILE"
echo

# 创建垃圾桶目录
mkdir -p "$TRASH_DIR"/{backup_files,deprecated,config_archive,migration_backup,agent_duplicates}

# 开始报告
cat > "$REPORT_FILE" << EOF
# Claude Enhancer 清理报告
生成时间: $(date '+%Y-%m-%d %H:%M:%S')
项目路径: $PROJECT_ROOT
备份路径: $TRASH_DIR

## 清理概要

EOF

# 函数：计算文件大小
get_file_size() {
    local file="$1"
    if [[ -f "$file" ]]; then
        stat -c%s "$file" 2>/dev/null || echo 0
    else
        echo 0
    fi
}

# 函数：安全移动文件到垃圾桶
safe_move_to_trash() {
    local source="$1"
    local category="$2"
    local dest_dir="$TRASH_DIR/$category"

    if [[ -f "$source" ]]; then
        local filename=$(basename "$source")
        local size=$(get_file_size "$source")

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

# 1. 清理备份文件 (.bak, .backup)
echo -e "${YELLOW}1. 扫描备份文件...${NC}"
cat >> "$REPORT_FILE" << EOF
### 1. 备份文件清理

以下文件将被清理:
EOF

backup_files=$(find "$PROJECT_ROOT" -name "*.bak*" -o -name "*.backup*" 2>/dev/null || true)

if [[ -n "$backup_files" ]]; then
    while IFS= read -r file; do
        if [[ -n "$file" ]]; then
            echo "备份文件: $file"
            echo "- \`$file\`" >> "$REPORT_FILE"
            BACKUP_COUNT=$((BACKUP_COUNT + 1))
        fi
    done <<< "$backup_files"
else
    echo "未找到备份文件"
    echo "- 无备份文件需要清理" >> "$REPORT_FILE"
fi

echo

# 2. 清理migration_backup目录
echo -e "${YELLOW}2. 扫描migration备份目录...${NC}"
migration_backup_dir="$PROJECT_ROOT/.claude/config/migration_backup_20250922_230103"

cat >> "$REPORT_FILE" << EOF

### 2. Migration备份目录清理

EOF

if [[ -d "$migration_backup_dir" ]]; then
    echo "Migration备份目录: $migration_backup_dir"
    echo "- \`$migration_backup_dir\`" >> "$REPORT_FILE"
    ls -la "$migration_backup_dir" | tail -n +2 | while read line; do
        echo "  - $(echo $line | awk '{print $9}')" >> "$REPORT_FILE"
    done
    MIGRATION_COUNT=1
else
    echo "Migration备份目录不存在"
    echo "- Migration备份目录不存在" >> "$REPORT_FILE"
fi

echo

# 3. 清理deprecated目录
echo -e "${YELLOW}3. 扫描deprecated目录...${NC}"
deprecated_dir="$PROJECT_ROOT/.claude/hooks/deprecated"

cat >> "$REPORT_FILE" << EOF

### 3. Deprecated文件清理

EOF

if [[ -d "$deprecated_dir" ]]; then
    echo "Deprecated目录: $deprecated_dir"
    echo "- \`$deprecated_dir\`" >> "$REPORT_FILE"
    deprecated_files=$(find "$deprecated_dir" -type f)
    if [[ -n "$deprecated_files" ]]; then
        while IFS= read -r file; do
            echo "Deprecated文件: $file"
            echo "  - \`$(basename "$file")\`" >> "$REPORT_FILE"
            DEPRECATED_COUNT=$((DEPRECATED_COUNT + 1))
        done <<< "$deprecated_files"
    fi
else
    echo "Deprecated目录不存在"
    echo "- Deprecated目录不存在" >> "$REPORT_FILE"
fi

echo

# 4. 清理config-archive中的冗余文件
echo -e "${YELLOW}4. 扫描config-archive冗余文件...${NC}"
config_archive_dir="$PROJECT_ROOT/.claude/config-archive"

cat >> "$REPORT_FILE" << EOF

### 4. Config Archive清理

保留核心配置文件，清理以下冗余文件:
EOF

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
                echo "冗余配置文件: $file"
                echo "- \`$filename\`" >> "$REPORT_FILE"
                ARCHIVE_COUNT=$((ARCHIVE_COUNT + 1))
            fi
        done <<< "$archive_files"
    fi

    echo
    echo "保留的核心配置文件:"
    for keep in "${keep_files[@]}"; do
        if [[ -f "$config_archive_dir/$keep" ]]; then
            echo "  ✓ $keep"
        fi
    done

    cat >> "$REPORT_FILE" << EOF

保留的核心配置文件:
EOF
    for keep in "${keep_files[@]}"; do
        if [[ -f "$config_archive_dir/$keep" ]]; then
            echo "- \`$keep\` ✓" >> "$REPORT_FILE"
        fi
    done
else
    echo "Config-archive目录不存在"
    echo "- Config-archive目录不存在" >> "$REPORT_FILE"
fi

echo

# 5. 检查重复的Agent定义文件
echo -e "${YELLOW}5. 扫描重复Agent定义...${NC}"

cat >> "$REPORT_FILE" << EOF

### 5. 重复Agent定义检查

EOF

# 查找可能的重复agent文件
agent_dirs=(
    "$PROJECT_ROOT/.claude/agents"
    "$PROJECT_ROOT/.claude/config"
)

found_duplicates=false
for dir in "${agent_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
        # 查找agent相关文件
        agent_files=$(find "$dir" -name "*agent*" -type f 2>/dev/null || true)
        if [[ -n "$agent_files" ]]; then
            while IFS= read -r file; do
                if [[ -n "$file" ]]; then
                    echo "Agent相关文件: $file"
                    echo "- \`$file\`" >> "$REPORT_FILE"
                    found_duplicates=true
                fi
            done <<< "$agent_files"
        fi
    fi
done

if [[ "$found_duplicates" == false ]]; then
    echo "未发现重复的Agent定义文件"
    echo "- 未发现重复的Agent定义文件" >> "$REPORT_FILE"
fi

echo

# 确认执行
echo -e "${RED}=== 清理确认 ===${NC}"
echo "即将清理的文件统计:"
echo "- 备份文件: $BACKUP_COUNT 个"
echo "- Migration备份: $MIGRATION_COUNT 个目录"
echo "- Deprecated文件: $DEPRECATED_COUNT 个"
echo "- Config归档文件: $ARCHIVE_COUNT 个"
echo

read -p "确认执行清理操作？所有文件将先备份到 .trash 目录 (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "清理操作已取消"
    exit 0
fi

echo
echo -e "${GREEN}=== 开始清理操作 ===${NC}"

# 执行清理操作

# 1. 移动备份文件
echo -e "${BLUE}清理备份文件...${NC}"
backup_files=$(find "$PROJECT_ROOT" -name "*.bak*" -o -name "*.backup*" 2>/dev/null || true)
if [[ -n "$backup_files" ]]; then
    while IFS= read -r file; do
        if [[ -n "$file" ]]; then
            safe_move_to_trash "$file" "backup_files"
        fi
    done <<< "$backup_files"
fi

# 2. 移动migration备份目录
echo -e "${BLUE}清理migration备份...${NC}"
if [[ -d "$migration_backup_dir" ]]; then
    safe_move_to_trash "$migration_backup_dir" "migration_backup"
fi

# 3. 移动deprecated目录
echo -e "${BLUE}清理deprecated文件...${NC}"
if [[ -d "$deprecated_dir" ]]; then
    deprecated_files=$(find "$deprecated_dir" -type f)
    if [[ -n "$deprecated_files" ]]; then
        while IFS= read -r file; do
            safe_move_to_trash "$file" "deprecated"
        done <<< "$deprecated_files"
    fi
fi

# 4. 移动冗余配置文件
echo -e "${BLUE}清理冗余配置文件...${NC}"
if [[ -d "$config_archive_dir" ]]; then
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
            fi
        done <<< "$archive_files"
    fi
fi

echo

# 实际删除操作
echo -e "${RED}=== 执行删除操作 ===${NC}"

# 删除备份文件
backup_files=$(find "$PROJECT_ROOT" -name "*.bak*" -o -name "*.backup*" 2>/dev/null || true)
if [[ -n "$backup_files" ]]; then
    while IFS= read -r file; do
        if [[ -n "$file" && -e "$file" ]]; then
            echo "删除: $file"
            rm -f "$file"
        fi
    done <<< "$backup_files"
fi

# 删除migration备份目录
if [[ -d "$migration_backup_dir" ]]; then
    echo "删除目录: $migration_backup_dir"
    rm -rf "$migration_backup_dir"
fi

# 删除deprecated目录中的文件
if [[ -d "$deprecated_dir" ]]; then
    echo "清空deprecated目录: $deprecated_dir"
    deprecated_files=$(find "$deprecated_dir" -type f)
    if [[ -n "$deprecated_files" ]]; then
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

echo

# 完成报告
cat >> "$REPORT_FILE" << EOF

## 清理结果

- 总处理文件数: $TOTAL_FILES
- 总清理大小: $(numfmt --to=iec $TOTAL_SIZE)
- 备份位置: \`$TRASH_DIR\`

## 清理操作

1. ✅ 备份文件清理完成 ($BACKUP_COUNT 个)
2. ✅ Migration备份清理完成 ($MIGRATION_COUNT 个目录)
3. ✅ Deprecated文件清理完成 ($DEPRECATED_COUNT 个)
4. ✅ Config归档清理完成 ($ARCHIVE_COUNT 个)

## 安全恢复

如需恢复任何文件，可从以下位置获取:
\`\`\`bash
# 恢复所有文件
cp -r $TRASH_DIR/* $PROJECT_ROOT/

# 恢复特定类型文件
cp -r $TRASH_DIR/backup_files/* $PROJECT_ROOT/
cp -r $TRASH_DIR/deprecated/* $PROJECT_ROOT/.claude/hooks/deprecated/
\`\`\`

## 后续建议

1. 验证系统功能正常
2. 运行测试确保无影响
3. 30天后可删除 .trash 目录
EOF

echo -e "${GREEN}=== 清理完成 ===${NC}"
echo "处理统计:"
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