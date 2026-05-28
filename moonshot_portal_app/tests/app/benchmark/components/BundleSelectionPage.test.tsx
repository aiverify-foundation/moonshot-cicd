import { render, screen } from '@/tests/utils/test-utils';
import BundleSelectionPage from '@/app/benchmark/components/BundleSelectionPage';
import type { Bundle } from '@/lib/api';

const mockBundles: Bundle[] = [
  {
    id: 'safety-bundle',
    name: 'Safety Bundle',
    description: 'Bundle description text',
    category: 'Safety',
    tests: [
      {
        name: 'Test One',
        dataset: {
          id: 'ds-1',
          name: 'ds-1',
          description: '',
          num_of_dataset_prompts: 5,
        },
      },
    ],
    prompt_count: 5,
  },
];

jest.mock('@/hooks/useBundlesRedux', () => ({
  useBundlesRedux: () => ({
    bundles: mockBundles,
    loading: false,
    error: null,
    refetch: jest.fn(),
  }),
}));

jest.mock('@/app/benchmark/components/ViewBundleDetailsSheet', () => () => null);

describe('BundleSelectionPage', () => {
  it('shows updated bundle selection header and description copy', () => {
    render(<BundleSelectionPage />);

    expect(screen.getByTestId('select-bundles-header')).toHaveTextContent(
      'Select Test Bundles',
    );
    expect(screen.getByTestId('select-bundles-description')).toHaveTextContent(
      'Select suitable bundles for your benchmark test',
    );
    expect(screen.getByTestId('Breadcrumb')).toHaveTextContent(
      'Select Tests Or Test Bundles',
    );
  });
});
