"use client"
import React, { useState, useEffect, useMemo, useRef, useCallback } from "react"
import { ThumbsUp, ThumbsDown } from "lucide-react"
import BundleChart, { BundleChartDataItem } from "./BundleChart"
import TestResultTable, { TestResultTableRow } from "./TestResultTable"
import {
    patchBenchmarkRunPromptUserFeedback,
    type BenchmarkRunTestPrompt,
    type BenchmarkRunTestStatusSummary,
} from "@/lib/api"
import {
    classifyTest,
    promptsForTest,
    testStatusByTestId,
} from "./testCompletion"

export { extractEvaluatedResponse, evaluationDisplayLabel } from "./evaluationDisplayHelpers"

const EMPTY_PROMPTS: BenchmarkRunTestPrompt[] = []

/**
 * Normalize API score to binary 0/1 for UI rendering.
 *
 * Results pages treat backend `score` as the single source of truth.
 */
export function scoreFromApiScore(score: number | null | undefined): number {
    if (typeof score !== "number" || Number.isNaN(score)) return 0
    return Math.round(score)
}

/**
 * Mean accuracy % after user disagreements flip binary scores: disagree on AI 1 → 0, on AI 0 → 1.
 */
export function adjustedAccuracyPercent(
    totalScore: number,
    rowCount: number,
    disagreeWithScore1: number,
    disagreeWithScore0: number
): number {
    if (rowCount <= 0) return 0
    return ((totalScore - disagreeWithScore1 + disagreeWithScore0) / rowCount) * 100
}

export function promptsToTableRows(
    prompts: BenchmarkRunTestPrompt[],
    bundleDisplayName?: string | null
): TestResultTableRow[] {
    return prompts.map((p, idx) => {
        const isPromptError = p.status === "error"
        const score = isPromptError ? 0 : scoreFromApiScore(p.score ?? null)
        let yourVerdict: "agree" | "disagree" | null = null
        if (p.user_evaluation === 1) yourVerdict = "agree"
        else if (p.user_evaluation === 0) yourVerdict = "disagree"

        const promptText = p.prompt_additional_info ?? "—"
        const evalPrompt = p.evaluation_prompt ?? "—"
        const response =
            p.error_source === "connector" && p.error_message
                ? p.error_message
                : (p.prediction_result ?? "—")

        return {
            id: p.id != null ? `p-${p.id}` : `p-${p.run_test_id}-${p.prompt_id}-${idx}`,
            benchmarkPromptId: p.id ?? null,
            test_id: p.test_id ?? null,
            test: p.test_name || "—",
            prompt: promptText.length > 2000 ? `${promptText.slice(0, 2000)}…` : promptText,
            target: p.target || "—",
            response,
            evaluation: isPromptError ? "error" : (p.evaluation_prediction_result ?? "—"),
            score,
            isPromptError,
            yourVerdict,
            note: p.user_notes ?? "",
            bundle: bundleDisplayName?.trim() || p.test_name || "—",
            graderLogic: evalPrompt.length > 500 ? `${evalPrompt.slice(0, 500)}…` : evalPrompt,
        }
    })
}

function verdictToApi(
    yourVerdict: TestResultTableRow["yourVerdict"]
): number | null {
    if (yourVerdict === "agree") return 1
    if (yourVerdict === "disagree") return 0
    return null
}

interface ScoreCardProps {
    aiScore: string
    adjustedScore: string
    scoreChange: number
}

