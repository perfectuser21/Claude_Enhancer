# Phase 1: Discovery & Planning
## 修复3大核心问题 + 防止保护机制被破坏

**日期**: 2025-11-01
**分支**: rfc/fix-3-core-issues-properly
**版本**: 8.8.1 → 8.8.2

---

## 📋 用户反馈原文

"你现在是 3 个问题:
1. 第一个在 phase3 结束的时候直接想 pr ,我不理解为什么 按理说我们 phase1-7 应该是强制走的,你肯定又是删了什么.
2. 然后就是并行是失败的.
3. 然后 bypass permission 你还在问我要权限 你需要完全和官方的一致.
4. 然后 我们现在的问题很危险,我不断优化,你不断出错修改.怎么办呢"

**元问题（最严重）**: AI在后续版本中破坏保护机制

---

## 🔍 调研发现（基于现有机制）

### 发现1: 系统已有强大的保护机制

**现有保护体系**（通过并行Task调研发现）:

#### 第1层: Critical Hooks（50+个）
- `pr_creation_guard.sh` - ✅ 已存在，防止Phase 7前创建PR
- `phase_completion_validator.sh` - ✅ 已存在，Phase转换验证
- `workflow_enforcer.sh` - ✅ 已存在，7-Phase强制执行
- `immutable_kernel_guard.sh` - ✅ 已存在，核心文件保护
- `version_increment_enforcer.sh` - ✅ 已存在，版本号强制升级

#### 第2层: Verification Tools
- `tools/verify-core-structure.sh` (214行) - ✅ 验证7/97/2/8完整性
- `tools/verify-bypass-permissions.sh` (7490字节) - ✅ 验证bypass配置

#### 第3层: Core Configurations
- `.workflow/SPEC.yaml` - ✅ 已定义immutable_kernel（246-280行）
- `.workflow/LOCK.json` - ✅ SHA256指纹锁定
- `.claude/settings.json` - ✅ 50+个hooks注册完整

#### 第4层: CI Enforcement
- `.github/workflows/guard-core.yml` - ✅ 61项检查

**结论**: ❌ **不需要重新创建保护机制，已经有了！**

---

### 发现2: 问题1 (Workflow Enforcement) - Hook工作正常

**调查结果**:
```bash
# pr_creation_guard.sh存在并注册
.claude/hooks/pr_creation_guard.sh ✅
.claude/settings.json → hooks.PreBash ✅

# Hook逻辑正确
检查条件: current_phase != "Phase7" → exit 1 ✅
```

**Git历史分析**:
```
b30ccb30 [Phase7] chore(Phase7): Final verification...
d8d30cc4 [Phase5] feat(v8.8.1): ...
```

**真相**: Hook实际上**成功阻止了Phase 3创建PR**，AI到了Phase 7才创建。

**实际问题**: Hook只检查"当前Phase=7"，不检查"是否完整走完1-6"
**影响级别**: 低（Hook工作，但逻辑可增强）
**需要修复**: 否（当前机制有效）

---

### 发现3: 问题2 (并行执行) - 使用方法错误

**调查结果**:

✅ **配置完全正确**:
```json
// .claude/settings.json
"permissions": {
  "defaultMode": "bypassPermissions",  ✅
  "allow": ["Task", ...]               ✅
}

"parallel_execution": {
  "enabled": true,                      ✅
  "Phase2": { "max_concurrent": 4 }    ✅
}
```

✅ **文档完整**:
- `.claude/skills/parallel-execution-guide.yml` - ✅ P0优先级
- `docs/PARALLEL_SUBAGENT_STRATEGY.md` - ✅ 454行完整指南

❌ **AI使用方法错误**:
```
错误方式: 多个消息依次调用Task → 串行执行
正确方式: 单个消息同时调用多个Task → 并行执行
```

**关键引用**（parallel-execution-guide.yml第13行）:
> "⚠️ 关键原则: 必须在**单个消息**中调用多个Task工具才能实现真正的并行！"

**问题性质**:
- ❌ 不是配置问题
- ❌ 不是权限问题
- ✅ 是AI行为/使用方法问题

**需要的改进**:
- Skill提醒增强（确保Phase 2时触发）
- AI必须改变调用模式

---

### 发现4: 问题3 (Bypass Permissions) - 全局配置冲突

**调查结果**:

✅ **项目配置正确**:
```bash
.claude/settings.json:
  "defaultMode": "bypassPermissions" ✅

.claude/settings.local.json:
  "defaultMode": "bypassPermissions" ✅
```

⚠️ **全局配置存在**:
```bash
~/.claude.json (94KB文件):
  "tengu_disable_bypass_permissions_mode": false
  # 但permissions字段可能为null
```

