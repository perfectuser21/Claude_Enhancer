Feature: GET /phases
  As a client
  I want GET /phases
  So that API contract is honored

  @contract @generated
  Scenario: GET /phases returns 2xx per contract
    Given the API "/phases" exists per OpenAPI
    When I call "GET" "/phases" with valid payload
    Then the response status should be 200
    And the response should conform to schema "GET /phases"

  @contract @error
  Scenario: GET /phases handles errors gracefully
    Given the API "/phases" exists per OpenAPI
    When I call "GET" "/phases" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
