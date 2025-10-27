# Acceptance Checklist
# Claude Enhancer v8.0 - Dual Evolution Learning System
# 定义"完成"的标准

---

## 📋 核心功能验收

### 1. Learning System（学习系统）

- [ ] **1.1** Learning Item可以在Phase 2捕获错误模式
- [ ] **1.2** Learning Item可以在Phase 2捕获性能优化
- [ ] **1.3** Learning Item可以在Phase 3捕获测试失败模式
- [ ] **1.4** Learning Item可以在Phase 4捕获代码质量问题
- [ ] **1.5** Learning Item可以在Phase 1/4捕获架构决策
- [ ] **1.6** Learning Item可以在Phase 6捕获成功模式
- [ ] **1.7** 所有Learning Item存储为YAML格式
- [ ] **1.8** Learning Item文件命名遵守规范：`{timestamp}_{seq}_{category}_{project}.yml`
- [ ] **1.9** 在CE目录开发时，项目名为"claude-enhancer"
- [ ] **1.10** 在外部项目开发时，Learning Item返回存储到CE目录
- [ ] **1.11** 实现by_project符号链接索引
- [ ] **1.12** 实现by_category符号链接索引

### 2. Auto-fix Mechanism（自动修复机制）

- [ ] **2.1** Tier1 (Auto)：可以自动修复依赖缺失（ImportError）
- [ ] **2.2** Tier1 (Auto)：可以自动修复格式化错误
- [ ] **2.3** Tier1 (Auto)：可以自动修复端口冲突
- [ ] **2.4** Tier2 (Try Then Ask)：构建失败时尝试修复，失败后询问
- [ ] **2.5** Tier2 (Try Then Ask)：测试失败时尝试修复，失败后询问
- [ ] **2.6** Tier3 (Must Confirm)：数据迁移必须询问用户
- [ ] **2.7** Tier3 (Must Confirm)：安全补丁必须询问用户
- [ ] **2.8** Auto-fix所有操作记录到audit日志
- [ ] **2.9** Auto-fix失败可以自动回滚
- [ ] **2.10** Auto-fix集成到Phase 2 Implementation
- [ ] **2.11** Auto-fix集成到Phase 3 Testing

### 3. TODO Queue System（TODO队列系统）

- [ ] **3.1** Learning Item（confidence ≥ 0.80）自动转换为TODO
- [ ] **3.2** Learning Item（confidence < 0.80）加入待审查队列
- [ ] **3.3** TODO包含完整信息：标题、描述、优先级、预估工作量
- [ ] **3.4** TODO关联到原始Learning Item（可追溯）
- [ ] **3.5** 实现`ce todo list`命令
- [ ] **3.6** 实现`ce todo show <id>`命令
- [ ] **3.7** 实现`ce todo accept <id>`命令
- [ ] **3.8** 实现`ce todo reject <id>`命令
- [ ] **3.9** 实现`ce todo defer <id> --days N`命令
- [ ] **3.10** TODO状态管理：pending → in_progress → completed/rejected

### 4. Notion Integration（Notion同步）

- [ ] **4.1** Phase 7完成后自动触发Notion同步
- [ ] **4.2** Learning Items同步到Notion "notes" database
- [ ] **4.3** TODOs同步到Notion "tasks" database
- [ ] **4.4** Project Summary同步到Notion "events" database
- [ ] **4.5** 生成非技术摘要（中文，无技术术语）
- [ ] **4.6** 实现术语替换字典（API→接口，数据库→数据存储等）
- [ ] **4.7** 实现`ce sync notion`手动同步命令
- [ ] **4.8** 同步失败时记录错误并支持重试
- [ ] **4.9** 同步历史记录保存到`.notion/sync_history.json`
- [ ] **4.10** Notion Token安全存储（不提交到Git）

### 5. ce命令行工具

- [ ] **5.1** 实现`ce dev`命令（在外部项目启动CE工作流）
- [ ] **5.2** 实现`ce mode status`命令（查看当前模式）
- [ ] **5.3** 实现`ce learning list`命令（查看Learning Items）
- [ ] **5.4** 实现`ce learning stats`命令（统计信息）
- [ ] **5.5** 实现`ce todo list`命令（查看TODO队列）
- [ ] **5.6** 实现`ce sync notion`命令（手动同步）
- [ ] **5.7** CE_HOME环境变量自动检测（fallback机制）
- [ ] **5.8** 所有命令提供`--help`帮助信息
- [ ] **5.9** 所有命令提供`--dry-run`预览模式

---

## 🏗️ 架构验收

### 6. 文件结构

- [ ] **6.1** 创建`.learning/`目录结构
- [ ] **6.2** 创建`.learning/items/`存储Learning Items
- [ ] **6.3** 创建`.learning/by_project/`项目索引
- [ ] **6.4** 创建`.learning/by_category/`类别索引
- [ ] **6.5** 创建`.learning/index.json`全局索引
- [ ] **6.6** 创建`.learning/stats.json`统计信息
- [ ] **6.7** 创建`.todos/`目录结构
- [ ] **6.8** 创建`.notion/`目录结构
- [ ] **6.9** 创建`scripts/learning/`脚本目录
- [ ] **6.10** 所有新增目录添加到`.gitignore`（数据不提交）

