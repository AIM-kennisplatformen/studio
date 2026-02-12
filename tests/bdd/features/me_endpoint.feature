Feature: Local API Test

  Scenario: Verify /me redirects to login when unauthenticated
    When I create 'GET' request 'request'
    And I add 'http://localhost:10090/me' url to '$request'
    And I send '$request' request and save response as 'response'
    When I parse '$response' body as '$redirectInfo'
    Then I expect '$response.payload.status' to equal '500'
