# Claude Enhancer {{VERSION}} - AI Programming Workflow System

> **Core Identity**: Personal productivity tool for AI-assisted development
> Last Updated: {{LAST_UPDATED}}

## 🎯 System Identity

**What Claude Enhancer Is**:
- ✅ Personal workflow system for individual developers
- ✅ Quality assurance framework for AI programming
- ✅ Structured 8-phase development process
- ✅ Multi-agent orchestration platform

**What It Is NOT**:
- ❌ Enterprise product (no team management, no licensing)
- ❌ Production deployment tool (local development only)
- ❌ SaaS service (self-hosted only)

---

## 🚨 Rule 0: Branch Management (Phase -1)
**Priority: Highest | Enforced before P0-P7**

### Core Principle
```
New Task = New Branch (No Exceptions)
```

### Workflow
```
User Request → Analyze Task → Check Branch → Create if Needed → Execute P0-P7
```

### Smart Decision Logic

**🟢 Continue Current Branch** (no prompt):
- Task matches branch theme (e.g., "add login timeout" on `feature/user-auth`)
- User says "continue"/"improve"/"fix"
- Same domain as current work

**🟡 Quick Clarification** (brief):
- Uncertain relationship
- Could be related or separate
- Example: "Email verification - part of auth or new notification system?"

**🔴 Suggest New Branch** (with reason):
- Completely different domain
- Current branch completed/merged
- User says "new feature"
- Currently on main/master

### Multi-Terminal Support
```
Terminal 1: feature/auth      ← Claude Instance A
Terminal 2: feature/payment   ← Claude Instance B
Terminal 3: feature/monitoring ← Claude Instance C

Each isolated, independent P0-P7 workflow
```

**Enforcement**: `.claude/hooks/branch_helper.sh` + Git hooks

---

## 🚨 Rule 1: Document Management
**Priority: Highest | Prevents document sprawl**

### Core Principle
```
7 Core Docs = Permanent
.temp/ = Auto-delete (7 days)
AI internal ≠ User documentation
```

### Whitelist (Root Directory)
```
ALLOWED (can update):
├─ README.md          ✅ Update only
├─ CLAUDE.md         ✅ Update only
├─ INSTALLATION.md   ✅ Update only
├─ ARCHITECTURE.md   ✅ Update only
├─ CONTRIBUTING.md   ✅ Update only
├─ CHANGELOG.md      ✅ Append only
└─ LICENSE           ✅ Rarely change

FORBIDDEN (cannot create):
❌ *_REPORT.md
❌ *_ANALYSIS.md
❌ *_SUMMARY.md
❌ README2.md, CLAUDE_NEW.md, etc.
```

### Temporary Analysis
```bash
✅ Write: .temp/analysis/code_review_20251013.md  # AI internal
✅ Write: .temp/reports/test_results.json         # CI artifacts
❌ Write: CODE_REVIEW_REPORT.md                   # Root pollution
```

### Information Delivery Methods

**Method A**: Direct conversation (simple) ✅ Preferred
```
"I found 3 bugs: 1) Shell syntax error in line 42..."
```

**Method B**: Temporary file (detailed) ✅ Optional
```
.temp/analysis/audit_20251013.md  # AI reads, user ignores
```

**Method C**: Update core docs (permanent) ⚠️ Rare
```
Only when user explicitly requests: "Update README with new feature"
```

### Enforcement
- **Layer 1**: `.claude/hooks/pre_write_document.sh` - Block before write
- **Layer 2**: `scripts/cleanup_documents.sh` - Post-commit cleanup
- **Layer 3**: CI/CD - Daily validation (≤7 docs)

---

## 🚀 8-Phase Workflow (P0-P7)

{{FEATURE_8PHASE}}

| Phase | Name | Purpose | Output |
|-------|------|---------|--------|
| P0 | Discovery | Technical spike | Feasibility findings |
| P1 | Plan | Requirements | PLAN.md |
| P2 | Skeleton | Architecture | Directory structure |
| P3 | Implementation | Coding | Working code |
| P4 | Testing | Validation | TEST-REPORT.md |
| P5 | Review | Audit | REVIEW.md |
| P6 | Release | Documentation | Release artifacts |
| P7 | Monitor | Observability | SLO dashboards |

### Agent Strategy (4-6-8 Principle)
- **4 agents**: Simple tasks (bug fix, doc update)
- **6 agents**: Standard tasks (new feature, refactor)
- **8 agents**: Complex tasks (architecture, major feature)

---

## 🛡️ Quality Assurance Layers

{{FEATURE_QUALITY}}

### Layer 1: Contract-Driven
{{FEATURE_BDD}}
- **BDD Scenarios**: 65 executable acceptance tests
{{FEATURE_OPENAPI}}
- **OpenAPI**: API contract definitions
{{FEATURE_PERF}}
- **Performance Budgets**: 30 tracked metrics
{{FEATURE_SLO}}
- **SLO Monitoring**: 11 service level objectives

### Layer 2: Workflow Framework
- 8 standardized phases (P0-P7)

