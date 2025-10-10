# AI Operation Contract / AI操作契约

## 📋 Contract Version / 契约版本
- **Version**: 1.0.0
- **Last Updated**: 2025-10-09
- **Scope**: Claude Enhancer 5.3+ AI Agents
- **Enforcement**: Pre-commit hooks + Claude Hooks

---

## 🎯 Contract Purpose / 契约目的

This contract defines the **mandatory preparation sequence** that ALL AI agents (including Claude Code and specialized agents) MUST follow before performing ANY file modifications in Claude Enhancer projects.

本契约定义了**强制准备序列**，所有AI代理（包括Claude Code和专业代理）在Claude Enhancer项目中执行任何文件修改之前**必须**遵循。

### Core Problems Solved / 解决的核心问题

1. **FM-3**: AI operates in uninitialized directory / AI在未初始化目录操作
2. **Workflow bypass**: AI starts coding without entering workflow / AI未进入工作流就开始编码
3. **Branch protection**: AI modifies files directly on main / AI直接在main分支修改文件

---

## 🔒 MANDATORY Preparation Sequence / 强制准备序列

### ⚠️ RULE: 3-Step Sequence BEFORE ANY File Modification

```
┌─────────────────────────────────────────────────────────┐
│  BEFORE you touch ANY file, you MUST complete:         │
│                                                          │
│  Step 1: Verify Git Repository Status                  │
│  Step 2: Ensure Proper Branch (not main/master)        │
│  Step 3: Enter Claude Enhancer Workflow (P0-P7)        │
│                                                          │
│  ❌ NO file modifications allowed before these steps!   │
└─────────────────────────────────────────────────────────┘
```

---

## 📖 Detailed Steps / 详细步骤

### Step 1: Verify Git Repository Status / 验证Git仓库状态

**Requirement**: Project MUST be a Git repository with Claude Enhancer initialized.

**Commands to Run**:
```bash
# Check if it's a git repository
git rev-parse --git-dir

# Check if .git/hooks/pre-commit exists
[ -f .git/hooks/pre-commit ] && echo "✓ Hooks installed" || echo "✗ Run tools/bootstrap.sh"

# Check if .phase directory exists
[ -d .phase ] && echo "✓ Workflow initialized" || echo "✗ Workflow not initialized"
```

**Expected Output**:
```
✓ Git repository detected
✓ Hooks installed
✓ Workflow initialized
```

**If Not Initialized**:
```bash
# Run bootstrap script
bash tools/bootstrap.sh

# Or if bootstrap.sh doesn't exist
git config core.hooksPath .git/hooks
chmod +x .git/hooks/*
```

---

### Step 2: Ensure Proper Branch / 确保在正确分支

**Requirement**: NEVER operate on `main` or `master` branch directly.

**Commands to Run**:
```bash
# Check current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $BRANCH"

# Verify not on protected branch
if [[ "$BRANCH" == "main" ]] || [[ "$BRANCH" == "master" ]]; then
    echo "❌ STOP: On protected branch!"
else
    echo "✓ Safe to proceed on: $BRANCH"
fi
```

**3 Ways to Create Feature Branch**:

#### Option A: Auto-Branch Mode (RECOMMENDED - Fastest)
```bash
export CE_AUTOBRANCH=1
git commit -m "Your commit message"
# Hook will automatically create feature/P1-auto-YYYYMMDD-HHMMSS branch
```

#### Option B: Manual Feature Branch (Traditional)
```bash
git checkout -b feature/your-feature-name
```

#### Option C: Claude Enhancer Workflow (Most Compliant)
```bash
# This will guide you through P0-P7 phases
bash .claude/hooks/workflow_enforcer_v2.sh 'Task description'
```

---

### Step 3: Enter Claude Enhancer Workflow / 进入Claude Enhancer工作流

**Requirement**: Follow the 8-Phase workflow (P0-P7) for structured development.

