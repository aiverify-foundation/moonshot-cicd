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

const store = configureStore({
  reducer: {
    bundleSelection: bundleSelectionSlice.reducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
export default store;
