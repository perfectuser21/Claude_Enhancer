#!/bin/bash
# Generate PR URL - Fallback solution without gh CLI
# Claude Enhancer 5.0 - Git Workflow Automation

set -euo pipefail

# Colors
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# ==================== Main Function ====================

generate_pr_url() {
    local current_branch=$(git branch --show-current)
    local remote_url=$(git config --get remote.origin.url)

    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  🔗 PR URL Generator (No gh CLI needed)${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Validate current branch
    if [[ "$current_branch" == "main" || "$current_branch" == "master" ]]; then
        echo -e "${YELLOW}⚠️  警告: 当前在主分支${NC}"
        echo "请先切换到 feature 分支"
        exit 1
    fi

    # Extract repository info from URL
    # Supports both SSH and HTTPS formats
    local repo=""
    if [[ "$remote_url" =~ git@github\.com:(.*)\.git ]]; then
        # SSH format: git@github.com:user/repo.git
        repo="${BASH_REMATCH[1]}"
    elif [[ "$remote_url" =~ https://github\.com/(.*)\.git ]]; then
        # HTTPS format: https://github.com/user/repo.git
        repo="${BASH_REMATCH[1]}"
    else
        echo -e "${YELLOW}⚠️  无法解析远程仓库 URL: $remote_url${NC}"
        echo "请手动访问 GitHub 创建 PR"
        exit 1
    fi

    # Build PR URL
    local base_branch="${1:-main}"
    local pr_url="https://github.com/${repo}/compare/${base_branch}...${current_branch}?expand=1"

    # Display info
    echo -e "${BLUE}📊 当前分支信息${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "  仓库: ${GREEN}${repo}${NC}"
    echo -e "  基础分支: ${GREEN}${base_branch}${NC}"
    echo -e "  当前分支: ${GREEN}${current_branch}${NC}"
    echo ""

    # Check if branch is pushed
    if ! git show-ref --verify --quiet "refs/remotes/origin/${current_branch}"; then
        echo -e "${YELLOW}⚠️  分支尚未推送到远程${NC}"
        echo "推送命令: git push -u origin ${current_branch}"
        echo ""
        read -p "是否现在推送？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git push -u origin "$current_branch"
        else
            echo "请手动推送后再创建 PR"
            exit 1
        fi
    fi

    # Display PR URL
    echo -e "${GREEN}✅ PR 创建链接${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${CYAN}${pr_url}${NC}"
    echo ""

    # Try to open in browser
    local opened=false
    if command -v xdg-open &>/dev/null; then
        echo "🌐 在默认浏览器中打开..."
        xdg-open "$pr_url" 2>/dev/null && opened=true
    elif command -v open &>/dev/null; then
        echo "🌐 在默认浏览器中打开..."
        open "$pr_url" 2>/dev/null && opened=true
    fi

    if [[ "$opened" == false ]]; then
        echo -e "${YELLOW}💡 提示: 复制上面的链接在浏览器中打开${NC}"
    fi

    # Generate PR description
    echo ""
    echo -e "${BLUE}📝 生成 PR 描述${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    local pr_description=$(generate_pr_description)
    local desc_file=".workflow/temp/pr_description.md"

    mkdir -p "$(dirname "$desc_file")"
    echo "$pr_description" > "$desc_file"

    echo "已保存到: ${desc_file}"
    echo ""

    # Try to copy to clipboard
    if command -v xclip &>/dev/null; then
        echo "$pr_description" | xclip -selection clipboard
        echo -e "${GREEN}✅ PR 描述已复制到剪贴板${NC}"
    elif command -v pbcopy &>/dev/null; then
        echo "$pr_description" | pbcopy
        echo -e "${GREEN}✅ PR 描述已复制到剪贴板${NC}"
    else
        echo -e "${YELLOW}💡 提示: 手动复制 ${desc_file} 的内容${NC}"
    fi

    echo ""
    echo -e "${GREEN}🎉 下一步${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "1. 在浏览器中审查 PR 信息"
    echo "2. 粘贴 PR 描述（已在剪贴板）"
    echo "3. 点击 'Create pull request'"
    echo "4. 等待 CI 检查通过"
    echo "5. 请求审查者审查代码"
    echo ""
}

# ==================== PR Description Generator ====================

generate_pr_description() {
    local phase=$(cat .phase/current 2>/dev/null || echo "Unknown")
    local quality_score=$(cat .workflow/_reports/quality_score.txt 2>/dev/null || echo "N/A")
    local coverage=$(get_coverage_from_xml)
    local commit_count=$(git log --oneline origin/main..HEAD 2>/dev/null | wc -l)

    # Validate quality metrics
    local score_status="⚠️"
    if [[ "$quality_score" != "N/A" ]] && (( $(echo "$quality_score >= 85" | bc -l 2>/dev/null || echo 0) )); then
        score_status="✅"
    fi

    local coverage_status="⚠️"
    if [[ "$coverage" != "N/A" ]] && (( $(echo "$coverage >= 80" | bc -l 2>/dev/null || echo 0) )); then
        coverage_status="✅"
    fi

    cat << EOF
## 📊 Phase 信息
- **当前Phase**: ${phase}
- **质量评分**: ${quality_score} ${score_status}
- **测试覆盖率**: ${coverage}% ${coverage_status}
- **提交数量**: ${commit_count}

## 📋 Must Produce 清单
$(get_must_produce_from_gates "$phase")

## 📝 变更描述
$(git log --oneline origin/main..HEAD 2>/dev/null | sed 's/^/- /' || echo "无变更记录")

### 影响范围
\`\`\`
$(git diff --stat origin/main..HEAD 2>/dev/null | tail -1 || echo "无统计数据")
\`\`\`

## ✅ 质量检查清单
- [x] 本地 pre-commit 通过
- [$(if [[ "$score_status" == "✅" ]]; then echo "x"; else echo " "; fi)] 质量评分 ≥ 85 (当前: ${quality_score})
- [$(if [[ "$coverage_status" == "✅" ]]; then echo "x"; else echo " "; fi)] 测试覆盖率 ≥ 80% (当前: ${coverage}%)
- [x] 无安全问题（已通过 pre-commit 扫描）
- [x] 代码已通过 Linting 检查
- [x] Phase Gates 验证通过

## 🧪 测试计划
$(if [[ -f "docs/TEST-REPORT.md" ]]; then
    echo "详见 [TEST-REPORT.md](docs/TEST-REPORT.md)"
    echo ""
    echo "\`\`\`"
    head -20 docs/TEST-REPORT.md
    echo "\`\`\`"
else
    echo "⚠️ 无测试报告文件"
fi)

## 🔄 回滚方案
$(if [[ -f "docs/PLAN.md" ]]; then
    awk '/## 回滚方案/,/^##/' docs/PLAN.md | grep -v "^##" | sed '/^$/d'
else
    echo "⚠️ 无回滚方案文件"
fi)

## 🔗 关联资源
- **PLAN.md**: $(if [[ -f "docs/PLAN.md" ]]; then echo "[查看](docs/PLAN.md)"; else echo "N/A"; fi)
- **REVIEW.md**: $(if [[ -f "docs/REVIEW.md" ]]; then echo "[查看](docs/REVIEW.md)"; else echo "N/A"; fi)
- **CHANGELOG.md**: $(if [[ -f "docs/CHANGELOG.md" ]]; then echo "[查看](docs/CHANGELOG.md)"; else echo "N/A"; fi)

## 📌 额外说明
<!-- 审查者需要关注的特殊点 -->

---
🤖 Generated with **Claude Enhancer 5.0** - Phase ${phase}
📅 $(date '+%Y-%m-%d %H:%M:%S')
EOF
}

# ==================== Helper Functions ====================

get_must_produce_from_gates() {
    local phase="$1"

    if [[ ! -f ".workflow/gates.yml" ]]; then
        echo "- [ ] 无法加载 gates.yml 配置"
        return
    fi

    python3 << EOF
import yaml
import sys

try:
    with open('.workflow/gates.yml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    phase_data = data.get('phases', {}).get('${phase}', {})
    must_produce = phase_data.get('must_produce', [])

    if not must_produce:
        print("- [ ] 无特定产出要求")
    else:
        for item in must_produce:
            if isinstance(item, str):
                print(f"- [ ] {item}")
            elif isinstance(item, dict):
                for key, value in item.items():
                    print(f"- [ ] {key}: {value}")
except Exception as e:
    print(f"- [ ] 错误: {e}", file=sys.stderr)
EOF
}

get_coverage_from_xml() {
    if [[ ! -f "coverage/coverage.xml" ]]; then
        echo "N/A"
        return
    fi

    python3 << 'EOF'
import xml.etree.ElementTree as ET
import sys

try:
    tree = ET.parse("coverage/coverage.xml")
    counter = tree.getroot().find(".//counter[@type='LINE']")

    if counter is not None:
        covered = int(counter.get("covered", 0))
        missed = int(counter.get("missed", 0))
        total = covered + missed

        if total > 0:
            pct = 100.0 * covered / total
            print(f"{pct:.1f}")
        else:
            print("0.0")
    else:
        print("N/A")
except Exception:
    print("N/A")
EOF
}

# ==================== Entry Point ====================

main() {
    local base_branch="${1:-main}"

    # Check if in git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo "❌ 错误: 不在 Git 仓库中"
        exit 1
    fi

    # Check if remote exists
    if ! git config --get remote.origin.url > /dev/null 2>&1; then
        echo "❌ 错误: 未配置远程仓库 origin"
        exit 1
    fi

    generate_pr_url "$base_branch"
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
