import { buildBundleChartResult } from "@/app/test_result/components/TestResultBundle";
import type { BenchmarkRunTestPrompt } from "@/lib/api";
import type { TestResultTableRow } from "@/app/test_result/components/TestResultTable";

function prompt(
  overrides: Partial<BenchmarkRunTestPrompt> &
    Pick<BenchmarkRunTestPrompt, "run_test_id" | "prompt_id">
): BenchmarkRunTestPrompt {
  return {
    status: "pending",
    target: "",
    ...overrides,
  };
}

function row(overrides: Partial<TestResultTableRow>): TestResultTableRow {
  return {
    id: "r-1",
    test: "Test A",
    prompt: "p",
    target: "t",
    response: "r",
    evaluation: "e",
    score: 1,
    yourVerdict: null,
    note: "",
    bundle: "B",
    graderLogic: "",
    ...overrides,
  };
}

describe("buildBundleChartResult", () => {
  it("puts fully complete tests in chartBars and others in incompleteTests", () => {
    const prompts = [
      prompt({
        run_test_id: 1,
        prompt_id: 1,
        test_id: 10,
        test_name: "Clean Test",
        status: "completed",
        score: 1,
      }),
      prompt({
        run_test_id: 2,
        prompt_id: 2,
        test_id: 20,
        test_name: "Dirty Test",
        status: "error",
        score: 0,
      }),
    ];
    const tableData = [
      row({ id: "r-1", test: "Clean Test", test_id: 10, score: 1 }),
      row({ id: "r-2", test: "Dirty Test", test_id: 20, score: 0, isPromptError: true }),
    ];
    const result = buildBundleChartResult(
      prompts,
      tableData,
      [
        { test_id: 10, status: "completed" },
        { test_id: 20, status: "completed_with_errors" },
      ],
      null
    );
    expect(result.chartBars).toHaveLength(1);
    expect(result.chartBars[0].test_name).toBe("Clean Test");
    expect(result.incompleteTests).toEqual(["Dirty Test"]);
  });
});
