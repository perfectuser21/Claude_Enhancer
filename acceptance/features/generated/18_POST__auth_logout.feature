Feature: POST /auth/logout
  As a client
  I want POST /auth/logout
  So that API contract is honored

  @contract @generated
  Scenario: POST /auth/logout returns 2xx per contract
    Given the API "/auth/logout" exists per OpenAPI
    When I call "POST" "/auth/logout" with valid payload
    Then the response status should be 200
    And the response should conform to schema "POST /auth/logout"

  @contract @error
  Scenario: POST /auth/logout handles errors gracefully
    Given the API "/auth/logout" exists per OpenAPI
    When I call "POST" "/auth/logout" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
