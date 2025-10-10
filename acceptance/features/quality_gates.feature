Feature: Quality Gate Validation
  As a quality-focused developer
  I want automated quality checks at each phase
  So that code quality is maintained throughout development

  Background:
    Given I am working on a feature branch
    And quality gates are configured

  @quality @comprehensive
  Scenario: Validate all gate types
    Given I have a feature branch with changes
    When I run "ce validate"
    Then the system should check score (>= 85)
    And the system should check coverage (>= 80%)
    And the system should check security (no secrets)
    And the system should check signatures (all valid)
    And I should see a comprehensive quality report

  @quality @score
  Scenario: Code quality score calculation
    Given I have implemented a feature
    When I run "ce validate --quality"
    Then the quality score should be calculated based on:
      | Factor | Weight | Criteria |
      | Complexity | 25% | Cyclomatic complexity < 10 |
      | Duplication | 20% | Code duplication < 3% |
      | Documentation | 20% | All public APIs documented |
      | Test Coverage | 25% | Coverage >= 80% |
      | Code Style | 10% | Linting passes |
    And total score should be >= 85 to pass
    And detailed breakdown should be shown

  @quality @coverage
  Scenario: Test coverage validation
    Given I have written tests for my feature
    When I run "ce validate --coverage"
    Then coverage should be measured for:
      | Metric | Threshold |
      | Line coverage | >= 80% |
      | Branch coverage | >= 75% |
      | Function coverage | >= 90% |
      | Statement coverage | >= 80% |
    And uncovered lines should be reported
    And critical paths must have 100% coverage

  @quality @security
  Scenario: Security checks for sensitive data
    Given my code contains potential secrets
    When I run "ce validate --security"
    Then the system should scan for:
      | Pattern | Severity |
      | API keys | CRITICAL |
      | Passwords | CRITICAL |
      | Private keys | CRITICAL |
      | Access tokens | HIGH |
      | Database URLs | HIGH |
      | Email addresses | LOW |
    And any findings should be reported
    And CRITICAL findings should block progression

  @quality @secrets-detection
  Scenario: Detect hardcoded secrets in code
    Given I have code with hardcoded credentials
    """
    const apiKey = "sk_live_1234567890abcdef";
    const dbUrl = "mongodb://user:password@localhost/db";
    """
    When I run "ce validate --security"
    Then I should see error "Security violation: Hardcoded API key detected"
    And I should see error "Security violation: Database credentials in code"
    And the validation should fail
    And suggested fixes should be provided

  @quality @signatures
  Scenario: Verify all commits are signed
    Given I have 5 commits on my feature branch
    And 4 commits are GPG signed
    And 1 commit is not signed
    When I run "ce validate --signatures"
    Then I should see warning "1 unsigned commit found"
    And the unsigned commit hash should be listed
    And I should be advised to sign the commit
    And the gate should fail

  @quality @documentation
  Scenario: Check documentation completeness
    Given I have 10 public functions
    And 8 functions have JSDoc comments
    And 2 functions are undocumented
    When I run "ce validate --docs"
    Then I should see "Documentation coverage: 80%"
    And I should see list of undocumented functions
    And I should see "Required: 100%"
    And the check should fail

  @quality @linting
  Scenario: Code style and linting validation
    Given my code has style violations
    When I run "ce validate --lint"
    Then eslint should be executed
    And violations should be categorized:
      | Type | Count | Fixable |
      | Errors | 0 | - |
      | Warnings | 5 | 3 |
      | Info | 2 | 2 |
    And errors should block progression
    And fixable issues should be auto-fixed if requested

  @quality @performance
  Scenario: Performance budget validation
    Given I have performance budgets defined
    When I run "ce validate --performance"
    Then the following metrics should be checked:
      | Metric | Budget | Actual | Status |
      | Bundle size | < 500KB | 480KB | PASS |
      | API response | < 200ms | 150ms | PASS |
      | Memory usage | < 100MB | 95MB | PASS |
      | CPU usage | < 50% | 45% | PASS |
    And all metrics must be within budget
    And performance report should be generated

  @quality @complexity
  Scenario: Code complexity analysis
    Given I have functions with varying complexity
    When I run "ce validate --complexity"
    Then cyclomatic complexity should be measured
    And functions with complexity > 10 should be flagged
    And I should see:
      | Function | Complexity | Status |
      | processPayment() | 15 | FAIL - Too complex |
      | validateUser() | 8 | PASS |
      | formatData() | 5 | PASS |
    And refactoring suggestions should be provided

  @quality @dependencies
  Scenario: Dependency vulnerability scanning
    Given my project has npm dependencies
    When I run "ce validate --security"
    Then npm audit should be executed
    And vulnerabilities should be categorized:
      | Severity | Count | Action |
      | Critical | 0 | - |
      | High | 0 | - |
      | Moderate | 2 | Review |
      | Low | 5 | Monitor |
    And Critical/High vulnerabilities should block progression
    And update recommendations should be provided

  @quality @git-hygiene
  Scenario: Git commit hygiene validation
    Given I have commits on my feature branch
    When I run "ce validate --git"
    Then commit messages should be checked for:
      | Rule | Description |
      | Format | Follows conventional commits |
      | Length | Subject <= 72 characters |
      | Body | Has detailed explanation |
      | Signed | GPG signature present |
      | References | Links to issue/ticket |
    And violations should be reported
    And commit hygiene score should be calculated

  @quality @aggregated
  Scenario: Aggregated quality gate report
    Given I completed all development work
    When I run "ce validate --all"
    Then I should see a comprehensive report:
      """
      ╔═══════════════════════════════════════╗
      ║   Quality Gate Validation Report     ║
      ╠═══════════════════════════════════════╣
      ║ Code Quality Score    : 92/100  ✓    ║
      ║ Test Coverage         : 85%     ✓    ║
      ║ Security Scan         : PASS    ✓    ║
      ║ Commit Signatures     : 100%    ✓    ║
      ║ Documentation         : 95%     ✓    ║
      ║ Performance Budget    : PASS    ✓    ║
      ║ Complexity            : PASS    ✓    ║
      ║ Dependencies          : PASS    ✓    ║
      ╠═══════════════════════════════════════╣
      ║ Overall Status        : PASSED  ✓    ║
      ╚═══════════════════════════════════════╝
      """
    And I should be allowed to proceed to next phase

  @quality @custom-gates
  Scenario: Custom quality gate configuration
    Given I have custom quality gates in .workflow/gates.yml
    """
    gates:
      - name: api_contract
        check: openapi_validation
        required: true
      - name: i18n_complete
        check: translation_coverage >= 100%
        required: true
    """
    When I run "ce validate"
    Then custom gates should be executed
    And openapi.yaml should be validated
    And translation files should be checked
    And all custom gates must pass
