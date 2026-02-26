export default class Memory {
  redirectInfo = async (response) => {
    return {
      status: response.status,
      location: response.headers.get('location'),
    };
  };

  // Pre-built URLs for the test
  loginUrl = 'http://localhost:10090/auth/login';
  meUrl = 'http://localhost:10090/me';
  chatUrl = 'http://localhost:10090/app';

  // Authentik test user credentials
  authentikUsername = 'akadmin';
  authentikPassword = 'admin';

  // Chat test data
  testMessage = 'Hello, can you help me?';
}
