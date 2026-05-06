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
  ApiError,
  createDatabaseModelConfig,
  fetchProviderLatestDetails,
  setLlmProviderApiKey,
  updateDatabaseModelConfig,
  type DatabaseModelConfigDTO,
  type LlmProviderDetailsDTO,
} from '../../../lib/api';
import { useAppDispatch, useAppSelector } from '../../../hooks/reduxHooks';
import { setEndpointStatus } from '../../../store';
import { ConnectionStatus } from './RequiredEndpointsCard';
import type { Provider, ModelConfig, ProviderListEntry } from '../types/modelSelection';

// Constants — backend `/api/providers` defaultConfigPairs are the source of truth for new models
const DEFAULT_ADVANCED_PARAMS: AdvancedParam[] = [];

const TEST_POPOVER_TIMEOUT = 3000;

const resolveLlmProviderModelIdForSave = (editingModel: string): number => {
  const i = editingModel.indexOf(':');
  if (i !== -1) return parseInt(editingModel.slice(0, i), 10);
  return parseInt(editingModel, 10);
};

const resolveExistingDatabaseConfigId = (
  editingDatabaseConfigId: string | null | undefined,
  currentModelConfig: ModelConfig | null | undefined
): number | null => {
  const raw = editingDatabaseConfigId ?? currentModelConfig?.modelConfigId;
  if (raw == null || String(raw).trim() === '') return null;
  const n = parseInt(String(raw), 10);
  return Number.isFinite(n) && n > 0 ? n : null;
};

interface AdvancedParam {
  parameter: string;
  value: string;
}

// Helper functions
const getProviderModelInfoFromProviders = (
  editingModel: string,
  providers: ProviderListEntry[],
  models: ModelConfig[],
  editingDatabaseConfigId?: string | null
) => {
  const isNewModel = providers.some((p) => p.id === editingModel);
  const currentModelConfig = isNewModel
    ? null
    : editingDatabaseConfigId != null &&
        String(editingDatabaseConfigId).trim() !== ""
      ? models.find(
          (m) =>
            m.modelConfigId != null &&
            String(m.modelConfigId) === String(editingDatabaseConfigId)
        ) ?? models.find((m) => m.id === editingModel)
      : models.find((m) => m.id === editingModel);
  const currentProvider = isNewModel
    ? providers.find((p) => p.id === editingModel)
    : providers.find((p) => p.id === currentModelConfig?.provider);

  return { isNewModel, currentModelConfig, currentProvider };
};

const resolveSystemName = (
  provider: Provider | ProviderListEntry | undefined
): string => {
  if (!provider) return '';
  return 'system_name' in provider
    ? (provider.system_name ?? provider.id)
    : provider.id;
};

