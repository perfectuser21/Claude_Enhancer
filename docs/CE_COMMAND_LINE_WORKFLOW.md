# Claude Enhancer 命令行工作流优化方案 (ce CLI)

## 📊 当前状态分析

### 现有系统架构
```
Claude Enhancer 5.0
├── .workflow/executor.sh     - 核心执行引擎（P0-P7管理）
├── .workflow/config.yml      - 并行/自动化配置
├── .workflow/gates.yml       - 8阶段质量闸门
├── Git Hooks                 - 强制验证层
└── Claude Hooks              - 智能建议层
```

### 已有能力
- ✅ 8阶段工作流（P0-P7）
- ✅ Git自动化（auto_commit, auto_tag, auto_pr）
- ✅ 并行限制配置
- ✅ 质量闸门验证
- ✅ 分支保护机制

### 待优化点
- ❌ 命令行接口不够直观
- ❌ 需要记住复杂路径（bash .workflow/executor.sh）
- ❌ 多步操作需要分开执行
- ❌ 状态管理分散（.phase/current + .workflow/ACTIVE）
- ❌ 缺少统一的用户体验

---

## 🎯 优化设计：ce CLI 命令体系

### 设计理念
1. **简洁优先** - 常用操作1-2个词
2. **智能默认** - 减少决策负担
3. **渐进式** - 从简单到复杂的学习曲线
4. **可观测** - 随时了解系统状态

### 命令层级架构

```
ce (主命令)
├── start    <feature>    # 快速开始新功能
├── status              # 查看开发状态
├── validate            # 验证当前阶段
├── next                # 进入下一阶段
├── publish             # 发布（验证+推送+PR）
├── merge   <branch>    # 合并功能分支
├── clean               # 清理已合并分支
└── help                # 帮助信息
```

---

## 📐 完整命令规范

### 1. ce start <feature> - 快速启动

**功能**：创建feature分支并初始化P0阶段

**语法**：
```bash
ce start <feature-name> [--from=main] [--phase=P0]
```

**执行流程**：
```
Step 1: 分支创建
  ├─ 检查当前分支（如果在feature分支，先切回main）
  ├─ 生成分支名：feature/<feature-name>-YYYYMMDD
  └─ 创建并切换到新分支

Step 2: 工作流初始化
  ├─ 设置 .phase/current = P0
  ├─ 创建 .workflow/ACTIVE 文件
  └─ 初始化 .gates/ 目录

Step 3: 智能提示
  ├─ 显示P0阶段要求（可行性分析）
  ├─ 建议创建 docs/P0_<feature>_DISCOVERY.md
  └─ 显示可用的next命令
```

**输出示例**：
```
🚀 Claude Enhancer - 启动新功能开发

📍 当前状态:
  分支: main -> feature/auth-login-20251009
  阶段: P0 (Discovery - 可行性分析)

📋 P0阶段要求:
  • 创建可行性分析文档
  • 验证至少2个关键技术点
  • 评估技术/业务/时间风险
  • 得出明确结论（GO/NO-GO/NEEDS-DECISION）

💡 建议操作:
  1. 创建 docs/P0_auth-login_DISCOVERY.md
  2. 进行技术spike验证
  3. 运行 'ce validate' 检查P0完成度
  4. 运行 'ce next' 进入P1阶段

✅ 环境已就绪！开始你的探索之旅。
```

**错误处理**：
```bash
# 场景1：已在feature分支
❌ ERROR: 当前已在feature分支 'feature/old-feature'

   解决方案:
   1. 先完成当前功能: ce publish
   2. 或切回main: git checkout main
   3. 然后重新运行: ce start new-feature

# 场景2：有未提交更改
❌ ERROR: 检测到未提交的更改

   解决方案:
   1. 提交更改: git add . && git commit
   2. 或暂存更改: git stash
   3. 然后重新运行: ce start feature-name
```

---

### 2. ce status - 状态总览

**功能**：显示当前开发状态和进度

**语法**：
```bash
ce status [--verbose] [--json]
```

**输出示例**（标准模式）：
```
📊 Claude Enhancer 状态报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 基本信息
  项目: Claude Enhancer 5.0
  分支: feature/auth-login-20251009
  阶段: P3 (Implementation - 代码实现)
  启动: 2025-10-09 14:32:15 (2h 45m ago)

📈 工作流进度
  ✅ P0 Discovery      - 完成 (2025-10-09 14:45)
  ✅ P1 Plan           - 完成 (2025-10-09 15:20)
  ✅ P2 Skeleton       - 完成 (2025-10-09 15:45)
  ▶️  P3 Implementation - 进行中
  ⏸️  P4 Testing        - 待开始
  ⏸️  P5 Review         - 待开始
  ⏸️  P6 Release        - 待开始
  ⏸️  P7 Monitor        - 待开始

🔒 质量闸门状态
  ✅ Gate 00 (P0) - 已验证
  ✅ Gate 01 (P1) - 已验证
  ✅ Gate 02 (P2) - 已验证
  ⏳ Gate 03 (P3) - 验证中...

📝 当前阶段要求
  • 实现功能代码，确保可构建
  • 更新 docs/CHANGELOG.md Unreleased段
  • 生成变更点清单
  • 通过构建检查

⚡ 并行配置
  当前限制: 8个Agent (P3阶段最大值)
  自动调优: 启用 (quality_first策略)

🔧 Git自动化状态
  ✅ 自动提交 (Phase结束时)
  ✅ 自动打tag (P6完成时)
  ✅ 自动创建PR (P6完成时)
  ❌ 自动合并 (需手动确认)

💡 下一步建议
  1. 完成代码实现
  2. 运行 'ce validate' 验证P3
  3. 运行 'ce next' 进入P4测试阶段
```

