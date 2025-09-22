# 📚 Claude Enhancer 详细工作流程

## 🎯 核心执行逻辑

### 触发条件
当用户提出编程相关任务时，Claude Code必须：
1. 识别是否为编程任务
2. 判断任务复杂度（简单/标准/复杂）
3. 启动8-Phase工作流

## Phase 0: 分支管理 🌿

### 触发时机
- 任何新功能、修复、重构任务开始时

### 具体步骤
```bash
# 1. 检查当前分支状态
git status
git branch --show-current

# 2. 检查是否有未提交更改
if [有未提交更改]; then
    # 提醒用户处理
    echo "发现未提交更改，建议：commit或stash"
fi

# 3. 创建新分支
# 分支命名规范：
# - feature/xxx - 新功能
# - fix/xxx - 错误修复
# - refactor/xxx - 代码重构
# - test/xxx - 测试相关
# - docs/xxx - 文档更新

git checkout -b feature/[task-name]

# 4. 如果需要worktree（并行开发）
git worktree add ../[project]-[branch] [branch-name]
```

### Agent要求
- **数量**: 0个（纯Git操作）
- **Hook**: branch_helper.sh提醒

### 检查点
- [ ] 当前在正确的分支
- [ ] 没有未提交的更改冲突
- [ ] 分支名称符合规范

## Phase 1: 需求分析 📋

### 触发时机
- 分支创建后立即开始
- 或接到新任务时

### 具体步骤

#### Step 1: 理解用户意图
```markdown
分析维度：
1. **功能需求**: 用户想要什么功能？
2. **非功能需求**: 性能、安全、可用性要求？
3. **约束条件**: 时间、技术栈、兼容性？
4. **验收标准**: 如何判断任务完成？
```

#### Step 2: 搜索现有代码
```bash
# 搜索相关代码
grep -r "相关关键词" . --include="*.py" --include="*.js"

# 查看项目结构
tree -L 2 -I 'node_modules|__pycache__|.git'

# 检查依赖
cat package.json | jq '.dependencies'
cat requirements.txt
```

#### Step 3: 生成需求文档
```markdown
## 需求分析报告

### 任务描述
[具体描述]

### 影响范围
- 需要修改的文件：[列表]
- 需要新增的文件：[列表]
- 受影响的功能：[列表]

### 技术方案
- 实现方式：[描述]
- 技术选型：[框架/库]
- 风险评估：[潜在问题]
```

### Agent要求
- **最少**: 1个
- **推荐**: 2个
  - requirements-analyst：需求分析
  - business-analyst：业务逻辑（如果涉及）

### 检查点
- [ ] 需求明确且可实现
- [ ] 了解现有代码结构
- [ ] 确定技术方案

## Phase 2: 设计规划 🏗️

### 触发时机
- 需求分析完成后

### 具体步骤

#### Step 1: 架构设计
```markdown
## 架构设计

### 模块划分
- 核心模块：[功能描述]
- 辅助模块：[功能描述]
- 接口定义：[API/函数签名]

### 数据流
输入 → 处理 → 输出

### 错误处理
- 异常捕获策略
- 错误恢复机制
- 日志记录方案
```

#### Step 2: API设计（如果需要）
```yaml
# OpenAPI规范示例
paths:
  /api/endpoint:
    post:
      summary: 功能描述
      parameters:
        - name: param1
          type: string
          required: true
      responses:
        200:
          description: 成功响应
        400:
          description: 参数错误
```

#### Step 3: 数据库设计（如果需要）
```sql
-- 表结构设计
CREATE TABLE table_name (
    id SERIAL PRIMARY KEY,
    field1 VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引设计
CREATE INDEX idx_field1 ON table_name(field1);
```

### Agent要求
- **最少**: 2个
- **推荐**: 3个
  - backend-architect：整体架构
  - api-designer：接口设计
  - database-specialist：数据库设计（如需）

### 检查点
- [ ] 架构清晰合理
- [ ] 接口定义完整
- [ ] 数据结构设计完成

## Phase 3: 开发实现 💻

### 触发时机
- 设计完成后

### 任务类型与Agent映射

#### 认证系统 (authentication)
```xml
<!-- 必须5个Agent并行 -->
<function_calls>
  <invoke name="Task" subagent_type="backend-architect">实现认证架构</invoke>
  <invoke name="Task" subagent_type="security-auditor">安全审查</invoke>
  <invoke name="Task" subagent_type="database-specialist">用户数据表</invoke>
  <invoke name="Task" subagent_type="test-engineer">测试用例</invoke>
  <invoke name="Task" subagent_type="api-designer">API端点</invoke>
</function_calls>
```

#### API开发 (api_development)
```xml
<!-- 必须4个Agent并行 -->
<function_calls>
  <invoke name="Task" subagent_type="api-designer">设计RESTful API</invoke>
  <invoke name="Task" subagent_type="backend-architect">实现逻辑</invoke>
  <invoke name="Task" subagent_type="test-engineer">API测试</invoke>
  <invoke name="Task" subagent_type="technical-writer">API文档</invoke>
</function_calls>
```

#### 前端开发 (frontend)
```xml
<!-- 必须4个Agent并行 -->
<function_calls>
  <invoke name="Task" subagent_type="frontend-specialist">组件开发</invoke>
  <invoke name="Task" subagent_type="ux-designer">UI设计</invoke>
  <invoke name="Task" subagent_type="test-engineer">前端测试</invoke>
  <invoke name="Task" subagent_type="performance-engineer">性能优化</invoke>
</function_calls>
```

#### Bug修复 (bug_fix)
```xml
<!-- 必须3个Agent并行 -->
<function_calls>
  <invoke name="Task" subagent_type="error-detective">定位问题</invoke>
  <invoke name="Task" subagent_type="test-engineer">复现测试</invoke>
  <invoke name="Task" subagent_type="code-reviewer">验证修复</invoke>
</function_calls>
```

