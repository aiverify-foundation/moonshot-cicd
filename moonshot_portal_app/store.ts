import { configureStore, createSlice } from '@reduxjs/toolkit';

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
    bundleSelection: bundleSelectionSlice.reducer,
    modelSelection: modelSelectionSlice.reducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export default store;
