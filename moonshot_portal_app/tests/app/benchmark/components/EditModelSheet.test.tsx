import userEvent from '@testing-library/user-event';
import { createTestStore, render, screen, waitFor } from '@/tests/utils/test-utils';
import EditModelSheet from '@/app/benchmark/components/EditModelSheet';
import type { Provider, ModelConfig } from '@/app/benchmark/types/modelSelection';

jest.mock('../../../../lib/api', () => ({
  fetchProviderLatestDetails: jest.fn(),
  createDatabaseModelConfig: jest.fn(),
  updateDatabaseModelConfig: jest.fn(),
  setLlmProviderApiKey: jest.fn(),
  ApiError: class ApiError extends Error {},
}));

function getFetchProviderLatestDetailsMock() {
  return (
    jest.requireMock('../../../../lib/api') as {
      fetchProviderLatestDetails: jest.Mock;
    }
  ).fetchProviderLatestDetails;
}

function getUpdateDatabaseModelConfigMock() {
  return (
    jest.requireMock('../../../../lib/api') as {
      updateDatabaseModelConfig: jest.Mock;
    }
  ).updateDatabaseModelConfig;
}

function getCreateDatabaseModelConfigMock() {
  return (
    jest.requireMock('../../../../lib/api') as {
      createDatabaseModelConfig: jest.Mock;
    }
  ).createDatabaseModelConfig;
}

const highTempProvider: Provider = {
  id: '1',
  name: 'Test Provider',
  type: 'provider',
  defaultModel: 'gpt-4',
  modelTextboxExplanation: '',
  configPairs: [{ key: 'temperature', value: '30' }],
  modelToken: '',
  system_name: 'test_provider',
};

const defaultLatestDetails = {
  api_key_configured: true,
  database_model_configs: [] as unknown[],
  models: [{ id: 10, name: 'gpt-4', create_dt: '2026-01-01T00:00:00Z' }],
  provider: { id: '1', name: 'Test Provider', system_name: 'test_provider' },
};

