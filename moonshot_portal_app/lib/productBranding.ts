export const PRODUCT_VERSION = '1.0.0';

export function formatLandingVersion(): string {
  return PRODUCT_VERSION;
}

export function formatReportVersion(): string {
  return `v ${PRODUCT_VERSION}`;
}

export function getHeaderProductName(useAivetBranding: boolean): string {
  return useAivetBranding ? 'Evals Toolkit' : 'Moonshot';
}

export function getReportProductName(useAivetBranding: boolean): string {
  return useAivetBranding ? 'AI Verify Evals Toolkit' : 'Project Moonshot';
}

export function getTestToolReportLines(
  useAivetBranding: boolean,
): readonly [string, string] {
  return [getReportProductName(useAivetBranding), formatReportVersion()];
}

/** Single string with line break between product name and version (e.g. for PDF). */
export function getTestToolLabel(useAivetBranding: boolean): string {
  const [name, version] = getTestToolReportLines(useAivetBranding);
  return `${name}\n${version}`;
}
