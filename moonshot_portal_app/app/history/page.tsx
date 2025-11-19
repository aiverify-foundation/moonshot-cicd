"use client"
import React from 'react';
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { Progress } from "@/components/ui/progress"

interface HistoryCardProps {
    title: string;
    completedDate: string;
    bundleAndTestCount: string;
    status: string;
    progressValue: number;
    duration: string;
    href?: string;
}

const createHistoryCard = ({
    title,
    completedDate,
    bundleAndTestCount,
    status,
    progressValue,
    duration,
    href = "/test_result"
}: HistoryCardProps) => {
    const statusColors = {
        "Complete": "bg-green-100 border-green-200 text-green-800",
        "In Progress": "bg-blue-100 border-blue-200 text-blue-800",
        "Failed": "bg-red-100 border-red-200 text-red-800",
    };
    
    const statusColorClass = statusColors[status as keyof typeof statusColors] || "bg-gray-100 border-gray-200 text-gray-800";
    
    const getProgressClassName = () => {
        if (status === "Complete") {
            return "w-[100px] h-[16px] [&>div]:bg-green-600";
        } else if (status === "In Progress") {
            return "w-[100px] h-[16px] [&>div]:bg-blue-600";
        } else {
            return "w-[100px] h-[16px] [&>div]:bg-gray-600";
        }
    };
    
    const progressTextColor = status === "Complete" ? "text-green-600" : status === "In Progress" ? "text-blue-600" : "text-gray-600";

    return (
        <Link href={href}>
            <Badge variant="outline" className="w-full p-4 bg-slate-50 border-slate-200 cursor-pointer hover:bg-slate-100 transition-colors">
                <div className="text-left h-[180px] w-full">
                    <div className="mb-2">
                        <div className="text-left font-semibold text-base text-gray-900 mb-1">{title}</div>
                        <div className="font-normal text-sm text-slate-700 mb-1">{completedDate}</div>
                        <div className="font-normal text-[12px] text-slate-700">{bundleAndTestCount}</div>
                    </div>
                    <Badge variant="outline" className={`w-fit mt-2 ${statusColorClass} h-[23px]`}>
                        <div className="text-left text-[12px] font-semibold">
                            {status}
                        </div>
                    </Badge>
                    <div className="flex items-center gap-2 mt-4">
                        <Progress value={progressValue} className={getProgressClassName()} />
                        <div className={`text-[14px] font-semibold ${progressTextColor}`}>{progressValue}%</div>
                    </div>
                    <div className="font-normal text-[12px] text-slate-700 mt-4">Completed in {duration}</div>
                </div>
            </Badge>
        </Link>
    )
}

export default function History() {
    return (
      <main className="p-8 w-[1300px]">
        <div className="h-[100px]">
            <p className="text-slate-700 text-[14px] font-medium w-[600px]">History</p>
            <h1 className="text-2xl font-semibold text-gray-900 mb-2 mt-3">Recent Activity</h1>
            <Badge variant="outline">
                <div className="text-left">
                    Status
                </div>
            </Badge>
            <div className="grid grid-cols-4 gap-4 mt-4">
             {createHistoryCard({
                 title: "Demo Test Run 1",
                 completedDate: "Completed 15 Nov 2025, 1:20 PM",
                 bundleAndTestCount: "2 Bundles, 2 Tests",
                 status: "Complete",
                 progressValue: 100,
                 duration: "47min"
             })}
             {createHistoryCard({
                 title: "Demo Test Run 2",
                 completedDate: "Completed 2 Nov 2025, 3:22 PM",
                 bundleAndTestCount: "2 Bundles, 2 Tests",
                 status: "Complete",
                 progressValue: 100,
                 duration: "55min"
             })}
            </div>
        </div>
      </main>
    );
  }