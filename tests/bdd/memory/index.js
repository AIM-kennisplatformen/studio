export default class Memory {
  redirectInfo = async (response) => {
    return {
      status: response.status,
      location: response.headers.get('location'),
    };
  };
}
