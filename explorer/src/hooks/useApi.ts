import { useState, useEffect, useCallback } from 'react';

export type Fetcher<T, P = void> = (params: P) => Promise<T>;

export type ApiStatus = 'idle' | 'loading' | 'success' | 'error';

// ToDo: Deberia usar un valor sentinela para marcar que no hay nada en data o en error, diferente a null que es un valor valido como retorno de la API
export type UseApiReturn<T, E = Error> = { refetch: () => Promise<void> } & (
  | {
      data: null;
      status: 'idle' | 'loading';
      error: null;
      refetch: () => Promise<void>;
    }
  | {
      data: T;
      status: 'success';
      error: null;
    }
  | {
      data: T | null;
      status: 'error';
      error: E | null;
    }
);

export type UseApiOptions<T = any> = {
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
};

export function useQueryApi<T, P = void>(
  fetcher: Fetcher<T, P>,
  params: P,
  options: UseApiOptions<T> = {}
): UseApiReturn<T> {
  const { onSuccess, onError } = options;

  const [data, setData] = useState<T | null>(null);
  const [status, setStatus] = useState<ApiStatus>('idle');
  const [error, setError] = useState<Error | null>(null);

  const executeFetcher = useCallback(async () => {
    setStatus('loading');
    setError(null);

    try {
      const result = await fetcher(params);
      setData(result);
      setStatus('success');
      onSuccess?.(result);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      setStatus('error');
      onError?.(error);
    }
  }, [fetcher, onSuccess, onError, params]);

  const refetch = useCallback(async () => {
    await executeFetcher();
  }, [executeFetcher]);

  useEffect(() => {
    executeFetcher();
  }, [executeFetcher]);

  if (status === 'idle') {
    return {
      data: null,
      status,
      error: null,
      refetch,
    };
  }
  if (status === 'loading') {
    return {
      data: null,
      status,
      error: null,
      refetch,
    };
  }
  if (status === 'error' || !data) {
    return {
      data: null,
      status: 'error',
      error,
      refetch,
    };
  }
  return {
    data,
    status,
    error: null,
    refetch,
  };
}
