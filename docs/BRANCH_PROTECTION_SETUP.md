# Branch Protection 配置指南

**目标**: 配置GitHub分支保护规则，防止直接push到main分支

---

## 快速开始

### 1. 访问设置页面
1. 打开GitHub仓库
2. 点击 **Settings** (设置)
3. 左侧菜单点击 **Branches** (分支)

### 2. 添加保护规则
1. 点击 **Add rule** (添加规则)
2. Branch name pattern: 输入 `main`

### 3. 启用保护选项
勾选以下选项：

#### ✅ 必须启用的选项
- [ ] **Require a pull request before merging** (合并前需要PR)
  - Require approvals: 1
  - Dismiss stale pull request approvals when new commits are pushed

- [ ] **Require status checks to pass before merging** (需要通过状态检查)
  - Require branches to be up to date before merging
  - Status checks (选择以下项目):
    - `ce-gates / branch-protection`
    - `ce-gates / workflow-validation`
    - `ce-gates / security-scan`
    - `ce-gates / code-quality`

- [ ] **Require review from Code Owners** (需要CODEOWNERS审查)

- [ ] **Do not allow bypassing the above settings** (不允许绕过)

#### ⚠️ 可选选项
- [ ] Require linear history (要求线性历史)
- [ ] Include administrators (包含管理员)

### 4. 保存规则
点击 **Create** 或 **Save changes**

---

## 验证配置

### 测试1: 尝试直接push
```bash
git checkout main
echo "test" >> README.md
git add README.md
git commit -m "test: direct push"
git push origin main
```

**预期结果**: Push被拒绝，提示需要通过PR

### 测试2: 创建PR流程
```bash
git checkout -b feature/test
echo "test" >> README.md
git add README.md
git commit -m "feat: test branch protection"
git push origin feature/test
# 在GitHub上创建PR
```

**预期结果**: PR创建成功，显示需要通过CI检查

---

## 故障排查

### 问题1: 无法创建规则
- 检查权限: 需要Admin权限
- 检查仓库类型: 私有仓库的某些功能需要Pro版本

### 问题2: CI检查未显示
- 确认`.github/workflows/ce-gates.yml`已推送
- 检查Workflow是否启用（Actions标签页）
- 查看Workflow运行日志

---

## 高级配置

### 为不同分支设置不同规则
- `main`: 最严格保护
- `develop`: 中等保护
- `feature/*`: 宽松保护

### 紧急修复流程
如需临时禁用保护规则：
1. Settings → Branches
2. 找到规则，点击Edit
3. 临时取消勾选"Require status checks"
4. 修复完成后立即恢复

---

**注意**: Branch Protection是服务端强制，无法通过`--no-verify`绕过
