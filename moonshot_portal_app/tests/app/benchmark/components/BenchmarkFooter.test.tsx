import userEvent from '@testing-library/user-event';
import { render, screen, waitFor } from '@/tests/utils/test-utils';
import BenchmarkFooter from '@/app/benchmark/components/BenchmarkFooter';
import type { Bundle } from '@/lib/api';

const mockPush = jest.fn();
const mockStartBenchmarkRun = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock('@/lib/api', () => {
  const actual = jest.requireActual('@/lib/api') as Record<string, unknown>;
  return {
    ...actual,
    startBenchmarkRun: (...args: unknown[]) => mockStartBenchmarkRun(...args),
  };
});

const mockBundle: Bundle = {
  id: 'safety-bundle',
  name: 'Safety Bundle',
  description: '',
  category: 'Safety',
  tests: [
    {
      name: 'Test One',
      benchmark_test_id: 101,
      dataset: {
        id: 'ds1',
        name: 'ds1',
        description: '',
        num_of_dataset_prompts: 500,
      },
    },
  ],
};

const basePreloadedState = {
  bundles: { data: [mockBundle], loading: false, error: null },
  bundleSelection: { 'safety-bundle': true },
  testSelection: { 'safety-bundle': { '101': true } },
  modelSelection: {
    selectedProvider: 'openai',
    selectedModel: 'gpt-4',
    selectedConfig: '',
    isConfigValid: true,
    isTestNameValid: true,
    testName: 'My Run',
    benchmarkLlmProviderId: 1,
    benchmarkLlmProviderModelId: 2,
    benchmarkLlmProviderModelConfigId: 3,
    benchmarkCustomAppId: null,
    benchmarkCustomAppConfigId: null,
  },
  sampleSizeSelection: {
    mode: 'all' as const,
    populationMean: '90',
    confidenceLevel: '95',
    marginOfError: '3',
  },
};

describe('BenchmarkFooter', () => {
  beforeEach(() => {
    mockPush.mockReset();
    mockStartBenchmarkRun.mockReset();
    mockStartBenchmarkRun.mockResolvedValue({ message: 'ok' });
    window.alert = jest.fn();
  });

  it('omits prompts_by_test when sample size mode is all', async () => {
    const user = userEvent.setup();
    render(
      <BenchmarkFooter currentPage="model-selection" setCurrentPage={jest.fn()} />,
      { preloadedState: basePreloadedState }
    );

    await user.click(screen.getByTestId('run-benchmark-tests'));

    await waitFor(() => expect(mockStartBenchmarkRun).toHaveBeenCalledTimes(1));
    const payload = mockStartBenchmarkRun.mock.calls[0][0] as Record<string, unknown>;
    expect(payload.run_name).toBe('My Run');
    expect(payload.bundle_names).toEqual(['safety-bundle']);
    expect(payload.prompts_by_test).toBeUndefined();
  });

  it('sends prompts_by_test when sample size mode is calculated', async () => {
    const user = userEvent.setup();
    render(
      <BenchmarkFooter currentPage="model-selection" setCurrentPage={jest.fn()} />,
      {
        preloadedState: {
          ...basePreloadedState,
          sampleSizeSelection: {
            ...basePreloadedState.sampleSizeSelection,
            mode: 'calculated',
          },
        },
      }
    );

    await user.click(screen.getByTestId('run-benchmark-tests'));

    await waitFor(() => expect(mockStartBenchmarkRun).toHaveBeenCalledTimes(1));
    const payload = mockStartBenchmarkRun.mock.calls[0][0] as Record<string, unknown>;
    expect(payload.prompts_by_test).toEqual({ 101: 385 });
  });
});
