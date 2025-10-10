# Contributing to Claude Enhancer

Thank you for your interest in contributing to Claude Enhancer! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)
- [Quality Gates](#quality-gates)

---

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful of differing viewpoints and experiences.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Harassment, trolling, or derogatory comments
- Public or private harassment
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Violations may be reported to the project maintainers. All complaints will be reviewed and investigated promptly and fairly.

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:

- **bash** 4.0+ (Linux/macOS built-in)
- **git** 2.0+
- **Node.js** 18.0+
- **npm** 9.0+
- **Python** 3.8+ (for some tools)
- **shellcheck** (for shell script linting)

### Installation

```bash
# 1. Fork the repository on GitHub
# Click "Fork" button at https://github.com/claude-enhancer/claude-enhancer

# 2. Clone your fork
git clone https://github.com/YOUR-USERNAME/claude-enhancer.git
cd claude-enhancer

# 3. Add upstream remote
git remote add upstream https://github.com/claude-enhancer/claude-enhancer.git

# 4. Install dependencies
npm install

# 5. Install Git hooks
bash .claude/install.sh

# 6. Verify installation
npm test
# Expected: All 312+ tests should pass
```

---

## 🔄 Development Workflow

We follow the **8-Phase Claude Enhancer Workflow** for all contributions.

### Phase Flow

```
P0 (Discovery) → Spike & Feasibility
P1 (Plan) → Create docs/PLAN.md
P2 (Skeleton) → Design architecture
P3 (Implementation) → Write code
P4 (Testing) → Write tests (80%+ coverage)
P5 (Review) → Self-review before PR
P6 (Release) → Update docs
P7 (Monitor) → (Not applicable for contributions)
```

### Step-by-Step Contribution Process

```bash
# 1. Create feature branch (P0-P1)
git checkout -b feature/my-awesome-feature
echo "P1" > .phase/current

# 2. Document your plan (P1)
cat > docs/PLAN.md << 'EOF'
# Plan: My Awesome Feature

## Objective
What problem does this solve?

## Approach
How will you implement it?

## Files to Modify
- file1.sh
- file2.js

## Testing Strategy
How will you test it?
EOF

# 3. Design (P2)
echo "P2" > .phase/current
# Create directory structure if needed

# 4. Implement (P3)
echo "P3" > .phase/current
# Write your code
# Follow coding standards (see below)

# 5. Test (P4)
echo "P4" > .phase/current
npm test  # Must pass
npm run coverage  # Must be ≥80%

# 6. Review (P5)
echo "P5" > .phase/current
# Self-review your changes
# Run quality checks

# 7. Document (P6)
echo "P6" > .phase/current
# Update README, CHANGELOG if needed

# 8. Commit and push
git add .
git commit -m "feat: add awesome feature"
git push origin feature/my-awesome-feature

# 9. Create Pull Request
# Go to GitHub and create PR
```

---

## 📏 Coding Standards

### Shell Scripts (.sh files)

**Required Standards:**
- ✅ Use `#!/bin/bash` shebang
- ✅ Include `set -euo pipefail` at top
- ✅ Pass shellcheck with zero errors
- ✅ Use `readonly` for constants
- ✅ Quote all variables: `"${variable}"`
- ✅ Use meaningful function names
- ✅ Add comments for complex logic

**Example:**
```bash
#!/bin/bash
set -euo pipefail

# Constants
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_FILE="${SCRIPT_DIR}/output.log"

# Function: Process data
# Args: $1 - input file
# Returns: 0 on success, 1 on failure
process_data() {
    local input_file="$1"

    if [[ ! -f "${input_file}" ]]; then
        echo "Error: File not found: ${input_file}" >&2
        return 1
    fi

    # Process file...
    return 0
}

# Main execution
main() {
    process_data "$@"
}

main "$@"
```

**Shellcheck:**
```bash
# Must pass with zero errors
shellcheck your-script.sh
```

### JavaScript/TypeScript (.js, .ts files)

**Required Standards:**
- ✅ Use ESLint configuration (`.eslintrc.json`)
- ✅ Use Prettier for formatting
- ✅ ES6+ syntax (const/let, arrow functions)
- ✅ JSDoc comments for functions
- ✅ Meaningful variable names
- ✅ Maximum line length: 100 characters

**Example:**
```javascript
/**
 * Calculate quality score based on multiple dimensions
 * @param {Object} metrics - Quality metrics object
 * @param {number} metrics.code - Code quality score (0-15)
 * @param {number} metrics.tests - Test coverage score (0-15)
 * @returns {number} Total quality score (0-100)
 */
function calculateQualityScore(metrics) {
    const { code, tests, security } = metrics;
    return code + tests + security;
}
```

**Linting:**
```bash
# Must pass with zero errors
npm run lint

# Auto-fix issues
npm run lint:fix
```

### Python (.py files)

**Required Standards:**
- ✅ Follow PEP 8 style guide
- ✅ Use type hints (Python 3.8+)
- ✅ Docstrings for all functions/classes
- ✅ Maximum line length: 100 characters
- ✅ Use Black for formatting

**Example:**
```python
def calculate_score(metrics: dict) -> int:
    """
    Calculate quality score from metrics.

    Args:
        metrics: Dictionary containing quality metrics

    Returns:
        Total quality score (0-100)

    Raises:
        ValueError: If metrics are invalid
    """
    if not isinstance(metrics, dict):
        raise ValueError("Metrics must be a dictionary")

    return metrics.get("code", 0) + metrics.get("tests", 0)
```

### Documentation (.md files)

**Required Standards:**
- ✅ Use proper Markdown syntax
- ✅ Include table of contents for long docs
- ✅ Use code blocks with language tags
- ✅ Include examples where relevant
- ✅ Keep line length ≤120 characters

---

## 🧪 Testing Requirements

### Test Coverage Target: ≥80%

Every contribution **must** include tests that maintain or improve code coverage.

### Test Types

**1. Unit Tests** (150+ tests)
```bash
# Location: test/unit/
# Framework: Jest

# Example: test/unit/test_state_management.js
describe('State Management', () => {
    test('should create new session', () => {
        const session = createSession();
        expect(session).toHaveProperty('id');
        expect(session).toHaveProperty('timestamp');
    });
});
```

**2. Integration Tests** (57+ tests)
```bash
# Location: test/integration/
# Framework: Jest

# Example: test/integration/test_workflow.js
describe('Workflow Integration', () => {
    test('should complete P1-P6 cycle', async () => {
        await advancePhase('P1');
        await advancePhase('P2');
        // ... test complete workflow
        expect(getCurrentPhase()).toBe('P6');
    });
});
```

**3. Performance Tests** (105+ tests)
```bash
# Location: test/performance/
# Framework: Custom benchmarks

# Example: test/performance/test_startup.sh
test_startup_time() {
    local start=$(date +%s%N)
    bash .workflow/executor.sh --version
    local end=$(date +%s%N)
    local duration=$(((end - start) / 1000000))

    # Must be under 2 seconds
    assert_less_than "$duration" 2000
}
```

**4. BDD Tests** (65+ scenarios)
```bash
# Location: acceptance/features/
# Framework: Cucumber.js

# Example: acceptance/features/workflow.feature
Feature: 8-Phase Workflow
  Scenario: Complete development cycle
    Given I am in phase P1
    When I advance to P2
    Then the current phase should be P2
    And docs/PLAN.md should exist
```

### Running Tests

```bash
# Run all tests
npm test

# Run specific test type
npm run test:unit
npm run test:integration
npm run bdd

# Check coverage
npm run coverage
# Opens browser with coverage report

# Performance benchmarks
bash test/performance_suite.sh
```

### Writing Good Tests

**DO:**
- ✅ Test one thing per test
- ✅ Use descriptive test names
- ✅ Test edge cases and error conditions
- ✅ Mock external dependencies
- ✅ Clean up after tests

**DON'T:**
- ❌ Test implementation details
- ❌ Write tests that depend on execution order
- ❌ Leave commented-out test code
- ❌ Skip tests without good reason

---

## 📝 Commit Message Guidelines

We follow **Conventional Commits** specification.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples

**Good commits:**
```bash
feat(workflow): add P7 monitoring phase

Implements production monitoring with SLO tracking.
Adds 15 SLO definitions and health check probes.

Closes #123

---

fix(git-hooks): prevent concurrent phase execution

Adds file-based locking using flock to prevent race
conditions when multiple terminals run simultaneously.

Fixes #456

---

docs(readme): update installation instructions

Adds troubleshooting section and platform-specific notes.
```

**Bad commits:**
```bash
❌ "fixed bug"
❌ "update"
❌ "WIP"
❌ "asdf"
```

### Commit Message Validation

Our `commit-msg` Git hook enforces these rules:

```bash
# This will be validated automatically
git commit -m "feat: add new feature"  # ✅ Passes

git commit -m "Added feature"  # ❌ Fails
# Error: Commit message must follow conventional commits format
```

---

## 🔀 Pull Request Process

### Before Submitting

1. **Ensure all tests pass:**
   ```bash
   npm test  # All 312+ tests must pass
   ```

2. **Check code coverage:**
   ```bash
   npm run coverage  # Must be ≥80%
   ```

3. **Run linters:**
   ```bash
   npm run lint  # Zero errors/warnings
   shellcheck **/*.sh  # Zero errors
   ```

4. **Update documentation:**
   - Update README.md if adding features
   - Update CHANGELOG.md with changes
   - Add/update relevant docs/

5. **Self-review:**
   - Read through your changes
   - Check for debugging code
   - Verify all files are necessary

### Creating Pull Request

1. **Push to your fork:**
   ```bash
   git push origin feature/my-feature
   ```

2. **Create PR on GitHub:**
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill out PR template (provided automatically)

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass (312+ tests)
- [ ] Coverage ≥80%
- [ ] Added new tests for changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)

