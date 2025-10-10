# Code Review Report - [Feature/Module Name]

**Review Date**: YYYY-MM-DD
**Reviewer**: Claude Code
**Version**: v5.4.0
**Branch**: feature/xxx
**Commit Range**: [hash1...hash2]

---

## 📊 Overall Score: X.X/10.0

### Quality Breakdown

| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Readability | X.X/10 | 15% | X.XX |
| Maintainability | X.X/10 | 15% | X.XX |
| Security | X.X/10 | 20% | X.XX |
| Error Handling | X.X/10 | 10% | X.XX |
| Performance | X.X/10 | 10% | X.XX |
| Test Coverage | X.X/10 | 15% | X.XX |
| Documentation | X.X/10 | 5% | X.XX |
| Code Standards | X.X/10 | 5% | X.XX |
| Git Hygiene | X.X/10 | 3% | X.XX |
| Dependencies | X.X/10 | 2% | X.XX |
| **TOTAL** | | **100%** | **X.XX** |

---

## 🎯 Executive Summary

[Brief 2-3 sentence summary of the review findings]

### Key Findings
- ✅ **Strengths**: [List main strengths]
- ⚠️ **Concerns**: [List main concerns]
- 🔴 **Blockers**: [List any blocking issues]

---

## 📋 Detailed Analysis

### 1. Readability (X.X/10)

**Assessment**: [Clear/Moderate/Poor]

**Positives**:
- [ ] Clear variable and function names
- [ ] Consistent code style
- [ ] Logical code organization

**Issues**:
- [ ] Complex nested logic
- [ ] Inconsistent naming conventions
- [ ] Missing comments for complex sections

**Recommendations**:
1. [Specific recommendation]
2. [Specific recommendation]

---

### 2. Maintainability (X.X/10)

**Assessment**: [Excellent/Good/Needs Improvement]

**Positives**:
- [ ] Modular design
- [ ] Single Responsibility Principle followed
- [ ] DRY principle applied

**Issues**:
- [ ] Code duplication detected
- [ ] Large functions (>50 lines)
- [ ] High complexity scores

**Recommendations**:
1. [Specific recommendation]
2. [Specific recommendation]

---

### 3. Security (X.X/10)

**Assessment**: [Secure/Moderate Risk/High Risk]

**Security Checks**:
- [ ] No hardcoded credentials
- [ ] Input validation present
- [ ] Proper error messages (no info leakage)
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] Secure dependencies

**Issues Found**:
- [ ] [Specific security issue]
- [ ] [Specific security issue]

**Critical Issues**: [Yes/No]
**Severity**: [Low/Medium/High/Critical]

**Recommendations**:
1. [Specific security fix]
2. [Specific security fix]

---

### 4. Error Handling (X.X/10)

**Assessment**: [Comprehensive/Adequate/Insufficient]

**Positives**:
- [ ] Try-catch blocks present
- [ ] Meaningful error messages
- [ ] Proper error propagation
- [ ] Logging implemented

**Issues**:
- [ ] Silent failures
- [ ] Generic error messages
- [ ] Missing error handling for edge cases

**Recommendations**:
1. [Specific recommendation]
2. [Specific recommendation]

---

### 5. Performance (X.X/10)

**Assessment**: [Optimized/Acceptable/Needs Optimization]

**Performance Metrics**:
- **Complexity**: O(?) time, O(?) space
- **Database Queries**: N queries per operation
- **Memory Usage**: Estimated XMB
- **Response Time**: Xms (estimated)

**Issues**:
- [ ] N+1 query problem
- [ ] Inefficient algorithms
- [ ] Memory leaks potential

**Recommendations**:
1. [Specific optimization]
2. [Specific optimization]

---

### 6. Test Coverage (X.X/10)

**Coverage Metrics**:
- **Overall Coverage**: XX%
- **Critical Paths**: XX%
- **Edge Cases**: XX%

**Test Types**:
- [ ] Unit tests present (XX tests)
- [ ] Integration tests present (XX tests)
- [ ] E2E tests present (XX tests)

**Missing Tests**:
1. [Specific test case]
2. [Specific test case]

**Recommendations**:
1. Add tests for [specific scenario]
2. Increase coverage to ≥80%

---

### 7. Documentation (X.X/10)

**Assessment**: [Excellent/Good/Insufficient]

**Positives**:
- [ ] README updated
- [ ] API documentation present
- [ ] Inline comments for complex logic
- [ ] Usage examples provided

**Issues**:
- [ ] Missing function documentation
- [ ] Outdated documentation
- [ ] No usage examples

**Recommendations**:
1. [Specific documentation need]
2. [Specific documentation need]

---

### 8. Code Standards (X.X/10)

**Linter Results**:
- ShellCheck: X warnings
- Flake8: X warnings
- Pylint: X warnings

**Standards Compliance**:
- [ ] Follows project style guide
- [ ] Consistent formatting
- [ ] Proper type annotations (Python)

**Issues**:
- [List specific violations]

---

### 9. Git Hygiene (X.X/10)

**Commit Analysis**:
- **Total Commits**: X
- **Average Commit Size**: X lines
- **Commit Message Quality**: [Good/Fair/Poor]

**Positives**:
- [ ] Atomic commits
- [ ] Clear commit messages
- [ ] Proper branch naming

**Issues**:
- [ ] Large commits (>300 lines)
- [ ] Unclear commit messages
- [ ] Mixed concerns in commits

---

### 10. Dependencies (X.X/10)

**Dependency Analysis**:
- **New Dependencies**: X
- **Updated Dependencies**: X
- **Security Vulnerabilities**: X

**Issues**:
- [ ] Outdated dependencies
- [ ] Security vulnerabilities
- [ ] Unnecessary dependencies

---

## 🔍 Code Snippets Requiring Attention

### Critical Issue 1: [Title]
**File**: `path/to/file.ext:line`
**Severity**: High

```language
[code snippet]
```

**Problem**: [Description]
**Recommendation**: [Fix]

---

### Issue 2: [Title]
**File**: `path/to/file.ext:line`
**Severity**: Medium

```language
[code snippet]
```

**Problem**: [Description]
**Recommendation**: [Fix]

---

## ✅ Approval Checklist

- [ ] No critical security issues
- [ ] Quality score ≥ 8.0/10
- [ ] Test coverage ≥ 80%
- [ ] All linters pass
- [ ] Documentation complete
- [ ] No blocking issues

---

## 🎬 Final Decision

**Status**: [APPROVED / APPROVED WITH CONDITIONS / REJECTED]

**Conditions** (if applicable):
1. [Must-fix issue]
2. [Must-fix issue]

**Next Steps**:
1. [Action item]
2. [Action item]

---

## 📝 Reviewer Notes

[Any additional comments or observations]

---

**Review completed by**: Claude Enhancer v5.4.0
**Review duration**: Xm Xs
**Generated**: YYYY-MM-DD HH:MM:SS
