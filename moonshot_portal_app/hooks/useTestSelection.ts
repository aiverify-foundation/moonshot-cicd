import { useMemo } from 'react';
import { useStore } from 'react-redux';
import { useAppSelector, useAppDispatch } from './reduxHooks';
import {
  setTestSelected,
  toggleTestSelected,
  setMultipleTestsSelected,
  clearTestSelection,
  clearTestsForBundle,
  setBundleSelected,
  type RootState,
} from '../store';
import type { BundleTest } from '../lib/api';
import {
  areAllTestsSelected,
  getTestSelectionKey,
  hasAnySelectedTestsInBundle,
  isTestSelected,
  selectedTestsInBundle,
} from '../lib/benchmarkTestSelection';

/**
 * Get checked test names across selected bundles (union by name for endpoint grouping).
 */
export function useCheckedTestNames(): string[] {
  const testSelection = useAppSelector((state) => state.testSelection);
  const bundles = useAppSelector((state) => state.bundles.data);
  const bundleSelection = useAppSelector((state) => state.bundleSelection);

  return useMemo(() => {
    const names = new Set<string>();
    bundles.forEach((bundle) => {
      if (!bundleSelection[bundle.id]) return;
      selectedTestsInBundle(testSelection, bundle.id, bundle.tests).forEach((test) => {
        names.add(test.name);
      });
    });
    return Array.from(names);
  }, [testSelection, bundles, bundleSelection]);
}

/**
 * Check if a specific test is selected within a bundle.
 */
export function useIsTestSelected(
  bundleId: string,
  test: Pick<BundleTest, 'name' | 'benchmark_test_id'>
): boolean {
  const testSelection = useAppSelector((state) => state.testSelection);
  return isTestSelected(testSelection, bundleId, test);
}

/**
 * Check if any tests are selected in any bundle.
 */
export function useHasSelectedTests(): boolean {
  const testSelection = useAppSelector((state) => state.testSelection);

  return useMemo(() => {
    return Object.values(testSelection).some((bundleTests) =>
      Object.values(bundleTests).some(Boolean)
    );
  }, [testSelection]);
}

/**
 * Get all checked tests with their bundle information.
 * `bundleName` is the bundle display title (`Bundle.name`), not `Bundle.id` / system_name.
 */
export function useCheckedTestsWithBundles(): Array<{
  testName: string;
  bundleName: string;
  dataset: {
    id: string;
    name: string;
    description: string;
  };
}> {
  const testSelection = useAppSelector((state) => state.testSelection);
  const bundles = useAppSelector((state) => state.bundles.data);
  const bundleSelection = useAppSelector((state) => state.bundleSelection);

  return useMemo(() => {
    const checkedTests: Array<{
      testName: string;
      bundleName: string;
      dataset: {
        id: string;
        name: string;
        description: string;
      };
    }> = [];

    bundles.forEach((bundle) => {
      if (!bundleSelection[bundle.id]) return;
      selectedTestsInBundle(testSelection, bundle.id, bundle.tests).forEach((test) => {
        checkedTests.push({
          testName: test.name,
          bundleName: bundle.name,
          dataset: test.dataset,
        });
      });
    });

    return checkedTests;
  }, [testSelection, bundles, bundleSelection]);
}

/**
 * Check if all tests in a bundle are selected.
 */
export function useAreAllTestsInBundleChecked(
  bundleId: string,
  tests: Pick<BundleTest, 'name' | 'benchmark_test_id'>[]
): boolean {
  const testSelection = useAppSelector((state) => state.testSelection);

  return useMemo(() => {
    return areAllTestsSelected(testSelection, bundleId, tests);
  }, [testSelection, bundleId, tests]);
}

/**
 * Custom hook for managing test selection actions.
 */
export function useTestSelectionActions() {
  const dispatch = useAppDispatch();
  const store = useStore<RootState>();

  const syncBundleSelection = (bundleId: string) => {
    const { bundleSelection, testSelection } = store.getState();
    if (
      bundleSelection[bundleId] &&
      !hasAnySelectedTestsInBundle(testSelection, bundleId)
    ) {
      dispatch(setBundleSelected({ bundleId, selected: false }));
    }
  };

  const setTest = (
    bundleId: string,
    test: Pick<BundleTest, 'name' | 'benchmark_test_id'>,
    selected: boolean
  ) => {
    dispatch(
      setTestSelected({
        bundleId,
        testKey: getTestSelectionKey(test),
        selected,
      })
    );
    syncBundleSelection(bundleId);
  };

  const toggleTest = (bundleId: string, test: Pick<BundleTest, 'name' | 'benchmark_test_id'>) => {
    dispatch(
      toggleTestSelected({
        bundleId,
        testKey: getTestSelectionKey(test),
      })
    );
    syncBundleSelection(bundleId);
  };

  const setMultipleTests = (
    bundleId: string,
    tests: Pick<BundleTest, 'name' | 'benchmark_test_id'>[],
    selected: boolean
  ) => {
    dispatch(
      setMultipleTestsSelected({
        bundleId,
        testKeys: tests.map(getTestSelectionKey),
        selected,
      })
    );
    syncBundleSelection(bundleId);
  };

  const clearBundleTests = (bundleId: string) => {
    dispatch(clearTestsForBundle(bundleId));
  };

  const clearAllTests = () => {
    dispatch(clearTestSelection());
  };

  return {
    setTest,
    toggleTest,
    setMultipleTests,
    clearBundleTests,
    clearAllTests,
  };
}
