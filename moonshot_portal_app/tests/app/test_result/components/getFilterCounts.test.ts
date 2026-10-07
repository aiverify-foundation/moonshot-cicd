import {
  getFacetedFilterCounts,
  getGlobalFilterCounts,
  type FilterState,
} from "@/app/test_result/components/getFilterCounts"
import type { TestResultTableRow } from "@/app/test_result/components/TestResultTable"

function row(
  overrides: Partial<TestResultTableRow> & Pick<TestResultTableRow, "id" | "test">
): TestResultTableRow {
  return {
    prompt: "",
    target: "",
    response: "",
    evaluation: "{'score': 1}",
    score: 1,
    yourVerdict: null,
    note: "",
    bundle: "b",
    graderLogic: "",
    ...overrides,
  }
}

describe("getFilterCounts", () => {
  const data: TestResultTableRow[] = [
    row({ id: "1", test: "TestA", evaluation: "{'score': 1}", score: 1 }),
    row({ id: "2", test: "TestA", evaluation: "{'score': 0}", score: 0 }),
    row({ id: "3", test: "TestB", evaluation: "{'score': 1}", score: 1 }),
    row({
      id: "4",
      test: "TestB",
      evaluation: "{'score': 0}",
      score: 0,
      yourVerdict: "disagree",
    }),
  ]

  // Labels mirror evaluationDisplayLabel for score 1/0 Agree/Disagree
  const evalLabels = new Map([
    ["1", "Agree"],
    ["2", "Disagree"],
    ["3", "Agree"],
    ["4", "Disagree"],
  ])

  const allSelected: FilterState = {
    tests: new Set(["TestA", "TestB"]),
    evaluations: new Set(["Agree", "Disagree"]),
    yourVerdicts: new Set(["agree", "disagree", null]),
    adjusted: new Set(["adjusted", "not adjusted"]),
  }

  describe("getGlobalFilterCounts", () => {
    it("counts over all rows regardless of filters", () => {
      const counts = getGlobalFilterCounts(data, evalLabels)

      expect(counts.testCounts.get("TestA")).toBe(2)
      expect(counts.testCounts.get("TestB")).toBe(2)
      expect(counts.evaluationCounts.get("Agree")).toBe(2)
      expect(counts.evaluationCounts.get("Disagree")).toBe(2)
      expect(counts.yourVerdictCounts.get(null)).toBe(3)
      expect(counts.yourVerdictCounts.get("disagree")).toBe(1)
      expect(counts.adjustedCounts.get("adjusted")).toBe(1)
      expect(counts.adjustedCounts.get("not adjusted")).toBe(3)
    })
  })

  describe("getFacetedFilterCounts", () => {
    it("matches global counts when all options are selected", () => {
      const faceted = getFacetedFilterCounts(data, allSelected, "", evalLabels)
      const global = getGlobalFilterCounts(data, evalLabels)

      expect(faceted.testCounts).toEqual(global.testCounts)
      expect(faceted.evaluationCounts).toEqual(global.evaluationCounts)
      expect(faceted.yourVerdictCounts).toEqual(global.yourVerdictCounts)
      expect(faceted.adjustedCounts).toEqual(global.adjustedCounts)
    })

    it("updates Evaluation counts when Test selection is narrowed", () => {
      const filters: FilterState = {
        ...allSelected,
        tests: new Set(["TestA"]),
      }

      const counts = getFacetedFilterCounts(data, filters, "", evalLabels)

      // Evaluation facet applies Test filter (excludes only itself)
      expect(counts.evaluationCounts.get("Agree")).toBe(1)
      expect(counts.evaluationCounts.get("Disagree")).toBe(1)

      // Test facet ignores its own filter → full histogram given other filters
      expect(counts.testCounts.get("TestA")).toBe(2)
      expect(counts.testCounts.get("TestB")).toBe(2)
    })

    it("updates Test counts when Evaluation selection is narrowed", () => {
      const filters: FilterState = {
        ...allSelected,
        evaluations: new Set(["Agree"]),
      }

      const counts = getFacetedFilterCounts(data, filters, "", evalLabels)

      expect(counts.testCounts.get("TestA")).toBe(1)
      expect(counts.testCounts.get("TestB")).toBe(1)

      // Evaluation facet ignores its own filter → still full histogram
      expect(counts.evaluationCounts.get("Agree")).toBe(2)
      expect(counts.evaluationCounts.get("Disagree")).toBe(2)
    })

    it("applies search when computing faceted counts", () => {
      const counts = getFacetedFilterCounts(
        data,
        allSelected,
        "TestA",
        evalLabels
      )

      expect(counts.evaluationCounts.get("Agree")).toBe(1)
      expect(counts.evaluationCounts.get("Disagree")).toBe(1)
      expect(counts.testCounts.get("TestA")).toBe(2)
      expect(counts.testCounts.has("TestB")).toBe(false)
    })
  })
})
