import type { Bundle } from '@/lib/api';
import { isImdaStarterKitBundle } from '@/lib/bundles';
import type { HazardSection } from './types';

/** Map IMDA Starter Kit bundles to PDF hazard-scope sections. */
export function mapBundlesToHazardSections(bundles: Bundle[]): HazardSection[] {
  return bundles.filter(isImdaStarterKitBundle).map((bundle) => ({
    tag: bundle.name,
    items: bundle.tests.map((test) => ({
      title: test.name,
      desc: test.description ?? '',
    })),
  }));
}
