import type { SafetyReportBundle, SafetyReportScoreItem } from './types';

export const SCORE_BREAKDOWN_FIRST_PAGE_MAX_ROWS = 8;
export const SCORE_BREAKDOWN_CONTINUATION_PAGE_MAX_ROWS = 15;

export type ScoreBreakdownRow =
  | { kind: 'bundle'; bundleName: string }
  | { kind: 'item'; bundleName: string; item: SafetyReportScoreItem };

export type ScoreBreakdownChunk = ScoreBreakdownRow[];

function chunkLimit(chunkIndex: number): number {
  return chunkIndex === 0
    ? SCORE_BREAKDOWN_FIRST_PAGE_MAX_ROWS
    : SCORE_BREAKDOWN_CONTINUATION_PAGE_MAX_ROWS;
}

export function paginateScoreBreakdown(
  bundles: SafetyReportBundle[]
): ScoreBreakdownChunk[] {
  const chunks: ScoreBreakdownChunk[] = [[]];
  let chunkIndex = 0;

  for (const bundle of bundles) {
    if (bundle.items.length === 0) continue;

    let itemIndex = 0;
    while (itemIndex < bundle.items.length) {
      const limit = chunkLimit(chunkIndex);
      const current = chunks[chunkIndex];
      const remaining = limit - current.length;

      if (remaining === 0) {
        chunks.push([]);
        chunkIndex++;
        continue;
      }

      // Bundle header must share a chunk with at least one item row.
      if (remaining < 2) {
        chunks.push([]);
        chunkIndex++;
        continue;
      }

      current.push({ kind: 'bundle', bundleName: bundle.name });
      const slotsForItems = limit - current.length;
      const itemsToAdd = Math.min(slotsForItems, bundle.items.length - itemIndex);

      for (let j = 0; j < itemsToAdd; j++) {
        current.push({
          kind: 'item',
          bundleName: bundle.name,
          item: bundle.items[itemIndex + j],
        });
      }
      itemIndex += itemsToAdd;
    }
  }

  return chunks;
}
