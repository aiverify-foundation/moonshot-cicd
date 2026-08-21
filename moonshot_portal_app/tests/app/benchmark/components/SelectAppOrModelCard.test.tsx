import { render, screen } from '@/tests/utils/test-utils';
import SelectAppOrModelCard from '@/app/benchmark/components/SelectAppOrModelCard';
import type { Provider, ModelConfig, ModelApp, Config } from '@/app/benchmark/types/modelSelection';
import { createTestStore } from '@/tests/utils/test-utils';

/** Minimal fixtures for standard provider/model props (production uses API data). */
const testProviders: Provider[] = [
  {
    id: '1',
    name: 'Test Provider',
    type: 'provider',
    defaultModel: 'gpt-4',
    modelTextboxExplanation: 'Example',
    configPairs: [{ key: 'timeout', value: '30' }],
    modelToken: 'model',
    system_name: 'test_provider',
  },
];

const testModels: ModelConfig[] = [
  {
    id: '10',
    name: 'Test Model',
    modelname: 'gpt-4',
    provider: '1',
    modelConfigId: '20',
  },
];

const testCustomApps: ModelApp[] = [
  { id: '2', name: 'Custom API App', type: 'custom' },
];

const testConfigs: Config[] = [
  {
    id: '100',
    name: 'Default Config',
    connector: '2',
    configPairs: [],
    apiKeyConfigured: false,
  },
];

describe('SelectAppOrModelCard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial Page Load Display', () => {
    it('Scenario: GIVEN as a user WHEN load Standard Provider Side Sheet THEN display a card that displays the following. Display "Select App or Model Under Test" AND "confirm the details of the app or model to be tested." AND Display a Combobox', () => {
      // Create test store with initial state
      const store = createTestStore({
        modelSelection: {
          selectedProvider: '',
          selectedModel: '',
          selectedConfig: '',
          isConfigValid: false,
          isTestNameValid: false,
          testName: '',
          benchmarkLlmProviderId: null,
          benchmarkLlmProviderModelId: null,
          benchmarkLlmProviderModelConfigId: null,
          benchmarkCustomAppId: null,
          benchmarkCustomAppConfigId: null,
        },
      });

      // Render component with all required props
      render(
        <SelectAppOrModelCard
          providers={testProviders}
          models={testModels}
          custom_connectors={testCustomApps}
          configs={testConfigs}
        />,
        {
          store,
        }
      );

      // THEN display a card that displays the following:
      // Display "Select App or Model Under Test"
      const cardTitle = screen.getByTestId('card-title');
      expect(cardTitle).toBeInTheDocument();
      expect(cardTitle).toHaveTextContent('Select App or Model Under Test');

      // AND "confirm the details of the app or model to be tested."
      const cardDescription = screen.getByTestId('card-description');
      expect(cardDescription).toBeInTheDocument();
      expect(cardDescription).toHaveTextContent('Confirm the details of the app or model to be tested.');

      // AND Display a Combobox
      const providerCombobox = screen.getByTestId('provider-combobox-trigger');
      expect(providerCombobox).toBeInTheDocument();
      expect(providerCombobox).toHaveTextContent('Select provider...');
    });
  });
});
