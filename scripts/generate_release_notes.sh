#!/bin/bash
# Release Notes生成器
# 从CHANGELOG.md和PR描述生成标准格式的Release Notes
# 用法: generate_release_notes.sh VERSION PR_NUMBER

set -euo pipefail

# 从CHANGELOG.md提取版本内容
extract_from_changelog() {
    local version="$1"
    local changelog_file="CHANGELOG.md"

    if [[ ! -f "$changelog_file" ]]; then
        echo "⚠️ CHANGELOG.md不存在，跳过提取"
        return 1
    fi

    # 提取版本区块（从## [version]到下一个##）
    awk -v ver="$version" '
        /^## \['"$version"'\]/ { found=1; next }
        /^## \[/ { if (found) exit }
        found { print }
    ' "$changelog_file"
}

# 从GitHub PR获取描述（需要gh CLI）
extract_from_pr() {
    local pr_number="$1"

    if ! command -v gh &> /dev/null; then
        echo "⚠️ gh CLI未安装，跳过PR描述提取"
        return 1
    fi

    # 获取PR body
    gh pr view "$pr_number" --json body --jq '.body' 2>/dev/null || {
        echo "⚠️ 无法获取PR #$pr_number描述"
        return 1
    }
}

# 生成Release Notes
generate_release_notes() {
    local version="$1"
    local pr_number="${2:-}"

    cat <<EOF
# Release v$version

## 📋 更新内容

EOF

    # 从CHANGELOG提取
    if extract_from_changelog "$version" > /tmp/changelog_content.txt 2>/dev/null; then
        cat /tmp/changelog_content.txt
        echo ""
    else
        echo "（请查看CHANGELOG.md获取详细更新内容）"
        echo ""
    fi

    # 从PR提取
    if [[ -n "$pr_number" ]]; then
        echo "## 🔗 相关PR"
        echo ""
        echo "- PR #$pr_number"
        echo ""

        if extract_from_pr "$pr_number" > /tmp/pr_content.txt 2>/dev/null; then
            echo "### PR描述"
            echo ""
            cat /tmp/pr_content.txt
            echo ""
        fi
    fi

    # 添加标准footer
    cat <<'EOF'

---

## 📦 安装/升级

```bash
# 克隆或更新仓库
git pull origin main

# 如果是全新安装
./.claude/install.sh
```

## 🐛 问题反馈

如果遇到问题，请在 [Issues](../../issues) 中反馈。

---

🤖 自动生成于 $(date +'%Y-%m-%d %H:%M:%S')
EOF
}

# 主函数
main() {
    if [[ $# -lt 1 ]]; then
        cat <<EOF >&2
用法: $0 VERSION [PR_NUMBER]

生成Release Notes

参数:
  VERSION    - 版本号 (例如: 6.4.0)
  PR_NUMBER  - PR编号 (可选)

示例:
  $0 6.4.0
  $0 6.4.0 123
EOF
        exit 1
    fi

    local version="$1"
    local pr_number="${2:-}"

    generate_release_notes "$version" "$pr_number"
}

# 如果直接执行（不是source）
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
