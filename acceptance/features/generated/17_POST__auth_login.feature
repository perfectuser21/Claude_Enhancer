Feature: POST /auth/login
  As a client
  I want POST /auth/login
  So that API contract is honored

  @contract @generated
  Scenario: POST /auth/login returns 2xx per contract
    Given the API "/auth/login" exists per OpenAPI
    When I call "POST" "/auth/login" with valid payload
    Then the response status should be 200
    And the response should conform to schema "POST /auth/login"

  @contract @error
  Scenario: POST /auth/login handles errors gracefully
    Given the API "/auth/login" exists per OpenAPI
    When I call "POST" "/auth/login" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
