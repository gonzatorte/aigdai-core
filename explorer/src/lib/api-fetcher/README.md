# API Fetcher Library

A lightweight, cancellable API client that wraps native `fetch` with a clean, promise-based interface.

## Features

- ✅ **Cancellable requests** using `AbortController`
- ✅ **TypeScript support** with full type safety
- ✅ **Timeout handling** with configurable timeouts
- ✅ **Promise-based API** with `.then()`, `.catch()`, `.finally()`
- ✅ **Automatic JSON parsing** with fallback to text
- ✅ **Configurable base URL and headers**
- ✅ **All HTTP methods** (GET, POST, PUT, PATCH, DELETE)

## Quick Start

### Basic Usage

```typescript
import { api } from './lib/api-fetcher';

// GET request
const usersCall = api.get<User[]>('/api/users');
const users = await usersCall;

// POST request
const newUserCall = api.post<User>('/api/users', {
  name: 'John Doe',
  email: 'john@example.com'
});
const newUser = await newUserCall;
```

### Cancelling Requests

```typescript
const call = api.get<User[]>('/api/users');

// Cancel the request
call.cancel();

// Check if cancelled
if (call.isCancelled()) {
  console.log('Request was cancelled');
}
```

### React Component Example

```typescript
import React, { useEffect, useState } from 'react';
import { api, ApiCall } from './lib/api-fetcher';

function UserList() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [apiCall, setApiCall] = useState<ApiCall<User[]> | null>(null);

  const fetchUsers = async () => {
    // Cancel previous request if it exists
    if (apiCall) {
      apiCall.cancel();
    }

    setLoading(true);
    const call = api.get<User[]>('/api/users');
    setApiCall(call);

    try {
      const data = await call;
      setUsers(data);
    } catch (error) {
      if (error.message !== 'Request was cancelled') {
        console.error('Error fetching users:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();

    // Cleanup on unmount
    return () => {
      if (apiCall) {
        apiCall.cancel();
      }
    };
  }, []);

  return (
    <div>
      {loading && <div>Loading...</div>}
      {users.map(user => (
        <div key={user.id}>{user.name}</div>
      ))}
    </div>
  );
}
```

## API Reference

### `ApiCall<T>`

A cancellable wrapper around fetch promises.

#### Methods

- `cancel()`: Cancels the request
- `isCancelled()`: Returns true if the request was cancelled
- `then()`, `catch()`, `finally()`: Standard promise methods

### `ApiFetcher`

Main class for creating API calls.

#### Constructor

```typescript
const fetcher = new ApiFetcher({
  baseURL: 'https://api.example.com',
  defaultHeaders: {
    'Authorization': 'Bearer token'
  },
  defaultTimeout: 30000
});
```

#### Methods

- `get<T>(url, options?)`: GET request
- `post<T>(url, data?, options?)`: POST request
- `put<T>(url, data?, options?)`: PUT request
- `patch<T>(url, data?, options?)`: PATCH request
- `delete<T>(url, options?)`: DELETE request
- `request<T>(url, options)`: Generic request

### `api` (Default Instance)

Convenience functions using the default `ApiFetcher` instance.

```typescript
import { api } from './lib/api-fetcher';

// All methods return ApiCall instances
const call = api.get<User[]>('/users');
const postCall = api.post<User>('/users', userData);
const putCall = api.put<User>('/users/1', userData);
const deleteCall = api.delete('/users/1');
```

## Configuration Options

### `ApiRequestOptions`

```typescript
interface ApiRequestOptions extends RequestInit {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
}
```

### `ApiFetcher` Configuration

```typescript
interface ApiFetcherConfig {
  baseURL?: string;
  defaultHeaders?: Record<string, string>;
  defaultTimeout?: number;
}
```

## Error Handling

The library handles various error scenarios:

- **Network errors**: Standard fetch network errors
- **HTTP errors**: Non-2xx status codes
- **Timeout errors**: Configurable request timeouts
- **Cancellation errors**: When requests are cancelled
- **JSON parsing errors**: Automatic fallback to text

## Examples

See `api-fetcher-example.ts` for comprehensive usage examples including:

- Basic usage with default API instance
- Custom ApiFetcher configuration
- React component integration
- Promise chaining
- Timeout handling
- Error handling patterns 