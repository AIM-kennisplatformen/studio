Feature: Chatbot Messaging

  Scenario: Authenticate via Authentik and send a chat message

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

    # Step 5: Wait for the chat interface to load (welcome message is already visible)
    Then I expect 'ChatMessageInput' to be visible
    And I expect 'ChatResponse' to be visible

    # Step 6: Send a message in the chat
    When I type '$testMessage' to 'ChatMessageInput'
    And I click 'ChatSendButton'

    # Wait for LLM response to complete (up to 60 seconds)
    # The ChatLLMResponse selector will poll until finding actual response or timeout
    Then I expect 'ChatLLMResponse' to be visible
    
    # Debug: Log what's on the page after LLM responds
    Then I debug chat responses

    # Step 7: Verify the LLM response is not empty
    Then I expect text of 'ChatLLMResponse' not to equal '$js("")'
