# 🧠 Claude Enhancer智能文档加载策略

## 🎯 设计目标

1. **避免上下文污染** - 仅加载任务相关文档
2. **最小化Token使用** - 按需加载，精准匹配
3. **保持系统效率** - 快速触发，智能缓存
4. **确保信息完整** - 关键信息不遗漏

## 📊 文档分析与分类

### 🏗️ 第一层：核心架构文档（稀有加载）
**触发条件**：系统重构、架构迁移、新系统设计
```yaml
ARCHITECTURE/:
  - v2.0-FOUNDATION.md          # 四层架构定义
  - LAYER-DEFINITION.md         # L0-L3层详细说明
  - GROWTH-STRATEGY.md          # Feature分级规则
  - NAMING-CONVENTIONS.md       # 命名规范
  - decisions/*.md              # 架构决策记录

触发关键词:
  - "重构"、"架构"、"新功能分层"
  - "添加新模块"、"系统设计"
  - "迁移"、"优化结构"
```

### ⚙️ 第二层：工作流执行文档（常用加载）
**触发条件**：所有开发任务的Phase执行
```yaml
核心执行:
  - WORKFLOW.md                 # 8-Phase工作流
  - AGENT_STRATEGY.md           # 4-6-8策略
  - PHASE_AGENT_STRATEGY.md     # Phase与Agent映射

质量控制:
  - SAFETY_RULES.md             # 安全规则
  - SELF_CHECK_MECHANISM.md     # 自检机制
  - OUTPUT_CONTROL_STRATEGY.md  # 输出控制

触发关键词:
  - 任何编程任务开始
  - "Phase"、"工作流"
  - "Agent"、"并行执行"
```

### 🔧 第三层：专业Agent文档（按需加载）
**触发条件**：特定技术栈或专业领域任务
```yaml
56个专业Agent按技术栈分类:
  后端: backend-architect.md, backend-engineer.md, database-specialist.md
  前端: frontend-engineer.md, react-pro.md, vue-specialist.md
  测试: test-engineer.md, e2e-test-specialist.md, performance-tester.md
  安全: security-auditor.md
  运维: devops-engineer.md, kubernetes-expert.md

触发规则:
  - 任务包含特定技术关键词时加载对应Agent文档
  - Phase 3执行时，根据选择的Agent加载详细说明
```

### 📋 第四层：辅助参考文档（可选加载）
**触发条件**：特殊情况或故障排查
```yaml
故障排查:
  - ISSUES_AND_SOLUTIONS.md     # 问题解决
  - CONSISTENCY_ISSUES.md       # 一致性问题

用户指南:
  - QUICK_START.md              # 快速开始
  - HOW_TO_USE_CLAUDE_ENHANCER.md

系统维护:
  - CLEANUP_STRATEGY.md         # 清理策略
  - PERFORMANCE_OPTIMIZATION_SUMMARY.md
```

## 🎮 智能触发机制

### Phase-Based Loading（阶段触发）
```python
def get_documents_for_phase(phase, task_type, complexity):
    base_docs = ["WORKFLOW.md", "AGENT_STRATEGY.md"]

    if phase == 0:  # 分支创建
        return base_docs

    if phase == 1:  # 需求分析
        return base_docs + ["PHASE_AGENT_STRATEGY.md"]

    if phase == 2:  # 设计规划
        if "新功能" in task_type or "重构" in task_type:
            return base_docs + ["ARCHITECTURE/GROWTH-STRATEGY.md",
                               "ARCHITECTURE/LAYER-DEFINITION.md"]
        return base_docs

    if phase == 3:  # 实现开发
        agent_docs = get_agent_docs_by_complexity(complexity)
        return base_docs + agent_docs + ["SAFETY_RULES.md"]

    # ... 其他Phase
```

### Keyword-Based Loading（关键词触发）
```yaml
触发映射:
  架构相关:
    keywords: ["重构", "架构", "新模块", "分层", "迁移"]
    docs: ["ARCHITECTURE/v2.0-FOUNDATION.md", "ARCHITECTURE/LAYER-DEFINITION.md"]

  安全相关:
    keywords: ["安全", "权限", "认证", "加密", "漏洞"]
    docs: ["SAFETY_RULES.md", "agents/security-auditor.md"]

  性能相关:
    keywords: ["性能", "优化", "缓存", "慢查询", "内存"]
    docs: ["PERFORMANCE_OPTIMIZATION_SUMMARY.md", "agents/performance-engineer.md"]

  测试相关:
    keywords: ["测试", "TDD", "单元测试", "集成测试"]
    docs: ["agents/test-engineer.md", "agents/e2e-test-specialist.md"]
```

### Technology Stack Loading（技术栈触发）
```yaml
前端技术栈:
  React: ["agents/react-pro.md", "agents/frontend-engineer.md"]
  Vue: ["agents/vue-specialist.md", "agents/frontend-engineer.md"]
  Angular: ["agents/angular-expert.md", "agents/frontend-engineer.md"]

后端技术栈:
  Python: ["agents/python-pro.md", "agents/backend-engineer.md"]
  Go: ["agents/golang-pro.md", "agents/backend-engineer.md"]
  Java: ["agents/java-enterprise.md", "agents/backend-engineer.md"]

数据库:
  SQL: ["agents/database-specialist.md"]
  NoSQL: ["agents/database-specialist.md", "agents/data-engineer.md"]
```