**输出示例（详细模式）**：
```bash
ce status --verbose

# 额外显示:
📊 性能指标
  缓存命中率: 87.3%
  平均验证时间: 3.2s
  Hook并发数: 4

📂 文件变更统计
  新增: 12 文件
  修改: 8 文件
  删除: 2 文件

🧪 测试覆盖率
  单元测试: 未运行 (P4阶段)
  集成测试: 未运行 (P4阶段)
  冒烟测试: 未运行 (P4阶段)
```

**JSON输出**（供脚本使用）：
```json
{
  "project": "Claude Enhancer 5.0",
  "branch": "feature/auth-login-20251009",
  "current_phase": "P3",
  "phase_name": "Implementation",
  "started_at": "2025-10-09T14:32:15Z",
  "progress": {
    "completed": ["P0", "P1", "P2"],
    "current": "P3",
    "remaining": ["P4", "P5", "P6", "P7"]
  },
  "gates": {
    "passed": ["00", "01", "02"],
    "current": "03",
    "status": "validating"
  },
  "automation": {
    "auto_commit": true,
    "auto_tag": true,
    "auto_pr": true,
    "auto_merge": false
  }
}
```

---

### 3. ce validate - 验证当前阶段

**功能**：运行当前Phase的所有质量闸门检查

**语法**：
```bash
ce validate [--fix] [--skip-tests]
```

**执行流程**：
```
Phase 1: 读取当前阶段配置
  ├─ 从 .phase/current 读取当前Phase
  ├─ 从 gates.yml 加载验证规则
  └─ 显示将要执行的检查项

Phase 2: 并行执行检查
  ├─ 路径验证（allow_paths）
  ├─ 产物验证（must_produce）
  ├─ 安全扫描（敏感信息检测）
  ├─ 代码质量（linting）
  └─ 测试运行（如果是P4阶段）

Phase 3: 生成报告
  ├─ 显示通过/失败的检查
  ├─ 对失败项给出修复建议
  └─ 决定是否创建gate标记文件
```

**输出示例**（全部通过）：
```
🔍 Claude Enhancer - 验证 P3 阶段

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1/5] 路径验证
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

检查文件: src/auth/login.ts
  ✅ 匹配 src/** (允许路径)

检查文件: docs/CHANGELOG.md
  ✅ 匹配 docs/CHANGELOG.md (允许路径)

✅ 路径验证通过 (2/2 文件合规)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[2/5] 产物验证
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

检查: 实现功能代码，可构建
  ✅ 构建成功 (npm run build)

检查: docs/CHANGELOG.md Unreleased段新增条目
  ✅ 找到新增条目: "feat(auth): 实现登录功能"

✅ 产物验证通过 (2/2 项目完成)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[3/5] 安全扫描
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

扫描: 硬编码密码
  ✅ 未发现

扫描: API密钥
  ✅ 未发现

扫描: 私钥文件
  ✅ 未发现

✅ 安全扫描通过 (0个问题)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[4/5] 代码质量
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Linting: src/auth/login.ts
  ✅ ESLint通过

✅ 代码质量检查通过

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[5/5] 版本一致性
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

检查: VERSION -> manifest.yml
  ✅ 版本匹配 (5.1.0)

检查: VERSION -> settings.json
  ✅ 版本匹配 (5.1.0)

✅ 版本一致性检查通过

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 所有检查通过！

✅ Gate 03 已标记
✅ P3阶段验证完成

💡 下一步:
   运行 'ce next' 自动进入P4 (Testing) 阶段
```

