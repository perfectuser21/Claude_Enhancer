Feature: POST /agents/select
  As a client
  I want POST /agents/select
  So that API contract is honored

  @contract @generated
  Scenario: POST /agents/select returns 2xx per contract
    Given the API "/agents/select" exists per OpenAPI
    When I call "POST" "/agents/select" with valid payload
    Then the response status should be 200
    And the response should conform to schema "POST /agents/select"

  @contract @error
  Scenario: POST /agents/select handles errors gracefully
    Given the API "/agents/select" exists per OpenAPI
    When I call "POST" "/agents/select" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