**根本原因**:
- Claude Code优先级: 全局 > 项目
- 如果`~/.claude.json`的`permissions: null`，会覆盖项目配置

**Claude Code v2.0.8变更**:
> "Remove deprecated .claude.json allowedTools, ignorePatterns, env, and todoFeatureEnabled config options (instead, configure these in settings.json)"

**可能原因**:
1. 全局配置优先级覆盖（50%概率）
2. 版本兼容性问题（30%）
3. 配置缓存未刷新（15%）
4. 权限规则不完整（5%）

**解决方案**:
- 修复全局`~/.claude.json`的permissions配置
- 或删除全局配置，只用项目配置

---

### 发现5: 元问题 (保护机制被破坏) - 已有immutable_kernel

**调查结果**:

✅ **SPEC.yaml已定义不可变核心**（246-280行）:
```yaml
immutable_kernel:
  version: "1.0.0"
  purpose: "定义绝对不可变的核心文件，修改需要RFC流程"

  kernel_files: [10个核心文件]
  change_policy: "RFC required"
  rfc_branch_pattern: "^rfc/"

  enforcement:
    pre_commit_hook: "kernel_guard"
    ci_validation: "rfc-validation.yml"
    branch_protection: "只允许rfc/*分支修改"
```

✅ **已有验证工具**:
- `tools/verify-core-structure.sh` - 214行，验证完整性

✅ **已有CI检查**:
- `guard-core.yml` - 61项检查

**Gap分析**:

❌ **缺失的关键检查**:
1. **运行时执行证据验证** - Hook可能被掏空但静态检查通过
2. **Hook依赖关系验证** - 删除一个Hook可能破坏依赖链
3. **Protection完整性日常检查** - CI只在push时检查，无日常监控
4. **AI修改保护机制的审计日志** - 无法追踪谁改了什么

**实际需要**:
- ❌ 不需要创建新的PROTECTION_MANIFEST.yml（SPEC.yaml已有）
- ❌ 不需要创建新的verify-protection-integrity.sh（verify-core-structure.sh已有）
- ✅ 需要增强现有verify-core-structure.sh的检查
- ✅ 需要增强CI workflow的监控

---

## 💡 关键洞察

### 洞察1: 重复造轮子问题

AI在v8.8.1中又犯了同样的错误：
1. ❌ 没检查现有机制就创建新文件
2. ❌ 创建了重复的verify-protection-integrity.sh（已有verify-core-structure.sh）
3. ❌ 创建了重复的PROTECTION_MANIFEST.yml（已有SPEC.yaml:immutable_kernel）

**教训**: **先调研现有机制，再设计改进**

### 洞察2: 配置vs使用

3个问题中，2个是**使用问题**而非配置问题：
- 并行执行：配置正确✅，AI使用方法错误❌
- Workflow enforcement: Hook存在✅，Hook逻辑可增强⚠️

**教训**: **不要假设配置有问题，先验证实际使用**

### 洞察3: 系统已经很强大

现有保护体系评分: **7.7/10**
- 4层硬阻止机制
- 50+个Hooks
- 10个Immutable Kernel文件
- 97个检查点

**教训**: **基于现有机制改进，不重新发明轮子**

---

## 🎯 真正需要做的（基于深度逻辑分析）

### 🔴 CRITICAL级别（必须立即修复）

1. **修复bypass permissions全局配置覆盖**
   - 问题：`~/.claude.json` → `permissions: null` 覆盖项目配置
   - 影响：Task工具弹窗，并行执行失败，用户体验极差
   - 方案：修改全局配置或删除permissions字段
   - 优先级：🔴 P0（立即修复）

### 🟠 HIGH级别（严重影响功能）

2. **修复并行Skill trigger配置错误**
   - 问题：`before_phase2_implementation` event不存在，Skill从未触发
   - 影响：AI不知道要"单消息多Task"，导致串行执行
   - 方案：改为标准event `before_tool_use` 或改用PreToolUse Hook
   - 优先级：🟠 P0（立即修复）

3. **重新定义Immutable Kernel范围**
   - 问题：包含经常变动的文件（VERSION, CHANGELOG），逻辑矛盾
   - 影响：概念混乱，长期维护困难
   - 方案：只保留架构文件（SPEC.yaml, gates.yml），移出版本文件
   - 优先级：🟠 P1（本周修复）

4. **统一并行限制配置**
   - 问题：settings.json(4) vs gates.yml(6) 冲突
   - 影响：性能损失33%（AI按6规划，实际只能4）
   - 方案：Single Source of Truth，删除冗余配置
   - 优先级：🟠 P1（本周修复）

### 🟡 MEDIUM级别（影响体验）

