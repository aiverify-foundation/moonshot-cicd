"use client"
import React, { useState } from 'react';
import { Provider } from 'react-redux';
import store from '../../../store';
import BundleSelectionPage from './BundleSelectionPage';
import ModelSelectionPage from './ModelSelectionPage';
import BenchmarkSidebar from './BenchmarkSidebar';
import BenchmarkFooter from './BenchmarkFooter';

type PageType = 'bundle-selection' | 'model-selection';

export default function BenchmarkApp() {
  const [currentPage, setCurrentPage] = useState<PageType>('bundle-selection');

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'model-selection':
        return <ModelSelectionPage />;
      case 'bundle-selection':
      default:
        return <BundleSelectionPage />;
    }
  };

  return (
    <Provider store={store}>
        <BenchmarkSidebar currentPage={currentPage} />
        {renderCurrentPage()}
        <BenchmarkFooter 
          currentPage={currentPage}
          setCurrentPage={setCurrentPage}
        />
    </Provider>
  );
}
