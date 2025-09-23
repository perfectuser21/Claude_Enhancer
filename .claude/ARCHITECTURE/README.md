# ⚠️ 架构文档保护区

## 🔒 重要声明
此目录包含Claude Enhancer的核心架构决策和设计理念。
**永远不要删除或移动此目录！**

## 📋 保护规则
1. **只增不减**：此目录下的文件只能增加，不能删除
2. **版本备份**：修改任何文件前必须先备份原版本
3. **决策记录**：每个重大架构决策都要在 `decisions/` 目录记录
4. **独立保护**：版本迭代和重构不影响此目录

## 📁 目录结构说明
```
ARCHITECTURE/
├── README.md                      # 本文件，保护声明
├── v2.0-FOUNDATION.md            # v2.0基础架构定义（2025-09-23）
├── LAYER-DEFINITION.md           # 四层架构详细定义（L0-L3）
├── GROWTH-STRATEGY.md            # Claude Enhancer成长策略
├── NAMING-CONVENTIONS.md         # 命名规范和约定
└── decisions/                    # 架构决策记录（ADR）
    ├── 001-core-framework-services-features.md
    ├── 002-smart-layering.md
    └── 003-feature-classification.md
```

## 🎯 核心架构版本
- **当前版本**: v2.0
- **制定日期**: 2025-09-23
- **架构类型**: 四层智能分层架构（L0-L3）

## 📚 文档阅读顺序
1. `v2.0-FOUNDATION.md` - 了解基础架构
2. `LAYER-DEFINITION.md` - 理解层级职责
3. `GROWTH-STRATEGY.md` - 掌握成长路径
4. `decisions/*.md` - 查看历史决策

## ⚙️ 自动保护机制
- Git配置：`.gitignore` 和 `.gitattributes` 已配置保护
- 脚本检查：`scripts/protect_architecture.sh` 定期检查完整性
- 配置标记：在 `core/config.yaml` 中标记为受保护路径

## 🚨 警告
违反保护规则可能导致：
- 架构知识丢失
- 设计理念失传
- 历史决策遗忘
- 系统演进混乱

---
*此目录由Claude Enhancer架构委员会维护*
*最后更新：2025-09-23*