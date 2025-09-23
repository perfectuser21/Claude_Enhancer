# Perfect21 安全Hook系统使用指南

## 🛡️ 安全原则

Perfect21的Hook系统基于以下安全原则设计：
- **只读原则**: Hook不修改用户输入
- **建议原则**: 提供友好建议，不强制执行
- **透明原则**: 所有操作对用户可见
- **可控原则**: 用户可以随时禁用

## 🔧 当前Hook说明

### 1. branch_helper.sh 🌿
**触发时机**: 用户提交任务时  
**功能**: 检查是否在主分支，提醒创建feature分支  
**行为**: 友好提醒，不阻止操作

```bash
🌿 Claude Enhancer 提醒
═══════════════════════════════════════════
📍 当前在主分支: main
💡 建议创建feature分支开发：
  git checkout -b feature/your-feature
```

### 2. smart_agent_selector.sh 🤖  
**触发时机**: 执行Task工具前  
**功能**: 根据任务复杂度建议Agent组合  
**行为**: 输出选择建议，不修改执行

```bash
🤖 Claude Enhancer Agent智能选择 (4-6-8策略)
═══════════════════════════════════════════
📝 任务: 实现用户认证功能...
📊 复杂度: 🟡 标准任务
👥 推荐Agent组合:
  1. backend-architect - 方案设计
  2. backend-engineer - 功能实现
  ...
```

### 3. quality_gate.sh 🎯
**触发时机**: 所有工具使用前  
**功能**: 基本质量检查和安全扫描  
**行为**: 质量评分和建议，不阻止执行

```bash
🎯 质量评分: 85/100
📋 质量建议:
  💡 建议包含明确的动作词
✅ 质量检查通过
```

### 4. Git Hooks ✅📝🚀
**simple_pre_commit.sh**: 提交前代码检查  
**simple_commit_msg.sh**: 提交信息规范检查  
**simple_pre_push.sh**: 推送前验证  

这些是标准的Git Hook，会在相应的Git操作时运行。

## 📖 使用示例

### 正常开发流程
```bash
# 1. 用户提交任务
"实现用户登录功能"

# Hook输出 (不阻止执行)
🌿 当前在主分支: main，建议创建feature分支
🤖 建议使用6个Agent: backend-architect, security-auditor...  
🎯 质量评分: 90/100 ✅

# 2. 用户正常执行，Hook不干预
# Task工具正常运行，完成用户请求
```

### Hook建议处理
用户可以：
- ✅ **采纳建议** - 按Hook建议优化方案
- ✅ **忽略建议** - 继续原计划执行  
- ✅ **部分采纳** - 选择性接受建议
- ✅ **完全禁用** - 关闭Hook系统

## ⚙️ 配置选项

### 禁用特定Hook
编辑 `.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [],  // 禁用所有预执行Hook
    "UserPromptSubmit": []  // 禁用用户提交时Hook
  }
}
```

### 临时禁用所有Hook
```bash
export PERFECT21_HOOKS_DISABLED=true
```

### 调整Hook超时
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "command": "bash .claude/hooks/smart_agent_selector.sh",
        "timeout": 5000,  // 5秒超时
        "blocking": false  // 非阻塞
      }
    ]
  }
}
```

## 🔍 故障排除

### Hook不显示输出
1. 检查Hook文件权限: `ls -la .claude/hooks/`
2. 检查settings.json配置
3. 查看错误日志: `tail -f /tmp/perfect21_hooks.log`

### Hook执行缓慢
1. 检查网络连接 
2. 减少Hook超时时间
3. 临时禁用复杂Hook

### Hook输出混乱
1. 确认只有必要Hook启用
2. 检查Hook脚本语法
3. 重置为默认配置

## 🚫 禁止操作

以下操作是Hook系统**严格禁止**的：
- ❌ 修改用户的原始输入
- ❌ 阻止用户的合法操作  
- ❌ 重定向用户的执行流程
- ❌ 强制要求特定的执行方式
- ❌ 收集用户敏感信息
- ❌ 执行未经授权的系统操作

## ✅ 安全承诺

Perfect21 Hook系统承诺：
1. **尊重用户选择** - 永远以用户意图为准
2. **透明操作** - 所有Hook行为对用户可见
3. **安全边界** - 严格限制Hook权限范围
4. **性能优先** - 不影响系统执行效率
5. **可控可禁** - 用户随时可以禁用

## 📞 支持

如果遇到Hook相关问题：
1. 查看本指南的故障排除部分
2. 检查 `/tmp/perfect21_hooks.log` 日志
3. 临时禁用Hook系统隔离问题
4. 重置为默认安全配置

---
**安全第一，用户至上** - Perfect21 Hook System
