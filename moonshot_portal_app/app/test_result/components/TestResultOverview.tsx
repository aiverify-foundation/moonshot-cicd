"use client"
import { InfoIcon, XIcon } from "lucide-react"
import React, { useState } from "react"
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, LabelList, Tooltip, ErrorBar, Text, ReferenceLine } from "recharts"

function TestResultNote() {
    const [isVisible, setIsVisible] = useState(true)

    if (!isVisible) return null

    return (
        <div className="bg-blue-50 border border-blue-200 rounded-lg flex gap-2 items-start p-2">
            <div className="shrink-0 size-5 mt-0.5">
                <InfoIcon className="size-5 text-slate-700" />
            </div>
            <div className="flex flex-col gap-2 flex-1">
                <div className="flex flex-col gap-1">
                    <p className="font-semibold text-[14px] text-slate-700">
                        Making sense of test results
                    </p>
                    <p className="font-medium text-[14px] text-slate-700">
                        AI evaluations can be inaccurate at times. Review each verdict carefully before you make any decisions.
                    </p>
                </div>
                <div className="flex gap-2 items-center">
                    <button className="font-bold text-[14px] text-slate-700 hover:underline">
                        Learn more
                    </button>
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
}

interface ReportChartProps {
    chartData: ChartDataItem[]
    bundleName: string
}


function ReportChartScrollAdjustableHeight({ chartData, bundleName }: ReportChartProps) {
    // Calculate average of all chart data values
    const averageValue = chartData.length > 0
        ? Math.round(chartData.reduce((sum, item) => sum + item.adjusted_percentage_score, 0) / chartData.length)
        : 0

    // Custom Y-axis ticks to match design
    const yAxisTicks = [20, 40, 60, 80, 100]

    // Custom formatter for Y-axis labels
    const formatYAxisLabel = (value: number) => `${value}%`

    // Calculate confidence intervals and add to data
    const chartDataWithConfidence = chartData.map(entry => {
        // Fixed confidence interval of 7.8
        const confidenceInterval = 7.8;
        // For ErrorBar, we use the confidence interval amount as the error value
        // It will be displayed symmetrically (±)
        return {
            ...entry,
            error: confidenceInterval,
        };
    });

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
                                        // Calculate lower and upper bounds
                                        const lowerBound = Math.max(0, Math.round((data.adjusted_percentage_score - data.error) * 10) / 10);
                                        const upperBound = Math.min(100, Math.round((data.adjusted_percentage_score + data.error) * 10) / 10);
                                        return (
                                            <div className="bg-white border border-slate-200 rounded-lg shadow-lg p-3">
                                                <p className="font-semibold text-sm text-slate-700 mb-1">
                                                    {data.test_name}
                                                </p>
                                                <p className="font-medium text-sm text-slate-600">
                                                    Score: {data.adjusted_percentage_score}%
                                                </p>
                                                <p className="font-medium text-sm text-slate-600">
                                                    Confidence Interval: [{lowerBound}%, {upperBound}%]
                                                </p>
                                                
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
                                <ErrorBar 
                                    dataKey="error"
                                    width={2}
                                    strokeWidth={2}
                                    stroke="#0F172A"
                                    direction="x"
                                />
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
    /** When false, show Figma demo charts. */
    runMode?: boolean
    overviewLoading?: boolean
    overviewError?: string | null
    /** Real run: one chart per DB bundle (or a single "All results" entry for legacy runs). */
    bundleCharts?: OverviewBundleChart[]
}

const demoUndesirable: ChartDataItem[] = [
    { test_name: "MLCommons AILuminate - Hate", adjusted_percentage_score: 79 },
]

const demoDisclosure: ChartDataItem[] = [
    { test_name: "MLCommons AILuminate - Privacy - English", adjusted_percentage_score: 80 },
]

function gridClassForChartCount(n: number): string {
    if (n >= 3) return "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
    if (n === 2) return "grid grid-cols-1 sm:grid-cols-2 gap-4"
    return "grid grid-cols-1 max-w-xl gap-4"
}

export default function TestResultOverview({
    runMode = false,
    overviewLoading = false,
    overviewError = null,
    bundleCharts = [],
}: TestResultOverviewProps) {
    if (!runMode) {
        return (
            <div className="flex flex-col gap-4 mt-2">
                <TestResultNote />
                <div className="grid grid-cols-2 gap-4">
                    <ReportChartScrollAdjustableHeight chartData={demoUndesirable} bundleName="Undesirable Content" />
                    <ReportChartScrollAdjustableHeight chartData={demoDisclosure} bundleName="Data Disclosure" />
                </div>
            </div>
        )
    }

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

    const chartsWithData = bundleCharts.filter((c) => c.data.length > 0)

    if (chartsWithData.length === 0) {
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
            <TestResultNote />
            <div className={gridClassForChartCount(chartsWithData.length)}>
                {chartsWithData.map((c, i) => (
                    <ReportChartScrollAdjustableHeight
                        key={`${c.bundleName}-${i}`}
                        chartData={c.data}
                        bundleName={c.bundleName}
                    />
                ))}
            </div>
        </div>
    )
}