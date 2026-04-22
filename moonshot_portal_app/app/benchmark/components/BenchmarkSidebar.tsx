"use client"
import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Card, CardContent, CardDescription, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CircleCheckBig } from 'lucide-react';
import { useBundlesRedux } from '../../../hooks/useBundlesRedux';
import { useSelectedBundles } from '../../../hooks/useSelectedBundles';
import { useIsTestSelected, useTestSelectionActions } from '../../../hooks/useTestSelection';
import { useAppSelector } from '../../../hooks/reduxHooks';
import { useFixedConfigsRedux } from '../../../hooks/useFixedConfigsRedux';
import { FixedConfig } from '../../../lib/api';



interface BenchmarkSidebarProps {
  currentPage: 'bundle-selection' | 'model-selection';
}

interface AccordionTestData {
  id: string;
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
  get count(): string;
}

export default function BenchmarkSidebar({ currentPage }: BenchmarkSidebarProps) {
  const { bundles, loading, error } = useBundlesRedux();
  const selectedBundles = useSelectedBundles();
  const { setTest, toggleTest, setMultipleTests } = useTestSelectionActions();
  const testSelection = useAppSelector((state) => state.testSelection);
  const processedBundles = useRef<Set<string>>(new Set());
  const { configs: fixedConfigs } = useFixedConfigsRedux();

  // Auto-select all tests from selected bundles by default (only for new bundles)
  useEffect(() => {
    const currentBundleIds = new Set(selectedBundles.map(b => b.id));
    
    // Find new bundles that haven't been processed yet
    const newBundles = selectedBundles.filter(bundle => !processedBundles.current.has(bundle.id));
    
    if (newBundles.length > 0) {
      // For each new bundle, check if any tests are already selected
      // If tests are already selected, it means they were manually selected (e.g., from ViewBundleDetailsSheet)
      // and we should not auto-select all tests
      newBundles.forEach(bundle => {
        const bundleTestNames = bundle.tests.map(test => test.name);
        const alreadySelectedTests = bundleTestNames.filter(testName => testSelection[testName]);
        
        // Only auto-select all if no tests from this bundle are already selected
        if (alreadySelectedTests.length === 0 && bundleTestNames.length > 0) {
          setMultipleTests(bundleTestNames, true);
        }
        
        // Mark bundle as processed regardless
        processedBundles.current.add(bundle.id);
      });
    }
    
    // Remove bundles that are no longer selected and unselect their tests
    Array.from(processedBundles.current).forEach(bundleId => {
      if (!currentBundleIds.has(bundleId)) {
        // Find the bundle and unselect all its tests
        const deselectedBundle = bundles.find(b => b.id === bundleId);
        if (deselectedBundle) {
          const testNamesToUnselect = deselectedBundle.tests.map((test: { name: string }) => test.name);
          if (testNamesToUnselect.length > 0) {
            setMultipleTests(testNamesToUnselect, false);
          }
        }
        processedBundles.current.delete(bundleId);
      }
    });
  }, [selectedBundles, bundles, setMultipleTests]);

  const handleCheckChange = (testName: string) => {
    toggleTest(testName);
  };

  // Helper function to handle parent checkbox (select/deselect all)
  const handleParentCheckChange = (bundleId: string) => {
    const bundle = selectedBundles.find(b => b.id === bundleId);
    if (!bundle) return;

    const testNames = bundle.tests.map(test => test.name);
    const allChecked = testNames.every(testName => testSelection[testName]);
    const newCheckedState = !allChecked;

    setMultipleTests(testNames, newCheckedState);
  };

  const createTestAccordionItem = (data: AccordionTestData) => {
    const isChecked = testSelection[data.id] || false;
    
    // Find the matching fixed config if configId exists
    const matchingConfig = data.configId 
      ? fixedConfigs.find(config => config.id === data.configId)
      : undefined;
    
    return (
      <Card key={data.id} className="w-full mt-2 py-1 rounded-sm">
        <Accordion type="single" collapsible>
          <AccordionItem value={data.id} className="border-none">
            <div className="flex items-center px-4 py-1">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <Checkbox 
                    checked={isChecked}
                    onCheckedChange={() => handleCheckChange(data.id)}
                    className="rounded-sm"
                  />
                  <CardTitle className="text-sm font-medium">{data.title}</CardTitle>
                </div>
              </div>
            {/* Status indicators */}
            <div className="flex items-center gap-2">
              <CircleCheckBig className={`h-5 w-5 ${
                data.status === 'completed' 
                  ? 'text-green-500' 
                  : 'text-gray-300'
              }`} />
              <AccordionTrigger className="hover:no-underline p-0">
                <span className="sr-only">Toggle {data.title} details</span>
              </AccordionTrigger>
            </div>
          </div>
          <AccordionContent>
            <CardContent className="px-4 py-2">
              <div className="space-y-3">
                {/* Content for this accordion item can go here */}
                <div className="text-sm text-gray-600">
                  {matchingConfig && (
                    <Badge variant="outline" className="w-60 py-2 px-3 flex flex-col items-start">
                      <div>
                        <div className="font-bold mb-1">Endpoint Required:</div>
                        <div>{matchingConfig.name}</div>
                      </div>
                    </Badge>
                  )}
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
                  <Button variant="outline" size="sm">
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
    const bundle = selectedBundles.find(b => b.id === data.id);
    const testNames = bundle ? bundle.tests.map(test => test.name) : [];
    const allChecked = testNames.length > 0 && testNames.every(testName => testSelection[testName]);
    
    return (
      <AccordionItem key={data.id} value={data.id} className="border-none">
        <div className="flex items-center">
          <Badge variant="outline" className="flex items-center gap-2 px-3 py-2">
            <Checkbox 
              checked={allChecked}
              onCheckedChange={() => handleParentCheckChange(data.id)}
              className="rounded-sm"
            />
            <span className="font-medium text-sm">{data.title} {data.count}</span>
          </Badge>
        <Separator orientation="horizontal" className="flex-1 mx-2" />
        <AccordionTrigger className="hover:no-underline">
          <span className="sr-only">Toggle {data.title} section</span>
        </AccordionTrigger>
      </div>
      {/* px4 causes the tab for the accordion content*/}
      <AccordionContent className="px-4">
        <div>
          {data.items.map((item) => createTestAccordionItem(item))}
        </div>
      </AccordionContent>
    </AccordionItem>
    );
  };

  // Transform selected bundles into accordion data
  const parentAccordionData: BundleAccordionData[] = selectedBundles.map(bundle => ({
    id: bundle.id,
    title: bundle.name,
    items: bundle.tests.map(test => ({
      id: test.name,
      title: test.name,
      status: 'pending' as const, // Default status, could be enhanced later
      promptCount: test.dataset?.num_of_dataset_prompts ?? 0,
      metricName: test.metric?.name ?? 'N/A',
      description: test.description ?? '',
      configId: test.metric?.config_id
    })),
    get count() {
      const items_selected = this.items.filter(item => testSelection[item.id]);
      return `[${items_selected.length}/${this.items.length}]`;
    }
  }));

  // Calculate total test counts - updates when selectedBundles or testSelection changes
  const { totalTests, selectedTests } = useMemo(() => {
    // This sums the length of all the tests in all the bundles, acc is accumulator in reduce function
    const total = parentAccordionData.reduce((acc, bundle) => acc + bundle.items.length, 0);
    // This counts the number of tests that are selected
    const selected = Object.values(testSelection).filter(Boolean).length;
    return { totalTests: total, selectedTests: selected };
  }, [parentAccordionData, testSelection]);

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
        borderLeft: '1px solid #E2E8F0'
      }}
    >
      <div className="w-full max-w-md mx-auto px-4 py-2">
        <h2 className="text-lg font-semibold mb-2">Selected Tests [{selectedTests}/{totalTests}]</h2>
        <Separator className="mb-4" />
      </div>
      <div className="w-full max-w-md mx-auto p-1 flex-1 overflow-y-auto">
        {parentAccordionData.length > 0 ? (
          <Accordion type="multiple">
            {parentAccordionData.map((data) => createParentAccordion(data))}
          </Accordion>
        ) : (
          <div className="text-center text-gray-500 py-8">
            No bundles selected. Please select bundles to view their tests.
          </div>
        )}
      </div>
      {/* Sidebar content goes here */}
    </div>
  );
}
