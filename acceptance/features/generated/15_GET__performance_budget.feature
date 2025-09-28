Feature: GET /performance/budget
  As a client
  I want GET /performance/budget
  So that API contract is honored

  @contract @generated
  Scenario: GET /performance/budget returns 2xx per contract
    Given the API "/performance/budget" exists per OpenAPI
    When I call "GET" "/performance/budget" with valid payload
    Then the response status should be 200
    And the response should conform to schema "GET /performance/budget"

  @contract @error
  Scenario: GET /performance/budget handles errors gracefully
    Given the API "/performance/budget" exists per OpenAPI
    When I call "GET" "/performance/budget" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
