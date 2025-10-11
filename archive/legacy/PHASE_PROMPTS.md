# Phase提示语集合 - 给Claude的精确指令

## 🎯 每个Phase的一句话提示

### P1: Requirements Analysis
```
只编辑 docs/PLAN.md，必须包含"任务清单≥5/受影响文件清单（路径）/回滚方案"三段；禁止改 src/ tests/；输出后自检这三段。
```

### P2: Design Planning
```
只编辑 docs/DESIGN.md（接口/数据/目录草图），如需说明写 docs/SKELETON-NOTES.md；禁止改 src/ tests/。
```

### P3: Implementation
```
只改 src/** 与 docs/CHANGELOG.md（Unreleased 段新增）；按"工单卡"分配 ≤8 个 sub-agents，禁止 sub-agent 调 sub-agent；完成后生成"变更点清单"。
```

### P4: Local Testing
```
只改 tests/** 与 docs/TEST-REPORT.md；新增/改 ≥2 条测试（含≥1条边界），报告列覆盖点；确保 unit + boundary + smoke 能在几分钟内跑绿。
```

### P5: Code Commit
```
按提交规范书写 commit（[P#][role][T-xxx]），不得夹带越权改动；若 Gate 未过，先修再提。
```

### P6: Code Review
```
创建 PR→通过后合并到 main（Squash）；自动打 tag；合并后健康检查；失败自动回滚并生成 ROLLBACK-REPORT.md。
```

## 📋 Phase执行检查清单

### P1 检查项
- [ ] docs/PLAN.md 存在
- [ ] 含"## 任务清单"（≥5条，动词+对象）
- [ ] 含"## 受影响文件清单"（具体路径）
- [ ] 含"## 回滚方案"
- [ ] 未修改 src/ 或 tests/
- [ ] .gates/01.ok 已创建

### P2 检查项
- [ ] docs/DESIGN.md 存在
- [ ] 含接口定义段落
- [ ] 含数据结构段落
- [ ] 含目录草图段落
- [ ] 接口与 PLAN.md 对齐
- [ ] .gates/02.ok 已创建

### P3 检查项
- [ ] src/ 下有代码实现
- [ ] docs/CHANGELOG.md 的 Unreleased 段已更新
- [ ] 活动工单 ≤8（.tickets/*.todo）
- [ ] 未修改非白名单目录
- [ ] 构建/编译通过
- [ ] .gates/03.ok 已创建

### P4 检查项
- [ ] tests/ 下新增/改 ≥2 个测试文件
- [ ] 至少 1 个边界/负例测试
- [ ] docs/TEST-REPORT.md 存在
- [ ] 报告含覆盖率信息
- [ ] unit + boundary + smoke 测试绿
- [ ] .gates/04.ok 已创建

### P5 检查项
- [ ] commit message 符合规范：[P#][role][T-xxx]
- [ ] 无越权文件改动
- [ ] pre-commit hook 通过
- [ ] commit-msg hook 通过
- [ ] .gates/05.ok 已创建

### P6 检查项
- [ ] PR 已创建
- [ ] pre-push hook 通过
- [ ] 合并到 main（Squash merge）
- [ ] post-merge 健康检查通过
- [ ] tag 已创建
- [ ] .gates/06.ok 已创建

## 🚫 Phase权限矩阵

| Phase | 可修改 | 禁止修改 |
|-------|--------|----------|
| P1 | docs/PLAN.md | src/**, tests/**, *.json, *.yml |
| P2 | docs/DESIGN.md, docs/SKELETON-NOTES.md | src/**, tests/** |
| P3 | src/**, docs/CHANGELOG.md | tests/**, .github/**, deployment/** |
| P4 | tests/**, docs/TEST-REPORT.md | src/** (除bug修复) |
| P5 | commit操作 | 新增文件 |
| P6 | PR/merge操作 | 代码改动 |

## 💡 Agent调用原则

### 主Agent职责
1. 分配工单给sub-agents
2. 协调sub-agents工作
3. 汇总结果
4. 更新.tickets/状态

### Sub-agent限制
```
⚠️ 重要：sub-agent 禁止再调用 sub-agent（防止嵌套死循环）
```

### 并发控制
```python
# 工单数限制
P1_MAX = 4  # 轻量级分析
P2_MAX = 6  # 设计协作
P3_MAX = 8  # 最大并发实现
P4_MAX = 6  # 测试执行
P5_MAX = 4  # 提交协调
P6_MAX = 2  # 审查收敛
```

## 📝 Commit Message规范

### 格式
```
[P#][role][T-xxx] 简短描述

详细说明（可选）

Changed:
- 文件1：改动说明
- 文件2：改动说明

Tested:
- 测试1：结果
- 测试2：结果
```

### 示例
```
[P3][backend][T-1234] 实现用户认证API

添加JWT认证中间件和用户登录接口

Changed:
- src/auth/jwt.py: 新增JWT生成和验证
- src/api/login.py: 实现登录端点

Tested:
- tests/test_jwt.py: 全部通过
- tests/test_login.py: 全部通过
```

## 🔄 自动回滚触发条件

1. **post-merge健康检查失败**
   - smoke测试不过
   - 关键文件缺失
   - 配置格式错误

2. **性能退化**
   - 启动时间 > 5秒
   - 响应时间 > 基准2倍

3. **处理流程**
   - 生成 ROLLBACK-REPORT.md
   - 标记工单为 .blocked
   - 回滚到上一个 tag
   - 记录到 .gates/rollback.log

---

*这些提示语可直接复制到Claude的输入中，确保精确执行每个Phase的要求。*