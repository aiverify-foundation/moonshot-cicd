import { useMemo } from 'react';
import { useAppSelector, useAppDispatch } from './reduxHooks';
import { 
  setTestSelected, 
  toggleTestSelected, 
  setMultipleTestsSelected, 
  clearTestSelection 
} from '../store';

/**
 * Get all checked test names as strings
 */
export function useCheckedTestNames(): string[] {
  const testSelection = useAppSelector((state) => state.testSelection);

  return useMemo(() => {
    return Object.entries(testSelection)
      .filter(([_, isSelected]) => isSelected)
      .map(([testName, _]) => testName);
  }, [testSelection]);
}

/**
 * Check if a specific test is selected
 */
export function useIsTestSelected(testName: string): boolean {
  const testSelection = useAppSelector((state) => state.testSelection);
  return Boolean(testSelection[testName]);
}

/**
 * Check if any tests are selected
 */
export function useHasSelectedTests(): boolean {
  const testSelection = useAppSelector((state) => state.testSelection);
  
  return useMemo(() => {
    return Object.values(testSelection).some(isSelected => isSelected);
  }, [testSelection]);
}

/**
 * Get all checked tests with their bundle information.
 * `bundleName` is the bundle display title (`Bundle.name`), not `Bundle.id` / system_name.
 * Per-test toggles are sent to POST `/api/start-benchmark-run` as `tests_by_bundle` when
 * `BenchmarkFooter` builds that payload from `benchmark_test_id` on each test.
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

    bundles.forEach(bundle => {
      bundle.tests.forEach(test => {
        if (testSelection[test.name]) {
          checkedTests.push({
            testName: test.name,
            bundleName: bundle.name,
            dataset: test.dataset
          });
        }
      });
    });

    return checkedTests;
  }, [testSelection, bundles]);
}

/**
 * Check if all tests in a bundle are selected
 */
export function useAreAllTestsInBundleChecked(bundleName: string, testNames: string[]): boolean {
  const testSelection = useAppSelector((state) => state.testSelection);

  return useMemo(() => {
    return testNames.every(testName => testSelection[testName]);
  }, [testSelection, testNames]);
}

/**
 * Custom hook for managing test selection actions
 */
export function useTestSelectionActions() {
  const dispatch = useAppDispatch();

  const setTest = (testName: string, selected: boolean) => {
    dispatch(setTestSelected({ testName, selected }));
  };

  const toggleTest = (testName: string) => {
    dispatch(toggleTestSelected(testName));
  };

  const setMultipleTests = (testNames: string[], selected: boolean) => {
    dispatch(setMultipleTestsSelected({ testNames, selected }));
  };

  const clearAllTests = () => {
    dispatch(clearTestSelection());
  };

  return {
    setTest,
    toggleTest,
    setMultipleTests,
    clearAllTests,
  };
}
