/**
 * API service for communicating with the Moonshot CI/CD backend
 */

const API_BASE_URL = 'http://localhost:8000';

/** Prompt-level row from test_details.csv (GET /api/bundles → tests[].details). */
export interface TestDetailRow {
  category_name: string;
  dataset: string;
  hazard: string;
  input: string;
  target: string;
  response: string;
  evaluator_verdict: string;
}

export interface BundleTest {
  name: string;
  /** benchmark_test.id from the API; required for per-bundle test subset runs. */
  benchmark_test_id?: number | null;
  description?: string;
  /** True when the metric uses an LLM-as-judge path (e.g. AILuminate safety classifier). */
  requires_llm_aaj?: boolean;
  /** Metric-side connector system_name when requires_llm_aaj (e.g. together_adapter). */
  metric_provider_system_name?: string | null;
  /** Evaluator model from moonshot_config metrics (connector_configurations.model). */
  metric_grader_model_name?: string | null;
  dataset: {
    id: string;
    name: string;
    description: string;
    num_of_dataset_prompts: number;
  };
  metric?: {
    name?: string;
    config_id?: string;
    [key: string]: string | undefined;
  };
  /** Sample prompt rows for this test's dataset; null when CSV has no rows. */
  details?: TestDetailRow[] | null;
}

export interface Bundle {
  /** Bundle system_name (YAML key); use for Redux keys and POST `bundle_names`. */
  id: string;
  name: string;
  description: string;
  category: string;
  tests: BundleTest[];
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

/** POST /api/start-benchmark-run */
export type StartBenchmarkRunRequest =
  | {
      run_name: string;
      /** Each entry is a bundle system_name (same as `Bundle.id` from GET /api/bundles). */
      bundle_names: string[];
      llm_provider_id: number;
      llm_provider_model_id: number;
      llm_provider_model_config_id: number;
      tests_by_bundle?: Record<string, number[]>;
      prompts_by_test?: Record<number, number>;
    }
  | {
      run_name: string;
      bundle_names: string[];
      custom_app_id: number;
      custom_app_config_id: number;
      tests_by_bundle?: Record<string, number[]>;
      prompts_by_test?: Record<number, number>;
    };

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
  custom_app_id?: number | null;
  custom_app_config_id?: number | null;
  endpoint_config_name?: string | null;
}

/** GET /api/benchmark-runs/check-name */
export interface CheckBenchmarkRunNameResponse {
  run_name: string;
  available: boolean;
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
  /** benchmark_test.id when returned from API (prompts / results). */
  test_id?: number | null;
  prompt_id: number;
  status: string;
  target?: string;
  prompt_additional_info?: string | null;
  prediction_result?: string | null;
  prediction_context?: string | null;
  evaluation_prompt?: string | null;
  evaluation_prediction_result?: string | null;
  evaluation_accuracy?: number | null;
  /**
   * Canonical prompt score for results UI.
   * Parsed server-side from `evaluation_prediction_result` (JSON object `score`, JSON number, or dict repr)
   * and intentionally does not use `evaluation_accuracy`.
   */
  score?: number | null;
  user_evaluation?: number | null;
  user_notes?: string | null;
  /** Display name of the test this prompt belongs to (benchmark_test.name). */
  test_name?: string;
  /** Latest per-prompt error message from benchmark_run_test_error. */
  error_message?: string | null;
  /** Latest per-prompt error source: "connector" or "metric". */
  error_source?: string | null;
}

/** Per-test confidence half-width on GET .../results (same scale as `score`). */
export interface BenchmarkRunTestMarginOfError {
  test_id: number;
  margin_of_error: number;
}

/** Per-test execution timing from benchmark_run_test_status on GET .../results. */
export interface BenchmarkRunTestStatusSummary {
  test_id: number;
  start_dt?: string | null;
  end_dt?: string | null;
  /** not_started | in_progress | completed | completed_with_errors | failed | ... */
  status?: string;
}

/** GET /api/benchmark-runs/{run_id}/results */
export interface BenchmarkRunResultsBundleSummary {
  test_bundle_id: number;
  name: string;
  system_name: string;
  test_ids: number[];
}

export interface BenchmarkRunResults {
  run: BenchmarkRun;
  bundles: BenchmarkRunResultsBundleSummary[];
  prompts: BenchmarkRunTestPrompt[];
  test_margin_of_error: BenchmarkRunTestMarginOfError[];
  test_run_status: BenchmarkRunTestStatusSummary[];
}

