#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 版本一致性检查脚本
# Claude Enhancer v6.5.0
# ═══════════════════════════════════════════════════════════════
# 功能：强制检查VERSION、settings.json、manifest.yml三者版本一致
# 用途：pre-commit hook / CI验证
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ═══════════════════════════════════════════════════════════════
# 版本提取函数
# ═══════════════════════════════════════════════════════════════

get_version_file() {
    if [[ ! -f "$PROJECT_ROOT/VERSION" ]]; then
        echo "ERROR: VERSION file not found" >&2
        return 1
    fi
    cat "$PROJECT_ROOT/VERSION" | tr -d '\n\r' | xargs
}

get_settings_version() {
    local settings="$PROJECT_ROOT/.claude/settings.json"
    if [[ ! -f "$settings" ]]; then
        echo "ERROR: settings.json not found" >&2
        return 1
    fi

    if command -v jq >/dev/null 2>&1; then
        jq -r '.version' "$settings" 2>/dev/null || echo "ERROR"
    else
        python3 -c "import json; print(json.load(open('$settings'))['version'])" 2>/dev/null || echo "ERROR"
    fi
}

get_manifest_version() {
    local manifest="$PROJECT_ROOT/.workflow/manifest.yml"
    if [[ ! -f "$manifest" ]]; then
        echo "ERROR: manifest.yml not found" >&2
        return 1
    fi

    if command -v python3 >/dev/null 2>&1; then
        python3 -c "import yaml; print(yaml.safe_load(open('$manifest'))['version'])" 2>/dev/null || echo "ERROR"
    else
        grep "^version:" "$manifest" | awk '{print $2}' | tr -d '"' || echo "ERROR"
    fi
}

get_package_version() {
    local package="$PROJECT_ROOT/package.json"
    if [[ ! -f "$package" ]]; then
        echo "ERROR: package.json not found" >&2
        return 1
    fi

    if command -v jq >/dev/null 2>&1; then
        jq -r '.version' "$package" 2>/dev/null || echo "ERROR"
    else
        python3 -c "import json; print(json.load(open('$package'))['version'])" 2>/dev/null || echo "ERROR"
    fi
}

get_changelog_version() {
    local changelog="$PROJECT_ROOT/CHANGELOG.md"
    if [[ ! -f "$changelog" ]]; then
        echo "ERROR: CHANGELOG.md not found" >&2
        return 1
    fi

    # Extract first RELEASED version number in brackets [X.Y.Z] (skip [Unreleased])
    # Only match lines starting with ## [digit.digit.digit]
    grep -oP '^## \[\K[0-9]+\.[0-9]+\.[0-9]+(?=\])' "$changelog" 2>/dev/null | head -1 || echo "ERROR"
}

get_spec_version() {
    local spec="$PROJECT_ROOT/.workflow/SPEC.yaml"
    if [[ ! -f "$spec" ]]; then
        echo "ERROR: SPEC.yaml not found" >&2
        return 1
    fi

    # Extract version - try .version first (top level), fallback to .metadata.version
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "import yaml; data = yaml.safe_load(open('$spec')); print(data.get('version') or data.get('metadata', {}).get('version', 'ERROR'))" 2>/dev/null || echo "ERROR"
    else
        # Fallback: try top-level version first, then metadata.version
        grep "^version:" "$spec" | head -1 | awk '{print $2}' | tr -d '"' || \
        grep -A 5 "^metadata:" "$spec" | grep "version:" | head -1 | awk '{print $2}' | tr -d '"' || echo "ERROR"
    fi
}

# ═══════════════════════════════════════════════════════════════
# 版本一致性检查
# ═══════════════════════════════════════════════════════════════

