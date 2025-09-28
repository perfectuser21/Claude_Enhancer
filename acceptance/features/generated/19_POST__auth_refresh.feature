Feature: POST /auth/refresh
  As a client
  I want POST /auth/refresh
  So that API contract is honored

  @contract @generated
  Scenario: POST /auth/refresh returns 2xx per contract
    Given the API "/auth/refresh" exists per OpenAPI
    When I call "POST" "/auth/refresh" with valid payload
    Then the response status should be 200
    And the response should conform to schema "POST /auth/refresh"

  @contract @error
  Scenario: POST /auth/refresh handles errors gracefully
    Given the API "/auth/refresh" exists per OpenAPI
    When I call "POST" "/auth/refresh" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
