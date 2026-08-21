"use client"
import React, { useState, useEffect, useRef } from "react"
import { ThumbsUp, ThumbsDown, Info } from "lucide-react"
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
} from "@/components/ui/sheet"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { TestResultTableRow } from "./TestResultTable"
import { evaluationDisplayLabel } from "./evaluationDisplayHelpers"
import PromptTemplateSheet from "@/components/PromptTemplateSheet"

interface TestResultSheetProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    data: TestResultTableRow[]
    currentIndex: number
    onIndexChange: (index: number) => void
    onDataChange?: (id: string, updates: Partial<TestResultTableRow>) => void
}

export default function TestResultSheet({
    open,
    onOpenChange,
    data,
    currentIndex,
    onIndexChange,
    onDataChange,
}: TestResultSheetProps) {
    const currentRow = data[currentIndex] as TestResultTableRow
    const totalItems = data.length
    const currentItemNumber = currentIndex + 1
    
    // Local state for note to allow controlled input
    const [note, setNote] = useState(currentRow?.note || "")
    
    // State for prompt template sheet
    const [promptTemplateSheetOpen, setPromptTemplateSheetOpen] = useState(false)
    
    // Refs for scrollable divs
    const promptScrollRef = useRef<HTMLDivElement>(null)
    const responseScrollRef = useRef<HTMLDivElement>(null)

    // Update note state when currentRow changes
    useEffect(() => {
        setNote(currentRow?.note || "")
    }, [currentRow?.note, currentIndex])
    
    // Scroll prompt and response to top when index changes
    useEffect(() => {
        if (promptScrollRef.current) {
            promptScrollRef.current.scrollTop = 0
        }
        if (responseScrollRef.current) {
            responseScrollRef.current.scrollTop = 0
        }
    }, [currentIndex])

    const handlePrevious = () => {
        if (currentIndex > 0) {
            onIndexChange(currentIndex - 1)
        }
    }

    const handleNext = () => {
        if (currentIndex < totalItems - 1) {
            onIndexChange(currentIndex + 1)
        }
    }

    const handleVerdictChange = (value: string) => {
        if (currentRow && onDataChange) {
            onDataChange(currentRow.id, {
                yourVerdict: value === "" ? null : (value as "agree" | "disagree" | null),
            })
        }
    }

    const handleNoteChange = (value: string) => {
        setNote(value)
        if (currentRow && onDataChange) {
            onDataChange(currentRow.id, {
                note: value,
            })
        }
    }

    if (!currentRow) {
        return null
    }

    return (
        <Sheet open={open} onOpenChange={onOpenChange}>
            <SheetContent
                side="right"
                className="w-[660px] sm:max-w-[660px] overflow-y-auto p-6"
            >
                <SheetHeader className="pb-0 pt-0">
                    <div className="flex items-center justify-between">
                        <SheetTitle className="text-[14px] font-medium text-slate-500 leading-none pb-3">
                            Prompt {currentItemNumber}/{totalItems}
                        </SheetTitle>
                    </div>
                    <SheetDescription className="sr-only">
                        Detailed results for the selected prompt.
                    </SheetDescription>
                </SheetHeader>

                <div className="flex flex-col gap-[12px] mt-0">
                    {/* Bundle */}
                    <div className="flex flex-col gap-[6px]">
                        <p className="font-medium text-[12px] leading-normal text-slate-700">
                            Bundle
                        </p>
                        <p className="font-medium text-[14px] leading-[20px] text-black">
                            {currentRow.bundle || "N/A"}
                        </p>
                    </div>

                    {/* Test */}
                    <div className="flex flex-col gap-[6px]">
                        <p className="font-medium text-[12px] leading-normal text-slate-700">
                        Test
                        </p>
                        <p className="font-medium text-[14px] leading-[20px] text-black">
                            {currentRow.test || "N/A"}
                        </p>
                    </div>

                    {/* Prompt */}
                    <div className="flex flex-col gap-[6px]">
                        <p className="font-medium text-[12px] leading-normal text-slate-700">
                            Prompt
                        </p>
                        <div 
                            ref={promptScrollRef}
                            className="bg-white border border-slate-200 rounded-[6px] h-[80px] overflow-y-auto p-3">
                            <p className="font-medium text-[14px] leading-[20px] text-black whitespace-pre-wrap break-words">
                                {currentRow.prompt}
                            </p>
                        </div>
                    </div>

                    {/* Target */}
                    <div className="flex flex-col gap-[6px]">
                        <p className="font-medium text-[12px] leading-normal text-slate-700">
                            Target
                        </p>
                        <div className="bg-white border border-slate-200 rounded-[6px] h-[60px] overflow-y-auto p-3">
                            <p className="font-medium text-[14px] leading-[20px] text-black whitespace-pre-wrap break-words">
                                {currentRow.target}
                            </p>
                        </div>
                    </div>

                    {/* Response */}
                    <div className="flex flex-col gap-[6px]">
                        <p className="font-medium text-[12px] leading-normal text-slate-700">
                            Response
                        </p>
                        <div 
                            ref={responseScrollRef}
                            className="bg-white border border-slate-200 rounded-[6px] h-[80px] overflow-y-auto p-3"
                        >
                            <p className="font-medium text-[14px] leading-[20px] text-black whitespace-pre-wrap break-words">
                                {currentRow.response}
                            </p>
                        </div>
                    </div>

                    {/* Evaluator Information */}
                    {currentRow.evaluatorInfo && (
                        <div className="border border-slate-200 rounded-[6px] p-[15px] flex flex-col gap-4">
                            <p className="font-medium text-[12px] leading-normal text-slate-500">
                                Evaluator Information
                            </p>
                            <div className="flex gap-4 items-start flex-wrap">
                                {currentRow.evaluatorInfo.model !== undefined && (
                                    <>
                                        <div className="flex gap-2 items-center">
                                            <p className="font-normal text-[12px] leading-normal text-slate-500 whitespace-pre">
                                                Model
                                            </p>
                                            <p className="font-medium text-[12px] leading-normal text-slate-700 whitespace-pre">
                                                {currentRow.evaluatorInfo.model || "Nil"}
                                            </p>
                                        </div>
                                        <div className="h-[15px] w-px bg-slate-200" />
                                    </>
                                )}
                                {currentRow.evaluatorInfo.graderLogic !== undefined && (
                                    <>
                                        <div className="flex gap-2 items-center">
                                            <p className="font-normal text-[12px] leading-normal text-slate-500 whitespace-pre">
                                                Grader Logic
                                            </p>
                                            <div className="flex gap-0.5 items-center">
                                                <p className="font-medium text-[12px] leading-normal text-slate-700 whitespace-pre">
                                                    {currentRow.evaluatorInfo.graderLogic || "N/A"}
                                                </p>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-3 w-3 p-0 hover:bg-transparent"
                                                    onClick={() => setPromptTemplateSheetOpen(true)}
                                                    aria-label="View Prompt Template"
                                                >
                                                    <Info className="size-3 text-slate-500" />
                                                </Button>
                                            </div>
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Evaluation */}
                    <div className="flex flex-col gap-[6px]">
                        <p className="font-medium text-[12px] leading-normal text-slate-700">
                            Evaluation
                        </p>
                        <div
                            className={`inline-flex items-center justify-center px-1 py-1 rounded-[6px] border w-fit ${currentRow.score === 1 ? "bg-green-100 border-green-200" : "bg-red-100 border-red-200"}`}
                        >
                            <p
                                className={`font-semibold text-[12px] leading-normal whitespace-pre text-nowrap ${currentRow.score === 1 ? "text-green-800" : "text-red-800"}`}
                            >
                                {evaluationDisplayLabel(currentRow.evaluation, currentRow.score, {
                                    isPromptError: currentRow.isPromptError,
                                    errorSource: currentRow.errorSource,
                                })}
                            </p>
                        </div>
                    </div>

                    {/* Your Verdict */}
                    <div className="flex flex-col gap-[6px]">
                        <p className="font-medium text-[12px] leading-normal text-slate-700">
                            Your Agreement with Evaluation
                        </p>
                        <ToggleGroup
                            type="single"
                            value={currentRow.yourVerdict ?? ""}
                            onValueChange={handleVerdictChange}
                            spacing={0}
                            className="bg-slate-200 border border-slate-200 rounded-[6px] p-0 shadow-none w-fit"
                        >
                            <ToggleGroupItem
                                value="agree"
                                className={`p-1.5 rounded-none rounded-l-[6px] border-0 ${currentRow.yourVerdict === "agree" ? "bg-white" : "bg-transparent hover:bg-white/50"}`}
                            >
                                <ThumbsUp
                                    className={`size-[15px] ${currentRow.yourVerdict === "agree" ? "text-green-700" : "text-slate-500"}`}
                                />
                            </ToggleGroupItem>
                            <ToggleGroupItem
                                value="disagree"
                                className={`p-1.5 rounded-none rounded-r-[6px] border-0 ${currentRow.yourVerdict === "disagree" ? "bg-white" : "bg-transparent hover:bg-white/50"}`}
                            >
                                <ThumbsDown
                                    className={`size-[15px] ${currentRow.yourVerdict === "disagree" ? "text-red-700" : "text-slate-500"}`}
                                />
                            </ToggleGroupItem>
                        </ToggleGroup>
                    </div>

                    {/* Note */}
                    <div className="flex flex-col gap-[6px]">
                        <p className="font-medium text-[12px] leading-normal text-slate-700">
                            Note
                        </p>
                        <Textarea
                            value={note}
                            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => handleNoteChange(e.target.value)}
                            placeholder="Add a note..."
                            className="bg-white border border-slate-200 rounded-[6px] h-[80px] min-h-[80px] p-3 font-medium text-[14px] leading-[20px] text-black resize-none"
                        />
                    </div>
                </div>

                {/* Navigation Buttons */}
                <div className="flex items-center justify-between mt-auto pt-4 pb-6">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handlePrevious}
                        disabled={currentIndex === 0}
                        className="bg-white border border-slate-200 rounded-[6px] px-2 py-1.5 h-auto"
                    >
                        <p className="font-semibold text-[14px] leading-none text-slate-700 whitespace-pre">
                            Previous
                        </p>
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleNext}
                        disabled={currentIndex === totalItems - 1}
                        className="bg-white border border-slate-200 rounded-[6px] px-2 py-1.5 h-auto"
                    >
                        <p className="font-semibold text-[14px] leading-none text-slate-700 whitespace-pre">
                            Next
                        </p>
                    </Button>
                </div>
            </SheetContent>
            <PromptTemplateSheet 
                open={promptTemplateSheetOpen} 
                onOpenChange={setPromptTemplateSheetOpen} 
            />
        </Sheet>
    )
}

