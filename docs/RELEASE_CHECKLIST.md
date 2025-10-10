# Release Checklist

This checklist ensures all release criteria are met before publishing Claude Enhancer.

## Version: ___________
## Release Date: ___________
## Release Manager: ___________

---

## Phase 1: Pre-Release Validation

### Version Management
- [ ] VERSION file updated with new version number
- [ ] Version in `ce.sh` (CE_VERSION) matches VERSION file
- [ ] Version in `.claude/settings.json` updated (if applicable)
- [ ] Version references in documentation updated
- [ ] All version numbers are consistent across the project

### Documentation
- [ ] CHANGELOG.md updated with all changes
- [ ] CHANGELOG.md has proper section for this version
- [ ] README.md reviewed and updated if needed
- [ ] CLI_GUIDE.md reflects current features
- [ ] SYSTEM_OVERVIEW documents are current
- [ ] TROUBLESHOOTING_GUIDE is up to date
- [ ] API documentation complete (if applicable)
- [ ] Migration guide written (for breaking changes)

### Code Quality
- [ ] All tests passing locally
- [ ] No compiler/interpreter warnings
- [ ] Code coverage meets threshold (≥80%)
- [ ] ShellCheck passes on all scripts
- [ ] No TODO/FIXME comments for this release
- [ ] Dead code removed
- [ ] Debug statements removed
- [ ] Performance benchmarks acceptable

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Smoke tests pass
- [ ] Performance tests pass
- [ ] Security tests pass
- [ ] Manual testing completed
- [ ] Edge cases tested
- [ ] Error handling verified
- [ ] Regression tests pass

### Security
- [ ] Security scan clean (no P0/P1 vulnerabilities)
- [ ] No hardcoded secrets/credentials
- [ ] Dependencies up to date
- [ ] Known vulnerabilities documented
- [ ] Security audit completed (if major release)
- [ ] File permissions set correctly
- [ ] Input validation reviewed
- [ ] Authentication/authorization tested

### Git Status
- [ ] All changes committed
- [ ] No uncommitted changes
- [ ] No untracked critical files
- [ ] Branch up to date with main/master
- [ ] Merge conflicts resolved
- [ ] Git history is clean
- [ ] Commit messages follow conventions

---

## Phase 2: Build & Package

### Release Artifacts
- [ ] Release script executed successfully
- [ ] Tarball created: `claude-enhancer-vX.Y.Z.tar.gz`
- [ ] Checksums generated: `checksums.txt`
- [ ] GPG signature created (if available): `.asc` file
- [ ] Release notes generated: `RELEASE_NOTES.md`
- [ ] Artifact sizes reasonable
- [ ] Artifacts contain all necessary files
- [ ] Artifacts exclude development files

### Verification
- [ ] Tarball extracts without errors
- [ ] Extracted files have correct permissions
- [ ] Installation script works from tarball
- [ ] Healthcheck passes after installation
- [ ] CLI commands work after installation
- [ ] Documentation accessible after installation

### Checksums & Signatures
- [ ] SHA256 checksums verified
- [ ] GPG signature valid (if used)
- [ ] Checksums file format correct
- [ ] All artifacts checksummed

---

## Phase 3: Git Tagging

### Tag Creation
- [ ] Git tag created: `vX.Y.Z`
- [ ] Tag is annotated (not lightweight)
- [ ] Tag message includes release notes summary
- [ ] Tag points to correct commit
- [ ] Tag name follows semantic versioning
- [ ] Tag signed with GPG (if configured)

### Tag Verification
- [ ] Tag visible in `git tag -l`
- [ ] Tag annotation correct: `git show vX.Y.Z`
- [ ] Tag not yet pushed (wait for final approval)

---

## Phase 4: CI/CD Pipeline

### GitHub Actions
- [ ] `.github/workflows/release.yml` exists
- [ ] `.github/workflows/test.yml` exists
- [ ] Workflow syntax valid (YAML lint)
- [ ] Test workflow runs successfully
- [ ] Release workflow ready to trigger
- [ ] Required secrets configured
- [ ] Permissions set correctly

### CI Tests
- [ ] All CI jobs pass
- [ ] Unit test job passes
- [ ] Integration test job passes
- [ ] Performance test job passes
- [ ] Security test job passes
- [ ] Compatibility tests pass
- [ ] No flaky tests

