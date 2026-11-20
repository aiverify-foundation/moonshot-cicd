import {
  formatLandingVersion,
  formatReportVersion,
  getHeaderProductName,
  getReportProductName,
  getTestToolLabel,
  getTestToolReportLines,
  PRODUCT_VERSION,
} from '@/lib/productBranding';

describe('productBranding', () => {
  it('exposes PRODUCT_VERSION as semver without v prefix', () => {
    expect(PRODUCT_VERSION).toBe('1.0.0');
    expect(formatLandingVersion()).toBe('1.0.0');
  });

  it('formats report version with v prefix', () => {
    expect(formatReportVersion()).toBe('v 1.0.0');
  });

  it('returns header product names by branding flag', () => {
    expect(getHeaderProductName(true)).toBe('Evals Toolkit');
    expect(getHeaderProductName(false)).toBe('Moonshot');
  });

  it('returns report product names by branding flag', () => {
    expect(getReportProductName(true)).toBe('AI Verify Evals Toolkit');
    expect(getReportProductName(false)).toBe('Project Moonshot');
  });

  it('splits test tool into product name and version lines', () => {
    expect(getTestToolReportLines(true)).toEqual([
      'AI Verify Evals Toolkit',
      'v 1.0.0',
    ]);
    expect(getTestToolReportLines(false)).toEqual(['Project Moonshot', 'v 1.0.0']);
  });

  it('joins test tool lines for newline-separated label', () => {
    expect(getTestToolLabel(true)).toBe('AI Verify Evals Toolkit\nv 1.0.0');
    expect(getTestToolLabel(false)).toBe('Project Moonshot\nv 1.0.0');
  });
});
