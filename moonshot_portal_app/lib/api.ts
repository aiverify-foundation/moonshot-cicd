/**
 * API service for communicating with the Moonshot CI/CD backend
 */

const API_BASE_URL = 'http://localhost:8000';

export interface Bundle {
  /** Bundle system_name (YAML key); use for Redux keys and POST `bundle_names`. */
  id: string;
  name: string;
  description: string;
  category: string;
  tests: Array<{
    name: string;
    description?: string;
    /** True when the metric uses an LLM-as-judge path (e.g. Llama Guard annotator). */
    requires_llm_aaj?: boolean;
    /** Metric-side connector system_name when requires_llm_aaj (e.g. together_adapter). */
    metric_provider_system_name?: string | null;
    dataset: {
      id: string;
      name: string;
      description: string;
      num_of_dataset_prompts: number;
    };
    metric?: {
      name?: string;
      config_id?: string;
      [key: string]: string | undefined; //Undefined in order to accomodate the optional fields name and config_id
    };
  }>;
  /** Total prompts across tests; from GET /api/bundles. */
  prompt_count?: number;
}

export interface BundlesResponse {
  bundles: Bundle[];
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public statusText?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Fetches all bundles from the API
 */
export async function fetchBundles(): Promise<Bundle[]> {
  try {
    
    const response = await fetch(`${API_BASE_URL}/api/bundles`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      console.error(`API Error: ${response.status} - ${errorText}`);
      throw new ApiError(
        `Failed to fetch bundles: ${response.statusText} (${response.status})`,
        response.status,
        response.statusText
      );
    }

    const data: BundlesResponse = await response.json();
    return data.bundles;
  } catch (error) {
    console.error('Fetch bundles error:', error);
    
    if (error instanceof ApiError) {
      throw error;
    }
    
    // Handle network errors or other issues
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiError(
        `Cannot connect to API server at ${API_BASE_URL}. Please ensure the backend is running on port 8000.`
      );
    }
    
    throw new ApiError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

export interface FixedConfig {
  id: string;
  name: string;
  modelname: string;
  providerID: string;
  savedConfigPairs: Record<string, string>;
  lastUpdated: string | null;
}

export interface FixedConfigsResponse {
  configs: FixedConfig[];
}

/**
 * Fetches all fixed endpoint model configurations from the API
 */
export async function fetchFixedConfigs(): Promise<FixedConfig[]> {
  try {
   
    const response = await fetch(`${API_BASE_URL}/api/fixed-configs`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      console.error(`API Error: ${response.status} - ${errorText}`);
      throw new ApiError(
        `Failed to fetch fixed configs: ${response.statusText} (${response.status})`,
        response.status,
        response.statusText
      );
    }

    const data: FixedConfigsResponse = await response.json();
    return data.configs;
  } catch (error) {
    console.error('Fetch fixed configs error:', error);
    
    if (error instanceof ApiError) {
      throw error;
    }
    
    // Handle network errors or other issues
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiError(
        `Cannot connect to API server at ${API_BASE_URL}. Please ensure the backend is running on port 8000.`
      );
    }
    
    throw new ApiError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/** POST /api/start-benchmark-run */
export interface StartBenchmarkRunRequest {
  run_name: string;
  /** Each entry is a bundle system_name (same as `Bundle.id` from GET /api/bundles). Not filtered by per-test UI selection. */
  bundle_names: string[];
  llm_provider_id: number;
  llm_provider_model_id: number;
  llm_provider_model_config_id: number;
}

export interface StartBenchmarkRunResponse {
  message: string;
}

/**
 * Starts a benchmark run (one or more bundles) on the backend using relational
 * llm_provider / llm_provider_model / llm_provider_model_config ids.
 */
export async function startBenchmarkRun(
  payload: StartBenchmarkRunRequest
): Promise<StartBenchmarkRunResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/start-benchmark-run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      console.error(`API Error: ${response.status} - ${errorText}`);
      let detail = errorText;
      try {
        const parsed = JSON.parse(errorText) as { detail?: string | unknown };
        if (parsed?.detail != null) {
          detail =
            typeof parsed.detail === 'string'
              ? parsed.detail
              : JSON.stringify(parsed.detail);
        }
      } catch {
        /* use raw errorText */
      }
      throw new ApiError(
        `Failed to start benchmark run: ${detail}`,
        response.status,
        response.statusText
      );
    }

    return response.json() as Promise<StartBenchmarkRunResponse>;
  } catch (error) {
    console.error('Start benchmark run error:', error);
    if (error instanceof ApiError) throw error;
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiError(
        `Cannot connect to API server at ${API_BASE_URL}. Please ensure the backend is running on port 8000.`
      );
    }
    throw new ApiError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Health check for the API
 */
export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/`, {
      method: 'GET',
    });
    return response.ok;
  } catch {
    return false;
  }
}

/** GET /api/benchmark-runs */
export interface BenchmarkRun {
  id?: number | null;
  name: string;
  status: string;
  endpoint_type: string;
  start_time?: string | null;
  end_time?: string | null;
  llm_provider_id?: number | null;
  llm_provider_model_id?: number | null;
  llm_provider_model_config_id?: number | null;
}

/** GET /api/benchmark-runs/{run_id}/run-test-bundles */
export interface BenchmarkRunTestBundleRow {
  id?: number | null;
  run_id: number;
  test_bundle_id: number;
  test_id: number;
}

export function countBundlesAndTests(
  rows: BenchmarkRunTestBundleRow[]
): { bundleCount: number; testCount: number } {
  const bundleIds = new Set(rows.map((r) => r.test_bundle_id));
  const testIds = new Set(rows.map((r) => r.test_id));
  return { bundleCount: bundleIds.size, testCount: testIds.size };
}

/** GET /api/benchmark-runs/{run_id}/prompts */
export interface BenchmarkRunTestPrompt {
  id?: number | null;
  run_test_id: number;
  prompt_id: number;
  status: string;
  target?: string;
  prompt_additional_info?: string | null;
  prediction_result?: string | null;
  prediction_context?: string | null;
  evaluation_prompt?: string | null;
  evaluation_prediction_result?: string | null;
  evaluation_accuracy?: number | null;
  user_evaluation?: number | null;
  user_notes?: string | null;
  /** Display name of the test this prompt belongs to (benchmark_test.name). */
  test_name?: string;
}

async function handleJsonGet<T>(url: string, label: string): Promise<T> {
  const response = await fetch(url, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    console.error(`API Error: ${response.status} - ${errorText}`);
    throw new ApiError(
      `Failed to ${label}: ${response.statusText} (${response.status})`,
      response.status,
      response.statusText
    );
  }
  return response.json() as Promise<T>;
}

function parseErrorDetail(errorText: string): string {
  let detail = errorText;
  try {
    const parsed = JSON.parse(errorText) as { detail?: string | unknown };
    if (parsed?.detail != null) {
      detail =
        typeof parsed.detail === 'string'
          ? parsed.detail
          : JSON.stringify(parsed.detail);
    }
  } catch {
    /* use raw errorText */
  }
  return detail;
}

function handleConnectError(error: unknown, label: string): never {
  if (error instanceof ApiError) throw error;
  if (error instanceof TypeError && error.message.includes('fetch')) {
    throw new ApiError(
      `Cannot connect to API server at ${API_BASE_URL}. Please ensure the backend is running on port 8000.`
    );
  }
  throw new ApiError(
    `${label}: ${error instanceof Error ? error.message : 'Unknown error'}`
  );
}

/** GET /api/providers */
export interface LlmProviderDTO {
  id: string;
  name: string;
  system_name: string;
  version: number;
  defaultModel?: string;
  modelTextboxExplanation?: string;
  defaultConfigPairs?: Record<string, string>;
  modelToken?: string;
}

export async function fetchProviders(): Promise<LlmProviderDTO[]> {
  try {
    return await handleJsonGet<LlmProviderDTO[]>(
      `${API_BASE_URL}/api/providers`,
      'fetch providers'
    );
  } catch (error) {
    handleConnectError(error, 'Network error');
  }
}

/** GET /api/providers/by-system-name/{system_name}/latest-details */
export interface LlmProviderModelInfoDTO {
  id: number;
  name: string;
  create_dt: string;
}

export interface DatabaseModelConfigDTO {
  id: string;
  name: string;
  modelname: string;
  modelId: number;
  providerID: string;
  savedConfigPairs: Record<string, string>;
  lastUpdated: string;
}

export interface LlmProviderDetailsDTO {
  provider: LlmProviderDTO;
  models: LlmProviderModelInfoDTO[];
  endpoint_configs: Array<{ id: number; name: string }>;
  config_params?: Record<string, string> | null;
  database_model_configs?: DatabaseModelConfigDTO[];
  /** True when a stored API key exists for this provider; no secret is returned. */
  api_key_configured?: boolean;
}

export async function fetchProviderLatestDetails(
  systemName: string
): Promise<LlmProviderDetailsDTO> {
  const encoded = encodeURIComponent(systemName);
  try {
    return await handleJsonGet<LlmProviderDetailsDTO>(
      `${API_BASE_URL}/api/providers/by-system-name/${encoded}/latest-details`,
      'fetch provider details'
    );
  } catch (error) {
    handleConnectError(error, 'Network error');
  }
}

/** POST /api/providers/{provider_id}/api-key */
export interface SetLlmProviderApiKeyResponse {
  message: string;
}

export async function setLlmProviderApiKey(
  providerId: number,
  apiKey: string
): Promise<SetLlmProviderApiKeyResponse> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/providers/${providerId}/api-key`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey }),
      }
    );
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      console.error(`API Error: ${response.status} - ${errorText}`);
      const detail = parseErrorDetail(errorText);
      throw new ApiError(detail, response.status, response.statusText);
    }
    return response.json() as Promise<SetLlmProviderApiKeyResponse>;
  } catch (error) {
    console.error('Set LLM provider API key error:', error);
    handleConnectError(error, 'Network error');
  }
}

