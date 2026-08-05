"use client"
import React, { useEffect, useMemo, useState } from 'react';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetFooter } from "@/components/ui/sheet";
import { Info, FileTerminal, Square, CheckSquare } from 'lucide-react'
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useAppSelector, useAppDispatch } from '../../../hooks/reduxHooks';
import { toggleBundleSelected } from '../../../store';
import { useTestSelectionActions } from '../../../hooks/useTestSelection';
import { fetchProviders, type Bundle } from '@/lib/api';
import {
  collectAajProviderSystemNames,
  mapLlmProviderDtoToProvider,
  resolveAajProviderDisplayName,
} from '@/lib/aajProviderResolution';
import type { Provider } from '../types/modelSelection';
import { getTestSelectionKey, hasAnySelectedTestsInBundle, isTestSelected } from '@/lib/benchmarkTestSelection';

interface ViewBundleDetailsSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  bundle?: Bundle;
}

function CheckboxToggleButton({ checked, onCheckedChange, ...props }: { checked: boolean; onCheckedChange: (checked: boolean) => void; [key: string]: unknown }) {
  return (
    <Button
      variant={checked ? "default" : "outline"}
      onClick={() => onCheckedChange(!checked)}
      className="gap-2 w-[110px] justify-start"
      {...props}
    >
      <div className="flex items-center">
        {checked ? <CheckSquare className="h-4 w-4" /> : <Square className="h-4 w-4" />}
      </div>
      <div className="flex items-center">
        {checked ? "Selected" : "Select"}
      </div>
    </Button>
  );
}

/**
 * Component that displays the details of a test in the bundle
 */
