# PR和Branch Protection系统架构

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Claude Enhancer PR & Branch Protection System        │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                    Layer 4: Human Review                       │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │   │
│  │  │  PR Template     │  │   CODEOWNERS     │  │  Reviewers   │ │   │
│  │  │  - Checklist     │→ │  - Auto assign   │→ │  - Approve   │ │   │
│  │  │  - Must-produce  │  │  - By Phase      │  │  - Comment   │ │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────┘ │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                              ↑                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │              Layer 3: Branch Protection (GitHub)               │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │   │
│  │  │  Prevent Push    │  │  Status Checks   │  │  Approvals   │ │   │
│  │  │  - Block main    │  │  - CI jobs       │  │  - Count: 2+ │ │   │
│  │  │  - Force PR      │→ │  - All pass      │→ │  - Owners    │ │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────┘ │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                              ↑                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                Layer 2: CI/CD Pipeline                         │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │   │
│  │  │  Phase Gates     │  │   Tests          │  │  Security    │ │   │
│  │  │  - Validate      │  │  - Unit          │  │  - Scan      │ │   │
│  │  │  - Must-produce  │→ │  - Boundary      │→ │  - Secrets   │ │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────┘ │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                              ↑                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                 Layer 1: Git Hooks (Local)                     │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │   │
│  │  │  pre-commit      │  │  Path Whitelist  │  │  Linting     │ │   │
│  │  │  - Phase check   │  │  - Allow paths   │  │  - ESLint    │ │   │
│  │  │  - Branch check  │→ │  - Gates.yml     │→ │  - Shellcheck│ │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────┘ │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                              ↑                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                  Layer 0: 8-Phase Workflow                     │   │
│  │                                                                 │   │
│  │   P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7 → P0 (循环)          │   │
│  │  Disc  Plan Skel Impl Test Rev  Rel  Mon                      │   │
│  │                                                                 │   │
│  │  gates.yml defines: allow_paths, must_produce, gates          │   │
│  └────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## 数据流图

```
开发者提交代码
      ↓
┌─────────────────────────────────┐
│ 1. Local: Git Hooks             │
│    pre-commit:                  │
│    • 检查分支（禁止main）        │
│    • 验证Phase（必须有.phase）   │
│    • 路径白名单（gates.yml）     │
│    • 安全扫描（无密钥）          │
│    • Linting（无警告）           │
└─────────────┬───────────────────┘
              ↓ PASS
┌─────────────────────────────────┐
│ 2. Push to GitHub               │
│    git push origin feature-branch│
└─────────────┬───────────────────┘
              ↓
┌─────────────────────────────────┐
│ 3. Create PR                    │
│    gh pr create                 │
│    → PR Template自动加载         │
└─────────────┬───────────────────┘
              ↓
┌─────────────────────────────────┐
│ 4. Fill PR Template             │
│    开发者填写:                   │
│    • Phase信息                  │
│    • must_produce清单           │
│    • 测试证据                   │
│    • 回滚方案                   │
└─────────────┬───────────────────┘
              ↓
┌─────────────────────────────────┐
│ 5. CI/CD Triggered              │
│    .github/workflows/ci.yml:    │
│    • validate-phase-gates       │
│    • validate-must-produce      │
│    • run-unit-tests             │
│    • run-boundary-tests         │
│    • run-smoke-tests            │
│    • run-bdd-tests              │
│    • check-security             │
│    • validate-openapi           │
│    • check-performance          │
└─────────────┬───────────────────┘
              ↓ ALL PASS
┌─────────────────────────────────┐
│ 6. CODEOWNERS Auto-assign       │
│    GitHub自动:                  │
│    • 根据文件路径匹配owner       │
│    • 添加为Required reviewers   │
└─────────────┬───────────────────┘
              ↓
┌─────────────────────────────────┐
│ 7. Branch Protection Checks     │
│    GitHub验证:                  │
│    • Status checks ✅           │
│    • Approvals (2+) 等待...     │
│    • Conversations resolved     │
└─────────────┬───────────────────┘
              ↓
┌─────────────────────────────────┐
│ 8. Code Review                  │
│    Reviewers:                   │
│    • 审查代码质量                │
│    • 检查must_produce           │
│    • 验证测试证据                │
│    • 确认回滚方案                │
│    • Approve ✅                 │
└─────────────┬───────────────────┘
              ↓ ALL APPROVED
┌─────────────────────────────────┐
│ 9. Merge PR                     │
│    • Squash merge（保持历史）    │
│    • Delete branch              │
│    • Trigger deploy（如配置）    │
└─────────────────────────────────┘
```

