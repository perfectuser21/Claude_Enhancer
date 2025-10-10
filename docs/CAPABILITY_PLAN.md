# 能力与保障体系增强计划（P1）

**日期**: 2025-10-09
**Phase**: P1 (Plan)
**目标**: 实施自动化机制，解决"未开分支/未进工作流"问题

---

## 执行摘要

基于P0技术探索和用户提供的详细规划，本计划实施**能力增强系统**，通过自动化机制和AI契约，彻底解决两个核心问题：

1. **为什么AI/人有时没开新分支就改了** → 实施自动分支创建机制
2. **为什么没有进入工作流就开始动手** → 创建强制契约文档

**核心目标**：
- ✅ 创建一键初始化脚本（bootstrap.sh）
- ✅ 增强pre-commit自动开分支
- ✅ 创建AI操作契约文档
- ✅ 创建能力验证矩阵
- ✅ 创建系统化故障定位指南

**预估工作量**: 4小时
**风险等级**: LOW（纯增强，向后兼容）

---

## 任务清单

### 🎯 任务1：创建一键初始化脚本
**优先级**: P0 (Critical)
**工作量**: 1小时
**负责文件**: `tools/bootstrap.sh`

**子任务**：
1.1 配置git hooks路径自动设置
1.2 设置所有脚本执行权限
1.3 检查必要工具（jq/yq/shellcheck）
1.4 可选安装lint工具
1.5 创建初始化验证检查

**技术细节**：
```bash
#!/usr/bin/env bash
set -euo pipefail

# 核心配置
git config core.hooksPath .git/hooks
chmod +x .git/hooks/* || true
chmod +x .workflow/*.sh .workflow/**/*.sh 2>/dev/null || true

# 工具检查
command -v jq >/dev/null || echo "⚠️  Please install jq"
command -v yq >/dev/null || echo "⚠️  Please install yq"
command -v shellcheck >/dev/null || echo "⚠️  Please install shellcheck"

echo "✅ Hooks path & permissions set"
```

**验收标准**：
- [ ] 脚本创建且可执行
- [ ] git config正确设置
- [ ] 所有hooks有执行权限
- [ ] 工具检查输出清晰
- [ ] Windows/WSL兼容性说明

---

### 🎯 任务2：增强pre-commit自动开分支
**优先级**: P0 (Critical)
**工作量**: 1小时
**负责文件**: `.git/hooks/pre-commit`

**子任务**：
2.1 添加环境变量CE_AUTOBRANCH检测
2.2 实现自动分支创建逻辑
2.3 自动初始化.phase/current
2.4 添加时间戳确保分支唯一性
2.5 保留手动模式作为默认

**技术细节**：
```bash
# 在pre-commit顶部添加
branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$branch" == "main" ]]; then
    if [[ "${CE_AUTOBRANCH:-0}" == "1" ]]; then
        slug="auto-$(date +%Y%m%d-%H%M%S)"
        git switch -c "feature/P1-${slug}" main
        echo "P1" > .phase/current
        echo "ℹ️  Auto-created branch feature/P1-${slug}"
        echo "   Please re-run your command"
        exit 1
    else
        echo "❌ Cannot commit to main. Run:"
        echo "   git switch -c feature/P1-<description>"
        echo "   echo P1 > .phase/current"
        exit 1
    fi
fi
```

**验收标准**：
- [ ] 手动模式正常报错
- [ ] CE_AUTOBRANCH=1时自动创建
- [ ] 分支名唯一且规范
- [ ] .phase/current自动创建
- [ ] 用户提示清晰

---

### 🎯 任务3：创建AI操作契约文档
**优先级**: P1 (High)
**工作量**: 0.5小时
**负责文件**: `docs/AI_CONTRACT.md`

**子任务**：
3.1 创建系统指令模板（长期固定）
3.2 定义准备序列（3步骤）
3.3 明确拒绝策略
3.4 提供用户提示模板
3.5 创建中英文双语版本

**内容大纲**：
```markdown
# AI操作契约

## 系统指令（System Instructions）
在任何编程任务中，必须先执行准备序列：
1. 仓库自检（git根目录，分支≠main）
2. 工作流检查（.phase/current存在）
3. 分支规范检查（feature/fix/hotfix/chore）

## 拒绝策略（Rejection Policy）
若任一条件未满足：
- 拒绝写入文件
- 仅输出修复命令
- 不得继续生成代码

## 用户提示模板（User Prompt Template）
任务描述：...
期望阶段：P1
严格执行准备序列
```

**验收标准**：
- [ ] 契约文档清晰完整
- [ ] 可直接复制给AI使用
- [ ] 包含具体命令示例
- [ ] 中英文版本
- [ ] 集成到CLAUDE.md

---

### 🎯 任务4：创建能力验证矩阵
**优先级**: P1 (High)
**工作量**: 1小时
**负责文件**: `docs/CAPABILITY_MATRIX.md`

**子任务**：
4.1 创建能力编号体系（C0-C9）
4.2 定义验证方式（本地+CI）
4.3 描述失败表现
4.4 提供修复动作
4.5 关联测试脚本

**表格结构**：
```markdown
| 能力ID | 能力名称 | 本地验证 | CI验证 | 失败表现 | 修复动作 |
|--------|---------|---------|--------|---------|---------|
| C0 | 强制新分支 | pre-commit L140 | Branch Protection | 提交失败 | 运行bootstrap.sh |
| C1 | 强制工作流 | .phase/current检查 | Layer 2 | 拒绝提交 | echo P1 > .phase/current |
...
```

