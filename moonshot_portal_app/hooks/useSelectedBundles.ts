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
    return bundles.filter(bundle => bundleSelection[bundle.id]);
  }, [bundles, bundleSelection]);
}

/**
 * Selected bundle system names (`Bundle.id`), suitable for POST `bundle_names`.
 */
export function useSelectedBundleNames(): string[] {
  const bundleSelection = useAppSelector((state) => state.bundleSelection);

  return useMemo(() => {
    return Object.entries(bundleSelection)
      .filter(([_, isSelected]) => isSelected)
      .map(([bundleSystemName, _]) => bundleSystemName);
  }, [bundleSelection]);
}

/**
 * @param bundleSystemName Bundle `id` (system_name), not display `name`
 */
export function useIsBundleSelected(bundleSystemName: string): boolean {
  const bundleSelection = useAppSelector((state) => state.bundleSelection);
  return Boolean(bundleSelection[bundleSystemName]);
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
