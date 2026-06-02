/** Keys stored as dedicated form fields or secrets, not in the configuration-pairs grid. */
export const RESERVED_CONFIG_KEYS = new Set([
  'api_type',
  'api_url',
  'api_body',
  'api_key',
  'connector_adapter',
]);

export const DEFAULT_CUSTOM_API_TYPE = 'POST';
export const DEFAULT_CUSTOM_API_URL =
  'https://api.together.xyz/v1/chat/completions';
/** Together serverless model; messages content is replaced per benchmark prompt. */
export const DEFAULT_CUSTOM_API_BODY =
  '{"model": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "messages": [{"role": "user", "content": ""}], "max_tokens": 128}';
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
