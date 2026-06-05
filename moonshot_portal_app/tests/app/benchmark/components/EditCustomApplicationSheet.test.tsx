import userEvent from '@testing-library/user-event';
import { within } from '@testing-library/react';
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

function getParametersSection() {
  const heading = screen.getByText('Parameters');
  const section = heading.closest('div')?.parentElement;
  if (!section) throw new Error('Parameters section not found');
  return section;
}

function getHeadersSection() {
  const heading = screen.getByText('Headers');
  const section = heading.closest('div')?.parentElement;
  if (!section) throw new Error('Headers section not found');
  return section;
}

describe('EditCustomApplicationSheet', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    getCreateCustomAppConfigMock().mockResolvedValue({
      id: 5,
      custom_app_id: 1,
      name: 'Prod',
      savedConfigPairs: {
        connector_adapter: 'custom_api_connector_adapter',
        api_type: 'POST',
        api_url: 'https://api.example.com',
        api_body: '{}',
        parameters: '{}',
        headers: '{}',
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
        api_body: '{"messages":[]}',
        parameters: '{"timeout":"60"}',
        headers: '{"X-Custom":"value"}',
      },
      api_key_configured: true,
    });
    getSetCustomAppConfigSecretMock().mockResolvedValue({ message: 'ok' });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('creates config with reserved fields and JSON parameters/headers', async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
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

    const parametersSection = getParametersSection();
    const addParamButton = within(parametersSection).getAllByRole('button')[0];
    await user.click(addParamButton);
    const paramInputs = within(parametersSection).getAllByRole('textbox');
    await user.type(paramInputs[0], 'timeout');
    await user.type(paramInputs[1], '30');

    await user.click(screen.getByRole('button', { name: 'Test' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(getCreateCustomAppConfigMock()).toHaveBeenCalledWith(1, {
        name: 'Prod',
        savedConfigPairs: expect.objectContaining({
          api_type: 'POST',
          api_url: 'https://api.example.com',
          connector_adapter: 'custom_api_connector_adapter',
          parameters: JSON.stringify({ timeout: '30' }),
          headers: JSON.stringify({}),
        }),
      });
    });

    expect(getSetCustomAppConfigSecretMock()).toHaveBeenCalledWith(5, 'api_key', 'sk-test-key');
    expect(onSaved).toHaveBeenCalled();
  });

  it('loads parameters and headers from JSON savedConfigPairs', () => {
    const configs: Config[] = [
      {
        id: '10',
        name: 'Prod',
        connector: customProviderId,
        configPairs: [{ key: 'timeout', value: '60' }],
        headerPairs: [{ key: 'X-Custom', value: 'value' }],
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

    expect(screen.getByDisplayValue('timeout')).toBeInTheDocument();
    expect(screen.getByDisplayValue('60')).toBeInTheDocument();
    expect(screen.getByDisplayValue('X-Custom')).toBeInTheDocument();
    expect(screen.getByDisplayValue('value')).toBeInTheDocument();
  });

  it('loads legacy flat timeout into Parameters when parameters key is absent', () => {
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

    expect(screen.getByDisplayValue('timeout')).toBeInTheDocument();
    expect(screen.getByDisplayValue('60')).toBeInTheDocument();
  });

  it('updates existing config with serialized parameters and headers', async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    const configs: Config[] = [
      {
        id: '10',
        name: 'Prod',
        connector: customProviderId,
        configPairs: [{ key: 'timeout', value: '60' }],
        headerPairs: [{ key: 'Accept', value: 'application/json' }],
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
            parameters: JSON.stringify({ timeout: '60' }),
            headers: JSON.stringify({ Accept: 'application/json' }),
          }),
        })
      );
    });
    expect(getSetCustomAppConfigSecretMock()).not.toHaveBeenCalled();
  });

  it('auto-saves parameters on edit for existing config', async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
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

    getUpdateCustomAppConfigMock().mockClear();

    const timeoutValueInput = screen.getByDisplayValue('60');
    await user.clear(timeoutValueInput);
    await user.type(timeoutValueInput, '90');

    jest.advanceTimersByTime(500);

    await waitFor(() => {
      expect(getUpdateCustomAppConfigMock()).toHaveBeenCalledWith(
        10,
        expect.objectContaining({
          savedConfigPairs: expect.objectContaining({
            parameters: JSON.stringify({ timeout: '90' }),
          }),
        })
      );
    });
  });

  it('rejects reserved parameter name in Parameters grid on test', async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

    render(
      <EditCustomApplicationSheet
        open
        onOpenChange={() => {}}
        editingConfig={customProviderId}
        modelApps={modelApps}
        configs={[]}
      />
    );

    const parametersSection = getParametersSection();
    const addParamButton = within(parametersSection).getAllByRole('button')[0];
    await user.click(addParamButton);
    const paramInputs = within(parametersSection).getAllByRole('textbox');
    await user.type(paramInputs[0], 'parameters');
    await user.type(paramInputs[1], 'bad');

    await user.clear(screen.getByLabelText(/configuration name/i));
    await user.type(screen.getByLabelText(/configuration name/i), 'Prod');
    await user.clear(screen.getByLabelText(/^url/i));
    await user.type(screen.getByLabelText(/^url/i), 'https://api.example.com');

    await user.click(screen.getByRole('button', { name: 'Test' }));

    expect(screen.getByText('Test Failed')).toBeInTheDocument();
  });

  it('adds header row and includes headers in save payload', async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

    render(
      <EditCustomApplicationSheet
        open
        onOpenChange={() => {}}
        editingConfig={customProviderId}
        modelApps={modelApps}
        configs={[]}
      />
    );

    await user.clear(screen.getByLabelText(/configuration name/i));
    await user.type(screen.getByLabelText(/configuration name/i), 'Prod');
    await user.clear(screen.getByLabelText(/^url/i));
    await user.type(screen.getByLabelText(/^url/i), 'https://api.example.com');
    await user.type(screen.getByLabelText(/api secret/i), 'sk-test-key');

    const headersSection = getHeadersSection();
    const addHeaderButton = within(headersSection).getAllByRole('button')[0];
    await user.click(addHeaderButton);
    const headerInputs = within(headersSection).getAllByRole('textbox');
    await user.type(headerInputs[0], 'Accept');
    await user.type(headerInputs[1], 'application/json');

    await user.click(screen.getByRole('button', { name: 'Test' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(getCreateCustomAppConfigMock()).toHaveBeenCalledWith(
        1,
        expect.objectContaining({
          savedConfigPairs: expect.objectContaining({
            headers: JSON.stringify({ Accept: 'application/json' }),
          }),
        })
      );
    });
  });
});
