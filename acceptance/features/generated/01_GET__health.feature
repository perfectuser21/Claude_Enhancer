Feature: GET /health
  As a client
  I want GET /health
  So that API contract is honored

  @contract @generated
  Scenario: GET /health returns 2xx per contract
    Given the API "/health" exists per OpenAPI
    When I call "GET" "/health" with valid payload
    Then the response status should be 200
    And the response should conform to schema "GET /health"

  @contract @error
  Scenario: GET /health handles errors gracefully
    Given the API "/health" exists per OpenAPI
    When I call "GET" "/health" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
