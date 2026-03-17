"use client"
import React, { useState, useEffect, useMemo } from "react"
import { ThumbsUp, ThumbsDown } from "lucide-react"
import BundleChart, { BundleChartDataItem } from "./BundleChart"
import TestResultTable, { TestResultTableRow } from "./TestResultTable"
import { parseCsvData } from "./parseCsvData"

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

function calculateChartDataFromTableData(data: TestResultTableRow[]): BundleChartDataItem[] {
    // Group data by test name (normalize by trimming whitespace)
    const testGroups = new Map<string, TestResultTableRow[]>()
    
    data.forEach((row) => {
        // Normalize test name by trimming whitespace to avoid duplicates from spacing variations
        const testName = (row.test || "Unknown Test").trim()
        if (!testGroups.has(testName)) {
            testGroups.set(testName, [])
        }
        testGroups.get(testName)!.push(row)
    })

    // Calculate scores for each test group
    const chartData: BundleChartDataItem[] = []
    
    testGroups.forEach((rows, testName) => {
        const totalCount = rows.length
        const totalScore = rows.reduce((sum, row) => sum + row.score, 0)
        
        // Calculate disagree counts for this test group
        let disagreeWithScore1 = 0
        let disagreeWithScore0 = 0
        
        rows.forEach((row) => {
            if (row.yourVerdict === "disagree") {
                if (row.score === 1) {
                    disagreeWithScore1++
                } else if (row.score === 0) {
                    disagreeWithScore0++
                }
            }
        })
        
        // Calculate AI score as percentage (total score / total count * 100)
        const aiScore = totalCount > 0 ? (totalScore / totalCount) * 100 : 0
        
        // Calculate adjusted score: (totalScore - disagreeWithScore1 + disagreeWithScore0) / totalCount * 100
        const adjustedScore = totalCount > 0 
            ? ((totalScore - disagreeWithScore1*2 + disagreeWithScore0*2) / totalCount) * 100 
            : 0
        
        // Round scores to avoid floating point precision issues
        const roundedAiScore = Math.round(aiScore * 100) / 100
        const roundedAdjustedScore = Math.round(adjustedScore * 100) / 100
  
        chartData.push({
            test_name: testName,
            aiScore: roundedAiScore,
            adjustedScore: roundedAdjustedScore,
            aiScoreLowerDifference: 7.8,
            aiScoreUpperDifference: 7.8,
            adjustedScoreLowerDifference: 7.8,
            adjustedScoreUpperDifference: 7.8,
        })
    })

    // Ensure uniqueness - since we group by test name, each test should only appear once
    // But we'll add a final check to prevent any duplicates
    const seenTestNames = new Set<string>()
    const uniqueChartData: BundleChartDataItem[] = []
    
    chartData.forEach((item) => {
        // If we somehow have a duplicate test name (shouldn't happen after grouping), skip it
        if (seenTestNames.has(item.test_name)) {
            console.warn(`Duplicate test name detected in chart data: ${item.test_name}. This should not happen after grouping.`)
            return
        }
        seenTestNames.add(item.test_name)
        uniqueChartData.push(item)
    })

    return uniqueChartData
}

interface TestResultBundleProps {
    onAdjustedScoreChange?: (score: number) => void
}

export default function TestResultBundle({ onAdjustedScoreChange }: TestResultBundleProps) {
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

    // Calculate chart data from table data (memoized to prevent unnecessary recalculations)
    const chartData = useMemo(() => {
        return calculateChartDataFromTableData(tableData)
    }, [tableData])

    // Calculate overall AI score and adjusted score
    const totalPromptsForScore = tableData.length
    const totalScore = tableData.reduce((sum, row) => sum + row.score, 0)
    const overallAiScore = totalPromptsForScore > 0 
        ? (totalScore / totalPromptsForScore) * 100 
        : 0
    
    // Calculate overall disagree counts
    const overallDisagreeWithScore1 = verdictStats.disagreeWithScore1
    const overallDisagreeWithScore0 = verdictStats.disagreeWithScore0
    
    // Calculate overall adjusted score: (totalScore - disagreeWithScore1 + disagreeWithScore0) / totalPromptsForScore * 100
    const overallAdjustedScore = totalPromptsForScore > 0
        ? ((totalScore - overallDisagreeWithScore1*2 + overallDisagreeWithScore0*2) / totalPromptsForScore) * 100
        : 0
    const overallScoreChange = overallAdjustedScore - overallAiScore

    // Notify parent component of adjusted score changes
    useEffect(() => {
        if (onAdjustedScoreChange && !isLoading) {
            onAdjustedScoreChange(overallAdjustedScore)
        }
    }, [overallAdjustedScore, isLoading, onAdjustedScoreChange])

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
            {/* Chart */}
            <BundleChart
                title={`Tests (${chartData.length})`}
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