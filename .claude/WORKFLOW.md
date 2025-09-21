# Claude Enhancer 工作流框架

## 核心理念：框架固定，内容灵活

### 固定的框架（5个阶段）

```
┌──────────────────────────────────────────┐
│  Phase 1: 需求分析 (Requirements)         │
│  理解要做什么，为什么要做                  │
└────────────────┬─────────────────────────┘
                 ↓
┌──────────────────────────────────────────┐
│  Phase 2: 设计规划 (Design)               │
│  如何实现，技术选型，架构设计              │
└────────────────┬─────────────────────────┘
                 ↓
┌──────────────────────────────────────────┐
│  Phase 3: 实现开发 (Implementation)       │
│  编写代码，实现功能                       │
└────────────────┬─────────────────────────┘
                 ↓
┌──────────────────────────────────────────┐
│  Phase 4: 测试验证 (Testing)              │
│  确保质量，验证功能                       │
└────────────────┬─────────────────────────┘
                 ↓
┌──────────────────────────────────────────┐
│  Phase 5: 文档交付 (Documentation)        │
│  使用说明，部署指南                       │
└──────────────────────────────────────────┘
```

### 灵活的内容（根据任务动态调整）

#### 示例1：构建REST API
- Phase 1: 分析API需求、用户场景
- Phase 2: 设计端点、数据模型、认证方案
- Phase 3: 实现控制器、服务层、数据层
- Phase 4: 单元测试、集成测试、性能测试
- Phase 5: API文档、部署配置

#### 示例2：优化数据库查询
- Phase 1: 分析慢查询、性能瓶颈
- Phase 2: 设计索引策略、查询优化方案
- Phase 3: 实现索引、重写查询、缓存
- Phase 4: 基准测试、负载测试
- Phase 5: 优化报告、维护指南

#### 示例3：修复安全漏洞
- Phase 1: 分析漏洞影响、攻击向量
- Phase 2: 设计修复方案、防护策略
- Phase 3: 实现补丁、加固代码
- Phase 4: 安全测试、渗透测试
- Phase 5: 安全报告、更新日志

### Agent选择原则

**不是固定组合，而是根据需要动态选择：**

```javascript
// 伪代码示例
function selectAgents(task) {
    const agents = [];

    // 根据任务内容动态选择
    if (task.includes("API")) {
        agents.push("api-designer");
    }
    if (task.includes("数据库")) {
        agents.push("database-specialist");
    }
    if (task.includes("安全")) {
        agents.push("security-auditor");
    }
    if (task.includes("性能")) {
        agents.push("performance-engineer");
    }

    // 基础Agent（通常都需要）
    if (needsArchitecture) {
        agents.push("backend-architect");
    }
    if (needsTesting) {
        agents.push("test-engineer");
    }

    return agents;
}
```

### Git集成（固定流程）

```bash
# 1. 开发分支
git checkout -b feature/your-feature

# 2. 开发过程（5个Phase）
# ... 代码实现 ...

# 3. 提交（触发pre-commit检查）
git add .
git commit -m "feat: 完成功能开发"

# 4. 推送（触发pre-push检查）
git push origin feature/your-feature

# 5. 创建PR
gh pr create

# 6. 合并
git merge
```

### 质量保证机制

#### 自动检查（Git Hooks）
- **pre-commit**: 语法、格式、敏感信息
- **commit-msg**: 提交信息规范
- **pre-push**: 测试通过、无TODO

#### 人工把关
- Code Review
- 功能验证
- 文档审核

## 总结

**框架是骨架，内容是血肉**

- 5个Phase的框架始终不变
- 每个Phase的具体内容根据任务灵活调整
- Agent选择根据实际需要动态决定
- Git工作流保持标准化

这样既有规范的流程，又有足够的灵活性！