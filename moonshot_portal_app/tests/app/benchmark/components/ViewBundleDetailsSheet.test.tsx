import userEvent from '@testing-library/user-event';
import { render, screen, waitFor } from '@/tests/utils/test-utils';
import ViewBundleDetailsSheet from '@/app/benchmark/components/ViewBundleDetailsSheet';
import {
  getTestSelectionKey,
  hasAnySelectedTestsInBundle,
  isTestSelected,
} from '@/lib/benchmarkTestSelection';
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
      name: 'AILuminate Safety Classifier Test',
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

const accuracyTestKey = getTestSelectionKey(bundleWithoutAaj.tests[0]);

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

    expect(screen.getByText('Required Connectors for LLM-as-judge Models')).toBeInTheDocument();
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
    expect(screen.queryByText('Required Connectors for LLM-as-judge Models')).not.toBeInTheDocument();
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

  it('seeds checkboxes from global selection on open', async () => {
    render(
      <ViewBundleDetailsSheet open bundle={bundleWithoutAaj} onOpenChange={jest.fn()} />,
      {
        preloadedState: {
          bundles: { data: [bundleWithoutAaj], loading: false, error: null },
          testSelection: {
            'accuracy-bundle': { [accuracyTestKey]: true },
          },
          bundleSelection: { 'accuracy-bundle': true },
        },
      }
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Toggle test' })).toHaveTextContent('Selected');
    });
    expect(screen.getByRole('button', { name: /^Add/ })).toHaveTextContent('Add 1 test');
  });

  it('does not update global selection until Add is pressed', async () => {
    const user = userEvent.setup();
    const onOpenChange = jest.fn();

    const { store } = render(
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

    expect(
      isTestSelected(store.getState().testSelection, 'accuracy-bundle', bundleWithoutAaj.tests[0])
    ).toBe(false);
    expect(store.getState().bundleSelection['accuracy-bundle']).toBeFalsy();

    await user.click(screen.getByRole('button', { name: 'Add 1 test' }));

    expect(
      isTestSelected(store.getState().testSelection, 'accuracy-bundle', bundleWithoutAaj.tests[0])
    ).toBe(true);
    expect(store.getState().bundleSelection['accuracy-bundle']).toBe(true);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it('discards draft changes on Close and re-seeds from global on reopen', async () => {
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
    expect(screen.getByRole('button', { name: 'Toggle test' })).toHaveTextContent('Selected');

    const closeButtons = screen.getAllByRole('button', { name: 'Close' });
    await user.click(closeButtons[closeButtons.length - 1]);
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(
      hasAnySelectedTestsInBundle(store.getState().testSelection, 'accuracy-bundle')
    ).toBe(false);

    rerender(
      <ViewBundleDetailsSheet
        open={false}
        bundle={bundleWithoutAaj}
        onOpenChange={onOpenChange}
      />
    );
    rerender(
      <ViewBundleDetailsSheet
        open
        bundle={bundleWithoutAaj}
        onOpenChange={onOpenChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Toggle test' })).toHaveTextContent('Select');
    });
  });

  it('commits deselection on Add and removes bundle when all tests are cleared', async () => {
    const user = userEvent.setup();
    const onOpenChange = jest.fn();

    const { store } = render(
      <ViewBundleDetailsSheet
        open
        bundle={bundleWithoutAaj}
        onOpenChange={onOpenChange}
      />,
      {
        preloadedState: {
          bundles: { data: [bundleWithoutAaj], loading: false, error: null },
          testSelection: {
            'accuracy-bundle': { [accuracyTestKey]: true },
          },
          bundleSelection: { 'accuracy-bundle': true },
        },
      }
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Toggle test' })).toHaveTextContent('Selected');
    });

    await user.click(screen.getByRole('button', { name: 'Toggle test' }));
    await user.click(screen.getByRole('button', { name: /^Add/ }));

    expect(store.getState().bundleSelection['accuracy-bundle']).toBe(false);
    expect(
      hasAnySelectedTestsInBundle(store.getState().testSelection, 'accuracy-bundle')
    ).toBe(false);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
