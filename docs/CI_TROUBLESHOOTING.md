# CI 故障排查指南

**目标**: 快速诊断和解决CI工作流问题

---

## 常见问题

### 1. CI工作流未触发

**症状**: Push或PR后，Actions页面无任何运行记录

**排查步骤**:
```bash
# 1. 检查workflow文件是否存在
ls -la .github/workflows/ce-gates.yml

# 2. 检查YAML语法
# 访问 https://www.yamllint.com/ 验证语法

# 3. 检查分支配置
git branch --show-current
# 确认是main或feature分支
```

**解决方案**:
- 确保workflow文件在正确路径
- 检查`on:`触发条件是否匹配当前分支
- 查看Actions设置是否禁用了Workflow

---

### 2. 某个Job一直失败

**症状**: 某个检查步骤红叉，其他通过

**排查步骤**:
1. 点击失败的Job查看日志
2. 定位具体失败的Step
3. 复制错误信息

**常见原因**:
- 工具未安装（shellcheck/eslint/flake8）
- 文件路径错误
- 权限不足

---

### 3. 性能问题：CI运行超时

**症状**: CI运行时间超过10分钟

**排查**:
```bash
# 查看各Job的运行时间
# 在Actions页面点击Summary
```

**优化方案**:
- 启用缓存（npm/pip）
- 并行执行jobs
- 减少不必要的文件扫描

---

### 4. 安全扫描误报

**症状**: 检测到假的密钥或私钥

**排查**:
```bash
# 检查被标记的文件
grep -r "PRIVATE KEY" .
```

**解决**:
- 如果是测试文件，添加到白名单
- 如果是真实密钥，立即删除并轮换

---

### 5. Path Whitelist检查失败

**症状**: 提示文件不在允许路径中

**排查**:
```bash
# 查看当前Phase
cat .phase/current

# 查看允许的路径
grep -A 5 "P[0-9]:" .workflow/gates.yml
```

**解决**:
- 确认文件路径是否符合gates.yml定义
- 检查是否在正确的Phase

---

## 调试技巧

### 本地复现CI环境
```bash
# 1. 安装相同的工具版本
./workflow/scripts/install_lint_tools.sh

# 2. 手动运行检查
shellcheck .git/hooks/pre-commit
npm run lint
flake8 .

# 3. 测试gates_parser
bash .workflow/scripts/gates_parser.sh get_allow_paths P3
```

### 查看详细日志
在Workflow中添加调试输出：
```yaml
- name: Debug
  run: |
    echo "Current phase: $(cat .phase/current)"
    echo "Staged files:"
    git diff --name-only origin/main
```

---

## 获取帮助

### 查看文档
- GitHub Actions文档: https://docs.github.com/en/actions
- Claude Enhancer文档: docs/

### 报告问题
如果问题持续存在：
1. 收集错误日志
2. 记录复现步骤
3. 创建Issue附带以上信息
