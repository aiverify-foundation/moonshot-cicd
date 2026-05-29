import { render, screen, waitFor } from '@/tests/utils/test-utils';
import ViewBundleDetailsSheet from '@/app/benchmark/components/ViewBundleDetailsSheet';
import type { Bundle } from '@/lib/api';

const mockFetchProviders = jest.fn();

jest.mock('@/lib/api', () => ({
  fetchProviders: (...args: unknown[]) => mockFetchProviders(...args),
}));

const bundleWithAaj: Bundle = {
  id: 'safety-bundle',
  name: 'Safety Bundle',
  description: 'Bundle with AAJ tests',
  category: 'Safety',
  prompt_count: 10,
  tests: [
    {
      name: 'Llama Guard Test',
      requires_llm_aaj: true,
      metric_provider_system_name: 'together_adapter',
      dataset: {
        id: 'ds-1',
        name: 'ds-1',
        description: '',
        num_of_dataset_prompts: 5,
      },
    },
    {
      name: 'Refusal Test',
      requires_llm_aaj: true,
      metric_provider_system_name: 'openai_adapter',
      dataset: {
        id: 'ds-2',
        name: 'ds-2',
        description: '',
        num_of_dataset_prompts: 5,
      },
    },
  ],
};

const bundleWithoutAaj: Bundle = {
  id: 'accuracy-bundle',
  name: 'Accuracy Bundle',
  description: 'No judge providers',
  category: 'Quality',
  prompt_count: 3,
  tests: [
    {
      name: 'Accuracy Test',
      requires_llm_aaj: false,
      dataset: {
        id: 'ds-3',
        name: 'ds-3',
        description: '',
        num_of_dataset_prompts: 3,
      },
      metric: { name: 'accuracy_adapter' },
    },
  ],
};

describe('ViewBundleDetailsSheet', () => {
  beforeEach(() => {
    mockFetchProviders.mockReset();
    mockFetchProviders.mockResolvedValue([
      {
        id: '1',
        name: 'OpenAI',
        system_name: 'openai_adapter',
        version: 1,
      },
      {
        id: '42',
        name: 'Together AI',
        system_name: 'together_adapter',
        version: 1,
      },
    ]);
  });

  it('shows required endpoint connectors with provider names', async () => {
    render(
      <ViewBundleDetailsSheet open bundle={bundleWithAaj} onOpenChange={jest.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByTestId('required-endpoint-connectors')).toBeInTheDocument();
      expect(screen.getByText('Together AI')).toBeInTheDocument();
    });

    expect(screen.getByText('Required Endpoint Connectors')).toBeInTheDocument();
    expect(screen.getByText('OpenAI')).toBeInTheDocument();
    expect(screen.queryByText('Llama-Guard-2-8B')).not.toBeInTheDocument();
  });

  it('hides required endpoint connectors when bundle has no AAJ tests', async () => {
    render(
      <ViewBundleDetailsSheet open bundle={bundleWithoutAaj} onOpenChange={jest.fn()} />
    );

    await waitFor(() => {
      expect(mockFetchProviders).toHaveBeenCalled();
    });

    expect(screen.queryByTestId('required-endpoint-connectors')).not.toBeInTheDocument();
    expect(screen.queryByText('Required Endpoint Connectors')).not.toBeInTheDocument();
  });

  it('does not fetch providers when sheet is closed', () => {
    render(
      <ViewBundleDetailsSheet
        open={false}
        bundle={bundleWithAaj}
        onOpenChange={jest.fn()}
      />
    );

    expect(mockFetchProviders).not.toHaveBeenCalled();
  });
});
