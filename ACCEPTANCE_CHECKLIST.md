# Acceptance Checklist: Fix Workflow Interference

**Task**: 修复AI工作流干扰问题，确保Claude Enhancer项目中任何开发请求都立即进入Phase 1

**Generated**: 2025-10-22 (Phase 1.3: Technical Discovery)
**Branch**: feature/fix-workflow-interference

---

## ✅ Core Acceptance Criteria

### 1. 全局配置修复 (Global Config Fix)
- [ ] `/root/.claude/CLAUDE.md` 中"双模式协作系统"章节已删除
- [ ] 替换为CE专用规则："Claude Enhancer项目 → 立即进入Phase 1"
- [ ] Phase系统统一为"7-Phase (Phase 1-7)"，不再是"8-Phase (P0-P7)"
- [ ] 明确说明：开发任务（开发/实现/创建/优化）= 直接进入Phase 1.2

### 2. 行为验证 (Behavior Validation)
- [ ] 测试对话1: "帮我开发XXX" → AI立即说"好的，进入Phase 1.2需求讨论"
- [ ] 测试对话2: "实现XXX功能" → AI不再写proposal文档，直接进工作流
- [ ] 测试对话3: "优化XXX模块" → AI直接进Phase 1.2，不等触发词
- [ ] 测试对话4: "这是什么？"（纯查询）→ AI直接回答，不进工作流（正确）

### 3. 文档清理 (Document Cleanup)
- [ ] `/tmp/SOLUTION.md` 已归档/删除（临时分析文档）
- [ ] `/tmp/analyze_interference.md` 已归档/删除
- [ ] 不再创建临时proposal/analysis文档在根目录

### 4. 配置一致性 (Config Consistency)
- [ ] 全局配置与项目配置Phase数量一致（7 Phases）
- [ ] 全局配置明确："对于Claude Enhancer项目，遵循项目CLAUDE.md"
- [ ] 创建备份文件：`/root/.claude/CLAUDE.md.backup`

---

## 🧪 Test Scenarios (BDD-Style)

### Scenario 1: 开发请求立即进入工作流
```gherkin
Given AI在Claude Enhancer项目中
When 用户说"帮我开发用户认证功能"
Then AI应该立即响应"好的，进入Phase 1.2需求讨论"
And AI不应该创建任何proposal文档
And AI应该创建feature分支（如果在main分支）
```

### Scenario 2: 纯分析请求不进入工作流
```gherkin
Given AI在Claude Enhancer项目中
When 用户说"为什么会出现这个错误？"
Then AI应该直接分析问题并回答
And AI不应该进入工作流
And AI不应该创建分支
```

### Scenario 3: 配置修改任务本身也走工作流
```gherkin
Given AI在Claude Enhancer项目中
When 用户说"修复配置干扰问题"
Then AI应该进入Phase 1.1检查分支
And AI应该创建feature/fix-workflow-interference分支
And AI应该通过Phase 1-7完成修复
```

---

## 🚫 Anti-Patterns to Avoid

### ❌ 错误行为1: 写临时文档而不是进工作流
```
用户："评估这个方案"
AI: [创建CE_SELF_EVOLUTION_PROPOSAL.md] ← 错误！
应该: 进入Phase 1.3 Technical Discovery
```

### ❌ 错误行为2: 等待触发词
```
用户："帮我实现登录功能"
AI: "您希望进入执行模式吗？" ← 错误！
应该: 立即进入Phase 1.2
```

### ❌ 错误行为3: 在main分支直接创建文件
```
用户："创建一个新工具"
AI: [在main分支Write文件] ← 错误！
应该: Phase 1.1检查分支 → 创建feature分支
```

---

## 📊 Success Metrics

### Quantitative
- **错误率**: 从4次/天 → 0次/周
- **响应时间**: 听到开发请求 → 进入Phase 1 < 1轮对话
- **文档污染**: 根目录.md文件保持≤7个

### Qualitative
- AI理解"开发"、"实现"、"创建"、"优化"都是开发任务
- AI不再询问"是否启动工作流"
- AI能区分开发任务 vs 纯分析任务

---

## 🎯 Definition of Done

**这个任务完成的标准**：

1. ✅ 配置文件已修改并验证
2. ✅ 通过至少3个测试对话验证行为正确
3. ✅ 临时文档已清理
4. ✅ 代码已review并merge到main
5. ✅ 用户确认："没问题，这个干扰解决了"

---

## 📝 Notes

- 这个checklist本身是通过Phase 1.3生成的（meta recursion ✓）
- 修复完成后，这个checklist会在Phase 6用于验收确认
- 如果发现新的acceptance criteria，更新这个文件
