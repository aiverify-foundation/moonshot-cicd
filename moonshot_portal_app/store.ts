import { configureStore, createSlice, createAsyncThunk } from '@reduxjs/toolkit';
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
    resetModelSelection: (state) => {
      state.selectedProvider = '';
      state.selectedModel = '';
      state.selectedConfig = '';
      state.isConfigValid = false;
    },
  },
});

export const { 
  setSelectedProvider, 
  setSelectedModel, 
  setSelectedConfig, 
  updateConfigValidity, 
  resetModelSelection 
} = modelSelectionSlice.actions;

const store = configureStore({
  reducer: {
    bundles: bundlesSlice.reducer,
    bundleSelection: bundleSelectionSlice.reducer,
    modelSelection: modelSelectionSlice.reducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export default store;
