# Gate Validator v5.0 使用指南

> Claude Enhancer 5.0 完整验证系统 - 确保工作流质量和规范

## 🎯 核心功能

Gate Validator 是 Claude Enhancer 5.0 的核心验证组件，提供：

1. **路径白名单验证** - 确保只修改允许的文件和目录
2. **必须产出检查** - 验证Phase要求的文件和内容存在
3. **Gates条件验证** - 检查构建、测试等条件
4. **并行限制检查** - 确保Agent数量不超过Phase限制

## 📋 快速开始

### 基本用法

```bash
# 验证当前Phase
./.workflow/gate_validator.sh

# 验证特定Phase和Agent数量
./.workflow/gate_validator.sh P3 6

# 详细模式验证
./.workflow/gate_validator.sh -v P2

# 显示当前Phase
./.workflow/gate_validator.sh --current

# 显示所有Phase状态
./.workflow/gate_validator.sh --status
```

### 返回码

- `0` - 验证通过
- `1` - 验证失败

## 🔧 配置文件

Gate Validator 使用 `.workflow/gates.yml` 作为配置文件。主要配置项：

### Phase配置

每个Phase包含以下配置：

```yaml
phases:
  P1:
    name: "Plan"
    allow_paths: ["docs/PLAN.md"]  # 路径白名单
    must_produce:                   # 必须产出
      - "docs/PLAN.md: 包含三级标题：## 任务清单, ## 受影响文件清单, ## 回滚方案"
      - "任务清单≥5条（每条以动词开头，包含具体文件/模块名）"
    gates:                          # 验证条件
      - "必须存在 docs/PLAN.md"
      - "必须匹配三个标题"
```

### 并行限制

```yaml
parallel_limits:
  P1: 4    # Phase P1 最多4个Agent
  P2: 6    # Phase P2 最多6个Agent
  P3: 8    # Phase P3 最多8个Agent
  P4: 6    # Phase P4 最多6个Agent
  P5: 4    # Phase P5 最多4个Agent
  P6: 2    # Phase P6 最多2个Agent
```

## 📝 验证规则详解

### 1. 路径白名单验证

检查Git变更的文件是否在允许的路径范围内：

- ✅ 允许：`src/auth/login.ts` (匹配 `src/**`)
- ❌ 禁止：`config/database.yml` (不在白名单)

支持的路径模式：
- `docs/PLAN.md` - 精确文件路径
- `src/**` - 目录及其所有子文件
- `tests/**` - 测试目录

### 2. 必须产出检查

验证Phase要求的文件和内容：

#### 文件存在性检查
```yaml
must_produce:
  - "docs/PLAN.md: 包含项目计划"
```

#### 内容要求检查
- **三级标题检查** - 检查文件是否包含 `## 标题`
- **任务清单数量** - 检查列表项数量 (`-` 开头的行)
- **测试数量** - 检查测试文件数量

#### 特殊检查规则
- `任务清单≥5条` - 检查列表项数量
- `新增.*测试.*≥.*2` - 检查测试文件数量
- `三段：风格一致性/风险清单/回滚可行性` - 检查段落数量

### 3. Gates条件验证

检查特定的验证条件：

#### 文件存在条件
- `必须存在 docs/PLAN.md` - 检查文件存在
- `必须匹配三个标题` - 检查内容格式

#### 构建条件
- `构建/编译通过` - 运行构建命令
  - Node.js项目：`npm run build`
  - Make项目：`make build`

#### 测试条件
- `pre-push: unit+boundary+smoke 必须绿` - 运行测试
  - Node.js项目：`npm test`

### 4. 并行限制检查

确保使用的Agent数量不超过Phase限制：

```
Phase P1: 最多4个Agent  (计划阶段，轻量)
Phase P2: 最多6个Agent  (骨架阶段，中等)
Phase P3: 最多8个Agent  (实现阶段，重量)
Phase P4: 最多6个Agent  (测试阶段，中等)
Phase P5: 最多4个Agent  (审查阶段，轻量)
Phase P6: 最多2个Agent  (发布阶段，最轻)
```

## 📊 报告和日志

### 验证报告

每次验证都会生成详细报告：

```
.workflow/logs/gate_validation_P1_2025-09-26T14:47:28+08:00.log
```

报告内容：
- Phase和状态
- 验证详情
- 环境信息
- 配置信息

