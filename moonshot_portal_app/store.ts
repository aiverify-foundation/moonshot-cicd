import { configureStore, createSlice, createAsyncThunk, combineReducers } from '@reduxjs/toolkit';
import { fetchBundles, Bundle } from './lib/api';

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
        state.data = action.payload;
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
    },
    setSelectedModel: (state, action) => {
      state.selectedModel = action.payload;
      // Clear config when model is selected
      state.selectedConfig = '';
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
        };
      }
    ) => {
      state.benchmarkLlmProviderId = action.payload.llm_provider_id;
      state.benchmarkLlmProviderModelId = action.payload.llm_provider_model_id;
      state.benchmarkLlmProviderModelConfigId = action.payload.llm_provider_model_config_id;
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
        state.isConfigValid = Boolean(state.selectedConfig);
      }
    },
    setTestNameFilled: (state, action) => {
      state.isTestNameValid = action.payload;
    },
    setBenchmarkTestName: (state, action: { payload: string }) => {
      state.testName = action.payload;
      state.isTestNameValid = action.payload.trim().length > 0;
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
  initialState: {} as Record<string, boolean>,
  reducers: {
    setTestSelected: (state, action) => {
      const { testName, selected } = action.payload;
      state[testName] = selected;
    },
    toggleTestSelected: (state, action) => {
      const testName = action.payload;
      state[testName] = !state[testName];
    },
    setMultipleTestsSelected: (state, action) => {
      const { testNames, selected } = action.payload;
      testNames.forEach((testName: string) => {
        state[testName] = selected;
      });
    },
    clearTestSelection: (state) => {
      return {};
    },
    clearTestsForBundle: (state, action) => {
      const bundleName = action.payload;
      // This will be handled by the component logic
      return state;
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

const rootReducer = combineReducers({
  bundles: bundlesSlice.reducer,
  bundleSelection: bundleSelectionSlice.reducer,
  modelSelection: modelSelectionSlice.reducer,
  testSelection: testSelectionSlice.reducer,
  endpointStatus: endpointStatusSlice.reducer,
});

const store = configureStore({
  reducer: rootReducer,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Export function to create a test store with optional preloaded state
export function createTestStore(preloadedState?: Partial<RootState>) {
  const defaultState = store.getState();
  
  // Merge preloadedState with default state
  const mergedState = preloadedState 
    ? {
        bundles: { ...defaultState.bundles, ...(preloadedState.bundles || {}) },
        bundleSelection: { ...defaultState.bundleSelection, ...(preloadedState.bundleSelection || {}) },
        modelSelection: { ...defaultState.modelSelection, ...(preloadedState.modelSelection || {}) },
        testSelection: { ...defaultState.testSelection, ...(preloadedState.testSelection || {}) },
        endpointStatus: { ...defaultState.endpointStatus, ...(preloadedState.endpointStatus || {}) },
      }
    : defaultState;
  
  return configureStore({
    reducer: rootReducer,
    preloadedState: mergedState as any,
  });
}

export default store;
