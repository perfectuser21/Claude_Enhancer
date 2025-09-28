Feature: GET /metrics
  As a client
  I want GET /metrics
  So that API contract is honored

  @contract @generated
  Scenario: GET /metrics returns 2xx per contract
    Given the API "/metrics" exists per OpenAPI
    When I call "GET" "/metrics" with valid payload
    Then the response status should be 200
    And the response should conform to schema "GET /metrics"

  @contract @error
  Scenario: GET /metrics handles errors gracefully
    Given the API "/metrics" exists per OpenAPI
    When I call "GET" "/metrics" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
