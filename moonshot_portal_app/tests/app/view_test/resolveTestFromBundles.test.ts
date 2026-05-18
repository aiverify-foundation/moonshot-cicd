import type { Bundle } from '@/lib/api';
import { findTestInBundles } from '@/app/view_test/resolveTestFromBundles';

const sampleBundles: Bundle[] = [
  {
    id: 'undesirable-content',
    name: 'Undesirable Content',
    description: '',
    category: 'Safety',
    tests: [
      {
        name: 'MLCommons AILuminate - Violent Crimes',
        dataset: {
          id: 'mlc-ailuminate-vcr',
          name: 'mlc-ailuminate-vcr',
          description: '',
          num_of_dataset_prompts: 100,
        },
        metric: { name: 'llamaguardannotator_adapter' },
        details: [
          {
            category_name: 'Cat',
            dataset: 'mlc-ailuminate-vcr',
            hazard: 'vcr',
            input: 'prompt one',
            target: 't1',
            response: 'r1',
            evaluator_verdict: '1',
          },
        ],
      },
    ],
  },
];

describe('findTestInBundles', () => {
  it('finds test by name and dataset id', () => {
    const found = findTestInBundles(
      sampleBundles,
      'MLCommons AILuminate - Violent Crimes',
      'mlc-ailuminate-vcr',
    );

    expect(found?.name).toBe('MLCommons AILuminate - Violent Crimes');
    expect(found?.details).toHaveLength(1);
    expect(found?.details?.[0].input).toBe('prompt one');
  });

  it('decodes URI-encoded query params', () => {
    const found = findTestInBundles(
      sampleBundles,
      encodeURIComponent('MLCommons AILuminate - Violent Crimes'),
      'mlc-ailuminate-vcr',
    );

    expect(found).toBeDefined();
  });

  it('returns undefined when no match', () => {
    expect(
      findTestInBundles(sampleBundles, 'Unknown Test', 'mlc-ailuminate-vcr'),
    ).toBeUndefined();
    expect(
      findTestInBundles(
        sampleBundles,
        'MLCommons AILuminate - Violent Crimes',
        'wrong-dataset',
      ),
    ).toBeUndefined();
  });
});
