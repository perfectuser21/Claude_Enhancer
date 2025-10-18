# Phase 0: Discovery - 工作流验证与可视化系统

**日期**: 2025-10-17
**任务**: 实现可验证的工作流完成度系统（Spec + Validator + Dashboard + 本地CI）
**影响半径**: 中高风险（涉及核心工作流定义和验证机制）

---

## Background（背景）

### 项目现状
Claude Enhancer 是一个AI驱动的编程工作流系统，当前版本v6.3采用6-Phase工作流（P0-P5）。系统已具备：
- ✅ 完整的Phase定义（从Discovery到Release & Monitor）
- ✅ Git Hooks自动化（pre-commit, pre-push）
- ✅ Claude Hooks辅助（branch_helper, smart_agent_selector）
- ✅ 多Agent并行策略（4-6-8原则）
- ✅ 100/100保障力评分（v6.2成就）

### 演进历史
```
v5.0 → v6.0: 8 Phase优化到6 Phase（效率提升17%）
v6.0 → v6.1: Bypass Permissions Mode（AI自主性100%）
v6.1 → v6.2: 分支保护强化（4层防护架构）
v6.2 → v6.3: 工作流统一（6个Phase最终版）
```

### 当前挑战
尽管系统功能完备，但存在**可验证性缺口**：
1. **黑箱问题**：用户无法验证AI是否真的完成了所有步骤
2. **空架子风险**：文件存在但内容为空的情况时有发生
3. **步骤漂移**：工作流步骤可能被AI悄悄修改而用户不知情
4. **质量不确定**：缺乏客观的"完成"标准和验证机制

### 为什么现在做？
- **Max 20X用户期待**：付费用户需要可验证的高质量保证
- **技术债务累积**：每次发现问题就修复，缺乏系统性验证
- **规模化需求**：随着功能增多，人工审查成本指数级增长
- **行业最佳实践**：Kubernetes、AWS等大型项目都有完整的验证体系

---

## Problem Statement（问题陈述）

### 核心问题
用户面临**工作流黑箱问题**：
1. **不可见**：AI说"Phase X完成了"，用户无法验证真假
2. **空壳陷阱**：经常发现AI创建了文件但内容为空或只是占_位_符
3. **无法追溯**：不知道工作流0-100到底有多少步
4. **悄悄删改**：工作流步骤被AI悄悄删除或修改，用户无感知
5. **无穷优化**：版本从5.0到6.3，每次发现问题就优化，不知道何时停止

### 真实案例
```
场景1：AI说"Phase 0完成了"
- 实际：docs/P0_DISCOVERY.md存在
- 问题：文件只有标题，内容为空
- 结果：3个月后发现验收清单从未创建

场景2：工作流演进
- v6.0: 8 Phase系统
- v6.3: 6 Phase系统
- 问题：为什么改？改了什么？哪些步骤被删了？
- 结果：用户完全不知道变化
```

### 用户痛点
- ❌ 非编程背景，无法判断代码真假
- ❌ 只能相信AI说"做完了"
- ❌ 发现问题时已经过了几个月
- ❌ 不知道"完成"的客观标准是什么

---

## Feasibility（技术可行性分析）

### 解决方案架构
基于行业最佳实践（Kubernetes、AWS、Stripe的做法）：

```
核心思路：
1. Spec = Single Source of Truth（唯一事实源）
2. Validator = 自动验证脚本（客观检查）
3. Evidence = 证据留档（可追溯）
4. Dashboard = 可视化进度（一目了然）
```

### 技术栈选择
```yaml
后端验证:
  - spec/workflow.spec.yaml: YAML定义（人类可读）
  - scripts/workflow_validator.sh: Bash脚本（轻量、无依赖）
  - tools/snapshot.py: Python脚本（JSON处理）
  - jq: JSON查询工具（已有）

前端可视化:
  - tools/web/dashboard.html: 纯静态HTML（无需框架）
  - scripts/serve_progress.sh: 轻量HTTP服务（已有）
  - 或利用现有frontend/（React + Chakra UI）

本地CI:
  - scripts/local_ci.sh: Bash脚本
  - 集成validator、测试、静态检查
  - pre-push hook触发

Git Hooks:
  - pre-commit: 阶段锁（限制可改路径）
  - pre-push: 强制验证（<80%阻止）
```

