/**
 * Parsing helpers for benchmark_run_test_prompt.evaluation_prediction_result blobs.
 * Backend often persists Python dict repr (str(dict)), not JSON.
 */

export function extractEvaluatedResponse(raw: string | null | undefined): string | null {
    if (raw == null || raw.trim() === "") return null
    const s = raw.trim()
    try {
        const parsed = JSON.parse(s) as Record<string, unknown>
        if (typeof parsed === "object" && parsed !== null) {
            const v = parsed.evaluated_response
            if (typeof v === "string" && v.trim() !== "") return v.trim()
        }
        return null
    } catch {
        const m = s.match(/\bevaluated_response['"]?\s*:\s*['"]([^'"]*)['"]/)
        const v = m?.[1]
        return v && v.trim() !== "" ? v.trim() : null
    }
}

export function evaluationDisplayLabel(evaluationBlob: string, score: number): string {
    return extractEvaluatedResponse(evaluationBlob) ?? (score === 1 ? "Agree" : score === 0 ? "Disagree" : evaluationBlob)
}
