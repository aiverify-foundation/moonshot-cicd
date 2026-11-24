import {
  ADAPTER_NOT_FOUND_CODE,
  ApiError,
  adapterNotFoundMessage,
  downloadBenchmarkRunResults,
  fetchMetricScoreResultNames,
  parseAdapterNotFound,
  regenerateBenchmarkRunPrompt,
  startRegenerateFailedBenchmarkRunPrompts,
} from '@/lib/api';

const ADAPTER_DETAIL = {
  code: ADAPTER_NOT_FOUND_CODE,
  message: "The metric adapter 'gone_metric' is not available on the server.",
  adapter_type: 'metric',
  adapter_name: 'gone_metric',
};

function errorResponse(status: number, body: unknown) {
  return {
    ok: false,
    status,
    statusText: status === 404 ? 'Not Found' : 'Conflict',
    text: async () => (typeof body === 'string' ? body : JSON.stringify(body)),
  };
}

describe('parseAdapterNotFound', () => {
  it('returns the structured detail', () => {
    expect(
      parseAdapterNotFound(JSON.stringify({ detail: ADAPTER_DETAIL }))
    ).toEqual(ADAPTER_DETAIL);
  });

  it.each([
    ['a plain string detail', JSON.stringify({ detail: 'Run is still running' })],
    ['another object detail', JSON.stringify({ detail: { code: 'other' } })],
    ['a missing detail', JSON.stringify({})],
    ['a null detail', JSON.stringify({ detail: null })],
    ['an adapter code without names', JSON.stringify({ detail: { code: ADAPTER_NOT_FOUND_CODE } })],
    ['text that is not JSON', 'Internal Server Error'],
    ['an empty body', ''],
  ])('returns null for %s', (_label, body) => {
    expect(parseAdapterNotFound(body)).toBeNull();
  });
});

describe('adapterNotFoundMessage', () => {
  it('names the adapter and the unavailable action', () => {
    expect(
      adapterNotFoundMessage(
        { adapter_type: 'metric', adapter_name: 'gone_metric' },
        'exporting results'
      )
    ).toBe(
      'The metric adapter "gone_metric" used by this run is no longer installed on the server, ' +
        'so exporting results is unavailable. Ask an administrator to restore it.'
    );
  });
});

describe('adapter-not-found errors from the API', () => {
  const originalFetch = global.fetch;
  const originalConsoleError = console.error;

  beforeEach(() => {
    console.error = jest.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    console.error = originalConsoleError;
  });

  function mockFetch(response: unknown) {
    global.fetch = jest.fn().mockResolvedValue(response) as unknown as typeof fetch;
  }

  async function rejection(promise: Promise<unknown>): Promise<ApiError> {
    try {
      await promise;
    } catch (e) {
      return e as ApiError;
    }
    throw new Error('expected the promise to reject');
  }

  it('export throws a friendly ApiError with the adapter code', async () => {
    mockFetch(errorResponse(409, { detail: ADAPTER_DETAIL }));

    const error = await rejection(downloadBenchmarkRunResults(7, 'run'));

    expect(error).toBeInstanceOf(ApiError);
    expect(error.code).toBe(ADAPTER_NOT_FOUND_CODE);
    expect(error.status).toBe(409);
    expect(error.adapter).toEqual({ type: 'metric', name: 'gone_metric' });
    expect(error.message).toContain('"gone_metric"');
    expect(error.message).toContain('exporting results');
    expect(error.message).not.toContain('{');
  });

  it('single rerun throws a friendly ApiError with the adapter code', async () => {
    mockFetch(errorResponse(409, { detail: ADAPTER_DETAIL }));

    const error = await rejection(regenerateBenchmarkRunPrompt(42));

    expect(error.code).toBe(ADAPTER_NOT_FOUND_CODE);
    expect(error.message).toContain('re-running this prompt');
    expect(error.message).not.toContain('{');
  });

  it('bulk rerun throws a friendly ApiError with the adapter code', async () => {
    mockFetch(errorResponse(409, { detail: ADAPTER_DETAIL }));

    const error = await rejection(startRegenerateFailedBenchmarkRunPrompts(12));

    expect(error.code).toBe(ADAPTER_NOT_FOUND_CODE);
    expect(error.message).toContain('re-running failed prompts');
  });

  it('keeps plain-string conflict messages unchanged and has no code', async () => {
    mockFetch(
      errorResponse(409, {
        detail: 'Cannot regenerate while the benchmark run is still running.',
      })
    );

    const error = await rejection(regenerateBenchmarkRunPrompt(42));

    expect(error.code).toBeUndefined();
    expect(error.message).toBe(
      'Failed to regenerate prompt: Cannot regenerate while the benchmark run is still running.'
    );
  });

  it('shows the message of an object detail that is not an adapter error', async () => {
    mockFetch(errorResponse(409, { detail: { message: 'Export blocked' } }));

    const error = await rejection(downloadBenchmarkRunResults(7));

    expect(error.code).toBeUndefined();
    expect(error.message).toBe('Export blocked');
  });

  describe('fetchMetricScoreResultNames', () => {
    it('flags adapter_missing and keeps the True/False defaults on an adapter 404', async () => {
      mockFetch(errorResponse(404, { detail: ADAPTER_DETAIL }));

      await expect(fetchMetricScoreResultNames('gone_metric')).resolves.toEqual({
        metric_name: 'gone_metric',
        result_pass: 'True',
        result_fail: 'False',
        adapter_missing: true,
      });
    });

    it('does not flag adapter_missing for a plain 404', async () => {
      mockFetch(errorResponse(404, { detail: "Metric 'x' was not found." }));

      const result = await fetchMetricScoreResultNames('x');

      expect(result.adapter_missing).toBeUndefined();
      expect(result.result_pass).toBe('True');
    });

    it('does not flag adapter_missing when the 404 body cannot be read', async () => {
      mockFetch({
        ok: false,
        status: 404,
        text: async () => {
          throw new Error('stream closed');
        },
      });

      const result = await fetchMetricScoreResultNames('x');

      expect(result.adapter_missing).toBeUndefined();
    });

    it('does not read the body for non-404 failures', async () => {
      const text = jest.fn();
      mockFetch({ ok: false, status: 500, text });

      const result = await fetchMetricScoreResultNames('x');

      expect(result.adapter_missing).toBeUndefined();
      expect(text).not.toHaveBeenCalled();
    });
  });
});
