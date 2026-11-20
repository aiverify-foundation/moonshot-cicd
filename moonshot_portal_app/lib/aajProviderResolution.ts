import type { BundleTest, LlmProviderDTO } from '@/lib/api';
import type { Provider } from '@/app/benchmark/types/modelSelection';

export function mapLlmProviderDtoToProvider(dto: LlmProviderDTO): Provider {
  const pairs = dto.defaultConfigPairs ?? {};
  return {
    id: dto.id,
    name: dto.name,
    type: 'provider',
    defaultModel: dto.defaultModel ?? '',
    modelTextboxExplanation: dto.modelTextboxExplanation ?? '',
    configPairs: Object.keys(pairs).map((key) => ({
      key,
      value: String(pairs[key]),
    })),
    modelToken: dto.modelToken ?? '',
    system_name: dto.system_name,
  };
}

export function resolveAajProviderDisplayName(
  systemName: string,
  providers: Provider[]
): string {
  const provider = providers.find((p) => p.system_name === systemName);
  return provider?.name ?? `${systemName} (provider not in API)`;
}

/** Label for RequiredEndpointsCard rows (provider name + LLM judge suffix). */
export function resolveAajEndpointCardLabel(
  systemName: string,
  providers: Provider[]
): string {
  const provider = providers.find((p) => p.system_name === systemName);
  if (provider) {
    return `${provider.name} (LLM judge)`;
  }
  return `${systemName} (provider not in API)`;
}

/** Model Name value on the View Test page. */
export function resolveModelNameLabel(
  test: BundleTest | null | undefined
): string {
  const model = test?.metric_grader_model_name?.trim();
  return model && model.length > 0 ? model : '—';
}

/** AAJ tests grouped by metric_provider_system_name → display names for UI lists. */
export function groupAajTestsByProviderSystemName(
  tests: BundleTest[] | undefined
): Map<string, Set<string>> {
  const bySystem = new Map<string, Set<string>>();
  if (!tests?.length) return bySystem;
  for (const test of tests) {
    if (!test.requires_llm_aaj || !test.metric_provider_system_name?.trim()) {
      continue;
    }
    const sn = test.metric_provider_system_name.trim();
    if (!bySystem.has(sn)) {
      bySystem.set(sn, new Set());
    }
    bySystem.get(sn)!.add(test.name);
  }
  return bySystem;
}

/** Unique metric-side provider system_names for tests that require LLM-as-judge. */
export function collectAajProviderSystemNames(
  tests: BundleTest[] | undefined
): string[] {
  return Array.from(groupAajTestsByProviderSystemName(tests).keys()).sort((a, b) =>
    a.localeCompare(b)
  );
}

/** Provider display names required by a bundle's tests (for summary UI). */
export function resolveRequiredAajProviderNames(
  tests: BundleTest[] | undefined,
  providers: Provider[]
): string[] {
  return collectAajProviderSystemNames(tests).map((systemName) =>
    resolveAajProviderDisplayName(systemName, providers)
  );
}
