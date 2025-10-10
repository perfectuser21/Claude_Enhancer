# Claude Enhancer 5.3 Disaster Recovery Plan

## Executive Summary

This document outlines the disaster recovery (DR) procedures for Claude Enhancer 5.3. It defines recovery objectives, backup strategies, and step-by-step recovery procedures for various disaster scenarios.

## Recovery Objectives

### RTO (Recovery Time Objective)
**Target**: < 1 hour

Maximum acceptable time to restore service after a disaster.

### RPO (Recovery Point Objective)
**Target**: < 24 hours

Maximum acceptable data loss measured in time.

### Service Level Targets
- **Critical Systems**: RTO < 15 minutes, RPO < 1 hour
- **Standard Systems**: RTO < 1 hour, RPO < 24 hours
- **Non-Critical Systems**: RTO < 4 hours, RPO < 48 hours

## Disaster Scenarios

### Scenario 1: Complete System Failure

**Impact**: All services unavailable
**RTO**: 30 minutes
**RPO**: 24 hours

**Recovery Procedure**:
```bash
# 1. Verify backup availability
ls -lh backups/*.tar.gz | tail -5

# 2. Restore from latest backup
./runbooks/scripts/restore.sh backups/latest.tar.gz

# 3. Reinstall dependencies
npm ci

# 4. Reinstall Git hooks
./.claude/install.sh

# 5. Start services
./runbooks/scripts/startup.sh

# 6. Verify recovery
./scripts/healthcheck.sh
```

### Scenario 2: Data Corruption

**Impact**: Configuration or state files corrupted
**RTO**: 15 minutes
**RPO**: 24 hours

**Recovery Procedure**:
```bash
# 1. Stop services
./runbooks/scripts/shutdown.sh

# 2. Identify corrupted files
git status
git diff

# 3. Restore from Git
git checkout HEAD -- .claude/settings.json
git checkout HEAD -- .workflow/ACTIVE

# 4. Or restore from backup
./runbooks/scripts/restore.sh backups/latest.tar.gz

# 5. Restart services
./runbooks/scripts/startup.sh
```

### Scenario 3: Git Repository Corruption

**Impact**: Git history or objects corrupted
**RTO**: 1 hour
**RPO**: 0 (recoverable from remote)

**Recovery Procedure**:
```bash
# 1. Backup current state (even if corrupted)
tar -czf corrupted_state_$(date +%Y%m%d).tar.gz .git

# 2. Remove corrupted repository
rm -rf .git

# 3. Re-clone from remote
git clone <repository-url> temp_clone
mv temp_clone/.git .
rm -rf temp_clone

# 4. Verify repository integrity
git fsck --full

# 5. Reinstall hooks
./.claude/install.sh
```

### Scenario 4: Configuration Loss

**Impact**: Settings and configuration files lost
**RTO**: 10 minutes
**RPO**: 24 hours

**Recovery Procedure**:
```bash
# 1. Restore from latest backup
./runbooks/scripts/restore.sh backups/latest.tar.gz

# 2. Or create from template
cp .claude/settings.example.json .claude/settings.json

# 3. Verify configuration
cat .claude/settings.json | jq .

# 4. Test configuration
./scripts/healthcheck.sh
```

### Scenario 5: Dependency Corruption

**Impact**: node_modules corrupted or missing
**RTO**: 20 minutes
**RPO**: 0 (recoverable from npm)

**Recovery Procedure**:
```bash
# 1. Remove corrupted dependencies
rm -rf node_modules
rm -f package-lock.json

# 2. Clear npm cache
npm cache clean --force

# 3. Reinstall dependencies
npm ci

# 4. Verify installation
npm ls --depth=0

# 5. Test functionality
npm run bdd
```

## Backup Strategy

### Automated Backups