## 组件交互图

```
┌─────────────────┐
│  .phase/current │  ← 当前Phase状态
└────────┬────────┘
         │ 读取
         ↓
┌─────────────────────────────────┐
│  .workflow/gates.yml            │  ← Phase规则定义
│  • allow_paths                  │
│  • must_produce                 │
│  • gates                        │
└────────┬────────────────────────┘
         │ 解析
         ↓
┌─────────────────────────────────┐
│  .git/hooks/pre-commit          │  ← 本地验证
│  • 读取gates.yml                │
│  • 验证路径白名单                │
│  • 检查must_produce（Phase结束） │
└────────┬────────────────────────┘
         │ 通过
         ↓
┌─────────────────────────────────┐
│  GitHub PR                      │
└────────┬────────────────────────┘
         │ 加载
         ↓
┌─────────────────────────────────┐
│  .github/PR_TEMPLATE.md         │  ← PR规范
│  • 读取.phase/current           │
│  • 显示对应must_produce         │
│  • 提供检查清单                  │
└────────┬────────────────────────┘
         │ 触发
         ↓
┌─────────────────────────────────┐
│  .github/workflows/ci.yml       │  ← CI验证
│  • Phase gates验证              │
│  • 测试套件运行                  │
│  • 性能检查                     │
└────────┬────────────────────────┘
         │ 状态
         ↓
┌─────────────────────────────────┐
│  Branch Protection Rules        │  ← 远程保护
│  • Required status checks       │
│  • Required approvals           │
│  • Linear history               │
└────────┬────────────────────────┘
         │ 查询
         ↓
┌─────────────────────────────────┐
│  .github/CODEOWNERS             │  ← 审查分配
│  • 匹配文件路径                  │
│  • 分配审查者                    │
└────────┬────────────────────────┘
         │ 审查
         ↓
┌─────────────────────────────────┐
│  Human Reviewers                │
│  • Code review                  │
│  • Approve                      │
└────────┬────────────────────────┘
         │ 合并
         ↓
┌─────────────────────────────────┐
│  main Branch                    │
└─────────────────────────────────┘
```

## Phase到PR的映射

```
Phase P0 (Discovery)
   ↓
   必须产出:
   • docs/SPIKE.md
   ↓
   允许路径:
   • ** (所有文件，快速实验)
   ↓
   PR Template显示:
   • P0 Discovery清单
   • GO/NO-GO决策要求
   • 风险识别清单

Phase P1 (Plan)
   ↓
   必须产出:
   • docs/PLAN.md (3个标题)
   • 任务清单 ≥5条
   ↓
   允许路径:
   • docs/PLAN.md
   ↓
   PR Template显示:
   • P1 Plan清单
   • 任务清单要求
   • 回滚方案要求

Phase P3 (Implementation)
   ↓
   必须产出:
   • 功能代码（可构建）
   • docs/CHANGELOG.md更新
   ↓
   允许路径:
   • src/**
   • docs/CHANGELOG.md
   ↓
   PR Template显示:
   • P3 Implementation清单
   • 构建验证
   • CHANGELOG更新验证

Phase P4 (Testing)
   ↓
   必须产出:
   • 测试用例 ≥2条
   • docs/TEST-REPORT.md
   ↓
   允许路径:
   • tests/**
   • docs/TEST-REPORT.md
   ↓
   PR Template显示:
   • P4 Testing清单
   • 测试类型清单
   • 测试证据要求
   ↓
   强制执行:
   • pre-push: npm test必须通过

Phase P5 (Review)
   ↓
   必须产出:
   • docs/REVIEW.md
   • APPROVE/REWORK结论
   ↓
   允许路径:
   • docs/REVIEW.md
   ↓
   PR Template显示:
   • P5 Review清单
   • 三段验证
   • 结论要求

Phase P6 (Release)
   ↓
   必须产出:
   • docs/README.md (3段)
   • docs/CHANGELOG.md (版本号)
   • Git tag
   ↓
   允许路径:
   • docs/README.md
   • docs/CHANGELOG.md
   • .tags/**
   ↓
   PR Template显示:
   • P6 Release清单
   • 版本号验证
   • 发布说明要求

Phase P7 (Monitor)
   ↓
   必须产出:
   • observability/slo/slo.yml
   • observability/alerts/
   • docs/MONITORING.md
   ↓
   允许路径:
   • observability/**
   • metrics/**
   • docs/MONITORING.md
   ↓
   PR Template显示:
   • P7 Monitor清单
   • SLO定义要求
   • 告警配置验证
```

