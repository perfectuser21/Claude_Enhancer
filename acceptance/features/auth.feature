Feature: Authentication and Authorization
  As a Claude Enhancer user
  I need secure authentication and authorization
  To protect my workflow and data

  @auth @security
  Scenario: User login with valid credentials
    Given I have valid credentials
    When I login with email "user@example.com" and password "secure123"
    Then I should receive a JWT token
    And token should be valid for 24 hours

  @auth @security
  Scenario: User login with invalid credentials
    Given I have invalid credentials
    When I login with email "user@example.com" and password "wrong"
    Then I should receive 401 unauthorized error
    And no token should be generated

  @auth @rbac
  Scenario: Role-based access control
    Given I am logged in as "developer"
    When I try to access admin endpoints
    Then I should receive 403 forbidden error
    And access should be logged

  @auth @mfa
  Scenario: Two-factor authentication
    Given I have 2FA enabled
    When I login with correct credentials
    Then I should be prompted for 2FA code
    And login succeeds only with valid code

  @auth @token
  Scenario: Token refresh mechanism
    Given I have an expiring token
    When I request token refresh
    Then I should receive new token
    And old token should be invalidated
