import {
  BenchmarkRunResultsBundleSummary,
  BenchmarkRunTestPrompt,
  BenchmarkRunTestStatusSummary,
} from "@/lib/api";
import { isPromptErrored } from "./testCompletion";

/** True when a prompt succeeded (not errored) for success-only progress counts. */
export function isPromptCompleted(p: BenchmarkRunTestPrompt): boolean {
  const status = p.status?.toLowerCase() ?? "";
  if (status === "error") return false;
  if (status === "completed") return true;
  if (p.prediction_result != null && p.prediction_result !== "") return true;
  return false;
}

function testKeyForPrompt(prompt: BenchmarkRunTestPrompt): number {
  return prompt.test_id ?? prompt.run_test_id;
}

export interface TestTiming {
  startDt: string | null;
  endDt: string | null;
}

export function testTimingMapFromRunStatus(
  rows: BenchmarkRunTestStatusSummary[]
): Map<number, TestTiming> {
  const map = new Map<number, TestTiming>();
  for (const row of rows) {
    map.set(row.test_id, {
      startDt: row.start_dt ?? null,
      endDt: row.end_dt ?? null,
    });
  }
  return map;
}

export interface TestProgressItem {
  testId: number;
  testName: string;
  completedPrompts: number;
  erroredPrompts: number;
  totalPrompts: number;
  progressPercent: number;
  startDt: string | null;
  endDt: string | null;
}

export interface BundleTestProgressGroup {
  bundleId: number | null;
  bundleName: string;
  tests: TestProgressItem[];
}

function computeTestProgressItem(
  testId: number,
  testName: string,
  prompts: BenchmarkRunTestPrompt[],
  timing: TestTiming
): TestProgressItem {
  const completedPrompts = prompts.filter(isPromptCompleted).length;
  const erroredPrompts = prompts.filter(isPromptErrored).length;
  const totalPrompts = prompts.length;
  const processedPrompts = completedPrompts + erroredPrompts;
  const progressPercent =
    totalPrompts > 0
      ? Math.min(100, Math.round((processedPrompts / totalPrompts) * 100))
      : 0;

  return {
    testId,
    testName,
    completedPrompts,
    erroredPrompts,
    totalPrompts,
    progressPercent,
    startDt: timing.startDt,
    endDt: timing.endDt,
  };
}

export function groupTestProgressByBundle(
  prompts: BenchmarkRunTestPrompt[],
  bundles: BenchmarkRunResultsBundleSummary[],
  testTimingByTestId: Map<number, TestTiming> = new Map()
): BundleTestProgressGroup[] {
  const promptsByTestId = new Map<number, BenchmarkRunTestPrompt[]>();
  const testNames = new Map<number, string>();

  for (const prompt of prompts) {
    const testId = testKeyForPrompt(prompt);
    if (!promptsByTestId.has(testId)) promptsByTestId.set(testId, []);
    promptsByTestId.get(testId)!.push(prompt);
    const name = (prompt.test_name ?? "Unknown").trim() || "Unknown";
    testNames.set(testId, name);
  }

  const buildTestItem = (testId: number): TestProgressItem =>
    computeTestProgressItem(
      testId,
      testNames.get(testId) ?? "Unknown",
      promptsByTestId.get(testId) ?? [],
      testTimingByTestId.get(testId) ?? { startDt: null, endDt: null }
    );

  const sortTests = (tests: TestProgressItem[]) =>
    [...tests].sort((a, b) => a.testName.localeCompare(b.testName));

  if (bundles.length === 0) {
    const allTestIds = [...promptsByTestId.keys()];
    return [
      {
        bundleId: null,
        bundleName: "All results",
        tests: sortTests(allTestIds.map(buildTestItem)),
      },
    ];
  }

  const assignedTestIds = new Set<number>();
  const groups: BundleTestProgressGroup[] = [];

  for (const bundle of bundles) {
    const tests = bundle.test_ids
      .filter((id) => promptsByTestId.has(id))
      .map(buildTestItem);
    tests.forEach((t) => assignedTestIds.add(t.testId));
    if (tests.length === 0) continue;
    groups.push({
      bundleId: bundle.test_bundle_id,
      bundleName: bundle.name,
      tests: sortTests(tests),
    });
  }

  const unassigned = [...promptsByTestId.keys()].filter((id) => !assignedTestIds.has(id));
  if (unassigned.length > 0) {
    groups.push({
      bundleId: null,
      bundleName: "Other",
      tests: sortTests(unassigned.map(buildTestItem)),
    });
  }

  return groups;
}
