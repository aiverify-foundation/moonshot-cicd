import type { TestResultTableRow } from "./TestResultTable"

export type FilterState = {
  tests: Set<string>
  evaluations: Set<string>
  yourVerdicts: Set<string | null>
  adjusted: Set<string>
}

export type FilterCounts = {
  testCounts: Map<string, number>
  evaluationCounts: Map<string, number>
  yourVerdictCounts: Map<string | null, number>
  adjustedCounts: Map<string, number>
}

export type FacetDimension = "tests" | "evaluations" | "yourVerdicts" | "adjusted"

function adjustedKey(row: TestResultTableRow): string {
  return row.yourVerdict === "disagree" ? "adjusted" : "not adjusted"
}

function matchesSearch(
  row: TestResultTableRow,
  searchTerm: string,
  evalLabel: string
): boolean {
  if (!searchTerm.trim()) return true

  const searchLower = searchTerm.toLowerCase().trim()
  const yourVerdictDisplay =
    row.yourVerdict === "agree"
      ? "agree"
      : row.yourVerdict === "disagree"
        ? "disagree"
        : "not set"

  const searchableText = [
    row.test,
    row.prompt,
    row.target,
    row.response,
    row.evaluation,
    evalLabel,
    yourVerdictDisplay,
    row.note,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase()

  return searchableText.includes(searchLower)
}

function matchesFilters(
  row: TestResultTableRow,
  filters: FilterState,
  evalLabel: string,
  skip: FacetDimension | null
): boolean {
  if (skip !== "tests" && !filters.tests.has(row.test)) return false
  if (skip !== "evaluations" && !filters.evaluations.has(evalLabel)) return false
  if (skip !== "yourVerdicts" && !filters.yourVerdicts.has(row.yourVerdict))
    return false
  if (skip !== "adjusted") {
    const key = adjustedKey(row)
    if (!filters.adjusted.has(key)) return false
  }
  return true
}

function emptyCounts(): FilterCounts {
  return {
    testCounts: new Map(),
    evaluationCounts: new Map(),
    yourVerdictCounts: new Map(),
    adjustedCounts: new Map(),
  }
}

function incrementCounts(
  counts: FilterCounts,
  row: TestResultTableRow,
  evalLabel: string
): void {
  counts.testCounts.set(row.test, (counts.testCounts.get(row.test) || 0) + 1)
  counts.evaluationCounts.set(
    evalLabel,
    (counts.evaluationCounts.get(evalLabel) || 0) + 1
  )
  counts.yourVerdictCounts.set(
    row.yourVerdict,
    (counts.yourVerdictCounts.get(row.yourVerdict) || 0) + 1
  )
  const key = adjustedKey(row)
  counts.adjustedCounts.set(key, (counts.adjustedCounts.get(key) || 0) + 1)
}

/** Histogram over all rows (legacy behavior; ignores active filters). */
export function getGlobalFilterCounts(
  rows: TestResultTableRow[],
  evalLabels: Map<string, string>
): FilterCounts {
  const counts = emptyCounts()
  for (const row of rows) {
    const evalLabel = evalLabels.get(row.id) ?? ""
    incrementCounts(counts, row, evalLabel)
  }
  return counts
}

/**
 * Amazon-style faceted counts: for each dimension D, count options over rows
 * that match all active filters except D (plus search).
 */
export function getFacetedFilterCounts(
  rows: TestResultTableRow[],
  filters: FilterState,
  searchTerm: string,
  evalLabels: Map<string, string>
): FilterCounts {
  const counts = emptyCounts()
  const dimensions: FacetDimension[] = [
    "tests",
    "evaluations",
    "yourVerdicts",
    "adjusted",
  ]

  // One pass per filter group: counts for that group ignore its own filter.
  for (const dimension of dimensions) {
    for (const row of rows) {
      const evalLabel = evalLabels.get(row.id) ?? ""
      // Keep other active filters; skip the filter for this dimension.
      if (!matchesFilters(row, filters, evalLabel, dimension)) continue
      if (!matchesSearch(row, searchTerm, evalLabel)) continue

      // Tally only the current dimension so each group's counts stay independent.
      if (dimension === "tests") {
        counts.testCounts.set(
          row.test,
          (counts.testCounts.get(row.test) || 0) + 1
        )
      } else if (dimension === "evaluations") {
        counts.evaluationCounts.set(
          evalLabel,
          (counts.evaluationCounts.get(evalLabel) || 0) + 1
        )
      } else if (dimension === "yourVerdicts") {
        counts.yourVerdictCounts.set(
          row.yourVerdict,
          (counts.yourVerdictCounts.get(row.yourVerdict) || 0) + 1
        )
      } else {
        // "adjusted" when verdict is disagree; otherwise "not adjusted"
        const key = adjustedKey(row)
        counts.adjustedCounts.set(
          key,
          (counts.adjustedCounts.get(key) || 0) + 1
        )
      }
    }
  }

  return counts
}
