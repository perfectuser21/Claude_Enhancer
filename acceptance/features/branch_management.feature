Feature: Automated Branch Management
  As a developer
  I want branches automatically created and managed
  So that I follow naming conventions and maintain clean git history

  Background:
    Given I am in a Claude Enhancer project
    And I am on the main branch
    And my working directory is clean

  @branch @creation @naming
  Scenario: Create branch with standard naming convention
    Given I am on the main branch
    When I run "ce start user-authentication"
    Then a branch should be created matching "feature/P3-t.*-user-authentication"
    And the branch should be checked out
    And a session state file should be created
    And the phase should be initialized to P3

  @branch @naming @validation
  Scenario: Validate branch name format
    When I run "ce start login-feature"
    Then the branch name should follow format "feature/P<phase>-t<terminal>-<timestamp>-<feature>"
    And the feature name should be lowercase with hyphens
    And the branch should include phase marker
    And the branch should include terminal ID
    And the branch should be unique

  @branch @creation @phases
  Scenario: Create branch in different starting phases
    When I run "ce start auth-system --phase P0"
    Then a branch should be created with "P0" in the name
    And the phase marker should be set to P0

    When I run "ce start payment --phase P1"
    Then a branch should be created with "P1" in the name
    And the phase marker should be set to P1

  @branch @validation @name-rules
  Scenario: Enforce feature name validation rules
    When I run "ce start a"
    Then I should see error "Feature name must be 2-50 characters"

    When I run "ce start UserAuthentication"
    Then I should see error "Feature name must contain only lowercase letters, numbers, and hyphens"

    When I run "ce start -invalid-name"
    Then I should see error "Must start and end with alphanumeric character"

    When I run "ce start this-is-a-very-long-feature-name-that-exceeds-fifty-characters-limit"
    Then I should see error "Feature name must be 2-50 characters"

  @branch @duplicate
  Scenario: Prevent duplicate branch creation
    Given I created branch "feature/P3-t1-123-auth"
    When I try to run "ce start auth" with same terminal ID
    Then I should see error "Branch already exists"
    And I should be offered to switch to existing branch
    And no new branch should be created

  @branch @switching
  Scenario: Switch between feature branches
    Given I have branches:
      | Branch |
      | feature/P3-t1-auth |
      | feature/P3-t2-payment |
      | feature/P3-t3-search |
    When I run "ce switch t2"
    Then I should be on branch "feature/P3-t2-payment"
    And the session context should be loaded
    And the phase should be restored
    And modified files should be preserved

  @branch @listing
  Scenario: List active feature branches
    Given I have 3 active feature branches
    When I run "ce branches"
    Then I should see a table with:
      | Branch | Terminal | Phase | Age | Status |
      | feature/P3-t1-auth | t1 | P3 | 2h | active |
      | feature/P3-t2-payment | t2 | P4 | 1h | active |
      | feature/P3-t3-search | t3 | P1 | 30m | active |
    And branches should be sorted by age
    And current branch should be highlighted

  @branch @cleanup
  Scenario: Clean up merged branches
    Given I have merged branches:
      | Branch | Merged At |
      | feature/P3-t1-old-feature | 2 days ago |
      | feature/P3-t2-done-feature | 1 day ago |
    When I run "ce cleanup"
    Then I should see list of merged branches
    And I should be prompted "Delete 2 merged branches?"
    When I confirm
    Then the branches should be deleted locally and remotely
    And session directories should be archived
    And cleanup should be logged

  @branch @protection
  Scenario: Prevent direct commits to main branch
    Given I am on the main branch
    When I try to commit changes directly
    Then the pre-commit hook should block the commit
    And I should see error "Direct commits to main are not allowed"
    And I should be advised to create a feature branch
    And the commit should not be created

  @branch @sync
  Scenario: Sync branch with remote
    Given I have local branch "feature/P3-t1-auth"
    And the remote has new commits
    When I run "ce sync"
    Then the branch should be pulled from remote
    And any conflicts should be detected
    And I should see sync status
    And the session state should be updated

  @branch @rebase
  Scenario: Rebase feature branch on main
    Given I am on "feature/P3-t1-auth"
    And main has advanced by 5 commits
    When I run "ce rebase"
    Then the branch should be rebased on main
    And commit history should be updated
    And conflicts should be reported if any
    And the rebase should be logged

  @branch @archival
  Scenario: Archive stale branches
    Given I have a branch inactive for 30 days
    When I run "ce cleanup --stale"
    Then the stale branch should be identified
    And I should be prompted to archive it
    When I confirm
    Then the branch should be archived to refs/archive/
    And the session state should be preserved
    And the branch should be removed from active list

  @branch @naming-templates
  Scenario: Use custom branch naming templates
    Given I configured custom template "feature/P<phase>-<user>-<feature>"
    When I run "ce start login"
    Then the branch should match "feature/P3-john-login"
    And the template variables should be substituted
    And the naming convention should be validated

  @branch @terminal-isolation
  Scenario: Each terminal uses unique branch identifiers
    When I run "ce start auth" in terminal 1
    And I run "ce start auth" in terminal 2
    Then terminal 1 branch should include "t1"
    And terminal 2 branch should include "t2"
    And both branches should coexist
    And session files should be separate

  @branch @metadata
  Scenario: Branch metadata tracking
    Given I created branch "feature/P3-t1-auth"
    When I run "ce branch-info"
    Then I should see metadata:
      | Field | Value |
      | Created | 2025-10-09 08:30:00 |
      | Creator | john@example.com |
      | Base branch | main |
      | Current phase | P3 |
      | Commits | 8 |
      | Modified files | 12 |
      | Last activity | 5 minutes ago |
    And metadata should be stored in session manifest
