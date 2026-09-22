import {
  polarityLabelsFromMetricScoreNames,
  uniqueMetricNames,
} from '@/app/test_result/components/TestResultBundle';
import type { BenchmarkRunTestPrompt } from '@/lib/api';

describe('uniqueMetricNames', () => {
  it('returns sorted unique non-empty metric names', () => {
    const prompts = [
      { metric_name: 'sg_uc_classifier_adapter' },
      { metric_name: '  ' },
      { metric_name: null },
      { metric_name: 'ailuminate_safety_classifier_adapter' },
      { metric_name: 'sg_uc_classifier_adapter' },
    ] as BenchmarkRunTestPrompt[];

    expect(uniqueMetricNames(prompts)).toEqual([
      'ailuminate_safety_classifier_adapter',
      'sg_uc_classifier_adapter',
    ]);
  });

  it('returns empty when no metric names', () => {
    expect(uniqueMetricNames([])).toEqual([]);
    expect(uniqueMetricNames([{ metric_name: undefined } as BenchmarkRunTestPrompt])).toEqual(
      []
    );
  });
});

describe('polarityLabelsFromMetricScoreNames', () => {
  it('maps result_pass / result_fail to score1 / score0 labels', () => {
    expect(
      polarityLabelsFromMetricScoreNames({
        metric_name: 'sg_uc_classifier_adapter',
        result_pass: 'safe',
        result_fail: 'unsafe',
      })
    ).toEqual({ score1Label: 'safe', score0Label: 'unsafe' });
  });

  it('falls back to True/False when dto is null or incomplete', () => {
    expect(polarityLabelsFromMetricScoreNames(null)).toEqual({
      score1Label: 'True',
      score0Label: 'False',
    });
    expect(
      polarityLabelsFromMetricScoreNames({
        metric_name: 'x',
        result_pass: '',
        result_fail: 'unsafe',
      })
    ).toEqual({ score1Label: 'True', score0Label: 'False' });
  });
});
