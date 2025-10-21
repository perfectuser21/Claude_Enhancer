# Claude Enhancer 7.0 - Knowledge Base

## 📚 Purpose

This directory stores learning data from all projects using Claude Enhancer 7.0. The system automatically collects execution metrics and uses them to improve future project outcomes.

## 🗂️ Directory Structure

```
knowledge/
├── schema.json           # Data format definitions
├── sessions/             # Individual Phase execution records
│   └── YYYYMMDD_HHMMSS.json  # One file per Phase completion
├── metrics/              # Aggregated performance data
│   ├── web-app_duration.json
│   ├── cli-tool_duration.json
│   └── common_errors.json
├── patterns/             # Success patterns (curated)
│   ├── user_authentication.json
│   ├── api_development.json
│   └── ...
└── improvements/         # Auto-improvement logs (Milestone 3)
    └── YYYY-MM-DD_report.md
```

## 📊 Data Collection (Milestone 2)

### Session Data

每次 Phase 完成后自动收集：

```json
{
  "session_id": "20251021_143022",
  "project": "todo-app",
  "project_type": "web-app",
  "phase": 3,
  "duration_seconds": 1847,
  "agents_used": ["frontend-specialist", "test-engineer"],
  "errors": [],
  "warnings": ["shellcheck: SC2086"],
  "success": true,
  "timestamp": "2025-10-21T14:30:22Z"
}
```

**Trigger**: `.claude/hooks/post_phase.sh` (will be created in Milestone 2)

### Metrics Aggregation

每周自动汇总：

```json
{
  "project_type": "web-app",
  "phases": {
    "1": {"avg_duration_seconds": 1500, "success_rate": 0.95},
    "2": {"avg_duration_seconds": 7200, "success_rate": 0.92},
    "3": {"avg_duration_seconds": 1800, "success_rate": 0.98}
  },
  "common_errors": [
    {"error": "version mismatch", "count": 15, "last_seen": "2025-10-20T..."}
  ]
}
```

**Trigger**: Weekly cron job (Milestone 2)

### Success Patterns (Milestone 3)

手动或自动整理的最佳实践：

```json
{
  "pattern_name": "user_authentication",
  "recommended_agents": ["backend-architect", "security-auditor", "test-engineer"],
  "success_rate": 0.95,
  "avg_duration": {"phase1": 25, "phase2": 120, "phase3": 45},
  "common_pitfalls": ["忘记 session timeout", "密码强度不足"]
}
```

**Usage**: AI queries this during Phase 1 planning

## 🔒 Privacy & Security

### Data Anonymization

- `project_path` 字段是可选的，可以省略或匿名化
- 本地存储，不上传到云端
- 用户可以随时删除知识库数据

### Opt-Out

在项目的 `.claude/config.json` 中设置：

```json
{
  "learning": {
    "enabled": false
  }
}
```

## 🚀 Usage (For AI)

### Query Historical Data (Milestone 3)

```bash
# 查询成功模式
bash tools/query-knowledge.sh pattern user_authentication

# 查询常见错误
bash tools/query-knowledge.sh error web-app

# 查询平均时长
bash tools/query-knowledge.sh duration web-app
```

### Auto-Application in Phase 1

AI 在规划时自动：

1. 识别项目类型（如：user_authentication）
2. 查询知识库获取成功模式
3. 应用推荐的 Agent 组合
4. 提示常见陷阱
5. 使用历史时长估算

## 📈 Growth Timeline

### Milestone 1 (Week 1-2): Foundation
- ✅ Directory structure created
- ✅ Schema defined
- ⏳ No data collection yet

### Milestone 2 (Week 3-4): Data Collection
- 🔄 Automatic session logging
- 🔄 Weekly manual analysis
- 🔄 Knowledge base starts growing

### Milestone 3 (Week 5-8): Auto-Learning
- 🔄 AI uses historical data
- 🔄 Automatic pattern extraction
- 🔄 Self-improvement engine

## 🛠️ Maintenance

### Cleanup Old Data

```bash
# Sessions older than 6 months → archive/
find .claude/knowledge/sessions/ -name "*.json" -mtime +180 \
  -exec mv {} .claude/knowledge/archive/ \;
```

### Validate Data Format

```bash
# Validate all session files against schema
for file in .claude/knowledge/sessions/*.json; do
  ajv validate -s .claude/knowledge/schema.json -d "$file"
done
```

## 📖 References

- Schema: `.claude/knowledge/schema.json`
- Collection Hook: `.claude/hooks/post_phase.sh` (Milestone 2)
- Query Interface: `tools/query-knowledge.sh` (Milestone 3)
- Auto-Improver: `.claude/engine/auto_improver.sh` (Milestone 3)

---

*This knowledge base represents Claude Enhancer's memory - it gets smarter with every project you build.*