**Phase Overview**:
```
P0 Discovery    → Technical spike, feasibility validation
P1 Plan         → Requirements analysis, generate PLAN.md
P2 Skeleton     → Architecture design, directory structure
P3 Implementation → Coding with commits
P4 Testing      → Unit/integration/performance/BDD tests
P5 Review       → Code review, generate REVIEW.md
P6 Release      → Documentation, tags, health checks
P7 Monitor      → Production monitoring, SLO tracking
```

**How to Enter Workflow**:

```bash
# Check current phase
cat .phase/current

# If no phase set, start with P0
echo "P0" > .phase/current
mkdir -p .gates

# Create P0 spike document
touch docs/SPIKE_$(date +%Y%m%d).md
```

**Gate Signing** (Required at each phase completion):
```bash
# Example: Complete P0 phase
bash .workflow/scripts/sign_gate.sh P0 00 create

# Verify gate signature
[ -f .gates/00.ok ] && [ -f .gates/00.ok.sig ] && echo "✓ P0 gate signed"

# Move to next phase
echo "P1" > .phase/current
```

---

## 🚫 REJECTION Policy / 拒绝执行策略

### When AI MUST Refuse to Execute / AI必须拒绝执行的情况

The AI agent MUST refuse the user's request and provide fix instructions in the following scenarios:

#### Scenario 1: Uninitialized Repository

**Symptom**:
```bash
git rev-parse --git-dir  # Returns error
# OR
[ ! -f .git/hooks/pre-commit ]  # Hooks not installed
```

**AI Response**:
```
❌ REJECTION: Repository not initialized with Claude Enhancer

**Why I'm refusing**:
The project lacks Claude Enhancer's quality protection system.
I cannot safely modify files without hooks and workflow guards.

**How to fix** (choose one):

Option 1: Run bootstrap (if tools/bootstrap.sh exists)
  bash tools/bootstrap.sh

Option 2: Manual initialization
  git config core.hooksPath .git/hooks
  chmod +x .git/hooks/*
  mkdir -p .phase .gates

After initialization, please ask me again.
```

---

#### Scenario 2: Operating on Main Branch

**Symptom**:
```bash
git rev-parse --abbrev-ref HEAD  # Returns "main" or "master"
```

**AI Response**:
```
❌ REJECTION: Cannot modify files on protected branch (main/master)

**Why I'm refusing**:
Direct commits to main/master bypass code review and quality gates.
This violates the Claude Enhancer protection model.

**How to fix** (choose one):

Option 1: Auto-branch mode (fastest)
  export CE_AUTOBRANCH=1
  # Then retry your request

Option 2: Create feature branch manually
  git checkout -b feature/your-feature-name
  # Then retry your request

Option 3: Use workflow enforcer
  bash .claude/hooks/workflow_enforcer_v2.sh 'your task description'

After switching to a feature branch, please ask me again.
```

---

#### Scenario 3: Workflow Not Entered

**Symptom**:
```bash
[ ! -f .phase/current ]  # Phase file doesn't exist
# OR
cat .phase/current  # Returns empty or invalid phase
```

**AI Response**:
```
❌ REJECTION: Workflow not initialized

**Why I'm refusing**:
Claude Enhancer requires structured development through P0-P7 phases.
Random file modifications without workflow context lead to technical debt.

**How to fix**:

Step 1: Initialize workflow
  mkdir -p .phase .gates
  echo "P0" > .phase/current

Step 2: Start with Discovery Phase (P0)
  # Create a spike document to explore the problem
  touch docs/SPIKE_$(date +%Y%m%d).md

Step 3: Understand the phases
  # P0 → Explore and validate feasibility
  # P1 → Create implementation plan (PLAN.md)
  # P2 → Design skeleton structure
  # P3 → Implement code
  # ... and so on

After entering P0, please ask me again with context about what you want to achieve.
```

---

#### Scenario 4: Missing Gate Signatures