/** PATCH /api/benchmark-run-test-prompts/{prompt_id} */
export interface PatchBenchmarkRunTestPromptUserBody {
  user_evaluation: number | null;
  user_notes: string | null;
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

/** POST /api/providers/test-connection */
export interface TestLlmProviderConnectionPayload {
  llm_provider_id: number;
  model_name: string;
  savedConfigPairs?: Record<string, string>;
  api_key?: string;
}

export interface TestLlmProviderConnectionResponse {
  success: boolean;
  error?: string | null;
  response_preview?: string | null;
}

export async function testLlmProviderConnection(
  payload: TestLlmProviderConnectionPayload
): Promise<TestLlmProviderConnectionResponse> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/providers/test-connection`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }
    );
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      console.error(`API Error: ${response.status} - ${errorText}`);
      const detail = parseErrorDetail(errorText);
      throw new ApiError(detail, response.status, response.statusText);
    }
    return response.json() as Promise<TestLlmProviderConnectionResponse>;
  } catch (error) {
    console.error('Test LLM provider connection error:', error);
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
export type UpdateDatabaseModelConfigPayload =
  | {
      model_id: number;
      name: string;
      savedConfigPairs?: Record<string, string>;
    }
  | {
      llm_provider_id: number;
      model_name: string;
      name: string;
      savedConfigPairs?: Record<string, string>;
    };

export async function updateDatabaseModelConfig(
  configId: number,
  payload: UpdateDatabaseModelConfigPayload
): Promise<DatabaseModelConfigDTO> {
  try {
    const body: Record<string, unknown> = {
      name: payload.name,
      savedConfigPairs: payload.savedConfigPairs ?? {},
    };
    if ('model_id' in payload) {
      body.model_id = payload.model_id;
    } else {
      body.llm_provider_id = payload.llm_provider_id;
      body.model_name = payload.model_name;
    }
    const response = await fetch(
      `${API_BASE_URL}/api/database-model-configs/${configId}`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
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
 * Check whether a benchmark run name is available.
 */
export async function checkBenchmarkRunName(
  runName: string
): Promise<CheckBenchmarkRunNameResponse> {
  try {
    const params = new URLSearchParams({ run_name: runName });
    return await handleJsonGet<CheckBenchmarkRunNameResponse>(
      `${API_BASE_URL}/api/benchmark-runs/check-name?${params.toString()}`,
      'check benchmark run name'
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

/**
 * Fetches run header, bundle summaries, and prompts (with test_id) for the results UI.
 */
export async function fetchBenchmarkRunResults(
  runId: number
): Promise<BenchmarkRunResults> {
  try {
    return await handleJsonGet<BenchmarkRunResults>(
      `${API_BASE_URL}/api/benchmark-runs/${runId}/results`,
      'fetch benchmark run results'
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

function parseContentDispositionFilename(header: string | null): string | null {
  if (!header) return null;
  const match = /filename\*?=(?:UTF-8''|")?([^";]+)"?/i.exec(header);
  if (!match?.[1]) return null;
  try {
    return decodeURIComponent(match[1].trim());
  } catch {
    return match[1].trim();
  }
}

function triggerAnchorDownload(blob: Blob, filename: string): void {
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = objectUrl;
  anchor.download = filename;
  anchor.style.display = 'none';
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(objectUrl);
}

function isUserAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError';
}

type SaveFilePickerFn = (options?: {
  suggestedName?: string;
  types?: Array<{
    description?: string;
    accept: Record<string, string[]>;
  }>;
}) => Promise<FileSystemFileHandle>;

function getSaveFilePicker(): SaveFilePickerFn | null {
  if (typeof window === 'undefined') return null;
  const picker = (window as Window & { showSaveFilePicker?: SaveFilePickerFn })
    .showSaveFilePicker;
  return typeof picker === 'function' ? picker : null;
}

export type BlobDownloadAccept = {
  description: string;
  mime: string;
  extension: string;
};

/**
 * Save a blob via the native Save As dialog when supported, else trigger a direct download.
 */
export async function saveBlobAsFile(
  blob: Blob,
  filename: string,
  accept: BlobDownloadAccept = {
    description: 'JSON',
    mime: 'application/json',
    extension: '.json',
  }
): Promise<void> {
  const showSaveFilePicker = getSaveFilePicker();
  if (showSaveFilePicker) {
    try {
      const handle = await showSaveFilePicker({
        suggestedName: filename,
        types: [
          {
            description: accept.description,
            accept: { [accept.mime]: [accept.extension] },
          },
        ],
      });
      const writable = await handle.createWritable();
      await writable.write(blob);
      await writable.close();
      return;
    } catch (error) {
      if (isUserAbortError(error)) return;
      throw error;
    }
  }

  triggerAnchorDownload(blob, filename);
}

/**
 * Downloads GA Schema1 JSON for a completed benchmark run via GET /api/benchmark-runs/{run_id}/export.
 */
export async function downloadBenchmarkRunResults(
  runId: number,
  runName?: string
): Promise<void> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/benchmark-runs/${runId}/export`,
      { method: 'GET' }
    );

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      const detail = parseErrorDetail(errorText);
      throw new ApiError(
        detail || `Failed to download run results: ${response.statusText} (${response.status})`,
        response.status,
        response.statusText
      );
    }

    const blob = await response.blob();
    const filename =
      parseContentDispositionFilename(response.headers.get('Content-Disposition')) ??
      (runName ? `${runName}.json` : `benchmark-run-${runId}.json`);

    await saveBlobAsFile(blob, filename);
  } catch (error) {
    handleConnectError(error, 'Failed to download run results');
  }
}

