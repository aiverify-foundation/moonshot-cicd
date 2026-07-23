import {
  HAZARD_SCOPE_FOOTER_ELEMENTS,
  HAZARD_SCOPE_PAGE_MAX_ELEMENTS,
  HAZARD_SCOPE_SECTION_HEADER_ELEMENTS,
  hazardContentBudget,
  hazardPageTotalElements,
  paginateHazardSections,
} from '@/app/test_result/pdf/paginateHazardSections';
import type { HazardSection } from '@/app/test_result/pdf/types';

function makeSection(tag: string, itemCount: number): HazardSection {
  return {
    tag,
    items: Array.from({ length: itemCount }, (_, i) => ({
      title: `${tag} Test ${i + 1}`,
      desc: `Description ${i + 1}`,
    })),
  };
}

function contentElementCount(page: HazardSection[]): number {
  return page.reduce((sum, section) => sum + 1 + section.items.length, 0);
}

describe('paginateHazardSections', () => {
  it('returns a single empty page when there are no sections', () => {
    expect(paginateHazardSections([])).toEqual([[]]);
  });

  it('skips sections with zero items', () => {
    const pages = paginateHazardSections([
      { tag: 'Empty', items: [] },
      makeSection('Safety', 2),
    ]);

    expect(pages).toHaveLength(1);
    expect(pages[0]).toEqual([makeSection('Safety', 2)]);
  });

  it('reserves header and footer on a single page (content budget 8)', () => {
    // 1 tag + 7 tests = 8 content; +2 header +2 footer = 12
    const pages = paginateHazardSections([makeSection('Safety', 7)]);

    expect(pages).toHaveLength(1);
    expect(contentElementCount(pages[0])).toBe(8);
    expect(hazardPageTotalElements(pages[0], 0, 1)).toBe(
      HAZARD_SCOPE_PAGE_MAX_ELEMENTS
    );
  });

  it('spills to a second page when single-page content would exceed 8', () => {
    // 1 tag + 8 tests = 9 content → cannot fit with header+footer on one page
    const pages = paginateHazardSections([makeSection('Safety', 8)]);

    expect(pages).toHaveLength(2);
    expect(contentElementCount(pages[0])).toBeLessThanOrEqual(
      hazardContentBudget(0, 2)
    );
    expect(contentElementCount(pages[1])).toBeLessThanOrEqual(
      hazardContentBudget(1, 2)
    );
    expect(pages[0][0].tag).toBe('Safety');
    expect(pages[1][0].tag).toBe('Safety');
  });

  it('splits a 12-test bundle across pages with repeated tag', () => {
    const pages = paginateHazardSections([makeSection('Undesirable Content', 12)]);

    expect(pages.length).toBeGreaterThanOrEqual(2);
    expect(pages[0][0].tag).toBe('Undesirable Content');
    expect(pages[1][0].tag).toBe('Undesirable Content');
    expect(contentElementCount(pages[0])).toBe(hazardContentBudget(0, pages.length));
  });

  it('packs a continued bundle with the next bundle on a later page', () => {
    const pages = paginateHazardSections([
      makeSection('Undesirable Content', 12),
      makeSection('Adversarial Prompts', 1),
    ]);

    const last = pages[pages.length - 1];
    expect(last.some((s) => s.tag === 'Adversarial Prompts')).toBe(true);
    expect(
      last.some((s) => s.tag === 'Undesirable Content') || pages.length >= 2
    ).toBe(true);
  });

  it('never places a bundle tag without at least one item on the same page', () => {
    const pages = paginateHazardSections([
      makeSection('A', 11),
      makeSection('B', 5),
      makeSection('C', 20),
    ]);

    for (const [index, page] of pages.entries()) {
      for (const section of page) {
        expect(section.items.length).toBeGreaterThanOrEqual(1);
      }
      expect(contentElementCount(page)).toBeLessThanOrEqual(
        hazardContentBudget(index, pages.length)
      );
      expect(hazardPageTotalElements(page, index, pages.length)).toBeLessThanOrEqual(
        HAZARD_SCOPE_PAGE_MAX_ELEMENTS
      );
    }
  });

  it('places two small sections on the same page when they fit', () => {
    const pages = paginateHazardSections([
      makeSection('Undesirable Content', 2),
      makeSection('Adversarial Prompts', 1),
    ]);

    expect(pages).toHaveLength(1);
    expect(pages[0].map((s) => s.tag)).toEqual([
      'Undesirable Content',
      'Adversarial Prompts',
    ]);
    expect(contentElementCount(pages[0])).toBe(5);
    expect(hazardPageTotalElements(pages[0], 0, 1)).toBe(
      5 + HAZARD_SCOPE_SECTION_HEADER_ELEMENTS + HAZARD_SCOPE_FOOTER_ELEMENTS
    );
  });

  it('starts a new page when only one content slot remains before a new bundle', () => {
    // Two pages: first budget 10 (header only), last budget 10 (footer only).
    // Fill first with 1 tag + 8 items = 9; one slot left cannot fit tag + item.
    const pages = paginateHazardSections([
      makeSection('A', 8),
      makeSection('B', 2),
    ]);

    expect(pages).toHaveLength(2);
    expect(contentElementCount(pages[0])).toBe(9);
    expect(pages[1][0].tag).toBe('B');
    expect(pages[1][0].items).toHaveLength(2);
  });

  it('gives middle pages a full 12 content slots when there are 3+ pages', () => {
    const pages = paginateHazardSections([makeSection('Safety', 30)]);

    expect(pages.length).toBeGreaterThanOrEqual(3);
    expect(hazardContentBudget(0, pages.length)).toBe(
      HAZARD_SCOPE_PAGE_MAX_ELEMENTS - HAZARD_SCOPE_SECTION_HEADER_ELEMENTS
    );
    expect(hazardContentBudget(1, pages.length)).toBe(
      HAZARD_SCOPE_PAGE_MAX_ELEMENTS
    );
    expect(hazardContentBudget(pages.length - 1, pages.length)).toBe(
      HAZARD_SCOPE_PAGE_MAX_ELEMENTS - HAZARD_SCOPE_FOOTER_ELEMENTS
    );

    for (const [index, page] of pages.entries()) {
      expect(hazardPageTotalElements(page, index, pages.length)).toBeLessThanOrEqual(
        HAZARD_SCOPE_PAGE_MAX_ELEMENTS
      );
    }
  });
});
