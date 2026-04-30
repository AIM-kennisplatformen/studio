export default class Memory {
  // Use localhost to match the OAuth redirect_uri domain (cookie must be on same domain for session continuity)
  loginUrl = 'http://localhost:10090/auth/login';
  meUrl = 'http://localhost:10090/me';

  // Authentik test user credentials
  authentikUsername = 'akadmin';
  authentikPassword = 'admin';

  // Chat test data
  testMessage = 'Hello, can you help me?';

  // MCP test user credentials (separate user to avoid session state leaking between tests)
  mcpUsername = 'mcpuser';
  mcpPassword = 'mcppass';

  // MCP tool test data — a research question that should trigger mcp tool call
  mcpTestMessage = 'What are the best practices for blended learning?';
}