**验收标准**：
- [ ] 10个核心能力全覆盖
- [ ] 验证方式具体到行号
- [ ] 失败表现描述准确
- [ ] 修复动作可执行
- [ ] 关联测试用例

---

### 🎯 任务5：创建故障定位指南
**优先级**: P2 (Medium)
**工作量**: 0.5小时
**负责文件**: `docs/TROUBLESHOOTING_GUIDE.md`

**子任务**：
5.1 定义5种故障模式（FM-1到FM-5）
5.2 描述症状表现
5.3 提供定位方法
5.4 给出修复步骤
5.5 添加预防措施

**故障模式**：
```markdown
## FM-1: 本地钩子没生效
- 症状：能在main提交
- 定位：git config core.hooksPath
- 修复：运行bootstrap.sh

## FM-2: 开发者用了--no-verify
- 症状：本地绕过，CI失败
- 结论：设计预期，CI兜底

## FM-3: AI在未初始化目录操作
- 症状：无Hook触发
- 定位：git rev-parse --is-inside-work-tree
- 修复：要求AI只在仓库根执行

## FM-4: CI未设为Required
- 症状：红色CI仍能合并
- 修复：Branch Protection设置

## FM-5: 分支命名不规范
- 症状：本地过，CI拒绝
- 修复：使用规范分支名
```

**验收标准**：
- [ ] 5种故障模式完整
- [ ] 症状描述准确
- [ ] 定位方法可操作
- [ ] 修复步骤清晰
- [ ] 包含预防建议

---

## 受影响文件清单

### 新增文件（5个）
| 文件路径 | 用途 | 行数预估 |
|---------|-----|---------|
| `tools/bootstrap.sh` | 一键初始化脚本 | 100 |
| `docs/AI_CONTRACT.md` | AI操作契约 | 150 |
| `docs/CAPABILITY_MATRIX.md` | 能力验证矩阵 | 200 |
| `docs/TROUBLESHOOTING_GUIDE.md` | 故障定位指南 | 180 |
| `docs/CAPABILITY_SPIKE.md` | P0技术探索（已创建） | 250 |

**总计**: 5个新文件，约880行

### 修改文件（2个）
| 文件路径 | 修改内容 | 影响范围 |
|---------|---------|---------|
| `.git/hooks/pre-commit` | 添加自动分支逻辑 | 小（+30行） |
| `CLAUDE.md` | 集成AI契约 | 小（+20行） |

---

## 回滚方案

### 回滚触发条件
1. 自动分支创建导致意外行为
2. Bootstrap脚本破坏现有配置
3. AI契约导致工作流阻塞

### 回滚步骤

#### Level 1: 禁用自动分支（1分钟）
```bash
unset CE_AUTOBRANCH
# 或在pre-commit中注释掉自动分支代码
```

#### Level 2: 恢复手动配置（2分钟）
```bash
git config --unset core.hooksPath
# 手动设置回原路径
```

#### Level 3: 完全回滚（5分钟）
```bash
git checkout main
git branch -D feature/P0-capability-enhancement
git reset --hard HEAD~5
```

### 回滚验证
- [ ] 原有功能正常
- [ ] 手动模式可用
- [ ] CI检查通过

---

## 技术依赖

| 工具 | 用途 | 必需性 | 缺失时行为 |
|------|------|--------|-----------|
| bash | 脚本执行 | 必需 | 无法运行 |
| git | 版本控制 | 必需 | 无法运行 |
| jq | JSON解析 | 可选 | 警告提示 |
| yq | YAML解析 | 可选 | 警告提示 |
| shellcheck | Shell检查 | 可选 | 警告提示 |

---

## 风险分析

| 风险 | 概率 | 影响 | 缓解措施 |
|-----|-----|-----|---------|
| 自动分支名冲突 | 极低 | 低 | 时间戳保证唯一 |
| Bootstrap覆盖配置 | 低 | 中 | 先备份再执行 |
| Windows不兼容 | 低 | 低 | 提供WSL指南 |
| AI不遵守契约 | 中 | 低 | Hook强制兜底 |

**总体风险**: LOW ✅

---

## 质量门禁

### P1阶段必须通过的检查
- [x] **计划完整性**：5个任务定义清晰
- [x] **文件清单**：新增和修改文件明确
- [x] **回滚方案**：3级回滚步骤
- [x] **风险识别**：4个风险及缓解
- [x] **技术细节**：包含代码示例

### P1 → P2切换条件
1. 本文件（CAPABILITY_PLAN.md）完成
2. 所有任务优先级标注
3. 工作量预估（总计4小时）
4. 创建`.gates/01.ok`标记

---

## 里程碑时间线

```
Hour 1: 任务1（bootstrap.sh）
Hour 2: 任务2（pre-commit增强）
Hour 3: 任务3+5（AI契约+故障指南）
Hour 4: 任务4（能力矩阵）

总计: 4小时
```

---

## 成功标准

### 功能性标准
- [ ] Bootstrap一键初始化成功
- [ ] 自动分支创建工作
- [ ] AI契约文档可用
- [ ] 能力矩阵完整
- [ ] 故障指南实用

### 质量标准
- [ ] 向后完全兼容
- [ ] 文档清晰易懂
- [ ] 测试覆盖完整

---

## 参考资料

- P0阶段输出：`docs/CAPABILITY_SPIKE.md`
- 用户提供的详细规划
- 现有pre-commit实现（629行）

---

**P1阶段结论**: 计划制定完成，技术路线清晰，建议进入P2骨架阶段

**下一步**: 创建`.gates/01.ok`并切换到P2阶段