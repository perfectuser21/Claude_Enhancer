Feature: Phase Transition Validation
  As a developer following the 8-Phase workflow
  I want to progress through development phases with validation
  So that I maintain quality standards and follow a structured process

  Background:
    Given I am on a feature branch
    And the Claude Enhancer workflow is active

  @phase @transition @success
  Scenario: Successful phase progression with gates passed
    Given I am in phase P3 with all gates passed
    And I have committed all changes
    When I run "ce next"
    Then I should be in phase P4
    And the phase marker should be updated to "P4"
    And I should see next steps for P4 Testing phase
    And the transition should be logged

  @phase @transition @blocked
  Scenario: Blocked phase transition with failed gates
    Given I am in phase P3
    And gate 03 has not passed
    When I run "ce next"
    Then I should see error "Gate 03 not passed"
    And I should remain in phase P3
    And I should see details of failed gate checks
    And I should see remediation suggestions

  @phase @sequence
  Scenario: Enforce sequential phase progression
    Given I am in phase P1
    When I run "ce goto P4"
    Then I should see error "Cannot skip phases"
    And I should see "Must complete P2, P3 before P4"
    And I should remain in phase P1
    And the phase file should be unchanged

  @phase @gates @comprehensive
  Scenario: Validate all gate types in P4
    Given I am in phase P3 and ready to transition to P4
    When I run "ce next"
    Then the system should check the following gates:
      | Gate Type | Requirement | Status |
      | Code Quality | Score >= 85 | Checking |
      | Test Coverage | Coverage >= 80% | Checking |
      | Security | No secrets in code | Checking |
      | Documentation | All functions documented | Checking |
      | Signatures | All commits signed | Checking |
    And all gates must pass to proceed
    And failed gates should be listed with details

  @phase @p0
  Scenario: P0 Discovery phase validation
    Given I am in phase P0
    And I created spike documentation
    And I validated technical feasibility
    When I run "ce validate"
    Then the system should check:
      | Check | Description |
      | Spike exists | .workflow/spikes/<ticket>.md file present |
      | Feasibility | Technical feasibility documented |
      | Risks | Risks and dependencies identified |
      | Estimate | Work estimate provided |
    And validation report should be generated

  @phase @p1
  Scenario: P1 Planning phase requirements
    Given I am in phase P1
    When I run "ce validate"
    Then the system should verify:
      | Requirement | Check |
      | PLAN.md exists | File present in docs/ |
      | Task list | At least 5 tasks defined |
      | Architecture | Architecture section complete |
      | Affected files | List of files to modify |
      | Dependencies | External dependencies listed |
    And all requirements must be met to pass gate 01

  @phase @p3
  Scenario: P3 Implementation phase checks
    Given I am in phase P3
    And I have implemented core functionality
    When I run "ce validate"
    Then the system should check:
      | Check | Criteria |
      | Build | Code compiles without errors |
      | Basic tests | Core functionality works |
      | CHANGELOG | Updated with changes |
      | Commit count | At least 3 commits |
      | Code style | Passes linting |
    And gate 03 should pass if all checks succeed

  @phase @p4
  Scenario: P4 Testing phase comprehensive validation
    Given I am in phase P4
    When I run "ce validate"
    Then the following test types should be verified:
      | Test Type | Required Coverage | Status |
      | Unit tests | >= 80% | Pending |
      | Integration tests | >= 60% | Pending |
      | Edge cases | Critical paths | Pending |
      | Performance | Within budget | Pending |
    And BDD scenarios should be executed
    And test results should be reported

  @phase @p6
  Scenario: P6 Release phase readiness check
    Given I am in phase P6
    When I run "ce validate"
    Then the system should verify:
      | Deliverable | Status |
      | Documentation updated | Required |
      | CHANGELOG complete | Required |
      | Version bumped | Required |
      | Health checks pass | Required |
      | No TODO comments | Required |
      | All tests green | Required |
    And release readiness score should be calculated

  @phase @rollback
  Scenario: Rollback to previous phase
    Given I am in phase P4
    And I need to make changes to P3 code
    When I run "ce rollback P3"
    Then I should be moved back to phase P3
    And P4 artifacts should be preserved in backup
    And rollback should be logged with reason
    And I should see "Phase rolled back: P4 -> P3"

  @phase @history
  Scenario: Track phase transition history
    Given I progressed through phases P0 -> P1 -> P2 -> P3
    When I run "ce phase-history"
    Then I should see a timeline of phase transitions
    And each transition should show:
      | Field | Description |
      | From Phase | Previous phase |
      | To Phase | New phase |
      | Timestamp | When transition occurred |
      | Duration | Time spent in previous phase |
      | Gates Passed | List of passed gates |
    And total development time should be calculated

  @phase @parallel-support
  Scenario: Independent phase progression in multiple terminals
    Given terminal 1 is in phase P3 on "feature-auth"
    And terminal 2 is in phase P1 on "feature-payment"
    When I run "ce next" in terminal 1
    Then terminal 1 should move to P4
    And terminal 2 should remain in P1
    And each terminal should have independent phase tracking
    And phase files should not conflict

  @phase @skip-prevention
  Scenario: Prevent accidental phase skipping
    Given I am in phase P2
    And I manually edit .phase/current to "P5"
    When I run "ce validate"
    Then I should see error "Phase sequence violation detected"
    And the system should suggest fixing the phase marker
    And I should see "Expected P2 or P3, found P5"

  @phase @gate-override
  Scenario: Force phase transition with explicit confirmation
    Given I am in phase P3
    And gate 03 failed on code coverage (75% < 80%)
    When I run "ce next --force"
    Then I should see warning "Gate 03 failed, forcing transition"
    And I should be prompted "Are you sure? (yes/no)"
    When I type "yes"
    Then I should proceed to P4
    And the forced transition should be logged with reason
    And a warning flag should be set on the branch
