import type { BundleTest } from '@/lib/api';
import type { Provider } from '@/app/benchmark/types/modelSelection';
import {
  collectAajProviderSystemNames,
  resolveAajEndpointCardLabel,
  resolveAajProviderDisplayName,
  resolveModelNameLabel,
  resolveRequiredAajProviderNames,
} from '@/lib/aajProviderResolution';

const togetherProvider: Provider = {
  id: '42',
  name: 'Together AI',
  type: 'provider',
  defaultModel: '',
  modelTextboxExplanation: '',
  configPairs: [],
  modelToken: '',
  system_name: 'together_adapter',
};

describe('aajProviderResolution', () => {
  describe('resolveAajProviderDisplayName', () => {
    it('returns provider name when matched', () => {
      expect(
        resolveAajProviderDisplayName('together_adapter', [togetherProvider])
      ).toBe('Together AI');
    });

    it('returns fallback when provider is missing', () => {
      expect(resolveAajProviderDisplayName('missing_adapter', [])).toBe(
        'missing_adapter (provider not in API)'
      );
    });
  });

  describe('resolveAajEndpointCardLabel', () => {
    it('appends LLM judge suffix when provider exists', () => {
      expect(
        resolveAajEndpointCardLabel('together_adapter', [togetherProvider])
      ).toBe('Together AI (LLM judge)');
    });

    it('returns fallback without suffix when provider is missing', () => {
      expect(resolveAajEndpointCardLabel('missing_adapter', [])).toBe(
        'missing_adapter (provider not in API)'
      );
    });
  });

  describe('resolveModelNameLabel', () => {
    const aajTest: BundleTest = {
      name: 'Sample',
      requires_llm_aaj: true,
      metric_provider_system_name: 'together_adapter',
      metric_grader_model_name: 'meta-llama/Llama-Guard-4-12B',
      dataset: {
        id: 'ds-1',
        name: 'ds-1',
        description: '',
        num_of_dataset_prompts: 1,
      },
    };

    it('returns grader model name from API when present', () => {
      expect(resolveModelNameLabel(aajTest)).toBe(
        'meta-llama/Llama-Guard-4-12B'
      );
    });

    it('returns em dash when grader model is missing', () => {
      const nonAajTest: BundleTest = {
        ...aajTest,
        metric_grader_model_name: null,
      };
      expect(resolveModelNameLabel(nonAajTest)).toBe('—');
    });

    it('returns em dash when test is null', () => {
      expect(resolveModelNameLabel(null)).toBe('—');
    });

    it('returns em dash when grader model is blank', () => {
      expect(
        resolveModelNameLabel({ ...aajTest, metric_grader_model_name: '   ' })
      ).toBe('—');
    });
  });

  describe('collectAajProviderSystemNames', () => {
    it('returns unique sorted system names for AAJ tests', () => {
      const tests: BundleTest[] = [
        {
          name: 'A',
          requires_llm_aaj: true,
          metric_provider_system_name: 'openai_adapter',
          dataset: { id: '1', name: '1', description: '', num_of_dataset_prompts: 1 },
        },
        {
          name: 'B',
          requires_llm_aaj: true,
          metric_provider_system_name: 'together_adapter',
          dataset: { id: '2', name: '2', description: '', num_of_dataset_prompts: 1 },
        },
        {
          name: 'C',
          requires_llm_aaj: true,
          metric_provider_system_name: 'together_adapter',
          dataset: { id: '3', name: '3', description: '', num_of_dataset_prompts: 1 },
        },
      ];
      expect(collectAajProviderSystemNames(tests)).toEqual([
        'openai_adapter',
        'together_adapter',
      ]);
    });

    it('returns empty list when no AAJ tests', () => {
      expect(
        collectAajProviderSystemNames([
          {
            name: 'A',
            requires_llm_aaj: false,
            dataset: { id: '1', name: '1', description: '', num_of_dataset_prompts: 1 },
          },
        ])
      ).toEqual([]);
    });
  });

  describe('resolveRequiredAajProviderNames', () => {
    it('maps system names to provider display names', () => {
      expect(
        resolveRequiredAajProviderNames(
          [
            {
              name: 'A',
              requires_llm_aaj: true,
              metric_provider_system_name: 'together_adapter',
              dataset: { id: '1', name: '1', description: '', num_of_dataset_prompts: 1 },
            },
          ],
          [togetherProvider]
        )
      ).toEqual(['Together AI']);
    });
  });
});
