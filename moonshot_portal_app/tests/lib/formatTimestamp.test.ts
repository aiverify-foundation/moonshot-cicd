import {
  formatDurationMinutes,
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
  it("formats naive UTC as local time in a fixed timezone", () => {
    const formatted = formatRunTimestamp("2026-06-04T10:00:00", "completed");
    const d = parseApiUtcTimestamp("2026-06-04T10:00:00")!;
    const expected = `Completed ${d.toLocaleString("en-US", {
      timeZone: "Asia/Singapore",
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    })}`;
    expect(formatted).toBe(expected);
    expect(formatted).toContain("6:00");
    expect(formatted).not.toContain("10:00");
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
