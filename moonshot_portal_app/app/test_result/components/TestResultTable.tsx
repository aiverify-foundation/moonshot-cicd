"use client"
import React, { useState, useEffect, useMemo } from "react"
import { ThumbsUp, ThumbsDown, ArrowUpDown, ChevronLeft, ChevronRight, ChevronDown, Search } from "lucide-react"
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
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
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
        graderLogic?: string
        falsePositiveRate?: string
    }
    graderLogic: string
}

interface TestResultTableProps {
    data: TestResultTableRow[]
    pageSize?: number
    onDataChange?: (id: string, updates: Partial<TestResultTableRow>) => void
}

export default function TestResultTable({ data, pageSize = 10, onDataChange }: TestResultTableProps) {
    const [currentPage, setCurrentPage] = useState(1)
    const [sortColumn, setSortColumn] = useState<"evaluation" | null>("evaluation")
    const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc")
    const [sheetOpen, setSheetOpen] = useState(false)
    const [selectedRowIndex, setSelectedRowIndex] = useState(0)
    const [searchTerm, setSearchTerm] = useState("")

    // Extract unique filter values from data
    const filterOptions = useMemo(() => {
        const bundles = Array.from(new Set(data.map((row) => row.bundle).filter(Boolean))).sort()
        const evaluations = Array.from(new Set(data.map((row) => row.evaluation).filter(Boolean))).sort()
        const yourVerdicts: (string | null)[] = ["agree", "disagree", null]
        const adjustedOptions: string[] = ["adjusted", "not adjusted"]

        return {
            bundles,
            evaluations,
            yourVerdicts,
            adjustedOptions,
        }
    }, [data])

    // Initialize filter state with all options selected
    const [filters, setFilters] = useState<{
        bundles: Set<string>
        evaluations: Set<string>
        yourVerdicts: Set<string | null>
        adjusted: Set<string>
    }>(() => {
        const bundles = Array.from(new Set(data.map((row) => row.bundle).filter(Boolean))).sort()
        const evaluations = Array.from(new Set(data.map((row) => row.evaluation).filter(Boolean))).sort()
        
        return {
            bundles: new Set(bundles),
            evaluations: new Set(evaluations),
            yourVerdicts: new Set(["agree", "disagree", null]),
            adjusted: new Set(["adjusted", "not adjusted"]),
        }
    })

    // Reset filters when data changes
    useEffect(() => {
        setFilters({
            bundles: new Set(filterOptions.bundles),
            evaluations: new Set(filterOptions.evaluations),
            yourVerdicts: new Set(["agree", "disagree", null]),
            adjusted: new Set(["adjusted", "not adjusted"]),
        })
    }, [filterOptions])

    // Reset to page 1 when sorting or filters change
    useEffect(() => {
        setCurrentPage(1)
    }, [sortColumn, sortDirection])
    
    // Reset to page 1 when search term changes
    useEffect(() => {
        setCurrentPage(1)
    }, [searchTerm])
    
    // Reset to page 1 when filters change (using stringified version for stable comparison)
    const filterKey = useMemo(() => {
        return [
            Array.from(filters.bundles).sort().join(","),
            Array.from(filters.evaluations).sort().join(","),
            Array.from(filters.yourVerdicts)
                .map((v) => v ?? "null")
                .sort()
                .join(","),
            Array.from(filters.adjusted).sort().join(","),
        ].join("|")
    }, [filters])
    
    useEffect(() => {
        setCurrentPage(1)
    }, [filterKey])

    const handleSort = (column: "evaluation") => {
        if (sortColumn === column) {
            setSortDirection(sortDirection === "asc" ? "desc" : "asc")
        } else {
            setSortColumn(column)
            setSortDirection("asc")
        }
    }

    // Apply filters and search to data
    const filteredData = useMemo(() => {
        return data.filter((row) => {
            // Filter by bundle
            if (!filters.bundles.has(row.bundle)) return false

            // Filter by evaluation
            if (!filters.evaluations.has(row.evaluation)) return false

            // Filter by your verdict
            if (!filters.yourVerdicts.has(row.yourVerdict)) return false

            // Filter by adjusted/not adjusted
            const isAdjusted = row.yourVerdict === "disagree"
            if (isAdjusted && !filters.adjusted.has("adjusted")) return false
            if (!isAdjusted && !filters.adjusted.has("not adjusted")) return false

            // Filter by search term (case-insensitive search across all displayed columns)
            if (searchTerm.trim()) {
                const searchLower = searchTerm.toLowerCase().trim()
                const yourVerdictDisplay = 
                    row.yourVerdict === "agree" ? "agree" :
                    row.yourVerdict === "disagree" ? "disagree" : "not set"
                
                const searchableText = [
                    row.test,
                    row.prompt,
                    row.target,
                    row.response,
                    row.evaluation,
                    yourVerdictDisplay,
                    row.note,
                ]
                    .filter(Boolean)
                    .join(" ")
                    .toLowerCase()
                
                if (!searchableText.includes(searchLower)) return false
            }

            return true
        })
    }, [data, filters, searchTerm])

    // Sort the filtered dataset
    const sortedData = sortColumn
        ? [...filteredData].sort((a, b) => {
              if (sortColumn === "evaluation") {
                  const comparison = a.evaluation.localeCompare(b.evaluation)
                  return sortDirection === "asc" ? comparison : -comparison
              }
              return 0
          })
        : filteredData

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

    // Calculate counts for each filter option
    const getFilterCounts = () => {
        const bundleCounts = new Map<string, number>()
        const evaluationCounts = new Map<string, number>()
        const yourVerdictCounts = new Map<string | null, number>()
        const adjustedCounts = new Map<string, number>()

        data.forEach((row) => {
            // Bundle counts
            bundleCounts.set(row.bundle, (bundleCounts.get(row.bundle) || 0) + 1)

            // Evaluation counts
            evaluationCounts.set(row.evaluation, (evaluationCounts.get(row.evaluation) || 0) + 1)

            // Your verdict counts
            yourVerdictCounts.set(row.yourVerdict, (yourVerdictCounts.get(row.yourVerdict) || 0) + 1)

            // Adjusted counts
            const isAdjusted = row.yourVerdict === "disagree"
            const adjustedKey = isAdjusted ? "adjusted" : "not adjusted"
            adjustedCounts.set(adjustedKey, (adjustedCounts.get(adjustedKey) || 0) + 1)
        })

        return { bundleCounts, evaluationCounts, yourVerdictCounts, adjustedCounts }
    }

    const filterCounts = getFilterCounts()

    // Filter dropdown component
    const FilterDropdown = <T extends string | null>({
        label,
        options,
        selected,
        onToggle,
        counts,
        getDisplayLabel,
    }: {
        label: string
        options: T[]
        selected: Set<T>
        onToggle: (value: T) => void
        counts: Map<T, number>
        getDisplayLabel: (value: T) => string
    }) => {
        const [open, setOpen] = useState(false)
        const selectedCount = selected.size
        const totalCount = options.length

        return (
            <Popover open={open} onOpenChange={setOpen}>
                <PopoverTrigger asChild>
                    <Button
                        variant="outline"
                        className="h-9 px-3 text-sm font-medium text-slate-700 bg-white border-slate-200 hover:bg-slate-50"
                    >
                        {label}
                            <span className="ml-1.5 text-slate-500">({selectedCount})</span>
                        <ChevronDown className="ml-2 size-4 text-slate-500" />
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[200px] p-2" align="start">
                    <div className="flex flex-col gap-1 max-h-[300px] overflow-y-auto">
                        {options.map((option) => {
                            const isSelected = selected.has(option)
                            const count = counts.get(option) || 0
                            const displayLabel = getDisplayLabel(option)

                            return (
                                <label
                                    key={option ?? "null"}
                                    className="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-slate-100 cursor-pointer"
                                >
                                    <Checkbox
                                        checked={isSelected}
                                        onCheckedChange={() => onToggle(option)}
                                    />
                                    <span className="text-sm text-slate-700 flex-1">{displayLabel}</span>
                                    <span className="text-xs text-slate-500">{count}</span>
                                </label>
                            )
                        })}
                    </div>
                </PopoverContent>
            </Popover>
        )
    }

    return (
        <div className="flex flex-col w-full gap-4">
            {/* Filters and Search */}
            <div className="flex flex-wrap items-center gap-2">
                <FilterDropdown<string>
                    label="Bundle"
                    options={filterOptions.bundles}
                    selected={filters.bundles}
                    onToggle={(value) => {
                        setFilters((prev) => {
                            const newSet = new Set(prev.bundles)
                            if (newSet.has(value)) {
                                newSet.delete(value)
                            } else {
                                newSet.add(value)
                            }
                            return { ...prev, bundles: newSet }
                        })
                    }}
                    counts={filterCounts.bundleCounts}
                    getDisplayLabel={(value) => value || ""}
                />
                <FilterDropdown<string>
                    label="Evaluation"
                    options={filterOptions.evaluations}
                    selected={filters.evaluations}
                    onToggle={(value) => {
                        setFilters((prev) => {
                            const newSet = new Set(prev.evaluations)
                            if (newSet.has(value)) {
                                newSet.delete(value)
                            } else {
                                newSet.add(value)
                            }
                            return { ...prev, evaluations: newSet }
                        })
                    }}
                    counts={filterCounts.evaluationCounts}
                    getDisplayLabel={(value) => value || ""}
                />
                <FilterDropdown<string | null>
                    label="Your Agreement with Evaluation"
                    options={filterOptions.yourVerdicts}
                    selected={filters.yourVerdicts}
                    onToggle={(value) => {
                        setFilters((prev) => {
                            const newSet = new Set(prev.yourVerdicts)
                            if (newSet.has(value)) {
                                newSet.delete(value)
                            } else {
                                newSet.add(value)
                            }
                            return { ...prev, yourVerdicts: newSet }
                        })
                    }}
                    counts={filterCounts.yourVerdictCounts}
                    getDisplayLabel={(value) => {
                        if (value === "agree") return "Agree"
                        if (value === "disagree") return "Disagree"
                        return "Not Set"
                    }}
                />
                <FilterDropdown<string>
                    label="Adjusted/Not Adjusted"
                    options={filterOptions.adjustedOptions}
                    selected={filters.adjusted}
                    onToggle={(value) => {
                        setFilters((prev) => {
                            const newSet = new Set(prev.adjusted)
                            if (newSet.has(value)) {
                                newSet.delete(value)
                            } else {
                                newSet.add(value)
                            }
                            return { ...prev, adjusted: newSet }
                        })
                    }}
                    counts={filterCounts.adjustedCounts}
                    getDisplayLabel={(value) => {
                        if (value === "adjusted") return "Adjusted"
                        return "Not Adjusted"
                    }}
                />
                {/* Search Bar */}
                <div className="relative ml-auto">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 size-4 text-slate-400" />
                    <Input
                        type="text"
                        placeholder="Search across all columns..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-9 h-9 w-full max-w-md"
                    />
                </div>
            </div>

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
                                <p className="font-medium text-[14px] leading-[14px] text-slate-500">Your agreement<br />with evaluation</p>
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
                                            className={`inline-flex items-center justify-center px-1 py-1 rounded-[6px] border ${row.score === 1 ? "bg-green-100 border-green-200" : "bg-red-100 border-red-200"}`}
                                        >
                                            <p
                                                className={`font-semibold text-[12px] leading-normal whitespace-pre text-nowrap ${row.score === 1 ? "text-green-800" : "text-red-800"}`}
                                            >
                                                {row.score === 1 ? "Agree" : row.score === 0 ? "Disagree" : row.evaluation}
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
                                                className={`p-1.5 rounded-none rounded-l-[6px] border-0 ${row.yourVerdict === "agree" ? "bg-white" : "bg-transparent hover:bg-white/50"}`}
                                            >
                                                <ThumbsUp
                                                    className={`size-[15px] ${row.yourVerdict === "agree" ? "text-green-700" : "text-slate-500"}`}
                                                />
                                            </ToggleGroupItem>
                                            <ToggleGroupItem
                                                value="disagree"
                                                className={`p-1.5 rounded-none rounded-r-[6px] border-0 ${row.yourVerdict === "disagree" ? "bg-white" : "bg-transparent hover:bg-white/50"}`}
                                            >
                                                <ThumbsDown
                                                    className={`size-[15px] ${row.yourVerdict === "disagree" ? "text-red-700" : "text-slate-500"}`}
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

