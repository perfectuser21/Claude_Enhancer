# 🎯 Claude Enhancer智能文档加载使用指南

## 🌟 核心理念

**"知道该知道的，忽略该忽略的"**

智能加载策略让Claude Code能够：
- ✅ 精准加载任务相关文档
- ✅ 避免无关文档污染上下文
- ✅ 最小化Token使用
- ✅ 保持高效执行

## 🚀 快速开始

### 1. 基础使用（Python脚本）
```python
from smart_document_loader import SmartDocumentLoader

# 初始化加载器
loader = SmartDocumentLoader()

# 根据任务获取文档
docs, plan = loader.get_documents_for_task(
    user_request="添加用户认证功能",
    current_phase=2,
    max_tokens=30000
)

# 查看加载计划
print(f"加载了 {len(docs)} 个文档")
print(f"预估Token: {plan.estimated_tokens}")
print(f"文档列表: {[doc.path for doc in plan.documents]}")
```

### 2. 命令行使用
```bash
# 分析任务并生成加载计划
python3 .claude/scripts/smart_document_loader.py \
  --task "修复登录bug" \
  --phase 3 \
  --max-tokens 20000

# 查看加载统计
python3 .claude/scripts/smart_document_loader.py --stats
```

## 📊 典型使用场景

### 🟢 场景1：简单Bug修复
```yaml
用户请求: "修复用户登录页面的验证错误"
预期加载:
  - WORKFLOW.md (工作流)
  - AGENT_STRATEGY.md (4个Agent策略)
  - SAFETY_RULES.md (安全规则)
  - agents/test-engineer.md (测试专家)
  - ISSUES_AND_SOLUTIONS.md (问题排查)

Token预估: ~8,000
Agent数量: 4个
```

### 🟡 场景2：新功能开发
```yaml
用户请求: "添加React用户仪表板功能，需要后端API支持"
预期加载:
  - WORKFLOW.md (工作流)
  - AGENT_STRATEGY.md (6个Agent策略)
  - PHASE_AGENT_STRATEGY.md (Phase映射)
  - ARCHITECTURE/GROWTH-STRATEGY.md (Feature分级)
  - ARCHITECTURE/LAYER-DEFINITION.md (分层规则)
  - agents/frontend-engineer.md (前端专家)
  - agents/react-pro.md (React专家)
  - agents/backend-architect.md (后端架构师)
  - agents/api-designer.md (API设计师)

Token预估: ~20,000
Agent数量: 6个
```

### 🔴 场景3：系统架构重构
```yaml
用户请求: "重构整个系统架构，优化分层设计和模块依赖"
预期加载:
  - WORKFLOW.md (工作流)
  - AGENT_STRATEGY.md (8个Agent策略)
  - ARCHITECTURE/v2.0-FOUNDATION.md (基础架构)
  - ARCHITECTURE/LAYER-DEFINITION.md (层级定义)
  - ARCHITECTURE/NAMING-CONVENTIONS.md (命名规范)
  - ARCHITECTURE/decisions/*.md (架构决策)
  - agents/backend-architect.md (后端架构师)
  - agents/database-specialist.md (数据库专家)
  - SELF_CHECK_MECHANISM.md (自检机制)

Token预估: ~35,000
Agent数量: 8个
```

## 🎮 Phase-Based自动加载

### Phase 0: 分支创建
```yaml
自动加载:
  - WORKFLOW.md (了解整体流程)
  - AGENT_STRATEGY.md (选择Agent策略)

可选加载:
  - CLEANUP_STRATEGY.md (如果需要环境清理)

触发条件: 任务开始时
```

### Phase 1: 需求分析
```yaml
自动加载:
  - WORKFLOW.md
  - AGENT_STRATEGY.md
  - PHASE_AGENT_STRATEGY.md (Phase与Agent映射)

条件加载:
  - ARCHITECTURE/GROWTH-STRATEGY.md (如果是复杂任务)

触发条件: Phase >= 1
```

### Phase 2: 设计规划
```yaml
自动加载:
  - 基础文档 (Phase 1的所有文档)

条件加载:
  - ARCHITECTURE/v2.0-FOUNDATION.md (架构设计时)
  - ARCHITECTURE/LAYER-DEFINITION.md (分层决策时)
  - ARCHITECTURE/NAMING-CONVENTIONS.md (命名决策时)

触发条件: Phase >= 2 AND 架构相关关键词
```

### Phase 3: 实现开发
```yaml
自动加载:
  - WORKFLOW.md
  - AGENT_STRATEGY.md
  - SAFETY_RULES.md (安全规则)

技术栈加载:
  - agents/{tech-stack}.md (根据检测到的技术栈)

触发条件: Phase = 3 AND 技术栈检测
```

## 🔍 关键词触发机制

### 架构相关关键词
```yaml
触发词: ["架构", "重构", "设计", "分层", "模块", "系统"]
自动加载:
  - ARCHITECTURE/v2.0-FOUNDATION.md
  - ARCHITECTURE/LAYER-DEFINITION.md

示例:
  "重构用户模块的架构设计" → 加载架构文档
  "优化系统分层结构" → 加载分层文档
```

### 安全相关关键词
```yaml
触发词: ["安全", "权限", "认证", "登录", "加密", "漏洞"]
自动加载:
  - SAFETY_RULES.md
  - agents/security-auditor.md

示例:
  "添加用户认证功能" → 加载安全文档
  "修复权限漏洞" → 加载安全审计文档
```

