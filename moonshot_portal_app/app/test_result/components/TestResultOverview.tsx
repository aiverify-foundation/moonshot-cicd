"use client"
import { InfoIcon, XIcon } from "lucide-react"
import React, { useState } from "react"
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, LabelList, Tooltip, ErrorBar, Text, ReferenceLine } from "recharts"
import { BenchmarkRunResultsBundleSummary, BenchmarkRunTestPrompt, BenchmarkRunTestStatusSummary } from "@/lib/api"
import TestResultInProgress from "./TestResultInProgress"
import TestResultCompletedWithErrors, {
    groupErroredTestsByBundle,
} from "./TestResultCompletedWithErrors"
import { runHasPromptErrors } from "./testCompletion"

function TestResultNote() {
    const [isVisible, setIsVisible] = useState(true)

    if (!isVisible) return null

    return (
        <div
            className="bg-blue-50 border border-blue-200 rounded-lg flex gap-2 items-start p-2"
            data-testid="test-result-overview-note"
        >
            <div className="shrink-0 size-5 mt-0.5">
                <InfoIcon className="size-5 text-slate-700" />
            </div>
            <div className="flex flex-col gap-2 flex-1">
                <div className="flex flex-col gap-1">
                    <p className="font-semibold text-[14px] text-slate-700">
                        Human review recommended
                    </p>
                    <p className="font-medium text-[14px] text-slate-700">
                        Automated evaluators may not always be accurate. Please review individual evaluations carefully before relying on the overall test results.
                    </p>
                </div>
            </div>
            <button 
                onClick={() => setIsVisible(false)}
                className="shrink-0 size-4 mt-0.5 hover:opacity-70 transition-opacity"
                aria-label="Close"
            >
                <XIcon className="size-4 text-slate-500" />
            </button>
        </div>
    )
}

export interface ChartDataItem {
    test_name: string
    adjusted_percentage_score: number
    test_id?: number | null
    /** Half-width in chart % (0–100 domain) for this test; from API test_margin_of_error. */
    marginHalfWidthPercent?: number | null
}

interface ReportChartProps {
    chartData: ChartDataItem[]
    bundleName: string
    showMarginDebug?: boolean
}

const BUNDLE_CONFIDENCE_LEVEL_PCT = 95

