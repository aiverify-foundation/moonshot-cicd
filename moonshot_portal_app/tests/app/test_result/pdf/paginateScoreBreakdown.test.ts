import {
  paginateScoreBreakdown,
  SCORE_BREAKDOWN_CONTINUATION_PAGE_MAX_ROWS,
  SCORE_BREAKDOWN_FIRST_PAGE_MAX_ROWS,
} from '@/app/test_result/pdf/paginateScoreBreakdown';
import type { SafetyReportBundle } from '@/app/test_result/pdf/types';

function makeItem(label: string) {
  return { label, score: 80 };
}

function makeBundle(name: string, itemCount: number): SafetyReportBundle {
  return {
    name,
    score: 80,
    items: Array.from({ length: itemCount }, (_, i) =>
      makeItem(`${name} Test ${i + 1}`)
    ),
  };
}

function rowKinds(chunk: ReturnType<typeof paginateScoreBreakdown>[number]) {
  return chunk.map((row) => row.kind);
}

describe('paginateScoreBreakdown', () => {
  it('returns a single empty chunk when there are no bundles', () => {
    expect(paginateScoreBreakdown([])).toEqual([[]]);
  });

  it('skips bundles with zero items', () => {
    const bundles: SafetyReportBundle[] = [
      { name: 'Empty', score: 0, items: [] },
      makeBundle('Safety', 2),
    ];

    const chunks = paginateScoreBreakdown(bundles);
    expect(chunks).toHaveLength(1);
    expect(chunks[0]).toHaveLength(3);
    expect(rowKinds(chunks[0])).toEqual(['bundle', 'item', 'item']);
  });

  it('keeps a single bundle with at most first-page limit rows in one chunk', () => {
    const bundles = [makeBundle('Safety', 8)];
    const chunks = paginateScoreBreakdown(bundles);

    expect(chunks).toHaveLength(1);
    expect(chunks[0]).toHaveLength(9);
    expect(chunks[0].length).toBeLessThanOrEqual(SCORE_BREAKDOWN_FIRST_PAGE_MAX_ROWS);
  });

  it('splits 10 test items across two chunks with a repeated bundle header', () => {
    const bundles = [makeBundle('Safety', 10)];
    const chunks = paginateScoreBreakdown(bundles);

    expect(chunks).toHaveLength(2);
    expect(chunks[0]).toHaveLength(SCORE_BREAKDOWN_FIRST_PAGE_MAX_ROWS);
    expect(chunks[1]).toHaveLength(2);
    expect(rowKinds(chunks[0])[0]).toBe('bundle');
    expect(rowKinds(chunks[1])[0]).toBe('bundle');
  });

  it('splits 24 test items across three chunks respecting row limits', () => {
    const bundles = [makeBundle('Safety', 24)];
    const chunks = paginateScoreBreakdown(bundles);

    expect(chunks).toHaveLength(3);
    expect(chunks[0]).toHaveLength(SCORE_BREAKDOWN_FIRST_PAGE_MAX_ROWS);
    expect(chunks[1]).toHaveLength(SCORE_BREAKDOWN_CONTINUATION_PAGE_MAX_ROWS);
    expect(chunks[2]).toHaveLength(2);
  });

  it('splits 25 test items across three chunks with the last chunk partially filled', () => {
    const bundles = [makeBundle('Safety', 25)];
    const chunks = paginateScoreBreakdown(bundles);

    expect(chunks).toHaveLength(3);
    expect(chunks[0]).toHaveLength(SCORE_BREAKDOWN_FIRST_PAGE_MAX_ROWS);
    expect(chunks[1]).toHaveLength(SCORE_BREAKDOWN_CONTINUATION_PAGE_MAX_ROWS);
    expect(chunks[2]).toHaveLength(3);
  });

  it('repeats bundle header when a bundle continues on the next chunk', () => {
    const bundles = [makeBundle('Safety', 12)];
    const chunks = paginateScoreBreakdown(bundles);

    expect(chunks).toHaveLength(2);
    expect(rowKinds(chunks[0])[0]).toBe('bundle');
    expect(rowKinds(chunks[1])[0]).toBe('bundle');
    expect(chunks[1].filter((row) => row.kind === 'item')).toHaveLength(3);
  });

  it('never places a bundle header without at least one item in the same chunk', () => {
    const bundles = [
      makeBundle('A', 9),
      makeBundle('B', 5),
      makeBundle('C', 20),
    ];
    const chunks = paginateScoreBreakdown(bundles);

    for (const chunk of chunks) {
      for (let i = 0; i < chunk.length; i++) {
        if (chunk[i].kind === 'bundle') {
          expect(chunk[i + 1]?.kind).toBe('item');
        }
      }
    }
  });

  it('respects per-chunk row limits', () => {
    const bundles = [makeBundle('Safety', 40)];
    const chunks = paginateScoreBreakdown(bundles);

    expect(chunks[0].length).toBeLessThanOrEqual(SCORE_BREAKDOWN_FIRST_PAGE_MAX_ROWS);
    for (let i = 1; i < chunks.length; i++) {
      expect(chunks[i].length).toBeLessThanOrEqual(
        SCORE_BREAKDOWN_CONTINUATION_PAGE_MAX_ROWS
      );
    }
  });
});
