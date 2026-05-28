import {
  adjustedAccuracyPercent,
  scoreFromApiScore,
} from '@/app/test_result/components/TestResultBundle'
import { metricToPercentPoints } from '@/app/test_result/components/metricToPercentPoints'

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

describe('metricToPercentPoints', () => {
  it('returns null for null, undefined, or NaN', () => {
    expect(metricToPercentPoints(null)).toBeNull()
    expect(metricToPercentPoints(undefined)).toBeNull()
    expect(metricToPercentPoints(Number.NaN)).toBeNull()
  })

  it('multiplies values in [0, 1] by 100', () => {
    expect(metricToPercentPoints(0)).toBe(0)
    expect(metricToPercentPoints(0.078)).toBeCloseTo(7.8)
    expect(metricToPercentPoints(1)).toBe(100)
  })

  it('passes through values greater than 1 as percentage points', () => {
    expect(metricToPercentPoints(7.8)).toBe(7.8)
    expect(metricToPercentPoints(50)).toBe(50)
  })
})

describe('scoreFromApiScore', () => {
  it('uses backend score directly and rounds to binary', () => {
    expect(scoreFromApiScore(1)).toBe(1)
    expect(scoreFromApiScore(0)).toBe(0)
    expect(scoreFromApiScore(0.6)).toBe(1)
    expect(scoreFromApiScore(0.4)).toBe(0)
  })

  it('defaults to 0 when backend score is missing or invalid', () => {
    expect(scoreFromApiScore(null)).toBe(0)
    expect(scoreFromApiScore(undefined)).toBe(0)
    expect(scoreFromApiScore(Number.NaN)).toBe(0)
  })
})
