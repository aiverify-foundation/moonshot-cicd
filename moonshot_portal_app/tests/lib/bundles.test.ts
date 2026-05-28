import {
  IMDA_STARTER_KIT_CATEGORY,
  isImdaStarterKitBundle,
  sortBundlesForDisplay,
} from '@/lib/bundles';
import type { Bundle } from '@/lib/api';

function makeBundle(id: string, category: string): Bundle {
  return {
    id,
    name: id,
    description: '',
    category,
    tests: [],
  };
}

describe('sortBundlesForDisplay', () => {
  it('places IMDA Starter Kit bundles before others while preserving order within each group', () => {
    const bundles = [
      makeBundle('other-a', 'Custom'),
      makeBundle('imda-1', IMDA_STARTER_KIT_CATEGORY),
      makeBundle('other-b', 'Research'),
      makeBundle('imda-2', IMDA_STARTER_KIT_CATEGORY),
    ];

    expect(sortBundlesForDisplay(bundles).map((b) => b.id)).toEqual([
      'imda-1',
      'imda-2',
      'other-a',
      'other-b',
    ]);
  });

  it('returns a new array without mutating the input', () => {
    const bundles = [makeBundle('a', 'Custom')];
    const sorted = sortBundlesForDisplay(bundles);

    expect(sorted).not.toBe(bundles);
    expect(bundles.map((b) => b.id)).toEqual(['a']);
  });
});

describe('isImdaStarterKitBundle', () => {
  it('matches the IMDA Starter Kit category exactly', () => {
    expect(isImdaStarterKitBundle(makeBundle('x', IMDA_STARTER_KIT_CATEGORY))).toBe(true);
    expect(isImdaStarterKitBundle(makeBundle('x', 'IMDA Starter Kit'))).toBe(false);
  });
});
