# 重要决策记录
> 防止AI推翻之前的优化决策

**目的**: 记录关键决策，避免AI在后续开发中违背已确定的原则和优化方向。

---

## 📋 决策条目

### 2025-10-13: 系统定位明确
**决策**: 这是专业级个人工具，不是企业级系统
**原因**:
- 用户是编程小白，个人使用
- 不涉及团队协作
- 避免过度设计和复杂化
- 保持简单易用的初心

**禁止操作**：
- ❌ 添加团队协作功能
- ❌ 添加多用户权限管理
- ❌ 添加商业化部署配置
- ❌ 使用"企业级"、"团队"、"多用户"等术语

**允许操作**：
- ✅ 使用"专业级"、"个人工具"术语
- ✅ 优化单用户体验
- ✅ 简化配置流程
- ✅ 保持功能聚焦

**影响范围**: 所有文档、代码注释、配置文件

---

### 2025-10-13: 简化质量门禁
**决策**: 删除pylint，改用py_compile
**原因**:
- pylint误报太多（E0401, E0611等）
- 90%的错误是误判
- py_compile足够验证语法正确性
- 减少用户困扰和维护成本

**禁止操作**：
- ❌ 重新添加pylint配置
- ❌ 添加其他重量级linter（flake8, mypy等）
- ❌ 过度严格的代码检查

**允许操作**：
- ✅ 使用py_compile验证语法
- ✅ 添加针对性的自定义检查
- ✅ 优化现有检查规则

**相关文件**:
- `.git/hooks/pre-commit`
- `scripts/health-checker.sh`

---

### 2025-10-13: 记忆压缩系统
**决策**: 自动压缩memory-cache，防止token膨胀
**原因**:
- `.claude/memory-cache.json`会随时间增长
- 超过5KB会影响AI上下文理解
- 需要定期压缩保持<5KB

**机制**：
- 30天自动归档旧记忆
- 保留最近30条重要决策
- 压缩历史数据到`.temp/archive/`

**相关文件**:
- `scripts/memory-compressor.py`
- `.claude/memory-cache.json`

**禁止操作**：
- ❌ 无限制增长memory-cache
- ❌ 删除压缩机制
- ❌ 禁用自动归档

---

### 2025-10-13: 文档管理铁律
**决策**: 根目录只保留7个核心文档
**原因**:
- 文档泛滥导致信息混乱
- 用户找不到有用信息
- 临时分析报告应该放在.temp/

**核心文档清单**：
1. README.md
2. CLAUDE.md
3. INSTALLATION.md
4. ARCHITECTURE.md
5. CONTRIBUTING.md
6. CHANGELOG.md
7. LICENSE.md

**禁止操作**：
- ❌ 在根目录创建新的.md文件
- ❌ 创建*_REPORT.md、*_ANALYSIS.md等临时文件
- ❌ 复制文档（README2.md, CLAUDE_NEW.md等）

**允许操作**：
- ✅ 更新现有核心文档
- ✅ 在.temp/analysis/创建临时报告
- ✅ 在docs/子目录下创建结构化文档

**相关文件**:
- `.claude/hooks/pre_write_document.sh`
- `scripts/cleanup_documents.sh`

---

### 2025-10-13: 复杂度控制阈值
**决策**: 设定明确的复杂度上限
**原因**:
- 防止系统过度膨胀
- 保持"个人工具"的简单性
- 强制定期重构和简化

**阈值设定**：
```yaml
max_workflows: 8        # CI workflows数量
max_bdd_scenarios: 15   # BDD场景数量
max_claude_md_lines: 400  # CLAUDE.md长度
max_claude_hooks: 6     # Claude hooks数量
max_git_hooks_backups: 2  # 备份文件数量
```

**禁止操作**：
- ❌ 随意提高阈值
- ❌ 说"临时超标一下"
- ❌ 用`current_exception`永久豁免

**允许操作**：
- ✅ 合并冗余功能以降低数量
- ✅ 使用临时例外（必须设置过期时间）
- ✅ 重构以满足阈值

**相关文件**:
- `.claude/self-check-rules.yaml`
- `scripts/health-checker.sh`

---

### 2025-10-13: Git Hooks强制执行
**决策**: Git hooks是强制的，不可bypass
**原因**:
- 质量门禁必须在提交前执行
- 防止带bug代码进入仓库
- 保持代码质量一致性

**强制规则**：
- pre-commit: 语法检查、版本一致性
- commit-msg: 提交信息规范（Conventional Commits）
- pre-push: 分支保护、完整性检查

**禁止操作**：
- ❌ 频繁使用`git commit --no-verify`
- ❌ 删除git hooks
- ❌ 禁用hooks检查

**允许操作**：
- ✅ 修复hooks检测到的问题
- ✅ 临时禁用（紧急情况，事后必须补修）
- ✅ 优化hooks性能

**相关文件**:
- `.git/hooks/pre-commit`
- `.git/hooks/commit-msg`
- `.git/hooks/pre-push`

---

### 2025-10-13: 版本号统一管理
**决策**: VERSION文件是唯一真实来源
**原因**:
- 版本不一致导致混乱
- 多处定义容易不同步
- 自动化工具需要单一源

**版本管理规则**：
- `VERSION`文件 = 唯一真实来源
- `package.json`、`CLAUDE.md`等自动同步
- 发布前必须验证一致性

**相关工具**：
- `scripts/version-manager.py`
- Git hooks pre-commit检查

**禁止操作**：
- ❌ 手动修改多个地方的版本号
- ❌ 忽略版本不一致警告
- ❌ 跳过版本验证

**允许操作**：
- ✅ 使用version-manager.py统一更新
- ✅ 在VERSION文件中修改版本
- ✅ 让自动化工具同步其他文件

---

### 2025-10-13: 分支保护策略
**决策**: main/master分支禁止直接推送
**原因**:
- 保护主分支稳定性
- 强制PR流程和代码审查
- 防止未经验证的代码进入生产

**四层防护**：
1. 本地Git Hooks（逻辑防护100%）
2. CI/CD验证（权限监控）
3. GitHub Branch Protection（服务端强制）
4. 持续监控（健康检查）

**禁止操作**：
- ❌ 在main/master分支直接commit
- ❌ 绕过分支保护（--no-verify等）
- ❌ 在不相关分支上开发新功能

**允许操作**：
- ✅ 创建feature分支
- ✅ 提交PR进行审查
- ✅ 合并后自动部署

**相关文件**:
- `.git/hooks/pre-push`
- `.claude/hooks/branch_helper.sh`

---

## 🎯 如何使用这个文件

### AI开发者
在修改系统时，**必须先查阅这个文件**，确保不违反已记录的决策。

### 人类开发者
1. **修改前检查**: 看是否有相关决策
2. **重大变更**: 更新或添加决策条目
3. **定期审查**: 每季度审查决策是否仍然适用

### 决策变更流程
如果需要推翻某个决策：
1. 在对应条目下添加"**决策变更**"章节
2. 说明变更原因和新的决策
3. 保留历史记录（不要删除旧决策）
4. 更新"禁止操作"和"允许操作"清单

---

## 📊 决策统计

| 类别 | 决策数量 |
|------|---------|
| 系统定位 | 1 |
| 质量门禁 | 2 |
| 文档管理 | 1 |
| 复杂度控制 | 1 |
| 版本管理 | 1 |
| 分支保护 | 1 |
| **总计** | **7** |

---

**最后更新**: 2025-10-13
**维护者**: Claude Enhancer AI + 用户协作
**版本**: 1.0.0
