#!/bin/bash
# Version Cleaner - 自动清理旧版本文件
# Purpose: 防止多版本文件累积（如5个validator版本）
# Version: 1.0.0
# Created: 2025-10-25

set -euo pipefail

# Configuration
readonly PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
readonly ARCHIVE_DIR="${PROJECT_ROOT}/.archive/old_versions"
readonly VERSION_PATTERNS=(
    "*_v[0-9]*"
    "*_backup*"
    "*_original*"
    "*_old*"
    "*_copy*"
    "*_[0-9][0-9][0-9][0-9]*"  # 日期格式
)

# Ensure archive directory exists
mkdir -p "$ARCHIVE_DIR"

# 查找版本化文件
find_versioned_files() {
    local dir="${1:-$PROJECT_ROOT}"
    local files=()

    for pattern in "${VERSION_PATTERNS[@]}"; do
        while IFS= read -r -d '' file; do
            files+=("$file")
        done < <(find "$dir" -name "$pattern" -type f -print0 2>/dev/null)
    done

    # 去重并排序
    printf '%s\n' "${files[@]}" | sort -u
}

# 分析文件组（同一基础名的多个版本）
analyze_file_groups() {
    local -A groups

    while IFS= read -r file; do
        local base_name
        base_name=$(echo "$(basename "$file")" | sed -E 's/(_v[0-9]+|_backup|_original|_old|_copy|_[0-9]{4,}).*$//')

        if [[ -n "${groups[$base_name]:-}" ]]; then
            groups[$base_name]="${groups[$base_name]} $file"
        else
            groups[$base_name]="$file"
        fi
    done < <(find_versioned_files)

    # 输出每组文件
    for base in "${!groups[@]}"; do
        local files=(${groups[$base]})
        if [[ ${#files[@]} -gt 1 ]]; then
            echo "=== 文件组: $base (${#files[@]} 个版本) ==="
            for f in "${files[@]}"; do
                local size
                size=$(du -h "$f" 2>/dev/null | cut -f1)
                local modified
                modified=$(stat -c %y "$f" 2>/dev/null | cut -d' ' -f1)
                echo "  $f ($size, $modified)"
            done
            echo ""
        fi
    done
}

# 自动清理旧版本（保留最新的）
auto_clean_old_versions() {
    local dry_run="${1:-true}"
    local cleaned=0

    echo "🔍 扫描多版本文件..."

    # 使用临时文件存储分组
    local temp_file="/tmp/version_groups_$$.txt"
    analyze_file_groups > "$temp_file"

    if [[ ! -s "$temp_file" ]]; then
        echo "✅ 没有发现多版本文件"
        rm -f "$temp_file"
        return 0
    fi

    echo "📊 发现的多版本文件："
    cat "$temp_file"

    if [[ "$dry_run" == "true" ]]; then
        echo "⚠️  DRY RUN模式 - 不会真正删除文件"
        echo "使用 'auto_clean_old_versions false' 来执行清理"
    else
        echo "🗑️  开始清理旧版本..."

        # 对每个文件组，保留最新的，归档其他的
        while IFS= read -r line; do
            if [[ "$line" =~ ^===.*\(([0-9]+)\ 个版本\) ]]; then
                local count="${BASH_REMATCH[1]}"
                if [[ $count -gt 1 ]]; then
                    # 获取该组的所有文件
                    local files=()
                    while IFS= read -r file_line && [[ ! "$file_line" =~ ^=== ]] && [[ -n "$file_line" ]]; do
                        if [[ "$file_line" =~ ^[[:space:]]+(.+)[[:space:]]\( ]]; then
                            files+=("${BASH_REMATCH[1]}")
                        fi
                    done

                    # 找出最新的文件
                    local newest=""
                    local newest_time=0
                    for f in "${files[@]}"; do
                        local mtime
                        mtime=$(stat -c %Y "$f" 2>/dev/null || echo 0)
                        if [[ $mtime -gt $newest_time ]]; then
                            newest_time=$mtime
                            newest="$f"
                        fi
                    done

                    # 归档旧版本
                    for f in "${files[@]}"; do
                        if [[ "$f" != "$newest" ]]; then
                            echo "  归档: $f → $ARCHIVE_DIR/"
                            mv "$f" "$ARCHIVE_DIR/" 2>/dev/null || echo "    ❌ 归档失败: $f"
                            ((cleaned++))
                        else
                            echo "  保留: $f (最新)"
                        fi
                    done
                fi
            fi
        done < "$temp_file"

        echo "✅ 清理完成，归档了 $cleaned 个旧版本文件"
    fi

    rm -f "$temp_file"
}

# 特殊处理：validator版本清理
clean_validator_versions() {
    echo "🔍 检查workflow_validator版本..."

    local validators=(
        "${PROJECT_ROOT}/scripts/workflow_validator.sh"
        "${PROJECT_ROOT}/scripts/workflow_validator_v97.sh"
        "${PROJECT_ROOT}/scripts/workflow_validator_v75.sh"
        "${PROJECT_ROOT}/scripts/workflow_validator_v75_complete.sh"
        "${PROJECT_ROOT}/scripts/workflow_validator_original_backup.sh"
    )

    local current_validator=""
    local highest_version=0

    # 找出最高版本号的validator
    for v in "${validators[@]}"; do
        if [[ -f "$v" ]]; then
            if [[ "$v" =~ _v([0-9]+) ]]; then
                local version="${BASH_REMATCH[1]}"
                if [[ $version -gt $highest_version ]]; then
                    highest_version=$version
                    current_validator="$v"
                fi
            elif [[ "$v" =~ workflow_validator\.sh$ ]]; then
                # 没有版本号的可能是当前版本
                if [[ -z "$current_validator" ]]; then
                    current_validator="$v"
                fi
            fi
        fi
    done

    if [[ -n "$current_validator" ]]; then
        echo "📌 当前版本: $current_validator (v$highest_version)"

        # 归档其他版本
        for v in "${validators[@]}"; do
            if [[ -f "$v" ]] && [[ "$v" != "$current_validator" ]]; then
                echo "  归档: $(basename "$v")"
                mv "$v" "$ARCHIVE_DIR/" 2>/dev/null || echo "    ❌ 归档失败"
            fi
        done
    fi
}

# 主函数
main() {
    local command="${1:-help}"

    case "$command" in
        analyze)
            analyze_file_groups
            ;;
        clean)
            auto_clean_old_versions "${2:-true}"
            ;;
        clean-validators)
            clean_validator_versions
            ;;
        help|*)
            cat <<EOF
版本清理器 - 防止多版本文件累积

用法: $(basename "$0") [命令] [参数]

命令:
  analyze           分析多版本文件
  clean [dry_run]   清理旧版本 (默认dry_run=true)
  clean-validators  清理validator多版本
  help             显示帮助

示例:
  # 查看多版本文件
  $(basename "$0") analyze

  # 模拟清理（不真正删除）
  $(basename "$0") clean true

  # 执行清理
  $(basename "$0") clean false

功能:
  • 自动检测多版本文件
  • 保留最新版本
  • 归档旧版本到 .archive/
  • 防止版本累积
EOF
            ;;
    esac
}

# 如果直接执行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi