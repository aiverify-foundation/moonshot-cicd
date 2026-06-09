import type { BundleTest } from './api';

/** Redux testSelection: bundle system_name → testKey → selected */
export type TestSelectionState = Record<string, Record<string, boolean>>;

export function getTestSelectionKey(test: Pick<BundleTest, 'name' | 'benchmark_test_id'>): string {
  if (test.benchmark_test_id != null) {
    return String(test.benchmark_test_id);
  }
  return test.name;
}

export function isTestSelected(
  state: TestSelectionState,
  bundleId: string,
  test: Pick<BundleTest, 'name' | 'benchmark_test_id'>
): boolean {
  const testKey = getTestSelectionKey(test);
  return Boolean(state[bundleId]?.[testKey]);
}

export function areAllTestsSelected(
  state: TestSelectionState,
  bundleId: string,
  tests: Pick<BundleTest, 'name' | 'benchmark_test_id'>[]
): boolean {
  return tests.length > 0 && tests.every((test) => isTestSelected(state, bundleId, test));
}

export function countSelectedTests(
  state: TestSelectionState,
  bundleId: string,
  tests: Pick<BundleTest, 'name' | 'benchmark_test_id'>[]
): number {
  return tests.filter((test) => isTestSelected(state, bundleId, test)).length;
}

export function selectedTestsInBundle<T extends Pick<BundleTest, 'name' | 'benchmark_test_id'>>(
  state: TestSelectionState,
  bundleId: string,
  tests: T[]
): T[] {
  return tests.filter((test) => isTestSelected(state, bundleId, test));
}

export function countSelectedTestsAcrossBundles(
  state: TestSelectionState,
  bundleIds: string[]
): number {
  return bundleIds.reduce((acc, bundleId) => {
    const bundleState = state[bundleId];
    if (!bundleState) return acc;
    return acc + Object.values(bundleState).filter(Boolean).length;
  }, 0);
}

export function hasAnySelectedTestsInBundle(
  state: TestSelectionState,
  bundleId: string
): boolean {
  const bundleTests = state[bundleId];
  if (!bundleTests) return false;
  return Object.values(bundleTests).some(Boolean);
}
