import { mapRunToReportData } from '@/app/test_result/pdf/mapRunToReportData';
import type {
  BenchmarkRun,
  BenchmarkRunResultsBundleSummary,
  BenchmarkRunTestMarginOfError,
  BenchmarkRunTestPrompt,
} from '@/lib/api';

const baseRun: BenchmarkRun = {
  name: 'Acme Chatbot',
  status: 'completed',
  endpoint_type: 'openai',
  end_time: '2025-06-15T10:30:00Z',
  endpoint_config_name: 'gpt-4o-mini',
};

function makePrompt(
  overrides: Partial<BenchmarkRunTestPrompt> & {
    test_id: number;
    score: number;
  }
): BenchmarkRunTestPrompt {
  return {
    run_test_id: 1,
    prompt_id: 1,
    status: 'completed',
    test_name: `Test ${overrides.test_id}`,
    ...overrides,
  };
}

describe('mapRunToReportData', () => {
  it('maps prompts into bundle rows with per-test scores and CI bands', () => {
    const bundles: BenchmarkRunResultsBundleSummary[] = [
      {
        test_bundle_id: 1,
        name: 'Safety Bundle',
        system_name: 'sys',
        test_ids: [101, 102],
      },
    ];
    const prompts: BenchmarkRunTestPrompt[] = [
      makePrompt({ test_id: 101, test_name: 'Hate', score: 0.9, prompt_id: 1 }),
      makePrompt({ test_id: 101, test_name: 'Hate', score: 0.7, prompt_id: 2 }),
      makePrompt({ test_id: 102, test_name: 'Fraud', score: 0.5, prompt_id: 3 }),
    ];
    const margins: BenchmarkRunTestMarginOfError[] = [
      { test_id: 101, margin_of_error: 0.05 },
      { test_id: 102, margin_of_error: 0.1 },
    ];

    const result = mapRunToReportData(baseRun, bundles, prompts, margins);

    expect(result.companyName).toBe('gpt-4o-mini');
    expect(result.testRunName).toBe('Acme Chatbot');
    expect(result.bundles).toHaveLength(1);
    expect(result.bundles[0].name).toBe('Safety Bundle');
    expect(result.bundles[0].score).toBe(70);
    expect(result.bundles[0].items).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: 'Fraud',
          score: 50,
          ciLow: 40,
          ciHigh: 60,
        }),
        expect.objectContaining({
          label: 'Hate',
          score: 80,
          ciLow: 75,
          ciHigh: 85,
        }),
      ])
    );
  });

  it('groups all prompts when no result bundles are returned', () => {
    const prompts: BenchmarkRunTestPrompt[] = [
      makePrompt({ test_id: 201, test_name: 'Privacy', score: 1, prompt_id: 1 }),
      makePrompt({ test_id: 202, test_name: 'Violence', score: 0.6, prompt_id: 2 }),
    ];

    const result = mapRunToReportData(baseRun, [], prompts, []);

    expect(result.bundles).toHaveLength(1);
    expect(result.bundles[0].name).toBe('All results');
    expect(result.bundles[0].items).toHaveLength(2);
    expect(result.bundles[0].score).toBe(80);
  });

  it('omits CI bounds when margin data is missing', () => {
    const prompts: BenchmarkRunTestPrompt[] = [
      makePrompt({ test_id: 301, test_name: 'Only test', score: 0.75, prompt_id: 1 }),
    ];

    const result = mapRunToReportData(baseRun, [], prompts, []);

    const item = result.bundles[0].items[0];
    expect(item.score).toBe(75);
    expect(item.ciLow).toBeUndefined();
    expect(item.ciHigh).toBeUndefined();
  });

  it('formats report date from run end_time', () => {
    const result = mapRunToReportData(baseRun, [], [], []);
    expect(result.reportDate).toMatch(/2025/);
  });
});
