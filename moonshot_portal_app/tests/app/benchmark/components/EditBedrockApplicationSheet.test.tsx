import userEvent from '@testing-library/user-event';
import { render, screen, waitFor } from '@/tests/utils/test-utils';
import EditBedrockApplicationSheet from '@/app/benchmark/components/EditBedrockApplicationSheet';
import type { ModelApp } from '@/app/benchmark/types/modelSelection';
import {
  AWS_BEDROCK_API_APP_NAME,
  BEDROCK_API_CONNECTOR_ADAPTER,
  DEFAULT_BEDROCK_API_URL,
  DEFAULT_BEDROCK_RESPONSE_PATH,
  encodeCustomAppProviderId,
} from '@/app/benchmark/constants/customAppConfig';

jest.mock('@/lib/api', () => ({
  createCustomAppConfig: jest.fn(),
  updateCustomAppConfig: jest.fn(),
  setCustomAppConfigSecret: jest.fn(),
  testCustomAppConnection: jest.fn(),
  ApiError: class ApiError extends Error {},
}));

function getCreateCustomAppConfigMock() {
  return (
    jest.requireMock('@/lib/api') as {
      createCustomAppConfig: jest.Mock;
    }
  ).createCustomAppConfig;
}

function getTestCustomAppConnectionMock() {
  return (
    jest.requireMock('@/lib/api') as {
      testCustomAppConnection: jest.Mock;
    }
  ).testCustomAppConnection;
}

const bedrockProviderId = encodeCustomAppProviderId(2);
const modelApps: ModelApp[] = [
  { id: bedrockProviderId, name: AWS_BEDROCK_API_APP_NAME, type: 'custom' },
];

async function clickTestConnectionAndWait(
  user: ReturnType<typeof userEvent.setup>
) {
  await user.click(screen.getByRole('button', { name: 'Test Connection' }));
  await waitFor(() => {
    expect(getTestCustomAppConnectionMock()).toHaveBeenCalled();
  });
}

describe('EditBedrockApplicationSheet', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    getCreateCustomAppConfigMock().mockResolvedValue({
      id: 5,
      custom_app_id: 2,
      name: 'New Configuration',
      savedConfigPairs: {},
      api_key_configured: true,
    });
    getTestCustomAppConnectionMock().mockResolvedValue({
      success: true,
      status_code: 200,
      response_is_json: true,
      response_leaves: [],
    });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('creates bedrock config with converse defaults and adapter', async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

    render(
      <EditBedrockApplicationSheet
        open
        onOpenChange={() => {}}
        editingConfig={bedrockProviderId}
        modelApps={modelApps}
        configs={[]}
      />
    );

    expect(screen.getByLabelText(/^url/i)).toHaveValue(DEFAULT_BEDROCK_API_URL);
    expect(screen.queryByLabelText(/response path/i)).not.toBeInTheDocument();

    await user.type(screen.getByLabelText(/authorization secret/i), 'bedrock-api-key-test');
    await clickTestConnectionAndWait(user);
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(getCreateCustomAppConfigMock()).toHaveBeenCalledWith(2, {
        name: 'New Configuration',
        savedConfigPairs: expect.objectContaining({
          connector_adapter: BEDROCK_API_CONNECTOR_ADAPTER,
          api_url: DEFAULT_BEDROCK_API_URL,
          response_path: DEFAULT_BEDROCK_RESPONSE_PATH,
          api_key_auth_scheme: 'bearer',
        }),
      });
    });
  });
});
