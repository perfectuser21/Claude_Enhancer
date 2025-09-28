Feature: GET /slo
  As a client
  I want GET /slo
  So that API contract is honored

  @contract @generated
  Scenario: GET /slo returns 2xx per contract
    Given the API "/slo" exists per OpenAPI
    When I call "GET" "/slo" with valid payload
    Then the response status should be 200
    And the response should conform to schema "GET /slo"

  @contract @error
  Scenario: GET /slo handles errors gracefully
    Given the API "/slo" exists per OpenAPI
    When I call "GET" "/slo" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
