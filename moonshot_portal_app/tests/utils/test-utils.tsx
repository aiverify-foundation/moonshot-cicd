import React, { ReactElement } from 'react';
import { render as rtlRender, RenderOptions, screen, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { Store } from '@reduxjs/toolkit';
import { createTestStore, DeepPartial, RootState } from '@/store';

//React Testing Library's default render doesn't provide a Redux store. 
// Without a Provider, useAppDispatch and useAppSelector will throw an error 
// because they can't access the Redux context.
// So we need to create a custom render function that wraps the component
// with the Redux Provider. This is a workaround to get the Redux store into the component.


// Re-export testing utilities
export { screen, waitFor };

// Custom render function that wraps components with Redux Provider
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  preloadedState?: DeepPartial<RootState>;
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

