Feature: DELETE /hooks/{id}
  As a client
  I want DELETE /hooks/{id}
  So that API contract is honored

  @contract @generated
  Scenario: DELETE /hooks/{id} returns 2xx per contract
    Given the API "/hooks/{id}" exists per OpenAPI
    When I call "DELETE" "/hooks/{id}" with valid payload
    Then the response status should be 200
    And the response should conform to schema "DELETE /hooks/{id}"

  @contract @error
  Scenario: DELETE /hooks/{id} handles errors gracefully
    Given the API "/hooks/{id}" exists per OpenAPI
    When I call "DELETE" "/hooks/{id}" with invalid payload
    Then the response status should be 400 or 422
    And the error response should contain message and code