**Symptom**:
```bash
cat .phase/current  # Shows "P3"
# BUT
[ ! -f .gates/00.ok ] || [ ! -f .gates/01.ok ] || [ ! -f .gates/02.ok ]
# Previous gates not signed
```

**AI Response**:
```
❌ REJECTION: Skipped phases detected

**Why I'm refusing**:
Current phase is P3, but gates for P0/P1/P2 are missing.
This indicates phases were skipped, violating the sequential workflow.

**How to fix**:

Option 1: Go back and complete missing phases
  echo "P0" > .phase/current
  # Complete P0 (spike), P1 (plan), P2 (skeleton) properly

Option 2: Sign gates retroactively (if work was done)
  bash .workflow/scripts/sign_gate.sh P0 00 create
  bash .workflow/scripts/sign_gate.sh P1 01 create
  bash .workflow/scripts/sign_gate.sh P2 02 create

After fixing the workflow sequence, please ask me again.
```

---

#### Scenario 5: Capability Not Met (C0-C9 Matrix)

**Symptom**:
```bash
# Example: User asks to deploy but monitoring (C9) not configured
[ ! -f observability/slo/slo.yml ]  # SLO not defined
```

**AI Response**:
```
❌ REJECTION: Capability C9 (Monitoring) not satisfied

**Why I'm refusing**:
You're trying to deploy/release, but production monitoring (C9) is not configured.
Deploying without monitoring violates Claude Enhancer's production-readiness standard.

**How to fix**:

Step 1: Create SLO definitions
  mkdir -p observability/slo
  # Define at least 5 SLOs (availability, latency, error rate, etc.)

Step 2: Create health probes
  mkdir -p observability/probes
  touch observability/probes/liveness.yml
  touch observability/probes/readiness.yml

Step 3: Verify capability
  bash scripts/capability_snapshot.sh | grep "C9.*✅"

After setting up monitoring, please ask me again.
```

---

## 🎮 Phase-Specific Rules / 各阶段特定规则

### P0 (Discovery) - Exploration Only

**Allowed**:
- ✅ Read any files
- ✅ Run analysis commands (grep, find, git log)
- ✅ Create SPIKE.md document
- ✅ Create proof-of-concept scripts in `/tmp`

**NOT Allowed**:
- ❌ Modify production code
- ❌ Commit to repository
- ❌ Change dependencies (package.json, etc.)

**Completion Criteria**:
```bash
# Must have spike document
[ -f docs/SPIKE_*.md ]

# Sign gate
bash .workflow/scripts/sign_gate.sh P0 00 create

# Move to P1
echo "P1" > .phase/current
```

---

### P1 (Plan) - Planning Only

**Allowed**:
- ✅ Read existing code
- ✅ Create PLAN.md with task breakdown
- ✅ Estimate effort and risks
- ✅ Select agents (4-6-8 principle)

**NOT Allowed**:
- ❌ Write implementation code
- ❌ Modify existing files

**Completion Criteria**:
```bash
# Must have plan document
[ -f docs/PLAN_*.md ]

# Plan must include:
# - Task list (5-10 tasks)
# - Time estimates
# - Agent selection
# - Risk assessment

# Sign gate
bash .workflow/scripts/sign_gate.sh P1 01 create
echo "P2" > .phase/current
```

---

### P2 (Skeleton) - Structure Only

**Allowed**:
- ✅ Create directory structure
- ✅ Create empty/stub files
- ✅ Define interfaces and types
- ✅ Update import/export statements

**NOT Allowed**:
- ❌ Write function implementations
- ❌ Write test implementations

**Completion Criteria**:
```bash
# All planned files exist (even if stubs)
# Architecture diagram created
# Interfaces defined

bash .workflow/scripts/sign_gate.sh P2 02 create
echo "P3" > .phase/current
```

---

### P3 (Implementation) - Coding Phase

