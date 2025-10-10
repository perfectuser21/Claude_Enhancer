Feature: Cross-Terminal Conflict Detection
  As a developer working on multiple features
  I want to be warned when terminals modify the same files
  So that I can avoid merge conflicts and coordinate changes

  Background:
    Given I am in a Claude Enhancer project
    And I have multiple active terminal sessions

  @conflict @detection
  Scenario: Detect file overlap between terminals
    Given terminal 1 is working on "auth-feature" modifying ["src/auth.js", "src/user.js"]
    And terminal 2 is working on "profile-feature" modifying ["src/user.js", "src/profile.js"]
    When I run "ce status" in terminal 1
    Then I should see a warning "Conflict detected with terminal t2 on src/user.js"
    And the warning should suggest coordination
    And the conflicting file should be highlighted

  @conflict @prevention
  Scenario: Prevent concurrent modifications to shared configuration
    Given terminal 1 is modifying "package.json"
    When terminal 2 tries to modify "package.json"
    Then terminal 2 should be blocked
    And I should see error "File package.json is being modified by terminal t1"
    And I should be advised to wait or coordinate

  @conflict @analysis
  Scenario: Analyze potential merge conflicts before push
    Given terminal 1 completed feature "auth" modifying ["src/auth.ts", "src/app.ts"]
    And terminal 2 completed feature "logging" modifying ["src/app.ts", "src/logger.ts"]
    And feature "auth" is already merged to main
    When I run "ce publish" in terminal 2
    Then the system should detect potential conflict on "src/app.ts"
    And I should see a conflict analysis report
    And I should be prompted to resolve conflicts before publishing

  @conflict @severity
  Scenario: Classify conflict severity levels
    Given terminal 1 modified "README.md"
    And terminal 2 modified "README.md"
    When I run "ce conflicts"
    Then the conflict should be classified as "LOW" severity
    And I should see "Documentation file conflict - easy to resolve"

    When terminal 1 modified "src/core/engine.ts"
    And terminal 2 modified "src/core/engine.ts"
    Then the conflict should be classified as "HIGH" severity
    And I should see "Core logic conflict - requires careful review"

  @conflict @resolution
  Scenario: Suggest conflict resolution strategies
    Given terminal 1 and terminal 2 both modified "utils/helpers.ts"
    When I run "ce conflicts --verbose"
    Then I should see conflict details with line numbers
    And I should see suggested resolution strategies:
      | Strategy | Description |
      | Sequential | Merge terminal 1 first, then rebase terminal 2 |
      | Manual merge | Use git mergetool to resolve conflicts |
      | Split file | Refactor into separate files to avoid overlap |
    And I should see recommended strategy based on conflict complexity

  @conflict @cross-branch
  Scenario: Detect conflicts with main branch
    Given terminal 1 is on "feature/P3-t1-auth"
    And main branch has commits modifying "src/auth.ts"
    When I run "ce validate" in terminal 1
    Then I should see "Conflict with main branch detected"
    And I should see number of conflicting commits
    And I should be advised to rebase on main

  @conflict @multi-file
  Scenario: Track conflicts across multiple file modifications
    Given terminal 1 working on "feature-a" modified 5 files
    And terminal 2 working on "feature-b" modified 8 files
    And 3 files overlap between the features
    When I run "ce status --conflicts"
    Then I should see a conflict matrix showing:
      | Terminal | Feature | Files Modified | Conflicts |
      | t1 | feature-a | 5 | 3 |
      | t2 | feature-b | 8 | 3 |
    And I should see list of 3 overlapping files
    And each file should show which terminals are modifying it

  @conflict @real-time
  Scenario: Real-time conflict notification
    Given terminal 1 is editing "src/api.ts"
    And terminal 2 starts editing "src/api.ts"
    When the conflict is detected
    Then terminal 2 should show immediate warning
    And terminal 1 should be notified of concurrent edit
    And both terminals should show "CONCURRENT_EDIT" status
    And a conflict log entry should be created

  @conflict @safe-zones
  Scenario: No conflicts for isolated feature directories
    Given terminal 1 works on "features/auth/*" files
    And terminal 2 works on "features/payment/*" files
    And terminal 3 works on "features/search/*" files
    When I run "ce conflicts"
    Then I should see "No conflicts detected"
    And I should see "All features in isolated directories"
    And confidence score should be 100%
