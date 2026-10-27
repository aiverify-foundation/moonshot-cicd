'use client';

import React from 'react';
import type { ModelApp, Config } from '../types/modelSelection';
import {
  ApiError,
  createCustomAppConfig,
  updateCustomAppConfig,
  setCustomAppConfigSecret,
  testCustomAppConnection,
  type CustomAppConfigDTO,
  type TestCustomAppConnectionResponse,
} from '@/lib/api';
import {
  RESERVED_CONFIG_KEYS,
  DEFAULT_CUSTOM_API_TYPE,
  getCustomAppConnectorDefaults,
  RESPONSE_PATH_CONFIG_KEY,
  PROMPT_PLACEHOLDER,
  bodyContainsPromptPlaceholder,
  PARAMETERS_CONFIG_KEY,
  HEADERS_CONFIG_KEY,
  API_KEY_AUTH_SCHEME_CONFIG_KEY,
  API_KEY_AUTH_CUSTOM_HEADER_CONFIG_KEY,
  AWS_BEDROCK_API_APP_NAME,
  DEFAULT_BEDROCK_RESPONSE_PATH,
  decodeCustomAppProviderId,
  serializeParametersJson,
  serializeHeadersJson,
  type ApiKeyAuthScheme,
} from '../constants/customAppConfig';
import {
  AUTOSAVE_DEBOUNCE_MS,
  buildHeadersObject,
  buildParametersObject,
  getHeaderRowsFromConfig,
  getInitialApiFields,
  getModelAppConfigInfo,
  getParameterRowsFromConfig,
  type CustomApplicationFormVariant,
  type HeaderRow,
  type ParameterRow,
} from './customApplicationSheetShared';

export type UseCustomApplicationConfigFormOptions = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editingConfig: string;
  modelApps: ModelApp[];
  configs: Config[];
  onSaved?: (savedConfig: CustomAppConfigDTO) => void | Promise<void>;
  variant: CustomApplicationFormVariant;
};

export function useCustomApplicationConfigForm({
  open,
  onOpenChange,
  editingConfig,
  modelApps,
  configs,
  onSaved,
  variant,
}: UseCustomApplicationConfigFormOptions) {
  const isBedrockVariant = variant === 'bedrock';
  const showResponsePath = !isBedrockVariant;
  const connectionTestMode: 'bedrock_auto_parse' | 'json_path_picker' = isBedrockVariant
    ? 'bedrock_auto_parse'
    : 'json_path_picker';

  const { isNewConfig, currentConfig, currentModelApp } = React.useMemo(
    () => getModelAppConfigInfo(editingConfig, modelApps, configs),
    [editingConfig, modelApps, configs]
  );

  const defaultsAppName = isBedrockVariant
    ? AWS_BEDROCK_API_APP_NAME
    : currentModelApp?.name;

  const initialFields = React.useMemo(
    () => getInitialApiFields(currentConfig, isNewConfig, defaultsAppName),
    [currentConfig, isNewConfig, defaultsAppName]
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
  const [headers, setHeaders] = React.useState(() => getHeaderRowsFromConfig(currentConfig));
  const [autosaveStatus, setAutosaveStatus] = React.useState<
    'idle' | 'saving' | 'saved' | 'error'
  >('idle');
  const autosaveDebounceRef = React.useRef<NodeJS.Timeout | null>(null);
  const skipNextAutosaveRef = React.useRef(true);

  const buildSavedConfigPairs = React.useCallback((): Record<string, string> => {
    const connectorDefaults = getCustomAppConnectorDefaults(defaultsAppName);
    const out: Record<string, string> = {
      connector_adapter: connectorDefaults.connectorAdapter,
      api_type: apiType.trim() || DEFAULT_CUSTOM_API_TYPE,
      api_url: apiUrl.trim(),
      api_body: apiBody,
      [RESPONSE_PATH_CONFIG_KEY]: isBedrockVariant
        ? DEFAULT_BEDROCK_RESPONSE_PATH
        : responsePath.trim(),
      [PARAMETERS_CONFIG_KEY]: serializeParametersJson(buildParametersObject(parameters)),
      [HEADERS_CONFIG_KEY]: serializeHeadersJson(buildHeadersObject(headers)),
      [API_KEY_AUTH_SCHEME_CONFIG_KEY]: apiKeyAuthScheme,
      [API_KEY_AUTH_CUSTOM_HEADER_CONFIG_KEY]:
        apiKeyAuthScheme === 'custom' ? apiKeyAuthCustomHeader.trim() : '',
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
    defaultsAppName,
    isBedrockVariant,
  ]);

  React.useEffect(() => {
    const fields = getInitialApiFields(currentConfig, isNewConfig, defaultsAppName);
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
  }, [isNewConfig, currentConfig, editingConfig, defaultsAppName]);

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
    const fields = getInitialApiFields(currentConfig, isNewConfig, defaultsAppName);
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
      window.alert(
        `Request body must include ${PROMPT_PLACEHOLDER} where the benchmark prompt should be inserted.`
      );
      return;
    }
    if (showResponsePath && !responsePath.trim()) {
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
      !isNewConfig && currentConfig ? parseInt(currentConfig.id, 10) : Number.NaN;
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

  return {
    open,
    onOpenChange,
    variant,
    showResponsePath,
    connectionTestMode,
    currentModelApp,
    isNewConfig,
    configName,
    setConfigName,
    apiType,
    setApiType,
    apiUrl,
    setApiUrl,
    apiBody,
    setApiBody,
    responsePath,
    setResponsePath,
    secretValue,
    setSecretValue,
    apiKeyConfigured,
    apiKeyAuthScheme,
    setApiKeyAuthScheme,
    apiKeyAuthCustomHeader,
    setApiKeyAuthCustomHeader,
    saving,
    connectionTesting,
    connectionTestAttempted,
    connectionTestResult,
    parameters,
    headers,
    autosaveStatus,
    autosaveStatusLabel,
    resetForm,
    handleSave,
    handleTestConnection,
    addParameter,
    removeParameter,
    updateParameter,
    addHeader,
    removeHeader,
    updateHeader,
  };
}

export type CustomApplicationConfigFormState = ReturnType<
  typeof useCustomApplicationConfigForm
>;