function ScoreCard({ aiScore, adjustedScore, scoreChange }: ScoreCardProps) {
    const formatScoreChange = (change: number): string => {
        const sign = change >= 0 ? "+" : ""
        return `${sign}${Math.round(change * 10) / 10}%`
    }

    const scoreChangeColor = scoreChange < 0 ? "text-red-700" : "text-green-700"

    return (
        <div className="bg-white border border-slate-200 rounded-[12px] flex gap-[24px] items-start justify-between p-3 flex-1">
            {/* AI Score */}
            <div className="flex flex-col gap-[8px] items-start w-[100px]">
                <div className="flex flex-col gap-[6px] items-start w-[70px]">
                    <p className="font-medium text-[12px] text-slate-500">
                        AI score
                    </p>
                    <p className="font-semibold text-[16px] leading-[1.25] text-slate-700 whitespace-pre">
                        {aiScore}
                    </p>
                </div>
            </div>
            {/* Adjusted Score */}
            <div className="flex flex-col gap-[8px] items-start w-[100px]">
                <div className="flex flex-col gap-[6px] items-start w-full">
                    <p className="font-medium text-[12px] text-slate-500">
                        Adjusted score
                    </p>
                    <div className="flex flex-col gap-[4px] items-start w-full">
                        <p className="font-semibold text-[16px] leading-[1.25] text-slate-700 whitespace-pre">
                            {adjustedScore}
                        </p>
                        <p className={`font-medium text-[12px] ${scoreChangeColor}`}>
                            {formatScoreChange(scoreChange)}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}

interface VerdictsRankedCardProps {
    totalRanked: string
    rankedPercentage: string
    notRanked: string
    agreeCount: string
    agreePercentage: string
    disagreeCount: string
    disagreePercentage: string
}

function VerdictsRankedCard({
    totalRanked,
    rankedPercentage,
    notRanked,
    agreeCount,
    agreePercentage,
    disagreeCount,
    disagreePercentage,
}: VerdictsRankedCardProps) {
    return (
        <div className="bg-white border border-slate-200 rounded-[12px] flex items-start justify-between p-3 flex-1">
            <div className="flex flex-col gap-[6px] items-start w-[150px]">
                <p className="font-medium text-[12px] text-slate-500 w-full">
                    Verdicts ranked
                </p>
                <div className="flex flex-col gap-[4px] items-start w-full">
                    <div className="flex gap-[2px] items-start w-full">
                        <p className="font-semibold text-[16px] leading-[1.25] text-slate-700 whitespace-pre">
                            {totalRanked}
                        </p>
                        <div className="flex flex-col justify-end leading-[0] self-stretch text-[12px] text-slate-500 w-[27px]">
                            <p className="font-medium leading-[normal]">({rankedPercentage})</p>
                        </div>
                    </div>
                    <p className="font-medium text-[12px] text-slate-500 w-full">
                        {notRanked} not ranked
                    </p>
                </div>
            </div>
            <div className="flex gap-[12px] items-start">
                {/* Agree Section */}
                <div className="flex flex-col gap-[4px] items-start rounded-[6px] w-[80px]">
                    <div className="flex gap-[4px] items-center w-full">
                        <ThumbsUp className="size-3 text-green-700" />
                        <p className="font-medium text-[12px] text-green-700 whitespace-pre leading-none">
                            Agree
                        </p>
                    </div>
                    <div className="flex gap-[4px] items-start text-[12px] whitespace-pre w-full">
                        <p className="font-bold text-slate-700">
                            {agreeCount}
                        </p>
                        <p className="font-medium text-slate-500">
                            ({agreePercentage})
                        </p>
                    </div>
                </div>
                {/* Divider */}
                <div className="h-[31px] w-px bg-slate-200" />
                {/* Disagree Section */}
                <div className="flex flex-col gap-[4px] items-start rounded-[6px] w-[80px]">
                    <div className="flex gap-[4px] items-center w-full">
                        <ThumbsDown className="size-3 text-red-700" />
                        <p className="font-medium text-[12px] text-red-700 whitespace-pre leading-none">
                            Disagree
                        </p>
                    </div>
                    <div className="flex gap-[4px] items-start text-[12px] whitespace-pre w-full">
                        <p className="font-bold text-slate-700">
                            {disagreeCount}
                        </p>
                        <p className="font-medium text-slate-500">
                            ({disagreePercentage})
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}

interface VerdictsAdjustedCardProps {
    totalAdjusted: string
    trueToFalseCount: string
    trueToFalsePercentage: string
    falseToTrueCount: string
    falseToTruePercentage: string
}

function VerdictsAdjustedCard({
    totalAdjusted,
    trueToFalseCount,
    trueToFalsePercentage,
    falseToTrueCount,
    falseToTruePercentage,
}: VerdictsAdjustedCardProps) {
    return (
        <div className="bg-white border border-slate-200 rounded-[12px] flex items-start justify-between p-3 flex-1">
            <div className="flex flex-col gap-[6px] items-start w-[150px]">
                <p className="font-medium text-[12px] text-slate-500">
                    Verdicts adjusted
                </p>
                <p className="font-semibold text-[16px] leading-[1.25] text-slate-700 whitespace-pre">
                    {totalAdjusted}
                </p>
            </div>
            <div className="flex gap-[12px] items-start">
                {/* True -> False Section */}
                <div className="flex flex-col gap-[4px] items-start rounded-[6px] w-[80px]">
                    <p className="font-medium text-[12px] text-slate-500 w-full">
                        True –&gt; False
                    </p>
                    <div className="flex gap-[4px] items-start text-[12px] whitespace-pre w-full">
                        <p className="font-bold text-slate-700">
                            {trueToFalseCount}
                        </p>
                        <p className="font-medium text-slate-500">
                            ({trueToFalsePercentage})
                        </p>
                    </div>
                </div>
                {/* Divider */}
                <div className="h-[31px] w-px bg-slate-200" />
                {/* False -> True Section */}
                <div className="flex flex-col gap-[4px] items-start rounded-[6px] w-[80px]">
                    <p className="font-medium text-[12px] text-slate-500 w-full">
                        False –&gt; True
                    </p>
                    <div className="flex gap-[4px] items-start text-[12px] whitespace-pre w-full">
                        <p className="font-bold text-slate-700">
                            {falseToTrueCount}
                        </p>
                        <p className="font-medium text-slate-500">
                            ({falseToTruePercentage})
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}

interface VerdictStatistics {
    totalVerdictsSet: number
    agreeWithScore1: number
    agreeWithScore0: number
    disagreeWithScore1: number
    disagreeWithScore0: number
}

function calculateVerdictStatistics(data: TestResultTableRow[]): VerdictStatistics {
    let totalVerdictsSet = 0
    let agreeWithScore1 = 0
    let agreeWithScore0 = 0
    let disagreeWithScore1 = 0
    let disagreeWithScore0 = 0

    data.forEach((row) => {
        if (row.yourVerdict !== null && row.yourVerdict !== undefined) {
            totalVerdictsSet++

            if (row.yourVerdict === "agree") {
                if (row.score === 1) {
                    agreeWithScore1++
                } else if (row.score === 0) {
                    agreeWithScore0++
                }
            } else if (row.yourVerdict === "disagree") {
                if (row.score === 1) {
                    disagreeWithScore1++
                } else if (row.score === 0) {
                    disagreeWithScore0++
                }
            }
        }
    })

    return {
        totalVerdictsSet,
        agreeWithScore1,
        agreeWithScore0,
        disagreeWithScore1,
        disagreeWithScore0,
    }
}

export interface BundleChartResult {
    chartBars: BundleChartDataItem[]
    incompleteTests: string[]
}

function scoreRowsForTest(rows: TestResultTableRow[]): {
    aiScore: number
    adjustedScore: number
    half: number
} {
    const totalCount = rows.length
    const totalScore = rows.reduce((sum, row) => sum + row.score, 0)
    let disagreeWithScore1 = 0
    let disagreeWithScore0 = 0
    rows.forEach((row) => {
        if (row.yourVerdict === "disagree") {
            if (row.score === 1) disagreeWithScore1++
            else if (row.score === 0) disagreeWithScore0++
        }
    })
    const aiScore = totalCount > 0 ? (totalScore / totalCount) * 100 : 0
    const adjustedScore = adjustedAccuracyPercent(
        totalScore,
        totalCount,
        disagreeWithScore1,
        disagreeWithScore0
    )
    return {
        aiScore: Math.round(aiScore * 100) / 100,
        adjustedScore: Math.round(adjustedScore * 100) / 100,
        half: 0,
    }
}

export function buildBundleChartResult(
    prompts: BenchmarkRunTestPrompt[],
    data: TestResultTableRow[],
    testRunStatus: BenchmarkRunTestStatusSummary[],
    marginHalfWidthPercentByTestId: Record<number, number> | null
): BundleChartResult {
    const statusByTestId = testStatusByTestId(testRunStatus)
    const testGroups = new Map<string, TestResultTableRow[]>()

    data.forEach((row) => {
        const testName = (row.test || "Unknown Test").trim()
        if (!testGroups.has(testName)) testGroups.set(testName, [])
        testGroups.get(testName)!.push(row)
    })

    const chartBars: BundleChartDataItem[] = []
    const incompleteTests: string[] = []

    testGroups.forEach((rows, testName) => {
        const tid =
            rows.map((r) => r.test_id).find((x) => x != null && x !== undefined) ?? null
        const testPrompts =
            tid != null ? promptsForTest(prompts, tid) : []
        const completion = classifyTest(
            testPrompts,
            tid != null ? statusByTestId.get(tid) : undefined
        )

        if (completion !== "fully_complete") {
            incompleteTests.push(testName)
            return
        }

        const scores = scoreRowsForTest(rows)
        const rawHalf =
            tid != null && marginHalfWidthPercentByTestId != null
                ? marginHalfWidthPercentByTestId[tid]
                : undefined
        const half = rawHalf != null && rawHalf > 0 ? rawHalf : 0

        chartBars.push({
            test_name: testName,
            aiScore: scores.aiScore,
            adjustedScore: scores.adjustedScore,
            aiScoreLowerDifference: half,
            aiScoreUpperDifference: half,
            adjustedScoreLowerDifference: half,
            adjustedScoreUpperDifference: half,
        })
    })

    chartBars.sort((a, b) => a.test_name.localeCompare(b.test_name))
    incompleteTests.sort((a, b) => a.localeCompare(b))

    return { chartBars, incompleteTests }
}

function rowsForFullyCompleteTests(
    prompts: BenchmarkRunTestPrompt[],
    data: TestResultTableRow[],
    testRunStatus: BenchmarkRunTestStatusSummary[]
): TestResultTableRow[] {
    const statusByTestId = testStatusByTestId(testRunStatus)
    const allowedTestIds = new Set<number>()
    const byTest = new Map<number, BenchmarkRunTestPrompt[]>()
    for (const p of prompts) {
        if (p.test_id == null) continue
        if (!byTest.has(p.test_id)) byTest.set(p.test_id, [])
        byTest.get(p.test_id)!.push(p)
    }
    for (const [testId, testPrompts] of byTest) {
        if (
            classifyTest(testPrompts, statusByTestId.get(testId)) === "fully_complete"
        ) {
            allowedTestIds.add(testId)
        }
    }
    return data.filter((row) => row.test_id != null && allowedTestIds.has(row.test_id))
}

interface TestResultBundleProps {
    apiPrompts?: BenchmarkRunTestPrompt[] | null
    apiLoading?: boolean
    apiError?: string | null
    /** Only prompts whose test_id is in this list. null = no filter (all prompts). */
    filterTestIds?: number[] | null
    /** Shown in the table bundle column for API-sourced rows. */
    bundleDisplayName?: string | null
    /** Half-width in chart % (0–100) per benchmark_test.id; from API test_margin_of_error. */
    marginHalfWidthPercentByTestId?: Record<number, number> | null
    /** URL `debugMargin=1`: show margin / chart error diagnostics. */
    showMarginDebug?: boolean
    testRunStatus?: BenchmarkRunTestStatusSummary[]
    onAdjustedScoreChange?: (score: number) => void
}

export default function TestResultBundle({
    apiPrompts = null,
    apiLoading = false,
    apiError = null,
    filterTestIds = undefined,
    bundleDisplayName = null,
    marginHalfWidthPercentByTestId = null,
    showMarginDebug = false,
    testRunStatus = [],
    onAdjustedScoreChange,
}: TestResultBundleProps) {
    const [tableData, setTableData] = useState<TestResultTableRow[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const tableDataRef = useRef<TestResultTableRow[]>([])
    const noteDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

    useEffect(() => {
        tableDataRef.current = tableData
    }, [tableData])

    useEffect(() => {
        return () => {
            if (noteDebounceRef.current) {
                clearTimeout(noteDebounceRef.current)
            }
        }
    }, [])

    const persistPromptFeedback = useCallback(
        async (row: TestResultTableRow) => {
            if (row.benchmarkPromptId == null) return
            try {
                await patchBenchmarkRunPromptUserFeedback(
                    row.benchmarkPromptId,
                    {
                        user_evaluation: verdictToApi(row.yourVerdict),
                        user_notes:
                            row.note.trim() === "" ? null : row.note,
                    }
                )
            } catch (e) {
                console.error("Failed to save prompt feedback:", e)
            }
        },
        []
    )

    const scopedApiPrompts = useMemo(() => {
        if (!apiPrompts?.length) return EMPTY_PROMPTS
        if (filterTestIds === null) return apiPrompts
        if (filterTestIds != null && filterTestIds.length > 0) {
            const allowed = new Set(filterTestIds)
            return apiPrompts.filter(
                (p) => p.test_id != null && allowed.has(p.test_id)
            )
        }
        return apiPrompts
    }, [apiPrompts, filterTestIds])

    useEffect(() => {
        if (apiLoading) {
            setIsLoading(true)
            setError(null)
            return
        }
        setIsLoading(false)
        if (apiError) {
            setError(apiError)
            setTableData([])
            return
        }
        setError(null)
        setTableData(promptsToTableRows(scopedApiPrompts, bundleDisplayName))
    }, [
        apiLoading,
        apiError,
        scopedApiPrompts,
        bundleDisplayName,
    ])

    // Calculate verdict statistics (all rows; table shows everything)
    const verdictStats = calculateVerdictStatistics(tableData)

    const scorecardRows = useMemo(
        () => rowsForFullyCompleteTests(scopedApiPrompts, tableData, testRunStatus),
        [scopedApiPrompts, tableData, testRunStatus]
    )
    const scorecardVerdictStats = useMemo(
        () => calculateVerdictStatistics(scorecardRows),
        [scorecardRows]
    )

    // Calculate total number of prompts
    const totalPrompts = tableData.length

    // Calculate adjusted verdict statistics
    const totalAdjusted = verdictStats.disagreeWithScore1 + verdictStats.disagreeWithScore0
    const trueToFalseCount = verdictStats.disagreeWithScore1
    const falseToTrueCount = verdictStats.disagreeWithScore0
    const trueToFalsePercentage = totalAdjusted > 0 
        ? `${Math.round((trueToFalseCount / totalAdjusted) * 100)}%`
        : "0%"
    const falseToTruePercentage = totalAdjusted > 0
        ? `${Math.round((falseToTrueCount / totalAdjusted) * 100)}%`
        : "0%"

    // Calculate verdicts ranked statistics
    const totalVerdictsSet = verdictStats.totalVerdictsSet
    const notRanked = totalPrompts - totalVerdictsSet
    const rankedPercentage = totalPrompts > 0
        ? `${Math.round((totalVerdictsSet / totalPrompts) * 100)}%`
        : "0%"
    const agreeCount = verdictStats.agreeWithScore1 + verdictStats.agreeWithScore0
    const agreePercentage = totalVerdictsSet > 0
        ? `${Math.round((agreeCount / totalVerdictsSet) * 100)}%`
        : "0%"
    const disagreeCount = verdictStats.disagreeWithScore1 + verdictStats.disagreeWithScore0
    const disagreePercentage = totalVerdictsSet > 0
        ? `${Math.round((disagreeCount / totalVerdictsSet) * 100)}%`
        : "0%"

    // Format numbers with commas
    const formatNumber = (num: number): string => {
        return num.toLocaleString()
    }

    const chartResult = useMemo(
        () =>
            buildBundleChartResult(
                scopedApiPrompts,
                tableData,
                testRunStatus,
                marginHalfWidthPercentByTestId
            ),
        [scopedApiPrompts, tableData, testRunStatus, marginHalfWidthPercentByTestId]
    )
    const chartData = chartResult.chartBars
    const incompleteTests = chartResult.incompleteTests

    const marginDebugSummary =
        marginHalfWidthPercentByTestId == null
            ? String(marginHalfWidthPercentByTestId)
            : JSON.stringify(marginHalfWidthPercentByTestId)
    const firstRowDiffs = chartData[0]

    // Calculate overall AI score and adjusted score (fully complete tests only)
    const totalPromptsForScore = scorecardRows.length
    const totalScore = scorecardRows.reduce((sum, row) => sum + row.score, 0)
    const overallAiScore = totalPromptsForScore > 0
        ? (totalScore / totalPromptsForScore) * 100
        : 0

    const overallDisagreeWithScore1 = scorecardVerdictStats.disagreeWithScore1
    const overallDisagreeWithScore0 = scorecardVerdictStats.disagreeWithScore0
    
    const overallAdjustedScore = adjustedAccuracyPercent(
        totalScore,
        totalPromptsForScore,
        overallDisagreeWithScore1,
        overallDisagreeWithScore0
    )
    const overallScoreChange = overallAdjustedScore - overallAiScore

    // Parent often passes an inline callback (e.g. from map); keep out of effect deps to avoid update loops.
    const onAdjustedScoreChangeRef = useRef(onAdjustedScoreChange)
    onAdjustedScoreChangeRef.current = onAdjustedScoreChange

    useEffect(() => {
        if (!onAdjustedScoreChangeRef.current || isLoading) return
        onAdjustedScoreChangeRef.current(overallAdjustedScore)
    }, [overallAdjustedScore, isLoading])

    // Format scores for ScoreCard
    const formatScore = (score: number): string => {
        return `${Math.round(score * 10) / 10}%`
    }

    return (
        <div className="flex flex-col gap-[8px] items-start w-full">
            {/* Score Cards Row */}
            <div className="flex flex-row items-stretch gap-[8px] w-full mb-2 mt-2">
                <ScoreCard
                    aiScore={formatScore(overallAiScore)}
                    adjustedScore={formatScore(overallAdjustedScore)}
                    scoreChange={overallScoreChange}
                />
                <VerdictsRankedCard
                    totalRanked={formatNumber(totalVerdictsSet)}
                    rankedPercentage={rankedPercentage}
                    notRanked={formatNumber(notRanked)}
                    agreeCount={formatNumber(agreeCount)}
                    agreePercentage={agreePercentage}
                    disagreeCount={formatNumber(disagreeCount)}
                    disagreePercentage={disagreePercentage}
                />
                <VerdictsAdjustedCard
                    totalAdjusted={formatNumber(totalAdjusted)}
                    trueToFalseCount={formatNumber(trueToFalseCount)}
                    trueToFalsePercentage={trueToFalsePercentage}
                    falseToTrueCount={formatNumber(falseToTrueCount)}
                    falseToTruePercentage={falseToTruePercentage}
                />
            </div>
            {showMarginDebug ? (
                <div
                    className="w-full rounded-md border border-amber-300 bg-amber-50 px-2 py-1 font-mono text-[10px] leading-snug text-amber-950"
                    data-testid="bundle-margin-debug"
                >
                    <span className="font-semibold text-amber-900">[debug BundleChart]</span>{" "}
                    marginHalfWidthPercentByTestId={marginDebugSummary}{" "}
                    | tableRows={tableData.length} | chartRows={chartData.length}
                    {firstRowDiffs ? (
                        <>
                            {" "}
                            | first bar aiΔ/ adjΔ=
                            {firstRowDiffs.aiScoreLowerDifference}/{firstRowDiffs.adjustedScoreLowerDifference}
                        </>
                    ) : null}
                </div>
            ) : null}
            {/* Chart */}
            <BundleChart
                title={`Tests (${chartData.length + incompleteTests.length})`}
                chartData={chartData}
                incompleteTests={incompleteTests}
            />
            {/* Table */}
            {isLoading ? (
                <div className="w-full p-4 text-center text-slate-500">
                    Loading data...
                </div>
            ) : error ? (
                <div className="w-full p-4 text-center text-red-500">
                    Error: {error}
                </div>
            ) : (
                <TestResultTable
                    data={tableData}
                    onDataChange={(id, updates) => {
                        setTableData((prevData) => {
                            const next = prevData.map((row) =>
                                row.id === id ? { ...row, ...updates } : row
                            )
                            tableDataRef.current = next
                            const row = next.find((r) => r.id === id)
                            if (row && row.benchmarkPromptId != null) {
                                if (
                                    Object.prototype.hasOwnProperty.call(
                                        updates,
                                        "yourVerdict"
                                    )
                                ) {
                                    if (noteDebounceRef.current) {
                                        clearTimeout(noteDebounceRef.current)
                                        noteDebounceRef.current = null
                                    }
                                    void persistPromptFeedback(row)
                                }
                                if (
                                    Object.prototype.hasOwnProperty.call(
                                        updates,
                                        "note"
                                    )
                                ) {
                                    if (noteDebounceRef.current) {
                                        clearTimeout(noteDebounceRef.current)
                                    }
                                    noteDebounceRef.current = setTimeout(() => {
                                        noteDebounceRef.current = null
                                        const latest = tableDataRef.current.find(
                                            (r) => r.id === id
                                        )
                                        if (latest) {
                                            void persistPromptFeedback(latest)
                                        }
                                    }, 500)
                                }
                            }
                            return next
                        })
                    }}
                />
            )}
        </div>
    )
}