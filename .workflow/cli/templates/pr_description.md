# 🚀 Feature: [FEATURE_NAME]

## Summary

Brief description of the feature and its purpose.

<!-- Replace with actual feature description -->

---

## 📋 Changes

### Added
- Added X functionality to Y module
- Added Z configuration option

### Modified
- Modified A to support B
- Updated C for performance improvement

### Fixed
- Fixed issue with D not working in E scenario
- Resolved F bug affecting G users

### Removed
- Removed deprecated H function
- Cleaned up unused I dependencies

---

## 📊 Quality Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Quality Score** | [SCORE]/100 | ✅ Pass |
| **Test Coverage** | [COVERAGE]% | ✅ Pass |
| **Gate Signatures** | [SIGS]/8 | ✅ Complete |
| **Code Review** | Pending | ⏳ In Progress |
| **Security Scan** | Pass | ✅ Pass |

---

## 🧪 Testing

### Test Coverage Summary

- **Unit Tests**: X tests, Y% coverage
- **Integration Tests**: Z tests, 100% critical paths
- **E2E Tests**: A scenarios tested
- **Manual Testing**: B scenarios verified

### Test Results

```bash
# Unit Tests
✅ All 45 unit tests passed (2.3s)

# Integration Tests
✅ All 12 integration tests passed (5.1s)

# Quality Gates
✅ P0 Discovery - Passed
✅ P1 Planning - Passed
✅ P2 Skeleton - Passed
✅ P3 Implementation - Passed
✅ P4 Testing - Passed
✅ P5 Review - Passed
✅ P6 Release - Pending
✅ P7 Monitor - Pending
```

### Checklist

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing complete
- [ ] Performance benchmarks met
- [ ] Security scan clean
- [ ] All quality gates passed

---

## 📚 Documentation

### Updated Documentation

- [ ] User guide updated
- [ ] API reference updated
- [ ] CHANGELOG.md updated
- [ ] README.md updated (if needed)
- [ ] Migration guide added (if breaking changes)

### Documentation Links

- User Guide: [Link to section]
- API Reference: [Link to section]
- Examples: [Link to examples]

---

## 🔄 Migration Notes

### Breaking Changes

<!-- List any breaking changes -->
- None

### Upgrade Steps

<!-- Provide upgrade instructions if needed -->
```bash
# No migration required for this feature
```

### Backward Compatibility

- ✅ Fully backward compatible
- No API changes
- No configuration changes required

---

## 🎯 Affected Areas

### Files Changed

- `path/to/file1.sh` (+50, -10)
- `path/to/file2.sh` (+30, -5)
- `docs/file3.md` (+100, -0)

### Dependencies

- No new dependencies added
- All existing dependencies compatible

### Configuration

- No configuration changes required

---

## 🔍 Review Checklist

### Code Quality

- [ ] Code follows project style guide
- [ ] All functions have documentation
- [ ] No hardcoded values (use config)
- [ ] Error handling implemented
- [ ] Logging added where appropriate

### Testing

- [ ] Adequate test coverage (≥80%)
- [ ] Edge cases tested
- [ ] Error scenarios tested
- [ ] Performance tested

### Documentation

- [ ] User-facing changes documented
- [ ] API changes documented
- [ ] Code comments added
- [ ] CHANGELOG updated

### Security

- [ ] No secrets in code
- [ ] Input validation implemented
- [ ] No SQL injection risks
- [ ] No XSS vulnerabilities

### Performance

- [ ] No performance regressions
- [ ] Resource usage acceptable
- [ ] Caching implemented (if applicable)
- [ ] Optimizations applied

---

## 🚦 Deployment Plan

### Pre-Deployment

1. Final code review
2. All tests passing
3. Documentation complete
4. Stakeholders notified

### Deployment

1. Merge to main
2. Tag release (vX.Y.Z)
3. Deploy to production
4. Monitor health checks

### Post-Deployment

1. Verify functionality in production
2. Monitor error rates
3. Check performance metrics
4. Update status page

### Rollback Plan

If issues are detected:
```bash
# Immediate rollback
git revert [commit-sha]
git push origin main

# Or redeploy previous version
git checkout v[previous-version]
./deploy.sh
```

---

## 📸 Screenshots / Examples

<!-- Add screenshots or code examples here -->

### Before
```bash
# Old behavior
```

### After
```bash
# New behavior
```

---

## 🔗 Related Issues / PRs

<!-- Link to related issues and PRs -->

- Closes #XXX
- Related to #YYY
- Depends on #ZZZ

---

## 👥 Reviewers

<!-- Tag relevant reviewers -->

**Required Reviewers**:
- @backend-team
- @security-team

**Optional Reviewers**:
- @documentation-team

---

## 💬 Additional Notes

<!-- Any additional context or information -->

### Known Limitations

- Limitation A: Description and mitigation
- Limitation B: Description and future work

### Future Enhancements

- Enhancement idea A
- Enhancement idea B

---

## ✅ Final Checklist

**Before requesting review**:
- [ ] Code is complete and tested
- [ ] All tests pass locally
- [ ] Documentation is updated
- [ ] CHANGELOG is updated
- [ ] No merge conflicts
- [ ] CI/CD pipeline is green

**Before merging**:
- [ ] Code reviewed and approved
- [ ] All conversations resolved
- [ ] All gates passed
- [ ] Deployment plan ready
- [ ] Rollback plan documented

---

## 🤖 Automated Checks

<!-- These will be filled in by CI/CD -->

- ⏳ **Linting**: Pending
- ⏳ **Unit Tests**: Pending
- ⏳ **Integration Tests**: Pending
- ⏳ **Security Scan**: Pending
- ⏳ **Code Coverage**: Pending
- ⏳ **Performance Tests**: Pending

---

**Generated by**: CE CLI v1.0.0
**Created at**: YYYY-MM-DD HH:MM:SS
**Branch**: feature/[FEATURE_NAME]-YYYYMMDD-t1

---

Co-Authored-By: Claude <noreply@anthropic.com>
