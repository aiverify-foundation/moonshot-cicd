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
    dataset: {
      id: string;
      name: string;
      description: string;
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
    console.log(`Fetching bundles from: ${API_BASE_URL}/api/bundles`);
    
    const response = await fetch(`${API_BASE_URL}/api/bundles`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log(`Response status: ${response.status} ${response.statusText}`);

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
    console.log(`Successfully fetched ${data.bundles.length} bundles`);
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
  providerID: number;
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
    console.log(`Fetching fixed configs from: ${API_BASE_URL}/api/fixed-configs`);
    
    const response = await fetch(`${API_BASE_URL}/api/fixed-configs`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log(`Response status: ${response.status} ${response.statusText}`);

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
    console.log(`Successfully fetched ${data.configs.length} fixed configurations`);
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
