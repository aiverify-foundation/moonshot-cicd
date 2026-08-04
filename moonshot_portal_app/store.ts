import { configureStore, createSlice, createAsyncThunk, combineReducers } from '@reduxjs/toolkit';
import { fetchBundles, Bundle } from './lib/api';
import { sortBundlesForDisplay } from './lib/bundles';
import type { TestSelectionState } from './lib/benchmarkTestSelection';

// Async thunk for fetching bundles
export const fetchBundlesAsync = createAsyncThunk(
  'bundles/fetchBundles',
  async (_, { rejectWithValue }) => {
    try {
      const bundles = await fetchBundles();
      return bundles;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch bundles');
    }
  }
);

const bundlesSlice = createSlice({
  name: 'bundles',
  initialState: {
    data: [] as Bundle[],
    loading: false,
    error: null as string | null,
  },
  reducers: {
    clearBundlesError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchBundlesAsync.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchBundlesAsync.fulfilled, (state, action) => {
        state.loading = false;
        state.data = sortBundlesForDisplay(action.payload);
        state.error = null;
      })
      .addCase(fetchBundlesAsync.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearBundlesError } = bundlesSlice.actions;

const bundleSelectionSlice = createSlice({
  name: 'bundleSelection',
  /** Keys: bundle system_name (`Bundle.id` from GET /api/bundles), not display `name`. */
  initialState: {} as Record<string, boolean>,
  reducers: {
    setBundleSelected: (state, action) => {
      const { bundleId, selected } = action.payload;
      state[bundleId] = selected;
    },
    toggleBundleSelected: (state, action) => {
      const bundleId = action.payload;
      state[bundleId] = !state[bundleId];
    },
  },
});

export const { setBundleSelected, toggleBundleSelected } = bundleSelectionSlice.actions;

const modelSelectionSlice = createSlice({
  name: 'modelSelection',
  initialState: {
    selectedProvider: '',
    selectedModel: '',
    selectedConfig: '',
    isConfigValid: false,
    isTestNameValid: false,
    /** Benchmark run name (Test Name field on model selection page) */
    testName: '',
    /** Relational FKs for POST /api/start-benchmark-run (standard providers only) */
    benchmarkLlmProviderId: null as number | null,
    benchmarkLlmProviderModelId: null as number | null,
    benchmarkLlmProviderModelConfigId: null as number | null,
    benchmarkCustomAppId: null as number | null,
    benchmarkCustomAppConfigId: null as number | null,
  },
  reducers: {
    setSelectedProvider: (state, action) => {
      state.selectedProvider = action.payload;
      // Reset model and config when provider changes
      state.selectedModel = '';
      state.selectedConfig = '';
      state.benchmarkLlmProviderId = null;
      state.benchmarkLlmProviderModelId = null;
      state.benchmarkLlmProviderModelConfigId = null;
      state.benchmarkCustomAppId = null;
      state.benchmarkCustomAppConfigId = null;
    },
    setSelectedModel: (state, action) => {
      state.selectedModel = action.payload;
      // Clear config when model is selected
      state.selectedConfig = '';
      state.benchmarkCustomAppId = null;
      state.benchmarkCustomAppConfigId = null;
    },
    setSelectedConfig: (state, action) => {
      state.selectedConfig = action.payload;
      // Clear model when config is selected
      state.selectedModel = '';
      state.benchmarkLlmProviderId = null;
      state.benchmarkLlmProviderModelId = null;
      state.benchmarkLlmProviderModelConfigId = null;
    },
    setBenchmarkRunFks: (
      state,
      action: {
        payload: {
          llm_provider_id: number | null;
          llm_provider_model_id: number | null;
          llm_provider_model_config_id: number | null;
          custom_app_id?: number | null;
          custom_app_config_id?: number | null;
        };
      }
    ) => {
      state.benchmarkLlmProviderId = action.payload.llm_provider_id;
      state.benchmarkLlmProviderModelId = action.payload.llm_provider_model_id;
      state.benchmarkLlmProviderModelConfigId = action.payload.llm_provider_model_config_id;
      if (action.payload.custom_app_id !== undefined) {
        state.benchmarkCustomAppId = action.payload.custom_app_id;
      }
      if (action.payload.custom_app_config_id !== undefined) {
        state.benchmarkCustomAppConfigId = action.payload.custom_app_config_id;
      }
    },
    updateConfigValidity: (state) => {
      const base =
        Boolean(state.selectedProvider) &&
        (Boolean(state.selectedModel) || Boolean(state.selectedConfig));
      if (!base) {
        state.isConfigValid = false;
        return;
      }
      if (state.selectedModel) {
        state.isConfigValid =
          state.benchmarkLlmProviderModelConfigId != null &&
          state.benchmarkLlmProviderModelConfigId > 0;
      } else {
        state.isConfigValid =
          state.benchmarkCustomAppConfigId != null &&
          state.benchmarkCustomAppConfigId > 0;
      }
    },
    setTestNameFilled: (state, action) => {
      state.isTestNameValid = action.payload;
    },
    setBenchmarkTestName: (state, action: { payload: string }) => {
      state.testName = action.payload;
    },
    resetModelSelection: (state) => {
      state.selectedProvider = '';
      state.selectedModel = '';
      state.selectedConfig = '';
      state.isConfigValid = false;
      state.isTestNameValid = false;
      state.testName = '';
      state.benchmarkLlmProviderId = null;
      state.benchmarkLlmProviderModelId = null;
      state.benchmarkLlmProviderModelConfigId = null;
      state.benchmarkCustomAppId = null;
      state.benchmarkCustomAppConfigId = null;
    },
  },
});

export const { 
  setSelectedProvider, 
  setSelectedModel, 
  setSelectedConfig, 
  setBenchmarkRunFks,
  updateConfigValidity, 
  setTestNameFilled,
  setBenchmarkTestName,
  resetModelSelection 
} = modelSelectionSlice.actions;

const testSelectionSlice = createSlice({
  name: 'testSelection',
  initialState: {} as TestSelectionState,
  reducers: {
    setTestSelected: (state, action) => {
      const { bundleId, testKey, selected } = action.payload;
      if (!state[bundleId]) {
        state[bundleId] = {};
      }
      state[bundleId][testKey] = selected;
    },
    toggleTestSelected: (state, action) => {
      const { bundleId, testKey } = action.payload;
      if (!state[bundleId]) {
        state[bundleId] = {};
      }
      state[bundleId][testKey] = !state[bundleId][testKey];
    },
    setMultipleTestsSelected: (state, action) => {
      const { bundleId, testKeys, selected } = action.payload;
      if (!state[bundleId]) {
        state[bundleId] = {};
      }
      testKeys.forEach((testKey: string) => {
        state[bundleId][testKey] = selected;
      });
    },
    clearTestSelection: () => {
      return {};
    },
    clearTestsForBundle: (state, action) => {
      const bundleId = action.payload;
      delete state[bundleId];
    },
  },
});

export const { 
  setTestSelected, 
  toggleTestSelected, 
  setMultipleTestsSelected, 
  clearTestSelection,
  clearTestsForBundle 
} = testSelectionSlice.actions;

// Endpoint connection status slice
// Status values: "connected", "not connected", "Invalid Token"
const endpointStatusSlice = createSlice({
  name: 'endpointStatus',
  initialState: {} as Record<string, string>,
  reducers: {
    setEndpointStatus: (state, action) => {
      const { configId, status } = action.payload;
      state[configId] = status;
    },
    clearEndpointStatus: (state, action) => {
      const configId = action.payload;
      delete state[configId];
    },
    clearAllEndpointStatuses: (state) => {
      return {};
    },
  },
});

export const { 
  setEndpointStatus, 
  clearEndpointStatus, 
  clearAllEndpointStatuses 
} = endpointStatusSlice.actions;

export type SampleSizeMode = 'all' | 'calculated';

export interface SampleSizeSelectionState {
  mode: SampleSizeMode;
  populationMean: string;
  confidenceLevel: string;
  marginOfError: string;
}

const sampleSizeSelectionInitialState: SampleSizeSelectionState = {
  mode: 'all',
  populationMean: '90',
  confidenceLevel: '95',
  marginOfError: '3',
};

const sampleSizeSelectionSlice = createSlice({
  name: 'sampleSizeSelection',
  initialState: sampleSizeSelectionInitialState,
  reducers: {
    setSampleSizeMode: (state, action: { payload: SampleSizeMode }) => {
      state.mode = action.payload;
    },
    setSampleSizePopulationMean: (state, action: { payload: string }) => {
      state.populationMean = action.payload;
    },
    setSampleSizeConfidenceLevel: (state, action: { payload: string }) => {
      state.confidenceLevel = action.payload;
    },
    setSampleSizeMarginOfError: (state, action: { payload: string }) => {
      state.marginOfError = action.payload;
    },
  },
});

export const {
  setSampleSizeMode,
  setSampleSizePopulationMean,
  setSampleSizeConfidenceLevel,
  setSampleSizeMarginOfError,
} = sampleSizeSelectionSlice.actions;

const rootReducer = combineReducers({
  bundles: bundlesSlice.reducer,
  bundleSelection: bundleSelectionSlice.reducer,
  modelSelection: modelSelectionSlice.reducer,
  testSelection: testSelectionSlice.reducer,
  endpointStatus: endpointStatusSlice.reducer,
  sampleSizeSelection: sampleSizeSelectionSlice.reducer,
});

const store = configureStore({
  reducer: rootReducer,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

/** Nested partial for test preloaded state (matches createTestStore merge behavior). */
export type DeepPartial<T> = {
  [K in keyof T]?: T[K] extends object ? DeepPartial<T[K]> : T[K];
};

// Export function to create a test store with optional preloaded state
export function createTestStore(preloadedState?: DeepPartial<RootState>) {
  const defaultState = store.getState();
  
  // Merge preloadedState with default state
  const mergedState = preloadedState 
    ? {
        bundles: { ...defaultState.bundles, ...(preloadedState.bundles || {}) },
        bundleSelection: { ...defaultState.bundleSelection, ...(preloadedState.bundleSelection || {}) },
        modelSelection: { ...defaultState.modelSelection, ...(preloadedState.modelSelection || {}) },
        testSelection: { ...defaultState.testSelection, ...(preloadedState.testSelection || {}) },
        endpointStatus: { ...defaultState.endpointStatus, ...(preloadedState.endpointStatus || {}) },
        sampleSizeSelection: {
          ...defaultState.sampleSizeSelection,
          ...(preloadedState.sampleSizeSelection || {}),
        },
      }
    : defaultState;
  
  return configureStore({
    reducer: rootReducer,
    preloadedState: mergedState as any,
  });
}

export default store;
