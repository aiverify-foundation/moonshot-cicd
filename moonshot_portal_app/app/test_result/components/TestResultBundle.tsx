"use client"
import React, { useState, useEffect } from "react"
import { ThumbsUp, ThumbsDown } from "lucide-react"
import BundleChart, { BundleChartDataItem } from "./BundleChart"
import TestResultTable, { TestResultTableRow } from "./TestResultTable"
import { parseCsvData } from "./parseCsvData"

interface ScoreCardProps {
    aiScore: string
    adjustedScore: string
    scoreChange: string
}

function ScoreCard({ aiScore, adjustedScore, scoreChange }: ScoreCardProps) {
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
                        <p className="font-medium text-[12px] text-green-700">
                            {scoreChange}
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

export default function TestResultBundle() {
    const [tableData, setTableData] = useState<TestResultTableRow[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Load CSV data on component mount
    useEffect(() => {
        const loadCsvData = async () => {
            try {
                setIsLoading(true)
                setError(null)
                const data = await parseCsvData()
                setTableData(data)
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load CSV data")
                console.error("Error loading CSV data:", err)
            } finally {
                setIsLoading(false)
            }
        }

        loadCsvData()
    }, [])

    // Calculate verdict statistics
    const verdictStats = calculateVerdictStatistics(tableData)

    // Calculate adjusted verdict statistics
    const totalAdjusted = verdictStats.totalVerdictsSet
    const trueToFalseCount = verdictStats.disagreeWithScore1
    const falseToTrueCount = verdictStats.disagreeWithScore0
    const trueToFalsePercentage = totalAdjusted > 0 
        ? `${Math.round((trueToFalseCount / totalAdjusted) * 100)}%`
        : "0%"
    const falseToTruePercentage = totalAdjusted > 0
        ? `${Math.round((falseToTrueCount / totalAdjusted) * 100)}%`
        : "0%"

    // Format numbers with commas
    const formatNumber = (num: number): string => {
        return num.toLocaleString()
    }

    // Sample chart data
    const chartData: BundleChartDataItem[] = [
        { name: "MMLU", aiScore: 91, adjustedScore: 95, aiScoreLowerDifference: 5, aiScoreUpperDifference: 5, adjustedScoreLowerDifference: 5, adjustedScoreUpperDifference: 5 },
        { name: "Facts about Singapore", aiScore: 35, adjustedScore: 40, aiScoreLowerDifference: 5, aiScoreUpperDifference: 5, adjustedScoreLowerDifference: 5, adjustedScoreUpperDifference: 5 },
        { name: "Facts about Singapore", aiScore: 82, adjustedScore: 88, aiScoreLowerDifference: 5, aiScoreUpperDifference: 5, adjustedScoreLowerDifference: 5, adjustedScoreUpperDifference: 5 },
        { name: "Facts about Singapore", aiScore: 14, adjustedScore: 20, aiScoreLowerDifference: 5, aiScoreUpperDifference: 5, adjustedScoreLowerDifference: 5, adjustedScoreUpperDifference: 5 },
        { name: "Facts about Singapore", aiScore: 69, adjustedScore: 75, aiScoreLowerDifference: 5, aiScoreUpperDifference: 5, adjustedScoreLowerDifference: 5, adjustedScoreUpperDifference: 5 },
        { name: "Facts about Singapore", aiScore: 82, adjustedScore: 88, aiScoreLowerDifference: 5, aiScoreUpperDifference: 5, adjustedScoreLowerDifference: 5, adjustedScoreUpperDifference: 5 },
        { name: "Facts about Singapore", aiScore: 96, adjustedScore: 100, aiScoreLowerDifference: 5, aiScoreUpperDifference: 4, adjustedScoreLowerDifference: 5, adjustedScoreUpperDifference: 0 },
        { name: "Facts about Singapore", aiScore: 58, adjustedScore: 65, aiScoreLowerDifference: 5, aiScoreUpperDifference: 5, adjustedScoreLowerDifference: 5, adjustedScoreUpperDifference: 5 },
        { name: "Facts about Singapore", aiScore: 77, adjustedScore: 83, aiScoreLowerDifference: 5, aiScoreUpperDifference: 5, adjustedScoreLowerDifference: 5, adjustedScoreUpperDifference: 5 },
        { name: "Facts about Singapore", aiScore: 97, adjustedScore: 100, aiScoreLowerDifference: 5, aiScoreUpperDifference: 3, adjustedScoreLowerDifference: 5, adjustedScoreUpperDifference: 0 },
        { name: "Facts about Singapore", aiScore: 71, adjustedScore: 78, aiScoreLowerDifference: 5, aiScoreUpperDifference: 5, adjustedScoreLowerDifference: 5, adjustedScoreUpperDifference: 5 },
        { name: "Facts about Singapore", aiScore: 76, adjustedScore: 82, aiScoreLowerDifference: 5, aiScoreUpperDifference: 5, adjustedScoreLowerDifference: 5, adjustedScoreUpperDifference: 5 },
        { name: "Facts about Singapore", aiScore: 90, adjustedScore: 95, aiScoreLowerDifference: 5, aiScoreUpperDifference: 5, adjustedScoreLowerDifference: 5, adjustedScoreUpperDifference: 5 },
        { name: "Facts about Singapore", aiScore: 60, adjustedScore: 68, aiScoreLowerDifference: 5, aiScoreUpperDifference: 5, adjustedScoreLowerDifference: 5, adjustedScoreUpperDifference: 5 },
        { name: "Facts about Singapore", aiScore: 91, adjustedScore: 96, aiScoreLowerDifference: 5, aiScoreUpperDifference: 5, adjustedScoreLowerDifference: 5, adjustedScoreUpperDifference: 4 },
    ]

    return (
        <div className="flex flex-col gap-[8px] items-start w-full">
            {/* Score Cards Row */}
            <div className="flex flex-row items-stretch gap-[8px] w-full mb-2 mt-2">
                <ScoreCard
                    aiScore="52.5%"
                    adjustedScore="72.5%"
                    scoreChange="+20%"
                />
                <VerdictsRankedCard
                    totalRanked="1,201"
                    rankedPercentage="4%"
                    notRanked="200,041"
                    agreeCount="1,000"
                    agreePercentage="84%"
                    disagreeCount="201"
                    disagreePercentage="16%"
                />
                <VerdictsAdjustedCard
                    totalAdjusted={formatNumber(totalAdjusted)}
                    trueToFalseCount={formatNumber(trueToFalseCount)}
                    trueToFalsePercentage={trueToFalsePercentage}
                    falseToTrueCount={formatNumber(falseToTrueCount)}
                    falseToTruePercentage={falseToTruePercentage}
                />
            </div>
            {/* Chart */}
            <BundleChart
                title="tests (15)"
                chartData={chartData}
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
                        setTableData((prevData) =>
                            prevData.map((row) =>
                                row.id === id ? { ...row, ...updates } : row
                            )
                        )
                    }}
                />
            )}
        </div>
    )
}