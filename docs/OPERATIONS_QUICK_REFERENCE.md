# Claude Enhancer 5.3 - Operations Quick Reference

## Emergency Contacts

**P0 Incidents**: PagerDuty (on-call rotation)
**CTO**: cto@example.com
**Engineering Manager**: manager@example.com
**DevOps Team**: devops@example.com

## Quick Commands

### Health Check
```bash
./scripts/healthcheck.sh
```

### Immediate Rollback
```bash
./runbooks/scripts/rollback.sh --immediate
```

### Create Backup
```bash
./runbooks/scripts/backup.sh
```

### Collect Diagnostics
```bash
./runbooks/scripts/incident_triage.sh
```

### Check SLO Status
```bash
./scripts/check_slo_status.sh
```

## Incident Severity

| Level | Response | Resolution | Example |
|-------|----------|------------|---------|
| P0 | < 5 min | < 1 hour | Service down |
| P1 | < 15 min | < 4 hours | SLO violation |
| P2 | < 1 hour | < 24 hours | Minor bug |
| P3 | < 4 hours | < 7 days | Cosmetic issue |

## Documentation Index

### Deployment
- **DEPLOYMENT_GUIDE.md** - Full deployment procedures
- **PRODUCTION_CHECKLIST.md** - Pre-deployment checklist

### Operations
- **runbooks/startup.md** - System startup
- **runbooks/shutdown.md** - System shutdown
- **runbooks/backup.md** - Backup procedures
- **runbooks/monitoring.md** - Monitoring guide

### Incident Management
- **INCIDENT_RESPONSE.md** - Incident procedures
- **DISASTER_RECOVERY.md** - DR procedures
- **runbooks/troubleshooting.md** - Troubleshooting

### Maintenance
- **MAINTENANCE.md** - Maintenance schedule
- **runbooks/upgrade.md** - Upgrade procedures
- **runbooks/rollback.md** - Rollback procedures

### Governance
- **SLA_SLO.md** - Service levels
- **CHANGE_MANAGEMENT.md** - Change process
- **CAPACITY_PLANNING.md** - Capacity planning

## Key Metrics

### SLOs
- API Availability: 99.9%
- Auth Latency (p95): < 200ms
- Workflow Success: 98%
- Task Throughput: 20/sec

### Quality Scores
- Overall: 100/100
- BDD Scenarios: 65/65
- Performance Metrics: 90/90
- SLOs: 15/15
- CI Jobs: 9/9

## File Locations

```
/home/xx/dev/Claude Enhancer 5.0/
├── docs/                         # Documentation
│   ├── DEPLOYMENT_GUIDE.md
│   ├── INCIDENT_RESPONSE.md
│   ├── DISASTER_RECOVERY.md
│   └── runbooks/                 # Operational runbooks
│       ├── startup.md
│       ├── shutdown.md
│       └── ...
├── runbooks/scripts/             # Automation scripts
│   ├── startup.sh
│   ├── health_check.sh
│   └── ...
├── scripts/                      # Utility scripts
│   ├── healthcheck.sh
│   └── check_slo_status.sh
└── observability/               # Monitoring
    └── slo/slo.yml
```

## Automation Scripts

All scripts located in: `runbooks/scripts/`

- **startup.sh** - Start all services
- **shutdown.sh** - Stop all services
- **backup.sh** - Create backup
- **restore.sh** - Restore from backup
- **health_check.sh** - Run health checks
- **incident_triage.sh** - Collect diagnostics

## Escalation Path

```
L1: On-Call Engineer
 ↓ (15 min P0, 1hr P1)
L2: Engineering Manager
 ↓ (30 min P0, 2hr P1)
L3: CTO
 ↓ (critical only)
L4: CEO
```

## Rollback Decision Tree

```
Issue?
  ├─ P0 (Critical) → Immediate rollback
  ├─ P1 (High) → Evaluate (< 15 min)
  ├─ P2 (Medium) → Fix forward
  └─ P3 (Low) → Next release
```

---
**Quick Reference Guide v1.0**
**Last Updated**: 2025-10-10
