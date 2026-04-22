"use client"
import React, { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { useAppSelector } from '../../../hooks/reduxHooks';
import { startBenchmarkRun, ApiError } from '@/lib/api';
import { custom_connectors } from './MockData';

interface BenchmarkFooterProps {
  currentPage: 'bundle-selection' | 'model-selection';
  setCurrentPage: (page: 'bundle-selection' | 'model-selection') => void;
}


export default function BenchmarkFooter({ 
  currentPage,
  setCurrentPage
}: BenchmarkFooterProps) {
  const router = useRouter();
  const [isStartingRun, setIsStartingRun] = useState(false);
  const bundleSelection = useAppSelector((state) => state.bundleSelection);
  const {
    isConfigValid,
    testName,
    selectedProvider,
    benchmarkLlmProviderId,
    benchmarkLlmProviderModelId,
    benchmarkLlmProviderModelConfigId,
  } = useAppSelector((state) => state.modelSelection);
  const runName = (testName ?? '').trim();

  const selectedBundleSystemNames = useMemo(
    () => Object.entries(bundleSelection).filter(([, v]) => v).map(([id]) => id),
    [bundleSelection]
  );

  const isCustomConnector = custom_connectors.some((c) => c.id === selectedProvider);

  const canStartDbBenchmark =
    !isCustomConnector &&
    benchmarkLlmProviderId != null &&
    benchmarkLlmProviderModelId != null &&
    benchmarkLlmProviderModelConfigId != null &&
    selectedBundleSystemNames.length > 0;
  
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

  const handleRunTests = async () => {
    if (isStartingRun) return;
    if (!runName) {
      window.alert('Please enter a Test Name before running.');
      return;
    }
    if (
      benchmarkLlmProviderId == null ||
      benchmarkLlmProviderModelId == null ||
      benchmarkLlmProviderModelConfigId == null
    ) {
      window.alert('Select a database-backed model with a saved configuration before running.');
      return;
    }
    setIsStartingRun(true);
    try {
      await startBenchmarkRun({
        run_name: runName,
        bundle_names: selectedBundleSystemNames,
        llm_provider_id: benchmarkLlmProviderId,
        llm_provider_model_id: benchmarkLlmProviderModelId,
        llm_provider_model_config_id: benchmarkLlmProviderModelConfigId,
      });
      router.push('/history');
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? e.message
          : e instanceof Error
            ? e.message
            : 'Failed to start benchmark run';
      window.alert(msg);
    } finally {
      setIsStartingRun(false);
    }
  };
  
  // Calculate selected bundles count
  const selectedBundlesCount = selectedBundleSystemNames.length;

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
            onClick={() => void handleRunTests()}
            disabled={
              !isConfigValid ||
              !runName ||
              isStartingRun ||
              isCustomConnector ||
              !canStartDbBenchmark
            }
            data-testid="run-benchmark-tests"
          >
            {isStartingRun ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                Starting…
              </>
            ) : (
              'Run Benchmark Tests'
            )}
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
