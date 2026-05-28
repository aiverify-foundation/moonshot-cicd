import type { Bundle } from './api';

/** Bundle category from test config YAML (`category` field). */
export const IMDA_STARTER_KIT_CATEGORY = "IMDA's Starter Kit";

export function isImdaStarterKitBundle(bundle: Pick<Bundle, 'category'>): boolean {
  return bundle.category === IMDA_STARTER_KIT_CATEGORY;
}

/** IMDA Starter Kit bundles first; other bundles keep API/default order. */
export function sortBundlesForDisplay<T extends Pick<Bundle, 'category'>>(bundles: T[]): T[] {
  const imdaStarterKit: T[] = [];
  const other: T[] = [];

  for (const bundle of bundles) {
    if (isImdaStarterKitBundle(bundle)) {
      imdaStarterKit.push(bundle);
    } else {
      other.push(bundle);
    }
  }

  return [...imdaStarterKit, ...other];
}
