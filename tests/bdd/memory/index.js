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

  // Authentik test user credentials
  authentikUsername = 'akadmin';
  authentikPassword = 'admin';
}
