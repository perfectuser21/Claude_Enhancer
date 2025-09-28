Feature: GET /phases/{phase}/validate
  As a client
  I want GET /phases/{phase}/validate
  So that API contract is honored

  @contract @generated
  Scenario: GET /phases/{phase}/validate returns 2xx per contract
    Given the API "/phases/{phase}/validate" exists per OpenAPI
    When I call "GET" "/phases/{phase}/validate" with valid payload
    Then the response status should be 200
    And the response should conform to schema "GET /phases/{phase}/validate"

  @contract @error
  Scenario: GET /phases/{phase}/validate handles errors gracefully
    Given the API "/phases/{phase}/validate" exists per OpenAPI
    When I call "GET" "/phases/{phase}/validate" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