## Related Issues
Closes #issue_number
```

### Review Process

1. **Automated checks run:**
   - Tests (312+ tests)
   - Linting (shellcheck, eslint)
   - Coverage (≥80%)
   - Security scans

2. **Code review by maintainers:**
   - Review within 2-3 business days
   - Address feedback promptly
   - Push changes to same branch

3. **Approval & merge:**
   - Requires 1 approval
   - All checks must pass
   - Squash and merge used

---

## 📁 Project Structure

Understanding the project structure helps you navigate and contribute effectively.

```
Claude Enhancer/
├── .claude/                    # Claude-specific configurations
│   ├── agents/                # AI agent definitions
│   ├── hooks/                 # Claude hooks (assistive)
│   ├── settings.json          # Claude settings
│   └── install.sh            # Installation script
│
├── .workflow/                  # Workflow engine
│   ├── executor.sh           # Main workflow executor
│   ├── gates.yml             # Phase gates configuration
│   ├── manifest.yml          # Workflow manifest
│   ├── STAGES.yml            # Parallel execution stages
│   ├── cli/commands/         # CLI commands (7 files)
│   └── scripts/              # Helper scripts
│
├── .git/hooks/                # Git hooks (enforcement)
│   ├── pre-commit            # Pre-commit checks
│   ├── commit-msg            # Commit message validation
│   └── pre-push              # Pre-push tests
│
├── acceptance/                # BDD tests (65 scenarios)
│   ├── features/             # Cucumber feature files
│   └── steps/                # Step definitions
│
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md       # System architecture
│   ├── INSTALLATION.md       # Installation guide
│   ├── USER_GUIDE.md         # User documentation
│   └── *.md                  # Various guides
│
├── test/                      # Test suites
│   ├── unit/                 # Unit tests (150+)
│   ├── integration/          # Integration tests (57+)
│   ├── performance/          # Performance tests (105+)
│   └── coverage/             # Coverage reports
│
├── metrics/                   # Performance metrics
│   └── perf_budget.yml       # 90 metrics
│
├── observability/            # Monitoring
│   ├── slo/slo.yml          # 15 SLO definitions
│   └── probes/              # Health checks
│
├── README.md                 # Main documentation
├── CHANGELOG.md              # Version history
├── CONTRIBUTING.md           # This file
├── LICENSE                   # MIT license
└── package.json             # Node.js configuration
```

---

## 🛡️ Quality Gates

Every contribution must pass these quality gates:

### 1. Pre-Commit Gate

Runs automatically on `git commit`:

- ✅ Shellcheck (zero errors)
- ✅ ESLint (zero errors)
- ✅ Prettier formatting
- ✅ Secrets detection
- ✅ File permissions check
- ✅ Phase file validation

### 2. Commit Message Gate

Validates commit messages:

- ✅ Conventional commits format
- ✅ Type is valid (feat, fix, docs, etc.)
- ✅ Subject line ≤72 characters
- ✅ Body wrapping at 100 characters

### 3. Pre-Push Gate

Runs before `git push`:

- ✅ All tests pass (312+ tests)
- ✅ Code coverage ≥80%
- ✅ No TODO comments in committed code
- ✅ Documentation updated
- ✅ CHANGELOG.md updated

### 4. CI/CD Gates (GitHub Actions)

Runs on PR creation:

- ✅ Build succeeds
- ✅ All tests pass
- ✅ Coverage report generated
- ✅ Security scan (no vulnerabilities)
- ✅ Performance benchmarks
- ✅ BDD scenarios pass

### Bypassing Gates (Emergency Only)

In rare emergencies, you can bypass hooks:

```bash
# DO NOT DO THIS unless absolutely necessary
git commit --no-verify  # Bypasses pre-commit
git push --no-verify    # Bypasses pre-push
```

**Note:** CI/CD gates cannot be bypassed. All PRs must pass automated checks.

---

## 🎯 Contribution Areas

### Where to Contribute

**High Priority:**
- 🔴 Fix 3 P1 security vulnerabilities (VUL-001, VUL-002, VUL-003)
- 🔴 Complete API documentation (100/307 → 307/307 functions)
- 🟡 Add missing LICENSE file
- 🟡 Improve test coverage for specific modules

**Good First Issues:**
- 🟢 Documentation improvements
- 🟢 Add more examples
- 🟢 Fix typos and formatting
- 🟢 Add translations
- 🟢 Improve error messages

**Advanced Contributions:**
- Web dashboard for workflow monitoring
- Plugin system for custom agents
- Kubernetes integration
- Performance optimizations

### Finding Issues

Look for issues labeled:
- `good first issue` - Great for beginners
- `help wanted` - Community help needed
- `documentation` - Documentation work
- `bug` - Bug fixes
- `enhancement` - New features

---

## 💡 Tips for Contributors

### Best Practices

1. **Start small** - Begin with documentation or minor fixes
2. **Ask questions** - Use Discussions for clarification
3. **Follow the workflow** - Use the 8-Phase process
4. **Write tests** - Every change needs tests
5. **Update docs** - Keep documentation in sync

### Common Mistakes to Avoid

❌ **Not writing tests**
→ ✅ Add tests with every code change

❌ **Ignoring linter errors**
→ ✅ Fix all linting issues before committing

❌ **Large, unfocused PRs**
→ ✅ Keep PRs small and focused on one thing

❌ **Not updating documentation**
→ ✅ Update relevant docs with code changes

❌ **Breaking backward compatibility**
→ ✅ Ensure changes are backward compatible

### Getting Help

- **Questions?** Use [GitHub Discussions](https://github.com/claude-enhancer/claude-enhancer/discussions)
- **Bug found?** Open an [Issue](https://github.com/claude-enhancer/claude-enhancer/issues)
- **Need clarification?** Comment on relevant issue/PR

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the **MIT License**.

---

## 🙏 Thank You!

Your contributions make Claude Enhancer better for everyone. Thank you for taking the time to contribute!

---

**Questions?** Open a [Discussion](https://github.com/claude-enhancer/claude-enhancer/discussions) or contact the maintainers.

**Ready to contribute?** Pick an issue and get started! 🚀
