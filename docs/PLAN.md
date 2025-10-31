# Implementation Plan - v8.7.0 Deep Inspection Fixes

**任务**: 修复v8.7.0深度检测发现的问题
**计划日期**: 2025-10-31
**计划者**: Claude (Sonnet 4.5)

## 1. 任务清单 (Task Breakdown)

### Phase 1: Discovery & Planning ✅
- [x] 1.1 执行7-Phase深度检测
- [x] 1.2 发现Layer 8配置gap
- [x] 1.3 发现LOCK.json指纹未更新
- [x] 1.4 创建P1_DISCOVERY.md
- [x] 1.5 创建ACCEPTANCE_CHECKLIST.md
- [x] 1.6 创建IMPACT_ASSESSMENT.md
- [x] 1.7 创建PLAN.md (本文件)

### Phase 2: Implementation
- [ ] 2.1 补充gates.yml branch_protection配置
  - 添加protected_branches
  - 添加required_status_checks (6项)
  - 添加enforce_admins
  - 添加required_pull_request_reviews
- [ ] 2.2 运行tools/update-lock.sh更新指纹
- [ ] 2.3 清理state.json测试数据
- [ ] 2.4 验证YAML语法
- [ ] 2.5 验证JSON格式

### Phase 3: Testing
- [ ] 3.1 运行verify-core-structure.sh
- [ ] 3.2 重新执行Phase 2深度检测（Layer 8）
- [ ] 3.3 重新执行Phase 6深度检测（完整性）
- [ ] 3.4 验证8层防御100%
- [ ] 3.5 验证版本一致性100%

### Phase 4: Review
- [ ] 4.1 Review gates.yml配置完整性
- [ ] 4.2 Review LOCK.json指纹正确性
- [ ] 4.3 Diff检查（只有预期修改）
- [ ] 4.4 创建REVIEW.md

### Phase 5: Release
- [ ] 5.1 确认版本8.7.0不变
- [ ] 5.2 更新CHANGELOG.md（记录修复）
- [ ] 5.3 Commit到RFC分支
- [ ] 5.4 Push到远程

### Phase 6: Acceptance
- [ ] 6.1 对照ACCEPTANCE_CHECKLIST验证
- [ ] 6.2 生成验收报告
- [ ] 6.3 展示给用户
- [ ] 6.4 等待用户确认

### Phase 7: Closure
- [ ] 7.1 清理临时文件
- [ ] 7.2 最终验证
- [ ] 7.3 创建PR
- [ ] 7.4 等待用户说"merge"

## 2. 受影响文件清单 (Affected Files)

### 修改文件 (3个)
1. `.workflow/gates.yml` - 添加branch_protection配置
2. `.workflow/LOCK.json` - 更新指纹
3. `.workflow/state.json` - 清理测试数据

### 新增文件 (4个 - Phase 1文档)
1. `docs/P1_DISCOVERY.md`
2. `.workflow/ACCEPTANCE_CHECKLIST.md`
3. `.workflow/IMPACT_ASSESSMENT.md`
4. `docs/PLAN.md`

### 验证文件 (使用，不修改)
- `tools/verify-core-structure.sh`
- `tools/update-lock.sh`

## 3. 架构设计 (Architecture Design)

### Layer 8 Branch Protection配置结构

```yaml
branch_protection:
  enabled: true
  description: "GitHub服务端分支保护配置（Layer 8防护）"

  protected_branches:
    - main
    - master
    - production

  required_status_checks:
    strict: true  # 要求PR必须基于最新的base分支
    checks:
      - "CE Unified Gates"
      - "Quality Gate (Required Check)"
      - "ce/phase3-static-checks"
      - "ce/phase4-pre-merge-audit"
      - "ce/phase7-final-validation"
      - "Stage 3: Pre-merge Audit (Gate 2)"

  enforce_admins: true  # 管理员也必须遵守规则

  required_pull_request_reviews:
    dismiss_stale_reviews: false
    require_code_owner_reviews: false
    required_approving_review_count: 0  # 个人项目无需审批

  restrictions: null  # 不限制特定用户/团队

  require_linear_history: false
  allow_force_pushes: false
  allow_deletions: false

  block_creations: false
  required_conversation_resolution: false

  # 配置来源
  configured_via: "GitHub Branch Protection API"
  configured_date: "2025-10-29"
  rationale: "防御--no-verify绕过，强制PR流程和CI验证"
```

