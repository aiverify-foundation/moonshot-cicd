import {
  BenchmarkRun,
  BenchmarkRunResultsBundleSummary,
  BenchmarkRunTestMarginOfError,
  BenchmarkRunTestPrompt,
} from '@/lib/api';
import { metricToPercentPoints } from '../components/metricToPercentPoints';
import {
  accuracyToPercent,
  meanScorePercent,
} from '../components/scorePercent';
import type { SafetyReportBundle, SafetyReportPdfProps, SafetyReportScoreItem } from './types';

function ciFromScoreAndMargin(
  score: number,
  marginHalfWidthPercent: number | null | undefined
): Pick<SafetyReportScoreItem, 'ciLow' | 'ciHigh'> {
  if (marginHalfWidthPercent == null || marginHalfWidthPercent <= 0) return {};
  return {
    ciLow: Math.max(0, Math.round(score - marginHalfWidthPercent)),
    ciHigh: Math.min(100, Math.round(score + marginHalfWidthPercent)),
  };
}

function chartItemsFromPrompts(
  prompts: BenchmarkRunTestPrompt[],
  marginPercentByTestId: Map<number, number>
): SafetyReportScoreItem[] {
  const byTestId = new Map<number, { test_name: string; pcts: number[] }>();
  for (const p of prompts) {
    if (p.test_id == null) continue;
    const tid = p.test_id;
    const pct = accuracyToPercent(p.score);
    if (pct == null) continue;
    const name = (p.test_name ?? 'Unknown').trim() || 'Unknown';
    if (!byTestId.has(tid)) byTestId.set(tid, { test_name: name, pcts: [] });
    byTestId.get(tid)!.pcts.push(pct);
  }

  const items: SafetyReportScoreItem[] = [];
  for (const tid of byTestId.keys()) {
    const v = byTestId.get(tid)!;
    const score = Math.round(v.pcts.reduce((a, b) => a + b, 0) / v.pcts.length);
    const margin = marginPercentByTestId.get(tid);
    items.push({
      label: v.test_name,
      score,
      ...ciFromScoreAndMargin(score, margin),
    });
  }
  items.sort((a, b) => a.label.localeCompare(b.label));
  return items;
}

function bundleMeanPercent(
  prompts: BenchmarkRunTestPrompt[],
  testIds: number[]
): number | null {
  const set = new Set(testIds);
  const pts = prompts
    .filter((p) => p.test_id != null && set.has(p.test_id))
    .map((p) => accuracyToPercent(p.score))
    .filter((x): x is number => x != null);
  return meanScorePercent(pts);
}

function bundleCiFromItems(
  items: SafetyReportScoreItem[]
): Pick<SafetyReportBundle, 'ciLow' | 'ciHigh'> {
  const withCi = items.filter((i) => i.ciLow != null && i.ciHigh != null);
  if (!withCi.length) return {};
  return {
    ciLow: Math.min(...withCi.map((i) => i.ciLow!)),
    ciHigh: Math.max(...withCi.map((i) => i.ciHigh!)),
  };
}

function formatReportDate(run: BenchmarkRun): string {
  const raw = run.end_time ?? run.start_time;
  if (!raw) return '—';
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return raw;
  return d.toLocaleDateString('en-SG', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function overallScoreFromPrompts(prompts: BenchmarkRunTestPrompt[]): number {
  const pts = prompts
    .map((p) => accuracyToPercent(p.score))
    .filter((x): x is number => x != null);
  return meanScorePercent(pts) ?? 0;
}

export function mapRunToReportData(
  run: BenchmarkRun,
  bundles: BenchmarkRunResultsBundleSummary[],
  prompts: BenchmarkRunTestPrompt[],
  testMargins: BenchmarkRunTestMarginOfError[]
): Omit<SafetyReportPdfProps, 'hazardSections'> {
  const marginPercentByTestId = new Map<number, number>();
  for (const row of testMargins) {
    const c = metricToPercentPoints(row.margin_of_error);
    if (c != null && c > 0) marginPercentByTestId.set(row.test_id, c);
  }

  let reportBundles: SafetyReportBundle[];

  if (bundles.length === 0) {
    const items = chartItemsFromPrompts(prompts, marginPercentByTestId);
    const allTestIds = [
      ...new Set(
        prompts.map((p) => p.test_id).filter((id): id is number => id != null)
      ),
    ];
    const bundleScore =
      bundleMeanPercent(prompts, allTestIds) ?? overallScoreFromPrompts(prompts);
    reportBundles = [
      {
        name: 'All results',
        score: bundleScore,
        ...bundleCiFromItems(items),
        items,
      },
    ];
  } else {
    reportBundles = bundles.map((b) => {
      const filtered = prompts.filter(
        (p) => p.test_id != null && b.test_ids.includes(p.test_id)
      );
      const items = chartItemsFromPrompts(filtered, marginPercentByTestId);
      const score = bundleMeanPercent(prompts, b.test_ids) ?? 0;
      return {
        name: b.name,
        score,
        ...bundleCiFromItems(items),
        items,
      };
    });
  }

  return {
    companyName: run.endpoint_config_name?.trim() || '—',
    testRunName: run.name,
    reportDate: formatReportDate(run),
    bundles: reportBundles,
  };
}
