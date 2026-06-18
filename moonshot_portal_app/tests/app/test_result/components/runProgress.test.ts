import {
  groupTestProgressByBundle,
  isPromptCompleted,
  testStartDtMapFromRunStatus,
} from "@/app/test_result/components/runProgress";
import { BenchmarkRunTestPrompt } from "@/lib/api";

function prompt(
  overrides: Partial<BenchmarkRunTestPrompt> & Pick<BenchmarkRunTestPrompt, "run_test_id" | "prompt_id">
): BenchmarkRunTestPrompt {
  return {
    status: "pending",
    target: "",
    ...overrides,
  };
}

describe("isPromptCompleted", () => {
  it("returns true for completed status", () => {
    expect(isPromptCompleted(prompt({ run_test_id: 1, prompt_id: 1, status: "completed" }))).toBe(
      true
    );
  });

  it("returns true when prediction_result is set", () => {
    expect(
      isPromptCompleted(
        prompt({ run_test_id: 1, prompt_id: 1, status: "pending", prediction_result: "ok" })
      )
    ).toBe(true);
  });

  it("returns false for pending prompts", () => {
    expect(isPromptCompleted(prompt({ run_test_id: 1, prompt_id: 1, status: "pending" }))).toBe(
      false
    );
  });
});

describe("testStartDtMapFromRunStatus", () => {
  it("maps test_id to start_dt", () => {
    const map = testStartDtMapFromRunStatus([
      { test_id: 10, start_dt: "2026-06-04T10:00:00" },
      { test_id: 20, start_dt: null },
    ]);
    expect(map.get(10)).toBe("2026-06-04T10:00:00");
    expect(map.get(20)).toBeNull();
  });
});

describe("groupTestProgressByBundle", () => {
  it("groups tests under bundle names", () => {
    const prompts = [
      prompt({ run_test_id: 1, test_id: 10, prompt_id: 1, test_name: "Beta", status: "completed" }),
      prompt({ run_test_id: 1, test_id: 10, prompt_id: 2, test_name: "Beta", status: "pending" }),
      prompt({ run_test_id: 2, test_id: 20, prompt_id: 3, test_name: "Alpha", status: "completed" }),
    ];

    const testStartDtByTestId = testStartDtMapFromRunStatus([
      { test_id: 10, start_dt: "2026-06-04T10:00:00" },
      { test_id: 20, start_dt: null },
    ]);

    const groups = groupTestProgressByBundle(
      prompts,
      [
        {
          test_bundle_id: 1,
          name: "Safety Bundle",
          system_name: "safety",
          test_ids: [10, 20],
        },
      ],
      testStartDtByTestId
    );

    expect(groups).toHaveLength(1);
    expect(groups[0].bundleName).toBe("Safety Bundle");
    expect(groups[0].tests.map((t) => t.testName)).toEqual(["Alpha", "Beta"]);
    expect(groups[0].tests[0].completedPrompts).toBe(1);
    expect(groups[0].tests[0].startDt).toBeNull();
    expect(groups[0].tests[1].completedPrompts).toBe(1);
    expect(groups[0].tests[1].startDt).toBe("2026-06-04T10:00:00");
  });

  it("falls back to All results when there are no bundles", () => {
    const prompts = [
      prompt({ run_test_id: 1, test_id: 10, prompt_id: 1, test_name: "Only Test", status: "pending" }),
    ];

    const groups = groupTestProgressByBundle(prompts, []);

    expect(groups).toHaveLength(1);
    expect(groups[0].bundleName).toBe("All results");
    expect(groups[0].tests[0].testName).toBe("Only Test");
    expect(groups[0].tests[0].startDt).toBeNull();
  });
});
