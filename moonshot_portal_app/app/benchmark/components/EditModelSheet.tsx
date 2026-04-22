"use client"
import React from 'react';
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Card, CardContent } from '@/components/ui/card';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Trash2, Plus } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  FixedConfig,
  ApiError,
  createDatabaseModelConfig,
  fetchProviderLatestDetails,
  setLlmProviderApiKey,
  type LlmProviderDetailsDTO,
} from '../../../lib/api';
import { useAppDispatch } from '../../../hooks/reduxHooks';
import { setEndpointStatus } from '../../../store';
import { ConnectionStatus } from './RequiredEndpointsCard';
import type { Provider, ModelConfig, ProviderListEntry } from '../types/modelSelection';

// Constants
const DEFAULT_ADVANCED_PARAMS = [
  { parameter: 'temperature', value: '30' },
  { parameter: 'timeout', value: '0' }
];

const TEST_POPOVER_TIMEOUT = 3000;

interface AdvancedParam {
  parameter: string;
  value: string;
}

// Helper functions
const getProviderModelInfoFromFixedConfig = (editingModel: string, fixedConfigs: FixedConfig[]) => {
  const fixedConfig = fixedConfigs.find(c => c.id === editingModel);
  if (!fixedConfig) {
    return null;
  }
  
  //TODO: Get a real reference to a provider from providers
  // Create a new provider with only the name filled as fixedConfig.providerID
  const currentProvider: Provider = {
    id: fixedConfig.providerID,
    name: fixedConfig.providerID,
    type: 'provider',
    system_name: fixedConfig.providerID,
    defaultModel: '',
    modelTextboxExplanation: '',
    configPairs: [],
    modelToken: '',
  };
  
  // Create a mock model config from fixedConfig
  const currentModelConfig = {
    id: fixedConfig.id,
    name: fixedConfig.name,
    modelname: fixedConfig.modelname,
    provider: fixedConfig.providerID
  };
  
  return { isNewModel: false, currentModelConfig, currentProvider, fixedConfig };
};

const getProviderModelInfoFromProviders = (
  editingModel: string,
  providers: ProviderListEntry[],
  models: ModelConfig[]
) => {
  const isNewModel = providers.some(p => p.id === editingModel);
  const currentModelConfig = isNewModel ? null : models.find(m => m.id === editingModel);
  const currentProvider = isNewModel 
    ? providers.find(p => p.id === editingModel)
    : providers.find(p => p.id === currentModelConfig?.provider);
  
  return { isNewModel, currentModelConfig, currentProvider, fixedConfig: undefined };
};

const getAdvancedParamsFromProvider = (
  currentProvider: ProviderListEntry | undefined,
  fixedConfig?: FixedConfig
): AdvancedParam[] => {
  // If fixed config is provided, use its savedConfigPairs
  if (fixedConfig?.savedConfigPairs) {
    return Object.entries(fixedConfig.savedConfigPairs).map(([key, value]) => ({
      parameter: key,
      value: value
    }));
  }
  
  if (
    currentProvider &&
    'configPairs' in currentProvider &&
    currentProvider.configPairs.length > 0
  ) {
    return currentProvider.configPairs.map((cp) => ({
      parameter: cp.key,
      value: cp.value
    }));
  }
  return DEFAULT_ADVANCED_PARAMS;
};

interface EditModelSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editingModel: string;
  providers: ProviderListEntry[];
  models: ModelConfig[];
  isMetricEndpoint?: boolean;
  fixedConfigs?: FixedConfig[];
  onSaved?: () => void | Promise<void>;
}

