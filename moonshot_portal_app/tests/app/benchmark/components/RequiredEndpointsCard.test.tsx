import userEvent from '@testing-library/user-event';
import { createTestStore, render, screen, waitFor } from '@/tests/utils/test-utils';
import RequiredEndpointsCard, {
  aajEndpointStatusKey,
} from '@/app/benchmark/components/RequiredEndpointsCard';
import type { Bundle } from '@/lib/api';

const mockFetchProviders = jest.fn();
const mockFetchProviderLatestDetails = jest.fn();
const mockSetLlmProviderApiKey = jest.fn().mockResolvedValue({ message: 'API key stored' });

jest.mock('@/lib/api', () => {
  const actual = jest.requireActual('@/lib/api') as Record<string, unknown>;
  return {
    ...actual,
    fetchProviders: (...args: unknown[]) => mockFetchProviders(...args),
    fetchProviderLatestDetails: (...args: unknown[]) =>
      mockFetchProviderLatestDetails(...args),
    setLlmProviderApiKey: (...args: unknown[]) => mockSetLlmProviderApiKey(...args),
  };
});

describe('aajEndpointStatusKey', () => {
  it('prefixes system name for Redux', () => {
    expect(aajEndpointStatusKey('together_adapter')).toBe('aaj:together_adapter');
  });
});

describe('RequiredEndpointsCard', () => {
  const bundleWithAaj: Bundle = {
    id: 'bundle_one',
    name: 'Bundle One',
    description: '',
    category: 'cat',
    tests: [
      {
        name: 'Recipe A',
        requires_llm_aaj: true,
        metric_provider_system_name: 'together_adapter',
        dataset: {
          id: 'ds1',
          name: 'DS',
          description: '',
          num_of_dataset_prompts: 1,
        },
      },
    ],
  };

  beforeEach(() => {
    mockSetLlmProviderApiKey.mockClear();
    mockFetchProviders.mockResolvedValue([
      {
        id: '42',
        name: 'Together AI',
        system_name: 'together_adapter',
        version: 1,
      },
    ]);
    mockFetchProviderLatestDetails.mockResolvedValue({
      api_key_configured: true,
      database_model_configs: [],
      models: [{ id: 10, name: 'meta-llama/Llama-Guard-2-8B', create_dt: '2026-01-01T00:00:00Z' }],
      provider: { id: '42', name: 'Together AI', system_name: 'together_adapter' },
    });
  });

  it('shows an LLM judge card for selected AAJ tests after providers load', async () => {
    render(<RequiredEndpointsCard />, {
      preloadedState: {
        bundles: {
          data: [bundleWithAaj],
          loading: false,
          error: null,
        },
        testSelection: { 'Recipe A': true },
      },
    });

    await waitFor(() => {
      expect(screen.getByText('Together AI (LLM judge)')).toBeInTheDocument();
    });
    expect(screen.getByText('Recipe A')).toBeInTheDocument();
  });

  it('opens Add Provider Token sheet and marks endpoint connected on Save when key exists', async () => {
    const user = userEvent.setup();
    const { store } = render(<RequiredEndpointsCard />, {
      preloadedState: {
        bundles: {
          data: [bundleWithAaj],
          loading: false,
          error: null,
        },
        testSelection: { 'Recipe A': true },
      },
    });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Connect' })).toBeInTheDocument();
    });
    await user.click(screen.getByRole('button', { name: 'Connect' }));

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
    expect(screen.getByRole('dialog')).toHaveTextContent('Add Provider Token');
    expect(screen.getByRole('dialog')).toHaveTextContent('Model Provider*');

    await user.click(screen.getByRole('button', { name: /Test/i }));
    await user.click(screen.getByRole('button', { name: /^Save$/ }));

    await waitFor(() => {
      expect(store.getState().endpointStatus[aajEndpointStatusKey('together_adapter')]).toBe(
        'connected'
      );
    });
    expect(mockSetLlmProviderApiKey).not.toHaveBeenCalled();
  });
});
