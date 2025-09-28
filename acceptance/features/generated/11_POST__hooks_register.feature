Feature: POST /hooks/register
  As a client
  I want POST /hooks/register
  So that API contract is honored

  @contract @generated
  Scenario: POST /hooks/register returns 2xx per contract
    Given the API "/hooks/register" exists per OpenAPI
    When I call "POST" "/hooks/register" with valid payload
    Then the response status should be 200
    And the response should conform to schema "POST /hooks/register"

  @contract @error
  Scenario: POST /hooks/register handles errors gracefully
    Given the API "/hooks/register" exists per OpenAPI
    When I call "POST" "/hooks/register" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
