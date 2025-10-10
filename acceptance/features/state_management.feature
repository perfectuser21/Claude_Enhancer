Feature: Session State Management
  As a developer
  I want my development state persisted across sessions
  So that I can resume work seamlessly after interruptions

  Background:
    Given I am working on a Claude Enhancer project
    And session state persistence is enabled

  @state @persistence
  Scenario: Save and restore session state
    Given I start a feature "test-feature"
    And I modify 3 files:
      | File |
      | src/app.ts |
      | src/utils.ts |
      | test/app.test.ts |
    And I am in phase P3
    When I close the terminal and reopen
    And I run "ce status"
    Then the session should be restored
    And the file list should be preserved
    And the current phase should be P3
    And the branch should still be checked out

  @state @manifest
  Scenario: Session manifest structure
    Given I created a feature session
    When I check the session manifest
    Then it should contain:
      | Field | Type | Required |
      | session_id | string | yes |
      | terminal_id | string | yes |
      | feature_name | string | yes |
      | branch_name | string | yes |
      | phase | string | yes |
      | status | string | yes |
      | created_at | timestamp | yes |
      | updated_at | timestamp | yes |
      | commits | array | yes |
      | gates_passed | array | yes |
      | modified_files | array | no |
      | description | string | no |
    And the manifest should be valid YAML

  @state @updates
  Scenario: Automatic state updates during development
    Given I have an active session
    When I commit changes
    Then the session manifest should be updated with commit hash

    When I pass a quality gate
    Then the gates_passed array should be updated

    When I move to next phase
    Then the phase field should be updated
    And the updated_at timestamp should be refreshed

  @state @multi-session
  Scenario: Manage multiple concurrent sessions
    Given I have 3 active sessions:
      | Session | Terminal | Branch | Phase |
      | s1 | t1 | feature/P3-t1-auth | P3 |
      | s2 | t2 | feature/P3-t2-payment | P4 |
      | s3 | t3 | feature/P3-t3-search | P1 |
    When I run "ce sessions"
    Then all 3 sessions should be listed
    And each session should show its current state
    And I should be able to switch between sessions
    And session files should not conflict

  @state @recovery
  Scenario: Recover from corrupted session state
    Given I have a session with corrupted manifest
    When I run "ce status"
    Then I should see warning "Session state corrupted"
    And I should be offered recovery options:
      | Option | Description |
      | Rebuild | Rebuild from git history |
      | Reset | Reset to default state |
      | Manual | Edit manifest manually |
    When I choose "Rebuild"
    Then the session should be reconstructed from git data
    And I should see "Session recovered successfully"

  @state @phase-tracking
  Scenario: Track phase transition history in state
    Given I progressed through phases P0 -> P1 -> P2 -> P3
    When I check the session state
    Then phase_history should contain:
      | Phase | Started | Completed | Duration |
      | P0 | 08:00 | 08:30 | 30m |
      | P1 | 08:30 | 09:10 | 40m |
      | P2 | 09:10 | 09:30 | 20m |
      | P3 | 09:30 | - | ongoing |
    And total time should be calculated
    And average phase duration should be shown

  @state @file-tracking
  Scenario: Track modified files in session state
    Given I am working on a feature
    When I modify "src/auth.ts"
    Then it should be added to modified_files array

    When I stage the file
    Then it should be marked as staged in state

    When I commit the file
    Then it should move to committed_files array
    And the commit hash should be recorded

  @state @checkpoint
  Scenario: Create state checkpoints
    Given I completed P3 phase
    When I run "ce checkpoint 'P3 complete'"
    Then a checkpoint should be created
    And the checkpoint should include:
      | Data |
      | Full session state |
      | Git commit hash |
      | File snapshot |
      | Timestamp |
      | Description |
    And I should be able to restore to this checkpoint

  @state @restore
  Scenario: Restore session to previous checkpoint
    Given I have checkpoints at P2 and P3
    And I am currently in P4
    When I run "ce restore P3"
    Then the session should be restored to P3 state
    And the working directory should be reset
    And the phase marker should be P3
    And P4 changes should be stashed
    And I should see "Restored to checkpoint: P3 complete"

  @state @conflict-resolution
  Scenario: Handle state conflicts between terminals
    Given terminal 1 has session state at version 5
    And terminal 2 has session state at version 4
    When terminal 2 tries to update the state
    Then a conflict should be detected
    And I should see "State conflict detected"
    And I should be shown the differences
    And I should choose conflict resolution strategy:
      | Strategy | Description |
      | Merge | Merge both versions |
      | Ours | Keep terminal 2 version |
      | Theirs | Use terminal 1 version |

  @state @synchronization
  Scenario: Synchronize state across terminals
    Given I have session state in terminal 1
    When I open terminal 2 for the same session
    Then terminal 2 should load the latest state
    And both terminals should be synchronized

    When I make changes in terminal 1
    Then terminal 2 should be notified
    And terminal 2 should be able to refresh state

  @state @cleanup
  Scenario: Clean up old session states
    Given I have 10 completed sessions
    And 5 sessions are older than 30 days
    When I run "ce cleanup-state --older-than 30d"
    Then the 5 old sessions should be archived
    And active sessions should be preserved
    And archived states should be moved to .workflow/state/archive/
    And I should see "Archived 5 old session states"

  @state @export
  Scenario: Export session state for sharing
    Given I have a session with full state
    When I run "ce export-state --format json"
    Then a JSON file should be created with all state data
    And the export should be human-readable
    And sensitive data should be redacted
    And the file can be imported by another user

  @state @import
  Scenario: Import session state from file
    Given I have an exported state file
    When I run "ce import-state session-backup.json"
    Then the session should be recreated
    And all metadata should be restored
    And the branch should be created if needed
    And I should see "Session imported successfully"

  @state @integrity
  Scenario: Validate state file integrity
    Given I have a session state file
    When I run "ce validate-state"
    Then the state structure should be validated
    And required fields should be checked
    And timestamps should be validated
    And cross-references should be verified
    And I should see validation results

  @state @migration
  Scenario: Migrate state format to newer version
    Given I have state files in format v1
    And the system now uses format v2
    When I run "ce migrate-state"
    Then all state files should be upgraded to v2
    And old formats should be preserved as backups
    And the migration should be logged
    And I should see "Migrated 3 state files to v2"