---

## Phase 5: Release Execution

### Final Checks
- [ ] All previous checklist items completed
- [ ] Release notes reviewed by team
- [ ] Known issues documented
- [ ] Breaking changes clearly communicated
- [ ] Migration path clear for users
- [ ] Rollback plan prepared

### Push Release
- [ ] Git tag pushed: `git push origin vX.Y.Z`
- [ ] Release workflow triggered
- [ ] Release workflow completed successfully
- [ ] GitHub Release created automatically
- [ ] Release artifacts uploaded to GitHub
- [ ] Release notes visible on GitHub

### Verify GitHub Release
- [ ] Release visible at: `https://github.com/USER/REPO/releases`
- [ ] Release marked as latest
- [ ] Release not marked as pre-release (unless it is)
- [ ] Tarball downloadable
- [ ] Checksums downloadable
- [ ] Release notes formatted correctly
- [ ] Links in release notes work

---

## Phase 6: Post-Release Validation

### Installation Testing
- [ ] Install from GitHub release tarball
- [ ] Installation completes without errors
- [ ] Healthcheck passes after install
- [ ] Basic functionality works
- [ ] CLI commands respond correctly
- [ ] Documentation accessible

### Smoke Testing
- [ ] Test on clean environment
- [ ] Test on minimal system requirements
- [ ] Test basic workflow (start → next → validate)
- [ ] Test error handling
- [ ] Test help commands

### Monitoring
- [ ] Monitor GitHub release download stats
- [ ] Monitor for issue reports
- [ ] Check CI/CD pipeline status
- [ ] Review any automated alerts

---

## Phase 7: Communication

### Documentation Sites
- [ ] Update project website (if applicable)
- [ ] Update documentation site
- [ ] Update quick start guide
- [ ] Update installation instructions

### Announcements
- [ ] GitHub Discussions post created
- [ ] Social media announcement (if applicable)
- [ ] Blog post published (if applicable)
- [ ] Mailing list notified (if applicable)
- [ ] Community channels updated

### User Communication
- [ ] Breaking changes highlighted
- [ ] Migration guide referenced
- [ ] Known issues communicated
- [ ] Support channels available

---

## Phase 8: Cleanup

### Branch Management
- [ ] Release branch merged (if used)
- [ ] Old release branches deleted
- [ ] Feature branches cleaned up
- [ ] Git repository organized

### Issue Tracker
- [ ] Milestone closed for this release
- [ ] Issues tagged with release version
- [ ] Known issues documented
- [ ] Next milestone created

### Internal Updates
- [ ] Team notified of release
- [ ] Release notes archived
- [ ] Lessons learned documented
- [ ] Release metrics recorded

---

## Known Issues for This Release

Document any known issues that are acceptable for this release:

1. **Issue:** [Description]
   - **Impact:** [User impact]
   - **Workaround:** [How to work around]
   - **Fix planned:** [When will be fixed]

---

## Rollback Plan

If critical issues are discovered post-release:

1. **Immediate Actions:**
   - [ ] Mark release as pre-release on GitHub
   - [ ] Add warning to release notes
   - [ ] Post issue in announcements

2. **Rollback Steps:**
   - [ ] Document the critical issue
   - [ ] Create hotfix branch from previous stable tag
   - [ ] Apply fixes
   - [ ] Create new patch release
   - [ ] Update users via announcements

3. **Communication:**
   - [ ] Notify all users immediately
   - [ ] Provide rollback instructions
   - [ ] Estimate time for fix

---

## Sign-Off

### Release Manager
- **Name:** ___________
- **Date:** ___________
- **Signature:** ___________

### Technical Lead (if applicable)
- **Name:** ___________
- **Date:** ___________
- **Signature:** ___________

### QA Lead (if applicable)
- **Name:** ___________
- **Date:** ___________
- **Signature:** ___________

---

## Notes

Add any additional notes or context about this release:

```
[Space for release-specific notes]
```

---

## Checklist Summary

- **Total Items:** 150+
- **Completed:** ___ / ___
- **Completion Percentage:** ___%

**Release Status:** [ ] READY [ ] NOT READY [ ] RELEASED

---

**Last Updated:** 2025-10-09
**Template Version:** 1.0.0