**Daily Backups**:
```bash
# Cron job (runs at 2 AM daily)
0 2 * * * /home/xx/dev/Claude\ Enhancer\ 5.0/runbooks/scripts/backup.sh

# Retention: 30 days
# Location: backups/daily_YYYYMMDD.tar.gz
```

**Weekly Backups**:
```bash
# Cron job (runs Sunday at 3 AM)
0 3 * * 0 /home/xx/dev/Claude\ Enhancer\ 5.0/runbooks/scripts/backup.sh && \
  cp backups/$(date +%Y%m%d_%H%M%S).tar.gz backups/weekly_$(date +%Y%W).tar.gz

# Retention: 12 weeks
# Location: backups/weekly_YYYYWW.tar.gz
```

**Monthly Backups**:
```bash
# Cron job (runs 1st of month at 4 AM)
0 4 1 * * /home/xx/dev/Claude\ Enhancer\ 5.0/runbooks/scripts/backup.sh && \
  cp backups/$(date +%Y%m%d_%H%M%S).tar.gz backups/monthly_$(date +%Y%m).tar.gz

# Retention: 12 months
# Location: backups/monthly_YYYYMM.tar.gz
```

### Manual Backups

**Before Major Changes**:
```bash
# Before deployment
./runbooks/scripts/backup.sh

# Before configuration changes
cp .claude/settings.json .claude/settings.json.$(date +%Y%m%d_%H%M%S).bak

# Before Git operations
git stash
git branch backup_$(date +%Y%m%d_%H%M%S)
```

### Backup Verification

**Weekly Verification**:
```bash
#!/bin/bash
# Test latest backup
LATEST_BACKUP=$(ls -t backups/*.tar.gz | head -1)

# Extract to temp directory
mkdir -p /tmp/backup_test
tar -xzf "$LATEST_BACKUP" -C /tmp/backup_test

# Verify critical files
test -f /tmp/backup_test/*/. claude/settings.json && echo "✓ Config OK"
test -f /tmp/backup_test/*/.workflow/ACTIVE && echo "✓ Workflow OK"

# Cleanup
rm -rf /tmp/backup_test

echo "✓ Backup verification complete"
```

## Recovery Procedures

### Full System Recovery

**Step 1: Prepare Recovery Environment** (5 minutes)
```bash
# 1. Provision new server/system
# 2. Install prerequisites
sudo apt update
sudo apt install -y git nodejs npm

# 3. Verify prerequisites
git --version  # >= 2.30.0
node --version  # >= 18.0.0
npm --version  # >= 9.0.0
```

**Step 2: Restore from Backup** (10 minutes)
```bash
# 1. Download backup
# ... transfer backup file to new system ...

# 2. Extract backup
mkdir -p "/home/xx/dev/Claude Enhancer 5.0"
cd "/home/xx/dev/Claude Enhancer 5.0"
tar -xzf /path/to/backup.tar.gz

# 3. Restore from extracted backup
BACKUP_DIR=$(tar -tzf /path/to/backup.tar.gz | head -1 | cut -d'/' -f1)
cp -r "$BACKUP_DIR"/.claude .
cp -r "$BACKUP_DIR"/.workflow .
cp -r "$BACKUP_DIR"/.phase .
cp "$BACKUP_DIR"/.env . 2>/dev/null || true
```

**Step 3: Restore Repository** (10 minutes)
```bash
# 1. Clone repository
git clone <repository-url> .

# 2. Restore configuration
# ... already restored from backup ...

# 3. Install dependencies
npm ci

# 4. Install Git hooks
./.claude/install.sh
```

**Step 4: Verify and Start** (5 minutes)
```bash
# 1. Run health check
./scripts/healthcheck.sh

# 2. Start services
./runbooks/scripts/startup.sh

# 3. Verify functionality
npm run bdd

# 4. Check SLO compliance
cat observability/slo/slo.yml | head -20
```

### Partial Recovery

**Recover Configuration Only**:
```bash
# Extract just configuration
tar -xzf backup.tar.gz "*/..claude/" -C /tmp
cp -r /tmp/*/..claude .
```

