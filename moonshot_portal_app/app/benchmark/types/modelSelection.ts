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
  id: string;
  name: string;
  modelname: string;
  provider: string;
}

/** Saved connector configuration row (custom-application path; static data until a backend API exists). */
export interface Config {
  id: string;
  name: string;
  connector: string;
  configPairs: Array<{ key: string; value: string }>;
}

/** Custom application / connector app entry (custom-application path). */
export interface ModelApp {
  id: string;
  name: string;
  type: string;
}

/** Standard providers and custom apps shown together in the provider combobox and model sheet. */
export type ProviderListEntry = Provider | ModelApp;
