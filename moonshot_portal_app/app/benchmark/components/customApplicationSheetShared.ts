import type { Config, ModelApp } from '../types/modelSelection';
import {
  getCustomAppConnectorDefaults,
  parseApiKeyAuthScheme,
  type ApiKeyAuthScheme,
} from '../constants/customAppConfig';

export const AUTOSAVE_DEBOUNCE_MS = 500;

export type ParameterRow = {
  parameter: string;
  value: string;
};

export type HeaderRow = {
  header: string;
  value: string;
};

export const getModelAppConfigInfo = (
  editingConfig: string,
  modelApps: ModelApp[],
  configs: Config[]
) => {
  const isNewConfig = modelApps.some((p) => p.id === editingConfig);
  const currentConfig = isNewConfig ? null : configs.find((m) => m.id === editingConfig);
  const currentModelApp = isNewConfig
    ? modelApps.find((p) => p.id === editingConfig)
    : modelApps.find((p) => p.id === currentConfig?.connector);

  return { isNewConfig, currentConfig, currentModelApp };
};

export const getParameterRowsFromConfig = (
  currentConfig: Config | null | undefined
): ParameterRow[] => {
  if (currentConfig?.configPairs && currentConfig.configPairs.length > 0) {
    return currentConfig.configPairs.map((cp) => ({
      parameter: cp.key,
      value: cp.value,
    }));
  }
  return [];
};

export const getHeaderRowsFromConfig = (
  currentConfig: Config | null | undefined
): HeaderRow[] => {
  if (currentConfig?.headerPairs && currentConfig.headerPairs.length > 0) {
    return currentConfig.headerPairs.map((hp) => ({
      header: hp.key,
      value: hp.value,
    }));
  }
  return [];
};

export const getInitialApiFields = (
  currentConfig: Config | null | undefined,
  isNewConfig: boolean,
  appName: string | undefined
) => {
  const defaults = getCustomAppConnectorDefaults(appName);
  if (isNewConfig || !currentConfig) {
    return {
      apiType: defaults.apiType,
      apiUrl: defaults.apiUrl,
      apiBody: defaults.apiBody,
      responsePath: defaults.responsePath,
      apiKeyConfigured: false,
      apiKeyAuthScheme: defaults.apiKeyAuthScheme,
      apiKeyAuthCustomHeader: '',
    };
  }
  return {
    apiType: currentConfig.apiType ?? defaults.apiType,
    apiUrl: currentConfig.apiUrl ?? defaults.apiUrl,
    apiBody: currentConfig.apiBody ?? defaults.apiBody,
    responsePath: currentConfig.responsePath ?? defaults.responsePath,
    apiKeyConfigured: Boolean(currentConfig.apiKeyConfigured),
    apiKeyAuthScheme: parseApiKeyAuthScheme(
      currentConfig.apiKeyAuthScheme ?? defaults.apiKeyAuthScheme
    ),
    apiKeyAuthCustomHeader: currentConfig.apiKeyAuthCustomHeader ?? '',
  };
};

export const buildParametersObject = (rows: ParameterRow[]): Record<string, string> => {
  const out: Record<string, string> = {};
  for (const row of rows) {
    const k = row.parameter.trim();
    if (k) out[k] = row.value;
  }
  return out;
};

export const buildHeadersObject = (rows: HeaderRow[]): Record<string, string> => {
  const out: Record<string, string> = {};
  for (const row of rows) {
    const k = row.header.trim();
    if (k) out[k] = row.value;
  }
  return out;
};

export type CustomApplicationFormVariant = 'custom' | 'bedrock';

export type InitialApiFields = {
  apiType: string;
  apiUrl: string;
  apiBody: string;
  responsePath: string;
  apiKeyConfigured: boolean;
  apiKeyAuthScheme: ApiKeyAuthScheme;
  apiKeyAuthCustomHeader: string;
};