/** POST /api/database-model-configs */
export interface CreateDatabaseModelConfigPayload {
  /** Use either `model_id` or both `llm_provider_id` and `model_name`. */
  model_id?: number;
  llm_provider_id?: number;
  model_name?: string;
  name: string;
  savedConfigPairs?: Record<string, string>;
}

export interface DatabaseModelConfigDTO {
  id: string;
  name: string;
  modelname: string;
  providerID: string;
  savedConfigPairs: Record<string, string>;
  lastUpdated: string;
}

export async function createDatabaseModelConfig(
  payload: CreateDatabaseModelConfigPayload
): Promise<DatabaseModelConfigDTO> {
  try {
    const body: Record<string, unknown> = {
      name: payload.name,
      savedConfigPairs: payload.savedConfigPairs ?? {},
    };
    if (payload.model_id !== undefined && payload.model_id !== null) {
      body.model_id = payload.model_id;
    }
    if (payload.llm_provider_id !== undefined && payload.llm_provider_id !== null) {
      body.llm_provider_id = payload.llm_provider_id;
    }
    if (payload.model_name !== undefined) {
      body.model_name = payload.model_name;
    }
    const response = await fetch(`${API_BASE_URL}/api/database-model-configs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      console.error(`API Error: ${response.status} - ${errorText}`);
      const detail = parseErrorDetail(errorText);
      throw new ApiError(detail, response.status, response.statusText);
    }
    return response.json() as Promise<DatabaseModelConfigDTO>;
  } catch (error) {
    console.error('Create database model config error:', error);
    handleConnectError(error, 'Network error');
  }
}

/** PUT /api/database-model-configs/{config_id} */
export interface UpdateDatabaseModelConfigPayload {
  model_id: number;
  name: string;
  savedConfigPairs?: Record<string, string>;
}

export async function updateDatabaseModelConfig(
  configId: number,
  payload: UpdateDatabaseModelConfigPayload
): Promise<DatabaseModelConfigDTO> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/database-model-configs/${configId}`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_id: payload.model_id,
          name: payload.name,
          savedConfigPairs: payload.savedConfigPairs ?? {},
        }),
      }
    );
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      console.error(`API Error: ${response.status} - ${errorText}`);
      const detail = parseErrorDetail(errorText);
      throw new ApiError(detail, response.status, response.statusText);
    }
    return response.json() as Promise<DatabaseModelConfigDTO>;
  } catch (error) {
    console.error('Update database model config error:', error);
    handleConnectError(error, 'Network error');
  }
}

