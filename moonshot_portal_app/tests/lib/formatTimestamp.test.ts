import {
  formatDurationMinutes,
  formatElapsedSinceStart,
  formatRunTimestamp,
  parseApiUtcTimestamp,
} from "@/lib/formatTimestamp";

describe("parseApiUtcTimestamp", () => {
  it("treats naive API strings as UTC", () => {
    const d = parseApiUtcTimestamp("2026-06-04T10:00:00");
    expect(d).not.toBeNull();
    expect(d!.toISOString()).toBe("2026-06-04T10:00:00.000Z");
  });

  it("normalizes space-separated datetimes as UTC", () => {
    const d = parseApiUtcTimestamp("2026-06-04 10:00:00");
    expect(d!.toISOString()).toBe("2026-06-04T10:00:00.000Z");
  });

  it("parses strings that already include Z", () => {
    const d = parseApiUtcTimestamp("2026-06-04T10:00:00Z");
    expect(d!.toISOString()).toBe("2026-06-04T10:00:00.000Z");
  });

  it("parses strings with numeric offset", () => {
    const d = parseApiUtcTimestamp("2026-06-04T18:00:00+08:00");
    expect(d!.toISOString()).toBe("2026-06-04T10:00:00.000Z");
  });

  it("returns null for empty or invalid input", () => {
    expect(parseApiUtcTimestamp("")).toBeNull();
    expect(parseApiUtcTimestamp("not-a-date")).toBeNull();
  });
});

describe("formatRunTimestamp", () => {
  const localeOptions: Intl.DateTimeFormatOptions = {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  };

  it("formats naive UTC as local wall time of the UTC instant", () => {
    const iso = "2026-06-04T10:00:00";
    const formatted = formatRunTimestamp(iso, "completed");
    const d = parseApiUtcTimestamp(iso)!;
    const expected = `Completed ${d.toLocaleString(undefined, localeOptions)}`;
    expect(formatted).toBe(expected);

    // Regression: must not treat the naive API string as local wall time.
    // (On UTC hosts the wrong and correct parses coincide, so skip there.)
    const asLocalWall = new Date(iso);
    if (asLocalWall.getTime() !== d.getTime()) {
      expect(formatted).not.toBe(
        `Completed ${asLocalWall.toLocaleString(undefined, localeOptions)}`
      );
    }
  });

  it("returns placeholder when iso is missing", () => {
    expect(formatRunTimestamp(null, "completed")).toBe("Completed —");
    expect(formatRunTimestamp(undefined, "started")).toBe("Started —");
  });
});

describe("formatDurationMinutes", () => {
  it("computes duration from naive UTC instants", () => {
    expect(
      formatDurationMinutes("2026-06-04T10:00:00", "2026-06-04T10:45:00")
    ).toBe("45min");
  });

  it("returns null when start or end is missing", () => {
    expect(formatDurationMinutes(null, "2026-06-04T11:00:00")).toBeNull();
    expect(formatDurationMinutes("2026-06-04T10:00:00", null)).toBeNull();
  });
});

describe("formatElapsedSinceStart", () => {
  it("formats elapsed minutes from a naive UTC start", () => {
    const nowMs = Date.parse("2026-06-04T10:12:00Z");
    expect(formatElapsedSinceStart("2026-06-04T10:00:00", nowMs)).toBe("12min");
  });

  it("computes elapsed from naive UTC start_dt against a fixed now", () => {
    const nowMs = Date.parse("2026-06-04T10:20:00Z");
    expect(formatElapsedSinceStart("2026-06-04T10:00:00", nowMs)).toBe("20min");
  });

  it("parses start_dt with timezone suffix as UTC", () => {
    const nowMs = Date.parse("2026-06-04T10:20:00Z");
    expect(formatElapsedSinceStart("2026-06-04T10:00:00Z", nowMs)).toBe("20min");
  });

  it("does not add timezone offset for naive UTC start_dt (UTC+8 regression)", () => {
    const nowMs = Date.parse("2026-06-04T02:30:00Z");
    expect(formatElapsedSinceStart("2026-06-04T02:00:00", nowMs)).toBe("30min");
  });
});
