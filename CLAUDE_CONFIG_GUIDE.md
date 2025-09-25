# Claude配置管理最佳实践

## 🎯 三层配置架构（防覆盖）

### 1️⃣ 全局个人层（~/.claude/CLAUDE.md）
**永久保存，不会被覆盖**
```markdown
# 我的个人偏好和记忆
- 我是非技术人员，需要详细解释
- 我偏好看到决策选项而不是直接执行
- 我的常用项目：Claude Enhancer 5.0, Claude Enhancer
- 记住：我是Max 20X用户，不在乎Token

# 我的工作习惯
- 喜欢可视化进度条
- 需要看到验证步骤
- 偏好实际代码而非框架
```

### 2️⃣ 项目共享层（/project/CLAUDE.md）
**团队规范，进入Git**
```markdown
# 项目规范
- 使用8-Phase工作流
- 遵循4-6-8 Agent策略
- 代码规范：...
- 分支策略：...
```

### 3️⃣ 项目个人层（/project/CLAUDE.local.md）
**项目特定的个人偏好，gitignore**
```markdown
# 这个项目中我的特殊需求
- 重点关注性能优化
- 使用特定的测试命令
- 我的本地环境配置
```

## 📋 实施步骤

### 步骤1：创建全局个人配置
```bash
# 创建你的永久个人配置
mkdir -p ~/.claude
cat > ~/.claude/CLAUDE.md << 'EOF'
# 🌟 我的全局配置

## 关于我
- 非技术背景
- Max 20X用户
- 需要决策解释

## 我的偏好
- 实现必须可验证
- 提供多个方案选择
- 可视化进度展示

## 防空壳规则
- 禁止只写框架不写实现
- 每个功能必须能测试
- 决策前展示所有选项
EOF
```

### 步骤2：项目配置分离
```bash
# 项目共享配置（进Git）
cat > CLAUDE.md << 'EOF'
# 项目规范
[项目特定规则]
EOF

# 项目个人配置（不进Git）
cat > CLAUDE.local.md << 'EOF'
# 我在这个项目的特殊需求
[个人项目偏好]
EOF

# 添加到.gitignore
echo "CLAUDE.local.md" >> .gitignore
```

### 步骤3：使用#号动态添加
```
在对话中按#键可以让Claude自动将指令加入相应的CLAUDE.md
例如：# 记住这个项目使用pnpm而不是npm
```

## ⚠️ 官方核心原则

1. **保持简洁** - 你在给Claude写，不是给新手开发者
2. **避免冗余** - 文件夹叫components就不用解释是组件
3. **Token高效** - 每次对话都会加载，太长会影响性能
4. **动态维护** - 用#号实时更新，不是一次性设置

## 🔧 配置优先级（官方）

```
最具体 → 最通用
/project/subdir/CLAUDE.md     ← 最高优先级
/project/CLAUDE.md            ← 中等优先级
~/.claude/CLAUDE.md           ← 最低优先级
```

## 💡 实用技巧

### 1. 使用IMPORTANT强调
```markdown
# IMPORTANT: 必须遵守的规则
YOU MUST: 强制要求
```

### 2. 结构化组织
```markdown
## 环境设置
## 编码规范
## 工作流程
## 特殊要求
```

### 3. 定期优化
- 运行prompt improver优化指令
- 定期清理过时内容
- 根据实际使用调整

## 🚨 避免的陷阱

❌ **不要**：
- 写太长的说明文档
- 重复显而易见的内容
- 把它当成README

✅ **要**：
- 只写Claude需要知道的
- 保持指令清晰直接
- 定期更新和维护

## 📊 配置检查清单

```yaml
配置完整性:
  ☐ 全局个人配置已创建
  ☐ 项目配置已分离
  ☐ .gitignore已更新
  ☐ 测试加载优先级
  ☐ 验证不会被覆盖
```

## 🎯 最终验证

运行以下命令验证配置：
```bash
# 检查配置文件
ls -la ~/.claude/CLAUDE.md
ls -la ./CLAUDE.md
ls -la ./CLAUDE.local.md

# 验证Git忽略
git status | grep CLAUDE.local.md
```

---
记住：CLAUDE.md是你的AI助手的"宪法"，把它从通用工具提升为专业的项目感知开发者。