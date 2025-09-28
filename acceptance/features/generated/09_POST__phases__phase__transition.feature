Feature: POST /phases/{phase}/transition
  As a client
  I want POST /phases/{phase}/transition
  So that API contract is honored

  @contract @generated
  Scenario: POST /phases/{phase}/transition returns 2xx per contract
    Given the API "/phases/{phase}/transition" exists per OpenAPI
    When I call "POST" "/phases/{phase}/transition" with valid payload
    Then the response status should be 200
    And the response should conform to schema "POST /phases/{phase}/transition"

  @contract @error
  Scenario: POST /phases/{phase}/transition handles errors gracefully
    Given the API "/phases/{phase}/transition" exists per OpenAPI
    When I call "POST" "/phases/{phase}/transition" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
