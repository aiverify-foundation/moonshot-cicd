import {
  evaluationDisplayLabel,
  promptsToTableRows,
} from '@/app/test_result/components/TestResultBundle';
import type { BenchmarkRunTestPrompt } from '@/lib/api';

function makePrompt(
  overrides: Partial<BenchmarkRunTestPrompt> & Pick<BenchmarkRunTestPrompt, 'run_test_id' | 'prompt_id'>
): BenchmarkRunTestPrompt {
  return {
    status: 'completed',
    ...overrides,
  };
}

describe('promptsToTableRows', () => {
  it('maps connector errors to response error_message and Unknown evaluation', () => {
    const rows = promptsToTableRows([
      makePrompt({
        id: 1,
        run_test_id: 10,
        prompt_id: 100,
        status: 'error',
        error_source: 'connector',
        error_message: 'API timeout',
        prediction_result: null,
        evaluation_prediction_result: "{'score': 0}",
      }),
    ]);

    expect(rows).toHaveLength(1);
    expect(rows[0].response).toBe('API timeout');
    expect(rows[0].evaluation).toBe('error');
    expect(rows[0].errorSource).toBe('connector');
    expect(rows[0].score).toBe(0);
    expect(rows[0].isPromptError).toBe(true);
    expect(
      evaluationDisplayLabel(rows[0].evaluation, rows[0].score, {
        isPromptError: rows[0].isPromptError,
        errorSource: rows[0].errorSource,
      })
    ).toBe('Unknown');
  });

  it('maps metric errors to Error evaluation without using error_message as response', () => {
    const rows = promptsToTableRows([
      makePrompt({
        id: 2,
        run_test_id: 10,
        prompt_id: 101,
        status: 'error',
        error_source: 'metric',
        error_message: 'metric failed',
        prediction_result: null,
      }),
    ]);

    expect(rows[0].response).toBe('—');
    expect(rows[0].evaluation).toBe('error');
    expect(rows[0].errorSource).toBe('metric');
    expect(rows[0].score).toBe(0);
    expect(rows[0].isPromptError).toBe(true);
    expect(
      evaluationDisplayLabel(rows[0].evaluation, rows[0].score, {
        isPromptError: rows[0].isPromptError,
        errorSource: rows[0].errorSource,
      })
    ).toBe('Error');
  });

  it('maps metric errors to prediction_result in response when present', () => {
    const rows = promptsToTableRows([
      makePrompt({
        id: 4,
        run_test_id: 10,
        prompt_id: 103,
        status: 'error',
        error_source: 'metric',
        error_message: 'metric failed',
        prediction_result: 'model response text',
      }),
    ]);

    expect(rows[0].response).toBe('model response text');
    expect(rows[0].errorSource).toBe('metric');
    expect(
      evaluationDisplayLabel(rows[0].evaluation, rows[0].score, {
        isPromptError: rows[0].isPromptError,
        errorSource: rows[0].errorSource,
      })
    ).toBe('Error');
  });

  it('maps normal completed prompts unchanged', () => {
    const rows = promptsToTableRows([
      makePrompt({
        id: 3,
        run_test_id: 10,
        prompt_id: 102,
        status: 'completed',
        prediction_result: 'hello',
        evaluation_prediction_result: '{"score": 1}',
        score: 1,
      }),
    ]);

    expect(rows[0].response).toBe('hello');
    expect(rows[0].evaluation).toBe('{"score": 1}');
    expect(rows[0].score).toBe(1);
    expect(rows[0].isPromptError).toBe(false);
    expect(rows[0].errorSource).toBeNull();
  });
});
