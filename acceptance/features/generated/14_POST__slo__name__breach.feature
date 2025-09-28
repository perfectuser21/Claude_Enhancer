Feature: POST /slo/{name}/breach
  As a client
  I want POST /slo/{name}/breach
  So that API contract is honored

  @contract @generated
  Scenario: POST /slo/{name}/breach returns 2xx per contract
    Given the API "/slo/{name}/breach" exists per OpenAPI
    When I call "POST" "/slo/{name}/breach" with valid payload
    Then the response status should be 200
    And the response should conform to schema "POST /slo/{name}/breach"

  @contract @error
  Scenario: POST /slo/{name}/breach handles errors gracefully
    Given the API "/slo/{name}/breach" exists per OpenAPI
    When I call "POST" "/slo/{name}/breach" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
