import {
  classifyTest,
  filterPromptsForFullyCompleteTests,
  isPromptBulkRegeneratable,
  isPromptErrored,
  isPromptUnknownEvaluation,
  runHasBulkRegenerateTargets,
  runHasIncompleteWork,
  runHasPromptErrors,
  testStatusByTestId,
} from "@/app/test_result/components/testCompletion";
import { BenchmarkRunTestPrompt } from "@/lib/api";

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

describe("classifyTest", () => {
  it("returns fully_complete when all prompts completed", () => {
    const prompts = [
      prompt({ run_test_id: 1, prompt_id: 1, test_id: 10, status: "completed" }),
      prompt({ run_test_id: 1, prompt_id: 2, test_id: 10, status: "completed" }),
    ];
    expect(classifyTest(prompts, "completed")).toBe("fully_complete");
  });

  it("returns completed_with_errors when any prompt errored", () => {
    const prompts = [
      prompt({ run_test_id: 1, prompt_id: 1, test_id: 10, status: "completed" }),
      prompt({ run_test_id: 1, prompt_id: 2, test_id: 10, status: "error" }),
    ];
    expect(classifyTest(prompts, "completed_with_errors")).toBe(
      "completed_with_errors"
    );
  });

  it("returns incomplete when prompts still pending", () => {
    const prompts = [
      prompt({ run_test_id: 1, prompt_id: 1, test_id: 10, status: "completed" }),
      prompt({ run_test_id: 1, prompt_id: 2, test_id: 10, status: "pending" }),
    ];
    expect(classifyTest(prompts, "in_progress")).toBe("incomplete");
  });
});

describe("filterPromptsForFullyCompleteTests", () => {
  it("excludes prompts from errored tests", () => {
    const prompts = [
      prompt({ run_test_id: 1, prompt_id: 1, test_id: 10, status: "completed" }),
      prompt({ run_test_id: 1, prompt_id: 2, test_id: 20, status: "error" }),
    ];
    const statusMap = testStatusByTestId([
      { test_id: 10, status: "completed" },
      { test_id: 20, status: "completed_with_errors" },
    ]);
    const filtered = filterPromptsForFullyCompleteTests(prompts, statusMap);
    expect(filtered).toHaveLength(1);
    expect(filtered[0].test_id).toBe(10);
  });
});

describe("runHasPromptErrors", () => {
  it("detects error prompts", () => {
    expect(
      runHasPromptErrors([
        prompt({ run_test_id: 1, prompt_id: 1, status: "completed" }),
        prompt({ run_test_id: 1, prompt_id: 2, status: "error" }),
      ])
    ).toBe(true);
    expect(isPromptErrored(prompt({ run_test_id: 1, prompt_id: 1, status: "error" }))).toBe(
      true
    );
  });

  it("does not treat completed unknown evaluation as an error", () => {
    expect(
      runHasPromptErrors([
        prompt({
          run_test_id: 1,
          prompt_id: 1,
          status: "completed",
          evaluation_prediction_result:
            '{"score": 0, "evaluated_response": "unknown"}',
        }),
      ])
    ).toBe(false);
  });
});

describe("runHasBulkRegenerateTargets", () => {
  it("detects error prompts", () => {
    expect(
      isPromptBulkRegeneratable(
        prompt({ run_test_id: 1, prompt_id: 1, status: "error" })
      )
    ).toBe(true);
  });

  it("detects completed unknown evaluations", () => {
    const unknown = prompt({
      run_test_id: 1,
      prompt_id: 1,
      status: "completed",
      evaluation_prediction_result:
        '{"score": 0, "evaluated_response": "unknown"}',
    });
    expect(isPromptUnknownEvaluation(unknown)).toBe(true);
    expect(isPromptBulkRegeneratable(unknown)).toBe(true);
    expect(runHasBulkRegenerateTargets([unknown])).toBe(true);
  });

  it("detects unknown from Python dict-repr evaluation blobs", () => {
    const unknown = prompt({
      run_test_id: 1,
      prompt_id: 1,
      status: "completed",
      score: 0,
      evaluation_prediction_result:
        "{'score': 0.0, 'evaluated_response': 'unknown', 'accuracy': False}",
    });
    expect(isPromptUnknownEvaluation(unknown)).toBe(true);
    expect(runHasBulkRegenerateTargets([unknown])).toBe(true);
  });

  it("ignores completed non-unknown evaluations", () => {
    const safe = prompt({
      run_test_id: 1,
      prompt_id: 1,
      status: "completed",
      evaluation_prediction_result: '{"score": 1, "evaluated_response": "safe"}',
    });
    expect(isPromptUnknownEvaluation(safe)).toBe(false);
    expect(runHasBulkRegenerateTargets([safe])).toBe(false);
  });
});

describe("runHasIncompleteWork", () => {
  it("is true when any prompt is pending or running", () => {
    expect(
      runHasIncompleteWork(
        [prompt({ run_test_id: 1, prompt_id: 1, status: "pending" })],
        []
      )
    ).toBe(true);
    expect(
      runHasIncompleteWork(
        [prompt({ run_test_id: 1, prompt_id: 1, status: "running" })],
        []
      )
    ).toBe(true);
  });

  it("is true when a test is non-terminal", () => {
    expect(
      runHasIncompleteWork(
        [prompt({ run_test_id: 1, prompt_id: 1, status: "completed" })],
        [{ test_id: 10, status: "in_progress" }]
      )
    ).toBe(true);
  });

  it("is false when everything is terminal", () => {
    expect(
      runHasIncompleteWork(
        [prompt({ run_test_id: 1, prompt_id: 1, status: "completed" })],
        [{ test_id: 10, status: "completed" }]
      )
    ).toBe(false);
  });
});
