/**
 * Benchmark run timestamps from GET /api/benchmark-runs are UTC instants.
 * The API often serializes them without a timezone suffix (naive ISO strings);
 * they must be parsed as UTC, not as local wall time.
 */

const HAS_TIMEZONE_SUFFIX = /(?:Z|[+-]\d{2}:?\d{2})$/i;

function normalizeToIsoUtc(value: string): string {
  const trimmed = value.trim();
  const withT = trimmed.includes("T") ? trimmed : trimmed.replace(" ", "T");
  return HAS_TIMEZONE_SUFFIX.test(withT) ? withT : `${withT}Z`;
}

/** Parse an API timestamp string as a UTC instant. */
export function parseApiUtcTimestamp(value: string): Date | null {
  const trimmed = value.trim();
  if (!trimmed) return null;

  const d = new Date(normalizeToIsoUtc(trimmed));
  return Number.isNaN(d.getTime()) ? null : d;
}

export function formatRunTimestamp(
  iso: string | null | undefined,
  kind: "completed" | "started"
): string {
  if (!iso) return kind === "completed" ? "Completed —" : "Started —";
  const d = parseApiUtcTimestamp(iso);
  if (!d) return kind === "completed" ? "Completed —" : "Started —";
  const label = kind === "completed" ? "Completed" : "Started";
  return `${label} ${d.toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })}`;
}

function formatMinuteCount(mins: number): string {
  if (mins < 1) return "<1min";
  if (mins < 60) return `${mins}min`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m ? `${h}h ${m}min` : `${h}h`;
}

export function formatDurationMinutes(
  startIso: string | null | undefined,
  endIso: string | null | undefined
): string | null {
  if (!startIso || !endIso) return null;
  const startDate = parseApiUtcTimestamp(startIso);
  const endDate = parseApiUtcTimestamp(endIso);
  if (!startDate || !endDate) return null;
  const start = startDate.getTime();
  const end = endDate.getTime();
  if (end < start) return null;
  const mins = Math.round((end - start) / 60000);
  return formatMinuteCount(mins);
}

/** Elapsed time from a run or test start timestamp to now (or a fixed instant). */
export function formatElapsedSinceStart(
  startIso: string | null | undefined,
  nowMs = Date.now()
): string | null {
  if (!startIso) return null;
  const startDate = parseApiUtcTimestamp(startIso);
  if (!startDate) return null;
  const mins = Math.max(0, Math.round((nowMs - startDate.getTime()) / 60000));
  return formatMinuteCount(mins);
}