## 配置依赖关系

```
.workflow/gates.yml  (Phase规则定义)
         ↓ 被读取
   .git/hooks/pre-commit  (本地验证)
         ↓ 引用
   .github/PULL_REQUEST_TEMPLATE.md  (PR规范)
         ↓ 关联
   .github/workflows/ci-enhanced-5.3.yml  (CI定义)
         ↓ 产生
   Status Checks  (CI结果)
         ↓ 被要求
   Branch Protection Rules  (GitHub配置)
         ↓ 查询
   .github/CODEOWNERS  (审查分配)
         ↓ 添加
   Reviewers  (人工审查)
         ↓ 批准
   Merge  (合并到main)
```

## 文件依赖图

```
项目根目录
├── .phase/
│   └── current  ────────────┐
│                            │ 读取当前Phase
├── .workflow/               │
│   └── gates.yml  ──────────┼──────┐
│                            │      │ Phase规则
├── .git/hooks/              │      │
│   └── pre-commit  ─────────┘      │
│                                   │
├── .github/                        │
│   ├── PULL_REQUEST_TEMPLATE.md ──┘
│   │
│   ├── CODEOWNERS  ────────────────┐
│   │                               │ 审查分配
│   └── workflows/                  │
│       └── ci-enhanced-5.3.yml ────┼──┐
│                                   │  │
├── docs/                           │  │
│   ├── BRANCH_PROTECTION_SETUP.md │  │
│   ├── PR_TEMPLATE_USAGE_GUIDE.md │  │
│   └── PR_AND_BRANCH_PROTECTION_README.md
│                                   │  │
└── scripts/                        │  │
    └── setup_branch_protection.sh ┘  │
                                      │
                 ┌────────────────────┘
                 ↓
         GitHub Branch Protection
         • Required status checks
         • Required approvals
         • CODEOWNERS enforcement
```

## 时序图：完整PR流程

```
Developer  Local Hooks  GitHub  CI/CD  CODEOWNERS  Reviewers  Branch Protection
    │          │          │       │        │           │              │
    ├─ commit──→          │       │        │           │              │
    │          ├─check─→  │       │        │           │              │
    │          ├─PASS──→  │       │        │           │              │
    │←─────────┘          │       │        │           │              │
    │                     │       │        │           │              │
    ├─ push ─────────────→│       │        │           │              │
    │                     │       │        │           │              │
    ├─ create PR ────────→│       │        │           │              │
    │                     ├───trigger CI──→│           │              │
    │                     │       ├─run tests          │              │
    │                     │       ├─run gates          │              │
    │                     │       ├─run security       │              │
    │                     │       ├─PASS──→            │              │
    │                     │       │        │           │              │
    │                     ├───auto assign──→           │              │
    │                     │       │        ├─notify──→ │              │
    │                     │       │        │           │              │
    │                     │       │        │           ├─review code  │
    │                     │       │        │           ├─approve──────→│
    │                     │       │        │           │              │
    │                     │       │        │           │              ├─check status
    │                     │       │        │           │              ├─check approvals
    │                     │       │        │           │              ├─ALLOW MERGE
    │                     │       │        │           │              │
    ├─ merge PR ─────────→│       │        │           │              │
    │                     ├───merge to main             │              │
    │                     ├───delete branch             │              │
    │                     ├───trigger deploy (optional) │              │
    │←─ merge success ────┤       │        │           │              │
```

