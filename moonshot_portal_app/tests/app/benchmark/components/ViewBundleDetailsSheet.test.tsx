import userEvent from '@testing-library/user-event';
import { render, screen, waitFor } from '@/tests/utils/test-utils';
import ViewBundleDetailsSheet from '@/app/benchmark/components/ViewBundleDetailsSheet';
import { hasAnySelectedTestsInBundle } from '@/lib/benchmarkTestSelection';
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

  it('removes bundle from selection when all tests are deselected after Add', async () => {
    const user = userEvent.setup();
    const onOpenChange = jest.fn();

    const { store, rerender } = render(
      <ViewBundleDetailsSheet
        open
        bundle={bundleWithoutAaj}
        onOpenChange={onOpenChange}
      />,
      {
        preloadedState: {
          bundles: { data: [bundleWithoutAaj], loading: false, error: null },
        },
      }
    );

    await waitFor(() => {
      expect(mockFetchProviders).toHaveBeenCalled();
    });

    await user.click(screen.getByRole('button', { name: 'Toggle test' }));
    await user.click(screen.getByRole('button', { name: 'Add 1 test' }));

    expect(store.getState().bundleSelection['accuracy-bundle']).toBe(true);
    expect(onOpenChange).toHaveBeenCalledWith(false);

    rerender(
      <ViewBundleDetailsSheet
        open
        bundle={bundleWithoutAaj}
        onOpenChange={onOpenChange}
      />
    );

    await user.click(screen.getByRole('button', { name: 'Toggle test' }));

    expect(store.getState().bundleSelection['accuracy-bundle']).toBe(false);
    expect(
      hasAnySelectedTestsInBundle(
        store.getState().testSelection,
        'accuracy-bundle'
      )
    ).toBe(false);
  });
});
