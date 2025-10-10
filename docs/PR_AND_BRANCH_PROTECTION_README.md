# PR模板和Branch Protection完整指南

## 📚 文档导航

本套文档提供Claude Enhancer项目的PR和Branch Protection完整解决方案。

### 核心文档

| 文档 | 用途 | 适用人群 |
|------|------|----------|
| [PR模板](.github/PULL_REQUEST_TEMPLATE.md) | 创建PR时的标准模板 | 所有开发者 |
| [Branch Protection配置指南](BRANCH_PROTECTION_SETUP.md) | 配置仓库分支保护 | 管理员、DevOps |
| [PR模板使用指南](PR_TEMPLATE_USAGE_GUIDE.md) | PR模板详细使用说明 | 所有开发者 |
| [CODEOWNERS](.github/CODEOWNERS) | 代码所有者配置 | 管理员、Team Lead |

---

## 🚀 快速开始

### 新团队成员（5分钟入门）

1. **了解PR流程**
   ```bash
   # 阅读PR模板使用指南
   cat docs/PR_TEMPLATE_USAGE_GUIDE.md
   ```

2. **创建第一个PR**
   ```bash
   # 1. 创建feature分支
   git checkout -b feature/your-feature

   # 2. 开发并提交
   git add .
   git commit -m "feat: your feature"

   # 3. 推送
   git push origin feature/your-feature

   # 4. 创建PR（模板会自动加载）
   gh pr create
   ```

3. **填写PR模板**
   - 检查当前Phase
   - 勾选must_produce清单
   - 填写测试证据
   - 提供回滚方案

### 仓库管理员（30分钟配置）

1. **配置Branch Protection**
   ```bash
   # 使用自动化脚本
   ./scripts/setup_branch_protection.sh

   # 或手动配置
   # 参考: docs/BRANCH_PROTECTION_SETUP.md
   ```

2. **配置CODEOWNERS**
   ```bash
   # 复制模板到仓库
   cp .github/CODEOWNERS .github/CODEOWNERS

   # 根据团队调整
   vim .github/CODEOWNERS
   ```

3. **验证配置**
   ```bash
   # 运行验证脚本
   ./scripts/setup_branch_protection.sh --dry-run

   # 或手动验证
   gh api repos/{owner}/{repo}/branches/main/protection
   ```

---

## 📋 文档详解

### 1. PR模板 (.github/PULL_REQUEST_TEMPLATE.md)

**特点**：
- ✅ Phase感知（自动识别P0-P7）
- ✅ 动态产出清单（根据Phase显示must_produce）
- ✅ 质量门禁集成（4层保障体系）
- ✅ 回滚方案强制
- ✅ 测试证据要求

**核心章节**：
- Phase信息
- Phase产出要求
- 质量门禁检查
- 测试证据
- 回滚方案
- 影响范围
- 审查清单

**何时使用**：
- 每次创建PR时自动加载
- 作为PR质量的检查清单
- 作为Code Review的参考

### 2. Branch Protection配置指南 (BRANCH_PROTECTION_SETUP.md)

**内容包括**：
- ✅ 配置概述和保护目标
- ✅ 前置准备和权限检查
- ✅ Web界面配置步骤（带详细说明）
- ✅ CLI配置方法（自动化脚本）
- ✅ CODEOWNERS完整设置
- ✅ 配置验证方法
- ✅ 常见问题排查
- ✅ 最佳实践建议

**何时使用**：
- 新仓库初始化
- 提升安全级别
- 团队流程规范化
- 问题排查

### 3. PR模板使用指南 (PR_TEMPLATE_USAGE_GUIDE.md)

**内容包括**：
- ✅ 完整PR工作流
- ✅ 各Phase详细示例（P0-P7）
- ✅ 常见场景（Hotfix、多Phase合并等）
- ✅ 最佳实践
- ✅ 自动化技巧

**何时使用**：
- 新手学习PR流程
- 查找特定Phase的示例
- 了解最佳实践
- 设置自动化

### 4. CODEOWNERS (.github/CODEOWNERS)

**特点**：
- ✅ 按Phase分配审查责任
- ✅ 按模块分配代码所有者
- ✅ 详细注释和说明
- ✅ 涵盖所有关键路径

