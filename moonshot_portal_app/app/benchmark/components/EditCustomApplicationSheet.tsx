"use client"
import React from 'react';
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Card, CardContent } from '@/components/ui/card';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Trash2, Plus } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { ModelApp, Config } from "../types/modelSelection";
import {
  ApiError,
  createCustomAppConfig,
  updateCustomAppConfig,
  setCustomAppConfigSecret,
  type CustomAppConfigDTO,
} from "@/lib/api";
import {
  RESERVED_CONFIG_KEYS,
  DEFAULT_CUSTOM_API_TYPE,
  DEFAULT_CUSTOM_API_URL,
  DEFAULT_CUSTOM_API_BODY,
  DEFAULT_CONNECTOR_ADAPTER,
  PARAMETERS_CONFIG_KEY,
  HEADERS_CONFIG_KEY,
  decodeCustomAppProviderId,
  serializeParametersJson,
  serializeHeadersJson,
} from "../constants/customAppConfig";

const TEST_POPOVER_TIMEOUT = 3000;
const AUTOSAVE_DEBOUNCE_MS = 500;
const API_TYPE_OPTIONS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'] as const;

type AutosaveStatus = 'idle' | 'saving' | 'saved' | 'error';

interface ParameterRow {
  parameter: string;
  value: string;
}

interface HeaderRow {
  header: string;
  value: string;
}

const getModelAppConfigInfo = (editingConfig: string, modelApps: ModelApp[], configs: Config[]) => {
  const isNewConfig = modelApps.some(p => p.id === editingConfig);
  const currentConfig = isNewConfig ? null : configs.find(m => m.id === editingConfig);
  const currentModelApp = isNewConfig
    ? modelApps.find(p => p.id === editingConfig)
    : modelApps.find(p => p.id === currentConfig?.connector);

  return { isNewConfig, currentConfig, currentModelApp };
};

const getParameterRowsFromConfig = (currentConfig: Config | null | undefined): ParameterRow[] => {
  if (currentConfig?.configPairs && currentConfig.configPairs.length > 0) {
    return currentConfig.configPairs.map((cp) => ({
      parameter: cp.key,
      value: cp.value,
    }));
  }
  return [];
};

const getHeaderRowsFromConfig = (currentConfig: Config | null | undefined): HeaderRow[] => {
  if (currentConfig?.headerPairs && currentConfig.headerPairs.length > 0) {
    return currentConfig.headerPairs.map((hp) => ({
      header: hp.key,
      value: hp.value,
    }));
  }
  return [];
};

const getInitialApiFields = (currentConfig: Config | null | undefined, isNewConfig: boolean) => {
  if (isNewConfig || !currentConfig) {
    return {
      apiType: DEFAULT_CUSTOM_API_TYPE,
      apiUrl: DEFAULT_CUSTOM_API_URL,
      apiBody: DEFAULT_CUSTOM_API_BODY,
      apiKeyConfigured: false,
    };
  }
  return {
    apiType: currentConfig.apiType ?? DEFAULT_CUSTOM_API_TYPE,
    apiUrl: currentConfig.apiUrl ?? DEFAULT_CUSTOM_API_URL,
    apiBody: currentConfig.apiBody ?? DEFAULT_CUSTOM_API_BODY,
    apiKeyConfigured: Boolean(currentConfig.apiKeyConfigured),
  };
};

const buildParametersObject = (rows: ParameterRow[]): Record<string, string> => {
  const out: Record<string, string> = {};
  for (const row of rows) {
    const k = row.parameter.trim();
    if (k) out[k] = row.value;
  }
  return out;
};

const buildHeadersObject = (rows: HeaderRow[]): Record<string, string> => {
  const out: Record<string, string> = {};
  for (const row of rows) {
    const k = row.header.trim();
    if (k) out[k] = row.value;
  }
  return out;
};

interface EditCustomApplicationSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editingConfig: string;
  modelApps: ModelApp[];
  configs: Config[];
  onSaved?: (savedConfig: CustomAppConfigDTO) => void | Promise<void>;
}

