#!/bin/bash
# quick_security_fix.sh
# 快速应用CI/CD关键安全修复

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "🔒 Claude Enhancer - CI/CD Security Quick Fix"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 备份现有workflows
echo "📦 1. Backing up existing workflows..."
BACKUP_DIR=".github/workflows/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
if ls .github/workflows/*.yml 1> /dev/null 2>&1; then
    cp .github/workflows/*.yml "$BACKUP_DIR/"
    echo "   ✅ Backup created: $BACKUP_DIR"
else
    echo "   ⚠️  No workflows to backup"
fi

# 2. 创建CODEOWNERS
echo ""
echo "👥 2. Creating CODEOWNERS..."
mkdir -p .github
cat > .github/CODEOWNERS << 'EOF'
# ═══════════════════════════════════════════════════════════
# Claude Enhancer CODEOWNERS
# ═══════════════════════════════════════════════════════════

# 默认所有者
* @owner

# 🔐 安全关键文件
.github/** @security-team @owner
.github/workflows/** @security-team @devops-team
.git/hooks/** @security-team

# Secrets和环境配置
.env* @security-team
secrets/** @security-team

# 🏗️ 架构关键文件
.claude/** @architect-team @owner
CLAUDE.md @architect-team

# 📦 依赖管理
package.json @security-team @owner
package-lock.json @security-team
requirements.txt @security-team

# 🧪 测试和质量
test/** @qa-team
acceptance/** @qa-team
metrics/** @qa-team

# 📚 文档
docs/** @docs-team
README.md @docs-team @owner
EOF
echo "   ✅ CODEOWNERS created"

# 3. 创建安全扫描workflow
echo ""
echo "🔍 3. Creating security-scan workflow..."
cat > .github/workflows/security-scan.yml << 'EOF'
name: Security-Scan

on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches:
      - main
      - develop

# 🔒 最小权限
permissions:
  contents: read
  security-events: write
  pull-requests: write

jobs:
  secret-scan:
    name: Scan for Secrets
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code (Secure)
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false
          
      - name: Custom Secret Scan
        run: |
          echo "🔍 Scanning for hardcoded secrets..."
          
          ISSUES=0
          
          # 检查AWS密钥
          if git diff HEAD~1..HEAD 2>/dev/null | grep -E '^\+.*AKIA[0-9A-Z]{16}'; then
            echo "::error::AWS Access Key detected!"
            ((ISSUES++))
          fi
          
          # 检查私钥
          if git diff HEAD~1..HEAD 2>/dev/null | grep -E '^\+.*BEGIN (RSA |DSA |EC )?PRIVATE KEY'; then
            echo "::error::Private key detected!"
            ((ISSUES++))
          fi
          
          # 检查高熵字符串（可能是密码/token）
          if git diff HEAD~1..HEAD 2>/dev/null | \
             grep -E '^\+.*(password|token|secret|api_key).*=.*[a-zA-Z0-9]{32,}' | \
             grep -v 'example\|test\|placeholder\|your_'; then
            echo "::warning::Possible hardcoded credential detected"
          fi
          
          if [ $ISSUES -gt 0 ]; then
            echo ""
            echo "❌ Found $ISSUES critical security issues"
            echo "Please remove secrets and use GitHub Secrets instead"
            exit 1
          fi
          
          echo "✅ No secrets detected"
  
  dependency-scan:
    name: Scan Dependencies
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          persist-credentials: false
          
      - name: npm Audit
        if: hashFiles('package.json') != ''
        run: |
          if [ -f "package.json" ]; then
            echo "🔍 Running npm audit..."
            npm audit --audit-level=moderate || echo "::warning::Dependency vulnerabilities found"
          else
            echo "⚠️  No package.json found, skipping"
          fi
EOF
echo "   ✅ security-scan.yml created"

# 4. 更新现有workflows添加权限
echo ""
echo "🔐 4. Adding permissions to existing workflows..."

for workflow in .github/workflows/ce-*.yml; do
    if [ -f "$workflow" ]; then
        # 检查是否已有permissions
        if ! grep -q "^permissions:" "$workflow"; then
            echo "   Updating: $(basename $workflow)"
            
            # 在on:后添加permissions
            awk '/^on:/ { 
                print; 
                print "";
                print "# 🔒 Security: Minimal permissions";
                print "permissions:";
                print "  contents: read";
                print "  pull-requests: read";
                next;
            } 
            { print }' "$workflow" > "${workflow}.tmp"
            
            mv "${workflow}.tmp" "$workflow"
            echo "      ✅ Added permissions"
        else
            echo "   Skipping: $(basename $workflow) (already has permissions)"
        fi
    fi
done

# 5. 更新checkout步骤
echo ""
echo "🔒 5. Securing checkout steps..."

for workflow in .github/workflows/*.yml; do
    if [ -f "$workflow" ]; then
        # 检查是否有checkout但没有persist-credentials
        if grep -q "uses: actions/checkout" "$workflow" && \
           ! grep -A5 "uses: actions/checkout" "$workflow" | grep -q "persist-credentials"; then
            echo "   ⚠️  $(basename $workflow) needs manual review for checkout security"
        fi
    fi
done

# 6. 创建.gitignore补充（如果需要）
echo ""
echo "📝 6. Checking .gitignore..."
if [ -f ".gitignore" ]; then
    if ! grep -q "\.env" .gitignore; then
        echo "   ⚠️  Adding security patterns to .gitignore"
        cat >> .gitignore << 'EOF'

# Security: Environment and Secrets
.env
.env.*
!.env.example
secrets/
*.key
*.pem
EOF
        echo "      ✅ Security patterns added"
    else
        echo "   ✅ .gitignore already configured"
    fi
fi

# 7. 生成安全检查清单
echo ""
echo "📋 7. Generating security checklist..."
cat > SECURITY_IMPLEMENTATION_CHECKLIST.md << 'EOF'
# CI/CD安全实施检查清单

## 🚀 自动完成（通过quick_security_fix.sh）
- [x] 创建CODEOWNERS文件
- [x] 创建security-scan workflow
- [x] 为现有workflows添加permissions
- [x] 备份现有配置

## 📝 需要手动配置（GitHub Web UI）

### Branch Protection（高优先级）
在 Settings > Branches > Branch protection rules:

- [ ] 创建main分支保护规则
  - [ ] Require a pull request before merging
  - [ ] Require approvals: 2
  - [ ] Require review from Code Owners
  - [ ] Require status checks to pass:
    - [ ] CE-Quality-Gates / quality-check
    - [ ] CE-Workflow-Active / check-workflow
    - [ ] Security-Scan / secret-scan
  - [ ] Require conversation resolution
  - [ ] Require signed commits
  - [ ] Include administrators
  - [ ] Disable force pushes
  - [ ] Disable branch deletion

### GitHub Actions设置
在 Settings > Actions > General:

- [ ] Fork pull request workflows: "Require approval for all outside collaborators"
- [ ] Workflow permissions: "Read repository contents and packages permissions"
- [ ] 禁用 "Allow GitHub Actions to create and approve pull requests"

### Security & Analysis
在 Settings > Security & analysis:

- [ ] 启用 Dependabot alerts
- [ ] 启用 Dependabot security updates
- [ ] 启用 Secret scanning
- [ ] 启用 Code scanning (CodeQL)

### 更新CODEOWNERS团队
编辑 .github/CODEOWNERS，替换占位符：

- [ ] @owner → 你的GitHub用户名
- [ ] @security-team → 安全团队（如果有）
- [ ] @devops-team → DevOps团队
- [ ] @architect-team → 架构师团队
- [ ] @qa-team → QA团队
- [ ] @docs-team → 文档团队

如果是个人项目，可以全部替换为你的用户名。

## 🔍 验证步骤

- [ ] 创建测试PR验证权限配置
- [ ] 确认security-scan workflow运行成功
- [ ] 确认fork PR需要审批
- [ ] 测试branch protection是否生效
- [ ] 验证CODEOWNERS审批要求

## 📚 后续优化

- [ ] 添加TruffleHog/Gitleaks扫描
- [ ] 配置Snyk依赖扫描
- [ ] 启用CodeQL SAST扫描
- [ ] 设置secrets轮换提醒
- [ ] 建立安全事件响应流程

---

完成所有检查后，你的CI/CD安全评分将从2.5/10提升至7.0+/10
EOF
echo "   ✅ Checklist created: SECURITY_IMPLEMENTATION_CHECKLIST.md"

# 8. 总结
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Security fixes applied successfully!"
echo ""
echo "📁 Files created/updated:"
echo "   - .github/CODEOWNERS"
echo "   - .github/workflows/security-scan.yml"
echo "   - SECURITY_IMPLEMENTATION_CHECKLIST.md"
echo "   - Updated: .github/workflows/ce-*.yml"
echo ""
echo "📋 Next steps:"
echo "   1. Review: SECURITY_IMPLEMENTATION_CHECKLIST.md"
echo "   2. Configure Branch Protection (GitHub Settings)"
echo "   3. Update CODEOWNERS with your team names"
echo "   4. Test with a PR"
echo ""
echo "📊 Expected security score improvement: 2.5/10 → 7.0/10"
echo ""
echo "📖 Full report: CI_CD_SECURITY_AUDIT_REPORT.md"