**输出示例**（部分失败）：
```
🔍 Claude Enhancer - 验证 P3 阶段

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[2/5] 产物验证
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

检查: docs/CHANGELOG.md Unreleased段新增条目
  ❌ 未找到Unreleased段的新增内容

❌ 产物验证失败 (1/2 项目未完成)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[3/5] 安全扫描
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

扫描: API密钥
  ❌ 发现硬编码API密钥
     文件: src/config.ts
     行号: 42
     内容: apiKey = "sk-1234567890abcdef"

❌ 安全扫描失败 (1个问题)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ 验证失败 (2个检查未通过)

🔧 修复建议:

[问题1] CHANGELOG.md缺少条目
  当前状态: Unreleased段为空

  解决方案:
    1. 编辑 docs/CHANGELOG.md
    2. 在 ## Unreleased 下添加:
       - feat(auth): 实现登录功能
    3. 重新运行 'ce validate'

  自动修复:
    ce validate --fix

[问题2] 硬编码API密钥
  文件: src/config.ts:42

  解决方案:
    1. 创建 .env 文件
    2. 添加: API_KEY=sk-1234567890abcdef
    3. 代码改为: apiKey = process.env.API_KEY
    4. 确保 .env 在 .gitignore 中
    5. 重新运行 'ce validate'

  严重性: 🔴 CRITICAL - 必须修复才能继续
```

**自动修复模式**：
```bash
ce validate --fix

🔧 自动修复模式

[1/2] 修复 CHANGELOG.md
  • 分析最近提交...
  • 生成变更描述: "feat(auth): 实现登录功能"
  • 插入到 Unreleased 段
  ✅ 已自动修复

[2/2] 硬编码密钥
  ⚠️  无法自动修复（需人工判断）
  请手动处理上述建议

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
自动修复完成: 1/2

请修复剩余问题后重新运行 'ce validate'
```

---

### 4. ce next - 进入下一阶段

**功能**：验证当前Phase并自动进入下一Phase

**语法**：
```bash
ce next [--skip-validate] [--force]
```

**执行流程**：
```
Step 1: 验证当前阶段
  ├─ 运行 ce validate
  └─ 如果失败，停止并显示错误

Step 2: 自动提交（如果配置启用）
  ├─ 检查 config.yml 的 git.auto_commit
  ├─ 如果启用，执行 git add + commit
  └─ 使用Phase前缀（如 [P3][impl]）

Step 3: 阶段切换
  ├─ 读取 gates.yml 的 on_pass 动作
  ├─ 更新 .phase/current
  ├─ 更新 .workflow/ACTIVE
  └─ 创建下一阶段的gate标记文件

Step 4: 智能提示
  ├─ 显示新阶段的要求
  ├─ 提示必须产出的文档
  └─ 建议下一步操作
```

**输出示例**（成功）：
```
🚀 Claude Enhancer - 阶段推进

[1/4] 验证当前阶段 (P3)
  ✅ 所有检查通过

[2/4] 自动提交
  检测到未提交的更改:
    M  src/auth/login.ts
    M  docs/CHANGELOG.md

  📝 提交信息: [P3][impl] 实现登录功能
  ✅ 已提交 (commit: a1b2c3d)

[3/4] 阶段切换
  P3 (Implementation) → P4 (Testing)

  ✅ 已更新 .phase/current
  ✅ 已更新 .workflow/ACTIVE
  ✅ 已创建 .gates/03.ok

[4/4] 加载新阶段配置
  阶段: P4 (Testing - 测试验证)
  并行限制: 6个Agent

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 已成功进入 P4 阶段！

📋 P4阶段要求:
  • 新增/改动测试 ≥ 2条
  • 至少1条为边界/负例测试
  • 创建 docs/TEST-REPORT.md
  • 确保 unit+boundary+smoke 测试通过

⚡ 并行开发建议:
  使用6个Agent并行开发测试:
  1. test-engineer (主导)
  2. backend-architect (集成测试)
  3. performance-engineer (性能测试)
  4. security-auditor (安全测试)
  5. api-designer (契约测试)
  6. technical-writer (测试文档)

💡 下一步操作:
  1. 创建测试文件
  2. 运行 'ce validate' 检查测试完成度
  3. 运行 'ce next' 进入P5审查阶段
```

**错误场景**：
```bash
# 场景1：验证失败
❌ 无法进入下一阶段

当前阶段 (P3) 验证失败:
  • CHANGELOG.md缺少条目
  • 发现硬编码密钥

请先修复上述问题，然后重新运行 'ce next'

# 场景2：已是最后阶段
✅ 当前已在最后阶段 (P7 - Monitor)

💡 下一步建议:
  1. 运行 'ce publish' 发布功能
  2. 或运行 'ce merge main' 合并到主分支
```

**强制模式**（跳过验证）：
```bash
ce next --force

⚠️  警告: 强制模式已启用（跳过验证）

这可能导致:
  • 未完成的功能进入下一阶段
  • 质量问题累积
  • 后续阶段验证更困难

确认要继续吗？ (yes/no): yes

⏭️  已跳过验证，强制进入 P4 阶段

⚠️  建议尽快完成上一阶段的遗留问题
```

---

### 5. ce publish - 发布功能

**功能**：完整的发布流程（验证 → 推送 → PR）

**语法**：
```bash
ce publish [--skip-pr] [--draft] [--reviewer=<user>]
```

