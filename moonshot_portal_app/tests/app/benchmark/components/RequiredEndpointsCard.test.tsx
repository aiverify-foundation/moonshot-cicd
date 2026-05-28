import userEvent from '@testing-library/user-event';
import { render, screen, waitFor } from '@/tests/utils/test-utils';
import RequiredEndpointsCard, {
  aajEndpointStatusKey,
  ConnectionStatus,
  isAajEndpointAccepted,
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

describe('isAajEndpointAccepted', () => {
  it('accepts when Redux is connected', () => {
    expect(
      isAajEndpointAccepted(ConnectionStatus.CONNECTED, false)
    ).toBe(true);
  });

  it('accepts when API key is configured in DB', () => {
    expect(
      isAajEndpointAccepted(ConnectionStatus.NOT_CONNECTED, true)
    ).toBe(true);
  });

  it('rejects when neither connected nor key configured', () => {
    expect(
      isAajEndpointAccepted(ConnectionStatus.NOT_CONNECTED, false)
    ).toBe(false);
  });

  it('rejects invalid token even when API key is configured', () => {
    expect(
      isAajEndpointAccepted(ConnectionStatus.INVALID_TOKEN, true)
    ).toBe(false);
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

  const defaultPreloadedState = {
    bundles: {
      data: [bundleWithAaj],
      loading: false,
      error: null,
    },
    bundleSelection: { bundle_one: true },
    testSelection: { bundle_one: { 'Recipe A': true } },
  };

  const renderCard = (preloadedState?: Record<string, unknown>) =>
    render(<RequiredEndpointsCard />, {
      preloadedState: { ...defaultPreloadedState, ...preloadedState },
    });

  beforeEach(() => {
    mockSetLlmProviderApiKey.mockClear();
    mockFetchProviderLatestDetails.mockClear();
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

  it('shows updated required endpoints card copy', async () => {
    renderCard();

    expect(screen.getByTestId('additional-card-title')).toHaveTextContent(
      'Connect Required Endpoints',
    );
    expect(screen.getByTestId('additional-card-description')).toHaveTextContent(
      'Configure access to LLM-as-judge providers required by your selected tests.',
    );
  });

  it('shows an LLM judge card for selected AAJ tests after providers load', async () => {
    renderCard();

    await waitFor(() => {
      expect(screen.getByText('Together AI (LLM judge)')).toBeInTheDocument();
    });
    expect(screen.getByText('Recipe A')).toBeInTheDocument();
    expect(mockFetchProviderLatestDetails).toHaveBeenCalledWith('together_adapter');
  });

  it('shows green indicator and connected badge when DB key exists only', async () => {
    mockFetchProviderLatestDetails.mockResolvedValue({
      api_key_configured: true,
      database_model_configs: [],
      models: [],
      provider: { id: '42', name: 'Together AI', system_name: 'together_adapter' },
    });

    renderCard({ endpointStatus: {} });

    await waitFor(() => {
      expect(screen.getByTestId('required-endpoints-status-indicator')).toHaveClass(
        'text-green-500'
      );
    });
    expect(screen.getByText('connected')).toBeInTheDocument();
  });

  it('shows green indicator when Redux connected and DB key absent', async () => {
    mockFetchProviderLatestDetails.mockResolvedValue({
      api_key_configured: false,
      database_model_configs: [],
      models: [],
      provider: { id: '42', name: 'Together AI', system_name: 'together_adapter' },
    });

    renderCard({
      endpointStatus: { [aajEndpointStatusKey('together_adapter')]: 'connected' },
    });

    await waitFor(() => {
      expect(screen.getByText('Together AI (LLM judge)')).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByTestId('required-endpoints-status-indicator')).toHaveClass(
        'text-green-500'
      );
    });
    expect(screen.getByText('connected')).toBeInTheDocument();
  });

  it('shows red indicator and not connected when neither Redux nor DB key', async () => {
    mockFetchProviderLatestDetails.mockResolvedValue({
      api_key_configured: false,
      database_model_configs: [],
      models: [],
      provider: { id: '42', name: 'Together AI', system_name: 'together_adapter' },
    });

    renderCard({ endpointStatus: {} });

    await waitFor(() => {
      expect(screen.getByTestId('required-endpoints-status-indicator')).toHaveClass(
        'text-red-500'
      );
    });
    expect(screen.getByText('not connected')).toBeInTheDocument();
  });

  it('shows red indicator when Redux has invalid token even if DB key exists', async () => {
    mockFetchProviderLatestDetails.mockResolvedValue({
      api_key_configured: true,
      database_model_configs: [],
      models: [],
      provider: { id: '42', name: 'Together AI', system_name: 'together_adapter' },
    });

    renderCard({
      endpointStatus: {
        [aajEndpointStatusKey('together_adapter')]: ConnectionStatus.INVALID_TOKEN,
      },
    });

    await waitFor(() => {
      expect(screen.getByTestId('required-endpoints-status-indicator')).toHaveClass(
        'text-red-500'
      );
    });
    expect(screen.getByText(ConnectionStatus.INVALID_TOKEN)).toBeInTheDocument();
  });

  it('opens Add Provider Token sheet and marks endpoint connected on Save when key exists', async () => {
    const user = userEvent.setup();
    const { store } = renderCard({ endpointStatus: {} });

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