check_version_consistency() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}🔢 版本一致性检查 (6个文件)${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""

    # 提取所有6个版本
    local version_file=$(get_version_file)
    local version_settings=$(get_settings_version)
    local version_manifest=$(get_manifest_version)
    local version_package=$(get_package_version)
    local version_changelog=$(get_changelog_version)
    local version_spec=$(get_spec_version)

    # 检查提取是否成功
    if [[ "$version_file" == "ERROR"* ]] || [[ "$version_settings" == "ERROR"* ]] || \
       [[ "$version_manifest" == "ERROR"* ]] || [[ "$version_package" == "ERROR"* ]] || \
       [[ "$version_changelog" == "ERROR"* ]] || [[ "$version_spec" == "ERROR"* ]]; then
        echo -e "${RED}❌ 版本提取失败${NC}"
        echo ""
        [[ "$version_file" == "ERROR"* ]] && echo -e "  ${RED}✗${NC} VERSION文件: $version_file"
        [[ "$version_settings" == "ERROR"* ]] && echo -e "  ${RED}✗${NC} settings.json: $version_settings"
        [[ "$version_manifest" == "ERROR"* ]] && echo -e "  ${RED}✗${NC} manifest.yml: $version_manifest"
        [[ "$version_package" == "ERROR"* ]] && echo -e "  ${RED}✗${NC} package.json: $version_package"
        [[ "$version_changelog" == "ERROR"* ]] && echo -e "  ${RED}✗${NC} CHANGELOG.md: $version_changelog"
        [[ "$version_spec" == "ERROR"* ]] && echo -e "  ${RED}✗${NC} SPEC.yaml: $version_spec"
        return 1
    fi

    # 显示当前版本
    echo -e "${BOLD}当前版本：${NC}"
    echo -e "  ${CYAN}VERSION文件:${NC}      $version_file"
    echo -e "  ${CYAN}settings.json:${NC}    $version_settings"
    echo -e "  ${CYAN}manifest.yml:${NC}     $version_manifest"
    echo -e "  ${CYAN}package.json:${NC}     $version_package"
    echo -e "  ${CYAN}CHANGELOG.md:${NC}     $version_changelog"
    echo -e "  ${CYAN}SPEC.yaml:${NC}        $version_spec"
    echo ""

    # 版本一致性检查 - 所有6个必须完全相同
    if [[ "$version_file" == "$version_settings" ]] && \
       [[ "$version_file" == "$version_manifest" ]] && \
       [[ "$version_file" == "$version_package" ]] && \
       [[ "$version_file" == "$version_changelog" ]] && \
       [[ "$version_file" == "$version_spec" ]]; then
        echo -e "${GREEN}✅ 版本一致性检查通过${NC}"
        echo -e "   所有6个文件版本统一为: ${BOLD}$version_file${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}${BOLD}❌ 版本不一致检测到！${NC}"
        echo ""
        echo -e "${BOLD}不一致详情：${NC}"

        if [[ "$version_file" != "$version_settings" ]]; then
            echo -e "  ${RED}✗${NC} VERSION ($version_file) ≠ settings.json ($version_settings)"
        fi

        if [[ "$version_file" != "$version_manifest" ]]; then
            echo -e "  ${RED}✗${NC} VERSION ($version_file) ≠ manifest.yml ($version_manifest)"
        fi

        if [[ "$version_file" != "$version_package" ]]; then
            echo -e "  ${RED}✗${NC} VERSION ($version_file) ≠ package.json ($version_package)"
        fi

        if [[ "$version_file" != "$version_changelog" ]]; then
            echo -e "  ${RED}✗${NC} VERSION ($version_file) ≠ CHANGELOG.md ($version_changelog)"
        fi

        if [[ "$version_file" != "$version_spec" ]]; then
            echo -e "  ${RED}✗${NC} VERSION ($version_file) ≠ SPEC.yaml ($version_spec)"
        fi

        echo ""
        echo -e "${BOLD}🔧 修复方法：${NC}"
        echo ""
        echo -e "  ${YELLOW}1. 确定正确的版本号（通常是最新的）${NC}"
        echo ""
        echo -e "  ${YELLOW}2. 同步更新所有6个文件：${NC}"
        echo -e "     ${GREEN}# 更新VERSION文件${NC}"
        echo -e "     echo '${BOLD}X.Y.Z${NC}' > VERSION"
        echo ""
        echo -e "     ${GREEN}# 更新settings.json${NC}"
        echo -e "     jq '.version = \"${BOLD}X.Y.Z${NC}\"' .claude/settings.json > .tmp && mv .tmp .claude/settings.json"
        echo ""
        echo -e "     ${GREEN}# 更新manifest.yml${NC}"
        echo -e "     sed -i 's/^version:.*/version: ${BOLD}X.Y.Z${NC}/' .workflow/manifest.yml"
        echo ""
        echo -e "     ${GREEN}# 更新package.json${NC}"
        echo -e "     jq '.version = \"${BOLD}X.Y.Z${NC}\"' package.json > .tmp && mv .tmp package.json"
        echo ""
        echo -e "     ${GREEN}# 更新CHANGELOG.md (手动编辑第一个版本号)${NC}"
        echo -e "     # 确保第一个 [X.Y.Z] 格式的版本号匹配"
        echo ""
        echo -e "     ${GREEN}# 更新SPEC.yaml${NC}"
        echo -e "     sed -i 's/^# 版本: v.*/# 版本: v${BOLD}X.Y.Z${NC}/' .workflow/SPEC.yaml"
        echo -e "     sed -i '/^metadata:/,/^  version:/ s/version: \".*\"/version: \"${BOLD}X.Y.Z${NC}\"/' .workflow/SPEC.yaml"
        echo ""
        echo -e "  ${YELLOW}3. 重新提交${NC}"
        echo -e "     git add VERSION .claude/settings.json .workflow/manifest.yml package.json CHANGELOG.md .workflow/SPEC.yaml"
        echo -e "     git commit --amend --no-edit"
        echo ""
        echo -e "${RED}${BOLD}⚠️  提交已被阻止 - 请修复版本不一致后重试${NC}"
        echo ""

        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════
# 执行检查
# ═══════════════════════════════════════════════════════════════

check_version_consistency

exit $?
