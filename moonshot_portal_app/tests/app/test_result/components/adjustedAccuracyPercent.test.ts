import { adjustedAccuracyPercent } from '@/app/test_result/components/TestResultBundle'

describe('adjustedAccuracyPercent', () => {
  it('returns 0 when rowCount is 0', () => {
    expect(adjustedAccuracyPercent(5, 0, 0, 0)).toBe(0)
  })

  it('returns mean AI score when there are no disagreements', () => {
    expect(adjustedAccuracyPercent(8, 10, 0, 0)).toBe(80)
  })

  it('flips one AI-1 row to 0 when user disagrees once on a 1', () => {
    // 10 rows all score 1 → totalScore 10; one disagree on 1
    expect(adjustedAccuracyPercent(10, 10, 1, 0)).toBe(90)
  })

  it('flips one AI-0 row to 1 when user disagrees once on a 0', () => {
    expect(adjustedAccuracyPercent(0, 10, 0, 1)).toBe(10)
  })
})
