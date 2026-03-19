"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  ApiError,
  BenchmarkRun,
  countBundlesAndTests,
  fetchBenchmarkRuns,
  fetchBenchmarkRunTestBundles,
} from "@/lib/api";

interface HistoryCardProps {
  title: string;
  completedDate: string;
  bundleAndTestCount: string;
  status: string;
  progressValue: number;
  footerLine: string;
  href?: string;
}

function mapRunStatusToDisplay(status: string): string {
  const s = status.toLowerCase();
  if (s === "completed") return "Complete";
  if (s === "running") return "In Progress";
  if (s === "failed" || s === "error") return "Failed";
  return status.charAt(0).toUpperCase() + status.slice(1);
}

function formatRunTimestamp(iso: string | null | undefined, kind: "completed" | "started"): string {
  if (!iso) return kind === "completed" ? "Completed —" : "Started —";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return kind === "completed" ? "Completed —" : "Started —";
  const label = kind === "completed" ? "Completed" : "Started";
  return `${label} ${d.toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })}`;
}

function formatDurationMinutes(startIso: string | null | undefined, endIso: string | null | undefined): string | null {
  if (!startIso || !endIso) return null;
  const start = new Date(startIso).getTime();
  const end = new Date(endIso).getTime();
  if (Number.isNaN(start) || Number.isNaN(end) || end < start) return null;
  const mins = Math.round((end - start) / 60000);
  if (mins < 1) return "<1 min";
  if (mins < 60) return `${mins}min`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m ? `${h}h ${m}min` : `${h}h`;
}

const createHistoryCard = ({
  title,
  completedDate,
  bundleAndTestCount,
  status,
  progressValue,
  footerLine,
  href = "/test_result",
}: HistoryCardProps) => {
  const statusColors = {
    Complete: "bg-green-100 border-green-200 text-green-800",
    "In Progress": "bg-blue-100 border-blue-200 text-blue-800",
    Failed: "bg-red-100 border-red-200 text-red-800",
  };

  const statusColorClass =
    statusColors[status as keyof typeof statusColors] ||
    "bg-gray-100 border-gray-200 text-gray-800";

  const getProgressClassName = () => {
    if (status === "Complete") {
      return "w-[100px] h-[16px] [&>div]:bg-green-600";
    }
    if (status === "In Progress") {
      return "w-[100px] h-[16px] [&>div]:bg-blue-600";
    }
    return "w-[100px] h-[16px] [&>div]:bg-gray-600";
  };

  const progressTextColor =
    status === "Complete"
      ? "text-green-600"
      : status === "In Progress"
        ? "text-blue-600"
        : "text-gray-600";

  return (
    <Link href={href}>
      <Badge
        variant="outline"
        className="w-full p-4 bg-slate-50 border-slate-200 cursor-pointer hover:bg-slate-100 transition-colors"
      >
        <div className="text-left min-h-[180px] w-full">
          <div className="mb-2">
            <div className="text-left font-semibold text-base text-gray-900 mb-1">{title}</div>
            <div className="font-normal text-sm text-slate-700 mb-1">{completedDate}</div>
            <div className="font-normal text-[12px] text-slate-700">{bundleAndTestCount}</div>
          </div>
          <Badge variant="outline" className={`w-fit mt-2 ${statusColorClass} h-[23px]`}>
            <div className="text-left text-[12px] font-semibold">{status}</div>
          </Badge>
          <div className="flex items-center gap-2 mt-4">
            <Progress value={progressValue} className={getProgressClassName()} />
            <div className={`text-[14px] font-semibold ${progressTextColor}`}>{progressValue}%</div>
          </div>
          <div className="font-normal text-[12px] text-slate-700 mt-4">{footerLine}</div>
        </div>
      </Badge>
    </Link>
  );
};

type RunWithCounts = BenchmarkRun & {
  bundleCount: number;
  testCount: number;
};

export default function History() {
  const [runs, setRuns] = useState<RunWithCounts[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await fetchBenchmarkRuns();
      const sorted = [...list].sort((a, b) => {
        const ta = a.start_time ? new Date(a.start_time).getTime() : 0;
        const tb = b.start_time ? new Date(b.start_time).getTime() : 0;
        if (tb !== ta) return tb - ta;
        return (b.id ?? 0) - (a.id ?? 0);
      });

      const withCounts = await Promise.all(
        sorted.map(async (run) => {
          const id = run.id;
          if (id == null) {
            return { ...run, bundleCount: 0, testCount: 0 };
          }
          try {
            const rows = await fetchBenchmarkRunTestBundles(id);
            const { bundleCount, testCount } = countBundlesAndTests(rows);
            return { ...run, bundleCount, testCount };
          } catch {
            return { ...run, bundleCount: 0, testCount: 0 };
          }
        })
      );

      setRuns(withCounts);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load history");
      setRuns([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <main className="p-8 w-[1300px]">
      <div className="min-h-[100px]">
        <p className="text-slate-700 text-[14px] font-medium w-[600px]">History</p>
        <h1 className="text-2xl font-semibold text-gray-900 mb-2 mt-3">Recent Activity</h1>
        <Badge variant="outline">
          <div className="text-left">Status</div>
        </Badge>

        {loading && (
          <p className="text-sm text-slate-600 mt-6">Loading benchmark runs…</p>
        )}

        {error && !loading && (
          <div className="mt-6 space-y-2">
            <p className="text-sm text-red-600">{error}</p>
            <button
              type="button"
              onClick={() => load()}
              className="text-sm text-blue-600 underline"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && runs.length === 0 && (
          <p className="text-sm text-slate-600 mt-6">No benchmark runs yet.</p>
        )}

        <div className="grid grid-cols-4 gap-4 mt-4">
          {!loading &&
            !error &&
            runs.map((run) => {
              const displayStatus = mapRunStatusToDisplay(run.status);
              const isComplete = run.status.toLowerCase() === "completed";
              const isRunning = run.status.toLowerCase() === "running";
              const progressValue = isComplete ? 100 : isRunning ? 5 : 0;

              const completedDate = isComplete
                ? formatRunTimestamp(run.end_time ?? run.start_time, "completed")
                : formatRunTimestamp(run.start_time, "started");

              const duration = formatDurationMinutes(run.start_time ?? undefined, run.end_time ?? undefined);
              const footerLine = isComplete && duration
                ? `Completed in ${duration}`
                : isRunning
                  ? "Run in progress"
                  : duration
                    ? `Finished in ${duration}`
                    : "—";

              const b = run.bundleCount;
              const t = run.testCount;
              const bundleAndTestCount = `${b} Bundle${b === 1 ? "" : "s"}, ${t} Test${t === 1 ? "" : "s"}`;

              const cardHref =
                run.id != null ? `/test_result?runId=${run.id}` : "/test_result";

              return (
                <div key={run.id ?? `run-${run.name}`} className="min-w-0">
                  {createHistoryCard({
                    title: run.name,
                    completedDate,
                    bundleAndTestCount,
                    status: displayStatus,
                    progressValue,
                    footerLine,
                    href: cardHref,
                  })}
                </div>
              );
            })}
        </div>
      </div>
    </main>
  );
}
