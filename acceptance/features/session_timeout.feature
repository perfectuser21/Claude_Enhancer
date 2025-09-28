Feature: Session Timeout Management
  As a Claude Enhancer user
  I need the system to handle session timeouts properly
  To ensure balance between security and user experience

  Background:
    Given the system is initialized
    And session timeout is set to 30 minutes

  @security @session
  Scenario: Auto logout after session timeout
    Given user "test@example.com" is logged in
    And current session is created
    When waiting 31 minutes without activity
    Then session should expire
    And user should be logged out automatically
    And system should return 401 unauthorized

  @session @recovery
  Scenario: Context recovery after session timeout and re-login
    Given user "test@example.com" is editing a task
    And workflow is in phase "P3"
    And 5 agents have been selected
    When session times out
    And user logs in again
    Then system should restore previous workflow state
    And current phase should still be "P3"
    And agent selection should be preserved
    And unsaved changes should have recovery prompt

  @session @extension
  Scenario: Active user session auto-extension
    Given user "test@example.com" is logged in
    And session will expire in 5 minutes
    When user makes any API call
    Then session should be extended by 30 minutes
    And user operations should not be interrupted

  @session @warning
  Scenario: Session expiring soon warning
    Given user "test@example.com" is logged in
    And session will expire in 2 minutes
    When system detects imminent expiry
    Then countdown warning should be displayed
    And "Extend Session" option should be provided
    And "Save and Logout" option should be provided

  @session @concurrent
  Scenario: Multi-device session management
    Given user "test@example.com" is logged in on device A
    When same user logs in on device B
    Then both sessions should be managed independently
    And each session has independent timeout timer
    And user can view all active sessions
    And can choose to terminate specific sessions