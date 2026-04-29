"use client";

import TestResultOverview, {
  ChartDataItem,
  OverviewBundleChart,
} from "./TestResultOverview";
import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import TestResultBundle from "./TestResultBundle";
import {
  ApiError,
  BenchmarkRun,
  BenchmarkRunResultsBundleSummary,
  BenchmarkRunTestPrompt,
  fetchBenchmarkRunResults,
} from "@/lib/api";

const TAB_OVERVIEW = "overview";
const tabBundleId = (id: number) => `bundle:${id}`;
const TAB_ALL = "all";
const TAB_DEMO_UND = "demo-undesirable";
const TAB_DEMO_DISC = "demo-disclosure";

function accuracyToPercent(acc: number | null | undefined): number | null {
  if (acc == null || Number.isNaN(acc)) return null;
  if (acc >= 0 && acc <= 1) return acc * 100;
  return acc;
}

/** Per-test mean accuracy % for charting (any subset of prompts). */
function chartItemsFromPrompts(prompts: BenchmarkRunTestPrompt[]): ChartDataItem[] {
  const byTest = new Map<string, number[]>();
  for (const p of prompts) {
    const pct = accuracyToPercent(p.evaluation_accuracy);
    if (pct == null) continue;
    const name = (p.test_name ?? "Unknown").trim() || "Unknown";
    if (!byTest.has(name)) byTest.set(name, []);
    byTest.get(name)!.push(pct);
  }
  const items: ChartDataItem[] = [];
  byTest.forEach((vals, test_name) => {
    items.push({
      test_name,
      adjusted_percentage_score: Math.round(
        vals.reduce((a, b) => a + b, 0) / vals.length
      ),
    });
  });
  return items;
}

function bundleMeanPercent(
  prompts: BenchmarkRunTestPrompt[],
  testIds: number[]
): number | null {
  const set = new Set(testIds);
  const pts = prompts
    .filter((p) => p.test_id != null && set.has(p.test_id))
    .map((p) => accuracyToPercent(p.evaluation_accuracy))
    .filter((x): x is number => x != null);
  if (!pts.length) return null;
  return Math.round((pts.reduce((a, b) => a + b, 0) / pts.length) * 10) / 10;
}

function mapStatusLabel(status: string): string {
  const s = status.toLowerCase();
  if (s === "completed") return "Complete";
  if (s === "running") return "In Progress";
  if (s === "failed" || s === "error") return "Failed";
  if (s === "demo") return "Demo";
  return status.charAt(0).toUpperCase() + status.slice(1);
}

