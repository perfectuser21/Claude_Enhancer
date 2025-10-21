# Acceptance Checklist: v7.0.1 Post-Review Improvements

**Task**: 实施Alex审查报告的4个改进建议
**Version**: v7.0.1
**Created**: 2025-10-21
**Based on**: docs/P2_DISCOVERY.md

---

## 📋 Overview

本checklist定义了v7.0.1的"完成"标准。只有当所有Critical和High优先级条目都打✓时，才能进入Phase 6 验收阶段。

**总计**: 26个验收标准
- Critical: 11个（必须100%完成）
- High: 10个（必须100%完成）
- Medium: 5个（建议完成，可选）

---

## 🔴 Critical Acceptance Criteria (11个)

### AC1: learn.sh鲁棒性增强（6个）

- [ ] **AC1.1**: 0个session时生成空结构（不报错）
  - 测试：`rm -rf .claude/knowledge/sessions/*.json && bash tools/learn.sh`
  - 预期：生成`{meta:{...sample_count:0}, data:[]}`
  - 验证：`jq '.meta.sample_count' .claude/knowledge/metrics/by_type_phase.json` 输出0

- [ ] **AC1.2**: 1个session时正常聚合
  - 测试：创建1个session文件后运行learn.sh
  - 预期：data数组包含1个元素
  - 验证：`jq '.data | length' metrics.json` 输出1

- [ ] **AC1.3**: 100个session时性能<5秒
  - 测试：生成100个session文件，`time bash tools/learn.sh`
  - 预期：real time < 5.0s
  - 验证：性能benchmark报告

- [ ] **AC1.4**: 并发调用10次数据完整性100%
  - 测试：`for i in {1..10}; do bash tools/learn.sh & done; wait`
  - 预期：最终metrics.json格式正确，无损坏
  - 验证：`jq . metrics.json` 不报错

- [ ] **AC1.5**: 输出包含完整meta字段
  - 验证：`jq '.meta | keys | sort' metrics.json`
  - 预期：["last_updated","sample_count","schema","version"]

- [ ] **AC1.6**: data字段是JSON数组（不是对象列表）
  - 验证：`jq '.data | type' metrics.json`
  - 预期：输出"array"
  - **关键修复**：添加`[ ]`包装jq输出

### AC2: post_phase.sh输入验证（5个）

- [ ] **AC2.1**: 空值转换为`[]`
  - 测试：`AGENTS_USED="" bash .claude/hooks/post_phase.sh`
  - 验证：`jq '.agents_used' session.json` 输出`[]`

- [ ] **AC2.2**: 空格分隔字符串转换为JSON数组
  - 测试：`AGENTS_USED="backend test security" bash post_phase.sh`
  - 验证：`jq '.agents_used' session.json` 输出`["backend","test","security"]`

- [ ] **AC2.3**: JSON字符串直接使用
  - 测试：`AGENTS_USED='["a","b"]' bash post_phase.sh`
  - 验证：`jq '.agents_used' session.json` 输出`["a","b"]`

- [ ] **AC2.4**: 向后兼容（现有调用不受影响）
  - 测试：运行现有hooks，检查生成的session.json格式
  - 验证：所有hooks正常工作，无报错

- [ ] **AC2.5**: 生成的session.json格式正确
  - 验证：`jq . .claude/knowledge/sessions/*.json` 全部通过
  - 预期：无parse error

---

## 🟡 High Priority Acceptance Criteria (10个)

### AC3: doctor.sh自愈增强（6个）

- [ ] **AC3.1**: 缺失engine_api.json时自动创建
  - 测试：`rm .claude/engine/engine_api.json && bash tools/doctor.sh`
  - 验证：文件存在 && 包含`{"api":"7.0","min_project":"7.0"}`

- [ ] **AC3.2**: 缺失knowledge目录时自动创建
  - 测试：`rm -rf .claude/knowledge/* && bash tools/doctor.sh`
  - 验证：sessions/, patterns/, metrics/, improvements/ 全部创建

- [ ] **AC3.3**: 缺失schema.json时自动创建
  - 测试：`rm .claude/knowledge/schema.json && bash tools/doctor.sh`
  - 验证：文件存在 && 包含session/pattern/metric定义

- [ ] **AC3.4**: 缺失metrics时自动创建
  - 测试：`rm .claude/knowledge/metrics/*.json && bash tools/doctor.sh`
  - 验证：by_type_phase.json存在 && 是空结构

- [ ] **AC3.5**: 智能退出码
  - 测试1：全部健康 → exit 0
  - 测试2：自动修复5个问题 → exit 0 && 输出"5 issues auto-fixed"
  - 测试3：缺少jq → exit 1 && 输出"manual intervention required"

