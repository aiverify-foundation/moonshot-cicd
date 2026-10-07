import { renderHook, waitFor } from "@testing-library/react"
import { useFeatureFlags } from "@/hooks/useFeatureFlags"
import { getFeatureFlags } from "@/lib/api"
import { FeatureFlagNames } from "@/lib/featureFlags"

jest.mock("@/lib/api", () => ({
  getFeatureFlags: jest.fn(),
}))

const mockGetFeatureFlags = getFeatureFlags as jest.MockedFunction<
  typeof getFeatureFlags
>

describe("useFeatureFlags", () => {
  const originalError = console.error

  beforeEach(() => {
    jest.clearAllMocks()
    console.error = jest.fn()
  })

  afterEach(() => {
    console.error = originalError
  })

  it("returns loading then enables known flags", async () => {
    mockGetFeatureFlags.mockResolvedValue({
      flags: { [FeatureFlagNames.AIVET_Q42026_MOON774]: true },
    })

    const { result } = renderHook(() => useFeatureFlags())

    expect(result.current.loading).toBe(true)
    expect(result.current.isEnabled(FeatureFlagNames.AIVET_Q42026_MOON774)).toBe(
      false
    )

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.isEnabled(FeatureFlagNames.AIVET_Q42026_MOON774)).toBe(
      true
    )
  })

  it("fails closed when flag is false", async () => {
    mockGetFeatureFlags.mockResolvedValue({
      flags: { [FeatureFlagNames.AIVET_Q42026_MOON774]: false },
    })

    const { result } = renderHook(() => useFeatureFlags())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.isEnabled(FeatureFlagNames.AIVET_Q42026_MOON774)).toBe(
      false
    )
  })

  it("fails closed when fetch errors", async () => {
    mockGetFeatureFlags.mockRejectedValue(new Error("network"))

    const { result } = renderHook(() => useFeatureFlags())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.flags).toEqual({})
    expect(result.current.isEnabled(FeatureFlagNames.AIVET_Q42026_MOON774)).toBe(
      false
    )
  })

  it("fails closed when flag is missing from response", async () => {
    mockGetFeatureFlags.mockResolvedValue({ flags: {} })

    const { result } = renderHook(() => useFeatureFlags())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.isEnabled(FeatureFlagNames.AIVET_Q42026_MOON774)).toBe(
      false
    )
  })
})