const getAdvancedParamsFromProvider = (
  isNewModel: boolean,
  currentProvider: ProviderListEntry | undefined,
  savedConfigPairs?: Record<string, string>
): AdvancedParam[] => {
  if (!isNewModel && savedConfigPairs !== undefined) {
    return Object.entries(savedConfigPairs).map(([key, value]) => ({
      parameter: key,
      value: String(value),
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

const providerDefaultConfigPairCount = (
  currentProvider: ProviderListEntry | undefined
): number =>
  currentProvider && 'configPairs' in currentProvider
    ? currentProvider.configPairs.length
    : 0;

/** Resolve which database_model_configs row the sheet should load (handles multiple configs per model_id). */
function pickDatabaseModelConfigFromDetails(
  dbConfigs: DatabaseModelConfigDTO[] | undefined,
  explicitDatabaseConfigId: string | null | undefined,
  editingModel: string,
  currentModelConfig: ModelConfig | null | undefined,
  preferredConfigId: number | null
): DatabaseModelConfigDTO | undefined {
  const list = dbConfigs ?? [];
  if (
    explicitDatabaseConfigId != null &&
    String(explicitDatabaseConfigId).trim() !== ""
  ) {
    const byExplicit = list.find(
      (c) => String(c.id) === String(explicitDatabaseConfigId)
    );
    if (byExplicit) return byExplicit;
  }

  const mid = parseInt(editingModel, 10);
  if (!Number.isFinite(mid)) return undefined;

  if (preferredConfigId != null && preferredConfigId > 0) {
    const byPreferred = list.find(
      (c) =>
        parseInt(String(c.id), 10) === preferredConfigId &&
        Number(c.modelId) === mid
    );
    if (byPreferred) return byPreferred;
  }

  const mcid = currentModelConfig?.modelConfigId;
  if (mcid != null && String(mcid).trim() !== "") {
    const byStored = list.find((c) => String(c.id) === String(mcid));
    if (byStored && Number(byStored.modelId) === mid) return byStored;
  }

  const forModel = list.filter((c) => Number(c.modelId) === mid);
  if (forModel.length === 0) return undefined;
  if (forModel.length === 1) return forModel[0];

  const wantName = currentModelConfig?.name?.trim();
  if (wantName) {
    const byName = forModel.find((c) => (c.name ?? "").trim() === wantName);
    if (byName) return byName;
  }

  return forModel
    .slice()
    .sort((a, b) => {
      const tb = new Date(b.lastUpdated).getTime();
      const ta = new Date(a.lastUpdated).getTime();
      if (tb !== ta) return tb - ta;
      return parseInt(String(b.id), 10) - parseInt(String(a.id), 10);
    })[0];
}

interface EditModelSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editingModel: string;
  /** When set, load parameters for this llm_provider_model_config id (strongest disambiguator). */
  editingDatabaseConfigId?: string | null;
  providers: ProviderListEntry[];
  models: ModelConfig[];
  /**
   * When set, `Test` updates Redux endpoint status under this key instead of `editingModel`.
   * Used for required-endpoint rows (e.g. LLM AAJ provider rows).
   */
  endpointStatusKey?: string | null;
  onSaved?: () => void | Promise<void>;
}

export default function EditModelSheet({ 
  open, 
  onOpenChange, 
  editingModel, 
  editingDatabaseConfigId = null,
  providers, 
  models,
  endpointStatusKey = null,
  onSaved,
}: EditModelSheetProps) {
  const dispatch = useAppDispatch();
  const benchmarkLlmProviderModelId = useAppSelector(
    (s) => s.modelSelection.benchmarkLlmProviderModelId
  );
  const benchmarkLlmProviderModelConfigId = useAppSelector(
    (s) => s.modelSelection.benchmarkLlmProviderModelConfigId
  );
  const [saving, setSaving] = React.useState(false);
  
  // Get provider/model info using helper function with memoization
  const { isNewModel, currentModelConfig, currentProvider } = React.useMemo(() => {
    return getProviderModelInfoFromProviders(
      editingModel,
      providers,
      models,
      editingDatabaseConfigId
    );
  }, [editingModel, editingDatabaseConfigId, providers, models]);

  const [modelConfigName, setModelConfigName] = React.useState(isNewModel ? 'New Model' : currentModelConfig?.name || 'New Model');
  const [tokenValue, setTokenValue] = React.useState('');
  const [modelName, setModelName] = React.useState(isNewModel ? '' : currentModelConfig?.modelname || '');
  const [testResult, setTestResult] = React.useState<boolean | null>(null);
  const [popoverOpen, setPopoverOpen] = React.useState(false);
  const [advancedParams, setAdvancedParams] = React.useState(() =>
    getAdvancedParamsFromProvider(
      isNewModel,
      currentProvider,
      currentModelConfig?.savedConfigPairs
    )
  );
  const [apiKeyConfigured, setApiKeyConfigured] = React.useState(false);
  const timeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  // Update state when editingModel changes
  React.useEffect(() => {
    setModelConfigName(isNewModel ? 'New Model' : currentModelConfig?.name || 'New Model');
    setModelName(isNewModel ? '' : currentModelConfig?.modelname || '');
    setTokenValue('');
    setTestResult(null);
    setPopoverOpen(false);
    setAdvancedParams(
      getAdvancedParamsFromProvider(
        isNewModel,
        currentProvider,
        currentModelConfig?.savedConfigPairs
      )
    );
  }, [isNewModel, currentModelConfig, currentProvider, editingDatabaseConfigId]);

  React.useEffect(() => {
    if (open) {
      setTestResult(null);
    }
  }, [open]);

  React.useEffect(() => {
    if (!open) {
      setApiKeyConfigured(false);
      return;
    }
    if (!currentProvider) return;
    const systemName = resolveSystemName(currentProvider);
    if (!systemName.trim()) return;
    let cancelled = false;
    void (async () => {
      try {
        const details = await fetchProviderLatestDetails(systemName);
        if (cancelled) return;
        setApiKeyConfigured(Boolean(details.api_key_configured));

        if (isNewModel || !currentModelConfig) {
          return;
        }
        const mid = parseInt(editingModel, 10);
        const preferConfigId =
          Number.isFinite(mid) &&
          benchmarkLlmProviderModelId != null &&
          mid === benchmarkLlmProviderModelId
            ? benchmarkLlmProviderModelConfigId
            : null;
        const dbRow = pickDatabaseModelConfigFromDetails(
          details.database_model_configs,
          editingDatabaseConfigId,
          editingModel,
          currentModelConfig,
          preferConfigId
        );
        if (dbRow) {
          setAdvancedParams(
            Object.entries(dbRow.savedConfigPairs ?? {}).map(([parameter, value]) => ({
              parameter,
              value: String(value),
            }))
          );
        }
      } catch {
        if (!cancelled) setApiKeyConfigured(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [
    open,
    currentProvider,
    editingModel,
    isNewModel,
    currentModelConfig,
    benchmarkLlmProviderModelId,
    benchmarkLlmProviderModelConfigId,
    editingDatabaseConfigId,
  ]);

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
    setTokenValue('');
    setModelName('');
    setTestResult(null);
    setPopoverOpen(false);
    setAdvancedParams(
      getAdvancedParamsFromProvider(
        isNewModel,
        currentProvider,
        currentModelConfig?.savedConfigPairs
      )
    );
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
    const systemName = resolveSystemName(currentProvider);
    if (!systemName.trim()) {
      window.alert('Missing provider system name.');
      return;
    }
    setSaving(true);
    try {
      const details = await fetchProviderLatestDetails(systemName);
      const providerId = resolveProviderIdNumeric(details, currentProvider);
      const trimmedModel = modelName.trim();
      const keyConfigured = Boolean(details.api_key_configured);
      const trimmedToken = tokenValue.trim();
      if (!keyConfigured && !trimmedToken) {
        window.alert('Enter a token for this provider (no API key is stored yet).');
        return;
      }
      if (trimmedToken) {
        await setLlmProviderApiKey(providerId, trimmedToken);
      }

      const existingConfigId = resolveExistingDatabaseConfigId(
        editingDatabaseConfigId,
        currentModelConfig
      );

      if (!isNewModel && existingConfigId != null) {
        const baseModelId = resolveLlmProviderModelIdForSave(editingModel);
        let resolvedModelId = baseModelId;
        const modelMatch = details.models.find(
          (m) => (m.name ?? '').trim() === trimmedModel
        );
        if (modelMatch != null && Number.isFinite(modelMatch.id)) {
          resolvedModelId = modelMatch.id;
        }
        if (!Number.isFinite(resolvedModelId) || resolvedModelId <= 0) {
          window.alert('Invalid model reference for this configuration.');
          return;
        }
        await updateDatabaseModelConfig(existingConfigId, {
          model_id: resolvedModelId,
          name: modelConfigName.trim(),
          savedConfigPairs: buildSavedConfigPairs(),
        });
      } else {
        await createDatabaseModelConfig({
          llm_provider_id: providerId,
          model_name: trimmedModel,
          name: modelConfigName.trim(),
          savedConfigPairs: buildSavedConfigPairs(),
        });
      }
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
    setTestResult(true);

    const explicitKey =
      endpointStatusKey != null && String(endpointStatusKey).trim() !== ''
        ? String(endpointStatusKey)
        : '';
    const statusConfigId = explicitKey;
    if (statusConfigId) {
      dispatch(
        setEndpointStatus({
          configId: statusConfigId,
          status: ConnectionStatus.CONNECTED,
        })
      );
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
          <Input
            id="modelConfig"
            placeholder="Enter model configuration name"
            value={modelConfigName}
            onChange={(e) => setModelConfigName(e.target.value)}
            tabIndex={-1}
          />
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
                  <div className="text-sm px-3 py-2 rounded-md border text-gray-700 bg-gray-50">
                    {currentProvider?.name || 'No provider selected'}
                  </div>
                </div>

                {/* Token Section */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Label htmlFor="token" className="text-sm font-medium">
                      {apiKeyConfigured ? 'Token (optional)' : 'Token*'}
                    </Label>
                  </div>
                  <Input
                    id="token"
                    placeholder={
                      apiKeyConfigured && !tokenValue
                        ? '••••••••'
                        : 'Enter token'
                    }
                    type="password"
                    value={tokenValue}
                    onChange={(e) => setTokenValue(e.target.value)}
                    tabIndex={-1}
                  />
                  {apiKeyConfigured ? (
                    <p className="text-sm text-gray-600">
                      A key is already saved; leave blank to keep it, or enter a new one to replace it.
                    </p>
                  ) : null}
                </div>
              </CardContent>
            </Card>

            {/* Model Section */}
            <div className="space-y-2">
              <Label htmlFor="model" className="text-sm font-medium">
                Model*
              </Label>
              <Input
                id="model"
                placeholder={
                  currentProvider && 'defaultModel' in currentProvider
                    ? String(currentProvider.defaultModel || 'Enter model name')
                    : 'Enter model name'
                }
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                tabIndex={-1}
              />
            </div>

            {/* Configuration Notes */}
            <div className="space-y-2">
              <p className="text-sm text-gray-600">
                {currentProvider && 'modelTextboxExplanation' in currentProvider
                  ? String(currentProvider.modelTextboxExplanation ?? '')
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
                  <div className="w-16"></div>{/* Spacer for button column */}
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
                      {/* Only show delete button for rows beyond the default rows */}
                      {index >=
                        (isNewModel ? providerDefaultConfigPairCount(currentProvider) : 0) && (
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
                      Test_Placeholder
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
                  disabled={saving || testResult !== true}
                  className={
                    saving || testResult !== true
                      ? 'opacity-50 bg-gray-100 text-gray-400'
                      : ''
                  }
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
