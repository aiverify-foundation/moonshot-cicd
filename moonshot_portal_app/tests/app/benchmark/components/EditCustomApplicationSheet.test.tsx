import userEvent from '@testing-library/user-event';
import { render, screen, waitFor } from '@/tests/utils/test-utils';
import EditCustomApplicationSheet from '@/app/benchmark/components/EditCustomApplicationSheet';
import type { Config, ModelApp } from '@/app/benchmark/types/modelSelection';
import { encodeCustomAppProviderId } from '@/app/benchmark/constants/customAppConfig';

jest.mock('../../../../lib/api', () => ({
  createCustomAppConfig: jest.fn(),
  updateCustomAppConfig: jest.fn(),
  setCustomAppConfigSecret: jest.fn(),
  ApiError: class ApiError extends Error {},
}));

function getCreateCustomAppConfigMock() {
  return (
    jest.requireMock('../../../../lib/api') as {
      createCustomAppConfig: jest.Mock;
    }
  ).createCustomAppConfig;
}

function getUpdateCustomAppConfigMock() {
  return (
    jest.requireMock('../../../../lib/api') as {
      updateCustomAppConfig: jest.Mock;
    }
  ).updateCustomAppConfig;
}

function getSetCustomAppConfigSecretMock() {
  return (
    jest.requireMock('../../../../lib/api') as {
      setCustomAppConfigSecret: jest.Mock;
    }
  ).setCustomAppConfigSecret;
}

const customProviderId = encodeCustomAppProviderId(1);
const modelApps: ModelApp[] = [{ id: customProviderId, name: 'Together API', type: 'custom' }];

describe('EditCustomApplicationSheet', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    getCreateCustomAppConfigMock().mockResolvedValue({
      id: 5,
      custom_app_id: 1,
      name: 'Prod',
      savedConfigPairs: {
        connector_adapter: 'custom_api_connector_adapter',
        api_type: 'POST',
        api_url: 'https://api.example.com',
        api_body: '{}',
      },
      api_key_configured: false,
    });
    getUpdateCustomAppConfigMock().mockResolvedValue({
      id: 10,
      custom_app_id: 1,
      name: 'Prod',
      savedConfigPairs: {
        connector_adapter: 'custom_api_connector_adapter',
        api_type: 'POST',
        api_url: 'https://api.example.com',
        api_body: '{}',
      },
      api_key_configured: true,
    });
    getSetCustomAppConfigSecretMock().mockResolvedValue({ message: 'ok' });
  });

  it('creates config with reserved fields and stores api_key secret', async () => {
    const user = userEvent.setup();
    const onSaved = jest.fn();

    render(
      <EditCustomApplicationSheet
        open
        onOpenChange={() => {}}
        editingConfig={customProviderId}
        modelApps={modelApps}
        configs={[]}
        onSaved={onSaved}
      />
    );

    await user.clear(screen.getByLabelText(/configuration name/i));
    await user.type(screen.getByLabelText(/configuration name/i), 'Prod');
    await user.clear(screen.getByLabelText(/^url/i));
    await user.type(screen.getByLabelText(/^url/i), 'https://api.example.com');
    await user.type(screen.getByLabelText(/api secret/i), 'sk-test-key');
    await user.click(screen.getByRole('button', { name: 'Test' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(getCreateCustomAppConfigMock()).toHaveBeenCalledWith(1, {
        name: 'Prod',
        savedConfigPairs: expect.objectContaining({
          api_type: 'POST',
          api_url: 'https://api.example.com',
          connector_adapter: 'custom_api_connector_adapter',
        }),
      });
    });
    expect(getSetCustomAppConfigSecretMock()).toHaveBeenCalledWith(5, 'api_key', 'sk-test-key');
    expect(onSaved).toHaveBeenCalled();
  });

  it('updates existing config without secret when api_key already configured', async () => {
    const user = userEvent.setup();
    const configs: Config[] = [
      {
        id: '10',
        name: 'Prod',
        connector: customProviderId,
        configPairs: [{ key: 'timeout', value: '60' }],
        apiType: 'POST',
        apiUrl: 'https://api.example.com',
        apiBody: '{"messages":[]}',
        apiKeyConfigured: true,
      },
    ];

    render(
      <EditCustomApplicationSheet
        open
        onOpenChange={() => {}}
        editingConfig="10"
        modelApps={modelApps}
        configs={configs}
      />
    );

    await user.click(screen.getByRole('button', { name: 'Test' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(getUpdateCustomAppConfigMock()).toHaveBeenCalledWith(
        10,
        expect.objectContaining({
          name: 'Prod',
          savedConfigPairs: expect.objectContaining({
            api_url: 'https://api.example.com',
            timeout: '60',
          }),
        })
      );
    });
    expect(getSetCustomAppConfigSecretMock()).not.toHaveBeenCalled();
  });
});
