Feature: GET /migrations
  As a client
  I want GET /migrations
  So that API contract is honored

  @contract @generated
  Scenario: GET /migrations returns 2xx per contract
    Given the API "/migrations" exists per OpenAPI
    When I call "GET" "/migrations" with valid payload
    Then the response status should be 200
    And the response should conform to schema "GET /migrations"

  @contract @error
  Scenario: GET /migrations handles errors gracefully
    Given the API "/migrations" exists per OpenAPI
    When I call "GET" "/migrations" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