### LOCK.json更新流程

```
tools/update-lock.sh
  ↓
1. 读取VERSION (8.7.0)
  ↓
2. 计算7个核心文件SHA256
   - SPEC.yaml
   - gates.yml (新指纹)
   - CHECKS_INDEX.json
   - workflow_validator_v97.sh
   - pre_merge_audit.sh
   - static_checks.sh
   - verify-core-structure.sh
  ↓
3. 生成LOCK.json
   {
     "version": "8.7.0",
     "lock_mode": "soft",
     "key_files_sha256": {...}
   }
  ↓
4. 验证JSON格式
```

## 4. 技术选型 (Technology Stack)

**工具选型**:
- `tools/update-lock.sh` - LOCK.json指纹更新（已存在）
- `tools/verify-core-structure.sh` - 完整性验证（已存在）
- `jq` - JSON处理
- `yq` - YAML处理（如需）

**无需新依赖**

## 5. 风险识别与缓解 (Risk Management)

### 风险1: YAML语法错误
- **概率**: 极低
- **影响**: 中等（gates.yml解析失败）
- **缓解**: 使用IDE/编辑器YAML验证，commit前检查

### 风险2: LOCK.json更新失败
- **概率**: 极低
- **影响**: 高（阻止commit）
- **缓解**: 工具update-lock.sh已测试，失败会有清晰错误

### 风险3: 意外修改其他配置
- **概率**: 极低
- **影响**: 高
- **缓解**: 使用Git diff review，只修改指定行

## 6. 回滚方案 (Rollback Plan)

### 触发条件
- verify-core-structure.sh失败
- CI检查失败
- 用户要求回滚

### 回滚步骤

```bash
# Step 1: Revert commit
git revert <commit-sha>

# Step 2: Force push
git push origin rfc/deep-inspection-v8.7.0-fixes --force

# Step 3: 验证回滚成功
bash tools/verify-core-structure.sh
# 应输出: {"ok":true}
```

### 回滚验证清单
- [ ] verify-core-structure.sh通过
- [ ] git log显示revert commit
- [ ] gates.yml恢复到修改前
- [ ] LOCK.json恢复到修改前

## 7. 测试策略 (Testing Strategy)

### 单元测试
- **工具测试**: update-lock.sh执行成功
- **语法测试**: YAML/JSON格式正确

### 集成测试
- **Phase 2**: Layer 8检测从FAIL变PASS
- **Phase 6**: 完整性检测从FAIL变PASS
- **verify-core-structure.sh**: 返回{"ok":true}

### 验收测试
- 对照ACCEPTANCE_CHECKLIST逐项验证
- 深度检测综合评分≥98/100

## 8. 时间估算 (Timeline)

| Phase | 预估时间 | 实际耗时 |
|-------|---------|---------|
| Phase 1: Discovery | 15分钟 | 已完成 |
| Phase 2: Implementation | 3分钟 | 待执行 |
| Phase 3: Testing | 2分钟 | 待执行 |
| Phase 4: Review | 2分钟 | 待执行 |
| Phase 5: Release | 2分钟 | 待执行 |
| Phase 6: Acceptance | 1分钟 | 待执行 |
| Phase 7: Closure | 1分钟 | 待执行 |
| **总计** | **26分钟** | **进行中** |

## 9. 依赖关系 (Dependencies)

### 前置依赖
- [x] v8.7.0已部署到main
- [x] 深度检测已完成
- [x] 问题已识别

### 并行任务
- 无（任务简单，顺序执行即可）

### 后续任务
- Phase 2-7按顺序执行

## 10. 成功标准 (Success Criteria)

### 功能标准
- [x] gates.yml包含完整branch_protection配置
- [x] LOCK.json指纹更新成功
- [x] state.json测试数据清理

### 质量标准
- [ ] verify-core-structure.sh通过
- [ ] 8层防御100%
- [ ] 完整性验证100%
- [ ] 深度检测评分≥98/100

### 流程标准
- [ ] 所有Phase完成
- [ ] ACCEPTANCE_CHECKLIST 100%
- [ ] 用户确认"没问题"

---

**计划者**: Claude (Sonnet 4.5)
**计划日期**: 2025-10-31T00:38:00Z
**预估总时间**: 26分钟
**风险等级**: 低
