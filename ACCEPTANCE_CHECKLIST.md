# CE Comprehensive Dashboard v2 - Acceptance Checklist

**Version**: 7.2.0  
**Created**: 2025-10-23  
**Purpose**: Define success criteria for CE Dashboard v2 with capability showcase and learning system

---

## 📊 Section 1: CE能力展示 (6 criteria)

### 1.1 核心能力清单显示
- [ ] 显示7-Phase工作流系统  
- [ ] 显示97个检查点统计  
- [ ] 显示2个质量门禁  
- [ ] 显示分支保护机制（100%防护率）  
- [ ] 显示65个BDD场景  
- [ ] 显示90个性能指标  

### 1.2 能力详情展示  
- [ ] 基于CAPABILITY_MATRIX.md展示C0-C9能力  
- [ ] 每个能力显示：名称、类型、保障力等级  
- [ ] 可展开查看详细验证逻辑  
- [ ] 显示失败表现和修复动作  

### 1.3 Feature映射（复用dashboard.html）  
- [ ] 显示F001-F012功能卡片  
- [ ] 每个feature显示：图标、名称、描述、优先级、类别  
- [ ] 点击feature高亮相关检查点  
- [ ] 显示feature与steps的映射关系  

---

## 🧠 Section 2: 学习系统展示 (8 criteria)

### 2.1 决策历史 (DECISIONS.md)  
- [ ] 显示历史决策列表  
- [ ] 每个决策显示：日期、决策内容、原因  
- [ ] 显示禁止操作和允许操作  
- [ ] 显示影响范围  

### 2.2 上下文记忆 (memory-cache.json)  
- [ ] 显示recent_decisions对象  
- [ ] 每个记忆显示：importance等级（critical/warning/info）  
- [ ] 显示do_not_revert标记  
- [ ] 显示affected_files列表  

### 2.3 决策索引 (decision-index.json)  
- [ ] 显示按月份归档的决策  
- [ ] 显示归档统计（总数、大小）  
- [ ] 支持查看历史归档概要  

### 2.4 学习统计  
- [ ] 总决策数量统计  
- [ ] Critical/Warning/Info决策分布  
- [ ] 最近30天决策趋势  
- [ ] 记忆缓存大小监控（目标<5KB）  

---

## 📦 Section 3: 项目监控 (7 criteria)

### 3.1 多项目列表  
- [ ] 显示所有监控的项目列表  
- [ ] 每个项目显示：项目名、当前分支、当前Phase  
- [ ] 显示项目进度百分比  
- [ ] 区分active/idle/completed状态  

### 3.2 实时进度  
- [ ] 基于telemetry事件实时更新（5秒刷新）  
- [ ] 显示当前Phase (Phase 1-7)  
- [ ] 显示任务名称  
- [ ] 显示Agent使用情况  

### 3.3 项目详情  
- [ ] 点击项目查看详细信息  
- [ ] 显示最近事件列表  
- [ ] 显示已完成的Phase  
- [ ] 显示遇到的问题（如有）  

### 3.4 历史记录  
- [ ] 显示最近完成的项目（最多10个）  
- [ ] 每个项目显示：完成时间、总耗时  
- [ ] 支持查看项目完整事件日志  

---

## 🎨 Section 4: 界面与交互 (6 criteria)

### 4.1 布局  
- [ ] 两栏布局：CE能力展示（左/上） + 项目监控（右/下）  
- [ ] 响应式设计（支持不同屏幕尺寸）  
- [ ] 清晰的视觉分隔  

### 4.2 自动刷新  
- [ ] 5秒自动刷新（项目监控部分）  
- [ ] 显示最后更新时间  
- [ ] 支持手动刷新按钮  

### 4.3 API端点  
- [ ] `/` - HTML dashboard  
- [ ] `/api/capabilities` - CE能力数据  
- [ ] `/api/learning` - 学习系统数据  
- [ ] `/api/projects` - 项目监控数据  
- [ ] `/api/health` - 健康检查  

### 4.4 用户体验  
- [ ] 页面加载时间<2秒  
- [ ] 无JavaScript错误  
- [ ] 良好的错误提示（数据缺失时）  

---

## ✅ 总计

- **4个核心Section**: CE能力、学习系统、项目监控、界面交互  
- **27个验收标准**  
- **7个BDD场景**（见下方）

**完成标准**: 所有27个验收标准必须通过 ✅  

---

## 🧪 BDD测试场景 (7 scenarios)

1. **查看CE核心能力** - 7-Phase + 97检查点 + 100%防护率  
2. **查看决策历史** - DECISIONS.md列表 + 禁止/允许操作  
3. **监控项目进度** - 项目名 + Phase + 进度% + 5秒刷新  
4. **查看学习统计** - 决策数量 + 重要性分布 + 缓存大小  
5. **API健康检查** - GET /api/health 返回200  
6. **多项目并发监控** - 3个项目独立进度 + 状态区分  
7. **优雅降级** - 文件缺失时显示友好提示  

---

**生成时间**: 2025-10-23 Phase 1.3  
**下一步**: Phase 1.4 Impact Assessment
