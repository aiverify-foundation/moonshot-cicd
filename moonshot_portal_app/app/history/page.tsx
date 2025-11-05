"use client"
import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { Progress } from "@/components/ui/progress"

const createHistoryCard = () => {
    return (
        <Badge variant="outline" className="w-full p-4 bg-slate-50 border-slate-200">
            <div className="text-left h-[180px] w-full">
                <div className="mb-2">
                    <div className="text-left font-semibold text-base text-gray-900 mb-1">Demo Test Run</div>
                    <div className="font-normal text-sm text-slate-700 mb-1">Completed 6 July 2025, 3:22 PM</div>
                    <div className="font-normal text-[12px] text-slate-700">2 Bundles, 2 Tests</div>
                </div>
                <Badge variant="outline" className="w-fit mt-2 bg-green-100 border-green-200 h-[23px]">
                    <div className="text-left text-green-800 text-[12px] font-semibold">
                        Complete
                    </div>
                </Badge>
                <div className="flex items-center gap-2 mt-4">
                    <Progress value={100} className="w-[100px] h-[16px] [&>div]:bg-green-600" />
                    <div className="text-[14px] font-semibold text-green-600">100%</div>
                </div>
                <div className="font-normal text-[12px] text-slate-700 mt-4">Completed in 1h 5min</div>
            </div>
        </Badge>
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
             {createHistoryCard()}
             {createHistoryCard()}
             {createHistoryCard()}
             {createHistoryCard()}
             {createHistoryCard()}
             {createHistoryCard()}
            </div>
        </div>
      </main>
    );
  }