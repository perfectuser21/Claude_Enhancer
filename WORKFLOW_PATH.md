# Perfect21 工作流执行路径

## 🎯 系统架构概览

```
用户请求
    ↓
Claude Code (入口)
    ↓
Perfect21 动态工作流系统
    ↓
执行与反馈
```

## 📊 核心Features组成

### 主要功能模块（features/目录）

#### 🔹 核心四大模块
1. **learning_loop/learning_feedback** - 学习反馈系统
   - 记录执行历史
   - 分析最佳实践
   - 持续优化建议

2. **sync_point_manager** - 同步点管理器
   - 阶段间协调
   - 验证检查点
   - 确保质量门通过

3. **decision_recorder** - 决策记录器
   - 记录架构决策(ADR)
   - 追踪选择理由
   - 构建知识库

4. **quality_guardian/quality_gates** - 质量保证系统
   - 质量门标准
   - 自动化检查
   - 预防性质量控制

#### 🔹 工作流核心
- **workflow_orchestrator** - 工作流编排器（执行中心）
- **workflow_templates** - 工作流模板系统
- **workflow_engine** - 工作流引擎
- **dynamic_workflow_generator.py** - 动态工作流生成器（新）

#### 🔹 增强功能
- **capability_discovery** - 能力发现（动态扫描features）
- **git_workflow** - Git工作流集成
- **multi_workspace** - 多工作空间管理
- **phase_executor** - 阶段执行器

## 🔄 完整工作流路径

### 1️⃣ 请求接收阶段
```
用户: "用Perfect21实现用户认证系统"
         ↓
Claude Code: 识别关键词 ["实现", "用户", "认证", "系统"]
         ↓
调用: dynamic_workflow_generator.py
```

### 2️⃣ 任务分析阶段
```python
DynamicWorkflowGenerator.analyze_task()
    ├─ 提取关键词: ["用户", "认证", "系统"]
    ├─ 评估复杂度: MEDIUM (2-4个agents)
    ├─ 识别领域: 安全+开发
    └─ 估算规模: ~100行代码, 2个模块
```

### 3️⃣ Agent选择阶段
```python
DynamicWorkflowGenerator.select_agents()
    ├─ 关键词映射:
    │   ├─ "认证" → ["security-auditor"]
    │   ├─ "系统" → ["backend-architect", "api-designer"]
    │   └─ "用户" → ["database-specialist"]
    │
    └─ 优化后: ["security-auditor", "api-designer",
                "backend-architect", "test-engineer"]
```

### 4️⃣ 工作流生成阶段
```python
生成的工作流:
阶段1: 安全设计 [并行]
    ├─ @security-auditor: "分析认证安全需求"
    └─ @api-designer: "设计认证API接口"
    🔴 sync_point_manager: 验证设计一致性

阶段2: 开发实现 [顺序]
    ├─ @backend-architect: "实现认证逻辑"
    └─ @database-specialist: "设计用户表"
    📝 decision_recorder: 记录技术选择

阶段3: 质量保证 [并行]
    ├─ @test-engineer: "编写测试用例"
    └─ @security-auditor: "安全扫描"
    ✅ quality_gates: 检查覆盖率>90%
```

### 5️⃣ 执行阶段
```python
workflow_orchestrator.execute():
    for stage in workflow.stages:
        # 1. 执行前准备
        phase_executor.prepare(stage)

        # 2. 并行/顺序执行agents
        if stage.mode == "PARALLEL":
            results = parallel_executor.run(stage.agents)
        else:
            results = sequential_executor.run(stage.agents)

        # 3. 同步点验证
        if stage.sync_point:
            sync_point_manager.validate(results)

        # 4. 质量门检查
        if stage.quality_gate:
            quality_gates.check(results)

        # 5. 记录决策
        decision_recorder.record(stage, results)
```

### 6️⃣ 学习反馈阶段
```python
learning_feedback.analyze():
    ├─ 记录执行效果
    ├─ 分析性能指标
    ├─ 识别改进点
    └─ 更新最佳实践

capability_discovery.update():
    └─ 扫描新增功能，更新能力列表
```

## 📁 文件系统结构

```
Perfect21/
├── CLAUDE.md                          # 核心定义（不变）
├── CLAUDE_WORKFLOW.md                 # 动态工作流指南
├── WORKFLOW_PATH.md                   # 本文件（执行路径）
│
├── features/                          # 功能模块
│   ├── dynamic_workflow_generator.py  # 🆕 动态生成器
│   │
│   ├── workflow_orchestrator/         # 执行核心
│   │   └── orchestrator.py
│   │
│   ├── sync_point_manager/           # 核心功能1
│   ├── decision_recorder/            # 核心功能2
│   ├── learning_feedback/            # 核心功能3
│   ├── quality_gates/                # 核心功能4
│   │
│   ├── capability_discovery/         # 增强功能
│   ├── git_workflow/                 # Git集成
│   └── multi_workspace/              # 多工作空间
│
└── core/claude-code-unified-agents/  # 56个官方agents
```

## 🎯 执行要点

### Claude Code执行时记住：
1. **分析任务** → 使用dynamic_workflow_generator
2. **生成工作流** → 不用固定模板，动态生成
3. **分阶段执行** → 每阶段都要同步验证
4. **质量检查** → 不达标必须修复
5. **记录学习** → 执行后总结经验

### 关键决策点：
- 任务复杂度 → 决定agent数量
- 关键词匹配 → 决定agent类型
- 依赖关系 → 决定执行顺序
- 质量要求 → 决定验证标准

## 📈 优化循环

```
执行 → 反馈 → 学习 → 优化
  ↑                      ↓
  └──────────────────────┘
```

每次执行都会：
1. 被decision_recorder记录
2. 被learning_feedback分析
3. 优化future执行策略
4. 更新最佳实践

---
> 更新时间: 2025-01-17
> 版本: v2.0 - 动态工作流系统