import { useEffect } from 'react';
import { useAppSelector, useAppDispatch } from './reduxHooks';
import { fetchBundlesAsync, clearBundlesError } from '../store';

export interface UseBundlesReduxReturn {
  bundles: any[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * Custom hook for managing bundles data using Redux
 * This prevents duplicate API calls when used in multiple components
 */
export function useBundlesRedux(): UseBundlesReduxReturn {
  const dispatch = useAppDispatch();
  const { data: bundles, loading, error } = useAppSelector((state) => state.bundles);

  const refetch = () => {
    dispatch(fetchBundlesAsync());
  };

  useEffect(() => {
    // Only fetch if we don't have data and aren't already loading
    if (bundles.length === 0 && !loading) {
      dispatch(fetchBundlesAsync());
    }
  }, [dispatch, bundles.length, loading]);

  return {
    bundles,
    loading,
    error,
    refetch,
  };
}
