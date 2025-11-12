"use client"
import React from "react"
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, ReferenceLine, ErrorBar, Cell } from "recharts"

export interface BundleChartDataItem {
    name: string
    aiScore: number
    adjustedScore: number
    aiScoreLowerDifference: number
    aiScoreUpperDifference: number
    adjustedScoreLowerDifference: number
    adjustedScoreUpperDifference: number
}

interface BundleChartProps {
    title: string
    chartData: BundleChartDataItem[]
}

export default function BundleChart({ title, chartData }: BundleChartProps) {
    // Y-axis ticks to match design
    const yAxisTicks = [20, 40, 60, 80, 100]

    // Custom formatter for Y-axis labels
    const formatYAxisLabel = (value: number) => `${value}%`

    // Custom X-axis tick component for recipe names
    const CustomXAxisTick = ({ x, y, payload }: { x?: number; y?: number; payload?: { value: string } }) => {
        if (x === undefined || y === undefined || !payload) return null
        
        // Truncate text to max 12 characters
        const maxChars = 16
        const truncatedText = payload.value.length > maxChars 
            ? payload.value.substring(0, maxChars - 3) + '...' 
            : payload.value
        
        return (
            <g transform={`translate(${x},${y})`}>
                <text
                    x={0}
                    y={0}
                    dy={16}
                    textAnchor="middle"
                    fill="#60646c"
                    fontSize={10}
                    fontFamily="Inter, sans-serif"
                    fontWeight={500}
                >
                    {truncatedText}
                </text>
            </g>
        )
    }

    // Custom Y-axis tick component
    const CustomYAxisTick = ({ x, y, payload }: { x?: number; y?: number; payload?: { value: number } }) => {
        if (x === undefined || y === undefined || payload === undefined) return null
        return (
            <g transform={`translate(${x},${y})`}>
                <text
                    x={-8}
                    y={0}
                    dy={3}
                    textAnchor="end"
                    fill="#60646c"
                    fontSize={10}
                    fontFamily="Inter, sans-serif"
                    fontWeight={500}
                >
                    {formatYAxisLabel(payload.value)}
                </text>
            </g>
        )
    }

    // Custom tooltip
    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload
            const confidenceLevel = 95 // Standard confidence level
            
            return (
                <div className="bg-white border border-slate-200 rounded-lg shadow-lg p-3">
                    <p className="font-semibold text-sm text-slate-700 mb-2">
                        {data.name}
                    </p>
                    {payload.map((entry: any, index: number) => {
                        // Get the appropriate lower and upper differences based on the entry name
                        const isAiScore = entry.dataKey === 'aiScore'
                        const lowerDiff = isAiScore ? data.aiScoreLowerDifference : data.adjustedScoreLowerDifference
                        const upperDiff = isAiScore ? data.aiScoreUpperDifference : data.adjustedScoreUpperDifference
                        
                        const lowerBound = Math.max(0, entry.value - lowerDiff)
                        const upperBound = Math.min(100, entry.value + upperDiff)
                        
                        return (
                            <div key={index} className="mb-2">
                                <p className="font-medium text-sm text-slate-600" style={{ color: entry.color }}>
                                    {entry.name}: {entry.value}%
                                </p>
                                <p className="text-xs text-slate-500 mt-1">
                                    Confidence level at {confidenceLevel}% level: [{lowerBound.toFixed(1)}, {upperBound.toFixed(1)}]
                                </p>
                            </div>
                        )
                    })}
                </div>
            )
        }
        return null
    }

    // Custom legend
    const CustomLegend = () => {
        return (
            <div className="flex gap-8 items-center justify-center mt-2">
                <div className="flex gap-1 items-center">
                    <div className="relative w-3 h-3 flex items-center justify-center">
                        <div className="absolute w-px h-3 bg-slate-700" />
                        <div className="absolute top-0 w-3 h-px bg-slate-700" />
                        <div className="absolute bottom-0 w-3 h-px bg-slate-700" />
                    </div>
                    <p className="font-medium text-[12px] text-slate-700 leading-none">
                        Confidence interval
                    </p>
                </div>
                <div className="flex gap-1 items-center">
                    <div className="w-3 h-3 bg-orange-400 rounded-sm" />
                    <p className="font-medium text-[12px] text-slate-700 leading-none">
                        AI score
                    </p>
                </div>
                <div className="flex gap-1 items-center">
                    <div className="w-3 h-3 bg-blue-400 rounded-sm" />
                    <p className="font-medium text-[12px] text-slate-700 leading-none">
                        Adjusted score
                    </p>
                </div>
            </div>
        )
    }

    // Prepare data with error values for ErrorBar
    // ErrorBar supports asymmetric errors using [lower, upper] arrays
    // Cap error values so upper bound doesn't exceed 100 and lower bound doesn't go below 0
    const chartDataWithError = chartData.map(entry => {
        // Calculate bounds for AI score, capping at 0 and 100
        const aiScoreLowerBound = Math.max(0, entry.aiScore - entry.aiScoreLowerDifference)
        const aiScoreUpperBound = Math.min(100, entry.aiScore + entry.aiScoreUpperDifference)
        const aiScoreError: [number, number] = [
            entry.aiScore - aiScoreLowerBound, // lower error
            aiScoreUpperBound - entry.aiScore  // upper error
        ]
        
        // Calculate bounds for Adjusted score, capping at 0 and 100
        const adjustedScoreLowerBound = Math.max(0, entry.adjustedScore - entry.adjustedScoreLowerDifference)
        const adjustedScoreUpperBound = Math.min(100, entry.adjustedScore + entry.adjustedScoreUpperDifference)
        const adjustedScoreError: [number, number] = [
            entry.adjustedScore - adjustedScoreLowerBound, // lower error
            adjustedScoreUpperBound - entry.adjustedScore  // upper error
        ]
        
        return {
            ...entry,
            aiScoreError,
            adjustedScoreError,
        }
    })

    return (
        <div className="bg-white border border-slate-200 rounded-[12px] flex flex-col gap-2 p-3 w-full">
            {/* Title */}
            <div className="flex items-start justify-between pb-2">
                <p className="font-semibold text-[12px] text-slate-700">
                    {title}
                </p>
            </div>

            {/* Chart */}
            <div className="w-full">
                <ResponsiveContainer width="100%" height={220}>
                    <BarChart
                        data={chartDataWithError}
                        margin={{ top: 10, right: 20, bottom: 0, left: 0 }}
                        barCategoryGap="10%"
                        barSize={16}
                    >
                        <XAxis
                            type="category"
                            dataKey="name"
                            tick={<CustomXAxisTick />}
                            axisLine={false}
                            tickLine={false}
                            interval={0}
                        />
                        <YAxis
                            type="number"
                            domain={[0, 100]}
                            ticks={yAxisTicks}
                            tickFormatter={formatYAxisLabel}
                            tick={<CustomYAxisTick />}
                            axisLine={false}
                            tickLine={false}
                            interval={0}
                            allowDataOverflow={false}
                        />
                        {/* Reference lines for Y-axis grid */}
                        {yAxisTicks.map((tick) => (
                            <ReferenceLine
                                key={tick}
                                y={tick}
                                stroke="#E2E8F0"
                                strokeWidth={1}
                                strokeDasharray="0"
                            />
                        ))}
                        <Tooltip content={<CustomTooltip />} />
                        {/* AI Score Bar */}
                        <Bar
                            dataKey="aiScore"
                            fill="#FB923C"
                            radius={0}
                        >
                            {chartDataWithError.map((entry, index) => (
                                <Cell key={`ai-cell-${index}-${entry.name}`} fill="#FB923C" />
                            ))}
                            {/* Only render ErrorBar if there are actual error values */}
                            {chartDataWithError.some(entry => 
                                entry.aiScoreError[0] > 0 || entry.aiScoreError[1] > 0
                            ) && (
                                <ErrorBar
                                    key="ai-error-bar"
                                    dataKey="aiScoreError"
                                    width={2}
                                    strokeWidth={1.5}
                                    stroke="#334155"
                                    direction="y"
                                />
                            )}
                        </Bar>
                        {/* Adjusted Score Bar */}
                        <Bar
                            dataKey="adjustedScore"
                            fill="#60A5FA"
                            radius={0}
                        >
                            {chartDataWithError.map((entry, index) => (
                                <Cell key={`adjusted-cell-${index}-${entry.name}`} fill="#60A5FA" />
                            ))}
                            {/* Only render ErrorBar if there are actual error values */}
                            {chartDataWithError.some(entry => 
                                entry.adjustedScoreError[0] > 0 || entry.adjustedScoreError[1] > 0
                            ) && (
                                <ErrorBar
                                    key="adjusted-error-bar"
                                    dataKey="adjustedScoreError"
                                    width={2}
                                    strokeWidth={1.5}
                                    stroke="#334155"
                                    direction="y"
                                />
                            )}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Legend */}
            <CustomLegend />
        </div>
    )
}

