"use client"
import React from 'react';
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Card, CardContent } from '@/components/ui/card';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Trash2, Plus } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { ModelApp, Config } from "../types/modelSelection";

// Constants
const TEST_POPOVER_TIMEOUT = 3000;

interface AdvancedParam {
  parameter: string;
  value: string;
}

// Helper functions
const getModelAppConfigInfo = (editingConfig: string, modelApps: ModelApp[], configs: Config[]) => {
  const isNewConfig = modelApps.some(p => p.id === editingConfig);
  const currentConfig = isNewConfig ? null : configs.find(m => m.id === editingConfig);
  const currentModelApp = isNewConfig 
    ? modelApps.find(p => p.id === editingConfig)
    : modelApps.find(p => p.id === currentConfig?.connector);
  
  return { isNewConfig, currentConfig, currentModelApp };
};

const getAdvancedParamsFromConfig = (currentConfig: Config | null | undefined): AdvancedParam[] => {
  if (currentConfig?.configPairs && currentConfig.configPairs.length > 0) {
    return currentConfig.configPairs.map((cp) => ({
      parameter: cp.key,
      value: cp.value
    }));
  }
  return [];
};

interface EditCustomApplicationSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editingConfig: string;
  modelApps: ModelApp[];
  configs: Config[];
}

export default function EditCustomApplicationSheet({ 
  open, 
  onOpenChange, 
  editingConfig, 
  modelApps, 
  configs 
}: EditCustomApplicationSheetProps) {
  // Get modelApp/config info using helper function with memoization
  const { isNewConfig, currentConfig, currentModelApp } = React.useMemo(
    () => getModelAppConfigInfo(editingConfig, modelApps, configs),
    [editingConfig, modelApps, configs]
  );

  const [configName, setConfigName] = React.useState(isNewConfig ? 'New Configuration' : currentConfig?.name || 'New Configuration');
  const [testResult, setTestResult] = React.useState<boolean | null>(null);
  const [popoverOpen, setPopoverOpen] = React.useState(false);
  const [advancedParams, setAdvancedParams] = React.useState(() => {
    return getAdvancedParamsFromConfig(currentConfig);
  });
  const timeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  // Update state when editingConfig changes
  React.useEffect(() => {
    setConfigName(isNewConfig ? 'New Configuration' : currentConfig?.name || 'New Configuration');
    setTestResult(null);
    setPopoverOpen(false);
    setAdvancedParams(getAdvancedParamsFromConfig(currentConfig));
  }, [isNewConfig, currentConfig, currentModelApp]);

  // Cleanup timeout on unmount
  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const resetForm = () => {
    setConfigName('New Configuration');
    setTestResult(null);
    setPopoverOpen(false);
    setAdvancedParams(getAdvancedParamsFromConfig(currentConfig));
  };

  const handleSave = () => {
    // Add your save logic here
    console.log('Saving custom application configuration for:', editingConfig);
    resetForm();
    onOpenChange(false);
  };

  const handleTest = () => {
    if (configName.trim()) {
      setTestResult(true);
    } else {
      setTestResult(false);
    }
    
    // Show popover on click
    setPopoverOpen(true);
    
    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    // Clear the test result and close popover after 3 seconds
    timeoutRef.current = setTimeout(() => {
      setPopoverOpen(false);
    }, TEST_POPOVER_TIMEOUT);
  };

  const addParameter = () => {
    setAdvancedParams([...advancedParams, { parameter: '', value: '' }]);
  };

  const removeParameter = (index: number) => {
    setAdvancedParams(advancedParams.filter((_: AdvancedParam, i: number) => i !== index));
  };

  const updateParameter = (index: number, field: 'parameter' | 'value', value: string) => {
    const updated = [...advancedParams];
    updated[index][field] = value;
    setAdvancedParams(updated);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[1400px] sm:max-w-[700px] ml-4 overflow-y-auto pl-6 pr-6">
        <SheetHeader>
          <SheetTitle className="sr-only">Edit Custom Application Configuration</SheetTitle>
        </SheetHeader>
        
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold">Edit Custom Application Configuration</h2>
        </div>
        
        <div className="space-y-2 mb-6">
          <Label htmlFor="configName" className="text-sm font-medium">
            Configuration Name*
          </Label>
          <Input
            id="configName"
            placeholder="Enter configuration name"
            value={configName}
            onChange={(e) => setConfigName(e.target.value)}
            tabIndex={-1}
          />
        </div>

        <div className="flex flex-col h-full">
          <div className="flex-1 space-y-6 pb-6">
            {/* Advanced Parameters Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Advanced Parameters</h3>
              </div>
              
              <div className="space-y-3">
                {/* Header row with labels */}
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <Label className="text-sm font-medium text-gray-600">Parameter</Label>
                  </div>
                  <div className="flex-1">
                    <Label className="text-sm font-medium text-gray-600">Value</Label>
                  </div>
                  <div className="w-16"></div> {/* Spacer for button column */}
                </div>
                
                {/* Parameter rows */}
                {advancedParams.map((param: AdvancedParam, index: number) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="flex-1">
                      <Input
                        value={param.parameter}
                        onChange={(e) => updateParameter(index, 'parameter', e.target.value)}
                        tabIndex={-1}
                      />
                    </div>
                    <div className="flex-1">
                      <Input
                        value={param.value}
                        onChange={(e) => updateParameter(index, 'value', e.target.value)}
                        tabIndex={-1}
                      />
                    </div>
                    <div className="flex items-center gap-1 w-16">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeParameter(index)}
                        className="h-8 w-8 p-0"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                      {/* Add button only on the last row */}
                      {index === advancedParams.length - 1 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={addParameter}
                          className="h-8 w-8 p-0"
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
                
                {/* Show add button when there are no parameters */}
                {advancedParams.length === 0 && (
                  <div className="flex items-center gap-3">
                    <div className="flex-1"></div>
                    <div className="flex-1"></div>
                    <div className="flex items-center gap-1 w-16">
                      <div className="h-8 w-8"></div> {/* Spacer for delete button */}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={addParameter}
                        className="h-8 w-8 p-0"
                      >
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Action Buttons - Fixed at bottom */}
          <div className="mt-auto pt-6 pb-6 border-t">
            <div className="flex justify-between items-center">
              <Button variant="outline" onClick={() => {
                resetForm();
                onOpenChange(false);
              }}>
                Back
              </Button>
              <div className="flex gap-3">
                <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
                  <PopoverTrigger asChild>
                    <Button variant="outline" onClick={handleTest}>
                      Test
                    </Button>
                  </PopoverTrigger>
                  {testResult !== null && (
                    <PopoverContent className="bg-background border-2 border-gray-300 text-foreground shadow-lg w-auto max-w-fit p-2">
                      <p className={testResult ? 'text-green-600' : 'text-red-600'}>
                        {testResult ? 'Test Passed' : 'Test Failed'}
                      </p>
                    </PopoverContent>
                  )}
                </Popover>
                <Button 
                  onClick={handleSave} 
                  disabled={testResult !== true}
                  className={testResult !== true ? "opacity-50 bg-gray-100 text-gray-400" : ""}
                >
                  Save
                </Button>
              </div>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