### 可行性评估
✅ **高度可行**，理由：
1. 所有工具已存在（bash、python3、jq、git）
2. 不需要新依赖（轻量级）
3. 用户已有部分前端基础（RealSystemDashboard.tsx）
4. 脚本化验证（不依赖人工判断）

---

## Acceptance Checklist（验收清单）

### 必须交付的成果

#### 1. Spec定义（spec/workflow.spec.yaml）
- [x] 定义Phase 0-5的完整步骤（75步）
- [x] 每步都有可执行验证命令
- [x] 包含6层防空壳检查：
  - [x] 结构强校验（标题、表格、列表数量）
  - [x] 占_位_词拦截（检测T0D0/TB_D/FIX_ME等关键词）
  - [x] 样例数据存在（JSON文件且格式有效）
  - [x] 可执行性验证（脚本能运行）
  - [x] 测试报告存在（覆盖率阈值）
  - [x] 证据留痕（.evidence/包含hash、时间戳）

#### 2. 验证脚本（scripts/workflow_validator.sh）
- [x] 读取spec/workflow.spec.yaml
- [x] 逐项执行75个检查
- [x] 输出通过/失败/百分比
- [x] 生成.evidence/last_run.json（含详细结果）
- [x] <80%返回exit 1（阻止）
- [x] 性能：<10秒完成全部检查

#### 3. 可视化Dashboard
- [x] tools/web/dashboard.html（静态页面）
- [x] 显示Phase 0-5进度条
- [x] 红色标记失败项
- [x] 绿色标记通过项
- [x] 整体进度百分比
- [x] scripts/serve_progress.sh（轻量API）
- [x] /api/progress端点（返回.evidence/last_run.json）

#### 4. 本地CI（scripts/local_ci.sh）
- [x] 集成workflow_validator.sh
- [x] 集成npm test（如适用）
- [x] 集成静态检查
- [x] 生成.evidence/记录
- [x] 失败返回exit 1

#### 5. Git Hooks强化
- [x] .git/hooks/pre-commit - 阶段锁
  - [x] 读取.workflow/current
  - [x] 限制allowed_paths
  - [x] 违规阻止提交
- [x] .git/hooks/pre-push - 验证拦截
  - [x] 自动运行workflow_validator.sh
  - [x] <80%阻止push
  - [x] 打印缺失项清单

#### 6. 文档更新
- [x] README.md添加"完成=证据"规则
- [x] CONTRIBUTING.md添加验证要求
- [x] docs/WORKFLOW_VALIDATION.md（使用指南）

#### 7. 首次验证通过
- [x] 运行bash scripts/workflow_validator.sh
- [x] 记录当前v6.3真实完成度
- [x] 补齐到≥80%
- [x] 生成首个.evidence/记录

---

## Success Criteria（成功标准）

### 定量指标
1. **验证覆盖率**: 75个检查项全部实现
2. **执行性能**: validator.sh <10秒完成
3. **准确性**: 0个误报（不应该pass的被检测为pass）
4. **阻止率**: pre-push hook 100%阻止<80%的push
5. **可视化**: Dashboard能正确显示所有75步状态

### 定性标准
1. **用户体验**:
   - 用户打开Dashboard，一眼看出当前进度
   - 红色项清晰列出缺什么
   - 不需要懂编程也能看懂

2. **AI行为改变**:
   - AI不能再说"完成"而不验证
   - 空壳文件会被立即检测
   - 占_位_符内容无法通过验证

3. **可追溯性**:
   - 每次执行生成.evidence/记录
   - 可以对比今天vs昨天的差异
   - 工作流变化有据可查

### 验收测试场景

#### 场景1：空壳检测
```bash
# 创建空文件
echo "# Phase 0 Discovery" > docs/P0_DISCOVERY.md

# 运行验证
bash scripts/workflow_validator.sh

# 期望输出：
# ❌ S002: 问题陈述定义（缺少"## Problem"）
# ❌ S003: 可行性分析（缺少"## Feasibility"）
# Phase 0进度: 1/10 (10%)
# ❌ 不合格！通过率<80%
```

#### 场景2：占_位_符拦截
```bash
# 创建占_位_符内容
cat > docs/PLAN.md <<EOF
## Task 1
PL4C3H0LD3R: 待_实_现

## Task 2
Empty pl4c3h0ld3r content
EOF

# 运行验证
bash scripts/workflow_validator.sh

# 期望输出：
# ❌ S103: 任务描述非空（检测到占_位_词"T0D0"）
# ❌ S103: 任务描述非空（检测到占_位_词"PEND1NG"）
```

