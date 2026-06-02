/**
 * Shared types for benchmark model / application selection UI.
 * Standard LLM providers and models are loaded from the API; these shapes are used for props and mapping.
 */

export interface Provider {
  id: string;
  name: string;
  type: string;
  defaultModel: string;
  modelTextboxExplanation: string;
  configPairs: Array<{ key: string; value: string }>;
  modelToken: string;
  /** Backend stable id for GET /api/providers/by-system-name/{system_name}/latest-details */
  system_name?: string;
}

export interface ModelConfig {
  /**
   * Unique row key for the combobox. With a DB-backed config: `${llm_provider_model.id}:${config.id}`.
   * With no saved config for that model: `String(llm_provider_model.id)` (parseInt(id) yields the model id).
   */
  id: string;
  name: string;
  modelname: string;
  provider: string;
  /** llm_provider_model_config.id when loaded from database_model_configs */
  modelConfigId?: string;
  /** From database_model_configs when this model row has a saved config (latest-details). */
  savedConfigPairs?: Record<string, string>;
}

/** Saved connector configuration row (custom-application path). */
export interface Config {
  id: string;
  name: string;
  connector: string;
  configPairs: Array<{ key: string; value: string }>;
  /** Reserved / first-class fields split out for the edit sheet (from savedConfigPairs). */
  apiType?: string;
  apiUrl?: string;
  apiBody?: string;
  /** From GET custom app config; secret value is never returned. */
  apiKeyConfigured?: boolean;
}

/** Custom application / connector app entry (custom-application path). */
export interface ModelApp {
  id: string;
  name: string;
  type: string;
}

/** Standard providers and custom apps shown together in the provider combobox and model sheet. */
export type ProviderListEntry = Provider | ModelApp;
