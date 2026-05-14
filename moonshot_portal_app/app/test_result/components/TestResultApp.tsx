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
import { metricToPercentPoints } from "./metricToPercentPoints";
import {
  ApiError,
  BenchmarkRun,
  BenchmarkRunResultsBundleSummary,
  BenchmarkRunTestMarginOfError,
  BenchmarkRunTestPrompt,
  fetchBenchmarkRunResults,
} from "@/lib/api";

const TAB_OVERVIEW = "overview";
const tabBundleId = (id: number) => `bundle:${id}`;
const TAB_ALL = "all";

function accuracyToPercent(acc: number | null | undefined): number | null {
  if (acc == null || Number.isNaN(acc)) return null;
  if (acc >= 0 && acc <= 1) return acc * 100;
  return acc;
}

/** Per-test mean score % for charting (any subset of prompts). */
function chartItemsFromPrompts(
  prompts: BenchmarkRunTestPrompt[],
  marginPercentByTestId: Map<number, number> | null
): ChartDataItem[] {
  const byTestId = new Map<number, { test_name: string; pcts: number[] }>();
  for (const p of prompts) {
    if (p.test_id == null) continue;
    const tid = p.test_id;
    const pct = accuracyToPercent(p.score);
    if (pct == null) continue;
    const name = (p.test_name ?? "Unknown").trim() || "Unknown";
    if (!byTestId.has(tid)) byTestId.set(tid, { test_name: name, pcts: [] });
    byTestId.get(tid)!.pcts.push(pct);
  }
  const items: ChartDataItem[] = [];
  for (const tid of byTestId.keys()) {
    const v = byTestId.get(tid)!;
    const marginHalfWidthPercent = marginPercentByTestId?.get(tid) ?? null;
    items.push({
      test_name: v.test_name,
      test_id: tid,
      adjusted_percentage_score: Math.round(
        v.pcts.reduce((a, b) => a + b, 0) / v.pcts.length
      ),
      marginHalfWidthPercent,
    });
  }
  items.sort((a, b) => a.test_name.localeCompare(b.test_name));
  return items;
}