**执行流程**：
```
Phase 1: 完整性检查
  ├─ 验证至少完成到P4阶段
  ├─ 检查所有必需的gate文件
  └─ 确认所有测试通过

Phase 2: 最终验证
  ├─ 运行当前阶段的 ce validate
  ├─ 运行pre-push hook检查
  └─ 确认没有阻塞问题

Phase 3: 推送到远程
  ├─ git push origin <feature-branch>
  ├─ 设置upstream跟踪
  └─ 显示远程URL

Phase 4: 创建Pull Request（如果启用）
  ├─ 使用 gh pr create
  ├─ 生成PR标题和描述
  ├─ 添加标签（自动根据Phase）
  └─ 指定审查者（如果提供）

Phase 5: 后续提示
  ├─ 显示PR链接
  ├─ 显示CI/CD状态
  └─ 建议下一步操作
```

**输出示例**（完整流程）：
```
📦 Claude Enhancer - 发布功能

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1/5] 完整性检查
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

检查阶段进度...
  ✅ P0 Discovery - 完成
  ✅ P1 Plan - 完成
  ✅ P2 Skeleton - 完成
  ✅ P3 Implementation - 完成
  ✅ P4 Testing - 完成
  ⏳ P5 Review - 进行中

⚠️  建议: 完成P5审查后再发布
   继续发布吗？ (yes/no): yes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[2/5] 最终验证
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

运行 P5 阶段验证...
  ✅ docs/REVIEW.md 存在
  ✅ 包含三段分析（风格/风险/回滚）
  ✅ 结论为 APPROVE

运行 pre-push 检查...
  ✅ 工作流完整性
  ✅ 烟雾测试
  ✅ 权限检查

✅ 所有验证通过

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[3/5] 推送到远程
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

分支: feature/auth-login-20251009
目标: origin/feature/auth-login-20251009

推送中...
  Enumerating objects: 42
  Counting objects: 100%
  Writing objects: 100%

✅ 推送成功
   URL: https://github.com/user/repo/tree/feature/auth-login-20251009

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[4/5] 创建 Pull Request
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

自动生成PR内容...

标题: feat(auth): 实现登录功能

描述:
  ## Summary
  • 实现用户登录功能
  • 添加JWT token认证
  • 集成OAuth2.0支持

  ## Changes
  • 新增 src/auth/login.ts
  • 更新 docs/CHANGELOG.md
  • 添加14个测试用例

  ## Test Coverage
  • 单元测试: 92%
  • 集成测试: 通过
  • 安全测试: 通过

  ## Workflow Status
  ✅ P0-P5 全部通过
  📊 保障力评分: 100/100

  🤖 Generated with Claude Enhancer 5.0

创建中...
✅ PR已创建: #123

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[5/5] CI/CD 状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GitHub Actions 已触发:
  ⏳ BDD验收测试 - 运行中...
  ⏳ 性能基准测试 - 排队中
  ⏳ 安全扫描 - 排队中
  ⏳ OpenAPI验证 - 排队中

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 发布成功！

📎 PR链接:
   https://github.com/user/repo/pull/123

📊 CI/CD 仪表板:
   https://github.com/user/repo/actions

💡 下一步:
  1. 等待CI检查完成（约5-10分钟）
  2. 如果全绿，运行 'ce merge' 合并到main
  3. 或在GitHub上手动审查和合并
```

**草稿模式**：
```bash
ce publish --draft

# 创建Draft PR（不触发CI，不请求审查）
✅ 已创建草稿PR: #123

   可以继续修改代码，修改会自动同步到PR
   准备好后运行: gh pr ready #123
```

**跳过PR模式**：
```bash
ce publish --skip-pr

# 只推送，不创建PR
✅ 已推送到远程

💡 手动创建PR:
   gh pr create --title "feat(auth): 实现登录功能"
```

---

### 6. ce merge <branch> - 合并分支

**功能**：安全地合并feature分支到目标分支

**语法**：
```bash
ce merge [<target-branch>] [--squash] [--delete-branch]
```

**执行流程**：
```
Phase 1: 安全检查
  ├─ 验证目标分支存在
  ├─ 检查是否有冲突
  └─ 确认所有CI检查通过

Phase 2: 合并前验证
  ├─ 运行P7监控检查（如果适用）
  ├─ 确认SLO达标
  └─ 验证健康检查通过

Phase 3: 执行合并
  ├─ git checkout <target-branch>
  ├─ git pull origin <target-branch>
  ├─ git merge --squash <feature-branch>（默认）
  └─ git commit with detailed message

Phase 4: 健康检查
  ├─ 运行post-merge smoke tests
  ├─ 检查关键服务状态
  └─ 如果失败，自动回滚

Phase 5: 清理（如果启用）
  ├─ 删除本地feature分支
  ├─ 删除远程feature分支
  └─ 清理相关工作流文件
```

