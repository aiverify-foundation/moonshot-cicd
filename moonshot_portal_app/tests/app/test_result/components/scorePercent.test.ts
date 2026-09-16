import {
  accuracyToPercent,
  formatScorePercent,
  meanScorePercent,
} from "@/app/test_result/components/scorePercent";

describe("scorePercent", () => {
  describe("accuracyToPercent", () => {
    it("scales 0–1 values to 0–100", () => {
      expect(accuracyToPercent(0.598)).toBeCloseTo(59.8);
      expect(accuracyToPercent(1)).toBe(100);
      expect(accuracyToPercent(0)).toBe(0);
    });

    it("passes through already-percent values", () => {
      expect(accuracyToPercent(59.8)).toBe(59.8);
    });

    it("returns null for missing/NaN", () => {
      expect(accuracyToPercent(null)).toBeNull();
      expect(accuracyToPercent(undefined)).toBeNull();
      expect(accuracyToPercent(Number.NaN)).toBeNull();
    });
  });

  describe("meanScorePercent", () => {
    it("returns one-decimal prompt-level mean", () => {
      // Same inputs that previously produced integer overview 61% vs tab 59.8%
      // when averaged per-test vs prompt-level — here we only assert mean of percents.
      expect(meanScorePercent([50, 70, 59.4])).toBe(59.8);
    });

    it("returns null for empty list", () => {
      expect(meanScorePercent([])).toBeNull();
    });
  });

  describe("formatScorePercent", () => {
    it("formats to one decimal place", () => {
      expect(formatScorePercent(59.8)).toBe("59.8%");
      expect(formatScorePercent(61)).toBe("61%");
      expect(formatScorePercent(59.84)).toBe("59.8%");
      expect(formatScorePercent(59.85)).toBe("59.9%");
    });
  });
});
