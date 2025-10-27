import { useEffect } from 'react';
import { useAppSelector, useAppDispatch } from './reduxHooks';
import { fetchFixedConfigsAsync, clearFixedConfigsError } from '../store';

export interface UseFixedConfigsReduxReturn {
  configs: any[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * Custom hook for managing fixed configs data using Redux
 * This prevents duplicate API calls when used in multiple components
 */
export function useFixedConfigsRedux(): UseFixedConfigsReduxReturn {
  const dispatch = useAppDispatch();
  const { data: configs, loading, error } = useAppSelector((state) => state.fixedConfigs);

  const refetch = () => {
    dispatch(fetchFixedConfigsAsync());
  };

  useEffect(() => {
    // Only fetch if we don't have data and aren't already loading
    if (configs.length === 0 && !loading) {
      dispatch(fetchFixedConfigsAsync());
    }
  }, [dispatch, configs.length, loading]);

  return {
    configs,
    loading,
    error,
    refetch,
  };
}

