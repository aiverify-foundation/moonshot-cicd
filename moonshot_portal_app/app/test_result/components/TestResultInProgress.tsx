"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Progress } from "@/components/ui/progress";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  BenchmarkRunResultsBundleSummary,
  BenchmarkRunTestPrompt,
  BenchmarkRunTestStatusSummary,
} from "@/lib/api";
import { formatElapsedSinceStart } from "@/lib/formatTimestamp";
import { cn } from "@/lib/utils";
import {
  BundleTestProgressGroup,
  groupTestProgressByBundle,
  testStartDtMapFromRunStatus,
  TestProgressItem,
} from "./runProgress";

interface TestResultInProgressProps {
  prompts: BenchmarkRunTestPrompt[];
  bundles: BenchmarkRunResultsBundleSummary[];
  testRunStatus?: BenchmarkRunTestStatusSummary[];
}

function bundleAccordionValue(group: BundleTestProgressGroup): string {
  return String(group.bundleId ?? group.bundleName);
}

function progressBarValue(test: TestProgressItem): number {
  if (test.totalPrompts === 0) return 0;
  if (test.completedPrompts === 0) return 1;
  return test.progressPercent;
}

function isTestComplete(test: TestProgressItem): boolean {
  return test.totalPrompts > 0 && test.completedPrompts === test.totalPrompts;
}

function promptLabel(test: TestProgressItem): string {
  if (test.totalPrompts === 0) return "— prompts";
  return `${test.completedPrompts.toLocaleString()} / ${test.totalPrompts.toLocaleString()} prompts`;
}

function elapsedLine(test: TestProgressItem): string {
  if (!test.startDt) return "Not started";
  const elapsed = formatElapsedSinceStart(test.startDt, Date.now());
  return elapsed ? `Time lapsed: ${elapsed}` : "Not started";
}

function TestInProgressCard({ test }: { test: TestProgressItem }) {
  return (
    <div className="bg-slate-50 border border-slate-200 flex items-start p-2 rounded-lg w-full">
      <div className="flex flex-1 flex-col gap-2 items-start min-w-0">
        <p className="font-semibold text-[14px] text-slate-700 w-full">{test.testName}</p>

        <div className="flex gap-4 items-center pb-1 pt-2 w-full">
          <Progress
            value={progressBarValue(test)}
            className={cn(
              "flex-1 h-4 bg-slate-200 rounded-full [&>div]:rounded-full",
              isTestComplete(test) ? "[&>div]:bg-green-500" : "[&>div]:bg-blue-500"
            )}
          />
          <p className="font-medium text-[14px] text-slate-700 whitespace-nowrap shrink-0">
            {promptLabel(test)}
          </p>
        </div>

        <p className="font-medium text-[14px] text-slate-700">{elapsedLine(test)}</p>
      </div>
    </div>
  );
}

function BundleProgressCard({ group }: { group: BundleTestProgressGroup }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <AccordionItem value={bundleAccordionValue(group)} className="border-0 px-3">
        <AccordionTrigger className="py-3 hover:no-underline">
          <span className="font-semibold text-[14px] text-slate-700">{group.bundleName}</span>
        </AccordionTrigger>
        <AccordionContent className="pb-3">
          <div className="flex flex-col gap-4">
            {group.tests.map((test) => (
              <TestInProgressCard key={test.testId} test={test} />
            ))}
          </div>
        </AccordionContent>
      </AccordionItem>
    </div>
  );
}

export default function TestResultInProgress({
  prompts,
  bundles,
  testRunStatus = [],
}: TestResultInProgressProps) {
  const [, setTick] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => setTick((t) => t + 1), 30_000);
    return () => window.clearInterval(interval);
  }, []);

  const testStartDtByTestId = useMemo(
    () => testStartDtMapFromRunStatus(testRunStatus),
    [testRunStatus]
  );

  const groups = useMemo(
    () =>
      groupTestProgressByBundle(prompts, bundles, testStartDtByTestId).filter(
        (g) => g.tests.length > 0
      ),
    [prompts, bundles, testStartDtByTestId]
  );

  const defaultOpenBundles = useMemo(
    () => groups.map(bundleAccordionValue),
    [groups]
  );

  if (groups.length === 0) {
    return (
      <p className="text-sm text-slate-600" data-testid="test-result-in-progress">
        No test progress available yet.
      </p>
    );
  }

  return (
    <Accordion
      type="multiple"
      defaultValue={defaultOpenBundles}
      className="flex flex-col gap-4"
      data-testid="test-result-in-progress"
    >
      {groups.map((group) => (
        <BundleProgressCard key={bundleAccordionValue(group)} group={group} />
      ))}
    </Accordion>
  );
}