export default function EditModelSheet({ 
  open, 
  onOpenChange, 
  editingModel, 
  providers, 
  models,
  isMetricEndpoint = false,
  fixedConfigs,
  onSaved,
}: EditModelSheetProps) {
  const dispatch = useAppDispatch();
  const [saving, setSaving] = React.useState(false);
  
  // Get provider/model info using helper function with memoization
  const { isNewModel, currentModelConfig, currentProvider, fixedConfig } = React.useMemo(() => {
    if (isMetricEndpoint && fixedConfigs) {
      // If fixed config is found, use it, otherwise use providers which has default behaviour
      return getProviderModelInfoFromFixedConfig(editingModel, fixedConfigs) || 
             getProviderModelInfoFromProviders(editingModel, providers, models);
    }
    return getProviderModelInfoFromProviders(editingModel, providers, models);
  }, [editingModel, providers, models, isMetricEndpoint, fixedConfigs]);

  const [modelConfigName, setModelConfigName] = React.useState(isNewModel ? 'New Model' : currentModelConfig?.name || 'New Model');
  const [tokenValue, setTokenValue] = React.useState('');
  const [modelName, setModelName] = React.useState(isNewModel ? '' : currentModelConfig?.modelname || '');
  const [testResult, setTestResult] = React.useState<boolean | null>(null);
  const [popoverOpen, setPopoverOpen] = React.useState(false);
  const [advancedParams, setAdvancedParams] = React.useState(getAdvancedParamsFromProvider(currentProvider, fixedConfig));
  const timeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  // Update state when editingModel changes
  React.useEffect(() => {
    setModelConfigName(isNewModel ? 'New Model' : currentModelConfig?.name || 'New Model');
    setModelName(isNewModel ? '' : currentModelConfig?.modelname || '');
    setTokenValue(
      currentProvider && 'modelToken' in currentProvider
        ? currentProvider.modelToken || ''
        : ''
    );
    setTestResult(null);
    setPopoverOpen(false);
    setAdvancedParams(getAdvancedParamsFromProvider(currentProvider, fixedConfig));
  }, [isNewModel, currentModelConfig, currentProvider, fixedConfig]);

  // Cleanup timeout on unmount
  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const resetForm = () => {
    setModelConfigName('New Model');
    setTokenValue(
      currentProvider && 'modelToken' in currentProvider
        ? currentProvider.modelToken || ''
        : ''
    );
    setModelName('');
    setTestResult(null);
    setPopoverOpen(false);
    setAdvancedParams(getAdvancedParamsFromProvider(currentProvider, fixedConfig));
  };

  const buildSavedConfigPairs = (): Record<string, string> => {
    const out: Record<string, string> = {};
    for (const row of advancedParams) {
      const k = row.parameter.trim();
      if (k) out[k] = row.value;
    }
    return out;
  };

  const resolveProviderIdNumeric = (
    details: LlmProviderDetailsDTO,
    provider: ProviderListEntry
  ): number => {
    if (/^\d+$/.test(provider.id)) {
      return parseInt(provider.id, 10);
    }
    return parseInt(details.provider.id, 10);
  };

  const handleSave = async () => {
    if (testResult !== true) return;
    if (!currentProvider) {
      window.alert('No provider context for this configuration.');
      return;
    }
    if (!modelName.trim()) {
      window.alert('Enter a model name.');
      return;
    }
    const systemName =
      'system_name' in currentProvider
        ? (currentProvider.system_name ?? currentProvider.id)
        : currentProvider.id;
    if (!systemName.trim()) {
      window.alert('Missing provider system name.');
      return;
    }
    setSaving(true);
    try {
      const details = await fetchProviderLatestDetails(systemName);
      const providerId = resolveProviderIdNumeric(details, currentProvider);
      const trimmedModel = modelName.trim();
      await setLlmProviderApiKey(providerId, tokenValue.trim());
      await createDatabaseModelConfig({
        llm_provider_id: providerId,
        model_name: trimmedModel,
        name: modelConfigName.trim(),
        savedConfigPairs: buildSavedConfigPairs(),
      });
      await onSaved?.();
      resetForm();
      onOpenChange(false);
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? e.message
          : e instanceof Error
            ? e.message
            : 'Save failed';
      window.alert(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleTest = () => {
    const testPassed = Boolean(tokenValue.trim() && modelName.trim());
    setTestResult(testPassed);
    
    // Update endpoint status in Redux store if this is a metric endpoint
    if (isMetricEndpoint && editingModel) {
      const status = testPassed 
        ? ConnectionStatus.CONNECTED 
        : ConnectionStatus.INVALID_TOKEN;
      dispatch(setEndpointStatus({ configId: editingModel, status }));
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
          <SheetTitle className="sr-only">Edit Model Configuration</SheetTitle>
        </SheetHeader>
        
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold">Edit Model Configuration</h2>
        </div>
        
        <div className="space-y-2 mb-6">
          <Label htmlFor="modelConfig" className="text-sm font-medium">
            Model Configuration Name*
          </Label>
          {isMetricEndpoint ? (
            <div className="text-sm text-gray-700 bg-gray-50 px-3 py-2 rounded-md border">
              {modelConfigName}
            </div>
          ) : (
            <Input
              id="modelConfig"
              placeholder="Enter model configuration name"
              value={modelConfigName}
              onChange={(e) => setModelConfigName(e.target.value)}
              tabIndex={-1}
            />
          )}
        </div>

        <div className="flex flex-col h-full">
          <div className="flex-1 space-y-6 pb-6">
            {/* Model Provider and Token Card */}
            <Card className="py-0 gap-0">
              <CardContent className="p-4 space-y-4">
                {/* Model Provider Section */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium">
                    Model Provider*
                  </Label>
                  <div className={`text-sm px-3 py-2 rounded-md border ${isMetricEndpoint ? 'text-gray-700 bg-gray-50' : 'text-gray-700 bg-gray-50'}`}>
                    {currentProvider?.name || 'No provider selected'}
                  </div>
                </div>

                {/* Token Section */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Label htmlFor="token" className="text-sm font-medium">
                      Token*
                    </Label>
                  </div>
                  <Input
                    id="token"
                    placeholder="Enter token"
                    type="password"
                    value={tokenValue}
                    onChange={(e) => setTokenValue(e.target.value)}
                    tabIndex={-1}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Model Section */}
            <div className="space-y-2">
              <Label htmlFor="model" className="text-sm font-medium">
                Model*
              </Label>
              {isMetricEndpoint ? (
                <div className="text-sm text-gray-700 bg-gray-50 px-3 py-2 rounded-md border">
                  {modelName ||
                    (currentProvider && 'defaultModel' in currentProvider
                      ? currentProvider.defaultModel
                      : '') ||
                    'No model selected'}
                </div>
              ) : (
                <Input
                  id="model"
                  placeholder={
                    currentProvider && 'defaultModel' in currentProvider
                      ? currentProvider.defaultModel || 'Enter model name'
                      : 'Enter model name'
                  }
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  tabIndex={-1}
                />
              )}
            </div>

            {/* Configuration Notes */}
            <div className="space-y-2">
              <p className="text-sm text-gray-600">
                {currentProvider && 'modelTextboxExplanation' in currentProvider
                  ? currentProvider.modelTextboxExplanation
                  : ''}
              </p>
            </div>

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
                  {!isMetricEndpoint && <div className="w-16"></div>} {/* Spacer for button column */}
                </div>
                
                {/* Parameter rows */}
                {advancedParams.map((param: AdvancedParam, index: number) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="flex-1">
                      {isMetricEndpoint ? (
                        <div className="text-sm text-gray-700 bg-gray-50 px-3 py-2 rounded-md border">
                          {param.parameter}
                        </div>
                      ) : (
                        <Input
                          value={param.parameter}
                          onChange={(e) => updateParameter(index, 'parameter', e.target.value)}
                          tabIndex={-1}
                        />
                      )}
                    </div>
                    <div className="flex-1">
                      {isMetricEndpoint ? (
                        <div className="text-sm text-gray-700 bg-gray-50 px-3 py-2 rounded-md border">
                          {param.value}
                        </div>
                      ) : (
                        <Input
                          value={param.value}
                          onChange={(e) => updateParameter(index, 'value', e.target.value)}
                          tabIndex={-1}
                        />
                      )}
                    </div>
                    {!isMetricEndpoint && (
                      <div className="flex items-center gap-1 w-16">
                        {/* Only show delete button for rows beyond the default rows */}
                        {index >=
                          (currentProvider && 'configPairs' in currentProvider
                            ? currentProvider.configPairs.length
                            : 0) && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeParameter(index)}
                            className="h-8 w-8 p-0"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
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
                    )}
                  </div>
                ))}
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
                  onClick={() => void handleSave()} 
                  disabled={testResult !== true || saving}
                  className={testResult !== true || saving ? "opacity-50 bg-gray-100 text-gray-400" : ""}
                >
                  {saving ? 'Saving…' : 'Save'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
