import { ApiFetcher, api, ApiCall } from './api-fetcher';

// Example 1: Using the default api instance
export async function exampleWithDefaultApi() {
  // GET request
  const getCall: ApiCall<User[]> = api.get<User[]>('/api/users');

  try {
    const users = await getCall;
    console.log('Users:', users);
  } catch (error) {
    console.error('Error fetching users:', error);
  }

  // POST request
  const postCall = api.post<User>('/api/users', {
    name: 'John Doe',
    email: 'john@example.com',
  });

  try {
    const newUser = await postCall;
    console.log('Created user:', newUser);
  } catch (error) {
    console.error('Error creating user:', error);
  }
}

// Example 2: Using custom ApiFetcher instance
export function exampleWithCustomFetcher() {
  const customFetcher = new ApiFetcher({
    baseURL: 'https://api.example.com',
    defaultHeaders: {
      Authorization: 'Bearer your-token-here',
      'X-API-Version': 'v1',
    },
    defaultTimeout: 10000, // 10 seconds
  });

  const call = customFetcher.get<User[]>('/users');

  // You can cancel the call at any time
  setTimeout(() => {
    call.cancel();
    console.log('API call cancelled');
  }, 5000);

  return call;
}

// Example 3: Cancelling API calls in React components
export function exampleReactUsage() {
  let apiCall: ApiCall<User[]> | null = null;

  const fetchUsers = async () => {
    // Cancel previous call if it exists
    if (apiCall) {
      apiCall.cancel();
    }

    // Start new call
    apiCall = api.get<User[]>('/api/users');

    try {
      const users = await apiCall;
      console.log('Users loaded:', users);
    } catch (error) {
      if (error instanceof Error && error.message === 'Request was cancelled') {
        console.log('Request was cancelled');
      } else {
        console.error('Error:', error);
      }
    }
  };

  const cancelRequest = () => {
    if (apiCall) {
      apiCall.cancel();
      apiCall = null;
    }
  };

  return { fetchUsers, cancelRequest };
}

// Example 4: Chaining promises
export async function exampleChaining() {
  const call = api.get<User[]>('/api/users');

  call
    .then((users) => {
      console.log('Users loaded:', users);
      return users[0]; // Return first user
    })
    .then((firstUser) => {
      console.log('First user:', firstUser);
      // Make another API call
      return api.get<UserDetails>(`/api/users/${firstUser.id}/details`);
    })
    .then((userDetails) => {
      console.log('User details:', userDetails);
    })
    .catch((error) => {
      console.error('Error in chain:', error);
    });
}

// Example 5: Timeout handling
export async function exampleWithTimeout() {
  const call = api.request<User[]>('/api/users', {
    timeout: 5000, // 5 seconds timeout
  });

  try {
    const users = await call;
    console.log('Users loaded within 5 seconds:', users);
  } catch (error) {
    if (error instanceof Error && error.message.includes('timeout')) {
      console.log('Request timed out');
    } else {
      console.error('Other error:', error);
    }
  }
}

// Type definitions for examples
interface User {
  id: number;
  name: string;
  email: string;
}

interface UserDetails {
  id: number;
  name: string;
  email: string;
  bio: string;
  avatar: string;
}
