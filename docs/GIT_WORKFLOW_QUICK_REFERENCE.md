# Git 工作流快速参考卡片

**Claude Enhancer 5.0 - 多终端并行开发指南**

---

## 🚀 快速开始（3步完成设置）

### Step 1: 设置终端标识
```bash
# 在每个终端的 ~/.bashrc 或 ~/.zshrc 添加
export CE_TERMINAL_ID=t1  # Terminal 1
export CE_TERMINAL_ID=t2  # Terminal 2
export CE_TERMINAL_ID=t3  # Terminal 3

# 立即生效
source ~/.bashrc
```

### Step 2: 验证权限
```bash
# 测试 GitHub SSH 连接
ssh -T git@github.com
# 应该显示: "Hi username! You've successfully authenticated..."

# 检查远程仓库
git remote -v
# 应该显示: origin git@github.com:perfectuser21/Claude_Enhancer.git
```

### Step 3: 安装 ce 命令（待实现）
```bash
# 将在 P3 阶段实现
chmod +x scripts/ce
echo 'export PATH="$PATH:$(pwd)/scripts"' >> ~/.bashrc
```

---

## 📋 常用命令速查

### 创建分支
```bash
# 方式1: 使用 ce 命令（推荐 - P3后可用）
ce branch "auth system"
# 自动生成: feature/P3-t1-20251009-auth-system

# 方式2: 手动创建（当前可用）
phase=$(cat .phase/current)
terminal="${CE_TERMINAL_ID:-t1}"
date=$(date +%Y%m%d)
git checkout -b "feature/${phase}-${terminal}-${date}-your-description"
git push -u origin $(git branch --show-current)
```

### 开发流程
```bash
# 1. 查看状态
ce status  # 或 git status

# 2. 提交更改（自动通过 pre-commit hook）
git add .
git commit -m "feat: implement user authentication"

# 3. 推送到远程
git push

# 4. 创建 PR（P6 阶段）
ce publish  # 或手动生成 PR URL
```

### 发布流程（P6 阶段）
```bash
# 一键发布（质量检查 + PR 创建）
ce publish

# 等效的手动流程
bash .workflow/executor.sh validate  # 验证 Gates
git push origin $(git branch --show-current)
bash scripts/generate_pr_url.sh  # 生成 PR 链接
```

### 清理分支
```bash
# 清理已合并的本地分支
ce clean

# 手动清理
git branch --merged main | grep -v "^\*" | grep -v "main" | xargs git branch -d
git fetch --prune  # 清理远程已删除的追踪
```

---

## 🔄 典型工作流场景

### 场景1: 单个功能开发（1个终端）
```bash
# Terminal 1
export CE_TERMINAL_ID=t1

# 创建分支
ce branch "user authentication"
# → feature/P3-t1-20251009-user-authentication

# 开发 + 提交
git add src/auth/
git commit -m "feat: add JWT authentication"

# 发布
ce publish
# → 自动生成 PR URL 并打开浏览器
```

### 场景2: 并行开发（3个终端）
```bash
# Terminal 1 - 开发认证系统
export CE_TERMINAL_ID=t1
ce branch "auth system"
# → feature/P3-t1-20251009-auth-system

# Terminal 2 - 开发任务管理
export CE_TERMINAL_ID=t2
ce branch "task manager"
# → feature/P3-t2-20251009-task-manager

# Terminal 3 - 开发监控系统
export CE_TERMINAL_ID=t3
ce branch "monitoring"
# → feature/P3-t3-20251009-monitoring

# 三个分支互不冲突，可同时推送
```

### 场景3: 网络失败恢复
```bash
# 推送失败后
git push
# ❌ error: failed to push some refs

# 重试（自动重试3次）
ce publish --retry

# 手动保存离线状态
bash scripts/save_offline_state.sh

# 网络恢复后恢复
ce resume-publish
```

---

## 🛡️ 质量闸门检查项

### Pre-commit 自动检查
- ✅ 分支保护（禁止直推 main）
- ✅ Phase 验证（.phase/current 存在）
- ✅ 路径白名单（allow_paths）
- ✅ 安全扫描（密码/API密钥/私钥）
- ✅ 代码 Linting（shellcheck, eslint, flake8）

