"use client"
import React from 'react';
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Card, CardContent } from '@/components/ui/card';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Trash2, Plus } from "lucide-react";
import type { ModelApp, Config } from "../types/modelSelection";
import {
  ApiError,
  createCustomAppConfig,
  updateCustomAppConfig,
  setCustomAppConfigSecret,
  testCustomAppConnection,
  type CustomAppConfigDTO,
  type TestCustomAppConnectionResponse,
} from "@/lib/api";
import {
  RESERVED_CONFIG_KEYS,
  DEFAULT_CUSTOM_API_TYPE,
  DEFAULT_CUSTOM_API_URL,
  DEFAULT_CUSTOM_API_BODY,
  DEFAULT_RESPONSE_PATH,
  DEFAULT_CONNECTOR_ADAPTER,
  RESPONSE_PATH_CONFIG_KEY,
  PROMPT_PLACEHOLDER,
  bodyContainsPromptPlaceholder,
  PARAMETERS_CONFIG_KEY,
  HEADERS_CONFIG_KEY,
  API_KEY_AUTH_SCHEME_CONFIG_KEY,
  API_KEY_AUTH_CUSTOM_HEADER_CONFIG_KEY,
  DEFAULT_API_KEY_AUTH_SCHEME,
  API_KEY_AUTH_SCHEME_OPTIONS,
  parseApiKeyAuthScheme,
  type ApiKeyAuthScheme,
  decodeCustomAppProviderId,
  serializeParametersJson,
  serializeHeadersJson,
} from "../constants/customAppConfig";

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
      responsePath: DEFAULT_RESPONSE_PATH,
      apiKeyConfigured: false,
      apiKeyAuthScheme: DEFAULT_API_KEY_AUTH_SCHEME,
      apiKeyAuthCustomHeader: '',
    };
  }
  return {
    apiType: currentConfig.apiType ?? DEFAULT_CUSTOM_API_TYPE,
    apiUrl: currentConfig.apiUrl ?? DEFAULT_CUSTOM_API_URL,
    apiBody: currentConfig.apiBody ?? DEFAULT_CUSTOM_API_BODY,
    responsePath: currentConfig.responsePath ?? DEFAULT_RESPONSE_PATH,
    apiKeyConfigured: Boolean(currentConfig.apiKeyConfigured),
    apiKeyAuthScheme: parseApiKeyAuthScheme(currentConfig.apiKeyAuthScheme),
    apiKeyAuthCustomHeader: currentConfig.apiKeyAuthCustomHeader ?? '',
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
  const [responsePath, setResponsePath] = React.useState(initialFields.responsePath);
  const [secretValue, setSecretValue] = React.useState('');
  const [apiKeyConfigured, setApiKeyConfigured] = React.useState(initialFields.apiKeyConfigured);
  const [apiKeyAuthScheme, setApiKeyAuthScheme] = React.useState<ApiKeyAuthScheme>(
    initialFields.apiKeyAuthScheme
  );
  const [apiKeyAuthCustomHeader, setApiKeyAuthCustomHeader] = React.useState(
    initialFields.apiKeyAuthCustomHeader
  );
  const [saving, setSaving] = React.useState(false);
  const [connectionTesting, setConnectionTesting] = React.useState(false);
  const [connectionTestAttempted, setConnectionTestAttempted] = React.useState(false);
  const [connectionTestResult, setConnectionTestResult] =
    React.useState<TestCustomAppConnectionResponse | null>(null);
  const [parameters, setParameters] = React.useState(() =>
    getParameterRowsFromConfig(currentConfig)
  );
  const [headers, setHeaders] = React.useState(() =>
    getHeaderRowsFromConfig(currentConfig)
  );
  const [autosaveStatus, setAutosaveStatus] = React.useState<AutosaveStatus>('idle');
  const autosaveDebounceRef = React.useRef<NodeJS.Timeout | null>(null);
  const skipNextAutosaveRef = React.useRef(true);

  const buildSavedConfigPairs = React.useCallback((): Record<string, string> => {
    const out: Record<string, string> = {
      connector_adapter: DEFAULT_CONNECTOR_ADAPTER,
      api_type: apiType.trim() || DEFAULT_CUSTOM_API_TYPE,
      api_url: apiUrl.trim(),
      api_body: apiBody,
      [RESPONSE_PATH_CONFIG_KEY]: responsePath.trim(),
      [PARAMETERS_CONFIG_KEY]: serializeParametersJson(buildParametersObject(parameters)),
      [HEADERS_CONFIG_KEY]: serializeHeadersJson(buildHeadersObject(headers)),
      [API_KEY_AUTH_SCHEME_CONFIG_KEY]: apiKeyAuthScheme,
      [API_KEY_AUTH_CUSTOM_HEADER_CONFIG_KEY]:
        apiKeyAuthScheme === 'custom'
          ? apiKeyAuthCustomHeader.trim()
          : '',
    };
    return out;
  }, [
    apiType,
    apiUrl,
    apiBody,
    responsePath,
    parameters,
    headers,
    apiKeyAuthScheme,
    apiKeyAuthCustomHeader,
  ]);

  React.useEffect(() => {
    const fields = getInitialApiFields(currentConfig, isNewConfig);
    setConfigName(isNewConfig ? 'New Configuration' : currentConfig?.name || 'New Configuration');
    setApiType(fields.apiType);
    setApiUrl(fields.apiUrl);
    setApiBody(fields.apiBody);
    setResponsePath(fields.responsePath);
    setSecretValue('');
    setApiKeyConfigured(fields.apiKeyConfigured);
    setApiKeyAuthScheme(fields.apiKeyAuthScheme);
    setApiKeyAuthCustomHeader(fields.apiKeyAuthCustomHeader);
    setConnectionTestAttempted(false);
    setConnectionTestResult(null);
    setParameters(getParameterRowsFromConfig(currentConfig));
    setHeaders(getHeaderRowsFromConfig(currentConfig));
    setAutosaveStatus('idle');
    skipNextAutosaveRef.current = true;
  }, [isNewConfig, currentConfig, editingConfig]);

  React.useEffect(() => {
    return () => {
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
    apiKeyAuthScheme,
    apiKeyAuthCustomHeader,
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
    setResponsePath(fields.responsePath);
    setSecretValue('');
    setApiKeyConfigured(fields.apiKeyConfigured);
    setApiKeyAuthScheme(fields.apiKeyAuthScheme);
    setApiKeyAuthCustomHeader(fields.apiKeyAuthCustomHeader);
    setConnectionTestAttempted(false);
    setConnectionTestResult(null);
    setParameters(getParameterRowsFromConfig(currentConfig));
    setHeaders(getHeaderRowsFromConfig(currentConfig));
    setAutosaveStatus('idle');
    skipNextAutosaveRef.current = true;
  };

  const handleSave = async () => {
    if (!connectionTestAttempted) return;

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
    if (!bodyContainsPromptPlaceholder(apiBody)) {
      window.alert(`Request body must include ${PROMPT_PLACEHOLDER} where the benchmark prompt should be inserted.`);
      return;
    }
    if (!responsePath.trim()) {
      window.alert('Enter a Response Path before saving.');
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

  const handleTestConnection = async () => {
    const reserved = hasReservedKeyInParameters();
    if (reserved) {
      window.alert(`"${reserved}" is a reserved parameter name. Use the dedicated fields above.`);
      return;
    }

    if (!apiUrl.trim()) {
      window.alert('Enter a URL before testing the connection.');
      return;
    }
    if (!bodyContainsPromptPlaceholder(apiBody)) {
      window.alert(
        `Request body must include ${PROMPT_PLACEHOLDER} where the benchmark prompt should be inserted.`
      );
      return;
    }

    const trimmedSecret = secretValue.trim();
    const configId =
      !isNewConfig && currentConfig
        ? parseInt(currentConfig.id, 10)
        : Number.NaN;
    const hasStoredSecret =
      !isNewConfig && apiKeyConfigured && Number.isFinite(configId) && configId > 0;

    if (!trimmedSecret && !hasStoredSecret) {
      window.alert('Enter an authorization secret before testing the connection.');
      return;
    }

    setConnectionTestAttempted(true);
    setConnectionTesting(true);
    setConnectionTestResult(null);
    try {
      const result = await testCustomAppConnection({
        savedConfigPairs: buildSavedConfigPairs(),
        api_key: trimmedSecret || undefined,
        config_id: hasStoredSecret ? configId : undefined,
      });
      setConnectionTestResult(result);
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? e.message
          : e instanceof Error
            ? e.message
            : 'Connection test failed';
      setConnectionTestResult({
        success: false,
        response_body: '',
        error: msg,
      });
    } finally {
      setConnectionTesting(false);
    }
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
      <SheetContent
        side="right"
        className="w-[1400px] sm:max-w-[700px] ml-4 pl-6 pr-6 flex flex-col overflow-hidden"
      >
        <div className="flex flex-col flex-1 min-h-0">
          <div className="flex-1 min-h-0 overflow-y-auto space-y-6 pb-6">
            <SheetHeader className="p-0">
              <SheetTitle className="sr-only">Edit Custom Application Configuration</SheetTitle>
            </SheetHeader>

            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Edit Custom Application Configuration</h2>
            </div>

            <div className="space-y-2">
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
                    placeholder={'{"messages": [{"role": "user", "content": "{{prompt}}"}]}'}
                    value={apiBody}
                    onChange={(e) => setApiBody(e.target.value)}
                    className="min-h-[120px] font-mono text-sm"
                    tabIndex={-1}
                  />
                  <p className="text-sm text-gray-600">
                    Include {PROMPT_PLACEHOLDER} where the benchmark prompt should be inserted.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="apiKeyAuthScheme" className="text-sm font-medium">
                    Authorization Type*
                  </Label>
                  <select
                    id="apiKeyAuthScheme"
                    value={apiKeyAuthScheme}
                    onChange={(e) => setApiKeyAuthScheme(e.target.value as ApiKeyAuthScheme)}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs"
                    tabIndex={-1}
                  >
                    {API_KEY_AUTH_SCHEME_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <p className="text-sm text-gray-600">
                    {apiKeyAuthScheme === 'bearer'
                      ? 'Sends Authorization: Bearer <secret>'
                      : apiKeyAuthScheme === 'authorization_api_key'
                        ? 'Sends Authorization: ApiKey <secret>'
                        : apiKeyAuthScheme === 'x_api_key'
                          ? 'Sends X-API-Key: <secret>'
                          : apiKeyAuthScheme === 'x_api_key_lower'
                            ? 'Sends x-api-key: <secret>'
                            : 'Enter a custom header name below; the secret is sent as the header value.'}
                  </p>
                </div>

                {apiKeyAuthScheme === 'custom' ? (
                  <div className="space-y-2">
                    <Label htmlFor="apiKeyAuthCustomHeader" className="text-sm font-medium">
                      Custom Header*
                    </Label>
                    <Input
                      id="apiKeyAuthCustomHeader"
                      placeholder="e.g. X-API-Key:"
                      value={apiKeyAuthCustomHeader}
                      onChange={(e) => setApiKeyAuthCustomHeader(e.target.value)}
                      tabIndex={-1}
                    />
                  </div>
                ) : null}

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

            <div className="space-y-2">
              <Label className="text-sm font-medium">Connection test response</Label>
              {connectionTestResult ? (
                <>
                  <p
                    className={
                      connectionTestResult.success
                        ? 'text-sm text-green-600'
                        : 'text-sm text-red-600'
                    }
                  >
                    {connectionTestResult.success
                      ? `Connection succeeded (HTTP ${connectionTestResult.status_code ?? '—'})`
                      : connectionTestResult.error ||
                        `Connection failed (HTTP ${connectionTestResult.status_code ?? '—'})`}
                  </p>
                  {connectionTestResult.response_is_json &&
                  (connectionTestResult.response_leaves?.length ?? 0) > 0 ? (
                    <div className="max-h-48 overflow-y-auto rounded-md border bg-gray-50 p-3">
                      <div className="space-y-2">
                        <div className="flex items-start gap-3">
                          <div className="flex-1">
                            <Label className="text-xs font-medium text-gray-600">Path</Label>
                          </div>
                          <div className="flex-1">
                            <Label className="text-xs font-medium text-gray-600">Value</Label>
                          </div>
                        </div>
                        <p className="text-xs text-gray-600">
                          Click a path to set Response Path.
                        </p>
                        {connectionTestResult.response_leaves?.map((leaf, index) => (
                          <div key={index} className="flex items-start gap-3">
                            <div className="flex-1">
                              <button
                                type="button"
                                className="w-full text-left text-xs font-mono break-words text-gray-800 hover:bg-gray-100 hover:underline rounded px-1 py-0.5"
                                title="Click to use as Response Path"
                                onClick={() => setResponsePath(leaf.path)}
                              >
                                {leaf.path}
                              </button>
                            </div>
                            <div className="flex-1 text-xs font-mono break-words text-gray-800">
                              {leaf.value}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : connectionTestResult.response_is_json === false ? (
                    <>
                      <p className="text-sm text-gray-600">
                        Response is not JSON; showing raw body below.
                      </p>
                      <div className="max-h-48 overflow-y-auto rounded-md border bg-gray-50 p-3">
                        <pre className="text-xs font-mono whitespace-pre-wrap break-words">
                          {connectionTestResult.response_body ||
                            connectionTestResult.error ||
                            ''}
                        </pre>
                      </div>
                    </>
                  ) : (
                    <p className="text-sm text-gray-600">No scalar fields found.</p>
                  )}
                </>
              ) : (
                <p className="text-sm text-gray-600">
                  Run Test Connection to send a live request with the current form values.
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="responsePath" className="text-sm font-medium">
                Response Path*
              </Label>
              <Input
                id="responsePath"
                placeholder={DEFAULT_RESPONSE_PATH}
                value={responsePath}
                onChange={(e) => setResponsePath(e.target.value)}
                className="font-mono text-sm"
                tabIndex={-1}
              />
              <p className="text-sm text-gray-600">
                JSONPath used to read the model reply from the API response.
              </p>
            </div>
          </div>

          <div className="shrink-0 pt-6 pb-6 border-t">
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
                <Button
                  variant="outline"
                  onClick={() => void handleTestConnection()}
                  disabled={connectionTesting}
                >
                  {connectionTesting ? 'Testing…' : 'Test Connection'}
                </Button>
                <Button
                  onClick={() => void handleSave()}
                  disabled={!connectionTestAttempted || saving}
                  className={
                    !connectionTestAttempted ? 'opacity-50 bg-gray-100 text-gray-400' : ''
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
