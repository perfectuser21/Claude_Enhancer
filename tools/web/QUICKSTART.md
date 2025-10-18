# 30秒快速启动

## 启动Dashboard

```bash
cd /path/to/Claude\ Enhancer\ 5.0
bash scripts/serve_progress.sh
```

## 访问

打开浏览器访问：**http://localhost:8999**

## 你将看到

```
┌─────────────────────────────────────────┐
│  🧬 Claude Enhancer Workflow Progress   │
│                                         │
│        整体进度：42%                     │
│  ████████████░░░░░░░░░░░░                │
│                                         │
│  当前阶段：P2 Implementation             │
│  活跃Agents：3/6                        │
│  影响半径：69分（高风险任务）            │
├─────────────────────────────────────────┤
│  Phase 0: Discovery          ✅ 100%   │
│  ████████████████████████████  7/7     │
│                                         │
│  Phase 1: Planning           ✅ 100%   │
│  ████████████████████████████  12/12   │
│                                         │
│  Phase 2: Implementation     🔵 67%    │
│  ████████████████░░░░░░░░░░  10/15     │
│  ⚠️  code_coverage_check: 72% < 80%    │
│                                         │
│  Phase 3: Testing            ⏳ 0%     │
│  Phase 4: Review             ⏳ 0%     │
│  Phase 5: Release            ⏳ 0%     │
└─────────────────────────────────────────┘
```

## 功能

- ✅ 6个Phase实时进度监控
- ✅ 整体进度百分比（大号显示）
- ✅ 每个Phase显示X/Y通过
- ✅ 失败项红色/黄色标记
- ✅ 10秒自动刷新
- ✅ 移动端友好

## 自定义端口

```bash
export WORKFLOW_DASHBOARD_PORT=9000
bash scripts/serve_progress.sh
```

## 停止服务器

按 `Ctrl+C` 或：

```bash
kill $(lsof -ti:8999)
```

## 故障排查

### 端口被占用

```bash
export WORKFLOW_DASHBOARD_PORT=9000
bash scripts/serve_progress.sh
```

### 无数据显示

确保有活跃的workflow：

```bash
ls -la .workflow/current
```

## 更多信息

- 📖 用户文档：`tools/web/README.md`
- 🔧 技术文档：`tools/web/TECHNICAL.md`
- 📊 完整报告：`.temp/workflow_dashboard_design_report.md`

---

**就是这么简单！** 🎉
