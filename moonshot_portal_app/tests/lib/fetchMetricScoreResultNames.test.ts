import { fetchMetricScoreResultNames } from '@/lib/api';

describe('fetchMetricScoreResultNames', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('returns API body on success', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        metric_name: 'sg_uc_classifier_adapter',
        result_pass: 'safe',
        result_fail: 'unsafe',
      }),
    }) as unknown as typeof fetch;

    await expect(
      fetchMetricScoreResultNames('sg_uc_classifier_adapter')
    ).resolves.toEqual({
      metric_name: 'sg_uc_classifier_adapter',
      result_pass: 'safe',
      result_fail: 'unsafe',
    });
  });

  it('returns True/False defaults when response is not ok', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    }) as unknown as typeof fetch;

    await expect(
      fetchMetricScoreResultNames('sg_uc_classifier_adapter')
    ).resolves.toEqual({
      metric_name: 'sg_uc_classifier_adapter',
      result_pass: 'True',
      result_fail: 'False',
    });
  });

  it('returns True/False defaults on network failure', async () => {
    global.fetch = jest
      .fn()
      .mockRejectedValue(new TypeError('Failed to fetch')) as unknown as typeof fetch;

    await expect(fetchMetricScoreResultNames('any_metric')).resolves.toEqual({
      metric_name: 'any_metric',
      result_pass: 'True',
      result_fail: 'False',
    });
  });
});
