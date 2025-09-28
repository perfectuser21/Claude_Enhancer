Feature: PUT /performance/budget
  As a client
  I want PUT /performance/budget
  So that API contract is honored

  @contract @generated
  Scenario: PUT /performance/budget returns 2xx per contract
    Given the API "/performance/budget" exists per OpenAPI
    When I call "PUT" "/performance/budget" with valid payload
    Then the response status should be 200
    And the response should conform to schema "PUT /performance/budget"

  @contract @error
  Scenario: PUT /performance/budget handles errors gracefully
    Given the API "/performance/budget" exists per OpenAPI
    When I call "PUT" "/performance/budget" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
