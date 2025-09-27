# DocGate文档质量管理系统 - 部署指南

## 🚀 一键部署

```bash
# 克隆项目后，直接运行部署脚本
./deploy_docgate_system.sh
```

## 📋 系统要求

### 必需依赖
- **Git** >= 2.20
- **Python** >= 3.8 (推荐 3.9+)
- **Node.js** >= 16 (推荐 18+)
- **pip3** 和 **npm**

### 可选依赖
- **curl** (用于网络检查)
- **jq** (用于JSON处理)

## 🏗️ 系统架构

### 核心组件
```
DocGate文档质量管理系统
├── 三层质量门禁
│   ├── Layer 1: pre-commit (轻量级)
│   ├── Layer 2: pre-push (快速检查)
│   └── Layer 3: CI深度检查
├── Git工作流集成
│   ├── 自动化质量检查
│   ├── 提交信息规范
│   └── 分支保护策略
├── DocGate Agent
│   ├── 智能文档分析
│   ├── 质量评分系统
│   └── 修改建议生成
└── REST API服务
    ├── 文档检查接口
    ├── 配置管理
    └── 报告生成
```

### 文档类型支持
- **Markdown** (.md, .markdown)
- **reStructuredText** (.rst)
- **HTML** (.html, .htm)
- **纯文本** (.txt)

## 📁 部署后目录结构

```
项目根目录/
├── .claude/                     # Claude Enhancer配置
│   ├── scripts/                 # DocGate检查脚本
│   │   ├── docgate_pre_commit_check.py
│   │   ├── check_doc_links.py
│   │   ├── check_doc_structure.py
│   │   └── health_check.py
│   ├── hooks/                   # Claude hooks
│   └── git-hooks/               # Git hooks模板
├── docs/                        # 文档目录
│   ├── requirements/            # 需求文档
│   ├── design/                  # 设计文档
│   ├── api/                     # API文档
│   ├── guides/                  # 指南文档
│   ├── changelogs/              # 变更日志
│   ├── test-reports/            # 测试报告
│   ├── _templates/              # 文档模板
│   ├── _digest/                 # 文档摘要
│   └── _reports/                # 质量报告
├── backend/api/docgate/         # DocGate API服务
├── .docpolicy.yaml              # 文档策略配置
├── deploy_docgate_system.sh     # 一键部署脚本
├── DOCGATE_USAGE.md            # 详细使用指南
└── DEPLOY_README.md            # 本文档
```

## ⚙️ 配置说明

### .docpolicy.yaml 核心配置
```yaml
# 文档类型定义
types:
  requirement:
    path: "docs/requirements"
    required_fields: ["title", "summary", "status", "last_updated"]

# 质量标准
quality:
  require_tldr: true              # 必须有摘要
  min_key_points: 3               # 最少3个关键点
  max_file_kb: 5120              # 最大5MB

# 门禁控制
gates:
  pre_commit:
    enabled: true
    blocking: true                # 阻断提交

# DocGate Agent配置
docgate:
  enabled: true
  mode: "advisory"               # advisory/enforcing
```

## 🔧 常用命令

### 健康检查
```bash
# 运行系统健康检查
python3 .claude/scripts/health_check.py

# 查看详细状态
cat docgate_health_report.json
```

### 手动质量检查
```bash
# 检查单个文档
python3 .claude/scripts/docgate_pre_commit_check.py --files docs/api/my-api.md

# 检查所有链接
python3 .claude/scripts/check_doc_links.py docs/

# 检查文档结构
python3 .claude/scripts/check_doc_structure.py docs/
```

### 文档创建
```bash
# 使用模板创建新文档
cp docs/_templates/requirement.md docs/requirements/new-feature.md
cp docs/_templates/design.md docs/design/new-architecture.md
cp docs/_templates/api.md docs/api/new-endpoint.md
```

## 🐛 故障排除

### 常见问题

**1. 依赖安装失败**
```bash
# 检查Python版本
python3 --version

# 手动安装依赖
pip3 install fastapi pydantic pyyaml requests --user

# 检查Node.js版本
node --version
npm --version
```

**2. Git hooks不工作**
```bash
# 检查hooks权限
ls -la .git/hooks/

# 重新设置权限
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg
chmod +x .git/hooks/pre-push

# 测试hooks
git commit --dry-run
```

**3. 脚本执行失败**
```bash
# 检查Python模块
python3 -c "import yaml, requests; print('模块正常')"

# 检查脚本语法
python3 -m py_compile .claude/scripts/docgate_pre_commit_check.py

# 查看详细错误
python3 .claude/scripts/docgate_pre_commit_check.py --files README.md
```

**4. 配置文件错误**
```bash
# 验证YAML语法
python3 -c "import yaml; yaml.safe_load(open('.docpolicy.yaml'))"

# 恢复默认配置
cp .docgate_backup_*/docpolicy_backup.yaml .docpolicy.yaml
```

### 重新部署
```bash
# 如果部署出现问题，可以重新运行
./deploy_docgate_system.sh

# 查看部署日志
cat deploy_docgate_*.log
```

## 📈 最佳实践

### 1. 文档组织
- 按类型分目录存放文档
- 使用有意义的文件名
- 遵循模板格式规范

### 2. Git工作流
```bash
# 标准提交流程
git add docs/requirements/new-feature.md
git commit -m "docs(requirements): add user authentication feature spec"
git push

# 提交信息格式
# type(scope): description
#
# 类型: docs, feat, fix, style, refactor, test, chore
# 范围: requirements, design, api, guides等
```

### 3. 质量保障
- 每个文档都包含摘要和关键点
- 定期检查和更新链接
- 使用正确的Markdown格式

## 🔄 系统维护

### 定期维护任务
```bash
# 每周运行健康检查
python3 .claude/scripts/health_check.py

# 每月清理过期文档
find docs/ -name "*.md" -mtime +60 -exec mv {} archive/ \;

# 更新依赖包
pip3 install -r requirements_docgate.txt --upgrade
```

### 备份恢复
```bash
# 查看备份
ls -la .docgate_backup_*/

# 恢复配置
cp .docgate_backup_*/docpolicy_backup.yaml .docpolicy.yaml

# 恢复Git hooks
cp -r .docgate_backup_*/git_hooks_backup/* .git/hooks/
```

## 📞 获取支持

### 自助排查
1. 运行健康检查: `python3 .claude/scripts/health_check.py`
2. 查看部署日志: `cat deploy_docgate_*.log`
3. 检查配置文件: `cat .docpolicy.yaml`

### 文档资源
- **详细使用指南**: `DOCGATE_USAGE.md`
- **API文档**: `docs/api/docgate-api-specification.md`
- **设计文档**: `docs/design/document-quality-system-design.md`

### 问题反馈
如遇到问题，请提供以下信息：
- 系统环境 (OS, Python版本)
- 错误信息或日志
- 健康检查报告: `docgate_health_report.json`

---

**🌟 DocGate - 让文档质量管理变得简单高效！**