**输出示例**（成功）：
```
🔀 Claude Enhancer - 合并分支

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1/5] 安全检查
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

源分支: feature/auth-login-20251009
目标分支: main

检查PR状态...
  ✅ PR #123 已批准
  ✅ 所有CI检查通过
  ✅ 无合并冲突

检查目标分支状态...
  ✅ main 分支最新
  ✅ 无保护规则阻塞

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[2/5] 合并前验证
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

运行 P7 监控检查...
  ✅ 健康检查通过
  ✅ SLO达标（可用性: 99.9%）
  ✅ 性能基线验证通过

✅ 所有验证通过，可以安全合并

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[3/5] 执行合并
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

切换到目标分支...
  $ git checkout main
  $ git pull origin main

合并策略: Squash Merge

生成合并提交信息...
  feat(auth): 实现登录功能 (#123)

  完整功能实现:
  • 用户登录认证
  • JWT token管理
  • OAuth2.0集成

  测试覆盖:
  • 14个测试用例
  • 92%代码覆盖率

  工作流验证:
  ✅ P0-P7 全部通过
  ✅ 所有质量闸门验证

  Co-authored-by: Claude <noreply@anthropic.com>

执行合并...
  $ git merge --squash feature/auth-login-20251009
  $ git commit -m "..."

✅ 合并完成 (commit: x7y8z9a)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[4/5] 健康检查
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

运行 post-merge 冒烟测试...
  ✅ 构建成功
  ✅ 单元测试通过
  ✅ 关键API响应正常

检查系统健康度...
  ✅ 所有服务运行正常
  ✅ 无错误日志
  ✅ 资源使用正常

✅ 健康检查通过

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[5/5] 清理
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

删除本地分支...
  $ git branch -d feature/auth-login-20251009
  ✅ 已删除

删除远程分支...
  $ git push origin --delete feature/auth-login-20251009
  ✅ 已删除

清理工作流文件...
  ✅ 已清理 .phase/
  ✅ 已清理 .gates/
  ✅ 已清理 .workflow/ACTIVE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 合并成功！

📊 统计信息:
  提交数: 15 commits squashed into 1
  文件变更: +1247 -89 (净增: +1158 行)
  持续时间: 2天 14小时

💡 下一步:
  1. 推送到远程: git push origin main
  2. 开始新功能: ce start next-feature
  3. 查看项目状态: ce status
```

**冲突场景**：
```
❌ 检测到合并冲突

冲突文件:
  • src/auth/login.ts (12行冲突)
  • docs/CHANGELOG.md (3行冲突)

解决方案:
  1. 手动解决冲突:
     git checkout feature/auth-login-20251009
     git merge main
     # 解决冲突
     git commit

  2. 重新运行:
     ce merge main

自动解决冲突 (实验性):
  ce merge main --auto-resolve
```

**健康检查失败自动回滚**：
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[4/5] 健康检查
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

运行 post-merge 冒烟测试...
  ✅ 构建成功
  ❌ 单元测试失败 (3/45 failed)

🚨 健康检查失败！触发自动回滚...

回滚步骤:
  [1/3] 重置到上一个稳定commit
    $ git reset --hard <last-stable-commit>
    ✅ 已回滚

  [2/3] 恢复feature分支
    $ git checkout -b feature/auth-login-20251009-recovery
    ✅ 分支已恢复

  [3/3] 通知相关人员
    ✅ 已发送告警

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ 合并失败并已回滚

失败原因:
  健康检查未通过: 3个单元测试失败

🔍 失败的测试:
  1. test/auth/login.test.ts:45 - "should handle invalid credentials"
  2. test/auth/token.test.ts:12 - "should refresh expired token"
  3. test/user/profile.test.ts:89 - "should update user profile"

💡 建议操作:
  1. 切换到恢复分支: git checkout feature/auth-login-20251009-recovery
  2. 修复测试: 运行 npm test 查看详细错误
  3. 提交修复: git commit -m "fix: 修复测试失败问题"
  4. 重新发布: ce publish
  5. 再次尝试合并: ce merge main
```

---

### 7. ce clean - 清理已合并分支

**功能**：清理本地和远程的已合并feature分支

**语法**：
```bash
ce clean [--all] [--dry-run] [--keep=<days>]
```

**执行流程**：
```
Step 1: 扫描已合并分支
  ├─ 检查本地feature分支
  ├─ 检查远程feature分支
  └─ 识别已合并到main的分支

Step 2: 安全过滤
  ├─ 排除受保护的分支（main, develop, etc.）
  ├─ 排除最近N天的分支（--keep参数）
  └─ 排除有未合并commit的分支

Step 3: 交互式确认（默认）
  ├─ 显示将要删除的分支列表
  ├─ 要求用户确认
  └─ 允许单独选择保留某些分支

Step 4: 执行清理
  ├─ 删除本地分支
  ├─ 删除远程分支
  └─ 清理相关的refs和配置

