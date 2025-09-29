# 🛡️ Claude Enhancer 工作流硬闸系统

## 概述

工作流硬闸（Workflow Guard）是Claude Enhancer的强制执行机制，确保所有开发必须遵循标准化工作流程。通过三层防护机制，实现"不激活工作流就无法推送和合并"的硬性约束。

## 🚀 快速开始

### 1. 安装（首次使用）
```bash
# 安装本地hooks
bash setup_hooks.sh

# 验证安装
git config core.hooksPath
# 应显示: hooks/
```

### 2. 开始工作
```bash
# 创建feature分支
git checkout -b feature/my-awesome-feature

# 激活工作流（必须！）
ce start "实现用户认证功能"

# 正常开发
git add .
git commit -m "feat: add user authentication"
git push origin feature/my-awesome-feature
```

### 3. 创建PR
- 推送成功后，在GitHub上创建Pull Request
- CI会自动检查`.workflow/ACTIVE`文件
- 检查通过 ✅ → PR可合并

### 4. 完成工作
```bash
# PR合并后，停用工作流
ce stop

# 工作流会自动归档到 .workflow/archive/
```

## 🔒 三层防护机制

### 第一层：本地Pre-push Hook
- **作用**：推送前检查工作流激活状态
- **覆盖分支**：`feature/*`, `hotfix/*`, `release/*`, `bugfix/*`
- **行为**：未激活 → 拒绝推送

### 第二层：GitHub Actions CI检查
- **工作流**：CE-Workflow-Active
- **检查项**：`.workflow/ACTIVE`文件存在
- **行为**：文件缺失 → CI失败 → PR显示红叉

### 第三层：Branch Protection规则
- **保护分支**：main
- **规则**：必须通过所有CI检查才能合并
- **行为**：CI未通过 → 合并按钮灰色禁用

## 📋 常见场景

### 场景1：忘记激活工作流
```bash
$ git push origin feature/login
❌ 推送被拒绝：工作流未激活
解决方案：
  运行: ce start "你的任务描述"
```

### 场景2：分支不匹配
```bash
$ git push
❌ 推送被拒绝：工作流分支不匹配
当前分支: feature/login
工作流分支: feature/auth
解决方案：
  1. 切换到正确分支: git checkout feature/auth
  2. 或重新激活: ce start "新任务"
```

### 场景3：PR检查失败
```
GitHub PR页面显示:
❌ Check Workflow Active — Failed
原因：.workflow/ACTIVE文件不存在或格式错误
解决：
  1. 本地运行: ce start "任务"
  2. git add .workflow/ACTIVE
  3. git commit -m "chore: add workflow activation"
  4. git push
```

## 🛠️ 命令参考

### ce start
```bash
ce start "任务描述"

# 功能：
# - 生成.workflow/ACTIVE文件
# - 记录ticket、分支、负责人等信息
# - 自动分配ticket ID（T-YYYYMMDD-001格式）

# 注意：
# - 不能在main分支激活
# - 已激活时会更新而非重复创建
```

### ce stop
```bash
ce stop

# 功能：
# - 归档当前ACTIVE文件
# - 清除激活状态
# - 后续推送需要重新激活

# 归档位置：
# .workflow/archive/ACTIVE-时间戳-ticket.txt
```

### setup_hooks.sh
```bash
# 本地安装（仅当前仓库）
bash setup_hooks.sh

# 全局安装（影响所有仓库）
bash setup_hooks.sh --global

# 卸载
bash setup_hooks.sh --uninstall
```

## 🔧 高级功能

### 主分支物理锁定（可选）
```bash
# 锁定main分支（设为只读）
./scripts/lock_main.sh

# 解锁（紧急维护时）
./scripts/unlock_main.sh
# 需要输入 'UNLOCK' 确认
```

**用途**：
- 防止误操作直接修改main分支
- 物理级别保护，即使切换分支也保持
- 仅在紧急热修复时临时解锁

## ❓ 问题排查

### 1. Hook不生效
```bash
# 检查配置
git config core.hooksPath

# 重新安装
bash setup_hooks.sh

# 验证hook文件
ls -la hooks/pre-push
```

### 2. ACTIVE文件格式
正确格式示例：
```
ticket=T-20250129-001
phase=P1
branch=feature/user-auth
owner=John Doe
created_at=2025-01-29 10:30:00
ttl_hours=8
note=实现用户认证功能
```

### 3. 权限问题
```bash
# 确保脚本可执行
chmod +x scripts/ce-start scripts/ce-stop
chmod +x hooks/pre-push
chmod +x setup_hooks.sh
```

## 📊 工作流状态检查

随时查看当前工作流状态：
```bash
# 检查是否激活
[ -f .workflow/ACTIVE ] && echo "✅ 已激活" || echo "❌ 未激活"

# 查看激活信息
cat .workflow/ACTIVE

# 查看历史归档
ls -la .workflow/archive/
```

## 🎯 最佳实践

1. **一个任务一个工作流**：每个功能/修复对应一个工作流激活
2. **及时归档**：PR合并后立即运行`ce stop`
3. **分支命名规范**：使用`feature/`, `hotfix/`, `bugfix/`前缀
4. **提交信息规范**：遵循conventional commits格式
5. **定期清理**：定期清理`.workflow/archive/`中的旧归档

## 💡 提示

- 工作流激活是**强制的**，不是可选的
- Hook拦截是**本地的**，CI检查是**远程的**
- 两者结合形成完整防护，缺一不可
- 遇到问题先检查ACTIVE文件是否存在和正确

---

*Claude Enhancer Workflow Guard - 让规范成为习惯，让习惯成为自然*