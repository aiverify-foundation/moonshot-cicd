import { firstScorePolarityLabels } from '@/app/test_result/components/TestResultBundle';
import type { TestResultTableRow } from '@/app/test_result/components/TestResultTable';

function makeRow(
  overrides: Partial<TestResultTableRow> & Pick<TestResultTableRow, 'id' | 'score'>
): TestResultTableRow {
  return {
    test: 't',
    prompt: 'p',
    target: '—',
    response: 'r',
    evaluation: '—',
    yourVerdict: null,
    note: '',
    bundle: 'b',
    graderLogic: '—',
    ...overrides,
  };
}

describe('firstScorePolarityLabels', () => {
  it('returns True/False when there are no rows', () => {
    expect(firstScorePolarityLabels([])).toEqual({
      score1Label: 'True',
      score0Label: 'False',
    });
  });

  it('picks first non-Error/Unknown labels for score 1 and score 0', () => {
    const rows = [
      makeRow({
        id: 'err',
        score: 0,
        evaluation: 'error',
        isPromptError: true,
        errorSource: 'connector',
      }),
      makeRow({
        id: 's1-first',
        score: 1,
        evaluation: '{"evaluated_response": "safe", "score": 1}',
      }),
      makeRow({
        id: 's1-second',
        score: 1,
        evaluation: '{"evaluated_response": "later-safe", "score": 1}',
      }),
      makeRow({
        id: 's0-first',
        score: 0,
        evaluation: '{"evaluated_response": "unsafe", "score": 0}',
      }),
    ];

    expect(firstScorePolarityLabels(rows)).toEqual({
      score1Label: 'safe',
      score0Label: 'unsafe',
    });
  });

  it('skips Unknown and Error labels even when score matches', () => {
    const rows = [
      makeRow({
        id: 'unknown',
        score: 0,
        evaluation: 'error',
        isPromptError: true,
        errorSource: 'connector',
      }),
      makeRow({
        id: 'metric-error',
        score: 0,
        evaluation: 'error',
        isPromptError: true,
        errorSource: 'metric',
      }),
      makeRow({
        id: 'ok0',
        score: 0,
        evaluation: '{"evaluated_response": "False", "score": 0}',
      }),
      makeRow({
        id: 'ok1',
        score: 1,
        evaluation: '{"evaluated_response": "True", "score": 1}',
      }),
    ];

    expect(firstScorePolarityLabels(rows)).toEqual({
      score1Label: 'True',
      score0Label: 'False',
    });
  });

  it('falls back Agree/Disagree via evaluationDisplayLabel when blob has no evaluated_response', () => {
    const rows = [
      makeRow({ id: 'a', score: 1, evaluation: "{'score': 1}" }),
      makeRow({ id: 'b', score: 0, evaluation: "{'score': 0}" }),
    ];

    expect(firstScorePolarityLabels(rows)).toEqual({
      score1Label: 'Agree',
      score0Label: 'Disagree',
    });
  });

  it('falls back True when score 1 is missing and False when score 0 is missing', () => {
    expect(
      firstScorePolarityLabels([
        makeRow({
          id: 'only0',
          score: 0,
          evaluation: '{"evaluated_response": "unsafe", "score": 0}',
        }),
      ])
    ).toEqual({ score1Label: 'True', score0Label: 'unsafe' });

    expect(
      firstScorePolarityLabels([
        makeRow({
          id: 'only1',
          score: 1,
          evaluation: '{"evaluated_response": "safe", "score": 1}',
        }),
      ])
    ).toEqual({ score1Label: 'safe', score0Label: 'False' });
  });
});
