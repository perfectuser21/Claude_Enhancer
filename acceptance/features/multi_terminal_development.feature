Feature: Multi-Terminal Parallel Development
  As a developer using AI assistants
  I want to develop multiple features in parallel across different terminals
  So that I can maximize productivity and reduce development time

  Background:
    Given I am in a Claude Enhancer project
    And the main branch is up to date
    And I have a clean working directory

  @multi-terminal @core
  Scenario: Start features in 3 terminals simultaneously
    Given I have 3 terminal sessions
    When I run "ce start login-feature" in terminal 1
    And I run "ce start payment-feature" in terminal 2
    And I run "ce start search-feature" in terminal 3
    Then terminal 1 should have session "t1" with branch matching "feature/P3-t.*-login-feature"
    And terminal 2 should have session "t2" with branch matching "feature/P3-t.*-payment-feature"
    And terminal 3 should have session "t3" with branch matching "feature/P3-t.*-search-feature"
    And all 3 sessions should be independent
    And each session should have its own session directory

  @multi-terminal @isolation
  Scenario: Each terminal maintains independent Phase state
    Given terminal 1 is on branch "feature/P3-t1-123-auth" in phase P3
    And terminal 2 is on branch "feature/P3-t2-456-payment" in phase P1
    When I run "ce next" in terminal 1
    Then terminal 1 should be in phase P4
    And terminal 2 should still be in phase P1
    And the phase files should be independent

  @multi-terminal @file-tracking
  Scenario: Track modified files per terminal session
    Given terminal 1 is working on "auth-feature"
    When I modify "src/auth/login.ts" in terminal 1
    And I modify "src/auth/register.ts" in terminal 1
    And I run "ce status" in terminal 1
    Then the status should show 2 modified files
    And the session manifest should list both files
    And terminal 2 should not see these modifications in its status

  @multi-terminal @concurrent-commits
  Scenario: Concurrent commits from different terminals
    Given terminal 1 is on "feature/P3-t1-auth" with 2 uncommitted files
    And terminal 2 is on "feature/P3-t2-payment" with 3 uncommitted files
    When I commit changes in terminal 1 with message "feat(auth): add login"
    And I commit changes in terminal 2 with message "feat(payment): add checkout"
    Then terminal 1 branch should have 1 new commit
    And terminal 2 branch should have 1 new commit
    And the commits should be on different branches
    And there should be no conflicts

  @multi-terminal @session-recovery
  Scenario: Resume terminal session after restart
    Given I started feature "user-profile" in terminal 1
    And I modified 3 files in the session
    And I close terminal 1
    When I reopen terminal 1
    And I run "ce status"
    Then the session should be restored
    And the modified file list should be preserved
    And the branch should still be checked out
    And the phase state should be intact

  @multi-terminal @terminal-identification
  Scenario: Automatic terminal ID assignment
    When I run "ce start feature-a" without specifying terminal ID
    Then the system should auto-assign a terminal ID matching "t[0-9]+"
    And the terminal ID should be unique
    And the session directory should use the terminal ID
    And subsequent commands should use the same terminal ID

  @multi-terminal @parallel-phases
  Scenario: Different features in different phases simultaneously
    Given terminal 1 completed P1 for "auth-feature"
    And terminal 2 is in P3 for "payment-feature"
    And terminal 3 is in P5 for "search-feature"
    When I run "ce status --verbose"
    Then I should see terminal 1 in phase P1
    And I should see terminal 2 in phase P3
    And I should see terminal 3 in phase P5
    And each terminal should show correct phase-specific next steps