**何时使用**：
- 配置自动审查分配
- 明确代码责任
- 团队成员变动时更新

---

## 🎯 使用场景地图

### 场景1: 我是开发者，要提交代码

```
你的路径:
1. 查看: PR模板使用指南 → "使用流程"章节
2. 参考: 对应Phase的示例（如P3 Implementation）
3. 创建: 使用gh pr create（模板自动加载）
4. 填写: 根据当前Phase勾选清单
```

### 场景2: 我是新管理员，要配置仓库

```
你的路径:
1. 阅读: Branch Protection配置指南 → 完整阅读
2. 准备: 检查权限、安装gh cli、准备CODEOWNERS
3. 配置: 运行setup_branch_protection.sh脚本
4. 验证: 按指南验证配置是否生效
```

### 场景3: 我是Team Lead，要分配审查责任

```
你的路径:
1. 编辑: .github/CODEOWNERS
2. 参考: Branch Protection配置指南 → CODEOWNERS章节
3. 配置: 按模块和Phase分配所有者
4. 验证: 使用gh api验证语法
```

### 场景4: PR被Branch Protection阻止了

```
你的路径:
1. 查看: Branch Protection配置指南 → "常见问题"章节
2. 检查: Required status checks是否都通过
3. 验证: CODEOWNERS是否正确审查
4. 解决: 按指南修复具体问题
```

### 场景5: 要做紧急Hotfix

```
你的路径:
1. 参考: PR模板使用指南 → "常见场景" → "Hotfix"
2. 使用: 简化的Hotfix PR模板
3. 遵循: 快速验证流程
4. 部署: 金丝雀发布策略
```

---

## 🛠️ 工具和脚本

### 自动化脚本

| 脚本 | 功能 | 位置 |
|------|------|------|
| setup_branch_protection.sh | 配置Branch Protection | scripts/ |
| verify_ce_integration.sh | 验证CE集成 | 见配置指南 |
| create_pr_with_phase.sh | 自动填充Phase信息 | 见使用指南 |
| validate_must_produce.sh | 验证产出 | 需自行创建 |

### GitHub CLI命令参考

```bash
# Branch Protection相关
gh api repos/{owner}/{repo}/branches/main/protection  # 查看保护规则
gh pr create --template p3_implementation.md          # 使用特定模板
gh pr checks <pr-number>                              # 查看PR检查状态

# CODEOWNERS相关
gh api repos/{owner}/{repo}/codeowners/errors         # 验证CODEOWNERS语法

# PR相关
gh pr create                                          # 创建PR（自动加载模板）
gh pr view <pr-number>                                # 查看PR详情
gh pr merge <pr-number> --squash                      # 合并PR
```

---

## 📊 质量保障体系集成

### 4层保障机制

```
┌─────────────────────────────────────────┐
│ Layer 4: PR Review（人工把关）          │
│  - PR模板强制检查                        │
│  - CODEOWNERS自动审查                   │
│  - Required approvals                   │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ Layer 3: Branch Protection（远程保护）  │
│  - 禁止直接push                         │
│  - Required status checks               │
│  - Linear history                       │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ Layer 2: Workflow框架（流程引导）       │
│  - 8-Phase工作流                        │
│  - Must_produce验证                     │
│  - Phase gates检查                      │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ Layer 1: Git Hooks（本地强制）          │
│  - pre-commit检查                       │
│  - 路径白名单                           │
│  - 安全扫描                             │
│  - Linting                              │
└─────────────────────────────────────────┘
```

### PR模板在其中的作用

- **连接**本地开发和远程审查
- **强化**质量要求的可见性
- **标准化**PR格式和内容
- **提供**回滚和部署指导

---

## 🎓 学习路径

### 初级（1-2天）

**目标**: 能够创建符合规范的PR

1. 阅读PR模板使用指南 → "使用流程"
2. 实践创建一个简单的PR
3. 理解当前Phase的must_produce要求
4. 学会填写测试证据

### 中级（3-5天）

**目标**: 理解整个质量保障体系

1. 深入学习8-Phase工作流
2. 了解各Phase的详细要求
3. 掌握回滚方案编写
4. 理解Branch Protection机制

### 高级（1-2周）

**目标**: 能够配置和优化整个系统