### 具体实现步骤

#### Step 1: 创建/修改文件
```python
# 使用MultiEdit批量编辑
MultiEdit(
    file_path="/path/to/file.py",
    edits=[
        {
            "old_string": "旧代码",
            "new_string": "新代码"
        }
    ]
)

# 创建新文件
Write(
    file_path="/path/to/new_file.py",
    content="文件内容"
)
```

#### Step 2: 代码质量检查
```bash
# Python项目
pylint *.py
black *.py
mypy *.py

# JavaScript项目
eslint .
prettier --write .
```

### Agent要求
- **最少**: 4个
- **标准**: 6个
- **复杂**: 8个

### 检查点
- [ ] 代码功能实现完整
- [ ] 遵循项目代码规范
- [ ] 没有明显的bug

## Phase 4: 本地测试 🧪

### 触发时机
- 代码实现完成后

### 具体步骤

#### Step 1: 单元测试
```python
# 创建测试文件
def test_function():
    assert function(input) == expected_output
    assert function(edge_case) raises Exception
```

#### Step 2: 集成测试
```bash
# 运行测试
pytest -v
npm test
go test ./...
```

#### Step 3: 手动测试
```bash
# 启动服务
python main.py
npm run dev

# 测试功能
curl -X POST http://localhost:8000/api/endpoint
```

### Agent要求
- **最少**: 2个
  - test-engineer：编写测试
  - performance-engineer：性能测试（可选）

### 检查点
- [ ] 所有测试通过
- [ ] 覆盖率达标（>80%）
- [ ] 性能满足要求

## Phase 5: 代码提交 📝

### 触发时机
- 测试通过后

### 具体步骤

#### Step 1: 代码检查
```bash
# 查看更改
git status
git diff

# 检查是否有敏感信息
grep -r "password\|secret\|key" . --include="*.py"
```

#### Step 2: 提交代码
```bash
# 添加文件
git add .

# 提交（触发pre-commit hook）
git commit -m "type: 简短描述

详细说明：
- 实现了什么功能
- 修复了什么问题
- 影响了什么部分

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Hook检查
- **pre-commit**: 代码质量、格式、lint
- **commit-msg**: 提交信息格式

### 检查点
- [ ] 无敏感信息泄露
- [ ] 提交信息规范
- [ ] Hook检查通过

## Phase 6: 代码审查 👀

### 触发时机
- 代码提交后

### 具体步骤

#### Step 1: 自审查
```markdown
## 代码审查清单

### 功能性
- [ ] 功能完整实现
- [ ] 边界条件处理
- [ ] 错误处理完善

### 代码质量
- [ ] 命名清晰
- [ ] 注释充分
- [ ] 无重复代码

### 性能
- [ ] 无明显性能问题
- [ ] 资源正确释放

### 安全
- [ ] 输入验证
- [ ] 无SQL注入风险
- [ ] 无XSS风险
```

#### Step 2: 创建PR（如果需要）
```bash
# 推送到远程
git push origin feature/xxx

# 创建PR
gh pr create --title "Feature: XXX" --body "描述"
```

### Agent要求
- **最少**: 1个
  - code-reviewer：代码审查
- **推荐**: 2个
  - security-auditor：安全审查（额外）

### 检查点
- [ ] 代码质量合格
- [ ] 无安全隐患
- [ ] PR描述完整

## Phase 7: 合并部署 🚀

### 触发时机
- 代码审查通过后

### 具体步骤

#### Step 1: 合并代码
```bash
# 切换到主分支
git checkout main

# 合并feature分支
git merge feature/xxx

# 或使用PR合并
gh pr merge
```

#### Step 2: 部署（如果有CI/CD）
```bash
# 触发部署
git push origin main

# 或手动部署
./deploy.sh
```

#### Step 3: 清理
```bash
# 删除本地分支
git branch -d feature/xxx

# 删除远程分支
git push origin --delete feature/xxx

# 清理worktree（如果有）
git worktree prune
```

### Agent要求
- **可选**: 1个
  - devops-engineer：部署配置

### 检查点
- [ ] 合并无冲突
- [ ] 部署成功
- [ ] 分支清理完成

## 🔄 异常处理流程

### 任何Phase失败时
```python
if phase_failed:
    # 1. 记录失败原因
    log_error(phase, error_message)

    # 2. 尝试修复
    if can_auto_fix:
        fix_and_retry()
    else:
        # 3. 请求用户帮助
        ask_user_for_help()

    # 4. 重新执行该Phase
    retry_phase()
```

### 中断恢复
```bash
# 检查中断状态
bash .claude/hooks/phase_flow_monitor.sh check

# 从中断处继续
continue_from_last_phase()
```

## 📊 质量指标

### 每个Phase的成功标准

| Phase | 成功指标 | 最低要求 |
|-------|---------|---------|
| 0 | 正确的分支创建 | 100% |
| 1 | 需求理解准确 | 90% |
| 2 | 设计方案可行 | 95% |
| 3 | 代码功能完整 | 100% |
| 4 | 测试覆盖率 | >80% |
| 5 | 提交规范性 | 100% |
| 6 | 审查通过率 | 95% |
| 7 | 部署成功率 | 100% |

## 🎯 执行保证

### Claude Code承诺
1. **必须执行全部8个Phase**（除非用户明确跳过）
2. **每个Phase必须满足Agent数量要求**
3. **失败必须重试直到成功**
4. **全程使用TodoWrite追踪进度**

这个详细的Workflow定义了每个Phase的具体执行步骤、检查点和成功标准，确保Claude Code能够系统化、标准化地完成开发任务。