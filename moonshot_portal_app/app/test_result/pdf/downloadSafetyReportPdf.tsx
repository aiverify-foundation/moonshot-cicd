import React from 'react';
import { saveBlobAsFile } from '@/lib/api';
import { registerReportFonts } from './fonts';
import { mapRunToReportData } from './mapRunToReportData';
import type { SafetyReportPdfProps } from './types';
import {
  BenchmarkRun,
  BenchmarkRunResultsBundleSummary,
  BenchmarkRunTestMarginOfError,
  BenchmarkRunTestPrompt,
} from '@/lib/api';

export async function generateSafetyReportBlob(
  props: SafetyReportPdfProps
): Promise<Blob> {
  registerReportFonts();
  const { pdf } = await import('@react-pdf/renderer');
  const { default: SafetyReportDocument } = await import('./SafetyReportDocument');
  return pdf(<SafetyReportDocument {...props} />).toBlob();
}

export async function downloadSafetyReportPdf(
  run: BenchmarkRun,
  bundles: BenchmarkRunResultsBundleSummary[],
  prompts: BenchmarkRunTestPrompt[],
  testMargins: BenchmarkRunTestMarginOfError[]
): Promise<void> {
  const props = mapRunToReportData(run, bundles, prompts, testMargins);
  const blob = await generateSafetyReportBlob(props);
  const filename = run.name ? `${run.name}.pdf` : `benchmark-run-${run.id ?? 'report'}.pdf`;
  await saveBlobAsFile(blob, filename, {
    description: 'PDF',
    mime: 'application/pdf',
    extension: '.pdf',
  });
}
