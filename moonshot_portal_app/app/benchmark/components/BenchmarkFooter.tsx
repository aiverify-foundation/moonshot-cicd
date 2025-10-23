"use client"
import React from 'react';
import { useRouter } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { useAppSelector } from '../../../hooks/reduxHooks';

interface BenchmarkFooterProps {
  currentPage: 'bundle-selection' | 'model-selection';
  setCurrentPage: (page: 'bundle-selection' | 'model-selection') => void;
}


export default function BenchmarkFooter({ 
  currentPage,
  setCurrentPage
}: BenchmarkFooterProps) {
  const router = useRouter();
  const bundleSelection = useAppSelector((state) => state.bundleSelection);
  const { isConfigValid } = useAppSelector(state => state.modelSelection);
  
  // Navigation functions
  const handleNavigateToModels = () => {
    setCurrentPage('model-selection');
  };

  const handleBackToBundles = () => {
    setCurrentPage('bundle-selection');
  };

  const handleBackToHome = () => {
    router.push('/');
  };

  const handleRunTests = () => {
    // This would typically trigger the benchmark test execution
    console.log('Running benchmark tests...');
    // For now, just go back to bundles
    setCurrentPage('bundle-selection');
  };
  
  // Calculate selected bundles count
  const selectedBundlesCount = Object.values(bundleSelection).filter(Boolean).length;

  const getLeftButton = () => {
    switch (currentPage) {
      case 'bundle-selection':
        return (
          <Button 
            variant="outline" 
            className="flex items-center gap-2"
            onClick={handleBackToHome}
            data-testid="back-to-home-button"
          >
            Back to Home Page
          </Button>
        );
      case 'model-selection':
        return (
          <Button 
            variant="outline" 
            className="flex items-center gap-2"
            onClick={handleBackToBundles}
            data-testid="back-to-bundles-button"
          >
            Back to Bundle Selection
          </Button>
        );
      default:
        return null;
    }
  };

  const getRightButton = () => {
    switch (currentPage) {
      case 'bundle-selection':
        return (
          <Button 
            className="flex items-center gap-2" 
            onClick={handleNavigateToModels}
            disabled={selectedBundlesCount === 0}
            data-testid="configure-and-run-benchmark-tests"
          >
            Configure and Run Benchmark Tests
          </Button>
        );
      case 'model-selection':
        return (
          <Button 
            className="flex items-center gap-2" 
            onClick={handleRunTests}
            disabled={!isConfigValid}
            data-testid="run-benchmark-tests"
          >
            Run Benchmark Tests
          </Button>
        );
      default:
        return null;
    }
  };

  return (
    <div className="fixed bottom-0 left-12 right-0 h-[60px] bg-white border-t border-gray-200 shadow-lg z-50">
      <div className="flex items-center justify-between h-full px-6">
        {/* Left Button */}
        <div>
          {getLeftButton()}
        </div>

        {/* Right Button */}
        <div>
          {getRightButton()}
        </div>
      </div>
    </div>
  );
}
