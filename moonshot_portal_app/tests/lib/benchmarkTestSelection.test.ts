import {
  areAllTestsSelected,
  getTestSelectionKey,
  isTestSelected,
  selectedTestsInBundle,
  type TestSelectionState,
} from '@/lib/benchmarkTestSelection';
import type { BundleTest } from '@/lib/api';

const sharedTest: BundleTest = {
  name: 'Shared Recipe',
  benchmark_test_id: 42,
  dataset: {
    id: 'ds1',
    name: 'DS',
    description: '',
    num_of_dataset_prompts: 10,
  },
};

describe('benchmarkTestSelection', () => {
  it('uses benchmark_test_id as test key when present', () => {
    expect(getTestSelectionKey(sharedTest)).toBe('42');
  });

  it('falls back to test name when benchmark_test_id is missing', () => {
    const nameOnly: BundleTest = { name: 'Only Name', dataset: sharedTest.dataset };
    expect(getTestSelectionKey(nameOnly)).toBe('Only Name');
  });

  it('keeps selection independent per bundle for the same benchmark_test_id', () => {
    const state: TestSelectionState = {
      bundle_a: { '42': true },
      bundle_b: { '42': false },
    };

    expect(isTestSelected(state, 'bundle_a', sharedTest)).toBe(true);
    expect(isTestSelected(state, 'bundle_b', sharedTest)).toBe(false);
    expect(areAllTestsSelected(state, 'bundle_a', [sharedTest])).toBe(true);
    expect(areAllTestsSelected(state, 'bundle_b', [sharedTest])).toBe(false);
    expect(selectedTestsInBundle(state, 'bundle_a', [sharedTest])).toHaveLength(1);
    expect(selectedTestsInBundle(state, 'bundle_b', [sharedTest])).toHaveLength(0);
  });
});
