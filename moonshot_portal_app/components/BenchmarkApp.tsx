"use client"
import React, { useState } from 'react';
import { Provider } from 'react-redux';
import store from '../store';
import BundleSelectionPage from '../components/BundleSelectionPage';
import ModelSelectionPage from '../components/ModelSelectionPage';

type PageType = 'home' | 'bundle-selection' | 'model-selection';

export default function BenchmarkApp() {
  const [currentPage, setCurrentPage] = useState<PageType>('home');

  const handleNavigateToBundles = () => {
    setCurrentPage('bundle-selection');
  };

  const handleNavigateToModels = () => {
    setCurrentPage('model-selection');
  };

  const handleBackToHome = () => {
    setCurrentPage('home');
  };

  const handleBackToBundles = () => {
    setCurrentPage('bundle-selection');
  };

  const handleRunTests = () => {
    // This would typically trigger the benchmark test execution
    console.log('Running benchmark tests...');
    // For now, just go back to home
    setCurrentPage('home');
  };

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'bundle-selection':
        return (
          <BundleSelectionPage 
            onNext={handleNavigateToModels}
            onBack={handleBackToHome}
          />
        );
      case 'model-selection':
        return (
          <ModelSelectionPage 
            onBack={handleBackToBundles}
            onNext={handleRunTests}
          />
        );
      case 'home':
      default:
        return (
          <main className="p-8">
            <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
              <h1 className="text-3xl font-bold">Benchmark Test Suite</h1>
              <p className="text-gray-600 text-center max-w-md">
                Welcome to the Benchmark Test Suite. Start by selecting bundles for your benchmark test.
              </p>
              <button
                className="rounded-full border border-solid border-blue-500 transition-colors flex items-center justify-center bg-blue-500 text-white gap-2 hover:bg-blue-700 font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5 sm:w-auto mt-4"
                onClick={handleNavigateToBundles}
                data-testid="start-benchmark-button"
              >
                Start New Benchmark Test
              </button>
            </div>
          </main>
        );
    }
  };

  return (
    <Provider store={store}>
      {renderCurrentPage()}
    </Provider>
  );
}
