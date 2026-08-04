import { renderHook, waitFor, act } from '@testing-library/react';
import { Provider } from 'react-redux';
import React from 'react';
import {
  useTestNameValidation,
  TEST_NAME_DUPLICATE_ERROR,
  TEST_NAME_REQUIRED_ERROR,
} from '@/hooks/useTestNameValidation';
import { createTestStore, DeepPartial, RootState } from '@/store';
import { checkBenchmarkRunName } from '@/lib/api';

jest.mock('@/lib/api', () => ({
  checkBenchmarkRunName: jest.fn(),
  ApiError: class ApiError extends Error {
    constructor(
      message: string,
      public status?: number,
      public statusText?: string
    ) {
      super(message);
      this.name = 'ApiError';
    }
  },
}));

const mockCheckBenchmarkRunName = checkBenchmarkRunName as jest.MockedFunction<
  typeof checkBenchmarkRunName
>;

function renderValidationHook(preloadedState?: DeepPartial<RootState>) {
  const store = createTestStore(preloadedState);
  const wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(Provider, { store, children });
  const view = renderHook(() => useTestNameValidation(), { wrapper });
  return { ...view, store };
}

describe('useTestNameValidation', () => {
  const originalError = console.error;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    console.error = jest.fn();
  });

  afterEach(() => {
    jest.useRealTimers();
    console.error = originalError;
  });

  it('marks empty name as invalid with required error', () => {
    const { result } = renderValidationHook();

    expect(result.current.isTestNameValid).toBe(false);
    expect(result.current.errorMessage).toBe(TEST_NAME_REQUIRED_ERROR);
    expect(result.current.isChecking).toBe(false);
    expect(mockCheckBenchmarkRunName).not.toHaveBeenCalled();
  });

  it('debounces API call and marks available name as valid', async () => {
    mockCheckBenchmarkRunName.mockResolvedValue({
      run_name: 'my-run',
      available: true,
    });

    const { result, store } = renderValidationHook({
      modelSelection: {
        selectedProvider: '',
        selectedModel: '',
        selectedConfig: '',
        isConfigValid: false,
        isTestNameValid: false,
        testName: 'my-run',
        benchmarkLlmProviderId: null,
        benchmarkLlmProviderModelId: null,
        benchmarkLlmProviderModelConfigId: null,
      },
    });

    expect(result.current.isChecking).toBe(true);
    expect(mockCheckBenchmarkRunName).not.toHaveBeenCalled();

    await act(async () => {
      jest.advanceTimersByTime(400);
    });

    await waitFor(() => {
      expect(result.current.isTestNameValid).toBe(true);
    });

    expect(mockCheckBenchmarkRunName).toHaveBeenCalledWith('my-run');
    expect(result.current.errorMessage).toBeNull();
    expect(store.getState().modelSelection.isTestNameValid).toBe(true);
  });

  it('marks duplicate name as invalid with duplicate error', async () => {
    mockCheckBenchmarkRunName.mockResolvedValue({
      run_name: 'existing-run',
      available: false,
    });

    const { result, store } = renderValidationHook({
      modelSelection: {
        selectedProvider: '',
        selectedModel: '',
        selectedConfig: '',
        isConfigValid: false,
        isTestNameValid: false,
        testName: 'existing-run',
        benchmarkLlmProviderId: null,
        benchmarkLlmProviderModelId: null,
        benchmarkLlmProviderModelConfigId: null,
      },
    });

    await act(async () => {
      jest.advanceTimersByTime(400);
    });

    await waitFor(() => {
      expect(result.current.isTestNameValid).toBe(false);
    });

    expect(result.current.errorMessage).toBe(TEST_NAME_DUPLICATE_ERROR);
    expect(store.getState().modelSelection.isTestNameValid).toBe(false);
  });

  it('fails open when API check errors', async () => {
    mockCheckBenchmarkRunName.mockRejectedValue(new Error('network down'));

    const { result, store } = renderValidationHook({
      modelSelection: {
        selectedProvider: '',
        selectedModel: '',
        selectedConfig: '',
        isConfigValid: false,
        isTestNameValid: false,
        testName: 'my-run',
        benchmarkLlmProviderId: null,
        benchmarkLlmProviderModelId: null,
        benchmarkLlmProviderModelConfigId: null,
      },
    });

    await act(async () => {
      jest.advanceTimersByTime(400);
    });

    await waitFor(() => {
      expect(result.current.isTestNameValid).toBe(true);
    });

    expect(result.current.errorMessage).toBeNull();
    expect(store.getState().modelSelection.isTestNameValid).toBe(true);
  });
});
