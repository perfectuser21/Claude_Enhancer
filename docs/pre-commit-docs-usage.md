# Pre-commit 文档质量检查 Hook 使用指南

## 概述

`pre-commit-docs` 是 Claude Enhancer 5.0 的轻量级文档质量检查工具，专门用于 Git pre-commit hook，确保文档质量并阻止不合规的文档提交。

## 特性

### ⚡ 高性能设计
- **执行时间 < 50ms** - 超快速检查，不影响开发流程
- **单次遍历优化** - 避免重复文件操作
- **智能缓存** - 合并多项检查以提高效率

### 🛡️ 质量保障
- **路径合规性检查** - 确保文档放在正确位置
- **文件名规范验证** - 禁止不当命名模式
- **文件大小限制** - 防止过大文档进入仓库
- **敏感信息扫描** - 检测密码、API密钥等泄露风险

## 安装与配置

### 1. 脚本安装
```bash
# 脚本已自动安装在
.git/hooks/pre-commit-docs

# 并已集成到主 pre-commit hook
.git/hooks/pre-commit
```

### 2. 配置文件
使用 `.docpolicy.yaml` 进行配置：

```yaml
# 文档类型和路径映射
types:
  requirement:
    path: "docs/requirements"
  design:
    path: "docs/design"
  api:
    path: "docs/api"

# 质量标准
quality:
  max_file_kb: 5120              # 最大5MB

  # 禁止的文件名模式
  deny_name_patterns:
    - "(copy|backup|final\\(\\d+\\)|-old)\\.md$"
    - "(explain|debug|temp)\\.md$"
    - "\\s+\\.md$"               # 包含空格

# 门禁控制
gates:
  pre_commit:
    enabled: true
    checks:
      - path_check               # 路径检查
      - deny_name_patterns       # 文件名黑名单
      - file_size               # 文件大小
      - sensitive_info          # 敏感信息
    blocking: true              # 阻断提交
```

## 检查规则详解

### 1. 路径检查
确保文档放在正确的目录结构中：

```
✅ 允许的路径:
docs/requirements/PRD-001.md
docs/design/architecture.md
docs/api/endpoints.md
README.md
CHANGELOG.md

❌ 禁止的路径:
temp/random.md
docs/temp.md
```

### 2. 文件名规范
禁止以下文件名模式：

```
❌ 禁止的文件名:
- debug.md, temp.md, explain.md
- backup.md, copy.md, -old.md
- final(1).md, final(2).md
- "file with spaces.md"

✅ 推荐的文件名:
- PRD-001-user-login.md
- api-authentication.md
- database-design.md
```

### 3. 文件大小限制
- **默认限制**: 5MB (5120KB)
- **检查范围**: .md, .txt, .rst, .adoc 文件
- **超限处理**: 阻止提交并提示压缩

### 4. 敏感信息检测
检测以下模式：

```
❌ 危险内容:
password = "secret123"
api_key = "sk-1234567890abcdef..."
secret = "mysecret"
token = "ghp_xxxxxxxxxxxx"

✅ 安全做法:
password = "${PASSWORD}"
api_key = "从环境变量获取"
secret = "参考配置文档"
```

## 使用示例

### 正常提交流程
```bash
# 1. 添加符合规范的文档
git add docs/requirements/PRD-001.md

# 2. 提交时自动检查
git commit -m "feat: 添加用户登录需求文档"

# 输出:
# 📚 Claude Enhancer - Document Quality Check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 检查文件: 1 个文档
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 检查统计:
#    总文档数: 1
#    已检查: 1
#    执行时间: 46ms
# ✅ 文档质量检查通过
```

### 检查失败示例
```bash
# 1. 添加不规范文档
git add temp/debug.md

# 2. 提交被阻止
git commit -m "临时调试文档"

# 输出:
# 📚 Claude Enhancer - Document Quality Check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ❌ 路径错误: temp/debug.md
# ❌ 文件名违规: temp/debug.md
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ❌ 文档质量检查失败
#
# 修复建议:
# • 将文档移至正确路径
# • 重命名不规范的文件
# • 移除敏感信息
# • 压缩过大的文档
```

## 性能优化

### 设计原则
1. **单次遍历** - 所有检查在一次文件遍历中完成
2. **早期返回** - 发现错误立即标记，避免继续检查
3. **批量操作** - 使用 xargs 和管道优化文件操作
4. **禁用日志** - 生产环境禁用调试日志

### 性能指标
- **目标**: < 50ms
- **实际**: 46ms (1个文档)
- **扩展性**: 线性增长，每增加10个文档约+20ms

## 集成架构

```
Git Commit Flow:
┌─────────────────┐
│   git commit    │
└─────────┬───────┘
          │
┌─────────▼───────┐
│   pre-commit    │  (主Hook)
│                 │
│ 1. 分支保护     │
│ 2. 代码格式     │
│ 3. 安全检查     │
│ 4. 垃圾清理     │
│ 5. Claude标准   │
│ 6. 提交大小     │
│ 7. 📚文档质量   │ ← pre-commit-docs
│ 8. 质量标准     │
└─────────┬───────┘
          │
    ✅ 通过 / ❌ 阻止
```

## 故障排除

### 常见问题

**Q: 执行时间过长怎么办？**
A: 检查是否有大量文档或大文件，考虑分批提交。

**Q: 路径检查误报怎么办？**
A: 检查 `.docpolicy.yaml` 中的路径配置是否正确。

**Q: 敏感信息误报怎么办？**
A: 使用环境变量或配置文件外部化敏感信息。

**Q: 如何临时绕过检查？**
A: 不建议绕过，建议修复问题。如确需绕过：
```bash
git commit --no-verify -m "跳过检查"
```

### 调试方法

1. **查看详细日志**:
```bash
cat /tmp/claude_enhancer_doc_check.log
```

2. **手动运行检查**:
```bash
.git/hooks/pre-commit-docs
```

3. **测试配置解析**:
```bash
grep -A 5 "max_file_kb" .docpolicy.yaml
```

## 最佳实践

### 文档组织
```
docs/
├── requirements/          # 需求文档
│   ├── PRD-001-login.md
│   └── PRD-002-search.md
├── design/               # 设计文档
│   ├── architecture.md
│   └── database-schema.md
├── api/                  # API文档
│   ├── authentication.md
│   └── endpoints.md
└── guides/               # 使用指南
    ├── setup.md
    └── deployment.md
```

### 命名规范
- 使用小写字母和连字符
- 包含编号便于排序: `PRD-001-`, `API-v2-`
- 避免临时性名称: `temp`, `debug`, `test`
- 描述性命名: `user-authentication.md` vs `auth.md`

### 内容管理
- 保持文档简洁，大文档考虑拆分
- 敏感信息使用占位符
- 定期清理过时文档
- 使用模板确保一致性

---

*Claude Enhancer 5.0 - 让文档管理变得简单高效*