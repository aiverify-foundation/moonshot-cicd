import {
  mapRunStatusLabel,
  runStatusBadgeClassName,
} from "@/app/test_result/components/runStatusDisplay";
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

describe("runStatusDisplay", () => {
  it("maps failed run with prompt errors to Completed with Errors", () => {
    const prompts = [
      prompt({ run_test_id: 1, prompt_id: 1, status: "error" }),
    ];
    expect(mapRunStatusLabel("failed", prompts)).toBe("Completed with Errors");
    expect(runStatusBadgeClassName("failed", prompts)).toContain("red");
  });

  it("maps completed run to Complete", () => {
    expect(mapRunStatusLabel("completed", [])).toBe("Complete");
    expect(runStatusBadgeClassName("completed", [])).toContain("green");
  });
});
