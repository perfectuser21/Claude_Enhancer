# Memory Compression Quick Reference

## Daily Commands

```bash
# Check status
python3 scripts/memory-compressor.py --stats

# Compress if needed
python3 scripts/memory-compressor.py --force
```

## Decision Importance Levels

| Level | When to Use | Retention |
|-------|------------|-----------|
| `critical` | Core architecture, do_not_revert | Forever |
| `warning` | Major changes, 5+ files | 90 days |
| `info` | Experiments, temp fixes | 30 days |

## Add New Decision

```json
{
  "recent_decisions": {
    "2025-10-14_new_feature": {
      "date": "2025-10-14",
      "decision": "Add X feature",
      "rationale": "Because Y",
      "importance": "critical",
      "do_not_revert": true
    }
  }
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Size > 5KB | Run compressor |
| Missing archives | Check `.claude/memory-archive/` |
| Can't find old decisions | Check `decision-index.json` |

## Monitoring

```bash
# Watch token growth
watch -n 60 'python3 scripts/memory-compressor.py --stats | grep tokens'

# Auto-compress on commit (add to .git/hooks/post-commit)
python3 scripts/memory-compressor.py --force >/dev/null 2>&1 || true
```

## Architecture

```
memory-cache.json (Hot)  ← 30 days, <5KB
    ↓ (auto-compress)
memory-archive/ (Cold)   ← Historical, unlimited
    ↓ (quick-lookup)
decision-index.json      ← Monthly summaries
```

## Success Metrics

- ✅ memory-cache.json < 5KB
- ✅ < 1200 tokens per session
- ✅ Archives growing monthly
- ✅ No lost decisions
