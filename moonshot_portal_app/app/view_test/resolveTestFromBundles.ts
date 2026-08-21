import type { Bundle, BundleTest } from '@/lib/api';

/**
 * Find a benchmark test in loaded bundles by display name and dataset id
 * (matches query params from ViewBundleDetailsSheet "Learn More" link).
 */
export function findTestInBundles(
  bundles: Bundle[],
  testName: string,
  datasetId: string,
): BundleTest | undefined {
  const decodedName = decodeURIComponent(testName);
  const decodedDatasetId = decodeURIComponent(datasetId);

  for (const bundle of bundles) {
    for (const test of bundle.tests) {
      if (
        test.name === decodedName &&
        test.dataset?.id === decodedDatasetId
      ) {
        return test;
      }
    }
  }

  return undefined;
}
