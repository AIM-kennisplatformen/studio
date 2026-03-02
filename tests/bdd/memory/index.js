export default class Memory {
  // Pre-built URLs for the test
  loginUrl = 'http://localhost:10090/auth/login';
  meUrl = 'http://localhost:10090/me';

  // Authentik test user credentials
  authentikUsername = 'akadmin';
  authentikPassword = 'admin';

  // Chat test data
  testMessage = 'Hello, can you help me?';

  // MCP tool test data — a research question that should trigger paper_search
  mcpTestMessage = 'What are the best practices for blended learning?';
}
