#!/bin/bash
# 版本号比较工具
# 比较两个semver版本号，判断第一个是否大于第二个
# 用法: compare_versions.sh NEW_VERSION OLD_VERSION
# 返回: 0 (NEW > OLD), 1 (NEW <= OLD 或格式错误)

set -euo pipefail

# 验证semver格式
validate_semver() {
    local version="$1"
    if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "❌ 错误: 无效的semver格式: $version" >&2
        echo "   期望格式: X.Y.Z (例如: 1.2.3)" >&2
        return 1
    fi
    return 0
}

# 比较两个版本号
compare_versions() {
    local new_version="$1"
    local old_version="$2"

    # 验证格式
    validate_semver "$new_version" || return 1
    validate_semver "$old_version" || return 1

    # 分解版本号
    IFS='.' read -r new_major new_minor new_patch <<< "$new_version"
    IFS='.' read -r old_major old_minor old_patch <<< "$old_version"

    # 比较major版本
    if [[ $new_major -gt $old_major ]]; then
        echo "✅ Major版本递增: $old_major → $new_major"
        return 0
    elif [[ $new_major -lt $old_major ]]; then
        echo "❌ Major版本降低: $old_major → $new_major"
        return 1
    fi

    # Major相同，比较minor版本
    if [[ $new_minor -gt $old_minor ]]; then
        echo "✅ Minor版本递增: $old_minor → $new_minor"
        return 0
    elif [[ $new_minor -lt $old_minor ]]; then
        echo "❌ Minor版本降低: $old_minor → $new_minor"
        return 1
    fi

    # Major和Minor相同，比较patch版本
    if [[ $new_patch -gt $old_patch ]]; then
        echo "✅ Patch版本递增: $old_patch → $new_patch"
        return 0
    elif [[ $new_patch -lt $old_patch ]]; then
        echo "❌ Patch版本降低: $old_patch → $new_patch"
        return 1
    fi

    # 版本号完全相同
    echo "❌ 版本号未变化: $new_version == $old_version"
    return 1
}

# 主函数
main() {
    if [[ $# -ne 2 ]]; then
        cat <<EOF >&2
用法: $0 NEW_VERSION OLD_VERSION

比较两个semver版本号，判断NEW_VERSION是否大于OLD_VERSION

示例:
  $0 1.2.3 1.2.2  # ✅ 返回0 (patch递增)
  $0 1.3.0 1.2.9  # ✅ 返回0 (minor递增)
  $0 2.0.0 1.9.9  # ✅ 返回0 (major递增)
  $0 1.2.2 1.2.3  # ❌ 返回1 (版本降低)
  $0 1.2.3 1.2.3  # ❌ 返回1 (版本未变)
EOF
        exit 1
    fi

    local new_version="$1"
    local old_version="$2"

    echo "🔍 版本比较: $new_version vs $old_version"

    if compare_versions "$new_version" "$old_version"; then
        echo "✅ 版本检查通过"
        exit 0
    else
        echo "❌ 版本检查失败"
        exit 1
    fi
}

# 如果直接执行（不是source）
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
