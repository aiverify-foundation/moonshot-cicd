"use client";

import React from "react";
import {
  BenchmarkRunResultsBundleSummary,
  BenchmarkRunTestPrompt,
  BenchmarkRunTestStatusSummary,
} from "@/lib/api";
import { formatElapsedSinceStart } from "@/lib/formatTimestamp";
import { testStartDtMapFromRunStatus } from "./runProgress";
import {
  classifyTest,
  isPromptErrored,
  testStatusByTestId,
} from "./testCompletion";

export interface ErroredTestSummary {
  testId: number;
  testName: string;
  completedPrompts: number;
  totalPrompts: number;
  erroredPrompts: number;
  startDt: string | null;
}

export interface BundleErroredTestsGroup {
  bundleName: string;
  tests: ErroredTestSummary[];
}

function buildErroredTestSummary(
  testId: number,
  testName: string,
  testPrompts: BenchmarkRunTestPrompt[],
  startDt: string | null
): ErroredTestSummary {
  const erroredPrompts = testPrompts.filter(isPromptErrored).length;
  const completedPrompts = testPrompts.filter(
    (p) => p.status?.toLowerCase() === "completed"
  ).length;
  return {
    testId,
    testName,
    completedPrompts,
    totalPrompts: testPrompts.length,
    erroredPrompts,
    startDt,
  };
}

export function groupErroredTestsByBundle(
  prompts: BenchmarkRunTestPrompt[],
  bundles: BenchmarkRunResultsBundleSummary[],
  testRunStatus: BenchmarkRunTestStatusSummary[]
): BundleErroredTestsGroup[] {
  const statusByTestId = testStatusByTestId(testRunStatus);
  const startDtByTestId = testStartDtMapFromRunStatus(testRunStatus);

  const testNames = new Map<number, string>();
  const promptsByTestId = new Map<number, BenchmarkRunTestPrompt[]>();
  for (const p of prompts) {
    if (p.test_id == null) continue;
    if (!promptsByTestId.has(p.test_id)) promptsByTestId.set(p.test_id, []);
    promptsByTestId.get(p.test_id)!.push(p);
    testNames.set(p.test_id, (p.test_name ?? "Unknown").trim() || "Unknown");
  }

  const erroredTestIds = [...promptsByTestId.keys()].filter((testId) => {
    const testPrompts = promptsByTestId.get(testId) ?? [];
    return (
      classifyTest(testPrompts, statusByTestId.get(testId)) ===
      "completed_with_errors"
    );
  });

  if (erroredTestIds.length === 0) return [];

  const buildGroup = (
    bundleName: string,
    testIds: number[]
  ): BundleErroredTestsGroup | null => {
    const tests = testIds
      .filter((id) => erroredTestIds.includes(id))
      .map((testId) =>
        buildErroredTestSummary(
          testId,
          testNames.get(testId) ?? "Unknown",
          promptsByTestId.get(testId) ?? [],
          startDtByTestId.get(testId) ?? null
        )
      )
      .sort((a, b) => a.testName.localeCompare(b.testName));
    if (tests.length === 0) return null;
    return { bundleName, tests };
  };

  if (bundles.length === 0) {
    const group = buildGroup("All results", erroredTestIds);
    return group ? [group] : [];
  }

  const groups: BundleErroredTestsGroup[] = [];
  const assigned = new Set<number>();
  for (const bundle of bundles) {
    const group = buildGroup(bundle.name, bundle.test_ids);
    if (group) {
      group.tests.forEach((t) => assigned.add(t.testId));
      groups.push(group);
    }
  }

  const unassigned = erroredTestIds.filter((id) => !assigned.has(id));
  if (unassigned.length > 0) {
    const other = buildGroup("Other", unassigned);
    if (other) groups.push(other);
  }

  return groups;
}

function SegmentedProgressBar({
  completed,
  errored,
  total,
}: {
  completed: number;
  errored: number;
  total: number;
}) {
  if (total <= 0) {
    return <div className="flex-1 h-4 bg-slate-200 rounded-full" />;
  }
  const completedPct = (completed / total) * 100;
  const erroredPct = (errored / total) * 100;
  return (
    <div className="flex flex-1 h-4 rounded-full overflow-hidden bg-slate-200">
      {completedPct > 0 ? (
        <div className="bg-blue-500 h-full" style={{ width: `${completedPct}%` }} />
      ) : null}
      {erroredPct > 0 ? (
        <div className="bg-red-500 h-full" style={{ width: `${erroredPct}%` }} />
      ) : null}
    </div>
  );
}

function ErroredTestCard({ test }: { test: ErroredTestSummary }) {
  const elapsed = test.startDt
    ? formatElapsedSinceStart(test.startDt, Date.now())
    : null;

  return (
    <div className="bg-slate-50 border border-slate-200 flex items-start p-2 rounded-lg w-full">
      <div className="flex flex-1 flex-col gap-2 items-start min-w-0">
        <p className="font-semibold text-[14px] text-slate-700 w-full">{test.testName}</p>
        <div className="flex gap-4 items-center pb-1 pt-2 w-full">
          <SegmentedProgressBar
            completed={test.completedPrompts}
            errored={test.erroredPrompts}
            total={test.totalPrompts}
          />
          <p className="font-medium text-[14px] text-slate-700 whitespace-nowrap shrink-0">
            {test.completedPrompts.toLocaleString()} / {test.totalPrompts.toLocaleString()} prompts
          </p>
        </div>
        <p className="font-medium text-[14px] text-slate-700">
          {elapsed ? `Time elapsed: ${elapsed}` : "Not started"}
        </p>
        <p className="font-medium text-[14px] text-red-700">
          {test.erroredPrompts.toLocaleString()} prompt(s) Failed
        </p>
      </div>
    </div>
  );
}

interface TestResultCompletedWithErrorsProps {
  groups: BundleErroredTestsGroup[];
}

export default function TestResultCompletedWithErrors({
  groups,
}: TestResultCompletedWithErrorsProps) {
  if (groups.length === 0) return null;

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2">
        <p className="font-semibold text-[14px] text-red-800">
          Test completed with errors
        </p>
      </div>

      {groups.map((group) => (
        <div key={group.bundleName} className="flex flex-col gap-3">
          <p className="font-semibold text-[14px] text-slate-700">
            Tests completed with errors — {group.bundleName}
          </p>
          <div className="flex flex-col gap-3">
            {group.tests.map((test) => (
              <ErroredTestCard key={test.testId} test={test} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

/** Exported for tests */
export { buildErroredTestSummary };