### 7. 集成验收

- [ ] **7.1** Phase 1嵌入架构学习钩子（不修改检查点数量）
- [ ] **7.2** Phase 2嵌入错误捕获和Auto-fix钩子
- [ ] **7.3** Phase 3嵌入性能学习和测试Auto-fix钩子
- [ ] **7.4** Phase 4嵌入代码质量学习钩子
- [ ] **7.5** Phase 7嵌入Notion同步钩子
- [ ] **7.6** 所有钩子不阻塞Phase正常执行（失败仅记录警告）
- [ ] **7.7** `tools/verify-core-structure.sh`验证通过（97检查点保持）
- [ ] **7.8** 不违反规则1（根目录文档≤7个）
- [ ] **7.9** 不违反规则2（核心结构锁定）

---

## 🧪 测试验收

### 8. 单元测试

- [ ] **8.1** Learning Item YAML序列化/反序列化测试
- [ ] **8.2** CE_HOME自动检测测试
- [ ] **8.3** Auto-fix Tier分类逻辑测试
- [ ] **8.4** TODO转换规则测试
- [ ] **8.5** 非技术摘要生成测试（术语替换）
- [ ] **8.6** 符号链接索引创建测试

### 9. 集成测试

- [ ] **9.1** 完整7-Phase工作流测试（CE自身开发）
- [ ] **9.2** 完整7-Phase工作流测试（外部项目开发）
- [ ] **9.3** Learning Item跨Phase捕获测试
- [ ] **9.4** Auto-fix端到端测试（Tier1/Tier2/Tier3）
- [ ] **9.5** TODO队列完整流程测试
- [ ] **9.6** Notion同步端到端测试

### 10. 性能测试

- [ ] **10.1** Learning Item写入性能<50ms
- [ ] **10.2** CE_HOME自动检测<100ms
- [ ] **10.3** Auto-fix决策<20ms
- [ ] **10.4** TODO转换<10ms/item
- [ ] **10.5** Notion同步<30s（100个Learning Items）

---

## 📖 文档验收

### 11. 用户文档

- [ ] **11.1** 更新README.md说明v8.0新功能
- [ ] **11.2** 更新CLAUDE.md添加Learning System说明
- [ ] **11.3** 创建Learning System用户指南
- [ ] **11.4** 创建Auto-fix配置指南
- [ ] **11.5** 创建TODO队列使用指南
- [ ] **11.6** 创建Notion集成配置指南
- [ ] **11.7** 所有新命令添加到命令参考

### 12. 技术文档

- [ ] **12.1** P1_DISCOVERY.md完成（>300行）✅
- [ ] **12.2** PLAN.md完成（>1000行）
- [ ] **12.3** Learning System架构文档
- [ ] **12.4** Auto-fix设计文档
- [ ] **12.5** 数据格式规范文档（YAML schemas）
- [ ] **12.6** API文档（ce命令行接口）

---

## 🔒 质量验收

### 13. Phase 3质量门禁

- [ ] **13.1** Shell语法验证通过（bash -n）
- [ ] **13.2** Shellcheck linting通过（无严重警告）
- [ ] **13.3** 代码复杂度<150行/函数
- [ ] **13.4** Hook性能<2秒
- [ ] **13.5** 测试覆盖率≥70%

### 14. Phase 4质量门禁

- [ ] **14.1** 配置完整性验证通过
- [ ] **14.2** 无遗留TODO/FIXME
- [ ] **14.3** 根目录文档≤7个
- [ ] **14.4** 版本一致性验证通过（6个文件）
- [ ] **14.5** 代码模式一致性验证通过
- [ ] **14.6** REVIEW.md完成（>3KB）

---

## 🎯 验收标准汇总

**必须达到≥90%完成率才能进入Phase 5**

- **核心功能**: 42个检查点
- **架构**: 9个检查点
- **测试**: 12个检查点
- **文档**: 13个检查点
- **质量**: 11个检查点

**总计**: 87个验收检查点

---

## ✅ 验收签字

- [ ] **Phase 1**: 架构设计合理，技术可行 __________ (日期)
- [ ] **Phase 2**: 核心功能实现完整 __________ (日期)
- [ ] **Phase 3**: 所有测试通过 __________ (日期)
- [ ] **Phase 4**: 代码审查通过 __________ (日期)
- [ ] **Phase 5**: 文档完整 __________ (日期)
- [ ] **Phase 6**: 用户验收通过 __________ (日期)
- [ ] **Phase 7**: 准备合并 __________ (日期)

---

**创建日期**: 2025-10-27
**目标版本**: v8.0.0
**状态**: Phase 1 - 规划中
