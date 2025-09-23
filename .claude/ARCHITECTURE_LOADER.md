# 🔄 Claude Enhancer架构文档加载器

> 此文件确保Claude Code能读取所有架构文档
> 放在.claude/目录下，与其他配置文档一起被自动加载

## 📖 架构文档自动加载

当Claude Code需要了解系统架构时，应该读取以下文档：

### 1️⃣ 基础架构（必读）
```bash
# 四层架构定义
cat .claude/ARCHITECTURE/v2.0-FOUNDATION.md

# 层级详细说明
cat .claude/ARCHITECTURE/LAYER-DEFINITION.md
```

### 2️⃣ 开发指南（按需）
```bash
# 添加新Feature时
cat .claude/ARCHITECTURE/GROWTH-STRATEGY.md

# 命名和编码时
cat .claude/ARCHITECTURE/NAMING-CONVENTIONS.md
```

### 3️⃣ 决策历史（理解为什么）
```bash
# 查看所有架构决策
ls .claude/ARCHITECTURE/decisions/*.md
```

## 🎯 快速定位规则

### 判断代码应该放在哪层
```yaml
是核心引擎代码？ → core/
是工作流或策略？ → framework/
是共享服务工具？ → services/
是具体功能实现？ → features/
```

### 判断Feature级别
```yaml
简单工具（<100行）？ → features/basic/
标准功能（需配置）？ → features/standard/
复杂系统（需分层）？ → features/advanced/
```

## 🔍 架构关键信息

### 当前架构版本
- **版本**: v2.0
- **制定日期**: 2025-09-23
- **类型**: 四层智能分层（L0-L3）

### 层级占比
- L0 Core: 5%
- L1 Framework: 15%
- L2 Services: 20%
- L3 Features: 60%+（持续增长）

### 依赖规则
- ✅ 允许：上层调用下层（L3→L2→L1→L0）
- ❌ 禁止：下层依赖上层（L0不能调用L1/L2/L3）

## 📝 执行任务时的检查点

在执行任何架构相关任务前，Claude Code应该：

1. **读取架构文档**
   ```python
   # 伪代码示例
   if task.involves("创建新功能"):
       read(".claude/ARCHITECTURE/GROWTH-STRATEGY.md")
       read(".claude/ARCHITECTURE/NAMING-CONVENTIONS.md")

   if task.involves("重构"):
       read(".claude/ARCHITECTURE/v2.0-FOUNDATION.md")
       read(".claude/ARCHITECTURE/LAYER-DEFINITION.md")
   ```

2. **遵循架构原则**
   - 小feature保持简单
   - 大feature充分组织
   - 保持层级依赖正确

3. **更新实施状态**
   - 如果涉及架构迁移，更新`IMPLEMENTATION-STATUS.md`

## 🚀 智能提示

当用户说：
- "添加新功能" → 查看GROWTH-STRATEGY.md判断级别
- "优化代码结构" → 参考LAYER-DEFINITION.md
- "重构系统" → 读取v2.0-FOUNDATION.md
- "为什么这样设计" → 查看decisions/目录

## 🔒 保护提醒

**ARCHITECTURE目录是永久保护的！**
- 只能增加文档，不能删除
- 修改需要先备份
- 所有架构决策都要记录

---
*这个加载器确保架构文档被正确使用*
*Claude Code应该在需要时主动读取这些文档*