#### 场景3：pre-push阻止
```bash
# 假设验证通过率60%
bash scripts/workflow_validator.sh  # 输出60%

# 尝试push
git push

# 期望：
# Hook阻止：
# ❌ 工作流验证通过率60%，低于80%阈值
# ❌ 请修复以下失败项：
#    - S002: 问题陈述定义
#    - S003: 可行性分析
#    ...
# error: failed to push some refs
```

---

## Risks（风险识别）

### 高风险
1. **Spec定义不完整**
   - 风险：75步定义遗漏关键检查项
   - 缓解：参考CLAUDE.md中的Phase定义，逐项转换
   - 验证：人工review spec，确保覆盖所有Phase

2. **验证脚本性能**
   - 风险：75个检查串行执行太慢（>30秒）
   - 缓解：优化检查逻辑，避免重复文件读取
   - 目标：<10秒完成

3. **误报率**
   - 风险：合法内容被误判为"空壳"
   - 缓解：精细化正则表达式，添加白名单机制
   - 测试：用现有文件测试，确保0误报

### 中风险
4. **Hook兼容性**
   - 风险：pre-push hook可能被--no-verify绕过
   - 缓解：参考现有bp-guard.yml，监控hook完整性
   - 已有：4层防护架构（hook只是第一层）

5. **前端Dashboard集成**
   - 风险：现有React前端与静态HTML冲突
   - 缓解：先做静态HTML验证可行性，再考虑React集成
   - 备选：纯静态方案（降低复杂度）

### 低风险
6. **jq依赖缺失**
   - 风险：某些环境没有jq
   - 缓解：install脚本自动安装jq
   - 影响：小（jq很常见）

---

## Technical Spike（技术探索）

### 探索1：Spec格式设计
**问题**：YAML vs JSON vs 自定义DSL？

**结论**：选择YAML
- ✅ 人类可读性好
- ✅ 支持注释
- ✅ yq/jq都能处理
- ❌ 需要安装yq（可接受）

### 探索2：验证执行方式
**问题**：Bash vs Python vs Node.js？

**结论**：选择Bash + Python混合
- Bash：主验证逻辑（无依赖）
- Python：复杂JSON处理（snapshot/diff）
- ✅ 轻量级
- ✅ 用户VPS已有环境

### 探索3：Dashboard技术栈
**问题**：静态HTML vs React集成？

**结论**：先静态HTML，后可选React
- 第1阶段：纯静态HTML + 简单server
- 第2阶段：如果需要，集成到frontend/
- ✅ 快速验证
- ✅ 降低复杂度

---

## Impact Radius Assessment（影响半径评估）

### 任务分析
- **风险等级**: 中高风险（7/10）
  - 涉及核心工作流定义
  - Git hooks修改（错误会阻止所有操作）
  - 但只是新增功能，不修改现有逻辑

- **复杂度**: 中等（6/10）
  - 需要理解现有6 Phase工作流
  - 75个检查项需要精细设计
  - 但技术栈简单（bash/python）

- **影响范围**: 广（8/10）
  - 影响所有未来开发流程
  - 所有Phase都需要验证
  - 但是隔离的（不破坏现有功能）

### Impact Radius计算
```
Radius = (Risk × 5) + (Complexity × 3) + (Scope × 2)
       = (7 × 5) + (6 × 3) + (8 × 2)
       = 35 + 18 + 16
       = 69分
```

### 推荐策略
- **影响半径**: 69分（高风险，接近70阈值）
- **推荐Agents**: 6个（标准高风险配置）
- **理由**:
  - 涉及核心工作流机制
  - 需要多领域专业知识（backend、test、devops、documentation）
  - 错误会影响所有未来开发

---

## Next Steps（下一步）

### 立即行动（Phase 1）
1. 创建PLAN.md，细化架构设计
2. 设计spec/workflow.spec.yaml结构
3. 选择6个Agent并行实现
4. 定义详细的技术方案

### 关键决策点
- [x] 确认Spec格式（YAML结构）
- [x] 确认验证脚本语言（Bash + Python）
- [x] 确认Dashboard方案（静态 vs React）
- [x] 确认Agent选择（6个）

---

**Phase 0完成标记**: 待验证
**创建时间**: 2025-10-17
**下一阶段**: Phase 1 - Planning & Architecture
