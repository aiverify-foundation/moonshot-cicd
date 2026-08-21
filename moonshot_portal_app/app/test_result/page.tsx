import { Suspense } from "react";
import TestResultApp from "./components/TestResultApp";

export default function Test() {
  return (
    <Suspense
      fallback={
        <main className="p-8 w-[1300px]">
          <p className="text-sm text-slate-600">Loading report…</p>
        </main>
      }
    >
      <TestResultApp />
    </Suspense>
  );
}
