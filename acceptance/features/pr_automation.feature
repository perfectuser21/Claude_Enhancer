Feature: Pull Request Automation
  As a developer
  I want to create PRs with one command
  So that I can quickly publish features with proper metadata

  Background:
    Given I am on a feature branch
    And GitHub CLI is installed and authenticated
    And my feature is ready for review

  @pr @creation
  Scenario: Create PR with GitHub CLI
    Given I have a feature branch "feature/P3-t1-user-auth"
    And all quality gates passed
    When I run "ce publish"
    Then a PR should be created with title matching the branch
    And the PR description should include quality metrics
    And the PR should be in draft mode
    And I should see the PR URL
    And the PR should be linked to the branch

  @pr @metadata
  Scenario: PR includes comprehensive metadata
    Given I completed feature "payment-integration"
    When I run "ce publish"
    Then the PR should include:
      | Section | Content |
      | Title | feat: payment-integration |
      | Feature Description | From PLAN.md summary |
      | Changes List | Git commit history |
      | Test Results | Coverage and test status |
      | Quality Metrics | Code quality score |
      | Phase Completed | P6 - Release Ready |
      | Affected Files | List of modified files |
      | Dependencies | Related PRs or features |
    And the PR should have labels based on content
    And the PR should request reviewers automatically

  @pr @draft-mode
  Scenario: Create draft PR for work in progress
    Given I am in phase P4 (not ready for final review)
    When I run "ce publish --draft"
    Then a draft PR should be created
    And the PR should be marked as "Work in Progress"
    And CI checks should still run
    And the PR should not request reviewers yet
    And I should see "Draft PR created successfully"

  @pr @ready-mode
  Scenario: Convert draft to ready for review
    Given I have a draft PR for my feature
    And I completed all phases through P6
    When I run "ce publish --ready"
    Then the PR should be marked as "Ready for review"
    And reviewers should be automatically assigned
    And team should be notified
    And the PR should move out of draft state

  @pr @quality-report
  Scenario: Include quality gate results in PR description
    Given I have all quality gates passed
    When I run "ce publish"
    Then the PR description should include:
      """
      ## Quality Gate Results

      ✅ Code Quality Score: 92/100
      ✅ Test Coverage: 85%
      ✅ Security Scan: PASSED
      ✅ All Commits Signed: YES
      ✅ Documentation: Complete
      ✅ Performance: Within Budget

      All quality gates passed ✓
      """
    And CI status badges should be included
    And test reports should be linked

  @pr @commit-list
  Scenario: Generate formatted commit list
    Given my feature has 8 commits
    When I run "ce publish"
    Then the PR should list commits in format:
      """
      ## Commits (8)

      - feat(auth): implement login endpoint [P3]
      - test(auth): add login tests [P4]
      - docs(auth): update API documentation [P6]
      - fix(auth): handle edge cases [P4]
      - refactor(auth): improve error handling [P3]
      - chore(auth): update dependencies [P3]
      - test(auth): add integration tests [P4]
      - docs(auth): add usage examples [P6]
      """
    And commits should be grouped by type
    And phase markers should be visible

  @pr @affected-files
  Scenario: List affected files with categorization
    Given my feature modified 12 files
    When I run "ce publish"
    Then the PR should categorize files:
      | Category | Files |
      | Source Code | 5 |
      | Tests | 4 |
      | Documentation | 2 |
      | Configuration | 1 |
    And file diff stats should be shown
    And high-impact files should be highlighted

  @pr @auto-labels
  Scenario: Automatic label assignment
    Given my feature involves authentication and security
    When I run "ce publish"
    Then the PR should be labeled with:
      | Label | Reason |
      | enhancement | New feature |
      | security | Security-related changes |
      | needs-review | Ready for review |
      | size:medium | 8 commits, 12 files |
    And labels should be based on analysis
    And custom labels from config should be applied

  @pr @reviewer-assignment
  Scenario: Smart reviewer assignment
    Given I configured code owners
    And my changes affect auth and payment modules
    When I run "ce publish"
    Then reviewers should be assigned:
      | Module | Reviewer |
      | auth | @security-team |
      | payment | @payment-expert |
      | tests | @qa-lead |
    And all owners of affected code should be notified
    And at least 1 approval should be required

  @pr @ci-trigger
  Scenario: Trigger CI/CD pipeline on PR creation
    Given I created a PR with "ce publish"
    When the PR is created
    Then GitHub Actions should be triggered
    And the following jobs should run:
      | Job | Purpose |
      | lint | Code style check |
      | test | Run all tests |
      | build | Verify build |
      | security | Security scan |
      | quality | Quality gates |
    And CI status should be visible in PR
    And I should be notified of CI results

  @pr @template
  Scenario: Use PR template with placeholders
    Given I have a PR template configured
    When I run "ce publish"
    Then the template should be populated with:
      | Placeholder | Replacement |
      | {{feature}} | Feature name from branch |
      | {{phase}} | Current phase |
      | {{commits}} | Commit count |
      | {{files}} | Modified file count |
      | {{coverage}} | Test coverage % |
      | {{quality}} | Quality score |
    And manual sections should remain for user input
    And checklist items should be pre-checked if applicable

  @pr @conflict-check
  Scenario: Check for conflicts before creating PR
    Given my branch has conflicts with main
    When I run "ce publish"
    Then I should see error "Cannot create PR: conflicts detected"
    And conflicting files should be listed
    And I should see resolution instructions
    And the PR should not be created
    And I should be advised to rebase on main

  @pr @dependency-tracking
  Scenario: Link dependent PRs
    Given my feature depends on PR #123
    When I run "ce publish --depends-on 123"
    Then the PR description should include:
      """
      ## Dependencies

      🔗 Depends on: #123
      ⚠️ Do not merge until #123 is merged
      """
    And the PR should be marked as blocked
    And automation should prevent merging until dependency is resolved

  @pr @auto-merge
  Scenario: Enable auto-merge after CI passes
    Given I created a PR
    And I trust the CI validation
    When I run "ce publish --auto-merge"
    Then auto-merge should be enabled
    And the PR should merge automatically when:
      | Condition |
      | All CI checks pass |
      | Required reviews approved |
      | No conflicts |
      | Not in draft mode |
    And I should see "Auto-merge enabled ✓"

  @pr @rollback-capability
  Scenario: Create rollback PR for failed release
    Given PR #456 was merged but caused issues
    When I run "ce rollback 456"
    Then a rollback PR should be created
    And the PR title should be "Rollback: PR #456"
    And the PR should revert the merge commit
    And the PR should be marked as urgent
    And the PR should link to the original PR
    And auto-merge should be disabled for safety
