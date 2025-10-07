import { useState, useEffect } from 'react';
import { fetchBundles, Bundle, ApiError } from '@/lib/api';

export interface UseBundlesReturn {
  bundles: Bundle[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * Custom hook for managing bundles data
 */
export function useBundles(): UseBundlesReturn {
  const [bundles, setBundles] = useState<Bundle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchBundles();
      setBundles(data);
    } catch (err) {
      const errorMessage = err instanceof ApiError 
        ? err.message 
        : 'An unexpected error occurred while fetching bundles';
      setError(errorMessage);
      console.error('Error fetching bundles:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return {
    bundles,
    loading,
    error,
    refetch: fetchData,
  };
}
