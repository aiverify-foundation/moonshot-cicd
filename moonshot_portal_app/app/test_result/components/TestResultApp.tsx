"use client";

import TestResultOverview, { ChartDataItem } from "./TestResultOverview";
import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import TestResultBundle from "./TestResultBundle";
import {
  ApiError,
  BenchmarkRun,
  BenchmarkRunTestPrompt,
  fetchBenchmarkRunById,
  fetchBenchmarkRunPrompts,
} from "@/lib/api";

function accuracyToPercent(acc: number | null | undefined): number | null {
  if (acc == null || Number.isNaN(acc)) return null;
  if (acc >= 0 && acc <= 1) return acc * 100;
  return acc;
}

function buildOverviewCharts(prompts: BenchmarkRunTestPrompt[]): {
  undesirable: ChartDataItem[];
  disclosure: ChartDataItem[];
} {
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
  const isDisclosure = (name: string) => /privacy|disclosure/i.test(name);
  const disclosure = items.filter((i) => isDisclosure(i.test_name));
  const undesirable = items.filter((i) => !isDisclosure(i.test_name));
  return { undesirable, disclosure };
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
  const [loading, setLoading] = useState(!!benchmarkRunId);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!benchmarkRunId) {
      setRun(null);
      setPrompts([]);
      setLoading(false);
      setError(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([
      fetchBenchmarkRunById(benchmarkRunId),
      fetchBenchmarkRunPrompts(benchmarkRunId),
    ])
      .then(([r, pr]) => {
        if (!cancelled) {
          setRun(r);
          setPrompts(pr);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setRun(null);
          setPrompts([]);
          setLoading(false);
          setError(e instanceof ApiError ? e.message : "Failed to load run");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [benchmarkRunId]);

  const { undesirable, disclosure } = useMemo(
    () => buildOverviewCharts(prompts),
    [prompts]
  );

  const disclosureTabPct = useMemo(() => {
    const pts = prompts
      .map((p) =>
        /privacy|disclosure/i.test(p.test_name ?? "")
          ? accuracyToPercent(p.evaluation_accuracy)
          : null
      )
      .filter((x): x is number => x != null);
    if (!pts.length) return null;
    return Math.round((pts.reduce((a, b) => a + b, 0) / pts.length) * 10) / 10;
  }, [prompts]);

  const runMode = benchmarkRunId != null;
  const displayTitle =
    runMode && run ? run.name : loading && runMode ? "Loading…" : "Demo Test Run";
  const statusRaw = runMode && run ? run.status : "demo";
  const statusLabel = mapStatusLabel(statusRaw);

  const [activeTab, setActiveTab] = useState("Overview");
  const [undesirableContentScore, setUndesirableContentScore] = useState<
    number | null
  >(null);

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

      <div className="bg-slate-100 flex items-center gap-[10px] p-[5px] rounded-[6px] mt-4">
        <button
          type="button"
          onClick={() => setActiveTab("Overview")}
          className={`flex gap-[10px] items-center px-3 py-1.5 rounded-[3px] transition-colors ${
            activeTab === "Overview"
              ? "bg-white"
              : "bg-transparent hover:bg-white/50"
          }`}
        >
          <p
            className={`font-semibold text-[14px] whitespace-nowrap ${
              activeTab === "Overview" ? "text-slate-800" : "text-slate-600"
            }`}
          >
            Overview
          </p>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("Undesirable content")}
          className={`flex gap-[10px] items-center px-3 py-1.5 rounded-[3px] transition-colors ${
            activeTab === "Undesirable content"
              ? "bg-white"
              : "bg-transparent hover:bg-white/50"
          }`}
        >
          <p
            className={`font-semibold text-[14px] whitespace-nowrap ${
              activeTab === "Undesirable content"
                ? "text-slate-800"
                : "text-slate-600"
            }`}
          >
            Undesirable content
          </p>
          <div className="bg-gray-100 border border-gray-200 flex gap-1 items-center justify-center p-1 rounded-[6px]">
            <p className="font-semibold text-[12px] text-gray-800 whitespace-nowrap">
              {undesirableContentScore !== null
                ? `${Math.round(undesirableContentScore * 10) / 10}%`
                : "—"}
            </p>
          </div>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("Data disclosure")}
          className={`flex gap-[10px] items-center px-3 py-1.5 rounded-[3px] transition-colors ${
            activeTab === "Data disclosure"
              ? "bg-white"
              : "bg-transparent hover:bg-white/50"
          }`}
        >
          <p
            className={`font-semibold text-[14px] whitespace-nowrap ${
              activeTab === "Data disclosure"
                ? "text-slate-800"
                : "text-slate-600"
            }`}
          >
            Data disclosure
          </p>
          <div className="bg-gray-100 border border-gray-200 flex gap-1 items-center justify-center p-1 rounded-[6px]">
            <p className="font-semibold text-[12px] text-gray-800 whitespace-nowrap">
              {runMode && disclosureTabPct !== null
                ? `${disclosureTabPct}%`
                : runMode
                  ? "—"
                  : "80%"}
            </p>
          </div>
        </button>
      </div>

      <div className={activeTab === "Undesirable content" ? "" : "hidden"}>
        <TestResultBundle
          benchmarkRunId={benchmarkRunId}
          apiPrompts={runMode ? prompts : null}
          apiLoading={runMode && loading}
          apiError={runMode ? error : null}
          onAdjustedScoreChange={setUndesirableContentScore}
        />
      </div>
      {activeTab === "Overview" && (
        <TestResultOverview
          runMode={runMode}
          overviewLoading={runMode && loading}
          overviewError={runMode && error ? error : null}
          chartUndesirable={undesirable}
          chartDisclosure={disclosure}
        />
      )}
    </main>
  );
}
