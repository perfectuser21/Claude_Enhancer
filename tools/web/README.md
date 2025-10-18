# Workflow Dashboard - 使用指南

## 快速开始

### 1. 启动Dashboard服务器

```bash
# 在项目根目录执行
bash scripts/serve_progress.sh
```

### 2. 打开浏览器

访问: **http://localhost:8999**

### 3. 查看实时进度

Dashboard会每10秒自动刷新，显示：
- 整体进度百分比
- 当前Phase状态
- 每个Phase的详细进度（0/7完成）
- 失败的检查项（红色标记）
- Impact半径评估

---

## 功能特性

### ✅ 实时进度监控
- 6个Phase（P0-P5）的实时状态
- 整体进度大号显示
- 自动10秒轮询刷新

### 🎨 可视化设计
- 绿色：已完成（100%）
- 蓝色：进行中（1-99%）
- 灰色：待开始（0%）
- 黄色：警告（非阻塞）
- 红色：失败（阻塞性）

### 📱 响应式布局
- 桌面端：900px宽度
- 移动端：自适应布局
- 卡片悬浮效果

### 🔄 手动刷新
点击右上角"🔄 Refresh"按钮立即刷新

---

## API端点

### GET /api/progress

返回当前工作流进度JSON：

```json
{
  "timestamp": "2025-10-17T08:54:15Z",
  "task_name": "工作流验证与可视化系统",
  "current_phase": "P0",
  "overall_progress": 17,
  "phases": [
    {
      "id": "P0",
      "name": "Discovery",
      "status": "in_progress",
      "progress": 100,
      "total_checks": 7,
      "passed_checks": 7,
      "failed_checks": [],
      "started_at": "2025-10-17T10:30:00Z",
      "completed_at": null
    }
    // ... 其他phases
  ],
  "impact_assessment": {
    "score": 69,
    "level": "high-risk",
    "recommended_agents": 6
  },
  "agents_active": 0,
  "agents_total": 6
}
```

---

## 配置选项

### 自定义端口

```bash
# 使用不同端口
export WORKFLOW_DASHBOARD_PORT=9000
bash scripts/serve_progress.sh
```

### 数据来源

Dashboard从以下文件读取数据：
- `.workflow/current` - 当前Phase状态
- `.workflow/impact_assessments/current.json` - Impact评估
- `.workflow/gates.yml` - Phase定义

生成的数据存储在：
- `.temp/workflow_progress.json`

---

## 故障排查

### 问题1：端口已被占用

```bash
# 错误信息
Port 8999 is already in use

# 解决方案
export WORKFLOW_DASHBOARD_PORT=9000
bash scripts/serve_progress.sh
```

### 问题2：没有工作流数据

```bash
# 错误信息
"error": "No active workflow found"

# 解决方案：确保有活跃的workflow
ls -la .workflow/current
```

### 问题3：Dashboard显示空白

1. 检查浏览器控制台错误
2. 验证API响应：`curl http://localhost:8999/api/progress`
3. 检查文件权限：`ls -la tools/web/dashboard.html`

---

## 技术架构

### 前端
- **纯HTML + Vanilla JavaScript**
- 无依赖，直接打开即用
- CSS Grid/Flexbox响应式布局
- Fetch API轮询

### 后端
- **Python 3 HTTP Server**
- 端口：8999（可配置）
- CORS支持
- 动态生成进度数据

### 数据生成
- **Bash + Python混合脚本**
- 解析YAML配置
- 实时计算进度

---

## 文件结构

```
tools/web/
├── dashboard.html        # Dashboard前端
└── README.md            # 本文件

scripts/
├── serve_progress.sh    # HTTP服务器
└── generate_progress_data.sh  # 数据生成器

.temp/
└── workflow_progress.json   # 生成的进度数据

.workflow/
├── current              # 当前Phase状态
├── gates.yml           # Phase定义
└── impact_assessments/
    └── current.json    # Impact评估
```

---

## 未来增强（可选）

### 阶段2：React集成
- 集成到现有`frontend/src/pages/workflow/`
- 复用Chakra UI组件
- WebSocket实时推送
- 更丰富的交互体验

### 阶段3：高级功能
- Phase日志实时流
- Agent执行详情
- 失败检查项详细说明
- 历史进度回放

---

## 常见问题

**Q: 为什么选择纯HTML而不是React？**

A: 第一阶段优先简单性和零依赖，任何人打开浏览器即可查看。React集成作为可选增强。

**Q: 数据多久刷新一次？**

A: 默认10秒自动刷新，也可以手动点击Refresh按钮。

**Q: 可以在远程服务器上运行吗？**

A: 可以，但需要修改Python服务器绑定地址从`localhost`改为`0.0.0.0`，并注意安全性。

**Q: 如何集成到现有前端？**

A: 参考`frontend/src/pages/workflow/RealSystemDashboard.tsx`，创建新的React组件调用`/api/progress`端点。

---

**作者**: Claude Enhancer Team
**版本**: 1.0.0
**更新**: 2025-10-17
