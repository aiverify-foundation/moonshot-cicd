/**
 * API service for communicating with the Moonshot CI/CD backend
 */

const API_BASE_URL = 'http://localhost:8000';

export interface Bundle {
  name: string;
  description: string;
  category: string;
  tests: Array<{
    name: string;
    description?: string;
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
  bundle_names: string[];
  llm_provider_name: string;
  llm_provider_config_name: string;
}

export interface StartBenchmarkRunResponse {
  message: string;
}

/**
 * Starts a benchmark run (one or more bundles) on the backend.
 * `llm_provider_config_name` must match a connector `id` in moonshot_config.yaml.
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
  llm_provider_endpoint_config_id?: number | null;
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