### Layer 3: Claude Hooks (Guidance)
- `branch_helper.sh` - Branch management
- `smart_agent_selector.sh` - Agent selection
- `quality_gate.sh` - Quality checks

### Layer 4: Git Hooks (Hard Enforcement)
- `pre-commit` - Syntax + tests + coverage
- `commit-msg` - Message format
- `pre-push` - Full validation

---

## 📁 Project Structure

```
.claude/
├── hooks/               # AI guidance hooks
├── core/               # Core modules
└── install.sh         # One-click setup

.workflow/
├── modules/           # 11 bash modules (~12.5k lines)
├── cli/              # 7 CLI commands
└── executor.log      # Operation logs

.phase/
├── current           # Active phase (P0-P7)
└── history/         # Phase transitions

{{FEATURE_BDD}}
acceptance/
├── features/        # 65 BDD scenarios
└── steps/          # Step definitions
{{/FEATURE_BDD}}

{{FEATURE_OPENAPI}}
api/
├── openapi.yaml    # API contracts
└── schemas/        # Data schemas
{{/FEATURE_OPENAPI}}

{{FEATURE_PERF}}
metrics/
└── perf_budget.yml # 30 performance budgets
{{/FEATURE_PERF}}

{{FEATURE_SLO}}
observability/
└── slo/slo.yml    # 11 SLO definitions
{{/FEATURE_SLO}}

.git/hooks/         # Quality enforcement
├── pre-commit
├── commit-msg
└── pre-push
```

---

## 🎮 Quick Start

### Installation (2 minutes)
```bash
# 1. Copy to your project
cd your-project
cp -r /path/to/claude-enhancer/.claude ./

# 2. Install hooks
bash .claude/install.sh

# 3. Verify
{{FEATURE_METRICS}}
python3 scripts/auto_metrics.py --check-only
{{/FEATURE_METRICS}}
bash scripts/cleanup_documents.sh
```

### First Workflow (10 minutes)
```bash
# 1. Create branch (auto if on main)
git checkout -b feature/my-feature

# 2. Start P1 Planning
echo "P1" > .phase/current
# AI reads requirements → generates PLAN.md

# 3. P2 Skeleton
echo "P2" > .phase/current
# AI creates directory structure

# 4. P3 Implementation (6 agents)
echo "P3" > .phase/current
# AI deploys: backend-architect, security-auditor, test-engineer,
#             api-designer, database-specialist, cleanup-specialist

# 5. P4 Testing
echo "P4" > .phase/current
npm test  # 312+ tests

# 6. P5 Review
echo "P5" > .phase/current
# AI generates REVIEW.md

# 7. Commit (hooks validate)
git add .
git commit -m "feat: implement my feature"

# 8. P6 Release
echo "P6" > .phase/current
# AI updates docs, creates tag
```

---

## 📊 Quality Metrics

{{FEATURE_METRICS}}

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Quality Score | 100 | 100 | ✅ |
| BDD Scenarios | ≥25 | 65 | ✅ |
| Performance Budgets | ≥30 | 30 | ✅ |
| SLO Definitions | ≥10 | 11 | ✅ |
| Test Cases | ≥250 | 312+ | ✅ |
| Code Coverage | ≥80% | 80%+ | ✅ |
| Security Score | ≥80 | 85/100 | ✅ |

{{/FEATURE_METRICS}}

---

## 🔒 Security

**Current Score**: 85/100 (⚠️ 3 P1 vulnerabilities, fix in v{{NEXT_VERSION}})

See [SECURITY_REVIEW.md](docs/SECURITY_REVIEW.md) for complete audit.

---

## 📚 Documentation

**Core Docs** (7 files only):
- [README.md](README.md) - Project overview
- [INSTALLATION.md](INSTALLATION.md) - Setup guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical design
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution workflow
- [CLAUDE.md](CLAUDE.md) - This file
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [LICENSE](LICENSE) - MIT License

**Guides**:
- [8-Phase Workflow](.claude/WORKFLOW.md)
- [Agent Strategy](.claude/AGENT_STRATEGY.md)
- [Troubleshooting](docs/TROUBLESHOOTING_GUIDE.md)

---

## 💡 Core Principles

### Max 20X Mindset
- **Quality First**: 100/100 perfect standards
- **Full Coverage**: P0-P7 complete lifecycle
- **Production Ready**: Not a toy, a tool

### AI-Human Collaboration
- **Human**: Vision, decisions, approval
- **AI**: Implementation, testing, documentation
- **System**: Quality gates, validation, safety

### Iterative Excellence
- Start simple (4 agents)
- Scale smart (6-8 agents)
- Validate always (4-layer QA)

---

## 🎖️ Certification

```
╔═══════════════════════════════════════╗
║   Claude Enhancer {{VERSION}}        ║
║   Quality Score: 100/100             ║
║   Production Ready: ✅                ║
╚═══════════════════════════════════════╝
```

---

**Claude Enhancer {{VERSION}}** - AI Programming Workflow System
*Your Personal Quality Assurance Framework*

Last Updated: {{LAST_UPDATED}} | Version: {{VERSION}}
