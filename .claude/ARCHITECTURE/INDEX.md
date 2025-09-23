# 📚 Claude Enhancer架构文档索引

> 本文件供Claude Code在执行任务时参考
> 包含所有关键架构文档的路径和用途说明

## 🏗️ 核心架构文档

### 必读文档（执行任务前应了解）
1. **[v2.0-FOUNDATION.md](./v2.0-FOUNDATION.md)**
   - 四层架构定义（Core-Framework-Services-Features）
   - 版本策略和设计原则
   - **何时读**: 需要理解系统整体架构时

2. **[LAYER-DEFINITION.md](./LAYER-DEFINITION.md)**
   - L0-L3层详细职责
   - 依赖规则和层级关系
   - **何时读**: 添加新功能，判断放在哪层时

3. **[GROWTH-STRATEGY.md](./GROWTH-STRATEGY.md)**
   - Feature分级标准（basic/standard/advanced）
   - 成长路径和优化策略
   - **何时读**: 创建新Feature时

## 📋 开发规范文档

4. **[NAMING-CONVENTIONS.md](./NAMING-CONVENTIONS.md)**
   - 文件、目录、变量命名规则
   - **何时读**: 创建新文件或重构时

## 🔍 架构决策记录

5. **[decisions/](./decisions/)**
   - ADR-001: 四层架构决策
   - ADR-002: Features智能分级
   - ADR-003: 文档保护机制
   - **何时读**: 需要理解设计理由时

## 📊 实施状态

6. **[IMPLEMENTATION-STATUS.md](./IMPLEMENTATION-STATUS.md)**
   - 当前实施进度
   - 迁移计划
   - **何时读**: 执行架构迁移任务时

## 🎯 快速参考

### 添加新功能时的决策树
```
代码 < 100行 且 单一功能？
  → features/basic/[功能名].py

需要配置文件 或 多个文件？
  → features/standard/[功能名]/

复杂子系统 且 需要内部分层？
  → features/advanced/[系统名]/
     ├── core/
     ├── main/
     └── modules/
```

### 层级依赖规则
```
允许: L3→L2→L1→L0 (上层可调用下层)
禁止: L0→L1/L2/L3 (下层不能依赖上层)
```

### 文件放置快速指南
- 永不变的核心逻辑 → `core/`
- 工作流和策略 → `framework/`
- 共享工具服务 → `services/`
- 具体功能实现 → `features/`

---
*此索引帮助Claude Code快速定位架构文档*
*更新时间：2025-09-23*