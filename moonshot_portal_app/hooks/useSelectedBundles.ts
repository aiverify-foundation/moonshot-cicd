import { useMemo } from 'react';
import { useAppSelector } from './reduxHooks';
import { Bundle } from '@/lib/api';

/**
 * Get all selected bundles as Bundle objects
 */
export function useSelectedBundles(): Bundle[] {
  const bundleSelection = useAppSelector((state) => state.bundleSelection);
  const bundles = useAppSelector((state) => state.bundles.data);

  return useMemo(() => {
    return bundles.filter(bundle => bundleSelection[bundle.name]);
  }, [bundles, bundleSelection]);
}

/**
 * Get all selected bundle names as strings
 */
export function useSelectedBundleNames(): string[] {
  const bundleSelection = useAppSelector((state) => state.bundleSelection);

  return useMemo(() => {
    return Object.entries(bundleSelection)
      .filter(([_, isSelected]) => isSelected)
      .map(([bundleName, _]) => bundleName);
  }, [bundleSelection]);
}

/**
 * Check if a specific bundle is selected
 */
export function useIsBundleSelected(bundleName: string): boolean {
  const bundleSelection = useAppSelector((state) => state.bundleSelection);
  return Boolean(bundleSelection[bundleName]);
}

/**
 * Check if any bundles are selected
 */
export function useHasSelectedBundles(): boolean {
  const bundleSelection = useAppSelector((state) => state.bundleSelection);
  
  return useMemo(() => {
    return Object.values(bundleSelection).some(isSelected => isSelected);
  }, [bundleSelection]);
}
