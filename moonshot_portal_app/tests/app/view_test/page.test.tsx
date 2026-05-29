import { render, screen, waitFor } from '@/tests/utils/test-utils';
import ViewTest from '@/app/view_test/page';
import type { Bundle } from '@/lib/api';

const mockFetchBundles = jest.fn();

jest.mock('next/navigation', () => ({
  useSearchParams: jest.fn(),
}));

jest.mock('@/lib/api', () => ({
  fetchBundles: (...args: unknown[]) => mockFetchBundles(...args),
}));

function getUseSearchParamsMock() {
  return (
    jest.requireMock('next/navigation') as {
      useSearchParams: jest.Mock;
    }
  ).useSearchParams;
}

const bundleWithDetails: Bundle[] = [
  {
    id: 'undesirable-content',
    name: 'Undesirable Content',
    description: '',
    category: 'Safety',
    tests: [
      {
        name: 'Sample Test',
        description: 'Test description from API',
        requires_llm_aaj: true,
        metric_provider_system_name: 'together_adapter',
        metric_grader_model_name: 'meta-llama/Llama-Guard-4-12B',
        dataset: {
          id: 'ds-1',
          name: 'ds-1',
          description: '',
          num_of_dataset_prompts: 42,
        },
        metric: { name: 'llamaguardannotator_adapter' },
        details: [
          {
            category_name: 'Cat',
            dataset: 'ds-1',
            hazard: 'h1',
            input: 'API input text',
            target: 'tgt',
            response: 'API response text',
            evaluator_verdict: 'safe',
          },
        ],
      },
    ],
  },
];

describe('ViewTest page', () => {
  beforeEach(() => {
    mockFetchBundles.mockReset();
    getUseSearchParamsMock().mockReturnValue({
      get: (key: string) => {
        if (key === 'test') return 'Sample Test';
        if (key === 'dataset') return 'ds-1';
        return null;
      },
    });
  });

  it('renders test metadata and detail rows from API', async () => {
    mockFetchBundles.mockResolvedValue(bundleWithDetails);

    render(<ViewTest />);

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1, name: 'Sample Test' })).toBeInTheDocument();
    });

    expect(screen.getByText('Test description from API')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('meta-llama/Llama-Guard-4-12B')).toBeInTheDocument();
    expect(screen.queryByText('llamaguardannotator_adapter')).not.toBeInTheDocument();
    expect(screen.queryByText('Together AI')).not.toBeInTheDocument();
    expect(screen.getByText('API input text')).toBeInTheDocument();
    expect(screen.getByText('API response text')).toBeInTheDocument();
    expect(screen.getByText('safe')).toBeInTheDocument();
  });

  it('shows em dash for Model Name when no grader model is configured', async () => {
    mockFetchBundles.mockResolvedValue([
      {
        ...bundleWithDetails[0],
        tests: [
          {
            ...bundleWithDetails[0].tests[0],
            requires_llm_aaj: false,
            metric_provider_system_name: null,
            metric_grader_model_name: null,
            metric: { name: 'accuracy_adapter' },
          },
        ],
      },
    ]);

    render(<ViewTest />);

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1, name: 'Sample Test' })).toBeInTheDocument();
    });

    expect(screen.getByText('—')).toBeInTheDocument();
    expect(screen.queryByText('accuracy_adapter')).not.toBeInTheDocument();
  });

  it('shows empty state when details is null', async () => {
    mockFetchBundles.mockResolvedValue([
      {
        ...bundleWithDetails[0],
        tests: [{ ...bundleWithDetails[0].tests[0], details: null }],
      },
    ]);

    render(<ViewTest />);

    await waitFor(() => {
      expect(
        screen.getByText('No sample prompts available for this dataset.'),
      ).toBeInTheDocument();
    });
  });

  it('shows error when query params are missing', async () => {
    getUseSearchParamsMock().mockReturnValue({
      get: () => null,
    });

    render(<ViewTest />);

    expect(
      screen.getByText(/Missing test or dataset in the URL/i),
    ).toBeInTheDocument();
    expect(mockFetchBundles).not.toHaveBeenCalled();
  });
});