/**
 * Updates user verdict (user_evaluation) and notes (user_notes) for one benchmark_run_test_prompt row.
 */
export async function patchBenchmarkRunPromptUserFeedback(
  promptId: number,
  body: PatchBenchmarkRunTestPromptUserBody
): Promise<BenchmarkRunTestPrompt> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/benchmark-run-test-prompts/${promptId}`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }
    );
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      console.error(`API Error: ${response.status} - ${errorText}`);
      const detail = parseErrorDetail(errorText);
      throw new ApiError(
        `Failed to save prompt feedback: ${detail}`,
        response.status,
        response.statusText
      );
    }
    return response.json() as Promise<BenchmarkRunTestPrompt>;
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

/** GET /api/custom-apps */
export interface CustomAppDTO {
  id: number;
  name: string;
}

/** GET/POST/PUT custom app config responses */
export interface CustomAppConfigDTO {
  id: number;
  custom_app_id: number;
  name: string;
  savedConfigPairs: Record<string, string>;
  update_dt?: string | null;
  api_key_configured?: boolean;
}

export interface CreateCustomAppConfigPayload {
  name: string;
  savedConfigPairs?: Record<string, string>;
}

export type UpdateCustomAppConfigPayload = CreateCustomAppConfigPayload;

export interface SetCustomAppConfigSecretResponse {
  message: string;
}

export interface TestCustomAppConnectionPayload {
  savedConfigPairs: Record<string, string>;
  api_key?: string;
  config_id?: number;
}

export interface ResponseLeafRow {
  path: string;
  value: string;
}

export interface TestCustomAppConnectionResponse {
  success: boolean;
  status_code?: number | null;
  response_body: string;
  error?: string | null;
  response_leaves?: ResponseLeafRow[];
  response_is_json?: boolean;
}

export async function fetchCustomApps(): Promise<CustomAppDTO[]> {
  try {
    return await handleJsonGet<CustomAppDTO[]>(
      `${API_BASE_URL}/api/custom-apps`,
      'fetch custom apps'
    );
  } catch (error) {
    handleConnectError(error, 'Network error');
  }
}

export async function fetchCustomAppConfigs(
  appId: number
): Promise<CustomAppConfigDTO[]> {
  try {
    return await handleJsonGet<CustomAppConfigDTO[]>(
      `${API_BASE_URL}/api/custom-apps/${appId}/configs`,
      'fetch custom app configs'
    );
  } catch (error) {
    handleConnectError(error, 'Network error');
  }
}

export async function createCustomAppConfig(
  appId: number,
  payload: CreateCustomAppConfigPayload
): Promise<CustomAppConfigDTO> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/custom-apps/${appId}/configs`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
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
    return response.json() as Promise<CustomAppConfigDTO>;
  } catch (error) {
    console.error('Create custom app config error:', error);
    handleConnectError(error, 'Network error');
  }
}

export async function updateCustomAppConfig(
  configId: number,
  payload: UpdateCustomAppConfigPayload
): Promise<CustomAppConfigDTO> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/custom-apps/configs/${configId}`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
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
    return response.json() as Promise<CustomAppConfigDTO>;
  } catch (error) {
    console.error('Update custom app config error:', error);
    handleConnectError(error, 'Network error');
  }
}

export async function testCustomAppConnection(
  payload: TestCustomAppConnectionPayload
): Promise<TestCustomAppConnectionResponse> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/custom-apps/test-connection`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }
    );
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      console.error(`API Error: ${response.status} - ${errorText}`);
      const detail = parseErrorDetail(errorText);
      throw new ApiError(detail, response.status, response.statusText);
    }
    return response.json() as Promise<TestCustomAppConnectionResponse>;
  } catch (error) {
    console.error('Test custom app connection error:', error);
    handleConnectError(error, 'Network error');
  }
}

export async function setCustomAppConfigSecret(
  configId: number,
  key: string,
  secret: string
): Promise<SetCustomAppConfigSecretResponse> {
  try {
    const encodedKey = encodeURIComponent(key);
    const response = await fetch(
      `${API_BASE_URL}/api/custom-apps/configs/${configId}/secrets/${encodedKey}`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ secret }),
      }
    );
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      console.error(`API Error: ${response.status} - ${errorText}`);
      const detail = parseErrorDetail(errorText);
      throw new ApiError(detail, response.status, response.statusText);
    }
    return response.json() as Promise<SetCustomAppConfigSecretResponse>;
  } catch (error) {
    console.error('Set custom app config secret error:', error);
    handleConnectError(error, 'Network error');
  }
}
