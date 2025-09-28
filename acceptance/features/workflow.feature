Feature: Workflow Management
  As a Claude Enhancer user
  I need to manage workflows through phases
  To ensure systematic development process

  @workflow @phases
  Scenario: Start P0 Discovery phase
    Given I have a new task "implement caching"
    When I start P0 Discovery phase
    Then spike directory should be created
    And technical exploration should begin
    And discovery results should be documented

  @workflow @phases
  Scenario: Progress from P1 to P2
    Given I completed P1 Planning phase
    When I move to P2 Skeleton phase
    Then directory structure should be created
    And architecture should be documented
    And P1 artifacts should be preserved

  @workflow @validation
  Scenario: Phase transition validation
    Given I am in P3 Implementation phase
    When I try to skip to P6 Release
    Then transition should be blocked
    And I should see validation error
    And required phases should be listed

  @workflow @rollback
  Scenario: Workflow rollback capability
    Given I am in P4 Testing phase
    And tests are failing
    When I request rollback to P3
    Then workflow should revert to P3
    And P4 artifacts should be preserved
    And rollback should be logged

  @workflow @monitoring
  Scenario: P7 Monitor phase activation
    Given I completed P6 Release phase
    When system enters P7 Monitor phase
    Then monitoring should be active
    And metrics should be collected
    And alerts should be configured
