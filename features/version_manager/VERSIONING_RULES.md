# Perfect21 版本管理规范

## 🎯 语义化版本控制规则 (SemVer 2.0.0)

Perfect21采用语义化版本控制（Semantic Versioning 2.0.0），格式为：`MAJOR.MINOR.PATCH`

### 版本号构成
```
X.Y.Z[-PRE_RELEASE][+BUILD_METADATA]
│ │ │
│ │ └─ PATCH: 修订号
│ └─── MINOR: 次版本号
└───── MAJOR: 主版本号
```

## 📊 版本升级规则

### 🔴 Major版本 (X.0.0) - 重大变更
**触发条件**：
- 架构重大重构或重新设计
- 不兼容的API变更或接口破坏
- 核心功能模块移除或重构
- 依赖关系的重大变更（如claude-code-unified-agents版本跳跃）
- 配置文件格式不兼容变更

**历史示例**：
- `v1.0.0 → v2.0.0`: 集成claude-code-unified-agents，架构重构从单一工具变为多Agent协作平台

**升级评估标准**：
- [ ] 现有用户是否需要修改代码或配置？
- [ ] 是否移除或重命名了公共API？
- [ ] 是否改变了核心工作流程？

### 🟡 Minor版本 (X.Y.0) - 功能增强
**触发条件**：
- 新增功能模块（如新的feature包）
- 向后兼容的功能增强
- 新增Agent集成或SubAgent支持
- 新增CLI命令或API接口
- 新增配置选项（保持向后兼容）

**历史示例**：
- `v2.0.0 → v2.1.0`: 新增capability_discovery、version_manager、完善git_workflow功能

**升级评估标准**：
- [ ] 是否新增了功能模块？
- [ ] 是否新增了API接口或CLI命令？
- [ ] 是否完全向后兼容？

### 🟢 Patch版本 (X.Y.Z) - 修复和优化
**触发条件**：
- Bug修复和错误处理改进
- 性能优化和代码重构
- 文档更新和注释完善
- 依赖包小版本更新
- 日志和错误消息改进

**升级评估标准**：
- [ ] 是否只涉及bug修复？
- [ ] 是否只是性能或文档改进？
- [ ] 是否完全向后兼容？

## 🚀 预发布版本

### Alpha版本 (X.Y.Z-alpha.N)
- 内部测试版本
- 功能可能不完整或不稳定
- 用于早期功能验证

### Beta版本 (X.Y.Z-beta.N)
- 功能完整但可能有bug
- 用于更广泛的测试
- API基本稳定

### RC版本 (X.Y.Z-rc.N)
- 发布候选版本
- 功能完整且稳定
- 主要用于最终验证

## 🎯 版本升级决策矩阵

| 变更类型 | 示例 | 版本类型 | 影响评估 |
|---------|------|---------|---------|
| 架构重构 | 更换核心依赖 | Major | 高 |
| API变更 | 删除公共方法 | Major | 高 |
| 新增模块 | 添加features/new_feature | Minor | 中 |
| 功能增强 | 新增CLI命令 | Minor | 中 |
| Bug修复 | 修复现有功能错误 | Patch | 低 |
| 文档更新 | 更新README | Patch | 低 |

## 🔧 自动化决策规则

### Breaking Changes检测
```python
# 检测breaking changes的规则
BREAKING_CHANGES_PATTERNS = [
    "删除public方法或类",
    "更改public API签名",
    "移除CLI命令或参数",
    "更改配置文件格式",
    "更改默认行为",
    "提升最低依赖版本要求"
]
```

### 功能变更检测
```python
# 检测功能变更的规则
FEATURE_CHANGES_PATTERNS = [
    "新增features/目录",
    "新增CLI命令",
    "新增API接口",
    "新增配置选项",
    "新增Agent集成"
]
```

## 📋 版本发布流程

### 1. 版本规划阶段
- [ ] 评估变更类型和影响范围
- [ ] 确定版本号（Major/Minor/Patch）
- [ ] 更新CHANGELOG.md

### 2. 开发阶段
- [ ] 功能开发和测试
- [ ] 文档更新
- [ ] 版本号同步检查

### 3. 发布前验证
- [ ] 版本一致性检查 (`vm.validate_version_consistency()`)
- [ ] 自动化测试通过
- [ ] 文档完整性检查

### 4. 正式发布
- [ ] 创建Git标签 (`git tag -a vX.Y.Z`)
- [ ] 更新版本文档
- [ ] 发布说明编写

## 🎉 版本命名约定

### Git标签格式
```bash
v2.1.0          # 正式版本
v2.1.0-alpha.1  # Alpha版本
v2.1.0-beta.2   # Beta版本
v2.1.0-rc.1     # RC版本
```

### 分支命名格式
```bash
release/v2.1.0    # 发布分支
hotfix/v2.1.1     # 热修复分支
```

## 📊 版本兼容性承诺

### 向后兼容性
- **Major版本**: 可能不兼容，需要用户适配
- **Minor版本**: 完全向后兼容，安全升级
- **Patch版本**: 完全向后兼容，建议升级

### 支持政策
- **当前Major版本**: 全功能支持和更新
- **前一个Major版本**: 安全更新和重要bug修复
- **更老版本**: 仅社区支持

---

*此文档随Perfect21版本演进持续更新*
*最后更新: 2025-09-15*
*适用版本: Perfect21 v2.1.0+*