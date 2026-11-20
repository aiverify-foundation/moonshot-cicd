import {
  areAllTestsSelected,
  buildPromptsByTest,
  getTestSelectionKey,
  hasAnySelectedTestsInBundle,
  isTestSelected,
  selectedTestsAcrossSelectedBundles,
  selectedTestsInBundle,
  type TestSelectionState,
} from '@/lib/benchmarkTestSelection';
import type { Bundle, BundleTest } from '@/lib/api';

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

  it('hasAnySelectedTestsInBundle returns true when at least one test is selected', () => {
    const state: TestSelectionState = {
      bundle_a: { '42': true, '99': false },
    };
    expect(hasAnySelectedTestsInBundle(state, 'bundle_a')).toBe(true);
  });

  it('hasAnySelectedTestsInBundle returns false when no tests are selected', () => {
    const state: TestSelectionState = {
      bundle_a: { '42': false },
    };
    expect(hasAnySelectedTestsInBundle(state, 'bundle_a')).toBe(false);
    expect(hasAnySelectedTestsInBundle(state, 'missing_bundle')).toBe(false);
  });
});

describe('selectedTestsAcrossSelectedBundles', () => {
  const duplicateName = 'Same Name';
  const testA: BundleTest = {
    name: duplicateName,
    benchmark_test_id: 10,
    requires_llm_aaj: true,
    metric_provider_system_name: 'together_adapter',
    dataset: {
      id: 'ds-a',
      name: 'DS A',
      description: '',
      num_of_dataset_prompts: 1,
    },
  };
  const testB: BundleTest = {
    name: duplicateName,
    benchmark_test_id: 20,
    requires_llm_aaj: true,
    metric_provider_system_name: 'openai_adapter',
    dataset: {
      id: 'ds-b',
      name: 'DS B',
      description: '',
      num_of_dataset_prompts: 1,
    },
  };
  const bundleA: Bundle = {
    id: 'bundle_a',
    name: 'Bundle A',
    description: '',
    category: 'cat',
    tests: [testA],
  };
  const bundleB: Bundle = {
    id: 'bundle_b',
    name: 'Bundle B',
    description: '',
    category: 'cat',
    tests: [testB],
  };

  it('excludes tests from bundles that are not selected', () => {
    const result = selectedTestsAcrossSelectedBundles(
      [bundleA, bundleB],
      { bundle_a: { '10': true }, bundle_b: { '20': true } },
      { bundle_a: true, bundle_b: false }
    );
    expect(result).toEqual([testA]);
  });

  it('does not conflate same display name across bundles', () => {
    const result = selectedTestsAcrossSelectedBundles(
      [bundleA, bundleB],
      { bundle_a: { '10': true }, bundle_b: { '20': false } },
      { bundle_a: true, bundle_b: true }
    );
    expect(result).toEqual([testA]);
    expect(result[0].metric_provider_system_name).toBe('together_adapter');
  });

  it('selects by benchmark_test_id when two tests share a name in one bundle', () => {
    const first: BundleTest = {
      name: duplicateName,
      benchmark_test_id: 1,
      dataset: testA.dataset,
    };
    const second: BundleTest = {
      name: duplicateName,
      benchmark_test_id: 2,
      dataset: testB.dataset,
    };
    const bundle: Bundle = {
      id: 'bundle_mixed',
      name: 'Mixed',
      description: '',
      category: 'cat',
      tests: [first, second],
    };
    const result = selectedTestsAcrossSelectedBundles(
      [bundle],
      { bundle_mixed: { '1': true, '2': false } },
      { bundle_mixed: true }
    );
    expect(result).toEqual([first]);
  });
});

const mockBundle: Bundle = {
  id: 'safety-bundle',
  name: 'Safety Bundle',
  description: '',
  category: 'Safety',
  tests: [
    {
      name: 'Test One',
      benchmark_test_id: 101,
      dataset: {
        id: 'ds1',
        name: 'ds1',
        description: '',
        num_of_dataset_prompts: 50,
      },
    },
    {
      name: 'Test Two',
      benchmark_test_id: 102,
      dataset: {
        id: 'ds2',
        name: 'ds2',
        description: '',
        num_of_dataset_prompts: 80,
      },
    },
  ],
};

describe('buildPromptsByTest', () => {
  it('maps each selected test to perTestSampleSize', () => {
    const result = buildPromptsByTest(
      [mockBundle],
      { 'safety-bundle': { '101': true, '102': false } },
      { 'safety-bundle': true },
      25
    );
    expect(result).toEqual({ map: { 101: 25 } });
  });

  it('includes all selected tests across bundles', () => {
    const bundleB: Bundle = {
      ...mockBundle,
      id: 'accuracy-bundle',
      name: 'Accuracy Bundle',
      tests: [
        {
          name: 'Accuracy Test',
          benchmark_test_id: 201,
          dataset: mockBundle.tests[0].dataset,
        },
      ],
    };
    const result = buildPromptsByTest(
      [mockBundle, bundleB],
      {
        'safety-bundle': { '101': true, '102': true },
        'accuracy-bundle': { '201': true },
      },
      { 'safety-bundle': true, 'accuracy-bundle': true },
      10
    );
    expect(result).toEqual({ map: { 101: 10, 102: 10, 201: 10 } });
  });

  it('returns error when benchmark_test_id is missing', () => {
    const bundleNoId: Bundle = {
      ...mockBundle,
      tests: [{ name: 'No Id Test', dataset: mockBundle.tests[0].dataset }],
    };
    const result = buildPromptsByTest(
      [bundleNoId],
      { 'safety-bundle': { 'No Id Test': true } },
      { 'safety-bundle': true },
      5
    );
    expect(result).toEqual({
      error: 'Missing benchmark id for test "No Id Test" in bundle "Safety Bundle".',
    });
  });
});
