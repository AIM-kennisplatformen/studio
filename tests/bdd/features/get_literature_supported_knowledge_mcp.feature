Feature: MCP Function Invocation

  Scenario: Verify paper_search MCP tool is called during chat

    # Step 1: Set up WebSocket interception to capture MCP tool events
    Given I start capturing MCP tool events

    # Step 2: Navigate to the backend login URL (triggers OAuth redirect to Authentik)
    Given I open '$loginUrl' url

    # Step 3: Fill in username on Authentik login page and submit
    When I type '$authentikUsername' to 'AuthentikUsernameInput'
    And I click 'AuthentikSubmitButton'

    # Step 4: Fill in password on Authentik login page and submit
    When I type '$authentikPassword' to 'AuthentikPasswordInput'
    And I click 'AuthentikSubmitButton'

    # Step 5: Wait for redirect back to the app (Authentik → /auth/callback → /app)
    Then I expect current url to contain '/app'

    # Step 6: Wait for the chat interface to load
    Then I expect 'ChatMessageInput' to be visible
    And I expect 'ChatResponse' to be visible

    # Step 7: Send a research question that should trigger the paper_search MCP tool
    When I type '$mcpTestMessage' to 'ChatMessageInput'
    And I click 'ChatSendButton'

    # Step 8: Wait for and verify an actual LLM response
    Then I should receive an LLM response within 90 seconds

    # Step 9: Verify the MCP tool was invoked during the response generation
    And the MCP tool 'get_literature_supported_knowledge' should have been called
