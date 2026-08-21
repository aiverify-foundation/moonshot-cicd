import {
  BenchmarkRunTestPrompt,
  BenchmarkRunTestStatusSummary,
} from "@/lib/api";

export type TestCompletionState =
  | "fully_complete"
  | "completed_with_errors"
  | "incomplete";

export function testStatusByTestId(
  rows: BenchmarkRunTestStatusSummary[]
): Map<number, string> {
  const map = new Map<number, string>();
  for (const row of rows) {
    if (row.status) map.set(row.test_id, row.status);
  }
  return map;
}

export function promptsForTest(
  prompts: BenchmarkRunTestPrompt[],
  testId: number
): BenchmarkRunTestPrompt[] {
  return prompts.filter((p) => p.test_id === testId);
}

export function isPromptErrored(p: BenchmarkRunTestPrompt): boolean {
  return p.status?.toLowerCase() === "error";
}

export function runHasPromptErrors(prompts: BenchmarkRunTestPrompt[]): boolean {
  return prompts.some(isPromptErrored);
}

export function classifyTest(
  testPrompts: BenchmarkRunTestPrompt[],
  testStatus?: string | null
): TestCompletionState {
  if (testPrompts.length === 0) return "incomplete";

  const promptStatuses = testPrompts.map((p) => p.status?.toLowerCase() ?? "");
  const normalizedTestStatus = testStatus?.toLowerCase() ?? "";

  if (promptStatuses.some((s) => s === "pending" || s === "running")) {
    return "incomplete";
  }
  if (promptStatuses.some((s) => s === "error")) {
    return "completed_with_errors";
  }
  if (
    normalizedTestStatus === "completed_with_errors" ||
    normalizedTestStatus === "failed"
  ) {
    return "completed_with_errors";
  }
  if (
    promptStatuses.every((s) => s === "completed") &&
    (normalizedTestStatus === "" || normalizedTestStatus === "completed")
  ) {
    return "fully_complete";
  }
  return "incomplete";
}

export function filterPromptsForFullyCompleteTests(
  prompts: BenchmarkRunTestPrompt[],
  testStatusById: Map<number, string>
): BenchmarkRunTestPrompt[] {
  const byTest = new Map<number, BenchmarkRunTestPrompt[]>();
  for (const p of prompts) {
    if (p.test_id == null) continue;
    if (!byTest.has(p.test_id)) byTest.set(p.test_id, []);
    byTest.get(p.test_id)!.push(p);
  }

  const allowedTestIds = new Set<number>();
  for (const [testId, testPrompts] of byTest) {
    if (
      classifyTest(testPrompts, testStatusById.get(testId)) === "fully_complete"
    ) {
      allowedTestIds.add(testId);
    }
  }

  return prompts.filter((p) => p.test_id != null && allowedTestIds.has(p.test_id));
}
