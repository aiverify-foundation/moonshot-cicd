/**
 * Values that share the same scale as evaluation_accuracy (0–1 ratio vs 0–100 percent).
 * Used for margin_of_error and chart axes in the 0–100 domain.
 */
export function metricToPercentPoints(
  value: number | null | undefined
): number | null {
  if (value == null || Number.isNaN(value)) return null;
  if (value >= 0 && value <= 1) return value * 100;
  return value;
}