function sanitizeTestId(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

function TestDetailCard({
  test,
  isSelected,
  onSelectionChange
}: {
  test: {
    name: string;
    description?: string;
    dataset: {
      id: string;
      name: string;
      description: string;
      num_of_dataset_prompts: number;
    };
  };
  isSelected: boolean;
  onSelectionChange: (selected: boolean) => void;
}) {
  const testSlug = sanitizeTestId(test.name);

  return (
    <Card className="w-[320px] pt-3 pb-2" data-testid={`test-detail-card-${testSlug}`}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <FileTerminal className="h-4 w-4 text-slate-600 flex-shrink-0" />
          <CardTitle className="text-base font-semibold" data-testid="test-detail-card-name">{test.name}</CardTitle>
        </div>
        {test.description && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <CardDescription className="text-sm text-gray-600 mt-0 line-clamp-3 cursor-help">
                  {test.description}
                </CardDescription>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="max-w-xs">{test.description}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex flex-col gap-1">
            <span className="text-sm text-gray-500">Prompts</span>
            <span className="text-sm font-semibold text-gray-900">{test.dataset.num_of_dataset_prompts || 0}</span>
          </div>
        </div>
      </CardContent>
      <CardFooter className="pt-1 pb-2 mt-auto flex items-center justify-between gap-2">
        <CheckboxToggleButton
          checked={isSelected}
          onCheckedChange={onSelectionChange}
          aria-label="Toggle test"
          size="sm"
        />
        <Button
          variant="outline"
          size="sm"
          className="w-[110px] justify-center"
          data-testid={`test-learn-more-${testSlug}`}
          onClick={() => {
            const testName = encodeURIComponent(test.name);
            const datasetId = encodeURIComponent(test.dataset.id);
            window.open(`/view_test?test=${testName}&dataset=${datasetId}`, '_blank');
          }}
        >
          Learn More
        </Button>
      </CardFooter>
    </Card>
  );
}

export default function ViewBundleDetailsSheet({ 
  open, 
  onOpenChange,
  bundle 
}: ViewBundleDetailsSheetProps) {
  const dispatch = useAppDispatch();
  const bundleSelection = useAppSelector((state) => state.bundleSelection);
  const testSelection = useAppSelector((state) => state.testSelection);
  const { setTest } = useTestSelectionActions();
  const [apiProviders, setApiProviders] = useState<Provider[]>([]);
  const [draftSelection, setDraftSelection] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!open) {
      setDraftSelection({});
      return;
    }
    if (!bundle) {
      setDraftSelection({});
      return;
    }
    const next: Record<string, boolean> = {};
    for (const test of bundle.tests) {
      const key = getTestSelectionKey(test);
      next[key] = isTestSelected(testSelection, bundle.id, test);
    }
    setDraftSelection(next);
    // Seed only when the sheet opens (or the bundle changes), not when global selection updates.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: capture selection at open time
  }, [open, bundle]);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    void (async () => {
      try {
        const dtos = await fetchProviders();
        if (!cancelled) {
          setApiProviders(dtos.map(mapLlmProviderDtoToProvider));
        }
      } catch {
        if (!cancelled) {
          setApiProviders([]);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open]);

  const requiredProviderSystemNames = useMemo(
    () => collectAajProviderSystemNames(bundle?.tests),
    [bundle?.tests]
  );

  const selectedCount = bundle
    ? bundle.tests.filter((test) => Boolean(draftSelection[getTestSelectionKey(test)])).length
    : 0;

  const canCommit =
    selectedCount > 0 ||
    Boolean(bundle && hasAnySelectedTestsInBundle(testSelection, bundle.id));

  const handleDraftSelectionChange = (testKey: string, selected: boolean) => {
    setDraftSelection((prev) => ({ ...prev, [testKey]: selected }));
  };

  const handleAddTests = () => {
    if (!bundle || !canCommit) return;

    for (const test of bundle.tests) {
      const key = getTestSelectionKey(test);
      setTest(bundle.id, test, Boolean(draftSelection[key]));
    }

    if (selectedCount > 0 && !bundleSelection[bundle.id]) {
      dispatch(toggleBundleSelected(bundle.id));
    }

    onOpenChange(false);
  };

  const buttonText = selectedCount > 1 
    ? `Add ${selectedCount} tests` 
    : selectedCount === 1 
    ? "Add 1 test"
    : "Add tests";

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-[1100px] sm:max-w-[1100px] ml-4 overflow-y-auto pl-6 pr-6"
        data-testid="bundle-details-sheet"
      >
        <SheetHeader className="p-2">
          <SheetTitle className="text-lg text-slate-500 pt-1 pb-0">Bundle</SheetTitle>
          <SheetDescription className="sr-only">
            Details for the selected benchmark bundle.
          </SheetDescription>
        </SheetHeader>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold" data-testid="bundle-details-name">{bundle?.name}</h1>
          <Badge className="bg-white border border-slate-200 flex gap-1 items-center justify-center px-1 py-1 rounded-md" data-name="State" data-node-id="I692:28780;520:20724">
            <span className="text-sm text-gray-600">{bundle?.category}</span>
          </Badge>
        </div>
        <p className="text-gray-600" data-testid="bundle-details-description">{bundle?.description || 'Bundle Description'}</p>
        <div className="flex items-center gap-5 mb-0">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Prompts</span>
            <span className="text-sm font-semibold" data-testid="bundle-details-prompt-count">{bundle?.prompt_count || 0}</span>
          </div>
          <Separator orientation="vertical" className="h-6" />
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Tests</span>
            <span className="text-sm font-semibold" data-testid="bundle-details-test-count">{bundle?.tests?.length || 0}</span>
          </div>
        </div>
        {requiredProviderSystemNames.length > 0 ? (
          <div
            className="w-full mt-0 p-4 bg-slate-50 border border-slate-200 rounded-md flex flex-col gap-2"
            data-testid="required-endpoint-connectors"
          >
            <div className="flex items-center gap-2">
              <Info className="h-4 w-4 text-slate-600 flex-shrink-0" />
              <span className="text-sm font-medium text-slate-700">Required Connectors for LLM-as-judge Models</span>
            </div>
            <ul className="text-sm text-slate-700 pl-6 list-disc space-y-1">
              {requiredProviderSystemNames.map((systemName) => (
                <li key={systemName}>
                  {resolveAajProviderDisplayName(systemName, apiProviders)}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        <div>
          <h3 className="text-base text-gray-900 font-semibold pt-0 pb-0">Tests ({bundle?.tests?.length || 0})</h3>
        </div>
        <Separator orientation="horizontal" />
        <div className="mt-4 grid grid-cols-3 gap-4">
          {bundle?.tests && bundle.tests.length > 0 ? (
            bundle.tests.map((test) => {
              const testKey = getTestSelectionKey(test);
              return (
                <TestDetailCard
                  key={test.name}
                  test={test}
                  isSelected={Boolean(draftSelection[testKey])}
                  onSelectionChange={(selected) => handleDraftSelectionChange(testKey, selected)}
                />
              );
            })
          ) : (
            <div className="text-sm text-gray-500 py-4">No tests available in this bundle.</div>
          )}
        </div>
        <SheetFooter className="flex flex-row justify-between mt-auto">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button disabled={!canCommit} onClick={handleAddTests}>
            {buttonText}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}

