/** Backend llm_provider.system_name for boto AWS Bedrock (hidden from model-under-test UI). */
export const AWS_BEDROCK_ADAPTER_SYSTEM_NAME = 'aws_bedrock_adapter';

/**
 * Whether an API provider may appear in "Select App or Model Under Test".
 * AWS Bedrock stays available via GET /api/providers for LLM-as-judge configuration.
 */
export function isSelectableModelUnderTestProvider(
  systemName: string | undefined
): boolean {
  const normalized = (systemName ?? '').trim();
  if (!normalized) return true;
  return normalized !== AWS_BEDROCK_ADAPTER_SYSTEM_NAME;
}