Step 5: 报告结果
  ├─ 显示删除的分支数量
  ├─ 显示释放的磁盘空间
  └─ 列出保留的分支
```

**输出示例**：
```
🧹 Claude Enhancer - 清理已合并分支

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
扫描已合并分支...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

本地分支:
  ✓ feature/auth-login-20251001 (已合并 8天前)
  ✓ feature/api-refactor-20250925 (已合并 14天前)
  ✓ fix/security-patch-20250920 (已合并 19天前)
  ✗ feature/new-dashboard-20251009 (未合并 - 保留)

远程分支:
  ✓ origin/feature/auth-login-20251001
  ✓ origin/feature/api-refactor-20250925
  ✓ origin/fix/security-patch-20250920

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 清理统计:
  可删除分支: 3个 (本地) + 3个 (远程)
  预计释放空间: ~45 MB

确认删除这些分支吗？ (yes/no/show): show

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
分支详情:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1] feature/auth-login-20251001
    最后提交: 2025-10-01 16:30:25
    作者: developer@example.com
    合并到: main (commit: a1b2c3d)
    PR: #118 (已关闭)
    大小: 12 MB

[2] feature/api-refactor-20250925
    最后提交: 2025-09-25 09:15:42
    作者: developer@example.com
    合并到: main (commit: e4f5g6h)
    PR: #105 (已关闭)
    大小: 28 MB

[3] fix/security-patch-20250920
    最后提交: 2025-09-20 14:22:10
    作者: security@example.com
    合并到: main (commit: i7j8k9l)
    PR: #98 (已关闭)
    大小: 5 MB

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

选择操作:
  [a] 全部删除
  [s] 选择性删除
  [n] 取消

输入选择: a

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
清理进行中...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

删除本地分支:
  ✓ feature/auth-login-20251001
  ✓ feature/api-refactor-20250925
  ✓ fix/security-patch-20250920

删除远程分支:
  ✓ origin/feature/auth-login-20251001
  ✓ origin/feature/api-refactor-20250925
  ✓ origin/fix/security-patch-20250920

清理refs和配置...
  ✓ 已清理Git缓存
  ✓ 已优化仓库

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 清理完成！

📊 结果:
  删除分支: 6个 (3本地 + 3远程)
  释放空间: 45 MB
  优化耗时: 3.2s

📂 保留的分支:
  • feature/new-dashboard-20251009 (未合并)
  • main (受保护)

💡 建议:
  定期运行清理以保持仓库整洁
  下次清理: ce clean
```

**Dry-run模式**：
```bash
ce clean --dry-run

🔍 清理预览（Dry-run模式）

将要删除的分支:
  ✓ feature/auth-login-20251001
  ✓ feature/api-refactor-20250925
  ✓ fix/security-patch-20250920

预计释放空间: ~45 MB

⚠️  这只是预览，不会执行实际删除
   运行 'ce clean' 执行清理
```

**保留最近N天**：
```bash
ce clean --keep=30

# 只清理30天前合并的分支
📊 清理统计:
  扫描: 5个已合并分支
  过滤: 2个（最近30天内）
  可删除: 3个
```

---

## 🔧 命令实现架构

### 技术栈
```
ce (Shell脚本)
├── /usr/local/bin/ce          - 主入口（符号链接）
├── .workflow/cli/              - CLI实现目录
│   ├── ce.sh                  - 主控制器
│   ├── commands/              - 子命令实现
│   │   ├── start.sh
│   │   ├── status.sh
│   │   ├── validate.sh
│   │   ├── next.sh
│   │   ├── publish.sh
│   │   ├── merge.sh
│   │   └── clean.sh
│   ├── lib/                   - 共享库
│   │   ├── colors.sh          - 颜色输出
│   │   ├── utils.sh           - 工具函数
│   │   ├── git-ops.sh         - Git操作
│   │   ├── phase-ops.sh       - Phase管理
│   │   └── report.sh          - 报告生成
│   └── config/                - 配置文件
│       └── defaults.yml       - 默认配置
└── Integration                - 与现有系统集成
    ├── executor.sh            - 工作流引擎
    ├── gates.yml              - 质量闸门
    └── config.yml             - 系统配置
```

### 核心函数库

```bash
# lib/phase-ops.sh
get_current_phase()        # 读取当前Phase
set_current_phase()        # 设置Phase
validate_phase()           # 验证Phase
get_phase_info()          # 获取Phase信息
get_next_phase()          # 计算下一Phase

# lib/git-ops.sh
create_feature_branch()   # 创建feature分支
push_to_remote()         # 推送到远程
create_pull_request()    # 创建PR
merge_branch()           # 合并分支
cleanup_branch()         # 清理分支

# lib/report.sh
generate_status_report() # 生成状态报告
generate_progress_bar()  # 生成进度条
format_duration()        # 格式化时间
format_file_size()       # 格式化文件大小

