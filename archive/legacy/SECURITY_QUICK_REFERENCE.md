# CI/CD安全快速参考指南

## 🚨 安全状态总览

**当前评分**: 2.5/10  
**目标评分**: 7.0/10  
**生产就绪**: ❌ 需要加固  

---

## ⚡ 快速修复（5分钟）

```bash
# 运行自动修复脚本
./scripts/quick_security_fix.sh

# 这将自动完成：
# ✅ 创建CODEOWNERS
# ✅ 添加security-scan workflow
# ✅ 为现有workflows添加权限配置
# ✅ 生成实施检查清单
```

---

## 🔴 Critical问题（必须立即修复）

### 1. GitHub Actions权限过大

**问题**: 所有workflow默认拥有所有权限  
**风险**: CVSS 8.6 - 恶意PR可以修改代码、泄露secrets

**修复**:
```yaml
# 在每个workflow顶部添加
permissions:
  contents: read
  pull-requests: read
```

### 2. 缺少Branch Protection

**问题**: 可以直接push到main，跳过检查  
**风险**: Critical - 绕过所有质量门禁

**修复**: 在GitHub Settings手动配置
1. Settings > Branches > Add rule
2. Branch pattern: `main`
3. 勾选:
   - Require PR + 2 approvals
   - Require status checks
   - Require Code Owner review
   - Disable force push

---

## 🟠 High问题（本周内修复）

### 3. 缺少CODEOWNERS

**修复**: 已由quick_security_fix.sh创建
```bash
# 编辑.github/CODEOWNERS，替换团队名
# @owner → 你的GitHub用户名
```

### 4. 未防护Fork PR攻击

**修复**: Settings > Actions > General
- Fork workflows: "Require approval for all outside collaborators"
- Workflow permissions: "Read repository contents"

---

## 🟡 Medium问题（本月内修复）

### 5. Checkout不安全

**当前**:
```yaml
- uses: actions/checkout@v3
```

**应改为**:
```yaml
- uses: actions/checkout@v4
  with:
    persist-credentials: false  # 防止token泄露
    fetch-depth: 1              # 浅克隆
```

### 6. 缺少依赖扫描

**修复**: 已由security-scan.yml添加
验证:
```bash
# 创建PR后检查Actions标签
# 应该看到Security-Scan / dependency-scan运行
```

---

## ✅ 验证清单

### 自动完成的
- [x] CODEOWNERS文件存在
- [x] security-scan workflow存在
- [x] workflows有permissions配置
- [x] 备份已创建

### 需要手动完成
- [ ] Branch Protection已配置
- [ ] Fork workflow需要审批
- [ ] Dependabot已启用
- [ ] Secret scanning已启用
- [ ] CODEOWNERS团队名已更新

### 测试验证
- [ ] 创建测试PR验证权限
- [ ] 确认security-scan运行
- [ ] 测试fork PR被限制
- [ ] 验证main分支保护

---

## 📊 配置优先级

### P0 - 立即（今天）
1. 运行 `./scripts/quick_security_fix.sh`
2. 配置Branch Protection（main分支）
3. 更新CODEOWNERS团队名

### P1 - 本周
4. 配置Fork workflow审批
5. 启用Dependabot
6. 启用Secret scanning

### P2 - 本月
7. 添加CodeQL扫描
8. 配置签名commit要求
9. 设置secrets轮换提醒

---

## 🛡️ Secrets安全规则

### ❌ 永远不要
```yaml
# 危险：会在日志中暴露
run: echo "TOKEN=${{ secrets.API_TOKEN }}"
run: curl -H "Auth: ${{ secrets.KEY }}"
```

### ✅ 正确做法
```yaml
# 安全：通过环境变量
env:
  API_TOKEN: ${{ secrets.API_TOKEN }}
run: |
  # GitHub会自动mask $API_TOKEN
  ./deploy.sh
```

### 存储位置
- GitHub Secrets: Settings > Secrets > Actions
- 环境Secrets: Settings > Environments > production

---

## 🔍 安全扫描工具

### 已集成
- ✅ Custom secret patterns (security-scan.yml)
- ✅ npm audit (dependency-scan)

### 推荐添加
- TruffleHog - 历史secrets扫描
- Gitleaks - Git secrets检测
- Snyk - 高级依赖扫描
- CodeQL - 静态代码分析

---

## 🚀 GitHub Settings配置指南

### 1. Branch Protection
```
Settings > Branches > Add rule

Branch name: main

✅ Require PR before merging
  ✅ Require 2 approvals
  ✅ Dismiss stale reviews
  ✅ Require Code Owner review

✅ Require status checks
  ✅ CE-Quality-Gates
  ✅ CE-Workflow-Active
  ✅ Security-Scan

✅ Require conversation resolution
✅ Require signed commits
✅ Include administrators
❌ Allow force pushes
❌ Allow deletions
```

### 2. Actions Settings
```
Settings > Actions > General

Fork PR workflows:
  ✅ Require approval for all outside collaborators

Workflow permissions:
  ✅ Read repository contents (IMPORTANT!)
  ❌ Read and write (dangerous)

PR permissions:
  ❌ Allow Actions to create PRs
```

### 3. Security Features
```
Settings > Security & analysis

✅ Dependency graph
✅ Dependabot alerts
✅ Dependabot security updates
✅ Secret scanning
✅ Code scanning (CodeQL)
```

---

## 📈 评分改进路线图

| 阶段 | 行动 | 评分 |
|-----|-----|-----|
| 当前 | 未加固 | 2.5/10 |
| 阶段1 | 运行quick_fix | 4.0/10 |
| 阶段2 | Branch Protection | 5.5/10 |
| 阶段3 | Fork限制 | 6.5/10 |
| 阶段4 | 安全扫描 | 7.5/10 |
| 目标 | 完整配置 | 8.5/10 |

---

## 🆘 常见问题

### Q: 我是个人项目，需要CODEOWNERS吗？
A: 建议保留，全部指向你的用户名。这样有审批记录。

### Q: Fork PR为什么需要审批？
A: 防止恶意代码在你的环境中运行，窃取secrets。

### Q: 签名commit必须吗？
A: 推荐但不强制。可以防止commit伪造。

### Q: 如何测试安全配置？
A: 创建测试PR，尝试：
- 添加.env文件 → 应被security-scan拦截
- 直接push到main → 应被branch protection拦截
- Fork后提PR → 应需要审批

---

## 📞 获取帮助

- 完整报告: `CI_CD_SECURITY_AUDIT_REPORT.md`
- 实施清单: `SECURITY_IMPLEMENTATION_CHECKLIST.md`
- 修复脚本: `scripts/quick_security_fix.sh`

---

**最后更新**: 2025-10-08  
**安全评估人**: Claude Code Security Auditor

