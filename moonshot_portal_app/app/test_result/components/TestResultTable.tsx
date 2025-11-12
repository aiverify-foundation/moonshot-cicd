"use client"
import React, { useState, useEffect } from "react"
import { ThumbsUp, ThumbsDown, ArrowUpDown, ChevronLeft, ChevronRight } from "lucide-react"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import TestResultSheet from "./TestResultSheet"

export interface TestResultTableRow {
    id: string
    test: string
    prompt: string
    target: string
    response: string
    evaluation: string
    score: number
    yourVerdict: "agree" | "disagree" | null
    note: string
    bundle: string
    evaluatorInfo?: {
        model?: string
        systemPrompt?: string
        falsePositiveRate?: string
    }
    evaluatorPrompt: string
}

interface TestResultTableProps {
    data: TestResultTableRow[]
    pageSize?: number
    onDataChange?: (id: string, updates: Partial<TestResultTableRow>) => void
}

export default function TestResultTable({ data, pageSize = 10, onDataChange }: TestResultTableProps) {
    const [currentPage, setCurrentPage] = useState(1)
    const [sortColumn, setSortColumn] = useState<"evaluation" | null>(null)
    const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc")
    const [sheetOpen, setSheetOpen] = useState(false)
    const [selectedRowIndex, setSelectedRowIndex] = useState(0)

    // Reset to page 1 when sorting changes
    useEffect(() => {
        setCurrentPage(1)
    }, [sortColumn, sortDirection])

    const handleSort = (column: "evaluation") => {
        if (sortColumn === column) {
            setSortDirection(sortDirection === "asc" ? "desc" : "asc")
        } else {
            setSortColumn(column)
            setSortDirection("asc")
        }
    }

    // Sort the entire dataset first
    const sortedData = sortColumn
        ? [...data].sort((a, b) => {
              if (sortColumn === "evaluation") {
                  const comparison = a.evaluation.localeCompare(b.evaluation)
                  return sortDirection === "asc" ? comparison : -comparison
              }
              return 0
          })
        : data

    const totalPages = Math.ceil(sortedData.length / pageSize)
    const startIndex = (currentPage - 1) * pageSize
    const endIndex = startIndex + pageSize
    const currentData = sortedData.slice(startIndex, endIndex)

    const handleRowClick = (row: TestResultTableRow) => {
        // Find the index of the row in the sorted data array
        const fullIndex = sortedData.findIndex((item) => item.id === row.id)
        if (fullIndex !== -1) {
            setSelectedRowIndex(fullIndex)
            setSheetOpen(true)
        }
    }

    const handleSheetIndexChange = (newIndex: number) => {
        setSelectedRowIndex(newIndex)
        // Update the current page if the new index is outside the current page
        const newPage = Math.floor(newIndex / pageSize) + 1
        if (newPage !== currentPage) {
            setCurrentPage(newPage)
        }
    }

    return (
        <div className="flex flex-col w-full">
            <div className="border border-slate-200 rounded-[12px] overflow-hidden">
                <Table>
                    <TableHeader>
                        <TableRow className="bg-slate-100 hover:bg-slate-100 border-0">
                            <TableHead className="w-[80px] px-0 py-2">
                                <p className="font-medium text-[14px] leading-[14px] text-slate-500 pl-4">Test</p>
                            </TableHead>
                            <TableHead className="w-[160px] px-0 py-2">
                                <p className="font-medium text-[14px] leading-[14px] text-slate-500">Prompt</p>
                            </TableHead>
                            <TableHead className="w-[160px] px-0 py-2">
                                <p className="font-medium text-[14px] leading-[14px] text-slate-500">Target</p>
                            </TableHead>
                            <TableHead className="w-[160px] px-0 py-2">
                                <p className="font-medium text-[14px] leading-[14px] text-slate-500">Response</p>
                            </TableHead>
                            <TableHead className="w-[90px] px-0 py-2">
                                <div className="flex gap-1 items-center">
                                    <button
                                        onClick={() => handleSort("evaluation")}
                                        className="flex gap-1 items-center hover:opacity-70 transition-opacity"
                                    >
                                        <p className="font-medium text-[14px] leading-[14px] text-slate-500 whitespace-pre">
                                            Evaluation
                                        </p>
                                        <ArrowUpDown className="size-4 text-slate-500" />
                                    </button>
                                </div>
                            </TableHead>
                            <TableHead className="w-[160px] px-0 py-2">
                                <p className="font-medium text-[14px] leading-[14px] text-slate-500">Your verdict</p>
                            </TableHead>
                            <TableHead className="w-[120px] px-0 py-2">
                                <p className="font-medium text-[14px] leading-[14px] text-slate-500">Note</p>
                            </TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {currentData.map((row) => (
                            <TableRow
                                key={row.id}
                                className="border-b border-slate-200 hover:bg-slate-50 h-[120px] cursor-pointer"
                                onClick={() => handleRowClick(row)}
                            >
                                <TableCell className="px-0 py-2 align-top">
                                    <div className="w-[80px] h-full max-h-[116px] overflow-y-auto pl-4">
                                        <p className="font-medium text-[14px] text-black leading-[20px] whitespace-pre-wrap break-words">
                                            {row.test}
                                        </p>
                                    </div>
                                </TableCell>
                                <TableCell className="px-0 py-2 align-top">
                                    <div className="w-[160px] h-full max-h-[116px] overflow-y-auto">
                                        <p className="font-medium text-[14px] text-black leading-[20px] whitespace-pre-wrap break-words">
                                            {row.prompt}
                                        </p>
                                    </div>
                                </TableCell>
                                <TableCell className="px-0 py-2 align-top">
                                    <div className="w-[160px] h-full max-h-[116px] overflow-y-auto">
                                        <p className="font-medium text-[14px] text-black leading-[20px] whitespace-pre-wrap break-words">
                                            {row.target}
                                        </p>
                                    </div>
                                </TableCell>
                                <TableCell className="px-0 py-2 align-top">
                                    <div className="w-[160px] h-full max-h-[116px] overflow-y-auto">
                                        <p className="font-medium text-[14px] text-black leading-[20px] whitespace-pre-wrap break-words">
                                            {row.response}
                                        </p>
                                    </div>
                                </TableCell>
                                <TableCell className="px-0 py-2 align-top">
                                    <div className="flex gap-1.5 items-start">
                                        <div
                                            className={cn(
                                                "inline-flex items-center justify-center px-1 py-1 rounded-[6px] border",
                                                row.score === 1
                                                    ? "bg-green-100 border-green-200"
                                                    : "bg-red-100 border-red-200"
                                            )}
                                        >
                                            <p
                                                className={cn(
                                                    "font-semibold text-[12px] leading-normal whitespace-pre text-nowrap",
                                                    row.score === 1
                                                        ? "text-green-800"
                                                        : "text-red-800"
                                                )}
                                            >
                                                {row.evaluation}
                                            </p>
                                        </div>
                                    </div>
                                </TableCell>
                                <TableCell className="px-0 py-2 align-top">
                                    <div 
                                        className="flex flex-col items-start"
                                        onClick={(e) => e.stopPropagation()}
                                    >
                                        <ToggleGroup
                                            type="single"
                                            value={row.yourVerdict || undefined}
                                            onValueChange={(value) => {
                                                if (onDataChange) {
                                                    onDataChange(row.id, {
                                                        yourVerdict: value === "" ? null : (value as "agree" | "disagree" | null),
                                                    })
                                                }
                                            }}
                                            spacing={0}
                                            className="bg-slate-200 border border-slate-200 rounded-[6px] p-0 shadow-none"
                                        >
                                            <ToggleGroupItem
                                                value="agree"
                                                className={cn(
                                                    "p-1.5 rounded-none rounded-l-[6px] border-0",
                                                    row.yourVerdict === "agree"
                                                        ? "bg-white"
                                                        : "bg-transparent hover:bg-white/50"
                                                )}
                                            >
                                                <ThumbsUp
                                                    className={cn(
                                                        "size-[15px]",
                                                        row.yourVerdict === "agree"
                                                            ? "text-green-700"
                                                            : "text-slate-500"
                                                    )}
                                                />
                                            </ToggleGroupItem>
                                            <ToggleGroupItem
                                                value="disagree"
                                                className={cn(
                                                    "p-1.5 rounded-none rounded-r-[6px] border-0",
                                                    row.yourVerdict === "disagree"
                                                        ? "bg-white"
                                                        : "bg-transparent hover:bg-white/50"
                                                )}
                                            >
                                                <ThumbsDown
                                                    className={cn(
                                                        "size-[15px]",
                                                        row.yourVerdict === "disagree"
                                                            ? "text-red-700"
                                                            : "text-slate-500"
                                                    )}
                                                />
                                            </ToggleGroupItem>
                                        </ToggleGroup>
                                    </div>
                                </TableCell>
                                <TableCell className="px-0 py-2 align-top">
                                    <div className="w-[120px] h-full max-h-[116px] overflow-y-auto">
                                        {row.note && (
                                            <p className="font-medium text-[14px] text-black leading-[20px] whitespace-pre-wrap break-words">
                                                {row.note}
                                            </p>
                                        )}
                                    </div>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                    <div className="text-sm text-slate-500">
                        Showing {startIndex + 1} to {Math.min(endIndex, sortedData.length)} of {sortedData.length} results
                    </div>
                    <div className="flex items-center gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                            disabled={currentPage === 1}
                            className="h-8 px-3"
                        >
                            <ChevronLeft className="size-4" />
                            <span>Previous</span>
                        </Button>
                        <div className="flex items-center gap-1">
                            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                                if (
                                    page === 1 ||
                                    page === totalPages ||
                                    (page >= currentPage - 1 && page <= currentPage + 1)
                                ) {
                                    return (
                                        <Button
                                            key={page}
                                            variant={currentPage === page ? "default" : "outline"}
                                            size="sm"
                                            onClick={() => setCurrentPage(page)}
                                            className="h-8 w-8 p-0"
                                        >
                                            {page}
                                        </Button>
                                    )
                                } else if (page === currentPage - 2 || page === currentPage + 2) {
                                    return (
                                        <span key={page} className="px-2 text-slate-500">
                                            ...
                                        </span>
                                    )
                                }
                                return null
                            })}
                        </div>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                            disabled={currentPage === totalPages}
                            className="h-8 px-3"
                        >
                            <span>Next</span>
                            <ChevronRight className="size-4" />
                        </Button>
                    </div>
                </div>
            )}

            {/* Test Result Sheet */}
            <TestResultSheet
                open={sheetOpen}
                onOpenChange={setSheetOpen}
                data={sortedData}
                currentIndex={selectedRowIndex}
                onIndexChange={handleSheetIndexChange}
                onDataChange={onDataChange}
            />
        </div>
    )
}