/**
 * Fetches all benchmark runs from the API
 */
export async function fetchBenchmarkRuns(): Promise<BenchmarkRun[]> {
  try {
    return await handleJsonGet<BenchmarkRun[]>(
      `${API_BASE_URL}/api/benchmark-runs`,
      'fetch benchmark runs'
    );
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiError(
        `Cannot connect to API server at ${API_BASE_URL}. Please ensure the backend is running on port 8000.`
      );
    }
    throw new ApiError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Fetches run-test-bundle rows for a benchmark run (for bundle/test counts).
 */
export async function fetchBenchmarkRunTestBundles(
  runId: number
): Promise<BenchmarkRunTestBundleRow[]> {
  try {
    return await handleJsonGet<BenchmarkRunTestBundleRow[]>(
      `${API_BASE_URL}/api/benchmark-runs/${runId}/run-test-bundles`,
      'fetch run-test-bundles'
    );
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiError(
        `Cannot connect to API server at ${API_BASE_URL}. Please ensure the backend is running on port 8000.`
      );
    }
    throw new ApiError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Fetches a single benchmark run by id. Throws ApiError (e.g. 404) on failure.
 */
export async function fetchBenchmarkRunById(runId: number): Promise<BenchmarkRun> {
  try {
    return await handleJsonGet<BenchmarkRun>(
      `${API_BASE_URL}/api/benchmark-runs/${runId}`,
      'fetch benchmark run'
    );
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiError(
        `Cannot connect to API server at ${API_BASE_URL}. Please ensure the backend is running on port 8000.`
      );
    }
    throw new ApiError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Fetches all run-test prompts for a benchmark run (includes test_name per row).
 */
export async function fetchBenchmarkRunPrompts(
  runId: number
): Promise<BenchmarkRunTestPrompt[]> {
  try {
    return await handleJsonGet<BenchmarkRunTestPrompt[]>(
      `${API_BASE_URL}/api/benchmark-runs/${runId}/prompts`,
      'fetch benchmark run prompts'
    );
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiError(
        `Cannot connect to API server at ${API_BASE_URL}. Please ensure the backend is running on port 8000.`
      );
    }
    throw new ApiError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}
