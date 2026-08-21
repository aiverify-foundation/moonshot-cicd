import React from 'react';
import { Text, View } from '@react-pdf/renderer';
import { brand, styles } from '../styles';

const SCORE_SCALE_MARKS = ['0', '50', '100'] as const;

type ScoreBarProps = {
  score: number;
  ciLow?: number;
  ciHigh?: number;
};

export default function ScoreBar({ score, ciLow, ciHigh }: ScoreBarProps) {
  const h = 10;
  const clampedScore = Math.min(100, Math.max(0, score));
  const hasCi = ciLow != null && ciHigh != null && ciHigh > ciLow;

  return (
    <View style={{ width: '100%' }}>
      <View style={{ width: '100%', height: h, position: 'relative' }}>
        <View
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 0,
            height: h,
            borderRadius: 999,
            backgroundColor: brand.barTrack,
          }}
        />
        {hasCi && (
          <View
            style={{
              position: 'absolute',
              top: 1,
              bottom: 1,
              left: `${ciLow}%`,
              width: `${ciHigh - ciLow}%`,
              borderRadius: 999,
              backgroundColor: brand.purple,
              opacity: 0.2,
            }}
          />
        )}
        <View
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            height: h,
            width: `${clampedScore}%`,
            borderRadius: 999,
            backgroundColor: brand.purple,
          }}
        />
        {hasCi &&
          [ciLow, ciHigh].map((p) => (
            <View
              key={p}
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: `${p}%`,
                width: 2,
                backgroundColor: 'rgba(0,0,0,0.25)',
                borderRadius: 2,
              }}
            />
          ))}
      </View>

      <View style={styles.scoreBarScaleRow}>
        {SCORE_SCALE_MARKS.map((mark) => (
          <Text key={mark} style={styles.scoreBarScaleLabel}>
            {mark}
          </Text>
        ))}
      </View>
    </View>
  );
}
