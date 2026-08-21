/** Keys stored as dedicated form fields or secrets, not in the configuration-pairs grid. */
export const RESERVED_CONFIG_KEYS = new Set([
  'api_type',
  'api_url',
  'api_body',
  'response_path',
  'api_key',
  'api_key_auth_scheme',
  'api_key_auth_custom_header',
  'connector_adapter',
  'parameters',
  'headers',
]);

export const PARAMETERS_CONFIG_KEY = 'parameters';
export const HEADERS_CONFIG_KEY = 'headers';
export const RESPONSE_PATH_CONFIG_KEY = 'response_path';
export const DEFAULT_RESPONSE_PATH = 'choices[0].message.content';
export const API_KEY_AUTH_SCHEME_CONFIG_KEY = 'api_key_auth_scheme';
export const API_KEY_AUTH_CUSTOM_HEADER_CONFIG_KEY = 'api_key_auth_custom_header';

export type ApiKeyAuthScheme =
  | 'bearer'
  | 'authorization_api_key'
  | 'x_api_key'
  | 'x_api_key_lower'
  | 'custom';

export const DEFAULT_API_KEY_AUTH_SCHEME: ApiKeyAuthScheme = 'bearer';

export const API_KEY_AUTH_SCHEME_OPTIONS: Array<{
  value: ApiKeyAuthScheme;
  label: string;
}> = [
  { value: 'bearer', label: 'Authorization: Bearer' },
  { value: 'authorization_api_key', label: 'Authorization: ApiKey' },
  { value: 'x_api_key', label: 'X-API-Key' },
  { value: 'x_api_key_lower', label: 'x-api-key (Anthropic)' },
  { value: 'custom', label: 'Custom header' },
];

export function parseApiKeyAuthScheme(value: string | undefined): ApiKeyAuthScheme {
  const normalized = (value ?? '').trim().toLowerCase();
  if (
    normalized === 'bearer' ||
    normalized === 'authorization_api_key' ||
    normalized === 'x_api_key' ||
    normalized === 'x_api_key_lower' ||
    normalized === 'custom'
  ) {
    return normalized;
  }
  return DEFAULT_API_KEY_AUTH_SCHEME;
}

export const PROMPT_PLACEHOLDER = '{{prompt}}';
export const CONNECTION_TEST_PROMPT = 'Hase the connection passed ? ';

export function bodyContainsPromptPlaceholder(body: string): boolean {
  return body.includes(PROMPT_PLACEHOLDER);
}

export const DEFAULT_CUSTOM_API_TYPE = 'POST';
export const DEFAULT_CUSTOM_API_URL =
  'https://api.together.xyz/v1/chat/completions';
/** Together serverless model; {{prompt}} is replaced per benchmark prompt. */
export const DEFAULT_CUSTOM_API_BODY = `{
  "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
  "messages": [
    {
      "role": "user",
      "content": "{{prompt}}"
    }
  ]
}`;
export const DEFAULT_CONNECTOR_ADAPTER = 'custom_api_connector_adapter';
export const CUSTOM_APP_PROVIDER_PREFIX = 'custom-app:';

export function encodeCustomAppProviderId(appId: number | string): string {
  return `${CUSTOM_APP_PROVIDER_PREFIX}${String(appId)}`;
}

export function decodeCustomAppProviderId(providerId: string): number | null {
  if (!providerId.startsWith(CUSTOM_APP_PROVIDER_PREFIX)) return null;
  const raw = providerId.slice(CUSTOM_APP_PROVIDER_PREFIX.length);
  const parsed = parseInt(raw, 10);
  if (!Number.isFinite(parsed) || parsed <= 0) return null;
  return parsed;
}

function parseJsonKeyValueMap(value: string | undefined): Record<string, string> {
  if (value == null || value.trim() === '') return {};
  try {
    const parsed: unknown = JSON.parse(value);
    if (parsed == null || typeof parsed !== 'object' || Array.isArray(parsed)) {
      return {};
    }
    const out: Record<string, string> = {};
    for (const [key, entryValue] of Object.entries(parsed)) {
      if (key.trim()) {
        out[key] = String(entryValue);
      }
    }
    return out;
  } catch {
    return {};
  }
}

export function parseParametersJson(value: string | undefined): Record<string, string> {
  return parseJsonKeyValueMap(value);
}

export function parseHeadersJson(value: string | undefined): Record<string, string> {
  return parseJsonKeyValueMap(value);
}

export function serializeParametersJson(params: Record<string, string>): string {
  const out: Record<string, string> = {};
  for (const [key, value] of Object.entries(params)) {
    const k = key.trim();
    if (k) out[k] = value;
  }
  return JSON.stringify(out);
}

export function serializeHeadersJson(headers: Record<string, string>): string {
  const out: Record<string, string> = {};
  for (const [key, value] of Object.entries(headers)) {
    const k = key.trim();
    if (k) out[k] = value;
  }
  return JSON.stringify(out);
}

/** Hydrate configuration-pair rows from savedConfigPairs (parameters JSON or legacy flat keys). */
export function hydrateConfigPairsFromSavedPairs(
  pairs: Record<string, string>
): Array<{ key: string; value: string }> {
  if (pairs[PARAMETERS_CONFIG_KEY] != null) {
    return Object.entries(parseParametersJson(pairs[PARAMETERS_CONFIG_KEY])).map(
      ([key, value]) => ({ key, value })
    );
  }
  return Object.entries(pairs)
    .filter(([key]) => !RESERVED_CONFIG_KEYS.has(key))
    .map(([key, value]) => ({ key, value: String(value) }));
}

/** Hydrate header rows from savedConfigPairs. */
export function hydrateHeaderPairsFromSavedPairs(
  pairs: Record<string, string>
): Array<{ key: string; value: string }> {
  if (pairs[HEADERS_CONFIG_KEY] == null) return [];
  return Object.entries(parseHeadersJson(pairs[HEADERS_CONFIG_KEY])).map(
    ([key, value]) => ({ key, value })
  );
}