# lib/utils.sh
confirm()                # 交互式确认
spinner()                # 加载动画
error_exit()            # 错误处理
log_*()                 # 日志函数
```

---

## ⚡ 性能优化策略

### 1. 缓存机制
```bash
# 缓存Phase状态（避免重复读取文件）
CACHE_CURRENT_PHASE=""
CACHE_GATES_STATUS=""
CACHE_GIT_BRANCH=""

get_current_phase_cached() {
    if [ -z "$CACHE_CURRENT_PHASE" ]; then
        CACHE_CURRENT_PHASE=$(cat .phase/current)
    fi
    echo "$CACHE_CURRENT_PHASE"
}
```

### 2. 并行执行
```bash
# 并行运行多个检查
validate_phase() {
    (
        validate_paths &
        validate_produces &
        validate_security &
        validate_quality &
        wait
    )
}
```

### 3. 增量验证
```bash
# 只验证变更的文件
LAST_VALIDATE_HASH=$(cat .workflow/.last_validate_hash 2>/dev/null)
CURRENT_HASH=$(git rev-parse HEAD)

if [ "$LAST_VALIDATE_HASH" == "$CURRENT_HASH" ]; then
    echo "✅ 使用缓存的验证结果"
    return 0
fi
```

### 4. 智能跳过
```bash
# P4阶段之前跳过测试运行
if [[ "$CURRENT_PHASE" < "P4" ]]; then
    echo "⏭️  跳过测试（P4阶段前不运行）"
    return 0
fi
```

---

## 📊 工作流状态图

```
                    Claude Enhancer 工作流

ce start              ┌─────────────────────┐
  ↓                  │   P0 Discovery      │
  └─────────────────→│   (可行性分析)       │
                     └─────────┬───────────┘
                               │ ce next
                               ↓
                     ┌─────────────────────┐
                     │   P1 Plan           │
                     │   (需求分析)         │
                     └─────────┬───────────┘
                               │ ce next
                               ↓
                     ┌─────────────────────┐
                     │   P2 Skeleton       │
                     │   (架构设计)         │
                     └─────────┬───────────┘
                               │ ce next
                               ↓
                     ┌─────────────────────┐
                     │   P3 Implementation │
                     │   (代码实现)         │
                     └─────────┬───────────┘
                               │ ce next
                               ↓
                     ┌─────────────────────┐
                     │   P4 Testing        │
                     │   (测试验证)         │
                     └─────────┬───────────┘
                               │ ce next
                               ↓
                     ┌─────────────────────┐
                     │   P5 Review         │
                     │   (代码审查)         │
                     └─────────┬───────────┘
                               │ ce next
                               ↓
                     ┌─────────────────────┐
                     │   P6 Release        │
     ce publish ────→│   (发布准备)         │
                     └─────────┬───────────┘
                               │ ce next
                               ↓
                     ┌─────────────────────┐
                     │   P7 Monitor        │
      ce merge  ────→│   (生产监控)         │
                     └─────────────────────┘
                               │
                               ↓
                          [合并到main]
                               │
                               ↓
                          ce clean
```

---

## 🔄 与现有系统集成

### 配置映射
```yaml
# .workflow/cli/config/defaults.yml

# 映射到 config.yml
git:
  auto_commit: ${CONFIG.git.auto_commit}
  auto_tag: ${CONFIG.git.auto_tag}
  auto_pr: ${CONFIG.git.auto_pr}
  auto_merge: ${CONFIG.git.auto_merge}

# 映射到 gates.yml
phases: ${GATES.phases}
gates: ${GATES.gates}

# CLI特有配置
cli:
  default_phase: "P0"
  confirm_destructive: true
  show_progress: true
  cache_ttl: 300
  spinner_style: "dots"
```

### 调用现有组件
```bash
# ce validate 调用现有的验证系统
ce validate → .workflow/executor.sh validate
           → Git hooks (pre-commit)
           → Claude hooks (quality_gate.sh)

# ce next 调用Phase推进逻辑
ce next → .workflow/executor.sh next
        → gates.yml 的 on_pass 动作
        → 自动commit（如果启用）

# ce publish 调用发布流程
ce publish → Git push
           → gh pr create（使用PR模板）
           → 触发GitHub Actions
```

---

## 📈 性能预期

### 命令响应时间
```
ce start    : < 0.5s  (分支创建 + 初始化)
ce status   : < 0.3s  (读取状态文件)
ce validate : 2-10s   (取决于检查项数量)
ce next     : 3-15s   (包含验证 + Phase切换)
ce publish  : 5-30s   (包含push + PR创建)
ce merge    : 10-60s  (包含健康检查)
ce clean    : 1-5s    (分支扫描 + 删除)
```

### 优化收益
```
Before (手动执行):
  启动新功能: 5-10分钟
  验证阶段: 10-15分钟
  发布流程: 15-20分钟

After (ce CLI):
  启动新功能: < 30秒
  验证阶段: < 10秒
  发布流程: < 1分钟