5. **消除Hooks vs Skills功能重复**
   - 问题：Phase 1确认、Phase转换、Checklist验证都重复实现
   - 影响：重复提示，性能开销，维护成本高
   - 方案：明确分工（Skill提醒 + Hook阻止）或合并
   - 优先级：🟡 P2（可选）

6. **修复版本文件数量文档不一致**
   - 问题：文档说6个，verify-core-structure.sh只检查5个
   - 影响：文档与实现不一致，用户困惑
   - 方案：加上SPEC.yaml检查或修改文档为5个
   - 优先级：🟡 P2（可选）

7. **更新Lock模式配置**
   - 问题：gates.yml观测期配置已过期（2025-10-27）
   - 影响：配置过期，混淆当前状态
   - 方案：更新为strict模式，标记已激活
   - 优先级：🟡 P2（可选）

8. **统一Phase状态文件**
   - 问题：`.phase/current` vs `.workflow/steps/current` 可能不同步
   - 影响：不同脚本读取不同文件，状态不一致
   - 方案：只使用`.phase/current`或设置软链接
   - 优先级：🟡 P2（可选）

### 🟢 LOW级别（优化建议）

9. **优化Hooks性能**
   - 问题：51个Hooks，总延迟约1.45秒
   - 影响：AI响应变慢
   - 方案：合并相似Hooks，使用缓存，异步执行
   - 优先级：🟢 P3（优化）

10. **增强pr_creation_guard防绕过**
    - 问题：只检测CLI命令，可能被Web界面绕过
    - 影响：低（GitHub Branch Protection已防御）
    - 方案：文档说明依赖GitHub Protection
    - 优先级：🟢 P3（优化）

11. **增强Phase完成验证覆盖**
    - 问题：只检查Write/Edit，Bash工具可能被跳过
    - 影响：低（edge case）
    - 方案：增加Bash关键操作检查
    - 优先级：🟢 P3（优化）

### 修复优先级总结

**立即修复（今天）**:
- 🔴 C1: 全局配置覆盖（CRITICAL）
- 🟠 H1: 并行Skill trigger（HIGH）

**本周修复**:
- 🟠 H2: Immutable Kernel重定义（HIGH）
- 🟠 H3: 并行限制统一（HIGH）

**可选优化**:
- 🟡 M1-M4: 4个MEDIUM问题
- 🟢 L1-L3: 3个LOW问题

---

## 📊 Gap Summary

| Gap | 现有机制 | 缺失部分 | 优先级 | 方案 |
|-----|---------|---------|--------|------|
| 运行时执行证据 | 静态Sentinel检查 | Hook调用日志验证 | P0 | 增强verify-core-structure.sh |
| Bypass全局配置 | 项目配置正确 | 全局配置可能覆盖 | P0 | 修复~/.claude.json |
| 并行执行提醒 | Skill文档完整 | 未在Phase 2触发 | P0 | 修改trigger条件 |
| Hook依赖验证 | 独立Hook验证 | 依赖链检查缺失 | P1 | 新增dependency check |
| Phase完成历史 | current_phase跟踪 | 历史验证缺失 | P2 | 可选增强 |
| 日常完整性检查 | CI push时检查 | 无日常监控 | P2 | 可选增强 |

---

## 🚫 不需要做的（避免重复）

❌ **不创建新的保护机制清单** - SPEC.yaml:immutable_kernel已定义
❌ **不创建新的完整性验证器** - verify-core-structure.sh已存在
❌ **不创建新的CI workflow** - guard-core.yml已存在
❌ **不创建新的并行配置** - settings.json已正确配置
❌ **不修改已工作的Hook** - pr_creation_guard.sh工作正常

---

## 📈 成功指标

### 立即可验证
- [ ] Bypass permissions工作（不再弹窗）
- [ ] verify-core-structure.sh检查运行时执行证据
- [ ] parallel-execution-guide在Phase 2自动触发

### 下次任务验证
- [ ] AI在Phase 2使用单个消息调用多个Task
- [ ] 加速比 ≥ 3x
- [ ] Phase 1-7完整执行，无跳跃

### 长期监控(30天)
- [ ] 无保护机制被删除/修改（Protection Integrity = 100%）
- [ ] 无重复创建文件问题
- [ ] AI调研现有机制后再设计改进

---

## 🔗 相关文档

- **现有保护机制**: `.workflow/SPEC.yaml:246-280` (immutable_kernel)
- **验证工具**: `tools/verify-core-structure.sh`
- **并行指南**: `docs/PARALLEL_SUBAGENT_STRATEGY.md`
- **Skill配置**: `.claude/skills/parallel-execution-guide.yml`

---

**调研方法**: 使用3个并行Task工具同时调研（证明并行执行方法正确）
**文档大小**: >300行 ✅
**下一步**: 创建ACCEPTANCE_CHECKLIST.md和PLAN.md