export default function EditCustomApplicationSheet({
  open,
  onOpenChange,
  editingConfig,
  modelApps,
  configs,
  onSaved,
}: EditCustomApplicationSheetProps) {
  const { isNewConfig, currentConfig, currentModelApp } = React.useMemo(
    () => getModelAppConfigInfo(editingConfig, modelApps, configs),
    [editingConfig, modelApps, configs]
  );

  const initialFields = React.useMemo(
    () => getInitialApiFields(currentConfig, isNewConfig),
    [currentConfig, isNewConfig]
  );

  const [configName, setConfigName] = React.useState(
    isNewConfig ? 'New Configuration' : currentConfig?.name || 'New Configuration'
  );
  const [apiType, setApiType] = React.useState(initialFields.apiType);
  const [apiUrl, setApiUrl] = React.useState(initialFields.apiUrl);
  const [apiBody, setApiBody] = React.useState(initialFields.apiBody);
  const [secretValue, setSecretValue] = React.useState('');
  const [apiKeyConfigured, setApiKeyConfigured] = React.useState(initialFields.apiKeyConfigured);
  const [saving, setSaving] = React.useState(false);
  const [testResult, setTestResult] = React.useState<boolean | null>(null);
  const [popoverOpen, setPopoverOpen] = React.useState(false);
  const [parameters, setParameters] = React.useState(() =>
    getParameterRowsFromConfig(currentConfig)
  );
  const [headers, setHeaders] = React.useState(() =>
    getHeaderRowsFromConfig(currentConfig)
  );
  const [autosaveStatus, setAutosaveStatus] = React.useState<AutosaveStatus>('idle');
  const timeoutRef = React.useRef<NodeJS.Timeout | null>(null);
  const autosaveDebounceRef = React.useRef<NodeJS.Timeout | null>(null);
  const skipNextAutosaveRef = React.useRef(true);

  const buildSavedConfigPairs = React.useCallback((): Record<string, string> => {
    const out: Record<string, string> = {
      connector_adapter: DEFAULT_CONNECTOR_ADAPTER,
      api_type: apiType.trim() || DEFAULT_CUSTOM_API_TYPE,
      api_url: apiUrl.trim(),
      api_body: apiBody,
      [PARAMETERS_CONFIG_KEY]: serializeParametersJson(buildParametersObject(parameters)),
      [HEADERS_CONFIG_KEY]: serializeHeadersJson(buildHeadersObject(headers)),
    };
    return out;
  }, [apiType, apiUrl, apiBody, parameters, headers]);

  React.useEffect(() => {
    const fields = getInitialApiFields(currentConfig, isNewConfig);
    setConfigName(isNewConfig ? 'New Configuration' : currentConfig?.name || 'New Configuration');
    setApiType(fields.apiType);
    setApiUrl(fields.apiUrl);
    setApiBody(fields.apiBody);
    setSecretValue('');
    setApiKeyConfigured(fields.apiKeyConfigured);
    setTestResult(null);
    setPopoverOpen(false);
    setParameters(getParameterRowsFromConfig(currentConfig));
    setHeaders(getHeaderRowsFromConfig(currentConfig));
    setAutosaveStatus('idle');
    skipNextAutosaveRef.current = true;
  }, [isNewConfig, currentConfig, editingConfig]);

  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (autosaveDebounceRef.current) {
        clearTimeout(autosaveDebounceRef.current);
      }
    };
  }, []);

  React.useEffect(() => {
    if (!open) return;
    if (skipNextAutosaveRef.current) {
      skipNextAutosaveRef.current = false;
      return;
    }
    if (isNewConfig || !currentConfig) return;

    const configId = parseInt(currentConfig.id, 10);
    if (!Number.isFinite(configId) || configId <= 0) return;

    if (autosaveDebounceRef.current) {
      clearTimeout(autosaveDebounceRef.current);
    }

    autosaveDebounceRef.current = setTimeout(() => {
      autosaveDebounceRef.current = null;
      void (async () => {
        setAutosaveStatus('saving');
        try {
          await updateCustomAppConfig(configId, {
            name: configName.trim() || currentConfig.name,
            savedConfigPairs: buildSavedConfigPairs(),
          });
          setAutosaveStatus('saved');
        } catch {
          setAutosaveStatus('error');
        }
      })();
    }, AUTOSAVE_DEBOUNCE_MS);

    return () => {
      if (autosaveDebounceRef.current) {
        clearTimeout(autosaveDebounceRef.current);
        autosaveDebounceRef.current = null;
      }
    };
  }, [
    open,
    isNewConfig,
    currentConfig,
    parameters,
    headers,
    configName,
    buildSavedConfigPairs,
  ]);

  const hasReservedKeyInParameters = (): string | null => {
    for (const row of parameters) {
      const k = row.parameter.trim();
      if (k && RESERVED_CONFIG_KEYS.has(k)) return k;
    }
    return null;
  };

  const resetForm = () => {
    const fields = getInitialApiFields(currentConfig, isNewConfig);
    setConfigName(isNewConfig ? 'New Configuration' : currentConfig?.name || 'New Configuration');
    setApiType(fields.apiType);
    setApiUrl(fields.apiUrl);
    setApiBody(fields.apiBody);
    setSecretValue('');
    setApiKeyConfigured(fields.apiKeyConfigured);
    setTestResult(null);
    setPopoverOpen(false);
    setParameters(getParameterRowsFromConfig(currentConfig));
    setHeaders(getHeaderRowsFromConfig(currentConfig));
    setAutosaveStatus('idle');
    skipNextAutosaveRef.current = true;
  };

  const handleSave = async () => {
    if (testResult !== true) return;

    const reserved = hasReservedKeyInParameters();
    if (reserved) {
      window.alert(`"${reserved}" is a reserved parameter name. Use the dedicated fields above.`);
      return;
    }

    if (!configName.trim()) {
      window.alert('Enter a configuration name.');
      return;
    }

    if (!currentModelApp) {
      window.alert('No custom application context for this configuration.');
      return;
    }

    const customAppId = decodeCustomAppProviderId(currentModelApp.id);
    if (customAppId == null) {
      window.alert('Invalid custom application id.');
      return;
    }

    const trimmedSecret = secretValue.trim();
    if (isNewConfig && !trimmedSecret) {
      window.alert('Enter an Authorization secret for this configuration.');
      return;
    }
    if (!isNewConfig && !apiKeyConfigured && !trimmedSecret) {
      window.alert('Enter an Authorization secret (no secret is stored yet).');
      return;
    }

    setSaving(true);
    try {
      const savedConfigPairs = buildSavedConfigPairs();
      const payload = {
        name: configName.trim(),
        savedConfigPairs,
      };

      let savedConfig: CustomAppConfigDTO;
      if (!isNewConfig && currentConfig) {
        const configId = parseInt(currentConfig.id, 10);
        if (!Number.isFinite(configId) || configId <= 0) {
          window.alert('Invalid configuration id.');
          return;
        }
        savedConfig = await updateCustomAppConfig(configId, payload);
      } else {
        savedConfig = await createCustomAppConfig(customAppId, payload);
      }

      if (trimmedSecret) {
        await setCustomAppConfigSecret(savedConfig.id, 'api_key', trimmedSecret);
        savedConfig = { ...savedConfig, api_key_configured: true };
      }

      await onSaved?.(savedConfig);
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
    const reserved = hasReservedKeyInParameters();
    if (reserved) {
      setTestResult(false);
    } else if (configName.trim() && apiUrl.trim()) {
      setTestResult(true);
    } else {
      setTestResult(false);
    }

    setPopoverOpen(true);
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      setPopoverOpen(false);
    }, TEST_POPOVER_TIMEOUT);
  };

  const addParameter = () => {
    setParameters([...parameters, { parameter: '', value: '' }]);
  };

  const removeParameter = (index: number) => {
    setParameters(parameters.filter((_: ParameterRow, i: number) => i !== index));
  };

  const updateParameter = (index: number, field: 'parameter' | 'value', value: string) => {
    const updated = [...parameters];
    updated[index][field] = value;
    setParameters(updated);
  };

  const addHeader = () => {
    setHeaders([...headers, { header: '', value: '' }]);
  };

  const removeHeader = (index: number) => {
    setHeaders(headers.filter((_: HeaderRow, i: number) => i !== index));
  };

  const updateHeader = (index: number, field: 'header' | 'value', value: string) => {
    const updated = [...headers];
    updated[index][field] = value;
    setHeaders(updated);
  };

  const autosaveStatusLabel =
    autosaveStatus === 'saving'
      ? 'Saving…'
      : autosaveStatus === 'saved'
        ? 'Saved'
        : autosaveStatus === 'error'
          ? 'Save failed'
          : null;

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
            <Card className="py-0 gap-0">
              <CardContent className="p-4 space-y-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Custom Application*</Label>
                  <div className="text-sm px-3 py-2 rounded-md border text-gray-700 bg-gray-50">
                    {currentModelApp?.name || 'No application selected'}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="apiType" className="text-sm font-medium">
                    API Type*
                  </Label>
                  <select
                    id="apiType"
                    value={apiType}
                    onChange={(e) => setApiType(e.target.value)}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs"
                    tabIndex={-1}
                  >
                    {API_TYPE_OPTIONS.map((method) => (
                      <option key={method} value={method}>
                        {method}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="apiUrl" className="text-sm font-medium">
                    URL*
                  </Label>
                  <Input
                    id="apiUrl"
                    placeholder="https://api.example.com/v1/chat"
                    value={apiUrl}
                    onChange={(e) => setApiUrl(e.target.value)}
                    tabIndex={-1}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="apiBody" className="text-sm font-medium">
                    Request Body*
                  </Label>
                  <Textarea
                    id="apiBody"
                    placeholder='{"messages": []}'
                    value={apiBody}
                    onChange={(e) => setApiBody(e.target.value)}
                    className="min-h-[120px] font-mono text-sm"
                    tabIndex={-1}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="apiSecret" className="text-sm font-medium">
                    {apiKeyConfigured ? 'Authorization Secret (optional)' : 'Authorization Secret*'}
                  </Label>
                  <Input
                    id="apiSecret"
                    placeholder={
                      apiKeyConfigured && !secretValue
                        ? '••••••••'
                        : 'Enter Authorization secret'
                    }
                    type="password"
                    value={secretValue}
                    onChange={(e) => setSecretValue(e.target.value)}
                    tabIndex={-1}
                  />
                  {apiKeyConfigured ? (
                    <p className="text-sm text-gray-600">
                      A secret is already saved; leave blank to keep it, or enter a new one to replace it.
                    </p>
                  ) : null}
                </div>
              </CardContent>
            </Card>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Parameters</h3>
                {autosaveStatusLabel ? (
                  <span
                    className={
                      autosaveStatus === 'error'
                        ? 'text-sm text-red-600'
                        : 'text-sm text-gray-500'
                    }
                  >
                    {autosaveStatusLabel}
                  </span>
                ) : null}
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <Label className="text-sm font-medium text-gray-600">Parameter</Label>
                  </div>
                  <div className="flex-1">
                    <Label className="text-sm font-medium text-gray-600">Value</Label>
                  </div>
                  <div className="w-16"></div>
                </div>

                {parameters.map((param: ParameterRow, index: number) => (
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
                      {index === parameters.length - 1 && (
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

                {parameters.length === 0 && (
                  <div className="flex items-center gap-3">
                    <div className="flex-1"></div>
                    <div className="flex-1"></div>
                    <div className="flex items-center gap-1 w-16">
                      <div className="h-8 w-8"></div>
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

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Headers</h3>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <Label className="text-sm font-medium text-gray-600">Header</Label>
                  </div>
                  <div className="flex-1">
                    <Label className="text-sm font-medium text-gray-600">Value</Label>
                  </div>
                  <div className="w-16"></div>
                </div>

                {headers.map((row: HeaderRow, index: number) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="flex-1">
                      <Input
                        value={row.header}
                        onChange={(e) => updateHeader(index, 'header', e.target.value)}
                        tabIndex={-1}
                      />
                    </div>
                    <div className="flex-1">
                      <Input
                        value={row.value}
                        onChange={(e) => updateHeader(index, 'value', e.target.value)}
                        tabIndex={-1}
                      />
                    </div>
                    <div className="flex items-center gap-1 w-16">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeHeader(index)}
                        className="h-8 w-8 p-0"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                      {index === headers.length - 1 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={addHeader}
                          className="h-8 w-8 p-0"
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))}

                {headers.length === 0 && (
                  <div className="flex items-center gap-3">
                    <div className="flex-1"></div>
                    <div className="flex-1"></div>
                    <div className="flex items-center gap-1 w-16">
                      <div className="h-8 w-8"></div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={addHeader}
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

          <div className="mt-auto pt-6 pb-6 border-t">
            <div className="flex justify-between items-center">
              <Button
                variant="outline"
                onClick={() => {
                  resetForm();
                  onOpenChange(false);
                }}
              >
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
                  className={testResult !== true ? 'opacity-50 bg-gray-100 text-gray-400' : ''}
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