### 性能相关关键词
```yaml
触发词: ["性能", "优化", "缓存", "慢查询", "内存", "速度"]
自动加载:
  - agents/performance-engineer.md
  - CLEANUP_STRATEGY.md (如果涉及清理优化)

示例:
  "优化数据库查询性能" → 加载性能文档
  "解决内存泄漏问题" → 加载性能和清理文档
```

## 🛠️ 技术栈智能检测

### 前端技术栈
```yaml
检测词: ["react", "vue", "angular", "前端", "UI", "界面", "组件"]
自动加载:
  - agents/frontend-engineer.md (通用前端)
  - agents/react-pro.md (如果检测到React)
  - agents/vue-specialist.md (如果检测到Vue)

示例:
  "创建React用户界面" → 加载React相关文档
  "优化Vue组件性能" → 加载Vue相关文档
```

### 后端技术栈
```yaml
检测词: ["python", "golang", "java", "API", "数据库", "服务器"]
自动加载:
  - agents/backend-engineer.md (通用后端)
  - agents/python-pro.md (如果检测到Python)
  - agents/golang-pro.md (如果检测到Go)
  - agents/database-specialist.md (如果涉及数据库)

示例:
  "用Python实现API接口" → 加载Python和API文档
  "优化Go服务性能" → 加载Go和性能文档
```

## 📈 Token优化策略

### 自动优化规则
```python
# Token使用优化
def optimize_for_tokens(task_analysis, max_tokens):
    if max_tokens <= 15000:  # 简单任务
        return load_minimal_docs(task_analysis)
    elif max_tokens <= 30000:  # 标准任务
        return load_standard_docs(task_analysis)
    else:  # 复杂任务
        return load_comprehensive_docs(task_analysis)
```

### 优先级降级策略
```yaml
超过Token限制时的处理:
1. 保留所有P0文档 (核心工作流)
2. 选择性保留P1文档 (高频使用)
3. 根据相关度排序P2文档
4. 移除P3文档 (可以后续按需加载)

例外规则:
- 安全相关任务: 始终保留SAFETY_RULES.md
- 架构相关任务: 始终保留架构文档
- 特定技术栈: 始终保留对应Agent文档
```

## 🔄 使用最佳实践

### 1. 任务描述优化
```yaml
❌ 模糊描述: "改改代码"
✅ 清晰描述: "修复用户登录API的认证bug"

❌ 过于简单: "优化"
✅ 具体说明: "优化React组件渲染性能，减少重复渲染"

好的描述包含:
- 明确的动作 (修复/添加/优化)
- 具体的组件 (登录API/React组件)
- 技术细节 (认证/渲染性能)
```

### 2. Phase使用建议
```yaml
Phase 0-1: 使用基础文档，了解流程
Phase 2: 如果涉及架构，主动请求架构文档
Phase 3: 确保技术栈正确检测，加载对应Agent
Phase 4-5: 关注测试和安全检查文档
```

### 3. 自定义加载
```python
# 手动指定需要的文档
loader.force_load_documents([
    "ARCHITECTURE/v2.0-FOUNDATION.md",
    "agents/security-auditor.md"
])

# 排除不需要的文档
loader.exclude_documents([
    "CLEANUP_STRATEGY.md"
])
```

## 📊 监控和反馈

### 查看加载统计
```python
stats = loader.get_loading_statistics()
print(f"缓存文档数: {stats['cache_size']}")
print(f"会话文档数: {stats['session_cache_size']}")
print(f"使用模式数: {stats['usage_patterns']}")
```

### 优化建议
```yaml
如果发现:
- Token使用经常超限 → 提高任务描述精确度
- 加载了不相关文档 → 优化关键词描述
- 遗漏了重要文档 → 主动指定所需文档类型

持续改进:
- 记录哪些文档组合最有效
- 分析加载模式，优化触发条件
- 根据实际使用调整文档分类
```

## 🚀 高级功能

### 1. 预测性加载
```python
# 根据当前Phase预测下一步需要的文档
loader.enable_predictive_loading(lookahead=1)
```

### 2. 学习模式
```python
# 启用学习模式，根据历史优化加载策略
loader.enable_learning_mode(confidence_threshold=0.8)
```

### 3. 自定义触发器
```yaml
# 添加自定义触发规则
custom_triggers:
  project_specific:
    keywords: ["项目特定词汇"]
    documents: ["项目特定文档.md"]
```

## 💡 故障排查

### 常见问题
```yaml
Q: 加载了太多不相关文档？
A: 优化任务描述，使用更精确的关键词

Q: 遗漏了重要文档？
A: 检查关键词和技术栈描述，或手动指定

Q: Token使用超限？
A: 降低max_tokens参数，或简化任务描述

Q: 加载速度慢？
A: 检查缓存策略，确保常用文档被缓存
```

### 调试模式
```python
# 启用调试，查看详细加载过程
loader.enable_debug_mode()
docs, plan = loader.get_documents_for_task("你的任务")
```

---

## 🎯 总结

智能文档加载策略通过：
- **Phase驱动** - 根据工作流阶段自动加载
- **关键词匹配** - 根据任务内容智能识别
- **技术栈检测** - 自动加载相关专业文档
- **优先级管理** - 确保重要文档优先加载
- **Token优化** - 避免上下文污染和超限

让Claude Code能够：
- 🎯 **精准加载** - 只加载任务需要的文档
- ⚡ **高效执行** - 最小化Token使用
- 🧠 **智能适配** - 根据情况动态调整
- 📈 **持续优化** - 基于使用模式自我改进

实现真正的"智能文档管理"，让AI助手更加精准和高效！