function bundleMeanPercent(
  prompts: BenchmarkRunTestPrompt[],
  testIds: number[]
): number | null {
  const set = new Set(testIds);
  const pts = prompts
    .filter((p) => p.test_id != null && set.has(p.test_id))
    .map((p) => accuracyToPercent(p.score))
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

  const showMarginDebug = searchParams.get("debugMargin") === "1";

  const [run, setRun] = useState<BenchmarkRun | null>(null);
  const [prompts, setPrompts] = useState<BenchmarkRunTestPrompt[]>([]);
  const [resultBundles, setResultBundles] = useState<BenchmarkRunResultsBundleSummary[]>(
    []
  );
  const [testMargins, setTestMargins] = useState<BenchmarkRunTestMarginOfError[]>([]);
  const [loading, setLoading] = useState(!!benchmarkRunId);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(TAB_OVERVIEW);
  const [bundleTabScores, setBundleTabScores] = useState<
    Record<number, number | null>
  >({});
  const [allTabScore, setAllTabScore] = useState<number | null>(null);

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
      setTestMargins([]);
      setLoading(false);
      setError(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    setPrompts([]);
    setResultBundles([]);
    setTestMargins([]);
    fetchBenchmarkRunResults(benchmarkRunId)
      .then((res) => {
        if (!cancelled) {
          setRun(res.run);
          setPrompts(res.prompts);
          setResultBundles(res.bundles);
          setTestMargins(res.test_margin_of_error ?? []);
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
          setTestMargins([]);
          setLoading(false);
          setError(e instanceof ApiError ? e.message : "Failed to load run");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [benchmarkRunId]);

  const marginPercentByTestId = useMemo(() => {
    const m = new Map<number, number>();
    for (const row of testMargins) {
      const c = metricToPercentPoints(row.margin_of_error);
      if (c != null && c > 0) m.set(row.test_id, c);
    }
    return m;
  }, [testMargins]);

  const marginPctRecord = useMemo(() => {
    const o: Record<number, number> = {};
    marginPercentByTestId.forEach((v, k) => {
      o[k] = v;
    });
    return o;
  }, [marginPercentByTestId]);

  const bundleCharts: OverviewBundleChart[] = useMemo(() => {
    if (!benchmarkRunId || loading) return [];
    if (resultBundles.length === 0) {
      return [
        {
          bundleName: "All results",
          data: chartItemsFromPrompts(prompts, marginPercentByTestId),
        },
      ];
    }
    return resultBundles.map((b) => ({
      bundleName: b.name,
      data: chartItemsFromPrompts(
        prompts.filter(
          (p) => p.test_id != null && b.test_ids.includes(p.test_id)
        ),
        marginPercentByTestId
      ),
    }));
  }, [benchmarkRunId, loading, resultBundles, prompts, marginPercentByTestId]);

  const runMode = benchmarkRunId != null;
  const displayTitle =
    runMode && run ? run.name : loading && runMode ? "Loading…" : "Demo Test Run";
  const statusRaw = runMode && run ? run.status : "demo";
  const statusLabel = mapStatusLabel(statusRaw);

  const runTabs = useMemo(() => {
    if (!runMode) return [] as { id: string; label: string; badge: string | null }[];
    if (resultBundles.length === 0) {
      const pts = prompts
        .map((p) => accuracyToPercent(p.score))
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

      </div>

      {runMode && showMarginDebug && (
        <div
          className="mt-4 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-left text-xs text-amber-950"
          data-testid="margin-debug-panel"
        >
          <p className="font-semibold text-amber-900">
            Margin / confidence bar debug{" "}
            <span className="font-normal text-amber-800">
              (append <code className="rounded bg-amber-100 px-1">{"&debugMargin=1"}</code> to the URL;
              keep your <code className="rounded bg-amber-100 px-1">runId</code>)
            </span>
          </p>
          <ul className="mt-2 list-inside list-disc space-y-1 font-mono">
            <li>loading: {String(loading)}</li>
            <li>prompts.length: {prompts.length}</li>
            <li>resultBundles.length: {resultBundles.length}</li>
            <li>test_margin_of_error.length: {testMargins.length}</li>
            <li>activeTab: {activeTab}</li>
          </ul>
          <table className="mt-2 w-full border-collapse border border-amber-200 text-left font-mono text-[11px]">
            <thead>
              <tr className="bg-amber-100/80">
                <th className="border border-amber-200 px-1 py-0.5">test_id</th>
                <th className="border border-amber-200 px-1 py-0.5">API margin_of_error</th>
                <th className="border border-amber-200 px-1 py-0.5">metricToPercentPoints</th>
              </tr>
            </thead>
            <tbody>
              {testMargins.map((row) => {
                const conv = metricToPercentPoints(row.margin_of_error);
                return (
                  <tr key={row.test_id}>
                    <td className="border border-amber-200 px-1 py-0.5">{row.test_id}</td>
                    <td className="border border-amber-200 px-1 py-0.5">
                      {JSON.stringify(row.margin_of_error)}
                    </td>
                    <td className="border border-amber-200 px-1 py-0.5">
                      {conv === null ? "null" : String(conv)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {resultBundles.length > 0 ? (
            <p className="mt-2 font-mono text-[11px]">
              Bundles (no per-bundle margin):{" "}
              {resultBundles.map((b) => `${b.name}(${b.test_bundle_id})`).join(", ")}
            </p>
          ) : (
            <p className="mt-2 font-mono text-[11px]">
              No result bundles (All results path): margins come from test_margin_of_error only.
            </p>
          )}
          <p className="mt-2 text-[11px] text-amber-900">
            bundleCharts (overview):{" "}
            {JSON.stringify(
              bundleCharts.map((c) => ({
                bundleName: c.bundleName,
                bars: c.data.length,
                perBarMarginPct: c.data.map((d) => d.marginHalfWidthPercent ?? null),
              }))
            )}
          </p>
        </div>
      )}

      {runMode && resultBundles.length === 0 && (
        <div className={activeTab === TAB_ALL ? "" : "hidden"}>
          <TestResultBundle
            apiPrompts={prompts}
            apiLoading={loading}
            apiError={error}
            filterTestIds={null}
            bundleDisplayName={null}
            marginHalfWidthPercentByTestId={marginPctRecord}
            showMarginDebug={showMarginDebug}
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
              apiPrompts={prompts}
              apiLoading={loading}
              apiError={error}
              filterTestIds={b.test_ids}
              bundleDisplayName={b.name}
              marginHalfWidthPercentByTestId={marginPctRecord}
              showMarginDebug={showMarginDebug}
              onAdjustedScoreChange={(score) =>
                setBundleTabScores((prev) => ({
                  ...prev,
                  [b.test_bundle_id]: score,
                }))
              }
            />
          </div>
        ))}

      {activeTab === TAB_OVERVIEW && (
        <TestResultOverview
          runMode={runMode}
          overviewLoading={runMode && loading}
          overviewError={runMode && error ? error : null}
          bundleCharts={runMode ? bundleCharts : undefined}
          showMarginDebug={runMode && showMarginDebug}
        />
      )}
    </main>
  );
}
