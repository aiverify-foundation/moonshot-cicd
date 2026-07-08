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
    it('returns Error for prompt errors', () => {
      expect(
        evaluationDisplayLabel('error', 0, { isPromptError: true })
      ).toBe('Error');
    });

    it('returns Error when evaluation blob is error', () => {
      expect(evaluationDisplayLabel('error', 0)).toBe('Error');
    });

    it('returns Disagree for score 0 without prompt error', () => {
      expect(evaluationDisplayLabel("{'score': 0}", 0)).toBe('Disagree');
    });

    it('returns Agree for score 1', () => {
      expect(evaluationDisplayLabel("{'score': 1}", 1)).toBe('Agree');
    });
  });
});