### Gate状态标记

验证通过时创建标记文件：

```
.gates/1.ok    # P1通过标记
.gates/2.ok    # P2通过标记
...
```

## 🚀 集成示例

### 在工作流中集成

```bash
#!/bin/bash
# 示例：Agent选择前验证

PHASE="P3"
AGENT_COUNT=6

# 1. 检查并行限制
if ! ./.workflow/gate_validator.sh "$PHASE" "$AGENT_COUNT" >/dev/null 2>&1; then
    echo "错误：Agent数量超出限制"
    exit 1
fi

# 2. 执行Agent任务
echo "开始执行 $AGENT_COUNT 个Agent..."
# ... 执行实际任务 ...

# 3. 验证Phase完成
if ./.workflow/gate_validator.sh "$PHASE" "$AGENT_COUNT"; then
    echo "Phase $PHASE 验证通过"
else
    echo "Phase $PHASE 验证失败，请检查产出"
    exit 1
fi
```

### Claude Code集成

```typescript
// 伪代码：Claude Code中的集成
async function executePhase(phase: string, agents: Agent[]) {
    // 1. 验证并行限制
    const validator = new GateValidator();
    if (!await validator.validateParallelLimit(phase, agents.length)) {
        throw new Error(`Phase ${phase} Agent数量超限`);
    }

    // 2. 执行Agent任务
    await Promise.all(agents.map(agent => agent.execute()));

    // 3. 验证Phase完成
    const result = await validator.validateGate(phase, agents.length);
    if (!result.success) {
        throw new Error(`Phase ${phase} 验证失败: ${result.errors.join(', ')}`);
    }

    return result;
}
```

## 🛠️ 故障排查

### 常见问题

#### 1. 路径白名单违规
```
错误: 路径白名单违规：
  - config/database.yml
```

**解决方案**:
- 检查 `gates.yml` 中的 `allow_paths` 配置
- 确保修改的文件在允许范围内
- 如需修改配置文件，需要更新白名单

#### 2. 必须产出缺失
```
错误: 必须产出验证失败：
  - 缺少文件: docs/PLAN.md
```

**解决方案**:
- 创建缺失的文件
- 确保文件内容符合要求
- 检查文件路径是否正确

#### 3. 并行限制超出
```
错误: 并行限制超出: 使用了 10 个agent，但Phase P1 限制为 4
```

**解决方案**:
- 减少Agent数量
- 或者检查是否Phase识别错误
- 考虑分阶段执行

#### 4. Gates条件失败
```
错误: Gates条件验证失败：
  - 构建失败
```

**解决方案**:
- 修复构建错误
- 确保依赖项已安装
- 检查代码语法错误

### 调试技巧

#### 1. 使用详细模式
```bash
./.workflow/gate_validator.sh -v P3 6
```

#### 2. 检查配置文件
```bash
cat .workflow/gates.yml
```

#### 3. 查看报告文件
```bash
ls -la .workflow/logs/gate_validation_*.log
cat .workflow/logs/gate_validation_P3_*.log
```

#### 4. 检查Phase状态
```bash
./.workflow/gate_validator.sh --status
```

## 📚 最佳实践

### 1. Phase流程管理

- **按顺序执行Phase** - 不要跳跃执行
- **每个Phase验证后再进入下一个** - 确保质量
- **关键Phase加强验证** - P3(实现)和P4(测试)

### 2. Agent数量优化

- **简单任务用较少Agent** - P1, P5, P6
- **复杂任务用较多Agent** - P3最多8个
- **根据任务复杂度动态调整** - 不要死板遵循限制

### 3. 错误处理

- **及时修复验证错误** - 不要累积问题
- **查看详细报告** - 理解具体失败原因
- **渐进式修复** - 一次解决一个问题

### 4. 配置维护

- **定期更新gates.yml** - 适应项目变化
- **合理设置白名单** - 既要安全又要灵活
- **测试验证规则** - 确保规则有效性

## 🎉 总结

Gate Validator 提供了完整的工作流验证体系，通过：

- ✅ **自动化验证** - 减少人工检查成本
- ✅ **规范化流程** - 确保团队一致性
- ✅ **质量保证** - 每个Phase都有明确标准
- ✅ **灵活配置** - 适应不同项目需求

使用Gate Validator可以显著提高开发质量和团队协作效率！