export default function TestResultApp() {
  const searchParams = useSearchParams();
  const benchmarkRunId = useMemo(() => {
    const raw = searchParams.get("runId");
    if (!raw) return null;
    const n = parseInt(raw, 10);
    return Number.isFinite(n) && n > 0 ? n : null;
  }, [searchParams]);

  const [run, setRun] = useState<BenchmarkRun | null>(null);
  const [prompts, setPrompts] = useState<BenchmarkRunTestPrompt[]>([]);
  const [resultBundles, setResultBundles] = useState<BenchmarkRunResultsBundleSummary[]>(
    []
  );
  const [loading, setLoading] = useState(!!benchmarkRunId);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(TAB_OVERVIEW);
  const [bundleTabScores, setBundleTabScores] = useState<
    Record<number, number | null>
  >({});
  const [allTabScore, setAllTabScore] = useState<number | null>(null);
  const [demoUndesirableScore, setDemoUndesirableScore] = useState<number | null>(
    null
  );

  useEffect(() => {
    setActiveTab(TAB_OVERVIEW);
    setBundleTabScores({});
    setAllTabScore(null);
  }, [benchmarkRunId]);

  useEffect(() => {
    if (!benchmarkRunId) {
      setRun(null);
      setPrompts([]);
      setResultBundles([]);
      setLoading(false);
      setError(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    setPrompts([]);
    setResultBundles([]);
    fetchBenchmarkRunResults(benchmarkRunId)
      .then((res) => {
        if (!cancelled) {
          setRun(res.run);
          setPrompts(res.prompts);
          setResultBundles(res.bundles);
          setLoading(false);
          if (res.bundles.length > 0) {
            setActiveTab((cur) => (cur === TAB_ALL ? TAB_OVERVIEW : cur));
          }
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setRun(null);
          setPrompts([]);
          setResultBundles([]);
          setLoading(false);
          setError(e instanceof ApiError ? e.message : "Failed to load run");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [benchmarkRunId]);

  const bundleCharts: OverviewBundleChart[] = useMemo(() => {
    if (!benchmarkRunId || loading) return [];
    if (resultBundles.length === 0) {
      return [{ bundleName: "All results", data: chartItemsFromPrompts(prompts) }];
    }
    return resultBundles.map((b) => ({
      bundleName: b.name,
      data: chartItemsFromPrompts(
        prompts.filter(
          (p) => p.test_id != null && b.test_ids.includes(p.test_id)
        )
      ),
    }));
  }, [benchmarkRunId, loading, resultBundles, prompts]);

  const runMode = benchmarkRunId != null;
  const displayTitle =
    runMode && run ? run.name : loading && runMode ? "Loading…" : "Demo Test Run";
  const statusRaw = runMode && run ? run.status : "demo";
  const statusLabel = mapStatusLabel(statusRaw);

  const runTabs = useMemo(() => {
    if (!runMode) return [] as { id: string; label: string; badge: string | null }[];
    if (resultBundles.length === 0) {
      const pts = prompts
        .map((p) => accuracyToPercent(p.evaluation_accuracy))
        .filter((x): x is number => x != null);
      const meanAll =
        pts.length > 0
          ? Math.round((pts.reduce((a, b) => a + b, 0) / pts.length) * 10) / 10
          : null;
      return [
        {
          id: TAB_ALL,
          label: "All results",
          badge:
            allTabScore !== null
              ? `${Math.round(allTabScore * 10) / 10}%`
              : meanAll !== null
                ? `${meanAll}%`
                : prompts.length
                  ? "—"
                  : null,
        },
      ];
    }
    return resultBundles.map((b) => ({
      id: tabBundleId(b.test_bundle_id),
      label: b.name,
      badge: (() => {
        const s = bundleTabScores[b.test_bundle_id];
        if (s !== null && s !== undefined) return `${Math.round(s * 10) / 10}%`;
        const m = bundleMeanPercent(prompts, b.test_ids);
        return m !== null ? `${m}%` : prompts.length ? "—" : null;
      })(),
    }));
  }, [
    runMode,
    resultBundles,
    prompts,
    bundleTabScores,
    allTabScore,
  ]);

  return (
    <main className="p-8 w-[1300px]">
      <div>
        <p className="text-slate-700 text-[14px] font-medium w-[600px]">Report</p>
        <div className="flex items-center justify-between mt-3 mb-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-semibold text-gray-900">
              {displayTitle}
            </h1>
            <Badge variant="outline">
              <div className="text-left">{statusLabel}</div>
            </Badge>
            {runMode && benchmarkRunId && (
              <span className="text-sm text-slate-500">Run #{benchmarkRunId}</span>
            )}
          </div>
          <Button
            className="font-extrabold text-[14px] text-white"
            style={{ backgroundColor: "#702F8A" }}
            disabled={runMode && (loading || !prompts.length)}
          >
            Download
          </Button>
        </div>

        {error && runMode && (
          <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
            <p>{error}</p>
            <Link
              href="/history"
              className="mt-2 inline-block font-medium text-red-900 underline"
            >
              Back to history
            </Link>
          </div>
        )}

        <div className="text-left font-medium text-[14px] text-slate-500 mb-3 mt-2">
          {runMode && run
            ? `Endpoint type: ${run.endpoint_type}`
            : " This is a test Description"}
        </div>
        <div className="flex items-center gap-2 mt-2 flex-wrap">
          <div className="text-left font-medium text-[12px] text-slate-500">
            Endpoint
          </div>
          <div className="text-left font-semibold text-[12px] text-slate-700">
            {runMode && run ? run.endpoint_type : "mistral-7b"}
          </div>
          <div className="h-4 w-px bg-slate-300" />
          <div className="text-left font-medium text-[12px] text-slate-500">
            Prompts
          </div>
          <div className="text-left font-semibold text-[12px] text-slate-700">
            {runMode ? (loading ? "—" : String(prompts.length)) : "200"}
          </div>
          {!runMode && (
            <>
              <div className="h-4 w-px bg-slate-300" />
              <div className="text-left font-medium text-[12px] text-slate-500">
                Confidence Level
              </div>
              <div className="text-left font-semibold text-[12px] text-slate-700">
                95%
              </div>
            </>
          )}
        </div>
      </div>

      <div className="bg-slate-100 flex flex-wrap items-center gap-[10px] p-[5px] rounded-[6px] mt-4">
        <button
          type="button"
          onClick={() => setActiveTab(TAB_OVERVIEW)}
          className={`flex gap-[10px] items-center px-3 py-1.5 rounded-[3px] transition-colors ${
            activeTab === TAB_OVERVIEW ? "bg-white" : "bg-transparent hover:bg-white/50"
          }`}
        >
          <p
            className={`font-semibold text-[14px] whitespace-nowrap ${
              activeTab === TAB_OVERVIEW ? "text-slate-800" : "text-slate-600"
            }`}
          >
            Overview
          </p>
        </button>

        {runMode &&
          runTabs.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setActiveTab(t.id)}
              className={`flex gap-[10px] items-center px-3 py-1.5 rounded-[3px] transition-colors max-w-[min(100%,280px)] ${
                activeTab === t.id ? "bg-white" : "bg-transparent hover:bg-white/50"
              }`}
            >
              <p
                className={`font-semibold text-[14px] truncate ${
                  activeTab === t.id ? "text-slate-800" : "text-slate-600"
                }`}
                title={t.label}
              >
                {t.label}
              </p>
              {t.badge != null && (
                <div className="bg-gray-100 border border-gray-200 flex gap-1 items-center justify-center p-1 rounded-[6px] shrink-0">
                  <p className="font-semibold text-[12px] text-gray-800 whitespace-nowrap">
                    {t.badge}
                  </p>
                </div>
              )}
            </button>
          ))}

        {!runMode && (
          <>
            <button
              type="button"
              onClick={() => setActiveTab(TAB_DEMO_UND)}
              className={`flex gap-[10px] items-center px-3 py-1.5 rounded-[3px] transition-colors ${
                activeTab === TAB_DEMO_UND
                  ? "bg-white"
                  : "bg-transparent hover:bg-white/50"
              }`}
            >
              <p
                className={`font-semibold text-[14px] whitespace-nowrap ${
                  activeTab === TAB_DEMO_UND ? "text-slate-800" : "text-slate-600"
                }`}
              >
                Undesirable content
              </p>
              <div className="bg-gray-100 border border-gray-200 flex gap-1 items-center justify-center p-1 rounded-[6px]">
                <p className="font-semibold text-[12px] text-gray-800 whitespace-nowrap">
                  {demoUndesirableScore !== null
                    ? `${Math.round(demoUndesirableScore * 10) / 10}%`
                    : "—"}
                </p>
              </div>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab(TAB_DEMO_DISC)}
              className={`flex gap-[10px] items-center px-3 py-1.5 rounded-[3px] transition-colors ${
                activeTab === TAB_DEMO_DISC
                  ? "bg-white"
                  : "bg-transparent hover:bg-white/50"
              }`}
            >
              <p
                className={`font-semibold text-[14px] whitespace-nowrap ${
                  activeTab === TAB_DEMO_DISC ? "text-slate-800" : "text-slate-600"
                }`}
              >
                Data disclosure
              </p>
              <div className="bg-gray-100 border border-gray-200 flex gap-1 items-center justify-center p-1 rounded-[6px]">
                <p className="font-semibold text-[12px] text-gray-800 whitespace-nowrap">
                  80%
                </p>
              </div>
            </button>
          </>
        )}
      </div>

      {runMode && resultBundles.length === 0 && (
        <div className={activeTab === TAB_ALL ? "" : "hidden"}>
          <TestResultBundle
            benchmarkRunId={benchmarkRunId}
            apiPrompts={prompts}
            apiLoading={loading}
            apiError={error}
            filterTestIds={null}
            bundleDisplayName={null}
            onAdjustedScoreChange={setAllTabScore}
          />
        </div>
      )}

      {runMode &&
        resultBundles.map((b) => (
          <div
            key={b.test_bundle_id}
            className={activeTab === tabBundleId(b.test_bundle_id) ? "" : "hidden"}
          >
            <TestResultBundle
              benchmarkRunId={benchmarkRunId}
              apiPrompts={prompts}
              apiLoading={loading}
              apiError={error}
              filterTestIds={b.test_ids}
              bundleDisplayName={b.name}
              onAdjustedScoreChange={(score) =>
                setBundleTabScores((prev) => ({
                  ...prev,
                  [b.test_bundle_id]: score,
                }))
              }
            />
          </div>
        ))}

      {!runMode && activeTab === TAB_DEMO_UND && (
        <TestResultBundle
          onAdjustedScoreChange={setDemoUndesirableScore}
        />
      )}

      {activeTab === TAB_OVERVIEW && (
        <TestResultOverview
          runMode={runMode}
          overviewLoading={runMode && loading}
          overviewError={runMode && error ? error : null}
          bundleCharts={runMode ? bundleCharts : undefined}
        />
      )}
    </main>
  );
}