1. 学习Branch Protection配置
2. 自定义CODEOWNERS
3. 编写自动化脚本
4. 优化团队工作流

---

## 🔍 常见问题快速索引

| 问题 | 查看文档 | 章节 |
|------|----------|------|
| 如何创建PR？ | PR模板使用指南 | 使用流程 |
| PR需要填写什么？ | PR模板使用指南 | 各Phase示例 |
| 如何配置Branch Protection？ | Branch Protection配置指南 | 配置步骤 |
| Status check不出现怎么办？ | Branch Protection配置指南 | 常见问题 Q1 |
| CODEOWNERS不生效？ | Branch Protection配置指南 | 常见问题 Q2 |
| 如何做紧急修复？ | PR模板使用指南 | 常见场景 → Hotfix |
| 管理员能绕过规则吗？ | Branch Protection配置指南 | 常见问题 Q3 |
| 如何验证配置？ | Branch Protection配置指南 | 验证配置 |
| PR无法合并？ | Branch Protection配置指南 | 常见问题 Q4 |
| 如何设置自动化？ | PR模板使用指南 | 自动化技巧 |

---

## 📈 持续改进

### 定期审查（建议每季度）

- [ ] Review PR模板是否需要更新
- [ ] 检查Branch Protection规则是否合适
- [ ] 更新CODEOWNERS（人员变动）
- [ ] 收集团队反馈
- [ ] 优化自动化脚本

### 度量指标

追踪以下指标以评估效果：

```
质量指标:
- PR平均review时间
- PR一次通过率
- 生产环境bug数量
- 回滚次数

流程指标:
- PR模板完整度
- Branch Protection覆盖率
- CODEOWNERS更新频率
- 自动化程度
```

### 团队培训

- 新成员入职培训（必修）
- 季度质量复盘会议
- 最佳实践分享
- 持续文档更新

---

## 🤝 贡献和反馈

### 如何贡献

如果你发现文档有改进空间：

1. 在Issues中提出建议
2. 提交PR改进文档
3. 分享使用经验
4. 贡献自动化脚本

### 获取帮助

- **文档问题**: 查看本README的常见问题索引
- **配置问题**: 参考Branch Protection配置指南
- **使用问题**: 参考PR模板使用指南
- **技术支持**: 在Issues中提问

---

## 📝 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2025-01-XX | 初始版本 |
| 1.1 | 2025-XX-XX | 添加更多示例 |
| 1.2 | 2025-XX-XX | 增强自动化支持 |

---

## 🔗 相关资源

### Claude Enhancer文档
- [8-Phase工作流](.claude/WORKFLOW.md)
- [质量保障体系](WORKFLOW_QUALITY_ASSURANCE.md)
- [Gates配置](.workflow/gates.yml)

### 外部资源
- [GitHub Branch Protection文档](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests)
- [GitHub CODEOWNERS文档](https://docs.github.com/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

## ✅ 配置检查清单

使用此清单确保完整配置：

### 管理员检查清单

- [ ] Branch Protection已配置
  - [ ] main分支保护已启用
  - [ ] Required status checks已配置
  - [ ] Required approvals已设置
  - [ ] Linear history已启用

- [ ] CODEOWNERS已配置
  - [ ] 文件位置正确（.github/CODEOWNERS）
  - [ ] 所有关键路径有owner
  - [ ] 语法验证通过
  - [ ] "Require review from Code Owners"已启用

- [ ] PR模板已配置
  - [ ] 模板文件存在
  - [ ] 团队成员知道如何使用

- [ ] CI/CD已配置
  - [ ] Workflow文件存在
  - [ ] Job名称与status checks匹配
  - [ ] 在所有PR上触发

- [ ] 文档已更新
  - [ ] README包含PR流程说明
  - [ ] 团队已培训

### 开发者检查清单

- [ ] 理解8-Phase工作流
- [ ] 知道如何创建符合规范的PR
- [ ] 理解当前Phase的must_produce要求
- [ ] 知道如何查看CI状态
- [ ] 知道如何处理PR被阻止的情况

---

**开始使用**: 根据你的角色，从"使用场景地图"中选择对应路径开始！

**完整体系**: PR模板 + Branch Protection + CODEOWNERS = 生产级质量保障

**持续改进**: 这是一个活的文档体系，欢迎反馈和贡献！