### Pre-push 自动检查
- ✅ 工作流完整性（必须有 PLAN.md）
- ✅ 质量评分 ≥ 85
- ✅ 测试覆盖率 ≥ 80%
- ✅ Gate 签名验证（生产分支）
- ✅ Smoke 测试通过

### P6 Publish 检查
- ✅ 当前 Phase = P6
- ✅ 所有 P6 Gates 通过
- ✅ README.md 包含：安装、使用、注意事项
- ✅ CHANGELOG.md 版本号递增
- ✅ Tag 创建成功

---

## 🚨 常见问题排查

### 问题1: "禁止直接提交到 main 分支"
```bash
# 原因：在 main 分支上执行 git commit
git branch --show-current
# → main

# 解决方案1: 自动分支模式
export CE_AUTOBRANCH=1
git commit -m "your message"
# → 自动创建 feature/P1-auto-YYYYMMDD-HHMMSS

# 解决方案2: 手动创建分支
git checkout -b feature/P3-t1-20251009-your-feature
git commit -m "your message"
```

### 问题2: "质量评分 < 85"
```bash
# 查看当前分数
cat .workflow/_reports/quality_score.txt

# 解决方案：提升测试覆盖率
npm test  # 运行测试
pytest --cov  # Python 测试覆盖

# 重新验证
bash .workflow/executor.sh validate
```

### 问题3: "Phase 验证失败"
```bash
# 查看当前 Phase
cat .phase/current

# 查看 must_produce 要求
cat .workflow/gates.yml | grep -A 10 "P$(cat .phase/current | tr -d 'P'):"

# 补全缺失的产出
# 例如 P1 需要 docs/PLAN.md
touch docs/PLAN.md
```

### 问题4: "推送被拒绝（权限）"
```bash
# 检查 SSH 密钥
ssh -T git@github.com

# 重新配置 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub  # 添加到 GitHub Settings → SSH Keys
```

### 问题5: "分支名称冲突"
```bash
# 现象：git checkout -b 报错 "already exists"
git branch
# → feature/P3-t1-20251009-auth-system 已存在

# 解决方案1: 使用不同的终端 ID
export CE_TERMINAL_ID=t2
ce branch "auth system"
# → feature/P3-t2-20251009-auth-system

# 解决方案2: 更改描述
ce branch "auth-system-v2"
# → feature/P3-t1-20251009-auth-system-v2
```

---

## 📊 PR 创建流程

### 自动生成 PR URL
```bash
# 执行 ce publish 后会看到
🔗 在浏览器中打开此链接创建 PR:
https://github.com/perfectuser21/Claude_Enhancer/compare/main...feature/P3-t1-20251009-auth-system?expand=1

# PR 描述会自动包含
✅ Phase 信息（P6）
✅ 质量评分（90）
✅ 测试覆盖率（85%）
✅ Must Produce 清单
✅ 变更历史
✅ 回滚方案
```

### PR 审查清单
```markdown
## 审查者检查项
- [ ] 代码符合项目规范
- [ ] 测试充分（覆盖率 ≥ 80%）
- [ ] 文档完整（README/CHANGELOG更新）
- [ ] 无安全风险
- [ ] 回滚方案可行
- [ ] CI 检查全部通过 ✅
```

### 合并策略
```bash
# GitHub 设置推荐
✅ Squash and merge（推荐）
   - 保持 main 分支历史清晰
   - 一个 PR = 一个 commit

❌ Create a merge commit（不推荐）
   - 历史复杂

❌ Rebase and merge（高级用户）
   - 需要理解 rebase 风险
```

---

## 🎯 最佳实践

### DO ✅
1. **每个终端设置唯一 CE_TERMINAL_ID**
2. **遵循 Phase 顺序** (P0→P1→P2→...→P7)
3. **提交前运行** `git status` 检查
4. **小步提交** (每个功能点一次提交)
5. **详细的 commit message** (遵循 Conventional Commits)
6. **定期推送** (避免本地积累过多提交)
7. **使用 ce publish** (自动质量检查)
8. **清理旧分支** (定期运行 `ce clean`)

### DON'T ❌
1. **不要绕过 Hooks** (`--no-verify`)
2. **不要直接推送 main** (会被 pre-push 阻止)
3. **不要在 PR 未合并前删除分支**
4. **不要忽略质量闸门警告**
5. **不要硬编码敏感信息** (密码/API密钥)
6. **不要跳过 Phase** (必须按顺序)
7. **不要创建超大 PR** (>500 行建议拆分)
8. **不要忘记更新文档** (README/CHANGELOG)