时间节省: 约85-90%
```

---

## 🎯 实施优先级

### Phase 1: 核心命令（P0）
- ✅ ce start
- ✅ ce status
- ✅ ce validate
- ✅ ce next

### Phase 2: 发布流程（P1）
- ✅ ce publish
- ✅ ce merge
- ✅ 健康检查和回滚

### Phase 3: 运维工具（P2）
- ✅ ce clean
- ✅ 性能优化
- ✅ 缓存机制

### Phase 4: 增强功能（P3）
- 🔄 自动修复（ce validate --fix）
- 🔄 智能建议增强
- 🔄 可视化仪表板

---

## 💡 使用场景示例

### 场景1: 快速启动新功能
```bash
# 1分钟内完成从想法到编码
$ ce start user-profile-api
🚀 功能分支已就绪，开始P0探索

# 快速验证可行性后进入P1
$ ce next
✅ 进入P1规划阶段

# 创建PLAN.md后继续
$ ce next
✅ 进入P2架构设计
```

### 场景2: 完整开发周期
```bash
# Day 1: 探索和规划
$ ce start payment-gateway
$ ce validate  # 验证P0完成
$ ce next      # → P1
$ ce next      # → P2

# Day 2-3: 实现和测试
$ ce next      # → P3
# ... 编码 ...
$ ce validate  # 检查代码质量
$ ce next      # → P4
# ... 写测试 ...
$ ce validate  # 运行测试
$ ce next      # → P5

# Day 4: 审查和发布
$ ce next      # → P6
$ ce publish   # 推送+创建PR

# Day 5: 合并到main
$ ce merge main
✅ 功能已上线
```

### 场景3: 快速修复bug
```bash
# 紧急修复流程
$ ce start hotfix-security-vuln
$ ce goto P3   # 跳过P0-P2
# ... 修复代码 ...
$ ce next      # → P4 测试
$ ce next --force  # 快速通过P5
$ ce publish --draft  # 创建草稿PR
# 测试通过后
$ gh pr ready
$ ce merge main
```

---

## 🔒 安全性考虑

### 破坏性操作保护
```bash
# 需要确认的操作
ce merge main          # 合并到主分支
ce clean --all        # 删除多个分支
ce next --force       # 强制跳过验证

# 自动备份
ce merge → 自动创建backup分支
ce clean → 保留refs/backup/
```

### 权限检查
```bash
# Git Hooks权限验证
ce publish → 触发pre-push → 权限检查

# 分支保护规则
ce merge main → 检查是否有合并权限
```

---

## 📚 帮助系统

### ce help 输出
```
Claude Enhancer CLI - AI驱动的生产级开发工作流

用法: ce <command> [options]

核心命令:
  start <feature>    快速启动新功能开发
  status            查看当前工作流状态
  validate          验证当前阶段完成度
  next              进入下一阶段
  publish           发布功能（推送+PR）
  merge [branch]    合并分支到目标分支
  clean             清理已合并的分支

选项:
  --help, -h        显示帮助信息
  --version, -v     显示版本信息
  --verbose         显示详细输出
  --json            JSON格式输出
  --dry-run         预览执行计划

示例:
  # 启动新功能
  ce start user-authentication

  # 查看状态
  ce status

  # 验证并进入下一阶段
  ce validate && ce next

  # 发布功能
  ce publish

  # 合并到main
  ce merge main

了解更多: https://github.com/user/repo/wiki/ce-cli
```

---

## 🎨 用户体验亮点

1. **即时反馈** - 所有操作都有清晰的进度指示
2. **智能提示** - 根据当前状态给出下一步建议
3. **容错设计** - 破坏性操作需要确认，支持回滚
4. **性能优化** - 缓存和并行执行，响应迅速
5. **美观输出** - 使用颜色、图标、进度条
6. **完整文档** - 内置帮助和错误提示

---

## 📊 对比分析

| 操作 | Before (手动) | After (ce CLI) | 提升 |
|------|---------------|----------------|------|
| 启动新功能 | 5-10分钟 | 30秒 | 10-20x |
| 验证阶段 | 10-15分钟 | 10秒 | 60-90x |
| 发布流程 | 15-20分钟 | 1分钟 | 15-20x |
| 状态查看 | 5分钟 | 2秒 | 150x |
| 分支清理 | 10-15分钟 | 5秒 | 120-180x |

**总体提升: 85-95% 时间节省**

---

## 🚀 下一步行动

1. **Review本方案** - 确认命令设计和功能
2. **实现Phase 1** - 核心命令（start, status, validate, next）
3. **集成测试** - 与现有executor.sh和hooks集成
4. **用户测试** - 收集反馈并优化
5. **完整实现** - 实现所有命令和功能
6. **文档完善** - Wiki和示例

---

*Claude Enhancer 5.0 - 让AI开发工作流像呼吸一样自然*
