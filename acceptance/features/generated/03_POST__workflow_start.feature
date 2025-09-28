Feature: POST /workflow/start
  As a client
  I want POST /workflow/start
  So that API contract is honored

  @contract @generated
  Scenario: POST /workflow/start returns 2xx per contract
    Given the API "/workflow/start" exists per OpenAPI
    When I call "POST" "/workflow/start" with valid payload
    Then the response status should be 200
    And the response should conform to schema "POST /workflow/start"

  @contract @error
  Scenario: POST /workflow/start handles errors gracefully
    Given the API "/workflow/start" exists per OpenAPI
    When I call "POST" "/workflow/start" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