function ReportChartScrollAdjustableHeight({
    chartData,
    bundleName,
    showMarginDebug = false,
}: ReportChartProps) {
    // Calculate average of all chart data values
    const averageValue = chartData.length > 0
        ? Math.round(chartData.reduce((sum, item) => sum + item.adjusted_percentage_score, 0) / chartData.length)
        : 0

    // Custom Y-axis ticks to match design
    const yAxisTicks = [20, 40, 60, 80, 100]

    // Custom formatter for Y-axis labels
    const formatYAxisLabel = (value: number) => `${value}%`

    // ErrorBar supports asymmetric errors using [lower, upper] arrays.
    // Cap so the whisker stays inside the 0–100 score domain (Recharts does not clip ErrorBar to axis domain).
    const chartDataWithConfidence = chartData.map((entry) => {
        const half =
            entry.marginHalfWidthPercent != null && entry.marginHalfWidthPercent > 0
                ? entry.marginHalfWidthPercent
                : 0
        const score = entry.adjusted_percentage_score
        const lowerErr = score - Math.max(0, score - half)
        const upperErr = Math.min(100, score + half) - score
        // Recharts ErrorBar keys each <line> by coordinates only; when both errors are 0 the
        // left and right caps are identical segments and React warns about duplicate keys.
        const error: [number, number] | null =
            lowerErr === 0 && upperErr === 0 ? null : [lowerErr, upperErr]
        return {
            ...entry,
            error,
            errorHalf: half,
        }
    })

    const showErrorBar = chartDataWithConfidence.some(
        (e) => e.error != null && (e.error[0] > 0 || e.error[1] > 0)
    )

    // Custom Y-axis tick component that uses HTML foreignObject for CSS-based truncation
    // Recharts will automatically truncate based on the container width (170px)
    const CustomYAxisTick = ({ x, y, payload }: { x?: number; y?: number; payload?: { value: string } }) => {
        if (x === undefined || y === undefined || !payload) return null
        return (
            <g>
                <foreignObject x={x - 130} y={y - 10} width={120} height={20}>
                    <div
                        style={{
                            fontSize: '14px',
                            fontFamily: 'Inter, sans-serif',
                            fontWeight: 500,
                            color: '#0F172A',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            width: '100%',
                            textAlign: 'left',
                        }}
                        title={payload.value} // Show full text on hover
                    >
                        {payload.value}
                    </div>
                </foreignObject>
            </g>
        )
    }

    return (
        <div className="bg-white border border-slate-200 rounded-[12px] flex flex-col gap-1 p-3 w-full h-[300px] relative">
            {/* Header section */}
            <div className="flex items-start justify-between pb-2 pt-0 px-0 w-full">
                <div className="flex flex-col gap-[2px] items-start text-[12px]">
                    <p className="font-semibold text-slate-700">
                        {bundleName}
                    </p>
                    <p className="font-medium text-slate-500">
                        0% reviewed
                    </p>
                </div>
                <div className="flex gap-2 items-center">
                    <div className="bg-green-100 border border-green-200 flex gap-1 items-center justify-center p-1 rounded-[6px]">
                        <p className="font-semibold text-[12px] text-green-800 whitespace-pre">
                            {averageValue}%
                        </p>
                    </div>
                </div>
            </div>

            {showMarginDebug ? (
                <div className="mb-1 max-w-full rounded border border-amber-300 bg-amber-50 px-2 py-1 font-mono text-[10px] leading-snug text-amber-950">
                    <span className="font-semibold text-amber-900">[debug]</span> per-row
                    marginHalfWidthPercent=
                    {JSON.stringify(chartData.map((e) => e.marginHalfWidthPercent ?? null))}{" "}
                    | chartRows={chartData.length} | showErrorBar={String(showErrorBar)}
                </div>
            ) : null}

            {/* Chart Content */}
            <div className="flex flex-col gap-4 items-start w-full flex-1 overflow-hidden">
                {/* Chart area - scrollable */}
                <div className="w-full flex-1 overflow-y-auto overflow-x-hidden">
                    <ResponsiveContainer width="100%" height={Math.max(60, chartData.length * 50)}>
                        <BarChart
                            data={chartDataWithConfidence}
                            layout="vertical"
                            margin={{ top: 5, right: 70, bottom: 5, left: -30 }}
                            barCategoryGap="10%"
                            barSize={28}
                        >
                            <XAxis 
                                type="number"
                                domain={[0, 100]}
                                ticks={yAxisTicks}
                                tickFormatter={formatYAxisLabel}
                                tick={{ 
                                    fontSize: 10, 
                                    fill: '#0F172A',
                                    fontFamily: 'Inter',
                                    fontWeight: 500,
                                }}
                                axisLine={false}
                                tickLine={false}
                                height={18}
                            />
                            <YAxis 
                                type="category"
                                dataKey="test_name"
                                tick={<CustomYAxisTick />}
                                axisLine={false}
                                tickLine={false}
                                width={170}
                                interval={0}
                            />
                            {/* XAxis guide lines */}
                            {yAxisTicks.map((tick) => (
                                <ReferenceLine
                                    key={tick}
                                    x={tick}
                                    stroke="#E2E8F0"
                                    strokeWidth={1}
                                    strokeDasharray="3 3"
                                />
                            ))}
                            <Tooltip
                                content={({ active, payload }) => {
                                    if (active && payload && payload.length) {
                                        const data = payload[0].payload;
                                        const lowerBound = Math.max(0, Math.round((data.adjusted_percentage_score - data.errorHalf) * 10) / 10);
                                        const upperBound = Math.min(100, Math.round((data.adjusted_percentage_score + data.errorHalf) * 10) / 10);
                                        return (
                                            <div className="bg-white border border-slate-200 rounded-lg shadow-lg p-3">
                                                <p className="font-semibold text-sm text-slate-700 mb-1">
                                                    {data.test_name}
                                                </p>
                                                <p className="font-medium text-sm text-slate-600">
                                                    Score: {data.adjusted_percentage_score}%
                                                </p>
                                                {data.errorHalf > 0 ? (
                                                    <>
                                                        <p className="font-medium text-sm text-slate-600 mt-1">
                                                            {BUNDLE_CONFIDENCE_LEVEL_PCT}% band (test margin of error): [{lowerBound}%, {upperBound}%]
                                                        </p>
                                                        <p className="text-xs text-slate-500 mt-1">
                                                            Interval is on the mean score for this test&apos;s prompts only (same scale as the bar).
                                                        </p>
                                                    </>
                                                ) : null}
                                            </div>
                                        );
                                    }
                                    return null;
                                }}
                            />
                            <Bar 
                                dataKey="adjusted_percentage_score" 
                                fill="#60A5FA"
                                radius={0}
                            >
                                {chartDataWithConfidence.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill="#60A5FA" />
                                ))}
                                {showErrorBar ? (
                                    <ErrorBar
                                        dataKey="error"
                                        width={2}
                                        strokeWidth={2}
                                        stroke="#0F172A"
                                        direction="x"
                                    />
                                ) : null}
                                <LabelList 
                                    dataKey="adjusted_percentage_score" 
                                    position="right"
                                    content={(props: { x?: number | string; y?: number | string; value?: number | string }) => {
                                        const { x, y, value } = props;
                                        if (x === undefined || y === undefined || value === undefined) return null;
                                        const xNum = typeof x === 'string' ? parseFloat(x) : x;
                                        const yNum = typeof y === 'string' ? parseFloat(y) : y;
                                        return (
                                            <Text
                                                x={xNum}
                                                y={yNum}
                                                //dx={400}
                                                dx={10}
                                                dy={15}
                                                fontSize={12}
                                                fontFamily="Inter"
                                                fill="#0F172A"
                                                textAnchor="start"
                                                verticalAnchor="middle"
                                            >
                                                {`${value}%`}
                                            </Text>
                                        );
                                    }}
                                />
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    )
}

