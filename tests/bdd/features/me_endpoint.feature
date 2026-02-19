Feature: Me Endpoint with Authentik Authentication

  Scenario: Authenticate via Authentik and call /me endpoint
    # Step 1: Navigate to the backend login URL (triggers OAuth redirect to Authentik)
    Given I open '$loginUrl' url

    # Step 2: Fill in username on Authentik login page and submit
    When I type '$authentikUsername' to 'AuthentikUsernameInput'
    And I click 'AuthentikSubmitButton'

    # Step 3: Fill in password on Authentik login page and submit
    When I type '$authentikPassword' to 'AuthentikPasswordInput'
    And I click 'AuthentikSubmitButton'

    # Step 4: Wait for redirect back to the app (Authentik → /auth/callback → /app)
    Then I expect current url to contain '/app'

    # Step 5: Create API request to /me and attach session cookies from browser
    When I create 'GET' request 'meRequest'
    And I add '$meUrl' url to '$meRequest'
    And I add browser cookies to '$meRequest'

    # Step 6: Send the request and verify the response
    And I send '$meRequest' request and save response as 'meResponse'
    And I parse '$meResponse' body as json
    Then I expect '$meResponse.status' to equal '$js(200)'
    And I expect '$meResponse.payload.authenticated' to equal '$js(true)'
