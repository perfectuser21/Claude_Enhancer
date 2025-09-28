Feature: GET /sessions
  As a client
  I want GET /sessions
  So that API contract is honored

  @contract @generated
  Scenario: GET /sessions returns 2xx per contract
    Given the API "/sessions" exists per OpenAPI
    When I call "GET" "/sessions" with valid payload
    Then the response status should be 200
    And the response should conform to schema "GET /sessions"

  @contract @error
  Scenario: GET /sessions handles errors gracefully
    Given the API "/sessions" exists per OpenAPI
    When I call "GET" "/sessions" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
