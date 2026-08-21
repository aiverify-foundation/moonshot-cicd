import type { HazardSection } from './types';

/** Total element budget per page (content + chrome). */
export const HAZARD_SCOPE_PAGE_MAX_ELEMENTS = 12;
/** Section title + intro on the first hazard page. */
export const HAZARD_SCOPE_SECTION_HEADER_ELEMENTS = 2;
/** Report footer on the last hazard page. */
export const HAZARD_SCOPE_FOOTER_ELEMENTS = 2;

function contentElementCount(page: HazardSection[]): number {
  return page.reduce((sum, section) => sum + 1 + section.items.length, 0);
}

/** Content slots available on a page after reserving header/footer chrome. */
export function hazardContentBudget(
  pageIndex: number,
  pageCount: number
): number {
  let budget = HAZARD_SCOPE_PAGE_MAX_ELEMENTS;
  if (pageIndex === 0) {
    budget -= HAZARD_SCOPE_SECTION_HEADER_ELEMENTS;
  }
  if (pageIndex === pageCount - 1) {
    budget -= HAZARD_SCOPE_FOOTER_ELEMENTS;
  }
  return budget;
}

export function hazardPageTotalElements(
  page: HazardSection[],
  pageIndex: number,
  pageCount: number
): number {
  let total = contentElementCount(page);
  if (pageIndex === 0) {
    total += HAZARD_SCOPE_SECTION_HEADER_ELEMENTS;
  }
  if (pageIndex === pageCount - 1) {
    total += HAZARD_SCOPE_FOOTER_ELEMENTS;
  }
  return total;
}

function paginateWithContentLimits(
  sections: HazardSection[],
  firstPageLimit: number,
  otherPageLimit: number
): HazardSection[][] {
  const pages: HazardSection[][] = [[]];
  let pageIndex = 0;
  let used = 0;

  const limitFor = (index: number) =>
    index === 0 ? firstPageLimit : otherPageLimit;

  for (const section of sections) {
    if (section.items.length === 0) continue;

    let itemIndex = 0;
    while (itemIndex < section.items.length) {
      const limit = limitFor(pageIndex);
      const remaining = limit - used;

      if (remaining === 0) {
        pages.push([]);
        pageIndex++;
        used = 0;
        continue;
      }

      if (remaining < 2) {
        pages.push([]);
        pageIndex++;
        used = 0;
        continue;
      }

      const itemsToAdd = Math.min(
        remaining - 1,
        section.items.length - itemIndex
      );
      pages[pageIndex].push({
        tag: section.tag,
        items: section.items.slice(itemIndex, itemIndex + itemsToAdd),
      });
      used += 1 + itemsToAdd;
      itemIndex += itemsToAdd;
    }
  }

  return pages;
}

/** Split a page so the kept portion has at most maxContent elements. */
function splitPageToFit(
  page: HazardSection[],
  maxContent: number
): [HazardSection[], HazardSection[]] {
  const kept: HazardSection[] = [];
  const overflow: HazardSection[] = [];
  let used = 0;
  let spilling = false;

  for (const section of page) {
    if (spilling) {
      overflow.push({ tag: section.tag, items: [...section.items] });
      continue;
    }

    const remaining = maxContent - used;
    if (remaining < 2) {
      spilling = true;
      overflow.push({ tag: section.tag, items: [...section.items] });
      continue;
    }

    const itemsToKeep = Math.min(remaining - 1, section.items.length);
    kept.push({
      tag: section.tag,
      items: section.items.slice(0, itemsToKeep),
    });
    used += 1 + itemsToKeep;

    if (itemsToKeep < section.items.length) {
      spilling = true;
      overflow.push({
        tag: section.tag,
        items: section.items.slice(itemsToKeep),
      });
    }
  }

  return [kept, overflow];
}

function ensureFooterRoom(pages: HazardSection[][]): HazardSection[][] {
  const result = pages.map((page) =>
    page.map((section) => ({
      tag: section.tag,
      items: [...section.items],
    }))
  );

  while (result.length > 0) {
    const pageCount = result.length;
    const maxLast = hazardContentBudget(pageCount - 1, pageCount);
    const last = result[pageCount - 1];
    if (contentElementCount(last) <= maxLast) {
      break;
    }
    const [kept, overflow] = splitPageToFit(last, maxLast);
    if (overflow.length === 0 || contentElementCount(overflow) === 0) {
      break;
    }
    result[pageCount - 1] = kept.filter((s) => s.items.length > 0);
    if (result[pageCount - 1].length === 0) {
      result.pop();
    }
    result.push(overflow.filter((s) => s.items.length > 0));
  }

  return result.length > 0 ? result : [[]];
}

/**
 * Paginate hazard sections into pages of at most 12 elements each.
 * Bundle tag = 1; each test (title + desc) = 1;
 * section header on first page = 2; footer on last page = 2.
 * When a bundle continues onto the next page, its tag is repeated.
 */
export function paginateHazardSections(
  sections: HazardSection[]
): HazardSection[][] {
  const hasContent = sections.some((s) => s.items.length > 0);
  if (!hasContent) {
    return [[]];
  }

  // First page reserves header (2); footer is applied in ensureFooterRoom.
  const firstPageLimit =
    HAZARD_SCOPE_PAGE_MAX_ELEMENTS - HAZARD_SCOPE_SECTION_HEADER_ELEMENTS;
  const pages = paginateWithContentLimits(
    sections,
    firstPageLimit,
    HAZARD_SCOPE_PAGE_MAX_ELEMENTS
  );

  return ensureFooterRoom(pages);
}
