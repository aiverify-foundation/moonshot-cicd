"use client"
import TestResultOverview from './TestResultOverview';
import React, { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { Progress } from "@/components/ui/progress"
import TestResultBundle from './TestResultBundle';


export default function TestResultApp() {
    const [activeTab, setActiveTab] = useState('Overview');
    const [undesirableContentScore, setUndesirableContentScore] = useState<number | null>(null);
    return (
      <main className="p-8 w-[1300px]">
        <div>
            <p className="text-slate-700 text-[14px] font-medium w-[600px]">Report</p>
            <div className="flex items-center gap-3 mt-3 mb-1">
                <h1 className="text-2xl font-semibold text-gray-900">Demo Test Run</h1>
                <Badge variant="outline">
                    <div className="text-left">
                        Status
                    </div>
                </Badge>
            </div>
            <div className="text-left font-medium text-[14px] text-slate-500 mb-3">Report description that spans several lines, I don't think this should be in descriptions?</div>
            {/* vertcal seperators have issues so using divs with inline styles */}
            <div className="flex items-center gap-2 mt-2">
                <div className="text-left font-medium text-[12px] text-slate-500">Endpoint</div>
                <div className="text-left font-semibold text-[12px] text-slate-700">chat gpt 4o</div>
                <div className="h-4 w-px bg-slate-300" />
                <div className="text-left font-medium text-[12px] text-slate-500">Prompts</div>
                <div className="text-left font-semibold text-[12px] text-slate-700">1337</div>
                <div className="h-4 w-px bg-slate-300" />                
                <div className="text-left font-medium text-[12px] text-slate-500">Confidence Level</div>
                <div className="text-left font-semibold text-[12px] text-slate-700">98.75%</div>
            </div>
        </div>

        <div className="bg-slate-100 flex items-center gap-[10px] p-[5px] rounded-[6px] mt-4">
            <button
                onClick={() => setActiveTab('Overview')}
                className={`flex gap-[10px] items-center px-3 py-1.5 rounded-[3px] transition-colors ${
                    activeTab === 'Overview'
                        ? 'bg-white'
                        : 'bg-transparent hover:bg-white/50'
                }`}
            >
                <p className={`font-semibold text-[14px] whitespace-nowrap ${
                    activeTab === 'Overview' ? 'text-slate-800' : 'text-slate-600'
                }`}>
                    Overview
                </p>
            </button>
            <button
                onClick={() => setActiveTab('Data disclosure')}
                className={`flex gap-[10px] items-center px-3 py-1.5 rounded-[3px] transition-colors ${
                    activeTab === 'Data disclosure'
                        ? 'bg-white'
                        : 'bg-transparent hover:bg-white/50'
                }`}
            >
                <p className={`font-semibold text-[14px] whitespace-nowrap ${
                    activeTab === 'Data disclosure' ? 'text-slate-800' : 'text-slate-600'
                }`}>
                    Data disclosure
                </p>
                <div className="bg-gray-100 border border-gray-200 flex gap-1 items-center justify-center p-1 rounded-[6px]">
                    <p className="font-semibold text-[12px] text-gray-800 whitespace-nowrap">
                        80%
                    </p>
                </div>
            </button>
            <button
                onClick={() => setActiveTab('Undesirable content')}
                className={`flex gap-[10px] items-center px-3 py-1.5 rounded-[3px] transition-colors ${
                    activeTab === 'Undesirable content'
                        ? 'bg-white'
                        : 'bg-transparent hover:bg-white/50'
                }`}
            >
                <p className={`font-semibold text-[14px] whitespace-nowrap ${
                    activeTab === 'Undesirable content' ? 'text-slate-800' : 'text-slate-600'
                }`}>
                    Undesirable content
                </p>
                <div className="bg-gray-100 border border-gray-200 flex gap-1 items-center justify-center p-1 rounded-[6px]">
                    <p className="font-semibold text-[12px] text-gray-800 whitespace-nowrap">
                        {undesirableContentScore !== null 
                            ? `${Math.round(undesirableContentScore * 10) / 10}%`
                            : '—'
                        }
                    </p>
                </div>
            </button>
        </div>
        {/* Always render TestResultBundle to load data on mount, but hide when not active */}
        <div className={activeTab === 'Undesirable content' ? '' : 'hidden'}>
            <TestResultBundle onAdjustedScoreChange={setUndesirableContentScore} />
        </div>
        {/* if activeTab is Overview, show TestResultOverview (If first expression is true, it evaluates to the component)*/}
        {activeTab === 'Overview' && <TestResultOverview />}
      </main>
    );
  }