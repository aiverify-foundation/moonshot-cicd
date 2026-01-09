import React, { ReactElement } from 'react';
import { render as rtlRender, RenderOptions, screen, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { Store } from '@reduxjs/toolkit';
import { createTestStore, RootState } from '@/store';

// we need the custome render function to wrap the component with the Redux Provider
// because the component is using the useAppSelector hook to get the state, 
// if we don't wrap the component with the Redux Provider
// the useAppSelector hook will not be able to get the state, 
// and the component will not render correctly

// Re-export testing utilities
export { screen, waitFor };

// Custom render function that wraps components with Redux Provider
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  preloadedState?: Partial<RootState>;
  store?: Store;
}

export function render(
  ui: ReactElement,
  {
    preloadedState,
    store = createTestStore(preloadedState),
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <Provider store={store}>{children}</Provider>;
  }

  const result = rtlRender(ui, { wrapper: Wrapper, ...renderOptions });
  return {
    ...result,
    store,
  };
}

// Re-export createTestStore for convenience
export { createTestStore };

