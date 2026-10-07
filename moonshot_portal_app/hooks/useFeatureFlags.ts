import { useState, useEffect, useCallback } from "react"
import { getFeatureFlags } from "@/lib/api"
import type { FeatureFlagName } from "@/lib/featureFlags"

export interface UseFeatureFlagsReturn {
  flags: Partial<Record<FeatureFlagName, boolean>>
  loading: boolean
  isEnabled: (name: FeatureFlagName) => boolean
}

/**
 * Loads feature flags once on mount. Fail closed: missing/error → false.
 */
export function useFeatureFlags(): UseFeatureFlagsReturn {
  const [flags, setFlags] = useState<Partial<Record<FeatureFlagName, boolean>>>(
    {}
  )
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const response = await getFeatureFlags()
        if (!cancelled) {
          setFlags(response.flags ?? {})
        }
      } catch (err) {
        console.error("Error fetching feature flags:", err)
        if (!cancelled) {
          setFlags({})
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  const isEnabled = useCallback(
    (name: FeatureFlagName): boolean => flags[name] === true,
    [flags]
  )

  return { flags, loading, isEnabled }
}