**Allowed**:
- ✅ Implement functions
- ✅ Write business logic
- ✅ Create commits (frequent, small)
- ✅ Refactor as needed

**Commit Message Enforcement**:
```bash
# Every commit MUST follow conventional commits
# Format: <type>(<scope>): <description>

# Valid examples:
git commit -m "feat(auth): add login endpoint"
git commit -m "fix(db): resolve connection timeout"
git commit -m "refactor(api): simplify error handling"

# Invalid examples (will be rejected by commit-msg hook):
git commit -m "changes"
git commit -m "fix stuff"
git commit -m "WIP"
```

**NOT Allowed**:
- ❌ Skipping tests (must add tests in P4)
- ❌ Deploying to production

**Completion Criteria**:
```bash
# All planned features implemented
# No TODO/FIXME comments in critical paths
# Code compiles/runs without errors

bash .workflow/scripts/sign_gate.sh P3 03 create
echo "P4" > .phase/current
```

---

### P4 (Testing) - Quality Assurance

**Required Tests**:
1. ✅ Unit tests (>80% coverage)
2. ✅ Integration tests
3. ✅ BDD scenarios (acceptance/)
4. ✅ Performance tests (metrics/perf_budget.yml)

**Enforcement**:
```bash
# Pre-push hook will verify:
npm run test          # Unit tests pass
npm run bdd           # BDD scenarios pass
npm run perf          # Performance within budget

# Coverage check
npm run coverage | grep "All files.*80"
```

**Completion Criteria**:
```bash
bash .workflow/scripts/sign_gate.sh P4 04 create
echo "P5" > .phase/current
```

---

### P5 (Review) - Code Review

**Required**:
- ✅ Generate REVIEW.md
- ✅ Address all code smells
- ✅ Security scan passed
- ✅ Performance regression check

**Commands**:
```bash
# Run code review
bash scripts/code_review.sh > docs/REVIEW_$(date +%Y%m%d).md

# Fix issues
# Re-run until clean

bash .workflow/scripts/sign_gate.sh P5 05 create
echo "P6" > .phase/current
```

---

### P6 (Release) - Documentation & Tagging

**Required**:
- ✅ Update CHANGELOG.md
- ✅ Update README.md
- ✅ Create git tag
- ✅ Health check passed

**Commands**:
```bash
# Update changelog
echo "## [1.2.0] - $(date +%Y-%m-%d)" >> CHANGELOG.md

# Tag release
git tag -a v1.2.0 -m "Release 1.2.0"

# Health check
bash scripts/healthcheck.sh

bash .workflow/scripts/sign_gate.sh P6 06 create
echo "P7" > .phase/current
```

---

### P7 (Monitor) - Production Monitoring

**Required**:
- ✅ SLO definitions (observability/slo/slo.yml)
- ✅ Alert rules configured
- ✅ Dashboards created
- ✅ Error budget tracking

**Completion**:
```bash
bash .workflow/scripts/sign_gate.sh P7 07 create
echo "DONE" > .phase/current
```

---

## 📊 Usage Example / 使用示例

### ✅ Correct Flow (AI Compliant)

```
User: "Add a login feature"

AI:
Let me verify the project setup first...

✓ Git repository detected
✓ Hooks installed
✓ Current branch: feature/add-login
✓ Current phase: P0

I'll start with P0 Discovery phase:

Step 1: Create spike document to explore authentication options
[Creates docs/SPIKE_auth_20251009.md]

Step 2: Research existing authentication code
[Reads relevant files]

Step 3: Evaluate 3 approaches
[Documents in spike]

P0 Complete! Signing gate...
[Signs .gates/00.ok]

Moving to P1 Planning...
[Continues through phases]
```

---

### ❌ Incorrect Flow (AI Non-Compliant)

