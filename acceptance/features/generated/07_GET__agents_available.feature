Feature: GET /agents/available
  As a client
  I want GET /agents/available
  So that API contract is honored

  @contract @generated
  Scenario: GET /agents/available returns 2xx per contract
    Given the API "/agents/available" exists per OpenAPI
    When I call "GET" "/agents/available" with valid payload
    Then the response status should be 200
    And the response should conform to schema "GET /agents/available"

  @contract @error
  Scenario: GET /agents/available handles errors gracefully
    Given the API "/agents/available" exists per OpenAPI
    When I call "GET" "/agents/available" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