**Recover Workflow State Only**:
```bash
# Extract workflow state
tar -xzf backup.tar.gz "*/.workflow/" "*/.phase/" -C /tmp
cp -r /tmp/*/.workflow .
cp -r /tmp/*/.phase .
```

## Testing Plan

### Monthly DR Drills

**Drill 1: Backup Restore Test**
```bash
# Objective: Verify backup can be restored
# Duration: 30 minutes
# Frequency: Monthly

# 1. Select random backup
# 2. Restore to test environment
# 3. Verify all services start
# 4. Run health checks
# 5. Document results
```

**Drill 2: Configuration Recovery**
```bash
# Objective: Recover from configuration loss
# Duration: 15 minutes
# Frequency: Monthly

# 1. Delete .claude/settings.json
# 2. Restore from backup
# 3. Verify system operation
# 4. Document time taken
```

### Quarterly Full DR Test

**Objective**: Complete disaster recovery from bare metal
**Duration**: 2 hours
**Frequency**: Quarterly

**Test Procedure**:
1. Provision clean test environment
2. Install prerequisites
3. Restore from backup
4. Clone repository
5. Verify full functionality
6. Measure RTO/RPO
7. Document lessons learned
8. Update procedures

### Annual DR Audit

**Objective**: Comprehensive review of DR capabilities
**Duration**: 1 day
**Frequency**: Annually

**Audit Checklist**:
- [ ] All backup procedures tested
- [ ] All recovery procedures tested
- [ ] RTO/RPO targets verified
- [ ] Documentation updated
- [ ] Team training current
- [ ] Contact information current
- [ ] Backup integrity verified
- [ ] Off-site backups tested

## Backup Storage

### Local Storage
- **Location**: `/home/xx/dev/Claude Enhancer 5.0/backups/`
- **Retention**: 30 days (daily), 12 weeks (weekly), 12 months (monthly)
- **Cleanup**: Automated via cron

### Off-Site Storage (Recommended)
```bash
# Sync to remote storage daily
rsync -avz backups/ user@remote-server:/backups/claude-enhancer/

# Or use cloud storage
aws s3 sync backups/ s3://claude-enhancer-backups/
```

### Backup Encryption (Production)
```bash
# Encrypt sensitive backups
tar -czf - backup_dir/ | gpg --encrypt --recipient admin@example.com > backup.tar.gz.gpg

# Decrypt when needed
gpg --decrypt backup.tar.gz.gpg | tar -xzf -
```

## Contact Information

### Emergency Contacts
- **Primary On-Call**: PagerDuty rotation
- **Backup Contact**: Engineering Manager
- **CTO**: cto@example.com
- **Infrastructure Team**: infra@example.com

### External Vendors
- **Cloud Provider Support**: (if using cloud)
- **Hardware Vendor**: (if applicable)
- **Backup Service**: (if using external backup)

## Recovery Checklist

```
Pre-Recovery:
  ☐ Disaster declared
  ☐ Stakeholders notified
  ☐ Recovery team assembled
  ☐ Backup identified
  ☐ Recovery environment prepared

Recovery:
  ☐ Backup restored
  ☐ Repository cloned
  ☐ Dependencies installed
  ☐ Configuration verified
  ☐ Services started

Post-Recovery:
  ☐ Health checks pass
  ☐ Functionality verified
  ☐ SLOs met
  ☐ Stakeholders notified
  ☐ Post-mortem scheduled
```

## Success Metrics

- **RTO Achieved**: < 1 hour
- **RPO Achieved**: < 24 hours
- **Data Loss**: Minimal (< 1 day)
- **Service Restoration**: 100%
- **SLO Compliance**: Maintained after recovery

---

**Document Version**: 1.0
**Last Updated**: 2025-10-10
**Next Review**: 2026-01-10
**Owner**: DevOps/SRE Team
**Classification**: Confidential
