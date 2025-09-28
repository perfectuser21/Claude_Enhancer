Feature: GET /workflow/{id}
  As a client
  I want GET /workflow/{id}
  So that API contract is honored

  @contract @generated
  Scenario: GET /workflow/{id} returns 2xx per contract
    Given the API "/workflow/{id}" exists per OpenAPI
    When I call "GET" "/workflow/{id}" with valid payload
    Then the response status should be 200
    And the response should conform to schema "GET /workflow/{id}"

  @contract @error
  Scenario: GET /workflow/{id} handles errors gracefully
    Given the API "/workflow/{id}" exists per OpenAPI
    When I call "GET" "/workflow/{id}" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