---

## 🔧 环境变量参考

| 变量 | 默认值 | 说明 | 示例 |
|------|--------|------|------|
| `CE_TERMINAL_ID` | `t1` | 终端标识 | `t1`, `t2`, `t3` |
| `CE_AUTOBRANCH` | `0` | 自动分支模式 | `0` (关闭), `1` (开启) |
| `MOCK_SCORE` | - | 质量分（测试用） | `90` |
| `MOCK_COVERAGE` | - | 覆盖率（测试用） | `85` |
| `PROJECT_ROOT` | 自动检测 | 项目根目录 | `/home/xx/dev/Claude Enhancer 5.0` |

### 推荐配置（~/.bashrc）
```bash
# Claude Enhancer 环境变量
export CE_TERMINAL_ID=t1  # 根据终端编号修改
export PATH="$PATH:/home/xx/dev/Claude\ Enhancer\ 5.0/scripts"

# 别名（可选）
alias ce-status='bash /home/xx/dev/Claude\ Enhancer\ 5.0/.workflow/executor.sh status'
alias ce-validate='bash /home/xx/dev/Claude\ Enhancer\ 5.0/.workflow/executor.sh validate'
```

---

## 📞 获取帮助

### 命令行帮助
```bash
ce help                    # 查看所有命令
ce branch --help           # 查看 branch 命令帮助
ce publish --help          # 查看 publish 命令帮助
```

### 状态查询
```bash
ce status                  # 当前状态
bash .workflow/executor.sh status  # 详细工作流状态
git status                 # Git 状态
```

### 日志查看
```bash
# 工作流日志
tail -f .workflow/executor.log

# Git Hooks 日志
tail -f .workflow/logs/hooks.log

# 质量闸门失败日志
cat .workflow/logs/publish_failures.log
```

### 文档资源
- **完整技术设计**: `docs/P0_GIT_BRANCH_PR_AUTOMATION_SPIKE.md`
- **工作流文档**: `.claude/WORKFLOW.md`
- **Gates 配置**: `.workflow/gates.yml`
- **项目说明**: `CLAUDE.md`

---

## 📈 性能指标

| 操作 | 预期时间 | 说明 |
|------|---------|------|
| `ce branch` | <2秒 | 创建分支 + 推送远程 |
| `ce publish` | 5-10秒 | 质量检查 + 推送 + PR URL生成 |
| `ce status` | <1秒 | 快速状态查询 |
| `ce clean` | 2-5秒 | 清理已合并分支 |
| Pre-commit Hook | 3-8秒 | 取决于文件数量 |
| Pre-push Hook | 10-30秒 | 包含测试运行 |

---

## ⚡ 高级技巧

### 技巧1: 批量分支清理
```bash
# 清理30天前的旧分支
git branch | grep -E 'feature/.*-[0-9]{8}-' | while read branch; do
    date=$(echo "$branch" | grep -oP '\d{8}')
    cutoff=$(date -d "30 days ago" +%Y%m%d)
    if [[ "$date" < "$cutoff" ]]; then
        echo "Deleting old branch: $branch"
        git branch -D "$branch"
    fi
done
```

### 技巧2: PR 描述复制到剪贴板
```bash
# Linux
bash scripts/generate_pr_description.sh | xclip -selection clipboard

# macOS
bash scripts/generate_pr_description.sh | pbcopy
```

### 技巧3: 离线开发模式
```bash
# 保存离线状态
bash scripts/save_offline_state.sh

# 网络恢复后恢复
bash scripts/resume_publish.sh
```

### 技巧4: 自定义分支前缀
```bash
# 修改 ce 脚本或设置环境变量
export CE_BRANCH_PREFIX="experiment"
ce branch "new-idea"
# → experiment/P3-t1-20251009-new-idea
```

---

**版本**: 1.0
**最后更新**: 2025-10-09
**适用于**: Claude Enhancer 5.0+

---

> 💡 **提示**: 将本文档打印或保存为 PDF，放在开发桌面上方便随时查阅！

> 🎓 **学习路径**: 新手建议先学习"常用命令速查"和"典型工作流场景"，熟练后再阅读"高级技巧"。
