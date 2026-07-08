import { BenchmarkRunTestPrompt } from "@/lib/api";
import { runHasPromptErrors } from "./testCompletion";

/** Display label for benchmark_run.status in results UI. */
export function mapRunStatusLabel(
  status: string,
  prompts: BenchmarkRunTestPrompt[] = []
): string {
  const s = status.toLowerCase();
  if (s === "completed") return "Complete";
  if (s === "running") return "In Progress";
  if ((s === "failed" || s === "error") && runHasPromptErrors(prompts)) {
    return "Completed with Errors";
  }
  if (s === "failed" || s === "error") return "Failed";
  return status.charAt(0).toUpperCase() + status.slice(1);
}

/** Tailwind classes for run status badge. */
export function runStatusBadgeClassName(
  status: string,
  prompts: BenchmarkRunTestPrompt[] = []
): string {
  const label = mapRunStatusLabel(status, prompts);
  if (label === "Complete") {
    return "bg-green-100 border-green-200 text-green-800";
  }
  if (label === "In Progress") {
    return "bg-blue-100 border-blue-200 text-blue-800";
  }
  if (label === "Completed with Errors" || label === "Failed") {
    return "bg-red-100 border-red-200 text-red-800";
  }
  return "bg-gray-100 border-gray-200 text-gray-800";
}