- [ ] **AC3.6**: 输出友好（Self-Healing Mode标题）
  - 验证：`bash tools/doctor.sh | head -1`
  - 预期：包含"Self-Healing Mode"

### AC4: Meta字段系统化（4个）

- [ ] **AC4.1**: by_type_phase.json包含meta
  - 验证：`jq '.meta' metrics.json | jq -e .`
  - 预期：不为null

- [ ] **AC4.2**: meta.version = "1.0"
  - 验证：`jq -r '.meta.version' metrics.json`
  - 预期：输出"1.0"

- [ ] **AC4.3**: meta.last_updated是ISO 8601格式
  - 验证：`jq -r '.meta.last_updated' metrics.json | grep -E '^\d{4}-\d{2}-\d{2}T'`
  - 预期：匹配成功

- [ ] **AC4.4**: meta.sample_count匹配实际session数
  - 测试：创建5个sessions，运行learn.sh
  - 验证：`jq '.meta.sample_count' metrics.json` 输出5

---

## 🟢 Medium Priority Acceptance Criteria (5个)

### AC5: 代码质量

- [ ] **AC5.1**: 所有改动通过shellcheck
  - 测试：`shellcheck tools/learn.sh .claude/hooks/post_phase.sh tools/doctor.sh`
  - 预期：0 warnings in modified code

- [ ] **AC5.2**: 所有改动通过bash -n验证
  - 测试：`bash -n tools/learn.sh && bash -n post_phase.sh && bash -n doctor.sh`
  - 预期：no errors

- [ ] **AC5.3**: 函数复杂度<150行
  - 验证：检查所有新增/修改函数的行数
  - 预期：无函数超过150行

- [ ] **AC5.4**: 向后兼容（不破坏现有功能）
  - 测试：运行完整test suite
  - 预期：所有现有测试通过

### AC6: 文档和测试

- [ ] **AC6.1**: 更新CHANGELOG.md（v7.0.1条目）
  - 验证：`grep "v7.0.1" CHANGELOG.md`
  - 预期：包含4个改进的说明

---

## 🎯 Phase-Specific Gates

### Phase 3 Quality Gate (必须通过)
- [ ] **运行`scripts/static_checks.sh`通过**
  - Shell语法验证: ✅
  - Shellcheck linting: ✅
  - 代码复杂度检查: ✅

### Phase 4 Quality Gate (必须通过)
- [ ] **运行`scripts/pre_merge_audit.sh`通过**
  - 配置完整性: ✅
  - 版本一致性: ✅ (6个文件 @ v7.0.1)
  - 文档完整性: ✅ (REVIEW.md >100行)
  - 无critical issues: ✅

### Phase 5 Release Requirements
- [ ] **版本文件全部更新到v7.0.1**
  - VERSION
  - .claude/settings.json
  - package.json
  - .workflow/manifest.yml
  - .workflow/SPEC.yaml
  - CHANGELOG.md

- [ ] **根目录文档数量≤7个**
  - 验证：`ls -1 *.md | wc -l`
  - 预期：≤7

---

## 📊 Progress Tracking

**完成度计算**：
```
总进度 = (已完成的Critical数 + 已完成的High数) / (11 + 10) × 100%

验收标准：
- Phase 3 → Phase 4: ≥80% (17/21)
- Phase 4 → Phase 5: ≥90% (19/21)
- Phase 5 → Phase 6: 100% (21/21 - Critical+High全部完成)
```

**当前状态**：
- Critical (11): 0/11 ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜
- High (10): 0/10 ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜
- Medium (5): 0/5 ⬜⬜⬜⬜⬜
- **总进度**: 0% (0/26)

---

## ✅ Sign-off

### Phase 6 Acceptance

**AI验证**（自动）：
- [ ] 所有Critical标准已完成（11/11）
- [ ] 所有High标准已完成（10/10）
- [ ] Phase 3质量门禁通过
- [ ] Phase 4质量门禁通过
- [ ] 版本一致性检查通过

**用户确认**（手动）：
- [ ] 用户确认："没问题"

**完成标志**：
```
╔═══════════════════════════════════════╗
║  ✅ v7.0.1 Acceptance Complete       ║
║  Critical: 11/11  High: 10/10        ║
║  Total: 21/21 (100%)                 ║
║  Status: READY FOR PHASE 7           ║
╚═══════════════════════════════════════╝
```

---

**创建时间**: 2025-10-21
**最后更新**: 2025-10-21
**状态**: Phase 1 - Checklist已定义，等待Phase 2实施
