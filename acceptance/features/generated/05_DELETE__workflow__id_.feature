Feature: DELETE /workflow/{id}
  As a client
  I want DELETE /workflow/{id}
  So that API contract is honored

  @contract @generated
  Scenario: DELETE /workflow/{id} returns 2xx per contract
    Given the API "/workflow/{id}" exists per OpenAPI
    When I call "DELETE" "/workflow/{id}" with valid payload
    Then the response status should be 200
    And the response should conform to schema "DELETE /workflow/{id}"

  @contract @error
  Scenario: DELETE /workflow/{id} handles errors gracefully
    Given the API "/workflow/{id}" exists per OpenAPI
    When I call "DELETE" "/workflow/{id}" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
