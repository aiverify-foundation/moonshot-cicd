import userEvent from '@testing-library/user-event';
import { render, screen, waitFor } from '@/tests/utils/test-utils';
import ModelSelectionPage from '@/app/benchmark/components/ModelSelectionPage';

const mockFetchProviders = jest.fn();
const mockFetchProviderLatestDetails = jest.fn();
const mockFetchCustomApps = jest.fn();
const mockFetchCustomAppConfigs = jest.fn();

jest.mock('@/lib/api', () => {
  const actual = jest.requireActual('@/lib/api') as Record<string, unknown>;
  return {
    ...actual,
    fetchProviders: (...args: unknown[]) => mockFetchProviders(...args),
    fetchProviderLatestDetails: (...args: unknown[]) =>
      mockFetchProviderLatestDetails(...args),
    fetchCustomApps: (...args: unknown[]) => mockFetchCustomApps(...args),
    fetchCustomAppConfigs: (...args: unknown[]) => mockFetchCustomAppConfigs(...args),
  };
});

jest.mock('@/app/benchmark/components/TestNameCard', () => () => (
  <div data-testid="test-name-card" />
));

jest.mock('@/app/benchmark/components/RequiredEndpointsCard', () => () => (
  <div data-testid="required-endpoints-card" />
));

jest.mock('@/app/benchmark/components/SampleSizeCard', () => () => (
  <div data-testid="sample-size-card" />
));

jest.mock('@/app/benchmark/components/SelectAppOrModelCard', () => {
  return function MockSelectAppOrModelCard(props: {
    models: Array<{ id: string; name: string }>;
    onModelsSaved?: (savedConfig: {
      id: string;
      name: string;
      modelname: string;
      modelId: number;
      providerID: string;
      savedConfigPairs: Record<string, string>;
      lastUpdated: string;
    }) => void | Promise<void>;
  }) {
    return (
      <div>
        <div data-testid="model-rows">
          {props.models.map((model) => `${model.id}:${model.name}`).join('|')}
        </div>
        <button
          type="button"
          onClick={() =>
            void props.onModelsSaved?.({
              id: '20',
              name: 'My Config',
              modelname: 'gpt-4.1',
              modelId: 11,
              providerID: 'test_provider',
              savedConfigPairs: {},
              lastUpdated: '2026-01-02T00:00:00Z',
            })
          }
        >
          Save Model
        </button>
      </div>
    );
  };
});

describe('ModelSelectionPage', () => {
  beforeEach(() => {
    mockFetchProviders.mockReset();
    mockFetchProviderLatestDetails.mockReset();
    mockFetchCustomApps.mockReset();
    mockFetchCustomAppConfigs.mockReset();
    mockFetchProviders.mockResolvedValue([
      {
        id: '1',
        name: 'Test Provider',
        system_name: 'test_provider',
        version: 1,
        defaultModel: 'gpt-4',
      },
    ]);
    mockFetchCustomApps.mockResolvedValue([]);
    mockFetchCustomAppConfigs.mockResolvedValue([]);
  });

  it('shows updated model selection breadcrumb copy', async () => {
    render(<ModelSelectionPage />);

    await waitFor(() => {
      expect(screen.getByTestId('Breadcrumb')).toHaveTextContent(
        'Select Tests Or Test Bundles',
      );
      expect(screen.getByTestId('Breadcrumb')).toHaveTextContent(
        'Select Model Or Application',
      );
      expect(screen.getByTestId('select-model-header')).toHaveTextContent(
        'Configure And Run Tests',
      );
    });
  });

  it('keeps the repointed config selected and hides the old raw model row after save', async () => {
    const user = userEvent.setup();
    mockFetchProviderLatestDetails
      .mockResolvedValueOnce({
        api_key_configured: true,
        database_model_configs: [
          {
            id: '20',
            name: 'My Config',
            modelname: 'gpt-4',
            modelId: 10,
            providerID: 'test_provider',
            savedConfigPairs: {},
            lastUpdated: '2026-01-01T00:00:00Z',
          },
        ],
        models: [{ id: 10, name: 'gpt-4', create_dt: '2026-01-01T00:00:00Z' }],
        provider: { id: '1', name: 'Test Provider', system_name: 'test_provider' },
      })
      .mockResolvedValueOnce({
        api_key_configured: true,
        database_model_configs: [
          {
            id: '20',
            name: 'My Config',
            modelname: 'gpt-4.1',
            modelId: 11,
            providerID: 'test_provider',
            savedConfigPairs: {},
            lastUpdated: '2026-01-02T00:00:00Z',
          },
        ],
        models: [
          { id: 10, name: 'gpt-4', create_dt: '2026-01-01T00:00:00Z' },
          { id: 11, name: 'gpt-4.1', create_dt: '2026-01-02T00:00:00Z' },
        ],
        provider: { id: '1', name: 'Test Provider', system_name: 'test_provider' },
      });

    const { store } = render(<ModelSelectionPage />, {
      preloadedState: {
        modelSelection: {
          selectedProvider: '1',
          selectedModel: '10:20',
          selectedConfig: '',
          isConfigValid: true,
          isTestNameValid: true,
          testName: 'benchmark',
          benchmarkLlmProviderId: 1,
          benchmarkLlmProviderModelId: 10,
          benchmarkLlmProviderModelConfigId: 20,
          benchmarkCustomAppId: null,
          benchmarkCustomAppConfigId: null,
        },
      },
    });

    await waitFor(() => {
      expect(screen.getByTestId('model-rows')).toHaveTextContent('10:20:My Config');
    });

    await user.click(screen.getByRole('button', { name: 'Save Model' }));

    await waitFor(() => {
      expect(screen.getByTestId('model-rows')).toHaveTextContent('11:20:My Config');
    });
    expect(screen.getByTestId('model-rows')).not.toHaveTextContent('10:gpt-4');

    await waitFor(() => {
      expect(store.getState().modelSelection.selectedModel).toBe('11:20');
    });
    expect(store.getState().modelSelection.benchmarkLlmProviderModelId).toBe(11);
    expect(store.getState().modelSelection.benchmarkLlmProviderModelConfigId).toBe(20);
  });
});
