"use client"
import React, { useEffect, useRef, useMemo } from 'react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Card, CardContent, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CircleCheckBig } from 'lucide-react';
import { useBundlesRedux } from '../../../hooks/useBundlesRedux';
import { useSelectedBundles } from '../../../hooks/useSelectedBundles';
import { useTestSelectionActions } from '../../../hooks/useTestSelection';
import { useAppSelector } from '../../../hooks/reduxHooks';
import type { BundleTest } from '@/lib/api';
import {
  areAllTestsSelected,
  countSelectedTests,
  countSelectedTestsAcrossBundles,
  isTestSelected,
  selectedTestsInBundle,
} from '@/lib/benchmarkTestSelection';

interface AccordionTestData {
  bundleId: string;
  test: BundleTest;
  title: string;
  status: 'pending' | 'completed';
  promptCount: number;
  metricName: string;
  description: string;
  configId?: string;
}

interface BundleAccordionData {
  id: string;
  title: string;
  items: AccordionTestData[];
  selectedCount: number;
}

export default function BenchmarkSidebar() {
  useBundlesRedux();
  const selectedBundles = useSelectedBundles();
  const { toggleTest, setMultipleTests, clearBundleTests } = useTestSelectionActions();
  const testSelection = useAppSelector((state) => state.testSelection);
  const processedBundles = useRef<Set<string>>(new Set());

  // Auto-select all tests from selected bundles by default (only for new bundles)
  useEffect(() => {
    const currentBundleIds = new Set(selectedBundles.map((b) => b.id));

    const newBundles = selectedBundles.filter((bundle) => !processedBundles.current.has(bundle.id));

    if (newBundles.length > 0) {
      newBundles.forEach((bundle) => {
        const alreadySelected = selectedTestsInBundle(testSelection, bundle.id, bundle.tests);

        if (alreadySelected.length === 0 && bundle.tests.length > 0) {
          setMultipleTests(bundle.id, bundle.tests, true);
        }

        processedBundles.current.add(bundle.id);
      });
    }

    Array.from(processedBundles.current).forEach((bundleId) => {
      if (!currentBundleIds.has(bundleId)) {
        clearBundleTests(bundleId);
        processedBundles.current.delete(bundleId);
      }
    });
  }, [selectedBundles, testSelection, setMultipleTests, clearBundleTests]);

  const handleCheckChange = (bundleId: string, test: BundleTest) => {
    toggleTest(bundleId, test);
  };

  const handleParentCheckChange = (bundleId: string) => {
    const bundle = selectedBundles.find((b) => b.id === bundleId);
    if (!bundle) return;

    const allChecked = areAllTestsSelected(testSelection, bundleId, bundle.tests);
    setMultipleTests(bundleId, bundle.tests, !allChecked);
  };

  const createTestAccordionItem = (data: AccordionTestData) => {
    const isChecked = isTestSelected(testSelection, data.bundleId, data.test);

    return (
      <Card key={`${data.bundleId}-${data.test.name}`} className="w-full mt-2 py-1 rounded-sm">
        <Accordion type="single" collapsible>
          <AccordionItem value={`${data.bundleId}-${data.test.name}`} className="border-none">
            <div className="flex items-center px-4 py-1">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <Checkbox
                    checked={isChecked}
                    onCheckedChange={() => handleCheckChange(data.bundleId, data.test)}
                    className="rounded-sm"
                  />
                  <CardTitle className="text-sm font-medium">{data.title}</CardTitle>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <CircleCheckBig
                  className={`h-5 w-5 ${
                    data.status === 'completed' ? 'text-green-500' : 'text-gray-300'
                  }`}
                />
                <AccordionTrigger className="hover:no-underline p-0">
                  <span className="sr-only">Toggle {data.title} details</span>
                </AccordionTrigger>
              </div>
            </div>
            <AccordionContent>
              <CardContent className="px-4 py-2">
                <div className="space-y-3">
                  <div className="text-sm text-gray-600">
                    <div className="flex items-center gap-2 mt-2 mb-2">
                      <span>Prompts : </span>
                      <span className="font-bold">{data.promptCount}</span>
                    </div>
                    <div className="mb-3">
                      <span>Evaluation Logic : </span>
                      <span className="font-bold">{data.metricName}</span>
                    </div>
                    <div className="mb-3">
                      <span className="font-medium">Description :</span>
                      <p className="mt-1">{data.description || 'No description available'}</p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const testName = encodeURIComponent(data.test.name);
                        const datasetId = encodeURIComponent(data.test.dataset.id);
                        window.open(`/view_test?test=${testName}&dataset=${datasetId}`, '_blank');
                      }}
                    >
                      Learn More
                    </Button>
                  </div>
                </div>
              </CardContent>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </Card>
    );
  };

  const createParentAccordion = (data: BundleAccordionData) => {
    const bundle = selectedBundles.find((b) => b.id === data.id);
    const allChecked =
      bundle != null && areAllTestsSelected(testSelection, data.id, bundle.tests);

    return (
      <AccordionItem key={data.id} value={data.id} className="border-none">
        <div className="flex items-center">
          <Badge variant="outline" className="flex items-center gap-2 px-3 py-2">
            <Checkbox
              checked={allChecked}
              onCheckedChange={() => handleParentCheckChange(data.id)}
              className="rounded-sm"
            />
            <span className="font-medium text-sm">
              {data.title} [{data.selectedCount}/{data.items.length}]
            </span>
          </Badge>
          <Separator orientation="horizontal" className="flex-1 mx-2" />
          <AccordionTrigger className="hover:no-underline">
            <span className="sr-only">Toggle {data.title} section</span>
          </AccordionTrigger>
        </div>
        <AccordionContent className="px-4">
          <div>{data.items.map((item) => createTestAccordionItem(item))}</div>
        </AccordionContent>
      </AccordionItem>
    );
  };

  const parentAccordionData: BundleAccordionData[] = useMemo(
    () =>
      selectedBundles.map((bundle) => ({
        id: bundle.id,
        title: bundle.name,
        selectedCount: countSelectedTests(testSelection, bundle.id, bundle.tests),
        items: bundle.tests.map((test) => ({
          bundleId: bundle.id,
          test,
          title: test.name,
          status: 'pending' as const,
          promptCount: test.dataset?.num_of_dataset_prompts ?? 0,
          metricName: test.metric?.name ?? 'N/A',
          description: test.description ?? '',
          configId: test.metric?.config_id,
        })),
      })),
    [selectedBundles, testSelection]
  );

  const { totalTests, selectedTests } = useMemo(() => {
    const total = parentAccordionData.reduce((acc, bundle) => acc + bundle.items.length, 0);
    const selected = countSelectedTestsAcrossBundles(
      testSelection,
      selectedBundles.map((b) => b.id)
    );
    return { totalTests: total, selectedTests: selected };
  }, [parentAccordionData, testSelection, selectedBundles]);

  return (
    <div
      style={{
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        padding: '20px 24px 32px',
        gap: '8px',
        isolation: 'isolate',
        position: 'fixed',
        width: '385px',
        height: '100vh',
        right: '0px',
        top: '0px',
        background: '#F8FAFC',
        borderLeft: '1px solid #E2E8F0',
      }}
    >
      <div className="w-full max-w-md mx-auto px-4 py-2">
        <h2 className="text-lg font-semibold mb-2">
          Selected Tests [{selectedTests}/{totalTests}]
        </h2>
        <Separator className="mb-4" />
      </div>
      <div className="w-full max-w-md mx-auto p-1 flex-1 overflow-y-auto">
        {parentAccordionData.length > 0 ? (
          <Accordion type="multiple">
            {parentAccordionData.map((data) => createParentAccordion(data))}
          </Accordion>
        ) : (
          <div className="text-center text-gray-500 py-8">
            No bundles selected. Please select Test Bundles to view their tests.
          </div>
        )}
      </div>
    </div>
  );
}
