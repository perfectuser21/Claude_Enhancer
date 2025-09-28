Feature: POST /migrations
  As a client
  I want POST /migrations
  So that API contract is honored

  @contract @generated
  Scenario: POST /migrations returns 2xx per contract
    Given the API "/migrations" exists per OpenAPI
    When I call "POST" "/migrations" with valid payload
    Then the response status should be 200
    And the response should conform to schema "POST /migrations"

  @contract @error
  Scenario: POST /migrations handles errors gracefully
    Given the API "/migrations" exists per OpenAPI
    When I call "POST" "/migrations" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
