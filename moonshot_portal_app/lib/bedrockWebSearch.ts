/** Backend llm_provider.system_name for Bedrock Mantle web search. */
export const BEDROCK_WEB_SEARCH_SYSTEM_NAME = 'bedrock_mantle_web_search';

export function isBedrockWebSearchProvider(systemName: string | undefined): boolean {
  return systemName === BEDROCK_WEB_SEARCH_SYSTEM_NAME;
}