```
User: "Add a login feature"

AI (BAD):
Sure! Let me create app/auth/login.js...
[Writes code directly]

❌ WRONG! This violates the contract:
- Didn't verify repository status
- Didn't check branch (might be on main!)
- Didn't enter workflow (no phase set)
- Skipped P0 discovery, P1 planning, P2 skeleton
```

**Correct AI Response**:
```
AI (GOOD):
❌ REJECTION: Workflow not initialized

Before I can add the login feature, I need to verify setup:

Please run:
  cat .phase/current

If it returns an error, initialize workflow:
  echo "P0" > .phase/current
  mkdir -p .gates docs

After initialization, I'll start with P0 Discovery phase to:
1. Explore authentication options
2. Evaluate security requirements
3. Plan the implementation approach

Then proceed through P1 (Plan) → P2 (Skeleton) → P3 (Implementation).
```

---

## 🔍 Contract Verification / 契约验证

### For AI Agents to Self-Check

Before ANY file modification, AI should run this mental checklist:

```
[ ] 1. Am I in a Git repository?
       → git rev-parse --git-dir

[ ] 2. Are hooks installed?
       → [ -x .git/hooks/pre-commit ]

[ ] 3. Am I on a feature branch (not main/master)?
       → git rev-parse --abbrev-ref HEAD

[ ] 4. Is workflow initialized?
       → [ -f .phase/current ]

[ ] 5. Is current phase valid?
       → cat .phase/current | grep -E "^P[0-7]$"

[ ] 6. Are previous gates signed?
       → [ -f .gates/XX.ok ] for all XX < current phase

[ ] 7. Does my action match the current phase?
       → P0=explore, P1=plan, P2=skeleton, P3=code, etc.

[ ] 8. Will this pass pre-commit hooks?
       → No hardcoded secrets, no syntax errors, etc.
```

**If ANY checkbox is unchecked → REJECT and guide user to fix**

---

## 📚 References / 参考文档

- Claude Enhancer Workflow: `.claude/WORKFLOW.md`
- Capability Matrix: `docs/CAPABILITY_MATRIX.md`
- Troubleshooting: `docs/TROUBLESHOOTING_GUIDE.md`
- Bootstrap Script: `tools/bootstrap.sh`
- Pre-commit Hook: `.git/hooks/pre-commit` (line 136-183)

---

## 📝 Contract Enforcement / 契约执行

### Layer 1: AI Self-Discipline
- AI agents voluntarily follow this contract
- Built into system prompts and agent instructions

### Layer 2: Claude Hooks (Soft Enforcement)
- `.claude/hooks/branch_helper.sh` - Suggests branch creation
- `.claude/hooks/smart_agent_selector.sh` - Recommends workflow
- `.claude/hooks/quality_gate.sh` - Warns about quality issues

### Layer 3: Git Hooks (Hard Enforcement)
- `.git/hooks/pre-commit` - BLOCKS commits that violate rules
- `.git/hooks/commit-msg` - Enforces commit message format
- `.git/hooks/pre-push` - Runs tests before push

### Layer 4: CI/CD (Server-Side Enforcement)
- `.github/workflows/*.yml` - Validates everything on server
- Prevents merging if any check fails

---

## 🎖️ Compliance Badge / 合规徽章

Projects that follow this contract can display:

```markdown
[![Claude Enhancer Compliant](https://img.shields.io/badge/Claude_Enhancer-Compliant-brightgreen)]()
```

---

## 📞 Support / 支持

If you encounter scenarios not covered by this contract:
1. Check `docs/TROUBLESHOOTING_GUIDE.md`
2. Review failure modes FM-1 to FM-5
3. Run diagnostic: `bash scripts/gap_scan.sh`

---

**Contract End / 契约结束**

By following this contract, AI agents ensure:
- ✅ No accidental main branch commits
- ✅ Structured development workflow
- ✅ Quality gates at every phase
- ✅ Production-ready code quality

**Effective Date**: Immediate upon repository initialization
**Supersedes**: All previous ad-hoc AI operation guidelines
