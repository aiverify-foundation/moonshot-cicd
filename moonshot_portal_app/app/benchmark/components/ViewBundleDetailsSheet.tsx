"use client"
import React from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetClose, SheetFooter } from "@/components/ui/sheet";
import { PanelRightClose, Info, FileTerminal, Database, Square, CheckSquare } from 'lucide-react'
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

interface Bundle {
  name: string;
  description: string;
  category: string;
  tests: Array<{
    name: string;
    description?: string;
    dataset: {
      id: string;
      name: string;
      description: string;
      num_of_dataset_prompts: number;
    };
  }>;
  prompt_count?: number;
}

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
function TestDetailCard({
  test,
  index,
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
  index: number;
  isSelected: boolean;
  onSelectionChange: (selected: boolean) => void;
}) {

  return (
    <Card className="w-[320px] pt-3 pb-2">
      <CardHeader>
        <div className="flex items-center gap-2">
          <FileTerminal className="h-4 w-4 text-slate-600 flex-shrink-0" />
          <CardTitle className="text-base font-semibold">{test.name}</CardTitle>
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
          variant="ghost" 
          size="sm" 
          className="text-sm"
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
  const [selectedTests, setSelectedTests] = React.useState<Set<number>>(new Set());
  const dispatch = useAppDispatch();
  const bundleSelection = useAppSelector((state) => state.bundleSelection);
  const { setMultipleTests, toggleTest } = useTestSelectionActions();

  const handleTestSelectionChange = (index: number, selected: boolean) => {
    setSelectedTests(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(index);
      } else {
        newSet.delete(index);
      }
      return newSet;
    });
  };

  const handleAddTests = () => {
    if (!bundle || selectedTests.size === 0) return;

    // Get test names from selected indices
    const selectedTestNames = Array.from(selectedTests)
      .map(index => bundle.tests[index]?.name)
      .filter((name): name is string => Boolean(name));

    if (selectedTestNames.length === 0) return;

    // First, set the specific tests as selected before toggling the bundle
    // This ensures the tests are selected before the sidebar's auto-select logic runs
    setMultipleTests(selectedTestNames, true);

    // Then ensure the bundle is selected (only toggle if not already selected)
    // The sidebar will detect that tests are already selected and won't auto-select all
    const isBundleSelected = Boolean(bundleSelection[bundle.name]);
    if (!isBundleSelected) {
      dispatch(toggleBundleSelected(bundle.name));
    }

    // Clear the local selection state and close the sheet
    setSelectedTests(new Set());
    onOpenChange(false);
  };

  const selectedCount = selectedTests.size;
  const buttonText = selectedCount > 1 
    ? `Add ${selectedCount} tests` 
    : selectedCount === 1 
    ? "Add 1 test"
    : "Add tests";

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[1100px] sm:max-w-[1100px] ml-4 overflow-y-auto pl-6 pr-6">
        <SheetHeader className="p-2">
          <SheetTitle className="text-lg text-slate-500 pt-1 pb-0">Bundle</SheetTitle>
        </SheetHeader>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold">{bundle?.name}</h1>
          <Badge className="bg-white border border-slate-200 flex gap-1 items-center justify-center px-1 py-1 rounded-md" data-name="State" data-node-id="I692:28780;520:20724">
            <span className="text-sm text-gray-600">{bundle?.category}</span>
          </Badge>
        </div>
        <p className="text-gray-600">{bundle?.description || 'Bundle Description'}</p>
        <div className="flex items-center gap-5 mb-0">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Prompts</span>
            <span className="text-sm font-semibold">{bundle?.prompt_count || 0}</span>
          </div>
          <Separator orientation="vertical" className="h-6" />
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Tests</span>
            <span className="text-sm font-semibold">{bundle?.tests?.length || 0}</span>
          </div>
        </div>
        <div className="w-full mt-0 p-4 bg-slate-50 border border-slate-200 rounded-md flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <Info className="h-4 w-4 text-slate-600 flex-shrink-0" />
            <span className="text-sm font-medium text-slate-700">Required Endpoint Connectors</span>
          </div>
          <p className="text-sm text-slate-700 pl-6">Llama-Guard-2-8B</p>
        </div>
        <div>
          <h3 className="text-base text-gray-900 font-semibold pt-0 pb-0">Tests ({bundle?.tests?.length || 0})</h3>
        </div>
        <Separator orientation="horizontal" />
        <div className="mt-4 grid grid-cols-3 gap-4">
          {bundle?.tests && bundle.tests.length > 0 ? (
            bundle.tests.map((test, index) => (
              <TestDetailCard 
                key={`test-${index}`} 
                test={test} 
                index={index}
                isSelected={selectedTests.has(index)}
                onSelectionChange={(selected) => handleTestSelectionChange(index, selected)}
              />
            ))
          ) : (
            <div className="text-sm text-gray-500 py-4">No tests available in this bundle.</div>
          )}
        </div>
        <SheetFooter className="flex flex-row justify-between mt-auto">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button disabled={selectedCount < 1} onClick={handleAddTests}>
            {buttonText}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}

