/**
 * PDF preview feature — delete this entire preview/ directory to remove.
 */
import { Suspense } from "react";
import SafetyReportPreviewApp from "./SafetyReportPreviewApp";

export default function SafetyReportPreviewPage() {
  return (
    <Suspense
      fallback={
        <main className="p-8">
          <p className="text-sm text-slate-600">Loading preview…</p>
        </main>
      }
    >
      <SafetyReportPreviewApp />
    </Suspense>
  );
}
