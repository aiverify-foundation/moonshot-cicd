/**
 * PDF preview feature — delete this entire preview/ directory to remove.
 */
"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import React, { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { ApiError, fetchBenchmarkRunResults } from "@/lib/api";
import { mapRunToReportData } from "../pdf/mapRunToReportData";
import PdfFitWidthPreview from "./PdfFitWidthPreview";

export default function SafetyReportPreviewApp() {
  const searchParams = useSearchParams();
  const benchmarkRunId = useMemo(() => {
    const raw = searchParams.get("runId");
    if (!raw) return null;
    const n = parseInt(raw, 10);
    return Number.isFinite(n) && n > 0 ? n : null;
  }, [searchParams]);

  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [runName, setRunName] = useState<string>("");
  const [loading, setLoading] = useState(!!benchmarkRunId);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!pdfUrl) return;
    return () => {
      URL.revokeObjectURL(pdfUrl);
    };
  }, [pdfUrl]);

  useEffect(() => {
    if (!benchmarkRunId) {
      setPdfUrl(null);
      setRunName("");
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);
    setPdfUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });

    (async () => {
      try {
        const res = await fetchBenchmarkRunResults(benchmarkRunId);
        if (cancelled) return;

        const status = res.run.status?.toLowerCase();
        if (status !== "completed") {
          setError("Preview is only available for completed runs.");
          setLoading(false);
          return;
        }
        if (!res.prompts.length) {
          setError("No prompt results are available for this run.");
          setLoading(false);
          return;
        }

        const props = mapRunToReportData(
          res.run,
          res.bundles,
          res.prompts,
          res.test_margin_of_error ?? []
        );
        const { generateSafetyReportBlob } = await import(
          "../pdf/downloadSafetyReportPdf"
        );
        const blob = await generateSafetyReportBlob(props);
        if (cancelled) return;

        setRunName(res.run.name);
        setPdfUrl(URL.createObjectURL(blob));
        setLoading(false);
      } catch (e) {
        if (cancelled) return;
        setError(
          e instanceof ApiError ? e.message : "Failed to generate PDF preview"
        );
        setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [benchmarkRunId]);

  if (!benchmarkRunId) {
    return (
      <main className="p-8">
        <h1 className="text-xl font-semibold text-gray-900">PDF preview</h1>
        <p className="mt-4 text-sm text-slate-600">
          Open a completed run from history to preview the safety report.
        </p>
        <Link
          href="/history"
          className="mt-2 inline-block text-sm font-medium text-slate-900 underline"
        >
          Go to history
        </Link>
      </main>
    );
  }

  const backHref = `/test_result/?runId=${benchmarkRunId}`;

  return (
    <div className="flex h-[calc(100vh)] w-full flex-col">
      <header className="flex shrink-0 items-center justify-between gap-4 border-b border-slate-200 bg-white px-6 py-5 shadow-sm">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            PDF preview
          </p>
          <h1 className="text-lg font-semibold text-gray-900">
            {runName || (loading ? "Loading…" : "Safety report")}
          </h1>
          <p className="text-sm text-slate-500">Run #{benchmarkRunId}</p>
        </div>
        <Button asChild variant="outline" className="shrink-0">
          <Link href={backHref}>Back to results</Link>
        </Button>
      </header>

      {error && (
        <div className="mx-6 mt-6 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          <p>{error}</p>
          <Link
            href={backHref}
            className="mt-2 inline-block font-medium text-red-900 underline"
          >
            Back to results
          </Link>
        </div>
      )}

      {loading && (
        <p className="p-8 text-sm text-slate-600">Generating preview…</p>
      )}

      {!loading && !error && pdfUrl && (
        <PdfFitWidthPreview url={pdfUrl} />
      )}
    </div>
  );
}
