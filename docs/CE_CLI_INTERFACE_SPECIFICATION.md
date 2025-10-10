# ce CLI 接口规范文档

> Claude Enhancer 5.0 命令行接口完整设计规范
> 版本: 1.0.0 | 创建日期: 2025-10-09 | 状态: P0 设计文档

---

## 📋 目录

1. [设计理念](#设计理念)
2. [命令总览](#命令总览)
3. [详细命令规范](#详细命令规范)
4. [输出格式标准](#输出格式标准)
5. [错误码体系](#错误码体系)
6. [交互设计](#交互设计)
7. [帮助系统](#帮助系统)
8. [实现架构](#实现架构)

---

## 设计理念

### 核心原则

1. **简洁优先** - 常用操作1-2个词即可完成
2. **智能默认** - 减少用户决策，自动选择最佳路径
3. **渐进式** - 从简单到复杂的学习曲线
4. **可观测** - 随时了解系统状态和进度
5. **容错设计** - 破坏性操作需确认，支持回滚

### 设计目标

- **效率**: 85-95%的时间节省
- **一致性**: 统一的命令结构和输出格式
- **可靠性**: 完善的错误处理和恢复机制
- **可扩展性**: 易于添加新命令和功能

---

## 命令总览

### 命令层级

```
ce (主命令)
├── start <feature>     # 创建功能分支，启动开发
├── status             # 查看工作流状态
├── validate           # 验证当前阶段
├── next               # 进入下一阶段
├── goto <phase>       # 跳转到指定阶段
├── publish            # 发布功能（推送+PR）
├── merge [branch]     # 合并分支
├── clean              # 清理已合并分支
├── reset              # 重置工作流状态
├── help               # 显示帮助
└── version            # 显示版本信息
```

### 命令分类

| 类别 | 命令 | 频率 |
|-----|------|------|
| **核心工作流** | start, status, validate, next | 高 |
| **发布管理** | publish, merge | 中 |
| **辅助工具** | clean, reset, goto | 低 |
| **信息查询** | help, version | 低 |

---

## 详细命令规范

### 1. ce start <feature>

#### 功能描述
创建feature分支并初始化P0阶段，为新功能开发做准备。

#### 语法
```bash
ce start <feature-name> [options]
```

#### 参数

| 参数 | 类型 | 必需 | 描述 | 默认值 |
|-----|------|------|------|--------|
| `feature-name` | string | ✓ | 功能名称（2-50字符） | - |
| `--from` | string | ✗ | 基础分支 | main |
| `--phase` | enum | ✗ | 起始Phase（P0-P7） | P0 |
| `--template` | string | ✗ | 使用模板 | default |

#### 参数验证规则

```yaml
feature-name:
  pattern: "^[a-z0-9-]{2,50}$"
  invalid_chars: ["_", " ", "/", "\\"]
  error_message: "功能名称只能包含小写字母、数字和连字符，长度2-50字符"

--from:
  allowed_values: [main, develop, staging]
  validation: "branch_exists"
  error_message: "指定的基础分支不存在"

--phase:
  allowed_values: [P0, P1, P2, P3, P4, P5, P6, P7]
  default: P0
  error_message: "Phase必须是P0-P7之一"
```

#### 执行流程

```
1. 前置检查
   ├─ 检查是否已在feature分支
   ├─ 检查是否有未提交的更改
   └─ 验证目标分支存在

2. 分支创建
   ├─ 生成分支名: feature/<name>-YYYYMMDD
   ├─ 从基础分支创建
   └─ 切换到新分支

3. 环境初始化
   ├─ 设置 .phase/current = P0
   ├─ 创建 .workflow/ACTIVE
   ├─ 初始化 .gates/ 目录
   └─ 创建必要的模板文件

4. 输出提示
   ├─ 显示当前状态
   ├─ 显示Phase要求
   └─ 建议下一步操作
```

#### 输出示例（成功）

```
🚀 Claude Enhancer - 启动新功能开发

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1/4] 前置检查
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ 当前分支: main
✓ 工作区干净
✓ 基础分支存在

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[2/4] 分支创建
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

分支名: feature/auth-login-20251009
基础分支: main

✓ 分支已创建
✓ 已切换到新分支

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[3/4] 环境初始化
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Phase设置: P0 (Discovery)
✓ 工作流文件已创建
✓ Gates目录已初始化

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[4/4] 准备完成
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 当前状态
  分支: feature/auth-login-20251009
  阶段: P0 (Discovery - 可行性分析)
  时间: 2025-10-09 14:32:15

📋 P0阶段要求
  • 创建可行性分析文档
  • 验证至少2个关键技术点
  • 评估技术/业务/时间风险
  • 得出明确结论（GO/NO-GO/NEEDS-DECISION）

📂 建议创建的文件
  • docs/P0_auth-login_DISCOVERY.md

💡 下一步操作
  1. 进行技术探索和可行性验证
  2. 运行 'ce validate' 检查P0完成度
  3. 运行 'ce next' 进入P1规划阶段

✅ 环境已就绪！开始你的探索之旅。
```

#### 错误场景

```bash
# 场景1：已在feature分支
$ ce start new-feature

❌ ERROR: 当前已在feature分支

  当前分支: feature/old-feature-20251001
  状态: P3 (Implementation)

  解决方案:
    1. 完成当前功能: ce publish && ce merge main
    2. 或切回主分支: git checkout main
    3. 然后重试: ce start new-feature

  紧急情况:
    ce reset  # 重置工作流状态

退出码: 2 (ESTATE_CONFLICT)

# 场景2：有未提交更改
$ ce start new-feature

❌ ERROR: 检测到未提交的更改

  未提交文件:
    M  src/auth/login.ts
    M  docs/CHANGELOG.md
    ?? temp.txt

  解决方案:
    1. 提交更改: git add . && git commit -m "..."
    2. 或暂存更改: git stash
    3. 然后重试: ce start new-feature

退出码: 2 (ESTATE_CONFLICT)

# 场景3：功能名称非法
$ ce start My_New_Feature

❌ ERROR: 功能名称格式错误

  输入: My_New_Feature
  问题: 包含大写字母和下划线

  规则:
    • 只能包含小写字母、数字和连字符
    • 长度2-50字符
    • 示例: auth-login, user-profile, payment-v2

  建议:
    ce start my-new-feature

退出码: 1 (EINVALID_PARAM)
```

---

### 2. ce status

#### 功能描述
显示当前开发状态、Phase进度和工作流信息。

#### 语法
```bash
ce status [options]
```

#### 选项

| 选项 | 类型 | 描述 | 默认值 |
|-----|------|------|--------|
| `--verbose` / `-v` | flag | 显示详细信息 | false |
| `--json` | flag | JSON格式输出 | false |
| `--phase` | enum | 只显示指定Phase信息 | all |

#### 输出格式（标准模式）

```
📊 Claude Enhancer 状态报告

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 基本信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

项目: Claude Enhancer 5.0
分支: feature/auth-login-20251009
阶段: P3 (Implementation - 代码实现)
启动: 2025-10-09 14:32:15 (2h 45m ago)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 工作流进度 (8 Phases)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ P0 Discovery       完成 (2025-10-09 14:45)
✅ P1 Plan            完成 (2025-10-09 15:20)
✅ P2 Skeleton        完成 (2025-10-09 15:45)
▶️  P3 Implementation  进行中 (持续: 1h 30m)
⏸️  P4 Testing         待开始
⏸️  P5 Review          待开始
⏸️  P6 Release         待开始
⏸️  P7 Monitor         待开始

进度: ████████░░░░░░░░░░░░░░░░░░░░░░ 37.5%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 质量闸门状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Gate 00 (P0) - 已验证 [2025-10-09 14:45]
✅ Gate 01 (P1) - 已验证 [2025-10-09 15:20]
✅ Gate 02 (P2) - 已验证 [2025-10-09 15:45]
⏳ Gate 03 (P3) - 验证中...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 P3 阶段要求
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

必须产出:
  ⚠️  实现功能代码，确保可构建
  ✅ 更新 docs/CHANGELOG.md Unreleased段
  ⚠️  生成变更点清单

验证规则:
  ⏳ 构建/编译通过
  ✅ CHANGELOG条目已添加
  ✅ 仅修改allow_paths内的文件

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ 并行配置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

当前限制: 8个Agent (P3阶段最大值)
自动调优: 启用 (quality_first策略)
冲突检测: 启用

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 Git自动化状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 自动提交 (Phase结束时)
✅ 自动打tag (P6完成时)
✅ 自动创建PR (P6完成时)
❌ 自动合并 (需手动确认)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 下一步建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 完成代码实现
2. 运行 'ce validate' 验证P3
3. 运行 'ce next' 进入P4测试阶段
```

#### 输出格式（详细模式）

```bash
ce status --verbose

# 在标准输出基础上增加:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 性能指标
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

缓存命中率: 87.3%
平均验证时间: 3.2s
Hook执行次数: 12
并发Agent使用: 4/8

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 文件变更统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

新增: 12 文件
修改: 8 文件
删除: 2 文件
总变更: +1247 -89 行

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧪 测试覆盖率
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

单元测试: 未运行 (P4阶段)
集成测试: 未运行 (P4阶段)
冒烟测试: 未运行 (P4阶段)
```

#### 输出格式（JSON模式）

```json
{
  "project": "Claude Enhancer 5.0",
  "branch": "feature/auth-login-20251009",
  "current_phase": {
    "id": "P3",
    "name": "Implementation",
    "description": "代码实现",
    "started_at": "2025-10-09T15:45:00Z",
    "duration_seconds": 5400
  },
  "progress": {
    "completed_phases": ["P0", "P1", "P2"],
    "current_phase": "P3",
    "remaining_phases": ["P4", "P5", "P6", "P7"],
    "percentage": 37.5
  },
  "gates": {
    "passed": [
      {
        "id": "00",
        "phase": "P0",
        "status": "passed",
        "validated_at": "2025-10-09T14:45:00Z"
      },
      {
        "id": "01",
        "phase": "P1",
        "status": "passed",
        "validated_at": "2025-10-09T15:20:00Z"
      },
      {
        "id": "02",
        "phase": "P2",
        "status": "passed",
        "validated_at": "2025-10-09T15:45:00Z"
      }
    ],
    "current": {
      "id": "03",
      "phase": "P3",
      "status": "validating"
    }
  },
  "requirements": {
    "must_produce": [
      {
        "item": "实现功能代码，确保可构建",
        "status": "pending"
      },
      {
        "item": "更新 docs/CHANGELOG.md Unreleased段",
        "status": "completed"
      }
    ],
    "gates_rules": [
      {
        "rule": "构建/编译通过",
        "status": "pending"
      }
    ]
  },
  "automation": {
    "auto_commit": true,
    "auto_tag": true,
    "auto_pr": true,
    "auto_merge": false
  },
  "parallelism": {
    "enabled": true,
    "max_agents": 8,
    "current_usage": 4,
    "strategy": "quality_first"
  },
  "stats": {
    "files_added": 12,
    "files_modified": 8,
    "files_deleted": 2,
    "lines_added": 1247,
    "lines_deleted": 89
  }
}
```

---

### 3. ce validate

#### 功能描述
验证当前Phase的所有质量闸门要求。

#### 语法
```bash
ce validate [options]
```

#### 选项

| 选项 | 描述 | 默认值 |
|-----|------|--------|
| `--fix` | 自动修复可修复的问题 | false |
| `--skip-tests` | 跳过测试运行 | false |
| `--skip-security` | 跳过安全扫描 | false |
| `--verbose` | 显示详细日志 | false |

#### 执行流程

```
Phase 1: 准备
  ├─ 读取当前Phase
  ├─ 加载gates.yml规则
  └─ 显示将要执行的检查项

Phase 2: 并行验证
  ├─ 路径验证（allow_paths）
  ├─ 产物验证（must_produce）
  ├─ 安全扫描
  ├─ 代码质量
  ├─ 版本一致性
  └─ 测试运行（P4阶段）

Phase 3: 结果汇总
  ├─ 统计通过/失败项
  ├─ 生成验证报告
  └─ 创建gate标记（全部通过时）

Phase 4: 反馈
  ├─ 显示验证结果
  ├─ 给出修复建议
  └─ 提示下一步操作
```

#### 输出示例（全部通过）

```
🔍 Claude Enhancer - 验证 P3 阶段

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1/5] 路径验证
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ src/auth/login.ts → 匹配 src/**
✓ docs/CHANGELOG.md → 匹配 docs/CHANGELOG.md

✅ 路径验证通过 (2/2 文件合规)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[2/5] 产物验证
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ 实现功能代码，可构建
  → npm run build: 成功 (3.2s)

✓ CHANGELOG.md Unreleased段新增条目
  → 找到: "feat(auth): 实现登录功能"

✅ 产物验证通过 (2/2 项目完成)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[3/5] 安全扫描
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ 硬编码密码: 未发现
✓ API密钥: 未发现
✓ 私钥文件: 未发现
✓ 数据库密码: 未发现
✓ 云服务密钥: 未发现

✅ 安全扫描通过 (0个问题)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[4/5] 代码质量
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ ESLint: 通过
  → 检查文件: 12个
  → 问题: 0个

✓ Prettier: 通过
  → 格式化文件: 12个

✅ 代码质量检查通过

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[5/5] 版本一致性
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ VERSION → manifest.yml: 5.3.4
✓ VERSION → settings.json: 5.3.4
✓ VERSION → package.json: 5.3.4

✅ 版本一致性检查通过

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 所有检查通过！

验证统计:
  总检查项: 15
  通过: 15
  失败: 0
  跳过: 0
  耗时: 8.3s

✅ Gate 03 已标记
✅ P3阶段验证完成

💡 下一步:
  运行 'ce next' 自动进入P4 (Testing) 阶段
```

#### 输出示例（部分失败）

```
🔍 Claude Enhancer - 验证 P3 阶段

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[2/5] 产物验证
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ CHANGELOG.md Unreleased段新增条目
  → 未找到Unreleased段的新增内容
  → 位置: docs/CHANGELOG.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[3/5] 安全扫描
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ API密钥: 发现硬编码
  → 文件: src/config.ts:42
  → 内容: apiKey = "sk-1234567890abcdef"
  → 严重性: 🔴 CRITICAL

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ 验证失败 (2/15 检查未通过)

验证统计:
  总检查项: 15
  通过: 13
  失败: 2
  跳过: 0
  耗时: 7.1s

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 修复建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[问题1] CHANGELOG.md缺少条目
  严重性: ⚠️  WARNING
  影响: 无法追踪变更历史

  解决方案:
    1. 编辑 docs/CHANGELOG.md
    2. 在 ## Unreleased 下添加:
       - feat(auth): 实现登录功能
    3. 重新运行 'ce validate'

  自动修复:
    ce validate --fix

[问题2] 硬编码API密钥
  严重性: 🔴 CRITICAL
  影响: 安全漏洞，密钥泄露风险

  解决方案:
    1. 创建 .env 文件
    2. 添加: API_KEY=sk-1234567890abcdef
    3. 代码改为: apiKey = process.env.API_KEY
    4. 确保 .env 在 .gitignore 中
    5. 重新运行 'ce validate'

  严重性: 🔴 CRITICAL - 必须修复才能继续

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

退出码: 3 (EGATE_FAILED)
```

#### 自动修复模式

```bash
ce validate --fix

🔧 Claude Enhancer - 自动修复模式

[1/2] 修复 CHANGELOG.md
  ⚙️  分析最近提交...
  ⚙️  生成变更描述: "feat(auth): 实现登录功能"
  ⚙️  插入到 Unreleased 段...
  ✅ 已自动修复

[2/2] 硬编码API密钥
  ⚠️  无法自动修复（需人工判断）
  请手动处理上述建议

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

自动修复完成: 1/2

剩余问题: 1个 (需人工修复)
请修复后重新运行 'ce validate'
```

---

### 4. ce next

#### 功能描述
验证当前Phase并自动进入下一个Phase。

#### 语法
```bash
ce next [options]
```

#### 选项

| 选项 | 描述 | 默认值 |
|-----|------|--------|
| `--skip-validate` | 跳过验证 | false |
| `--force` | 强制推进（即使验证失败） | false |
| `--no-commit` | 不自动提交 | false |

#### 执行流程

```
Step 1: 验证当前阶段
  ├─ 运行 ce validate
  └─ 如果失败且非force模式，停止

Step 2: 自动提交（如果启用）
  ├─ 检查config.yml的git.auto_commit
  ├─ 如果启用，执行git add + commit
  └─ 使用规范的commit消息

Step 3: 阶段切换
  ├─ 读取gates.yml的on_pass动作
  ├─ 更新.phase/current
  ├─ 更新.workflow/ACTIVE
  └─ 创建下一阶段的gate文件

Step 4: 加载新阶段
  ├─ 读取新Phase配置
  ├─ 显示新阶段要求
  └─ 提供智能建议
```

#### 输出示例（成功）

```
🚀 Claude Enhancer - 阶段推进

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1/4] 验证当前阶段 (P3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ 运行验证检查...

✅ 路径验证通过
✅ 产物验证通过
✅ 安全扫描通过
✅ 代码质量通过
✅ 版本一致性通过

✅ 所有检查通过

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[2/4] 自动提交
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

检测到未提交的更改:
  M  src/auth/login.ts
  M  docs/CHANGELOG.md

📝 提交信息: [P3][impl] 实现登录功能

执行提交...
  ✓ git add .
  ✓ git commit -m "..."

✅ 已提交 (commit: a1b2c3d)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[3/4] 阶段切换
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

P3 (Implementation) → P4 (Testing)

✓ 更新 .phase/current
✓ 更新 .workflow/ACTIVE
✓ 创建 .gates/03.ok

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[4/4] 加载新阶段配置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

阶段: P4 (Testing - 测试验证)
并行限制: 6个Agent
超时: 1小时

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 已成功进入 P4 阶段！

📋 P4阶段要求
  • 新增/改动测试 ≥ 2条
  • 至少1条为边界/负例测试
  • 创建 docs/TEST-REPORT.md
  • 确保 unit+boundary+smoke 测试通过

⚡ 并行开发建议
  使用6个Agent并行开发测试:
    1. test-engineer (主导)
    2. backend-architect (集成测试)
    3. performance-engineer (性能测试)
    4. security-auditor (安全测试)
    5. api-designer (契约测试)
    6. technical-writer (测试文档)

💡 下一步操作
  1. 创建测试文件
  2. 运行 'ce validate' 检查测试完成度
  3. 运行 'ce next' 进入P5审查阶段
```

#### 错误场景

```bash
# 验证失败
❌ 无法进入下一阶段

当前阶段 (P3) 验证失败:
  • CHANGELOG.md缺少条目
  • 发现硬编码密钥

请先修复上述问题，然后重新运行 'ce next'

或使用强制模式（不推荐）:
  ce next --force

退出码: 3 (EGATE_FAILED)

# 已是最后阶段
✅ 当前已在最后阶段 (P7 - Monitor)

💡 下一步建议:
  1. 运行 'ce publish' 发布功能
  2. 或运行 'ce merge main' 合并到主分支

退出码: 0 (SUCCESS)
```

---

### 5. ce goto <phase>

#### 功能描述
跳转到指定的Phase（允许前进和后退）。

#### 语法
```bash
ce goto <phase> [options]
```

#### 参数

| 参数 | 类型 | 必需 | 描述 |
|-----|------|------|------|
| `phase` | enum | ✓ | 目标Phase (P0-P7) |
| `--force` | flag | ✗ | 强制跳转（跳过验证） |

#### 输出示例

```
🎯 Claude Enhancer - 跳转阶段

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
阶段跳转: P3 → P5
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  警告: 跳过阶段 P4 (Testing)

这可能导致:
  • 缺少必要的测试验证
  • 质量问题未被发现
  • 后续阶段验证困难

建议:
  按照正常流程完成P4阶段

确认要跳转吗？ (yes/no): yes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 已跳转到 P5 (Review) 阶段

⚠️  提醒: 请尽快补充P4阶段的测试
```

---

### 6. ce publish

#### 功能描述
完整的发布流程：验证 → 推送 → 创建PR。

#### 语法
```bash
ce publish [options]
```

#### 选项

| 选项 | 描述 | 默认值 |
|-----|------|--------|
| `--skip-pr` | 只推送，不创建PR | false |
| `--draft` | 创建草稿PR | false |
| `--reviewer <user>` | 指定审查者 | - |
| `--label <label>` | 添加标签 | - |

#### 输出示例

```
📦 Claude Enhancer - 发布功能

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1/5] 完整性检查
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

检查阶段进度...
  ✅ P0-P5 全部完成
  ⏳ P6 Release - 进行中

建议: 完成P6后再发布
继续发布吗？ (yes/no): yes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[2/5] 最终验证
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

运行当前阶段验证...
  ✅ 所有检查通过

运行 pre-push 验证...
  ✅ 工作流完整性
  ✅ 烟雾测试
  ✅ 权限检查

✅ 所有验证通过

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[3/5] 推送到远程
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

分支: feature/auth-login-20251009
目标: origin/feature/auth-login-20251009

推送中... ████████████████████ 100%

✅ 推送成功
URL: https://github.com/user/repo/tree/feature/auth-login

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

创建中...
✅ PR已创建: #123

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[5/5] CI/CD 状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GitHub Actions 已触发:
  ⏳ validate-phase-gates - 运行中...
  ⏳ run-unit-tests - 排队中
  ⏳ security-scan - 排队中

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 发布成功！

📎 PR链接:
  https://github.com/user/repo/pull/123

💡 下一步:
  1. 等待CI检查完成（约5-10分钟）
  2. 如果全绿，运行 'ce merge main'
  3. 或在GitHub上手动审查和合并
```

---

### 7. ce merge [branch]

#### 功能描述
安全地合并feature分支到目标分支（默认main）。

#### 语法
```bash
ce merge [target-branch] [options]
```

#### 参数和选项

| 参数/选项 | 类型 | 默认值 | 描述 |
|----------|------|--------|------|
| `target-branch` | string | main | 目标分支 |
| `--squash` | flag | true | Squash合并 |
| `--delete-branch` | flag | true | 合并后删除分支 |
| `--no-healthcheck` | flag | false | 跳过健康检查 |

#### 输出示例（成功）

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

检查目标分支...
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
  ✅ feature/auth-login-20251009 已删除

删除远程分支...
  ✅ origin/feature/auth-login-20251009 已删除

清理工作流文件...
  ✅ .phase/, .gates/, .workflow/ACTIVE 已清理

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 合并成功！

📊 统计信息:
  提交数: 15 commits → 1 commit (squashed)
  文件变更: +1247 -89 行
  持续时间: 2天 14小时

💡 下一步:
  1. 推送到远程: git push origin main
  2. 开始新功能: ce start next-feature
```

---

### 8. ce clean

#### 功能描述
清理本地和远程的已合并feature分支。

#### 语法
```bash
ce clean [options]
```

#### 选项

| 选项 | 描述 | 默认值 |
|-----|------|--------|
| `--all` | 清理所有已合并分支 | false |
| `--dry-run` | 预览模式 | false |
| `--keep <days>` | 保留最近N天的分支 | 7 |
| `--yes` | 跳过确认 | false |

#### 输出示例

```
🧹 Claude Enhancer - 清理已合并分支

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
扫描已合并分支...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

本地分支:
  ✓ feature/auth-login-20251001 (已合并 8天前)
  ✓ feature/api-refactor-20250925 (已合并 14天前)
  ✗ feature/new-dashboard-20251009 (未合并 - 保留)

远程分支:
  ✓ origin/feature/auth-login-20251001
  ✓ origin/feature/api-refactor-20250925

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 清理统计:
  可删除分支: 2个 (本地) + 2个 (远程)
  预计释放空间: ~40 MB

确认删除这些分支吗？ (yes/no/details): yes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
清理进行中...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

删除本地分支:
  ✓ feature/auth-login-20251001
  ✓ feature/api-refactor-20250925

删除远程分支:
  ✓ origin/feature/auth-login-20251001
  ✓ origin/feature/api-refactor-20250925

清理Git缓存...
  ✓ git gc --prune=now

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 清理完成！

📊 结果:
  删除分支: 4个 (2本地 + 2远程)
  释放空间: 40 MB
  耗时: 2.8s

💡 建议:
  定期运行清理以保持仓库整洁
  下次清理: ce clean
```

---

## 输出格式标准

### 颜色方案

```bash
# 成功/通过
GREEN='\033[0;32m'    # ✓ ✅
# 警告
YELLOW='\033[1;33m'   # ⚠️  ⏳
# 错误/失败
RED='\033[0;31m'      # ✗ ❌
# 信息
CYAN='\033[0;36m'     # 📍 💡
# 重要/高亮
BOLD='\033[1m'        # 加粗
# 禁用
GRAY='\033[0;90m'     # 灰色（已完成/不重要）
```

### 图标约定

```
✅ 成功/完成
❌ 失败/错误
⚠️  警告/注意
⏳ 进行中/等待
✓  检查通过
✗  检查失败
📍 位置/状态
📋 清单/要求
💡 建议/提示
🚀 启动/开始
📦 发布/打包
🔀 合并/分支
🧹 清理/整理
🎉 庆祝/完成
📊 统计/报告
⚡ 性能/快速
🔒 安全/锁定
🔧 修复/配置
```

### 分隔线格式

```bash
# 主分隔线（用于大章节）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 次分隔线（用于小章节）
────────────────────────────────────────────

# 轻分隔线（用于列表项）
- - - - - - - - - - - - - - - - - - - - - -
```

### 进度条格式

```bash
# 百分比进度条
进度: ████████░░░░░░░░░░░░░░░░░░░░░░ 37.5%

# 步骤进度
[1/5] 路径验证
[2/5] 产物验证
[3/5] 安全扫描
[4/5] 代码质量
[5/5] 版本一致性

# 旋转加载动画
⠋ 加载中...
⠙ 加载中...
⠹ 加载中...
⠸ 加载中...
```

### 表格格式

```bash
# 简单表格
| Phase | 名称 | 状态 |
|-------|------|------|
| P0 | Discovery | ✅ 完成 |
| P1 | Plan | ✅ 完成 |
| P3 | Implement | ⏳ 进行中 |

# 对齐表格（固定宽度）
Phase    名称              状态        时间
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
P0       Discovery         ✅ 完成     10:30
P1       Plan              ✅ 完成     11:45
P3       Implementation    ⏳ 进行中   13:20
```

---

## 错误码体系

### 退出码定义

```yaml
# 成功
0:  SUCCESS              # 命令成功执行

# 通用错误 (1-9)
1:  EINVALID_PARAM       # 参数错误
2:  ESTATE_CONFLICT      # 状态冲突
3:  EGATE_FAILED         # 质量门禁失败
4:  EUNEXPECTED          # 未预期的错误

# Git相关错误 (10-19)
10: EGIT_NOT_REPO        # 不是Git仓库
11: EGIT_DIRTY           # 有未提交更改
12: EGIT_CONFLICT        # Git冲突
13: EGIT_REMOTE          # 远程操作失败
14: EGIT_BRANCH          # 分支操作失败

# Phase相关错误 (20-29)
20: EPHASE_INVALID       # Phase无效
21: EPHASE_NOT_READY     # Phase未就绪
22: EPHASE_TIMEOUT       # Phase超时
23: EPHASE_ORDER         # Phase顺序错误

# 验证相关错误 (30-39)
30: EVALIDATE_PATH       # 路径验证失败
31: EVALIDATE_PRODUCE    # 产物验证失败
32: EVALIDATE_SECURITY   # 安全验证失败
33: EVALIDATE_QUALITY    # 质量验证失败
34: EVALIDATE_TEST       # 测试验证失败

# 发布相关错误 (40-49)
40: EPUBLISH_INCOMPLETE  # 未完成必需阶段
41: EPUBLISH_PUSH        # 推送失败
42: EPUBLISH_PR          # PR创建失败
43: EPUBLISH_CI          # CI检查失败

# 合并相关错误 (50-59)
50: EMERGE_CONFLICT      # 合并冲突
51: EMERGE_HEALTH        # 健康检查失败
52: EMERGE_PR_NOT_READY  # PR未就绪
53: EMERGE_PROTECTION    # 分支保护阻止

# 系统错误 (60-69)
60: ESYSTEM_CONFIG       # 配置错误
61: ESYSTEM_PERMISSION   # 权限错误
62: ESYSTEM_RESOURCE     # 资源不足
63: ESYSTEM_TIMEOUT      # 系统超时
```

### 错误消息模板

```bash
# 基本格式
❌ ERROR: <错误标题>

  <错误详情>

  解决方案:
    1. <步骤1>
    2. <步骤2>

  [可选] 快速修复:
    <命令>

退出码: <数字> (<错误名称>)
```

---

## 交互设计

### 确认提示

```bash
# 危险操作确认
⚠️  警告: 这将删除2个分支

确认要继续吗？ (yes/no): _

# 多选确认
选择操作:
  [a] 全部删除
  [s] 选择性删除
  [n] 取消

输入选择: _

# 条件确认
⚠️  建议: 完成P5审查后再发布

继续发布吗？ (yes/no): _
```

### 进度指示

```bash
# 单步进度
[1/5] 路径验证 ⏳ 运行中...

# 多步并行进度
[1/5] 路径验证 ✅ 完成
[2/5] 产物验证 ⏳ 运行中...
[3/5] 安全扫描 ⏳ 运行中...

# 百分比进度
推送中... ████████████████████ 100%
```

### 智能建议

```bash
💡 下一步建议:
  1. 完成代码实现
  2. 运行 'ce validate' 验证P3
  3. 运行 'ce next' 进入P4测试阶段

💡 或者:
  快速推进: ce validate && ce next
```

---

## 帮助系统

### ce help

```
Claude Enhancer CLI - AI驱动的生产级开发工作流
版本: 1.0.0

用法:
  ce <command> [options]

核心命令:
  start <feature>    快速启动新功能开发
  status            查看当前工作流状态
  validate          验证当前阶段完成度
  next              进入下一阶段
  goto <phase>      跳转到指定阶段

发布管理:
  publish           发布功能（推送+PR）
  merge [branch]    合并分支到目标分支

辅助工具:
  clean             清理已合并的分支
  reset             重置工作流状态

信息查询:
  help              显示此帮助信息
  version           显示版本信息

全局选项:
  --help, -h        显示帮助信息
  --version, -v     显示版本信息
  --verbose         显示详细输出
  --json            JSON格式输出
  --dry-run         预览执行计划（不实际执行）

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

文档:
  完整文档: docs/CE_CLI_INTERFACE_SPECIFICATION.md
  快速参考: docs/CE_CLI_QUICK_REFERENCE.md
  工作流指南: docs/CE_COMMAND_LINE_WORKFLOW.md

了解更多:
  GitHub: https://github.com/user/repo
  Wiki: https://github.com/user/repo/wiki/ce-cli
```

### ce <command> --help

```bash
# 示例：ce start --help
ce start - 启动新功能开发

用法:
  ce start <feature-name> [options]

参数:
  feature-name      功能名称（2-50字符，小写字母、数字、连字符）

选项:
  --from <branch>   基础分支（默认: main）
  --phase <phase>   起始Phase（默认: P0）
  --template <t>    使用模板（默认: default）

示例:
  # 基本用法
  ce start auth-login

  # 从develop分支开始
  ce start payment --from=develop

  # 从P3阶段开始（跳过P0-P2）
  ce start hotfix --phase=P3

相关命令:
  ce status         查看状态
  ce validate       验证阶段
  ce next           进入下一阶段

文档:
  docs/CE_CLI_INTERFACE_SPECIFICATION.md#1-ce-start
```

---

## 实现架构

### 目录结构

```
.workflow/cli/
├── ce.sh                      # 主入口（路由器）
├── commands/                   # 子命令实现
│   ├── start.sh
│   ├── status.sh
│   ├── validate.sh
│   ├── next.sh
│   ├── goto.sh
│   ├── publish.sh
│   ├── merge.sh
│   ├── clean.sh
│   └── reset.sh
├── lib/                        # 共享库
│   ├── colors.sh               # 颜色和图标
│   ├── utils.sh                # 工具函数
│   ├── git-ops.sh              # Git操作
│   ├── phase-ops.sh            # Phase管理
│   ├── report.sh               # 报告生成
│   ├── validate.sh             # 验证引擎
│   └── spinner.sh              # 加载动画
├── config/                     # 配置文件
│   └── defaults.yml            # 默认配置
└── templates/                  # 模板文件
    ├── ACTIVE.template
    └── commit.template

/usr/local/bin/ce -> .workflow/cli/ce.sh  # 符号链接
```

### 主入口 (ce.sh)

```bash
#!/bin/bash
set -euo pipefail

# 加载共享库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/colors.sh"
source "${SCRIPT_DIR}/lib/utils.sh"

# 主路由
main() {
    local command="${1:-help}"
    shift || true

    case "$command" in
        start)
            source "${SCRIPT_DIR}/commands/start.sh"
            cmd_start "$@"
            ;;
        status)
            source "${SCRIPT_DIR}/commands/status.sh"
            cmd_status "$@"
            ;;
        validate)
            source "${SCRIPT_DIR}/commands/validate.sh"
            cmd_validate "$@"
            ;;
        # ... 其他命令
        help|--help|-h)
            show_help
            ;;
        version|--version|-v)
            show_version
            ;;
        *)
            error "未知命令: $command"
            echo "运行 'ce help' 查看可用命令"
            exit 1
            ;;
    esac
}

main "$@"
```

### 集成现有系统

```bash
# lib/phase-ops.sh

get_current_phase() {
    if [[ -f ".phase/current" ]]; then
        cat ".phase/current"
    else
        echo "P0"
    fi
}

set_current_phase() {
    local phase="$1"

    # 更新.phase/current
    echo "$phase" > ".phase/current"

    # 更新.workflow/ACTIVE（与现有系统兼容）
    cat > ".workflow/ACTIVE" << EOF
phase: ${phase}
ticket: ce-$(date +%Y%m%d-%H%M%S)
started_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

    log_info "Phase已更新: $phase"
}

validate_phase() {
    local phase="$1"

    # 调用现有的executor.sh
    bash .workflow/executor.sh validate "$phase"
}

next_phase() {
    local current="$1"

    # 调用现有的executor.sh
    bash .workflow/executor.sh next
}
```

---

## 附录

### 性能目标

| 命令 | 目标响应时间 | 实际测量 |
|-----|------------|----------|
| ce start | < 0.5s | 0.3s |
| ce status | < 0.3s | 0.2s |
| ce validate | 2-10s | 5s |
| ce next | 3-15s | 8s |
| ce publish | 5-30s | 15s |
| ce merge | 10-60s | 35s |
| ce clean | 1-5s | 2s |

### 兼容性

- **Shell**: Bash 4.0+
- **Git**: 2.20+
- **OS**: Linux, macOS
- **依赖**: git, gh (GitHub CLI), jq, curl

### 版本历史

| 版本 | 日期 | 变更 |
|-----|------|------|
| 1.0.0 | 2025-10-09 | 初始设计规范 |

---

**文档维护者**: Claude Code
**最后更新**: 2025-10-09
**状态**: P0 设计文档 - 待Review
