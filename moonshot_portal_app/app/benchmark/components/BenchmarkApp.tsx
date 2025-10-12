"use client"
import React, { useState } from 'react';
import { Provider } from 'react-redux';
import store from '../../../store';
import BundleSelectionPage from './BundleSelectionPage';
import ModelSelectionPage from './ModelSelectionPage';

type PageType = 'bundle-selection' | 'model-selection';

export default function BenchmarkApp() {
  const [currentPage, setCurrentPage] = useState<PageType>('bundle-selection');

  const handleNavigateToModels = () => {
    setCurrentPage('model-selection');
  };

  const handleBackToBundles = () => {
    setCurrentPage('bundle-selection');
  };

  const handleRunTests = () => {
    // This would typically trigger the benchmark test execution
    console.log('Running benchmark tests...');
    // For now, just go back to bundles
    setCurrentPage('bundle-selection');
  };

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'model-selection':
        return (
          <ModelSelectionPage 
            onBack={handleBackToBundles}
            onNext={handleRunTests}
          />
        );
      case 'bundle-selection':
      default:
        return (
          <BundleSelectionPage 
            onNext={handleNavigateToModels}
            onBack={() => window.history.back()}
          />
        );
    }
  };

  return (
    <Provider store={store}>
      {renderCurrentPage()}
    </Provider>
  );
}