## 安全层级

```
┌─────────────────────────────────────────────┐
│ Level 5: Emergency Override (Admin Only)    │
│ • --no-verify bypass (留日志)               │
│ • 临时禁用Branch Protection                  │
│ • 仅在紧急情况使用                           │
└─────────────────┬───────────────────────────┘
                  ↓ 正常情况
┌─────────────────────────────────────────────┐
│ Level 4: Human Judgment                     │
│ • Code Review (必须2+ approvals)            │
│ • CODEOWNERS审查 (领域专家)                 │
│ • 对话解决 (全部resolved)                   │
└─────────────────┬───────────────────────────┘
                  ↓ Review通过
┌─────────────────────────────────────────────┐
│ Level 3: Automated Gates (Remote)           │
│ • GitHub Branch Protection (无法绕过)       │
│ • Required status checks (9个CI jobs)       │
│ • Linear history (强制)                     │
└─────────────────┬───────────────────────────┘
                  ↓ CI通过
┌─────────────────────────────────────────────┐
│ Level 2: CI/CD Pipeline                     │
│ • Phase gates验证 (gates.yml)               │
│ • 测试套件 (unit/boundary/smoke)            │
│ • 安全扫描 (无敏感信息)                      │
│ • 性能检查 (不低于预算)                      │
└─────────────────┬───────────────────────────┘
                  ↓ 本地验证
┌─────────────────────────────────────────────┐
│ Level 1: Local Hooks (Developer Machine)    │
│ • pre-commit (路径/安全/linting)            │
│ • commit-msg (消息规范)                     │
│ • pre-push (测试，P4阶段)                   │
└─────────────────┬───────────────────────────┘
                  ↓ 工作流基础
┌─────────────────────────────────────────────┐
│ Level 0: 8-Phase Workflow Foundation        │
│ • .phase/current (当前状态)                 │
│ • .workflow/gates.yml (规则定义)            │
│ • Phase顺序验证 (P0→P1→...→P7)             │
└─────────────────────────────────────────────┘
```

## 配置优先级

```
最严格: claude-enhancer
   ├─ 9个Required status checks
   ├─ 2+ approvals
   ├─ Code Owners required
   ├─ Linear history
   ├─ Signed commits
   ├─ Enforce admins
   └─ Conversation resolution

严格: strict
   ├─ 4个Required status checks
   ├─ 2+ approvals
   ├─ Code Owners required
   ├─ Linear history
   └─ Enforce admins

标准: standard
   ├─ 2个Required status checks
   ├─ 2+ approvals
   └─ Code Owners required

基础: basic
   ├─ 无Required status checks
   └─ 1+ approvals

无保护: (不推荐)
   └─ 任何人可push
```

## 错误恢复路径

```
问题检测
   ├─ CI失败
   │   └─ 查看失败job详情
   │       ├─ Tests failed → 修复测试
   │       ├─ Linting failed → 修复代码
   │       ├─ Security failed → 移除敏感信息
   │       └─ Gates failed → 补充must_produce
   │
   ├─ Branch Protection阻止
   │   └─ 查看具体原因
   │       ├─ Status checks未通过 → 等待CI完成
   │       ├─ Approvals不足 → 等待reviewer
   │       ├─ Conversations未解决 → 回复评论
   │       └─ Branch不是最新 → git pull main
   │
   ├─ CODEOWNERS问题
   │   └─ 语法错误
   │       ├─ 运行验证脚本
   │       ├─ 修复语法
   │       └─ 重新commit
   │
   └─ Merge冲突
       └─ 解决冲突
           ├─ git pull origin main
           ├─ 解决冲突文件
           ├─ git add .
           └─ git push
```

---

## 总结

这个架构设计体现了：

1. **分层设计**: 从本地到远程，从自动到人工
2. **深度集成**: 与8-Phase工作流无缝配合
3. **多重保障**: 4层质量检查，层层把关
4. **自动化优先**: 能自动的绝不手动
5. **可扩展性**: 易于添加新的检查和规则
6. **可维护性**: 清晰的依赖关系和配置管理

**核心理念**: 让正确的事情容易做，让错误的事情难做。
