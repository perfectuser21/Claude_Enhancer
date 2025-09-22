# 🚀 如何正确使用Claude Enhancer

## 核心理解

### 1. **Claude Enhancer不会自动触发**

目前的问题：
- Hooks只是**提醒和建议**，不是强制执行
- 需要**你主动告诉我**使用多Agent策略

### 2. **两种集成方式**

#### 方式A：Hook提醒（当前实现）
```
You → Claude Code → Hook提醒 → Claude Code决定是否采纳
```
- 优点：灵活，不会打断工作流
- 缺点：可能被忽略

#### 方式B：强制执行（需要改造）
```
You → Claude Code → Hook阻止 → 必须使用多Agent
```
- 优点：确保遵守规则
- 缺点：可能过于严格

## 📝 正确的使用方法

### 1. **明确要求使用Claude Enhancer**

```
❌ 错误："帮我实现一个登录功能"
✅ 正确："用Claude Enhancer的多Agent策略实现登录功能"
✅ 正确："用8-Phase工作流实现登录功能"
```

### 2. **指定Agent数量**

```
✅ "用6个Agent并行实现这个API"
✅ "这是复杂任务，用8个Agent"
✅ "简单修复，4个Agent就够了"
```

### 3. **触发关键词**

以下关键词会触发Claude Enhancer建议：
- "Claude Enhancer"
- "多Agent"
- "并行执行"
- "8-Phase"
- "工作流"
- "4-6-8策略"

## 🧹 Cleanup集成

### 自动清理触发点

1. **Phase 5（代码提交）**
   ```bash
   # 自动执行
   .claude/scripts/cleanup.sh 5
   ```
   - 删除临时文件
   - 清理调试代码
   - 格式化代码

2. **Phase 7（部署）**
   ```bash
   # 自动执行
   .claude/scripts/cleanup.sh 7
   ```
   - 深度清理
   - 安全扫描
   - 生成部署包

### 手动执行清理

```bash
# 执行当前Phase的清理
.claude/scripts/cleanup.sh

# 执行特定Phase的清理
.claude/scripts/cleanup.sh 5
```

## 📋 完整示例

### 示例1：API开发

```
你："用Claude Enhancer实现一个用户管理API，包括CRUD操作"

我会：
1. 识别为标准任务（6个Agent）
2. 自动调用：
   - backend-architect（架构设计）
   - api-designer（API规范）
   - database-specialist（数据模型）
   - backend-engineer（实现）
   - test-engineer（测试）
   - technical-writer（文档）
3. Phase 5时自动加入cleanup-specialist
```

### 示例2：Bug修复

```
你："用4个Agent快速修复这个登录bug"

我会：
1. 识别为简单任务
2. 并行调用4个Agent
3. 快速完成修复
```

## ⚠️ 当前限制

### 需要手动触发
- Hook只是建议，不强制
- 需要明确说明使用Claude Enhancer
- cleanup需要手动运行脚本

### 解决方案
1. **短期**：明确告诉我使用Claude Enhancer
2. **中期**：改造成强制执行的Hook
3. **长期**：自动识别任务类型并执行

## 🔧 配置优化建议

### 启用强制模式

编辑`.claude/settings.json`：
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",  // 匹配所有工具
        "type": "command",
        "command": "bash .claude/hooks/enforcer.sh",
        "blocking": true  // 阻塞式执行
      }
    ]
  }
}
```

### 自动清理集成

在Git Hooks中集成：
```bash
# .git/hooks/pre-commit
.claude/scripts/cleanup.sh 5

# .git/hooks/pre-push
.claude/scripts/cleanup.sh 7
```

## 💡 最佳实践

1. **开始任务时**
   - 明确说"用Claude Enhancer"
   - 指定Agent数量或复杂度

2. **提交代码前**
   - 运行 `.claude/scripts/cleanup.sh 5`
   - 检查清理报告

3. **部署前**
   - 运行 `.claude/scripts/cleanup.sh 7`
   - 查看 `.claude/cleanup_report.md`

## 🎯 记住

**Claude Enhancer = 多Agent并行 + 8-Phase工作流 + 自动清理**

要激活它，你需要：
1. 明确要求使用
2. 或包含关键词
3. 或手动运行脚本

---

*未来会改进为全自动，但现在需要你的配合！*