export interface OverviewBundleChart {
    bundleName: string
    data: ChartDataItem[]
}

export interface TestResultOverviewProps {
    overviewLoading?: boolean
    overviewError?: string | null
    /** One chart per DB bundle (or a single "All results" entry for legacy runs). */
    bundleCharts?: OverviewBundleChart[]
    /** URL `debugMargin=1`: show margin / ErrorBar diagnostics on charts. */
    showMarginDebug?: boolean
    /** When true, show only the in-progress progress card (no charts or note). */
    isRunInProgress?: boolean
    prompts?: BenchmarkRunTestPrompt[]
    resultBundles?: BenchmarkRunResultsBundleSummary[]
    testRunStatus?: BenchmarkRunTestStatusSummary[]
}

function gridClassForChartCount(n: number): string {
    if (n >= 3) return "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
    if (n === 2) return "grid grid-cols-1 sm:grid-cols-2 gap-4"
    return "grid grid-cols-1 max-w-xl gap-4"
}

export default function TestResultOverview({
    overviewLoading = false,
    overviewError = null,
    bundleCharts = [],
    showMarginDebug = false,
    isRunInProgress = false,
    prompts = [],
    resultBundles = [],
    testRunStatus = [],
}: TestResultOverviewProps) {
    if (overviewLoading) {
        return (
            <div className="mt-4 text-sm text-slate-600">Loading overview…</div>
        )
    }

    if (overviewError) {
        return (
            <div className="mt-4 text-sm text-red-600">{overviewError}</div>
        )
    }

    if (isRunInProgress) {
        return (
            <div className="flex flex-col gap-4 mt-2">
                <TestResultInProgress
                  prompts={prompts}
                  bundles={resultBundles}
                  testRunStatus={testRunStatus}
                />
            </div>
        )
    }

    const hasRunErrors = runHasPromptErrors(prompts)
    const erroredTestGroups = hasRunErrors
        ? groupErroredTestsByBundle(prompts, resultBundles, testRunStatus)
        : []

    const chartsWithData = bundleCharts.filter((c) => c.data.length > 0)

    if (!hasRunErrors && chartsWithData.length === 0) {
        return (
            <div className="flex flex-col gap-4 mt-2">
                <TestResultNote />
                <p className="text-sm text-slate-600">
                    No chart data yet (prompts need evaluation scores).
                </p>
            </div>
        )
    }

    return (
        <div className="flex flex-col gap-4 mt-2">
            {hasRunErrors ? (
                <TestResultCompletedWithErrors groups={erroredTestGroups} />
            ) : null}
            {chartsWithData.length > 0 ? (
                <>
                    <TestResultNote />
                    <div
                        className={gridClassForChartCount(chartsWithData.length)}
                        data-testid="test-result-overview-charts"
                    >
                        {chartsWithData.map((c, i) => (
                            <ReportChartScrollAdjustableHeight
                                key={`${c.bundleName}-${i}`}
                                chartData={c.data}
                                bundleName={c.bundleName}
                                showMarginDebug={showMarginDebug}
                            />
                        ))}
                    </div>
                </>
            ) : hasRunErrors ? (
                <p className="text-sm text-slate-600">
                    No fully completed tests to chart in this run.
                </p>
            ) : null}
        </div>
    )
}