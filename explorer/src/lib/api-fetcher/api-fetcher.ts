/**
 * ApiCall - A cancellable wrapper around fetch promises
 */
export class ApiCall<T = any> {
  private abortController: AbortController;
  private promise: Promise<T>;
  private _isCancelled = false;

  constructor(promise: Promise<T>, abortController: AbortController) {
    this.promise = promise;
    this.abortController = abortController;
  }

  /**
   * Get the underlying promise
   */
  getPromise(): Promise<T> {
    return this.promise;
  }

  /**
   * Cancel the API call
   */
  cancel(): void {
    if (!this._isCancelled) {
      this._isCancelled = true;
      this.abortController.abort();
    }
  }

  /**
   * Check if the call has been cancelled
   */
  isCancelled(): boolean {
    return this._isCancelled;
  }

  /**
   * Chain additional promise operations
   */
  then<TResult1 = T, TResult2 = never>(
    onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | null,
    onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | null
  ): Promise<TResult1 | TResult2> {
    return this.promise.then(onfulfilled, onrejected);
  }

  /**
   * Add error handling
   */
  catch<TResult = never>(
    onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | null
  ): Promise<T | TResult> {
    return this.promise.catch(onrejected);
  }

  /**
   * Add finally handler
   */
  finally(onfinally?: (() => void) | null): Promise<T> {
    return this.promise.finally(onfinally);
  }
}

/**
 * HTTP methods supported by the API fetcher
 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

/**
 * Request options extending the native RequestInit
 */
export interface ApiRequestOptions extends RequestInit {
  method?: HttpMethod;
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
}

/**
 * API fetcher class that creates cancellable API calls
 */
export class ApiFetcher {
  private baseURL: string;
  private defaultHeaders: Record<string, string>;
  private defaultTimeout: number;

  constructor(
    config: {
      baseURL?: string;
      defaultHeaders?: Record<string, string>;
      defaultTimeout?: number;
    } = {}
  ) {
    this.baseURL = config.baseURL || '';
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      ...config.defaultHeaders,
    };
    this.defaultTimeout = config.defaultTimeout || 30000; // 30 seconds
  }

  /**
   * Create a cancellable API call
   */
  private createApiCall<T>(
    url: string,
    options: ApiRequestOptions = {}
  ): ApiCall<T> {
    const abortController = new AbortController();
    const timeout = options.timeout || this.defaultTimeout;

    // Prepare the full URL
    const fullURL = this.baseURL ? `${this.baseURL}${url}` : url;

    // Prepare headers
    const headers = {
      ...this.defaultHeaders,
      ...options.headers,
    };

    // Prepare request options
    const requestOptions: RequestInit = {
      method: options.method || 'GET',
      headers,
      signal: abortController.signal,
      ...options,
    };

    // Handle body serialization
    if (options.body && typeof options.body === 'object') {
      requestOptions.body = JSON.stringify(options.body);
    }

    // Create the fetch promise with timeout
    const fetchPromise = this.createFetchWithTimeout<T>(
      fullURL,
      requestOptions,
      timeout,
      abortController
    );

    return new ApiCall(fetchPromise, abortController);
  }

  /**
   * Create fetch with timeout support
   */
  private createFetchWithTimeout<T>(
    url: string,
    options: RequestInit,
    timeout: number,
    abortController: AbortController
  ): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      // Set up timeout
      const timeoutId = setTimeout(() => {
        abortController.abort();
        reject(new Error(`Request timeout after ${timeout}ms`));
      }, timeout);

      // Make the fetch request
      fetch(url, options)
        .then(async (response) => {
          clearTimeout(timeoutId);

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          // Try to parse as JSON, fallback to text
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            return response.json();
          } else {
            return response.text();
          }
        })
        .then((data) => {
          resolve(data as T);
        })
        .catch((error) => {
          clearTimeout(timeoutId);
          if (error.name === 'AbortError') {
            reject(new Error('Request was cancelled'));
          } else {
            reject(error);
          }
        });
    });
  }

  /**
   * GET request
   */
  get<T = any>(
    url: string,
    options?: Omit<ApiRequestOptions, 'method'>
  ): ApiCall<T> {
    return this.createApiCall<T>(url, { ...options, method: 'GET' });
  }

  /**
   * POST request
   */
  post<T = any>(
    url: string,
    data?: any,
    options?: Omit<ApiRequestOptions, 'method' | 'body'>
  ): ApiCall<T> {
    return this.createApiCall<T>(url, {
      ...options,
      method: 'POST',
      body: data,
    });
  }

  /**
   * PUT request
   */
  put<T = any>(
    url: string,
    data?: any,
    options?: Omit<ApiRequestOptions, 'method' | 'body'>
  ): ApiCall<T> {
    return this.createApiCall<T>(url, {
      ...options,
      method: 'PUT',
      body: data,
    });
  }

  /**
   * PATCH request
   */
  patch<T = any>(
    url: string,
    data?: any,
    options?: Omit<ApiRequestOptions, 'method' | 'body'>
  ): ApiCall<T> {
    return this.createApiCall<T>(url, {
      ...options,
      method: 'PATCH',
      body: data,
    });
  }

  /**
   * DELETE request
   */
  delete<T = any>(
    url: string,
    options?: Omit<ApiRequestOptions, 'method'>
  ): ApiCall<T> {
    return this.createApiCall<T>(url, { ...options, method: 'DELETE' });
  }

  /**
   * Generic request method
   */
  request<T = any>(url: string, options: ApiRequestOptions): ApiCall<T> {
    return this.createApiCall<T>(url, options);
  }
}

/**
 * Create a default API fetcher instance
 */
export const apiFetcher = new ApiFetcher();

/**
 * Convenience functions for common HTTP methods
 */
export const api = {
  get: <T = any>(url: string, options?: Omit<ApiRequestOptions, 'method'>) =>
    apiFetcher.get<T>(url, options),

  post: <T = any>(
    url: string,
    data?: any,
    options?: Omit<ApiRequestOptions, 'method' | 'body'>
  ) => apiFetcher.post<T>(url, data, options),

  put: <T = any>(
    url: string,
    data?: any,
    options?: Omit<ApiRequestOptions, 'method' | 'body'>
  ) => apiFetcher.put<T>(url, data, options),

  patch: <T = any>(
    url: string,
    data?: any,
    options?: Omit<ApiRequestOptions, 'method' | 'body'>
  ) => apiFetcher.patch<T>(url, data, options),

  delete: <T = any>(url: string, options?: Omit<ApiRequestOptions, 'method'>) =>
    apiFetcher.delete<T>(url, options),

  request: <T = any>(url: string, options: ApiRequestOptions) =>
    apiFetcher.request<T>(url, options),
};
