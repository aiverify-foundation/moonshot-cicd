/** Convert API accuracy (0–1) or already-percent values to 0–100. */
export function accuracyToPercent(acc: number | null | undefined): number | null {
  if (acc == null || Number.isNaN(acc)) return null;
  if (acc >= 0 && acc <= 1) return acc * 100;
  return acc;
}

/** Arithmetic mean rounded to one decimal place. */
export function meanScorePercent(values: number[]): number | null {
  if (!values.length) return null;
  return Math.round((values.reduce((a, b) => a + b, 0) / values.length) * 10) / 10;
}

/** Format a 0–100 score as e.g. `"59.8%"`. */
export function formatScorePercent(score: number): string {
  return `${Math.round(score * 10) / 10}%`;
}
