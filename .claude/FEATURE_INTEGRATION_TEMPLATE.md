# 新功能集成模板
# 使用此模板确保新功能彻底落地，而非空壳

## 📝 功能基本信息

- **功能名称**: [例：smart_cache]
- **功能类型**: [core/performance/quality/security/monitoring/utility]
- **开发者**: [AI/Human]
- **添加日期**: [YYYY-MM-DD]
- **版本要求**: [例：v7.3.0+]

## 🎯 功能定位

### 解决什么问题？
[明确描述要解决的具体问题]

### 与现有功能的关系
- **替代**: [是否替代某个现有功能]
- **增强**: [是否增强某个现有功能]
- **互补**: [与哪些功能配合使用]
- **冲突**: [可能与哪些功能冲突]

## 🏗️ 实现架构

### 文件结构
```
功能主体:
  - 位置: [.claude/tools/xxx.sh 或 scripts/xxx.sh]
  - 大小: [预计行数]
  - 模块: [是否需要拆分模块]

配置文件:
  - 位置: [.claude/config/xxx.yml]
  - 参数: [关键配置项]

测试文件:
  - 位置: [tests/test_xxx.sh]
  - 覆盖: [测试覆盖率目标]
```

### 依赖关系
```yaml
dependencies:
  required:    # 必须依赖
    - [功能A]
    - [功能B]
  optional:    # 可选依赖
    - [功能C]
  conflicts:   # 冲突项
    - [功能D]
```

## 🔧 Phase集成方案

### Phase 1 (Discovery)
- [ ] 不需要集成
- [ ] 需要集成，具体为：[描述]

### Phase 2 (Implementation)
- [ ] 不需要集成
- [ ] 需要集成，具体为：[描述]

### Phase 3 (Testing)
- [ ] 不需要集成
- [ ] 作为测试工具使用
- [ ] 具体集成点：[pre_test/post_test/replace_test]

### Phase 4 (Review)
- [ ] 不需要集成
- [ ] 作为审查工具使用
- [ ] 具体集成点：[pre_review/post_review/replace_review]

### Phase 5 (Release)
- [ ] 不需要集成
- [ ] 作为发布工具使用
- [ ] 具体集成点：[pre_release/post_release]

### Phase 6 (Acceptance)
- [ ] 不需要集成
- [ ] 需要验收确认

### Phase 7 (Closure)
- [ ] 不需要集成
- [ ] 作为清理工具使用

## 📊 性能指标

### 基线要求
```yaml
performance:
  latency: [<100ms]
  memory: [<50MB]
  cpu: [<5%]
```

### 测试方法
```bash
# 性能测试命令
time bash xxx.sh
# 内存测试命令
/usr/bin/time -v bash xxx.sh
```

## ✅ 集成验证清单

### 开发阶段
- [ ] 功能代码完成
- [ ] 单元测试编写
- [ ] 性能测试通过
- [ ] 文档更新

### 集成阶段
- [ ] 注册到FEATURE_REGISTRY.yaml
- [ ] Phase集成点配置
- [ ] Hook调用添加
- [ ] CI/CD集成

### 验证阶段
- [ ] 运行feature_integration_validator.sh
- [ ] 运行完整7-Phase流程
- [ ] 检查无冲突
- [ ] 性能无退化

### 发布阶段
- [ ] 更新CHANGELOG.md
- [ ] 更新README.md
- [ ] 版本号递增
- [ ] Tag创建

## 🚨 回滚方案

### 如何禁用
```bash
# 在FEATURE_REGISTRY.yaml中设置
status: "disabled"
```

### 如何卸载
```bash
# 1. 从注册表移除
# 2. 删除相关文件
# 3. 清理集成点
```

## 📝 经验教训

### 成功要素
- [什么做对了]

### 潜在风险
- [需要注意什么]

### 改进建议
- [下次如何做得更好]