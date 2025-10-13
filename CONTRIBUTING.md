# Contributing Guide - Claude Enhancer 6.2.0

Welcome! This guide explains how to contribute to Claude Enhancer using the 8-Phase workflow system.

## Quick Start for Contributors

### 1. Set Up Your Environment

```bash
# Fork and clone
git clone https://github.com/yourusername/claude-enhancer.git
cd claude-enhancer

# Install dependencies
npm install
./.claude/install.sh

# Verify setup
python3 scripts/auto_metrics.py --check-only
bash scripts/cleanup_documents.sh
```

### 2. Create a Feature Branch

```bash
# ALWAYS create a branch for new work
git checkout -b feature/your-feature-name

# Branch naming conventions:
# feature/     → New features
# bugfix/      → Bug fixes
# docs/        → Documentation updates
# perf/        → Performance improvements
# refactor/    → Code refactoring
```

### 3. Follow the 8-Phase Workflow

Every contribution must follow P0-P7. See [Development Workflow](#development-workflow) below.

## Development Workflow

### Phase -1: Branch Check (Pre-Phase)

**CRITICAL**: Before any work, verify you're on the correct branch.

```bash
# Check current branch
git branch --show-current

# If on main/master, CREATE NEW BRANCH
git checkout -b feature/your-feature
```

**Rules**:
- ❌ Never work on `main`, `master`, or `production`
- ❌ Never work on someone else's feature branch
- ✅ Always create a new branch for new work
- ✅ One branch per logical feature/fix

### Phase 0: Discovery (P0)

**Purpose**: Research and validate your approach before coding.

**Activities**:
1. Research existing solutions
2. Identify technical constraints
3. Evaluate alternative approaches
4. Validate feasibility

**Output**: Document your findings in `.temp/discovery/`

**Example**:
```bash
# Create discovery document
cat > .temp/discovery/feature-name-spike.md << 'EOF'
# Feature: Add New Authentication Method

## Research
- Investigated OAuth2, JWT, Session-based
- Reviewed existing auth implementation

## Findings
- OAuth2 is most suitable
- Requires new dependency: passport-oauth2
- Compatible with existing session system

## Risks
- Migration path for existing users
- Increased complexity in auth flow

## Recommendation
Proceed with OAuth2 implementation
EOF
```

### Phase 1: Planning (P1)

**Purpose**: Create detailed plan with agent selection.

**Activities**:
1. Break down requirements into tasks
2. Define acceptance criteria
3. Select agents (4-8 based on complexity)
4. Create PLAN.md

**Agent Selection** (4-6-8 Principle):
```bash
# Simple task (bug fix): 4 agents
- backend-engineer
- test-engineer
- code-reviewer
- technical-writer

# Standard task (new feature): 6 agents
- product-manager
- backend-architect
- backend-engineer
- test-engineer
- code-reviewer
- technical-writer

# Complex task (architecture): 8 agents
- product-manager
- architect
- backend-specialist
- frontend-specialist
- database-specialist
- test-engineer
- security-auditor
- performance-engineer
```

**Output**: Create PLAN.md

**Example PLAN.md**:
```markdown
# Plan: Add OAuth2 Authentication

## Overview
Implement OAuth2 authentication alongside existing methods.

## Requirements
- Support Google, GitHub OAuth2 providers
- Maintain existing session-based auth
- Secure token storage

## Tasks
1. [ ] Add passport-oauth2 dependency
2. [ ] Create OAuth2 strategy
3. [ ] Add OAuth2 routes
4. [ ] Update authentication middleware
5. [ ] Write tests
6. [ ] Update documentation

## Agents Selected (6)
- backend-architect: Design OAuth2 integration
- backend-engineer: Implement OAuth2 flow
- security-auditor: Review security implications
- test-engineer: Create test scenarios
- database-specialist: Design token storage
- technical-writer: Update documentation

## Success Criteria
- [ ] OAuth2 login works for Google and GitHub
- [ ] Existing auth still works
- [ ] Tests pass with 80%+ coverage
- [ ] Security audit passes
- [ ] Documentation updated

## Timeline
- P2: 2 hours
- P3: 6 hours
- P4: 4 hours
- P5: 2 hours
- P6: 1 hour
- Total: ~15 hours
```

### Phase 2: Skeleton (P2)

**Purpose**: Set up architecture and structure.

**Activities**:
1. Design system architecture
2. Create directory structure
3. Define interfaces
4. Add type definitions

**Example**:
```bash
# Create directory structure
mkdir -p src/auth/oauth2
mkdir -p src/auth/oauth2/strategies
mkdir -p src/auth/oauth2/providers
mkdir -p test/auth/oauth2

# Create skeleton files with interfaces
touch src/auth/oauth2/index.ts
touch src/auth/oauth2/types.ts
touch src/auth/oauth2/strategies/google.ts
touch src/auth/oauth2/strategies/github.ts
```

**Commit Message**:
```
feat(auth): add OAuth2 skeleton structure

- Create directory structure for OAuth2
- Define TypeScript interfaces
- Add provider strategy templates

Part-of: #123
Phase: P2
```

### Phase 3: Implementation (P3)

**Purpose**: Write the actual code.

**Activities**:
1. Implement features following PLAN.md
2. Follow code style guidelines
3. Make atomic commits
4. Document inline

**Code Style**:
- Use TypeScript for type safety
- Follow existing patterns
- Add JSDoc comments
- Keep functions small (<50 lines)

**Commit Guidelines**:
```
# Format
<type>(<scope>): <subject>

<body>

Part-of: #<issue>
Phase: P3

# Types
feat:     New feature
fix:      Bug fix
docs:     Documentation
style:    Formatting
refactor: Code restructuring
perf:     Performance improvement
test:     Tests
chore:    Maintenance

# Example
feat(auth): implement Google OAuth2 strategy

- Add Google OAuth2 strategy using passport-google-oauth20
- Configure callback URL handling
- Add token validation logic

Part-of: #123
Phase: P3
```

**Make Atomic Commits**:
```bash
# Good: Small, focused commits
git commit -m "feat(auth): add OAuth2 base strategy"
git commit -m "feat(auth): implement Google OAuth2"
git commit -m "feat(auth): implement GitHub OAuth2"

# Bad: Giant commit
git commit -m "add OAuth2 with everything"
```

### Phase 4: Testing (P4)

**Purpose**: Comprehensive test coverage.

**Activities**:
1. Write unit tests
2. Write integration tests
3. Create BDD scenarios
4. Run performance tests

**Test Requirements**:
- ✅ Unit test coverage: 80%+
- ✅ Integration tests for critical paths
- ✅ BDD scenarios for user workflows
- ✅ Performance benchmarks

**Example Unit Test**:
```typescript
// test/auth/oauth2/google.test.ts
describe('GoogleOAuth2Strategy', () => {
  it('should authenticate valid Google token', async () => {
    const strategy = new GoogleOAuth2Strategy();
    const user = await strategy.authenticate(validToken);
    expect(user).toBeDefined();
    expect(user.email).toBe('user@example.com');
  });

  it('should reject invalid token', async () => {
    const strategy = new GoogleOAuth2Strategy();
    await expect(
      strategy.authenticate(invalidToken)
    ).rejects.toThrow('Invalid token');
  });
});
```

**Example BDD Scenario**:
```gherkin
# acceptance/features/oauth2.feature
Feature: OAuth2 Authentication

  Scenario: User logs in with Google
    Given I am not logged in
    When I click "Login with Google"
    And I authorize the application
    Then I should be logged in
    And I should see my profile

  Scenario: OAuth2 token expires
    Given I am logged in via Google OAuth2
    When my OAuth2 token expires
    And I make an authenticated request
    Then I should be prompted to re-authenticate
```

**Run Tests**:
```bash
# Unit tests
npm test

# BDD tests
npm run bdd

# With coverage
npm run test:coverage

# Performance tests
npm run test:perf
```

### Phase 5: Review (P5)

**Purpose**: Quality assurance and code review.

**Activities**:
1. Self-review checklist
2. Run automated checks
3. Generate REVIEW.md
4. Address findings

**Self-Review Checklist**:
```markdown
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Test coverage ≥80%
- [ ] No console.log() statements
- [ ] Error handling is comprehensive
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance is acceptable
- [ ] Commits are atomic and well-described
- [ ] PLAN.md criteria are met
```

**Run Quality Checks**:
```bash
# Linting
npm run lint

# Type checking
npm run type-check

# Security audit
npm audit

# Check metrics
python3 scripts/auto_metrics.py --check-only

# Generate review
# This creates REVIEW.md with automated analysis
```

**REVIEW.md Example**:
```markdown
# Code Review: OAuth2 Authentication

## Summary
Implementation of OAuth2 authentication for Google and GitHub.

## Findings

### Strengths ✅
- Clean architecture with strategy pattern
- Comprehensive test coverage (87%)
- Good error handling
- Well documented

### Issues Found 🔍

#### High Priority
- [ ] Token refresh logic missing
- [ ] CSRF protection needed for OAuth2 callback

#### Medium Priority
- [ ] Add rate limiting to OAuth2 endpoints
- [ ] Improve error messages

#### Low Priority
- [ ] Extract magic numbers to constants
- [ ] Add more JSDoc examples

## Security Review ✅
- No hardcoded credentials
- Proper input validation
- Secure token storage
- HTTPS enforced

## Performance Review ✅
- OAuth2 flow: 245ms (target: <300ms)
- Token validation: 8ms (target: <10ms)

## Recommendations
1. Implement token refresh before merge
2. Add CSRF protection
3. Consider adding rate limiting

## Approval
Status: Approved with minor changes required
```

### Phase 6: Release (P6)

**Purpose**: Prepare for production.

**Activities**:
1. Update documentation
2. Update CHANGELOG.md
3. Create release notes
4. Run final health checks

**Update CHANGELOG.md**:
```markdown
## [Unreleased]

### Added
- OAuth2 authentication support for Google and GitHub
- Token refresh mechanism
- OAuth2-specific error handling

### Changed
- Enhanced authentication middleware to support multiple strategies

### Security
- Added CSRF protection for OAuth2 callbacks
- Implemented secure token storage with encryption
```

**Final Checks**:
```bash
# All tests pass
npm test && npm run bdd

# No uncommitted changes
git status

# Metrics are accurate
python3 scripts/auto_metrics.py --check-only

# Documents are clean
bash scripts/cleanup_documents.sh
```

**Ready for PR**:
```bash
# Push to your branch
git push origin feature/oauth2-authentication

# PR will be auto-created by auto-pr.yml workflow
# Or create manually with detailed description
```

### Phase 7: Monitor (P7)

**Purpose**: Post-merge monitoring.

**Activities**:
1. Monitor CI/CD pipeline
2. Track SLO metrics
3. Watch for errors
4. Gather feedback

**Monitoring Checklist**:
```markdown
- [ ] CI/CD pipeline passes
- [ ] No new errors in logs
- [ ] SLO metrics stable
- [ ] Performance within budget
- [ ] User feedback positive
```

## Pull Request Guidelines

### PR Title Format
```
<type>(<scope>): <description>

Examples:
feat(auth): add OAuth2 authentication support
fix(api): resolve race condition in session handling
docs(readme): update installation instructions
```

### PR Description Template
```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring

## Related Issues
Closes #123

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] BDD scenarios added/updated
- [ ] All tests passing

## Checklist
- [ ] Followed 8-Phase workflow (P0-P7)
- [ ] PLAN.md created and followed
- [ ] REVIEW.md generated
- [ ] Code review completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Metrics verified accurate
- [ ] No unauthorized documents in root

## Phase Status
- [x] P0: Discovery
- [x] P1: Planning
- [x] P2: Skeleton
- [x] P3: Implementation
- [x] P4: Testing
- [x] P5: Review
- [x] P6: Release
- [ ] P7: Monitor (post-merge)

## Screenshots (if applicable)
[Add screenshots here]
```

## Quality Standards

### Code Quality
- **Test Coverage**: ≥80%
- **Linting**: 0 errors, <5 warnings
- **Type Safety**: 100% (TypeScript)
- **Documentation**: All public APIs documented

### Performance Budgets
- API Response P95: <200ms
- Hook Execution: <30ms
- BDD Tests: <500ms
- Build Time: <3 minutes

### Security Standards
- No hardcoded secrets
- Input validation on all endpoints
- HTTPS only in production
- Regular dependency updates

## Common Mistakes to Avoid

### ❌ Don't Do This

1. **Working on main branch**
   ```bash
   # BAD
   git checkout main
   # make changes
   git commit
   ```

2. **Skipping phases**
   ```
   # BAD: Jump straight to coding
   User request → Write code → Push
   ```

3. **Giant commits**
   ```bash
   # BAD
   git commit -m "implement everything"
   ```

4. **Creating root documents**
   ```bash
   # BAD
   touch FEATURE_ANALYSIS.md  # Root directory
   ```

5. **Manual metric claims**
   ```markdown
   # BAD: in CLAUDE.md
   We have 150 BDD scenarios!  # Without verification
   ```

### ✅ Do This Instead

1. **Create feature branch**
   ```bash
   # GOOD
   git checkout -b feature/oauth2
   ```

2. **Follow all phases**
   ```
   # GOOD
   User request → P-1 → P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7
   ```

3. **Atomic commits**
   ```bash
   # GOOD
   git commit -m "feat(auth): add OAuth2 base class"
   git commit -m "feat(auth): implement Google strategy"
   git commit -m "feat(auth): implement GitHub strategy"
   ```

4. **Use proper directories**
   ```bash
   # GOOD
   touch .temp/analysis/feature-spike.md
   touch docs/architecture/oauth2-design.md
   ```

5. **Auto-collect metrics**
   ```bash
   # GOOD
   python3 scripts/auto_metrics.py --update-docs
   ```

## Getting Help

### Documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [INSTALLATION.md](INSTALLATION.md) - Setup guide
- [CLAUDE.md](CLAUDE.md) - Claude-specific workflows

### Common Issues

**Q: Git hook blocked my commit**
```bash
A: Read the error message carefully. Usually:
   - Fix linting errors: npm run lint --fix
   - Fix formatting: npm run format
   - Ensure tests pass: npm test
```

**Q: On wrong branch**
```bash
A: Create new branch:
   git checkout -b feature/correct-name
```

**Q: Metrics show inflation**
```bash
A: Run auto-update:
   python3 scripts/auto_metrics.py --update-docs
```

**Q: Too many root documents**
```bash
A: Run cleanup:
   bash scripts/cleanup_documents.sh
```

## Community

### Code of Conduct
- Be respectful and inclusive
- Focus on constructive feedback
- Assume good intentions
- Help others learn

### Recognition
Contributors are recognized in:
- CHANGELOG.md under each release
- GitHub contributors page
- Special mentions for significant contributions

## Advanced Topics

### Custom Agents
See [ARCHITECTURE.md](ARCHITECTURE.md#adding-new-agents)

### Custom Quality Gates
See [ARCHITECTURE.md](ARCHITECTURE.md#adding-new-quality-gates)

### Performance Optimization
See [docs/performance/](docs/performance/)

---

**Thank you for contributing!** 🎉

By following this guide, you're helping maintain Claude Enhancer's production-grade quality standards.
