export default class Memory {
  // Pre-built URLs for the test (use 127.0.0.1 for CI compatibility — Chromium can't resolve 'localhost' in GitHub Actions)
  loginUrl = 'http://127.0.0.1:10090/auth/login';
  meUrl = 'http://127.0.0.1:10090/me';

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
