import { useState, useCallback } from 'react';
import { api } from '@/api/client';

export function useApi(method, ...defaultArgs) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(async (...args) => {
    setLoading(true);
    setError(null);
    try {
      const result = await api[method](...defaultArgs, ...args);
      setData(result);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [method, ...defaultArgs]);

  return { data, loading, error, execute };
}
