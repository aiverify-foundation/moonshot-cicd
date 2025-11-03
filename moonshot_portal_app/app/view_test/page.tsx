"use client"
import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

export default function ViewTest() {
  return (
    <main className="p-8 w-[1300px]">
        <div className="h-[100px]">
            <h1 className="text-2xl font-bold mb-2">MLCommons AILuminate - Suicide and Self-harm</h1>
            <p className="text-gray-600 w-[600px]">Measures ability to respond without enabling, encouraging, or endorsing acts of intentional self-harm like suicide, self-injury (ex: cutting) and disordered eating. A high grade indicates that the system under test handles the response well.</p>
        </div>
        
        <div className="flex gap-4 w-full mt-4">
            <Badge variant="outline" className="h-[70px] w-1/2 flex flex-col items-start justify-start px-3 py-2 gap-3">
                <div className="text-left text-sm text-slate-500 font-medium">Dataset Information</div>
                <div className="text-left">
                    <span className="text-left text-sm text-slate-500">Prompts </span>
                    <span className="text-left text-sm text-slate-700">100</span>
                </div>
            </Badge>
            <Badge variant="outline" className="h-[70px] w-1/2 flex flex-col items-start justify-start px-3 py-2 gap-3">
                <div className="text-left text-sm text-slate-500 font-medium">Evaluator Information</div>
                <div className="text-left flex items-center gap-2">
                    <span className="text-left text-sm text-slate-500">Model </span>
                    <span className="text-left text-sm text-slate-700">100 </span>
                    <Separator orientation="vertical" className="h-4" />
                    <span className="text-left text-sm text-slate-500"> Grader Logic </span>
                    <span className="text-left text-sm text-slate-700">100</span>
                </div>
            </Badge>
        </div>
        <div className="flex items-center justify-between w-full mt-4">
            <h2 className="text-lg font-bold">How It Works</h2>
            <Button variant="secondary">Download All Prompts</Button>
        </div>
        <Separator orientation="horizontal" className="my-4" />
        <Badge variant="outline" className="h-[70px] w-full mb-4 flex flex-col items-start justify-start px-3 py-2 gap-3">
            <div className="text-left text-sm text-slate-500 font-medium">Prompt Template</div>
            <div className="text-left">
                <span className="text-left text-sm text-slate-500">Prompts </span>
                <span className="text-left text-sm text-slate-700">100</span>
            </div>
        </Badge>
        <Table>
          <TableHeader className="bg-slate-100">
            <TableRow>
              <TableHead>Input</TableHead>
              <TableHead>Target</TableHead>
              <TableHead>Response</TableHead>
              <TableHead>Evaluator Verdict</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow className="h-[180px]">
              <TableCell>Sample input 1</TableCell>
              <TableCell>Sample target 1</TableCell>
              <TableCell>Sample response 1</TableCell>
              <TableCell>Sample verdict 1</TableCell>
            </TableRow>
            <TableRow className="h-[180px]">
              <TableCell>Sample input 2</TableCell>
              <TableCell>Sample target 2</TableCell>
              <TableCell>Sample response 2</TableCell>
              <TableCell>Sample verdict 2</TableCell>
            </TableRow>
          </TableBody>
        </Table>
    </main>
  );
}
