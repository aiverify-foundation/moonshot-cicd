"use client";

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
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
import { fetchBundles, type BundleTest, type TestDetailRow } from '@/lib/api';
import { resolveModelNameLabel } from '@/lib/aajProviderResolution';
import { findTestInBundles } from '../resolveTestFromBundles';

function cellValue(value: string | undefined): string {
  const trimmed = (value ?? '').trim();
  return trimmed.length > 0 ? trimmed : '—';
}

function DetailTableRow({ row, index }: { row: TestDetailRow; index: number }) {
  return (
    <TableRow key={index} className="h-[180px]">
      <TableCell className="whitespace-normal break-words max-w-[300px] align-top">
        {cellValue(row.input)}
      </TableCell>
      <TableCell className="whitespace-normal break-words align-top">
        {cellValue(row.target)}
      </TableCell>
      <TableCell className="whitespace-normal break-words max-w-[400px] align-top">
        {cellValue(row.response)}
      </TableCell>
      <TableCell className="whitespace-normal break-words align-top">
        {cellValue(row.evaluator_verdict)}
      </TableCell>
    </TableRow>
  );
}

export default function ViewTestApp() {
  const searchParams = useSearchParams();
  const testParam = searchParams.get('test');
  const datasetParam = searchParams.get('dataset');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [test, setTest] = useState<BundleTest | null>(null);

  const loadTest = useCallback(async () => {
    if (!testParam || !datasetParam) {
      setLoading(false);
      setTest(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const bundles = await fetchBundles();
      const found = findTestInBundles(bundles, testParam, datasetParam);
      setTest(found ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load test details');
      setTest(null);
    } finally {
      setLoading(false);
    }
  }, [testParam, datasetParam]);

  useEffect(() => {
    void loadTest();
  }, [loadTest]);

  const details = test?.details ?? null;
  const hasDetails = Array.isArray(details) && details.length > 0;
  const modelName = resolveModelNameLabel(test);

  if (!testParam || !datasetParam) {
    return (
      <main className="p-8 w-[1300px]">
        <h1 className="text-2xl font-bold mb-2">Test not found</h1>
        <p className="text-gray-600 mb-4">
          Missing test or dataset in the URL. Open this page from a bundle&apos;s Learn More link.
        </p>
        <Button variant="outline" asChild>
          <Link href="/benchmark">Back to benchmark</Link>
        </Button>
      </main>
    );
  }

  if (loading) {
    return (
      <main className="p-8 w-[1300px]">
        <p className="text-gray-600">Loading test details…</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="p-8 w-[1300px]">
        <h1 className="text-2xl font-bold mb-2">Could not load test</h1>
        <p className="text-gray-600 mb-4">{error}</p>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => void loadTest()}>
            Retry
          </Button>
          <Button variant="outline" asChild>
            <Link href="/benchmark">Back to benchmark</Link>
          </Button>
        </div>
      </main>
    );
  }

  if (!test) {
    return (
      <main className="p-8 w-[1300px]">
        <h1 className="text-2xl font-bold mb-2">Test not found</h1>
        <p className="text-gray-600 mb-4">
          No test matches name &quot;{decodeURIComponent(testParam)}&quot; and dataset &quot;
          {decodeURIComponent(datasetParam)}&quot;.
        </p>
        <Button variant="outline" asChild>
          <Link href="/benchmark">Back to benchmark</Link>
        </Button>
      </main>
    );
  }

  return (
    <main className="p-8 w-[1300px]">
      <div className="min-h-[100px]">
        <h1 className="text-2xl font-bold mb-2">{test.name}</h1>
        {test.description ? (
          <p className="text-gray-600 w-[600px]">{test.description}</p>
        ) : null}
      </div>

      <div className="flex gap-4 w-full mt-8">
        <Badge
          variant="outline"
          className="h-[70px] w-1/2 flex flex-col items-start justify-start px-3 py-2 gap-3"
        >
          <div className="text-left text-sm text-slate-500 font-medium">
            Dataset Information
          </div>
          <div className="text-left">
            <span className="text-left text-sm text-slate-500">Prompts </span>
            <span className="text-left text-sm text-slate-700">
              {test.dataset?.num_of_dataset_prompts ?? 0}
            </span>
          </div>
        </Badge>
        <Badge
          variant="outline"
          className="h-[70px] w-1/2 flex flex-col items-start justify-start px-3 py-2 gap-3"
        >
          <div className="text-left text-sm text-slate-500 font-medium">
            Evaluator Information
          </div>
          <div className="text-left flex items-center gap-2 flex-wrap">
            <span className="text-left text-sm text-slate-500">LLM-as-judge Model </span>
            <span className="text-left text-sm text-slate-700">{modelName}</span>
          </div>
        </Badge>
      </div>

      <div className="flex items-center justify-between w-full mt-4">
        <h2 className="text-lg font-bold">How It Works</h2>
      </div>
      <Separator orientation="horizontal" className="my-4" />

      {!hasDetails ? (
        <p className="text-sm text-gray-600 py-4">
          No sample prompts available for this dataset.
        </p>
      ) : (
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
            {details.map((row, index) => (
              <DetailTableRow key={index} row={row} index={index} />
            ))}
          </TableBody>
        </Table>
      )}
    </main>
  );
}
