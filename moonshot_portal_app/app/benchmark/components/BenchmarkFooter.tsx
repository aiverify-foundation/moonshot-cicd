"use client"
import React, { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { useAppSelector } from '../../../hooks/reduxHooks';
import { startBenchmarkRun, ApiError } from '@/lib/api';
import { selectedTestsInBundle } from '@/lib/benchmarkTestSelection';

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
  const testSelection = useAppSelector((state) => state.testSelection);
  const bundles = useAppSelector((state) => state.bundles.data);
  const {
    isConfigValid,
    isTestNameValid,
    testName,
    benchmarkLlmProviderId,
    benchmarkLlmProviderModelId,
    benchmarkLlmProviderModelConfigId,
    benchmarkCustomAppId,
    benchmarkCustomAppConfigId,
  } = useAppSelector((state) => state.modelSelection);
  const runName = (testName ?? '').trim();

  const selectedBundleSystemNames = useMemo(
    () => Object.entries(bundleSelection).filter(([, v]) => v).map(([id]) => id),
    [bundleSelection]
  );

  /** When some tests in a bundle are unchecked, send `tests_by_bundle` using DB test ids from the API. */
  const testsByBundle = useMemo(() => {
    const out: Record<string, number[]> = {};
    for (const bundleId of selectedBundleSystemNames) {
      const bundle = bundles.find((b) => b.id === bundleId);
      if (!bundle?.tests?.length) continue;
      const selectedTests = selectedTestsInBundle(testSelection, bundleId, bundle.tests);
      const allSelected = selectedTests.length === bundle.tests.length;
      if (allSelected) continue;
      if (selectedTests.length === 0) {
        return {
          error: `Select at least one test in bundle "${bundle.name}", or deselect the bundle.`,
        } as const;
      }
      const ids: number[] = [];
      for (const t of selectedTests) {
        if (t.benchmark_test_id == null) {
          return { error: `Missing benchmark id for test "${t.name}" in bundle "${bundle.name}".` } as const;
        }
        ids.push(t.benchmark_test_id);
      }
      if (ids.length > 0) {
        out[bundleId] = ids;
      }
    }
    return { map: out } as const;
  }, [bundles, selectedBundleSystemNames, testSelection]);

  const canStartLlmBenchmark =
    benchmarkLlmProviderId != null &&
    benchmarkLlmProviderModelId != null &&
    benchmarkLlmProviderModelConfigId != null &&
    selectedBundleSystemNames.length > 0;

  const canStartCustomAppBenchmark =
    benchmarkCustomAppId != null &&
    benchmarkCustomAppConfigId != null &&
    selectedBundleSystemNames.length > 0;

  const canStartBenchmark = canStartLlmBenchmark || canStartCustomAppBenchmark;
  
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
    if (!canStartLlmBenchmark && !canStartCustomAppBenchmark) {
      window.alert(
        'Select a saved model configuration or custom application configuration before running.'
      );
      return;
    }
    if ('error' in testsByBundle) {
      window.alert(testsByBundle.error);
      return;
    }

    setIsStartingRun(true);
    try {
      const tests_by_bundle =
        Object.keys(testsByBundle.map).length > 0 ? testsByBundle.map : undefined;

      if (canStartCustomAppBenchmark) {
        await startBenchmarkRun({
          run_name: runName,
          bundle_names: selectedBundleSystemNames,
          custom_app_id: benchmarkCustomAppId!,
          custom_app_config_id: benchmarkCustomAppConfigId!,
          ...(tests_by_bundle ? { tests_by_bundle } : {}),
        });
      } else {
        await startBenchmarkRun({
          run_name: runName,
          bundle_names: selectedBundleSystemNames,
          llm_provider_id: benchmarkLlmProviderId!,
          llm_provider_model_id: benchmarkLlmProviderModelId!,
          llm_provider_model_config_id: benchmarkLlmProviderModelConfigId!,
          ...(tests_by_bundle ? { tests_by_bundle } : {}),
        });
      }
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
              !isTestNameValid ||
              isStartingRun ||
              !canStartBenchmark
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
        <div>
          {getLeftButton()}
        </div>
        <div>
          {getRightButton()}
        </div>
      </div>
    </div>
  );
}
