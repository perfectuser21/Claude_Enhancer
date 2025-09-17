# Perfect21 多工作空间管理器

## 🎯 核心功能

Perfect21多工作空间管理器是一个专为单人多功能并行开发设计的智能工作空间管理系统，支持：

- **工作空间隔离**：每个feature独立分支和端口
- **智能切换**：基于上下文自动推荐工作空间
- **自动协调**：冲突检测和合并建议
- **状态同步**：实时监控所有工作空间状态
- **Claude Code集成**：与开发工作流无缝集成

## 🚀 快速开始

### 创建工作空间

```bash
# 创建功能开发工作空间
python3 main/cli.py workspace create "user_auth" "实现用户认证系统" --type feature --priority 8

# 创建Bug修复工作空间
python3 main/cli.py workspace create "fix_login" "修复登录bug" --type bugfix --priority 9

# 创建实验性工作空间
python3 main/cli.py workspace create "new_ui" "尝试新UI设计" --type experiment --priority 3
```

### 查看和管理工作空间

```bash
# 列出所有工作空间
python3 main/cli.py workspace list

# 查看统计信息
python3 main/cli.py workspace stats

# 切换到指定工作空间
python3 main/cli.py workspace switch feature_user_auth
```

### 智能任务建议

```bash
# 获取任务建议和分析
python3 main/cli.py workspace suggest "实现用户登录API接口"

# 输出示例：
# 🎯 任务分析: 实现用户登录API接口
# 复杂度: 1/8
# 预估时间: 5小时
# 风险级别: low
# 建议类型: feature
#
# 💡 建议创建新工作空间:
#   名称: api_enhancement
#   类型: feature
#   原因: Clean workspace recommended for focused development
```

### 冲突检测和合并

```bash
# 检测工作空间冲突
python3 main/cli.py workspace conflicts feature_user_auth

# 预览合并（干运行）
python3 main/cli.py workspace merge feature_user_auth --dry-run

# 实际合并工作空间
python3 main/cli.py workspace merge feature_user_auth
```

## 🏠 与开发工作流集成

### 使用指定工作空间开发

```bash
# 在特定工作空间中执行开发任务
python3 main/cli.py develop "修复用户认证问题" --workspace bugfix_fix_login

# 输出示例：
# 🏠 工作空间模式启动
# 📋 任务: 修复用户认证问题
# 🏠 工作空间: bugfix_fix_login
# 端口: 3002
# 分支: feature/fix_login
#
# **开发建议:**
# - 使用端口 3002 进行开发服务器
# - 定期同步基分支以避免冲突
# - 完成后使用Perfect21合并工具进行安全合并
```

### 并行开发示例

```bash
# 终端1：开发用户认证功能
python3 main/cli.py workspace switch feature_user_auth
npm run dev -- --port 3000

# 终端2：修复登录bug
python3 main/cli.py workspace switch bugfix_fix_login
npm run dev -- --port 3002

# 终端3：实验新UI
python3 main/cli.py workspace switch experiment_new_ui
npm run dev -- --port 3004
```

## 📊 工作空间类型

| 类型 | 用途 | 示例 |
|------|------|------|
| `feature` | 新功能开发 | 用户认证、API接口、仪表板 |
| `bugfix` | Bug修复 | 登录问题、数据错误、UI故障 |
| `experiment` | 实验性开发 | 新技术验证、原型设计 |
| `hotfix` | 紧急修复 | 生产环境急修 |
| `refactor` | 代码重构 | 架构优化、性能提升 |

## 🔄 工作空间状态

| 状态 | 说明 |
|------|------|
| `active` | 活跃开发中 |
| `idle` | 闲置但保持 |
| `paused` | 暂停开发 |
| `merging` | 合并进行中 |
| `conflict` | 存在冲突 |
| `archived` | 已归档 |

## 🎨 最佳实践

### 1. 工作空间命名
- 使用描述性名称：`user_auth` 而不是 `feature1`
- 包含功能范围：`api_user_management` 而不是 `api`
- 避免空格和特殊字符

### 2. 优先级管理
- **1-3**：实验性、非紧急任务
- **4-6**：常规功能开发
- **7-8**：重要功能、Bug修复
- **9-10**：紧急修复、高优先级功能

### 3. 端口分配
- 工作空间会自动分配端口（3000-4000范围）
- 每个工作空间独占一个开发端口
- API服务器会自动分配相邻端口（如果需要）

### 4. 合并策略
- 定期同步基分支避免冲突
- 使用 `--dry-run` 预览合并
- 小功能及时合并，避免长期分支

## 🔧 技术实现

### 核心组件

1. **WorkspaceManager**: 核心工作空间管理
2. **WorkspaceIntegration**: Claude Code集成
3. **CLI Interface**: 命令行接口

### 存储结构

```
.perfect21/workspaces/
├── workspace_config.json     # 工作空间配置
├── feature_user_auth/        # 工作空间目录
│   └── config.json          # 工作空间专用配置
└── bugfix_fix_login/
    └── config.json
```

### Git集成

- 自动创建功能分支
- 冲突检测和解决建议
- 智能合并策略
- Hook集成支持

## 📈 使用案例

### 单人多功能开发

```bash
# 上午：开发用户认证
python3 main/cli.py workspace switch feature_user_auth
python3 main/cli.py develop "实现JWT认证" --workspace feature_user_auth

# 下午：修复发现的bug
python3 main/cli.py workspace create "fix_token" "修复token过期问题" --type bugfix
python3 main/cli.py develop "修复token刷新逻辑" --workspace bugfix_fix_token

# 晚上：尝试新技术
python3 main/cli.py workspace switch experiment_new_ui
python3 main/cli.py develop "尝试Vue3 Composition API" --workspace experiment_new_ui
```

### 阶段性合并

```bash
# 检查所有工作空间状态
python3 main/cli.py workspace list

# 合并完成的功能
python3 main/cli.py workspace merge feature_user_auth

# 清理已归档的工作空间
python3 main/cli.py workspace cleanup archived_workspaces --force
```

## 🚨 注意事项

1. **端口冲突**：确保端口范围内没有其他服务占用
2. **Git状态**：切换工作空间前确保提交或暂存更改
3. **依赖管理**：各工作空间可能有不同的依赖版本
4. **资源消耗**：并行开发会增加系统资源消耗

## 🔮 未来扩展

- [ ] 团队协作支持
- [ ] 云端工作空间同步
- [ ] 自动化测试集成
- [ ] 性能监控面板
- [ ] 工作空间模板系统