import {
  classifyTest,
  filterPromptsForFullyCompleteTests,
  isPromptErrored,
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
});
