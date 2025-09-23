# ADR-002: Features层采用智能分级（Basic-Standard-Advanced）

## 状态
已采纳

## 日期
2025-09-23

## 背景
Features层会持续增长，需要一个合理的组织方式。不是所有Feature都需要复杂的内部结构。

## 决策
Features层分为三个级别：
- **Basic**：简单工具，单文件实现
- **Standard**：中等复杂度，文件夹组织
- **Advanced**：复杂系统，可内部再分core/main/modules

## 理由
1. **避免过度设计**：简单功能保持简单
2. **渐进式复杂度**：随需求增长而演进
3. **灵活组织**：每个级别有适合的结构
4. **自然成长**：Feature可以从basic升级到advanced

## 影响
### 正面
- 小功能不会被过度组织
- 大系统有充分的结构空间
- 开发效率提高

### 负面
- 需要判断Feature属于哪个级别
- 可能需要定期调整分类

## 判断标准
```
代码量 < 100行 且 单一功能 → Basic
需要配置文件 或 多个组件 → Standard
独立子系统 且 内部复杂 → Advanced
```

## 示例
- Basic: `quick_fix.py`
- Standard: `code_review/` (包含规则、模板)
- Advanced: `ai_workflow/` (有自己的core/main/modules)

## 实施
1. 创建三个子目录
2. 制定分类标准文档
3. 迁移现有features
4. 建立升级机制

## 后续
- 每月评估分类合理性
- 记录Feature升级案例
- 优化判断标准