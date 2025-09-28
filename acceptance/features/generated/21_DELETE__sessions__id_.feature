Feature: DELETE /sessions/{id}
  As a client
  I want DELETE /sessions/{id}
  So that API contract is honored

  @contract @generated
  Scenario: DELETE /sessions/{id} returns 2xx per contract
    Given the API "/sessions/{id}" exists per OpenAPI
    When I call "DELETE" "/sessions/{id}" with valid payload
    Then the response status should be 200
    And the response should conform to schema "DELETE /sessions/{id}"

  @contract @error
  Scenario: DELETE /sessions/{id} handles errors gracefully
    Given the API "/sessions/{id}" exists per OpenAPI
    When I call "DELETE" "/sessions/{id}" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
