import userEvent from '@testing-library/user-event';
import { render, screen, waitFor } from '@/tests/utils/test-utils';
import ViewTestApp from '@/app/view_test/components/ViewTestApp';
import type { Bundle } from '@/lib/api';
import { FeatureFlagNames } from '@/lib/featureFlags';

const mockFetchBundles = jest.fn();
const mockIsEnabled = jest.fn<boolean, [string]>(() => false);

jest.mock('next/navigation', () => ({
  useSearchParams: jest.fn(),
}));

jest.mock('@/lib/api', () => ({
  fetchBundles: (...args: unknown[]) => mockFetchBundles(...args),
}));

jest.mock('@/hooks/useFeatureFlags', () => ({
  useFeatureFlags: () => ({
    flags: {},
    loading: false,
    isEnabled: mockIsEnabled,
  }),
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
        metric_connector_pre_prompt: 'PRE PROMPT TEXT',
        metric_connector_post_prompt: 'POST PROMPT TEXT',
        dataset: {
          id: 'ds-1',
          name: 'ds-1',
          description: '',
          num_of_dataset_prompts: 42,
        },
        metric: { name: 'ailuminate_safety_classifier_adapter' },
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

describe('ViewTestApp', () => {
  beforeEach(() => {
    mockFetchBundles.mockReset();
    mockIsEnabled.mockReset();
    mockIsEnabled.mockReturnValue(false);
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

    render(<ViewTestApp />);

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1, name: 'Sample Test' })).toBeInTheDocument();
    });

    expect(screen.getByText('Test description from API')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('meta-llama/Llama-Guard-4-12B')).toBeInTheDocument();
    expect(screen.queryByText('ailuminate_safety_classifier_adapter')).not.toBeInTheDocument();
    expect(screen.queryByText('Together AI')).not.toBeInTheDocument();
    expect(screen.getByText('API input text')).toBeInTheDocument();
    expect(screen.getByText('API response text')).toBeInTheDocument();
    expect(screen.getByText('safe')).toBeInTheDocument();
  });

  it('hides System Prompt UI when feature flag is off', async () => {
    mockFetchBundles.mockResolvedValue(bundleWithDetails);

    render(<ViewTestApp />);

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1, name: 'Sample Test' })).toBeInTheDocument();
    });

    expect(screen.queryByTestId('view-test-system-prompt-label')).not.toBeInTheDocument();
    expect(screen.queryByTestId('view-test-system-prompt-info')).not.toBeInTheDocument();
    expect(screen.queryByTestId('system-prompt-sheet')).not.toBeInTheDocument();
  });

  it('shows System Prompt info sheet when feature flag is on', async () => {
    mockIsEnabled.mockImplementation(
      (name: string) => name === FeatureFlagNames.AIVET_OCT2026_MOON687,
    );
    mockFetchBundles.mockResolvedValue(bundleWithDetails);
    const user = userEvent.setup();

    render(<ViewTestApp />);

    await waitFor(() => {
      expect(screen.getByTestId('view-test-system-prompt-label')).toBeInTheDocument();
    });

    expect(screen.getByText('System Prompt')).toBeInTheDocument();
    expect(screen.getByTestId('view-test-system-prompt-separator')).toBeInTheDocument();

    await user.click(screen.getByTestId('view-test-system-prompt-info'));

    expect(screen.getByTestId('system-prompt-sheet')).toBeInTheDocument();
    expect(screen.getByTestId('system-prompt-sheet-title')).toHaveTextContent('Sample Test');
    expect(screen.getByTestId('system-prompt-pre')).toHaveTextContent('PRE PROMPT TEXT');
    expect(screen.getByTestId('system-prompt-post')).toHaveTextContent('POST PROMPT TEXT');
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

    render(<ViewTestApp />);

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

    render(<ViewTestApp />);

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

    render(<ViewTestApp />);

    expect(
      screen.getByText(/Missing test or dataset in the URL/i),
    ).toBeInTheDocument();
    expect(mockFetchBundles).not.toHaveBeenCalled();
  });
});
