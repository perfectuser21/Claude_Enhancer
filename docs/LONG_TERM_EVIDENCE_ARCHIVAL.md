# 📦 Long-Term Evidence Archival Strategy

**Purpose**: Extend evidence retention beyond GitHub Actions' 90-day limit for compliance, auditing, and historical analysis.

---

## 🎯 Overview

While GitHub Actions provides 90-day artifact retention, certain scenarios require longer retention:

- **Compliance**: Regulatory requirements (e.g., SOX, HIPAA) often mandate 7+ years
- **Auditing**: Security audits may request historical evidence
- **Forensics**: Incident investigation requiring historical data
- **Trend Analysis**: Long-term quality and performance trends

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Evidence Generation Layer                       │
│  • bp_verify.sh (3-layer verification)                      │
│  • CI/CD workflows (test results, coverage)                 │
│  • Quality gates (metrics, scores)                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│           Short-Term Storage (90 days)                       │
│  • GitHub Actions Artifacts                                 │
│  • /tmp/*.log files                                         │
│  • .workflow/logs/* files                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓ (Automated sync)
┌─────────────────────────────────────────────────────────────┐
│          Long-Term Archival (7+ years)                       │
│  • AWS S3 / Backblaze B2 / Google Cloud Storage            │
│  • Self-hosted object storage (MinIO)                       │
│  • Network Attached Storage (NAS)                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Implementation Options

### Option 1: AWS S3 (Recommended for Cloud)

**Pros**:
- ✅ Highly reliable (99.999999999% durability)
- ✅ Lifecycle policies for automatic tiering
- ✅ Low cost with Glacier tiers
- ✅ Integrated with GitHub Actions

**Setup**:

1. **Create S3 Bucket**:
```bash
aws s3 mb s3://claude-enhancer-evidence-archive
```

2. **Configure Lifecycle Policy**:
```json
{
  "Rules": [
    {
      "Id": "TierToGlacier",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        },
        {
          "Days": 365,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ]
    }
  ]
}
```

3. **Add to bp-guard.yml**:
```yaml
- name: Archive evidence to S3
  if: always()
  run: |
    # Install AWS CLI
    pip install awscli

    # Upload evidence with metadata
    RUN_ID="${{ github.run_id }}"
    DATE=$(date +%Y-%m-%d)

    aws s3 cp /tmp/commit.log \
      "s3://claude-enhancer-evidence-archive/${DATE}/run-${RUN_ID}/" \
      --metadata "workflow=bp-guard,branch=${{ github.ref }},commit=${{ github.sha }}"

    aws s3 cp /tmp/push_main.log \
      "s3://claude-enhancer-evidence-archive/${DATE}/run-${RUN_ID}/"

    aws s3 cp /tmp/push_main_nov.log \
      "s3://claude-enhancer-evidence-archive/${DATE}/run-${RUN_ID}/"

    aws s3 cp /tmp/merge_attempt.log \
      "s3://claude-enhancer-evidence-archive/${DATE}/run-${RUN_ID}/"

    # Upload BP snapshot
    aws s3 cp .workflow/backups/bp_snapshot_latest.json \
      "s3://claude-enhancer-evidence-archive/${DATE}/bp-snapshots/"
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    AWS_DEFAULT_REGION: us-east-1
```

**Cost Estimation**:
- Standard storage: $0.023/GB/month
- Glacier storage: $0.004/GB/month
- Deep Archive: $0.00099/GB/month
- Typical evidence: ~50MB/week = ~2.5GB/year
- **Annual cost**: $0.69 (Standard) or $0.12 (Glacier)

---

### Option 2: Backblaze B2 (Cost-Effective)

**Pros**:
- ✅ 1/4 cost of S3
- ✅ No egress fees (first 3x storage is free)
- ✅ S3-compatible API

**Setup**:
```bash
# Install B2 CLI
pip install b2

# Authenticate
b2 authorize-account <key_id> <application_key>

# Create bucket
b2 create-bucket claude-enhancer-evidence allPrivate

# Upload script
#!/usr/bin/env bash
DATE=$(date +%Y-%m-%d)
RUN_ID="$1"

b2 upload-file --noProgress \
  claude-enhancer-evidence \
  /tmp/commit.log \
  "evidence/${DATE}/run-${RUN_ID}/commit.log"

# ... repeat for other logs
```

**Cost Estimation**:
- Storage: $0.005/GB/month
- **Annual cost**: $0.15 for 2.5GB

---

### Option 3: Self-Hosted (MinIO)

**Pros**:
- ✅ No recurring cloud costs
- ✅ Complete data control
- ✅ S3-compatible API

**Setup**:
```bash
# Run MinIO server
docker run -p 9000:9000 -p 9001:9001 \
  -v /mnt/data:/data \
  -e "MINIO_ROOT_USER=admin" \
  -e "MINIO_ROOT_PASSWORD=password" \
  minio/minio server /data --console-address ":9001"

# Create bucket
mc alias set myminio http://localhost:9000 admin password
mc mb myminio/claude-enhancer-evidence

# Upload script (same as S3)
```

---

### Option 4: GitHub Release Assets (Simple)

**Pros**:
- ✅ Free (within GitHub)
- ✅ Integrated with releases
- ✅ No additional infrastructure

**Cons**:
- ❌ No lifecycle management
- ❌ Manual cleanup required
- ❌ Limited to release cycles

**Setup**:
```bash
# Package evidence for release
VERSION=$(cat VERSION)
zip -r "evidence_v${VERSION}.zip" \
  /tmp/*.log \
  .workflow/backups/*.json \
  coverage/ \
  .workflow/_reports/

# Upload to release
gh release upload "v${VERSION}" "evidence_v${VERSION}.zip" \
  --clobber
```

---

## 📊 Comparison Matrix

| Feature | S3 | Backblaze B2 | MinIO | GitHub |
|---------|-----|--------------|-------|--------|
| **Cost** | $$$ | $ | Hardware only | Free |
| **Durability** | 11 nines | 11 nines | Depends on setup | High |
| **Lifecycle** | ✅ Automatic | ✅ Automatic | ✅ Manual | ❌ None |
| **Egress Cost** | $$$ | $ (free 3x) | None | None |
| **Setup Complexity** | Low | Low | Medium | Very Low |
| **Compliance** | ✅ Many certs | ✅ Some certs | Your setup | Limited |

---

## 🔒 Security Best Practices

### 1. Encryption at Rest
```bash
# S3 example
aws s3api put-bucket-encryption \
  --bucket claude-enhancer-evidence-archive \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

### 2. Access Control
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_ID:user/ci-uploader"
      },
      "Action": ["s3:PutObject", "s3:PutObjectAcl"],
      "Resource": "arn:aws:s3:::claude-enhancer-evidence-archive/*"
    }
  ]
}
```

### 3. Immutability (Compliance Lock)
```bash
# Enable Object Lock (prevents deletion)
aws s3api put-object-lock-configuration \
  --bucket claude-enhancer-evidence-archive \
  --object-lock-configuration '{
    "ObjectLockEnabled": "Enabled",
    "Rule": {
      "DefaultRetention": {
        "Mode": "COMPLIANCE",
        "Years": 7
      }
    }
  }'
```

---

## 📝 Evidence Manifest Format

Each archival package includes a manifest:

```json
{
  "version": "1.0",
  "generated_at": "2025-10-10T23:30:00Z",
  "repository": "perfectuser21/Claude_Enhancer",
  "workflow_run_id": "12345678",
  "commit_sha": "abc123def456",
  "branch": "main",
  "evidence_files": [
    {
      "name": "commit.log",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "size": 1024,
      "timestamp": "2025-10-10T23:29:45Z"
    },
    {
      "name": "bp_snapshot.json",
      "sha256": "d4e5f67890abc123def456789012345678901234567890abcdef1234567890ab",
      "size": 2048,
      "timestamp": "2025-10-10T23:29:50Z"
    }
  ],
  "verification": {
    "pass_rate": "100%",
    "checks_passed": 9,
    "checks_total": 9
  }
}
```

---

## 🔄 Retention Schedule

| Evidence Type | Short-Term | Mid-Term | Long-Term | Archival |
|---------------|-----------|----------|-----------|----------|
| **BP Verification** | 90 days (Actions) | 1 year (S3) | 3 years (Glacier) | 7 years (Deep Archive) |
| **Quality Metrics** | 90 days | 1 year | 3 years | 7 years |
| **Coverage Reports** | 90 days | 6 months | 2 years | 5 years |
| **SBOM** | Permanent | Permanent | Permanent | Permanent |
| **Release Artifacts** | Permanent | Permanent | Permanent | Permanent |

---

## 🚀 Automated Sync Script

Create `.github/workflows/evidence-archival.yml`:

```yaml
name: Evidence Long-Term Archival

on:
  workflow_run:
    workflows: ["Branch-Protection Guard"]
    types: [completed]

jobs:
  archive:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' || github.event.workflow_run.conclusion == 'failure' }}

    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          name: bp-probe-artifacts-${{ github.event.workflow_run.run_number }}
          path: ./evidence

      - name: Generate manifest
        run: |
          cat > evidence/manifest.json <<EOF
          {
            "version": "1.0",
            "generated_at": "$(date -Iseconds)",
            "repository": "${{ github.repository }}",
            "workflow_run_id": "${{ github.event.workflow_run.id }}",
            "commit_sha": "${{ github.sha }}",
            "branch": "${{ github.ref }}",
            "evidence_files": []
          }
          EOF

          # Add file checksums
          cd evidence
          for file in *.log *.json; do
            if [ -f "$file" ]; then
              sha256sum "$file"
            fi
          done > checksums.txt

      - name: Upload to S3
        if: env.AWS_ACCESS_KEY_ID != ''
        run: |
          pip install awscli
          DATE=$(date +%Y-%m-%d)
          RUN_ID="${{ github.event.workflow_run.id }}"

          aws s3 sync ./evidence \
            "s3://claude-enhancer-evidence-archive/${DATE}/run-${RUN_ID}/" \
            --metadata "repo=${{ github.repository }},commit=${{ github.sha }}"
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: us-east-1

      - name: Notification
        if: always()
        run: |
          if [ -n "$AWS_ACCESS_KEY_ID" ]; then
            echo "✅ Evidence archived to S3 successfully"
          else
            echo "⚠️  S3 credentials not configured, skipping archival"
          fi
```

---

## 📈 Monitoring and Alerts

### CloudWatch Alarm (S3)

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "evidence-archival-failures" \
  --alarm-description "Alert when evidence archival fails" \
  --metric-name PutRequests \
  --namespace AWS/S3 \
  --statistic Sum \
  --period 3600 \
  --threshold 0 \
  --comparison-operator LessThanThreshold \
  --dimensions Name=BucketName,Value=claude-enhancer-evidence-archive
```

### Storage Growth Tracking

```bash
# Get current storage size
aws s3 ls --summarize --human-readable --recursive \
  s3://claude-enhancer-evidence-archive/

# Estimate future storage
DAILY_SIZE=10  # MB
RETENTION_DAYS=2555  # 7 years
TOTAL_GB=$(echo "scale=2; $DAILY_SIZE * $RETENTION_DAYS / 1024" | bc)
echo "Estimated 7-year storage: ${TOTAL_GB} GB"
```

---

## ✅ Implementation Checklist

- [ ] Choose archival solution (S3 / B2 / MinIO / GitHub)
- [ ] Create bucket / storage location
- [ ] Configure encryption at rest
- [ ] Set up IAM / access controls
- [ ] Implement lifecycle policies (if cloud)
- [ ] Add archival step to bp-guard.yml
- [ ] Create evidence manifest generator
- [ ] Set up monitoring / alerts
- [ ] Document retrieval procedures
- [ ] Test archival and restoration
- [ ] Schedule periodic audits

---

## 🔍 Evidence Retrieval

### From S3:
```bash
# List available evidence
aws s3 ls s3://claude-enhancer-evidence-archive/ --recursive

# Download specific run
DATE="2025-10-10"
RUN_ID="12345678"
aws s3 sync \
  "s3://claude-enhancer-evidence-archive/${DATE}/run-${RUN_ID}/" \
  ./retrieved-evidence/

# Verify checksums
cd retrieved-evidence
sha256sum -c checksums.txt
```

### From Glacier:
```bash
# Initiate restore (takes 3-5 hours for Glacier, 12 hours for Deep Archive)
aws s3api restore-object \
  --bucket claude-enhancer-evidence-archive \
  --key "2025-10-10/run-12345678/commit.log" \
  --restore-request Days=7

# Download after restore completes
aws s3 cp "s3://claude-enhancer-evidence-archive/2025-10-10/run-12345678/" \
  ./retrieved-evidence/ --recursive
```

---

## 💡 Recommendations

**For Solo Developers / Small Teams**:
- Use **GitHub Release Assets** or **Backblaze B2**
- Minimize costs while maintaining compliance

**For Organizations**:
- Use **AWS S3** with Glacier tiering
- Implement compliance locks for regulatory requirements

**For Air-Gapped Environments**:
- Use **Self-hosted MinIO** or **NAS**
- Full data sovereignty and control

---

## 📚 Further Reading

- [AWS S3 Lifecycle Management](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [Backblaze B2 Pricing](https://www.backblaze.com/b2/cloud-storage-pricing.html)
- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)
- [GitHub Actions Artifacts](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts)

---

*This document provides a comprehensive strategy for long-term evidence archival, ensuring compliance, auditability, and historical analysis capabilities for Claude Enhancer's protection system.*
