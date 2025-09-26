# 🚀 Claude Enhancer 5.0 - Workflow Execution Engine

> 智能化的工作流执行引擎，实现自动化Phase管理和Gates验证

## 📋 系统概览

### 核心组件
- **executor.sh** - 主执行引擎脚本
- **gates.yml** - 工作流配置和Gates定义
- **integration.sh** - Claude Hooks系统集成
- **demo.sh** - 演示脚本

### 目录结构
```
.workflow/
├── executor.sh           # 主执行引擎
├── gates.yml            # Gates配置文件
├── demo.sh              # 演示脚本
├── README.md            # 本文档
├── executor.log         # 执行日志
├── temp/                # 临时文件目录
└── prompts/             # 提示词模板
```

## 🎯 核心功能

### 1. Phase管理系统
- **6个标准阶段**: P1(Plan) → P2(Skeleton) → P3(Implement) → P4(Test) → P5(Review) → P6(Docs & Release)
- **状态持久化**: 存储在 `.phase/current`
- **历史记录**: 记录每次phase切换时间

### 2. Gates验证引擎
- **智能条件解析**: 从gates.yml读取验证条件
- **多种验证类型**:
  - 文件存在性检查
  - 文档结构验证
  - 构建状态检查
  - 测试结果验证
  - 任务清单数量验证

### 3. Claude Hooks集成
- **阶段性Hook触发**: 根据当前Phase自动调用相应hooks
- **上下文感知**: 传递阶段信息给hooks
- **非阻塞执行**: 超时保护，不影响主流程

### 4. 智能推荐系统
- **阶段特定建议**: 根据当前Phase提供针对性建议
- **动作推荐**: 建议下一步操作
- **最佳实践提示**: 遵循工作流最佳实践

## 🔧 使用方法

### 基本命令

```bash
# 初始化工作流系统
./executor.sh init

# 查看当前状态和进度
./executor.sh status

# 验证当前阶段的Gates条件
./executor.sh validate

# 尝试进入下一阶段
./executor.sh next

# 跳转到指定阶段
./executor.sh goto P3

# 重置到P1阶段
./executor.sh reset

# 获取智能推荐
./executor.sh suggest

# 手动触发Claude Hooks
./executor.sh hooks

# 清理临时文件
./executor.sh clean
```

### 工作流程示例

```bash
# 1. 初始化系统
./executor.sh init

# 2. 查看当前状态（应该在P1阶段）
./executor.sh status

# 3. 创建PLAN.md文件（满足P1的Gates条件）
cat > docs/PLAN.md << 'EOF'
# 项目计划

## 任务清单
1. 任务一
2. 任务二
3. 任务三
4. 任务四
5. 任务五

## 受影响文件清单
- src/main.js
- docs/README.md

## 回滚方案
回滚步骤说明...
EOF

# 4. 验证P1阶段并自动进入P2
./executor.sh next

# 5. 查看新阶段的推荐
./executor.sh suggest
```

## 🎮 Phase详细说明

### P1 - Plan (计划阶段)
**目标**: 分析需求，制定计划
**Gates条件**:
- 必须存在 `docs/PLAN.md`
- 必须包含三个标题：任务清单、受影响文件清单、回滚方案
- 任务清单 ≥ 5条
- 受影响文件清单为具体路径格式

**推荐操作**:
- 创建完整的项目计划文档
- 明确任务分工和时间安排
- 识别风险点和回滚策略

### P2 - Skeleton (骨架阶段)
**目标**: 创建项目结构和接口骨架
**Gates条件**:
- 新增目录必须在PLAN中声明
- 接口文件存在且符合命名规范

**推荐操作**:
- 根据PLAN.md创建目录结构
- 定义核心接口和数据结构
- 记录架构决策

### P3 - Implement (实现阶段)
**目标**: 编写功能代码
**Gates条件**:
- 代码构建/编译通过
- CHANGELOG更新
- 不得修改非白名单目录

**推荐操作**:
- 使用4-6-8个Agent并行开发
- 确保代码质量和规范
- 及时更新文档

### P4 - Test (测试阶段)
**目标**: 验证功能正确性
**Gates条件**:
- 新增≥2条测试，至少1条边界测试
- unit+boundary+smoke测试通过
- 存在测试报告

**推荐操作**:
- 编写全面的测试用例
- 进行边界值测试
- 生成测试覆盖率报告

### P5 - Review (审查阶段)
**目标**: 代码审查和质量控制
**Gates条件**:
- 存在完整的审查报告
- 明确的批准或返工决定

**推荐操作**:
- 进行全面的代码审查
- 评估风险和可维护性
- 确认回滚可行性

### P6 - Docs & Release (文档和发布阶段)
**目标**: 完善文档，发布版本
**Gates条件**:
- README包含安装、使用、注意事项
- CHANGELOG版本号递增
- 成功打tag
- 通过健康检查

**推荐操作**:
- 完善用户文档
- 更新版本信息
- 执行发布流程

## 🔗 集成特性

### Claude Hooks集成
- **P1**: 触发 `branch_helper.sh` - 分支检查
- **P2**: 触发 `smart_cleanup_advisor.sh` - 清理建议
- **P3**: 触发 `smart_agent_selector.sh` + `concurrent_optimizer.sh` - Agent选择和优化
- **P4**: 触发 `performance_monitor.sh` + `quality_gate.sh` - 性能监控和质量检查
- **P5**: 触发 `smart_error_recovery.sh` - 错误恢复
- **P6**: 触发 `smart_git_workflow.sh` - Git工作流

### 日志系统
- **实时日志**: 所有操作都记录到 `executor.log`
- **结构化输出**: 时间戳、级别、模块、消息
- **彩色输出**: 区分不同类型的信息

### 错误处理
- **超时保护**: 防止hooks和验证器无限等待
- **非阻塞设计**: Hook失败不影响主流程
- **详细错误信息**: 帮助快速定位问题

## 📊 监控和诊断

### 状态监控
```bash
# 查看详细状态
./executor.sh status

# 检查日志
tail -f .workflow/executor.log

# 查看Gates完成情况
ls -la .gates/
```

### 故障排除
```bash
# 检查配置文件语法
python3 -c "import yaml; yaml.safe_load(open('.workflow/gates.yml'))"

# 重新初始化
./executor.sh clean
./executor.sh init

# 手动重置状态
rm -f .gates/*.ok
echo "P1" > .phase/current
```

## 🛠️ 自定义和扩展

### 添加新的Gates条件
1. 在 `gates.yml` 中定义新的验证条件
2. 在 `executor.sh` 的 `validate_gate_condition()` 函数中添加处理逻辑
3. 编写对应的验证函数

### 自定义Hooks集成
1. 在 `integrate_with_claude_hooks()` 函数中添加新的阶段处理
2. 确保Hook脚本具有执行权限
3. 使用环境变量传递上下文信息

### 配置自定义Phase
1. 修改 `gates.yml` 中的phases定义
2. 更新 `get_phase_info()` 函数
3. 在推荐系统中添加新阶段的建议

## 🚀 快速开始

```bash
# 1. 运行演示
./.workflow/demo.sh

# 2. 初始化你的项目
./.workflow/executor.sh init

# 3. 开始第一个工作流
./.workflow/executor.sh status
./.workflow/executor.sh suggest
```

---

**🎯 设计理念**: 自动化、智能化、非侵入式的工作流管理，让开发者专注于核心业务逻辑，而非流程管理。