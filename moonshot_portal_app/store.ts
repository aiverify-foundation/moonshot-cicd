import { configureStore, createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { fetchBundles, Bundle, fetchFixedConfigs, FixedConfig } from './lib/api';

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

// Async thunk for fetching fixed configs
export const fetchFixedConfigsAsync = createAsyncThunk(
  'fixedConfigs/fetchFixedConfigs',
  async (_, { rejectWithValue }) => {
    try {
      const configs = await fetchFixedConfigs();
      return configs;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch fixed configs');
    }
  }
);

const fixedConfigsSlice = createSlice({
  name: 'fixedConfigs',
  initialState: {
    data: [] as FixedConfig[],
    loading: false,
    error: null as string | null,
  },
  reducers: {
    clearFixedConfigsError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchFixedConfigsAsync.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchFixedConfigsAsync.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
        state.error = null;
      })
      .addCase(fetchFixedConfigsAsync.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearFixedConfigsError } = fixedConfigsSlice.actions;

const bundleSelectionSlice = createSlice({
  name: 'bundleSelection',
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
  },
  reducers: {
    setSelectedProvider: (state, action) => {
      state.selectedProvider = action.payload;
      // Reset model and config when provider changes
      state.selectedModel = '';
      state.selectedConfig = '';
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
    },
    updateConfigValidity: (state) => {
      state.isConfigValid = Boolean(state.selectedProvider && (state.selectedModel || state.selectedConfig));
    },
    setTestNameFilled: (state, action) => {
      state.isTestNameValid = action.payload;
    },
    resetModelSelection: (state) => {
      state.selectedProvider = '';
      state.selectedModel = '';
      state.selectedConfig = '';
      state.isConfigValid = false;
      state.isTestNameValid = false;
    },
  },
});

export const { 
  setSelectedProvider, 
  setSelectedModel, 
  setSelectedConfig, 
  updateConfigValidity, 
  setTestNameFilled,
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

const store = configureStore({
  reducer: {
    bundles: bundlesSlice.reducer,
    fixedConfigs: fixedConfigsSlice.reducer,
    bundleSelection: bundleSelectionSlice.reducer,
    modelSelection: modelSelectionSlice.reducer,
    testSelection: testSelectionSlice.reducer,
    endpointStatus: endpointStatusSlice.reducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export default store;
