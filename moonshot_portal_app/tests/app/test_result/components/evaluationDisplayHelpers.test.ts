import {
  evaluationDisplayLabel,
  extractEvaluatedResponse,
} from '@/app/test_result/components/evaluationDisplayHelpers';

describe('evaluationDisplayHelpers', () => {
  describe('extractEvaluatedResponse', () => {
    it('parses evaluated_response from JSON', () => {
      expect(
        extractEvaluatedResponse('{"evaluated_response": "safe", "score": 1}')
      ).toBe('safe');
    });
  });

  describe('evaluationDisplayLabel', () => {
    it('returns Unknown for connector prompt errors', () => {
      expect(
        evaluationDisplayLabel('error', 0, {
          isPromptError: true,
          errorSource: 'connector',
        })
      ).toBe('Unknown');
    });

    it('returns Unknown for prompt errors without error source', () => {
      expect(
        evaluationDisplayLabel('error', 0, { isPromptError: true })
      ).toBe('Unknown');
    });

    it('returns Error for metric prompt errors', () => {
      expect(
        evaluationDisplayLabel('error', 0, {
          isPromptError: true,
          errorSource: 'metric',
        })
      ).toBe('Error');
    });

    it('returns Unknown when evaluation blob is error without metric source', () => {
      expect(evaluationDisplayLabel('error', 0)).toBe('Unknown');
    });

    it('returns Disagree for score 0 without prompt error', () => {
      expect(evaluationDisplayLabel("{'score': 0}", 0)).toBe('Disagree');
    });

    it('returns Agree for score 1', () => {
      expect(evaluationDisplayLabel("{'score': 1}", 1)).toBe('Agree');
    });
  });
});
