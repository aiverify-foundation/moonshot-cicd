import { mapBundlesToHazardSections } from '@/app/test_result/pdf/mapBundlesToHazardSections';
import type { Bundle, BundleTest } from '@/lib/api';
import { IMDA_STARTER_KIT_CATEGORY } from '@/lib/bundles';

function makeTest(overrides: Partial<BundleTest> & { name: string }): BundleTest {
  return {
    description: 'default desc',
    dataset: {
      id: 'ds',
      name: 'Dataset',
      description: '',
      num_of_dataset_prompts: 1,
    },
    ...overrides,
  };
}

function makeBundle(
  overrides: Partial<Bundle> & { id: string; name: string; category: string }
): Bundle {
  return {
    description: '',
    tests: [],
    ...overrides,
  };
}

describe('mapBundlesToHazardSections', () => {
  it('keeps only IMDA Starter Kit bundles and maps name/description fields', () => {
    const bundles: Bundle[] = [
      makeBundle({
        id: 'demo',
        name: 'Sample Test Bundle',
        category: 'For Testing/ Demo',
        tests: [makeTest({ name: 'Demo Test', description: 'Should be excluded' })],
      }),
      makeBundle({
        id: 'undesirable-content',
        name: 'Undesirable Content',
        category: IMDA_STARTER_KIT_CATEGORY,
        tests: [
          makeTest({
            name: 'MLCommons AILuminate - Violent Crimes',
            description: 'Measures ability to respond without enabling violent crimes.',
          }),
          makeTest({
            name: 'MLCommons AILuminate - Hate',
            description: 'Measures ability to respond without demeaning people.',
          }),
        ],
      }),
      makeBundle({
        id: 'adversarial-prompts',
        name: 'Adversarial Prompts',
        category: IMDA_STARTER_KIT_CATEGORY,
        tests: [
          makeTest({
            name: 'CyberSecEval - Prompt Injections 3',
            description: 'Tests for susceptibility to prompt attacks.',
          }),
        ],
      }),
    ];

    expect(mapBundlesToHazardSections(bundles)).toEqual([
      {
        tag: 'Undesirable Content',
        items: [
          {
            title: 'MLCommons AILuminate - Violent Crimes',
            desc: 'Measures ability to respond without enabling violent crimes.',
          },
          {
            title: 'MLCommons AILuminate - Hate',
            desc: 'Measures ability to respond without demeaning people.',
          },
        ],
      },
      {
        tag: 'Adversarial Prompts',
        items: [
          {
            title: 'CyberSecEval - Prompt Injections 3',
            desc: 'Tests for susceptibility to prompt attacks.',
          },
        ],
      },
    ]);
  });

  it('uses empty string when test description is missing', () => {
    const bundles: Bundle[] = [
      makeBundle({
        id: 'undesirable-content',
        name: 'Undesirable Content',
        category: IMDA_STARTER_KIT_CATEGORY,
        tests: [makeTest({ name: 'Hate', description: undefined })],
      }),
    ];

    expect(mapBundlesToHazardSections(bundles)).toEqual([
      {
        tag: 'Undesirable Content',
        items: [{ title: 'Hate', desc: '' }],
      },
    ]);
  });

  it('returns an empty list when no IMDA Starter Kit bundles exist', () => {
    const bundles: Bundle[] = [
      makeBundle({
        id: 'demo',
        name: 'Sample',
        category: 'For Testing/ Demo',
        tests: [makeTest({ name: 'X' })],
      }),
    ];

    expect(mapBundlesToHazardSections(bundles)).toEqual([]);
  });
});
