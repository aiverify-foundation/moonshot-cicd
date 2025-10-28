import { useEffect, useMemo } from 'react';
import { useAppSelector, useAppDispatch } from './reduxHooks';
import { fetchFixedConfigsAsync, clearFixedConfigsError } from '../store';
import { useCheckedTestNames } from './useTestSelection';
import { FixedConfig, Bundle } from '../lib/api';

export interface UseFixedConfigsReduxReturn {
  configs: FixedConfig[];
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

/**
 * Get fixed configs that are referenced by the selected tools
 * Filters fixed configs based on config_id in the metric of selected tests
 */
export function useFixedConfigsForSelectedTests(): FixedConfig[] {
  const dispatch = useAppDispatch();
  const selectedTestNames = useCheckedTestNames();
  const bundles = useAppSelector((state) => state.bundles.data) as Bundle[];
  const { data: allFixedConfigs, loading } = useAppSelector((state) => state.fixedConfigs);

  // Ensure fixed configs are loaded
  useEffect(() => {
    if (allFixedConfigs.length === 0 && !loading) {
      dispatch(fetchFixedConfigsAsync());
    }
  }, [dispatch, allFixedConfigs.length, loading]);

  return useMemo(() => {
    // Extract all config_ids from selected tests' metrics
    const configIds = new Set<string>();
    
    bundles.forEach(bundle => {
      bundle.tests.forEach(test => {
        if (selectedTestNames.includes(test.name) && test.metric?.config_id) {
          configIds.add(test.metric.config_id);
       }
      });
    });


    // If no config_ids found, return empty array
    if (configIds.size === 0) {
      return [];
    }

    // Filter fixed configs to only include those with matching ids
    const filtered = allFixedConfigs.filter(config => configIds.has(config.id));
    return filtered;
  }, [selectedTestNames, bundles, allFixedConfigs]);
}