## 🚀 加载优先级系统

### P0 - 必须加载（每次任务）
```yaml
核心文档:
  - WORKFLOW.md               # 工作流框架
  - AGENT_STRATEGY.md         # Agent策略
  - SAFETY_RULES.md          # 安全规则

加载时机: 任务开始时立即加载
Cache策略: 永久缓存，除非文档更新
```

### P1 - 高概率加载（大部分任务）
```yaml
常用文档:
  - PHASE_AGENT_STRATEGY.md   # Phase映射
  - SELF_CHECK_MECHANISM.md   # 自检机制
  - OUTPUT_CONTROL_STRATEGY.md # 输出控制

加载时机: Phase 1开始时加载
Cache策略: 会话期间缓存
```

### P2 - 条件加载（特定场景）
```yaml
架构文档:
  - ARCHITECTURE/GROWTH-STRATEGY.md
  - ARCHITECTURE/LAYER-DEFINITION.md

专业Agent:
  - agents/{specific-agent}.md

加载时机: 关键词匹配或Phase 3时
Cache策略: 按需清理
```

### P3 - 罕见加载（故障排查）
```yaml
问题排查:
  - ISSUES_AND_SOLUTIONS.md
  - CONSISTENCY_ISSUES.md

系统维护:
  - CLEANUP_STRATEGY.md

加载时机: 明确请求时
Cache策略: 即用即清
```

## 💡 实现策略

### 智能预测加载
```python
class SmartDocumentLoader:
    def __init__(self):
        self.task_patterns = {
            "新功能开发": ["ARCHITECTURE/GROWTH-STRATEGY.md", "复杂度评估"],
            "Bug修复": ["简单Agent组合", "测试优先"],
            "性能优化": ["performance相关文档", "监控Agent"],
            "安全审计": ["security相关文档", "审计Agent"]
        }

    def predict_needed_docs(self, user_request):
        # 分析用户请求，预测需要的文档
        task_type = self.classify_task(user_request)
        complexity = self.assess_complexity(user_request)
        tech_stack = self.detect_technology(user_request)

        return self.build_loading_plan(task_type, complexity, tech_stack)
```

### 动态缓存策略
```yaml
缓存层级:
  L1 - 内存缓存: 核心文档（WORKFLOW.md等）
  L2 - 会话缓存: 当前任务相关文档
  L3 - 临时缓存: 一次性查询文档

清理策略:
  - L1: 永不清理（除非文档更新）
  - L2: Phase完成后评估是否保留
  - L3: 立即使用后清理
```

### 上下文管理
```python
class ContextManager:
    def __init__(self, max_tokens=50000):
        self.max_tokens = max_tokens
        self.current_docs = []
        self.priority_docs = []

    def add_document(self, doc_path, priority):
        if self.would_exceed_limit(doc_path):
            self.remove_lowest_priority_docs()

        self.load_document(doc_path, priority)

    def optimize_context(self):
        # 移除过时或不相关的文档
        # 保留高优先级和当前Phase相关文档
        pass
```

## 📈 性能指标

### 加载效率目标
```yaml
响应时间:
  - P0文档: <100ms（内存缓存）
  - P1文档: <200ms（会话缓存）
  - P2文档: <500ms（磁盘读取）
  - P3文档: <1s（完整加载）

Token使用:
  - 基础任务: <5,000 tokens
  - 标准任务: <15,000 tokens
  - 复杂任务: <30,000 tokens
  - 架构任务: <50,000 tokens

准确率:
  - 必要文档命中率: >95%
  - 不必要文档过滤率: >90%
  - 用户满意度: >95%
```

### 监控指标
```yaml
实时监控:
  - 文档加载频率统计
  - Token使用量趋势
  - 任务完成率
  - 错误率和重试率

优化反馈:
  - 哪些文档组合效果最好
  - 哪些触发条件需要调整
  - 哪些文档可以合并或拆分
```

## 🔄 持续优化

### 自学习机制
1. **使用模式分析** - 跟踪哪些文档组合最有效
2. **错误模式识别** - 分析加载不足或过度的情况
3. **触发条件优化** - 根据实际使用调整关键词和规则
4. **缓存策略调整** - 基于访问频率优化缓存决策

### 版本迭代
1. **季度回顾** - 分析加载策略效果
2. **规则更新** - 根据新文档和新功能调整
3. **性能优化** - 持续改进加载速度和准确性
4. **用户反馈** - 收集使用体验，改进策略

---

## 🎯 总结

这个智能加载策略通过：
- **分层分类** - 按重要性和使用频率分层
- **智能触发** - 基于Phase、关键词、技术栈的多维触发
- **优先级系统** - P0-P3的加载优先级
- **动态优化** - 缓存策略和持续学习

实现了：
- ✅ 避免上下文污染
- ✅ 最小化Token使用
- ✅ 保持高效执行
- ✅ 确保信息完整

让Claude Code能够智能地"知道该知道的，忽略该忽略的"，提供精准高效的任务执行。