describe('EditModelSheet', () => {
  beforeEach(() => {
    getFetchProviderLatestDetailsMock().mockResolvedValue({ ...defaultLatestDetails });
    getUpdateDatabaseModelConfigMock().mockResolvedValue({
      id: '20',
      name: 'x',
      modelname: 'gpt-4',
      providerID: 'test_provider',
      savedConfigPairs: {},
      lastUpdated: '2026-01-01T00:00:00Z',
    });
    getCreateDatabaseModelConfigMock().mockResolvedValue({
      id: '21',
      name: 'x',
      modelname: 'gpt-4',
      providerID: 'test_provider',
      savedConfigPairs: {},
      lastUpdated: '2026-01-01T00:00:00Z',
    });
  });

  it('loads saved advanced parameters when editing an existing DB-backed model config', async () => {
    const models: ModelConfig[] = [
      {
        id: '10',
        name: 'My Config',
        modelname: 'gpt-4',
        provider: '1',
        modelConfigId: '20',
        savedConfigPairs: { temperature: '0' },
      },
    ];

    const store = createTestStore({
      modelSelection: {
        selectedProvider: '1',
        selectedModel: '10',
        selectedConfig: '',
        isConfigValid: true,
        isTestNameValid: true,
        testName: 't',
        benchmarkLlmProviderId: null,
        benchmarkLlmProviderModelId: null,
        benchmarkLlmProviderModelConfigId: null,
      },
    });

    render(
      <EditModelSheet
        open
        onOpenChange={() => {}}
        editingModel="10"
        providers={[highTempProvider]}
        models={models}
      />,
      { store }
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('0')).toBeInTheDocument();
    });
    expect(screen.getByDisplayValue('temperature')).toBeInTheDocument();
    expect(screen.queryByDisplayValue('30')).not.toBeInTheDocument();
  });

  it('hydrates advanced parameters from latest-details when models omit savedConfigPairs', async () => {
    getFetchProviderLatestDetailsMock().mockResolvedValue({
      api_key_configured: true,
      database_model_configs: [
        {
          id: '99',
          name: 'My Config',
          modelname: 'gpt-4',
          modelId: 10,
          providerID: 'test_provider',
          savedConfigPairs: { temperature: '0' },
          lastUpdated: '2026-01-01T00:00:00Z',
        },
      ],
    });

    const models: ModelConfig[] = [
      {
        id: '10',
        name: 'My Config',
        modelname: 'gpt-4',
        provider: '1',
        modelConfigId: '99',
      },
    ];

    const store = createTestStore({
      modelSelection: {
        selectedProvider: '1',
        selectedModel: '10',
        selectedConfig: '',
        isConfigValid: true,
        isTestNameValid: true,
        testName: 't',
        benchmarkLlmProviderId: 1,
        benchmarkLlmProviderModelId: 10,
        benchmarkLlmProviderModelConfigId: 99,
      },
    });

    render(
      <EditModelSheet
        open
        onOpenChange={() => {}}
        editingModel="10"
        providers={[highTempProvider]}
        models={models}
      />,
      { store }
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('0')).toBeInTheDocument();
    });
    expect(screen.queryByDisplayValue('30')).not.toBeInTheDocument();
  });

  it('prefers editingDatabaseConfigId when two configs share the same llm_provider_model', async () => {
    getFetchProviderLatestDetailsMock().mockResolvedValue({
      api_key_configured: true,
      database_model_configs: [
        {
          id: '1',
          name: 'Config A',
          modelname: 'gpt-4',
          modelId: 10,
          providerID: 'test_provider',
          savedConfigPairs: { temperature: '30' },
          lastUpdated: '2026-01-01T00:00:00Z',
        },
        {
          id: '2',
          name: 'Config B',
          modelname: 'gpt-4',
          modelId: 10,
          providerID: 'test_provider',
          savedConfigPairs: { temperature: '0' },
          lastUpdated: '2026-01-02T00:00:00Z',
        },
      ],
    });

    const models: ModelConfig[] = [
      {
        id: '10:2',
        name: 'Config B',
        modelname: 'gpt-4',
        provider: '1',
        modelConfigId: '2',
        savedConfigPairs: { temperature: '0' },
      },
    ];

    const store = createTestStore({
      modelSelection: {
        selectedProvider: '1',
        selectedModel: '10:2',
        selectedConfig: '',
        isConfigValid: true,
        isTestNameValid: true,
        testName: 't',
        benchmarkLlmProviderId: null,
        benchmarkLlmProviderModelId: null,
        benchmarkLlmProviderModelConfigId: null,
      },
    });

    render(
      <EditModelSheet
        open
        onOpenChange={() => {}}
        editingModel="10:2"
        editingDatabaseConfigId="2"
        providers={[highTempProvider]}
        models={models}
      />,
      { store }
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('0')).toBeInTheDocument();
    });
    expect(screen.queryByDisplayValue('30')).not.toBeInTheDocument();
  });

  it('calls updateDatabaseModelConfig when saving an edit to an existing config', async () => {
    const user = userEvent.setup();
    const updateMock = getUpdateDatabaseModelConfigMock();
    const createMock = getCreateDatabaseModelConfigMock();

    const models: ModelConfig[] = [
      {
        id: '10:20',
        name: 'My Config',
        modelname: 'gpt-4',
        provider: '1',
        modelConfigId: '20',
        savedConfigPairs: { temperature: '0' },
      },
    ];

    const store = createTestStore({
      modelSelection: {
        selectedProvider: '1',
        selectedModel: '10:20',
        selectedConfig: '',
        isConfigValid: true,
        isTestNameValid: true,
        testName: 't',
        benchmarkLlmProviderId: 1,
        benchmarkLlmProviderModelId: 10,
        benchmarkLlmProviderModelConfigId: 20,
      },
    });

    render(
      <EditModelSheet
        open
        onOpenChange={() => {}}
        editingModel="10:20"
        editingDatabaseConfigId="20"
        providers={[highTempProvider]}
        models={models}
      />,
      { store }
    );

    await user.click(screen.getByRole('button', { name: /Test/i }));
    const nameInput = screen.getByPlaceholderText('Enter model configuration name');
    await user.clear(nameInput);
    await user.type(nameInput, 'Renamed Config');
    await user.click(screen.getByRole('button', { name: /^Save$/ }));

    await waitFor(() => {
      expect(updateMock).toHaveBeenCalledWith(
        20,
        expect.objectContaining({
          model_id: 10,
          name: 'Renamed Config',
          savedConfigPairs: { temperature: '0' },
        })
      );
    });
    expect(createMock).not.toHaveBeenCalled();
  });

  it('uses provider default pairs when creating a new config', async () => {
    const store = createTestStore({
      modelSelection: {
        selectedProvider: '1',
        selectedModel: '',
        selectedConfig: '',
        isConfigValid: false,
        isTestNameValid: true,
        testName: 't',
        benchmarkLlmProviderId: null,
        benchmarkLlmProviderModelId: null,
        benchmarkLlmProviderModelConfigId: null,
      },
    });

    render(
      <EditModelSheet
        open
        onOpenChange={() => {}}
        editingModel="1"
        providers={[highTempProvider]}
        models={[]}
      />,
      { store }
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('30')).toBeInTheDocument();
    });
  });

  it('dispatches endpoint status to endpointStatusKey when set', async () => {
    const user = userEvent.setup();
    const store = createTestStore({
      modelSelection: {
        selectedProvider: '1',
        selectedModel: '',
        selectedConfig: '',
        isConfigValid: false,
        isTestNameValid: true,
        testName: 't',
        benchmarkLlmProviderId: null,
        benchmarkLlmProviderModelId: null,
        benchmarkLlmProviderModelConfigId: null,
      },
    });

    render(
      <EditModelSheet
        open
        onOpenChange={() => {}}
        editingModel="1"
        providers={[highTempProvider]}
        models={[]}
        endpointStatusKey="aaj:together_adapter"
      />,
      { store }
    );

    await user.click(screen.getByRole('button', { name: /Test/i }));
    expect(store.getState().endpointStatus['aaj:together_adapter']).toBe('connected');
  });
});
