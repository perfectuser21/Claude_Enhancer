Feature: GET /spikes
  As a client
  I want GET /spikes
  So that API contract is honored

  @contract @generated
  Scenario: GET /spikes returns 2xx per contract
    Given the API "/spikes" exists per OpenAPI
    When I call "GET" "/spikes" with valid payload
    Then the response status should be 200
    And the response should conform to schema "GET /spikes"

  @contract @error
  Scenario: GET /spikes handles errors gracefully
    Given the API "/spikes" exists per OpenAPI
    When I call "GET" "/spikes" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
