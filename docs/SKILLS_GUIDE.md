# Claude Enhancer Skills Framework完全指南

**版本**：8.8.0  
**更新日期**：2025-10-31  
**作者**：Claude Code Team

---

## 目录
1. [什么是Skill？](#什么是skill)
2. [Skills vs Hooks的区别](#skills-vs-hooks的区别)
3. [Skills配置](#skills配置)
4. [如何创建新Skill](#如何创建新skill)
5. [7个Skills详解](#7个skills详解)
6. [Skills最佳实践](#skills最佳实践)
7. [Skills调试技巧](#skills调试技巧)

---

## 1. 什么是Skill？

Skill是AI的行为指导文档，定义在特定场景下AI应该如何工作。

**核心特点**：
- 声明式（定义"应该做什么"，不是"如何做"）
- 上下文注入（在AI prompt中添加指导）
- 触发条件（phase_transition、tool_use等）
- YAML格式（易读易维护）

**与Hooks的区别**：
| 对比项 | Skills | Hooks |
|--------|--------|-------|
| 执行方式 | AI读取并遵循 | 脚本自动执行 |
| 输出 | AI行为变化 | 日志/拦截/验证 |
| 语言 | YAML（提示文本） | Bash脚本 |
| 用途 | 指导AI行为 | 自动化检查 |

---

## 2. Skills vs Hooks的区别

### 场景对比

**场景1：Phase 1完成提醒**

**使用Skill**：
```yaml
# phase1-discovery-planning.yml
prompt: |
  Phase 1完成后，告诉用户："请您确认方案，说'我理解了，开始Phase 2'"
  ❌ 不能自动进入Phase 2
```
→ AI读取后会主动询问用户

**使用Hook**：
```bash
# phase1_completion_enforcer.sh
if [[ phase1_complete && phase_not_confirmed ]]; then
    echo "❌ Phase 2 blocked: User confirmation required"
    exit 1
fi
```
→ Hook拦截Phase 2转换

**组合使用**：Skill指导AI行为 + Hook强制执行规则

---

## 3. Skills配置

### 3.1 配置位置

**文件**：`.claude/settings.json`

**结构**：
```json
{
  "skills": [
    {
      "name": "phase1-discovery-planning",
      "path": ".claude/skills/phase1-discovery-planning.yml",
      "enabled": true,
      "priority": 10
    }
  ]
}
```

### 3.2 配置参数

| 参数 | 说明 | 示例 |
|------|------|------|
| name | Skill唯一标识 | "phase1-discovery-planning" |
| path | YAML文件路径 | ".claude/skills/xxx.yml" |
| enabled | 是否启用 | true/false |
| priority | 优先级（1-100） | 10（高优先级） |

### 3.3 触发条件（Trigger）

**phase_transition**：Phase转换时触发
```yaml
trigger:
  phase_transition: "Phase1 → Phase2"
```

**tool_use**：工具使用时触发
```yaml
trigger:
  tool_use: "before_write"
```

**keyword**：关键词匹配触发
```yaml
trigger:
  keyword: ["parallel", "并行执行"]
```

---

## 4. 如何创建新Skill

### 4.1 创建步骤

**Step 1：创建YAML文件**
```bash
touch .claude/skills/my_skill.yml
```

**Step 2：编写Skill定义**
```yaml
name: "my_skill"
description: "My custom skill description"
trigger:
  phase_transition: "Phase2 → Phase3"

prompt: |
  📋 Phase 3: Testing 开始
  
  **测试流程**：
  1. 运行单元测试
  2. 运行集成测试
  3. 验证覆盖率 ≥80%
  
  **完成行为**：
  - 生成测试报告
  - 告诉用户测试结果
```

**Step 3：注册到settings.json**
```json
{
  "skills": [
    {
      "name": "my_skill",
      "path": ".claude/skills/my_skill.yml",
      "enabled": true
    }
  ]
}
```

**Step 4：测试Skill**
```bash
# 验证YAML格式
python3 -c "import yaml; yaml.safe_load(open('.claude/skills/my_skill.yml'))"

# 验证settings.json
jq '.skills[] | select(.name == "my_skill")' .claude/settings.json
```

### 4.2 Skill编写最佳实践

**清晰的指令**：
```yaml
# ✅ 好：明确具体
prompt: |
  创建P1_DISCOVERY.md，必须包含：
  1. Executive Summary（>100行）
  2. Current State Analysis（>200行）
  3. Technical Approach（>300行）

# ❌ 差：模糊不清
prompt: |
  写一些发现文档
```

**可验证的标准**：
```yaml
# ✅ 好：可量化
prompt: |
  验收通过率 ≥90%（116/129项）

# ❌ 差：主观判断
prompt: |
  验收基本通过
```

**禁止行为明确**：
```yaml
# ✅ 好：明确禁止
prompt: |
  ❌ 不能自动进入Phase 2
  ❌ 必须等待用户确认

# ❌ 差：隐式假设
prompt: |
  Phase 1完成后继续
```

---

## 5. 7个Skills详解

### 5.1 phase1-discovery-planning

**作用**：Phase 1完整流程指导（5个substages）

**触发条件**：Phase转换到Phase1

**关键指导**：
- 5个substages必须按顺序完成
- 创建6个交付物（P1_DISCOVERY.md等）
- Phase 1完成必须等待用户确认

**文件位置**：`.claude/skills/phase1-discovery-planning.yml`

**使用示例**：
```
用户："帮我实现并行执行优化"
AI（读取skill后）："好的，我们开始Phase 1。首先检查分支..."
```

---

### 5.2 phase6-acceptance

**作用**：Phase 6验收流程指导

**触发条件**：Phase5 → Phase6转换

**关键指导**：
- 对照ACCEPTANCE_CHECKLIST.md逐项验证
- 生成ACCEPTANCE_REPORT.md
- 通过率≥90%才能进入Phase 7

**文件位置**：`.claude/skills/phase6-acceptance.yml`

---

### 5.3 phase7-closure

**作用**：Phase 7收尾流程指导

**触发条件**：Phase6 → Phase7转换

**关键指导**：
- 执行3个必需脚本（cleanup、version check、phase verify）
- 创建PR（正确流程）
- 禁止直接merge或创建tag

**文件位置**：`.claude/skills/phase7-closure.yml`

---

### 5.4 impact-assessment

**作用**：Impact Assessment执行指导

**触发条件**：Phase 1.4开始

**关键指导**：
- 运行impact_radius_assessor.sh
- 解释评分结果
- 应用Agent推荐

---

### 5.5 parallel-suggester

**作用**：并行执行建议

**触发条件**：Impact Radius ≥50

**关键指导**：
- 建议使用Task tool并行
- 引用STAGES.yml配置
- 单个消息调用多个agents

---

### 5.6 quality-gate

**作用**：质量门禁检查

**触发条件**：Phase 3/4

**关键指导**：
- 静态检查、单元测试、集成测试
- 覆盖率、性能、安全检查
- 不通过禁止进入下一Phase

---

### 5.7 gap-scan

**作用**：Gap扫描和修复

**触发条件**：Phase 6验收<90%

**关键指导**：
- 识别失败项
- 生成修复计划
- 重新验收

---

## 6. Skills最佳实践

### 6.1 Skills组织

**按Phase组织**：
```
.claude/skills/
├── phase1-discovery-planning.yml
├── phase2-implementation.yml
├── phase3-testing.yml
├── phase4-review.yml
├── phase5-release.yml
├── phase6-acceptance.yml
└── phase7-closure.yml
```

**按功能组织**：
```
.claude/skills/
├── parallel-execution/
│   ├── parallel-suggester.yml
│   └── parallel-executor.yml
└── quality/
    ├── quality-gate.yml
    └── gap-scan.yml
```

### 6.2 Skills优先级

**高优先级**（1-30）：核心workflow skills
- phase1-discovery-planning: 10
- phase6-acceptance: 15
- phase7-closure: 20

**中优先级**（31-60）：增强功能skills
- parallel-suggester: 40
- quality-gate: 50

**低优先级**（61-100）：辅助功能skills
- gap-scan: 70

---

## 7. Skills调试技巧

### 7.1 验证Skill加载

```bash
# 查看已加载的skills
jq '.skills[] | select(.enabled == true)' .claude/settings.json

# 验证YAML格式
for skill in .claude/skills/*.yml; do
    echo "Validating $skill"
    python3 -c "import yaml; yaml.safe_load(open('$skill'))"
done
```

### 7.2 测试Skill触发

```bash
# 模拟Phase转换
echo "Phase1" > .phase/current
# 观察AI是否加载phase1-discovery-planning skill

# 检查AI响应中是否包含skill指导内容
```

### 7.3 Skill效果验证

**验收标准**：
- AI行为符合skill定义
- 关键步骤不遗漏
- 禁止行为得到遵守

**示例**：
```
Skill定义："❌ 不能自动进入Phase 2"
AI行为：等待用户确认 ✓
AI行为：自动进入Phase 2 ✗（skill无效）
```

---

**总结**：
- 7个skills覆盖Phase 1-7
- 声明式定义，易于维护
- 与Hooks协同工作
- 清晰的指导和禁止行为

**更多信息**：
- Skills目录：`.claude/skills/`
- 配置文件：`.claude/settings.json`
- 示例：`examples/skills/`
