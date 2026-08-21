import { Suspense } from "react";
import ViewTestApp from "./components/ViewTestApp";

export default function ViewTestPage() {
  return (
    <Suspense
      fallback={
        <main className="p-8 w-[1300px]">
          <p className="text-gray-600">Loading test details…</p>
        </main>
      }
    >
      <ViewTestApp />
    </Suspense>
  );
}
