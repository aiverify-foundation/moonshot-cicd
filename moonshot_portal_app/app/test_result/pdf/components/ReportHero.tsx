import React from 'react';
import {
  Circle,
  Defs,
  LinearGradient,
  Rect,
  Stop,
  Svg,
  Text,
  View,
} from '@react-pdf/renderer';
import { REPORT_METADATA } from '../constants';
import { brand, styles } from '../styles';

type ReportHeroProps = {
  companyName: string;
  testRunName: string;
  reportDate: string;
};

function HeroGradient() {
  return (
    <Svg style={styles.heroGradient} viewBox="0 0 100 100" preserveAspectRatio="none">
      <Defs>
        <LinearGradient id="heroGrad" x1="0" y1="0" x2="1" y2="0">
          <Stop offset="0%" stopColor={brand.purpleDark} />
          <Stop offset="70%" stopColor={brand.purpleMid} />
          <Stop offset="100%" stopColor={brand.magenta} />
        </LinearGradient>
      </Defs>
      <Rect x="0" y="0" width="100" height="100" fill="url(#heroGrad)" />
    </Svg>
  );
}

type HeroRingProps = {
  size: number;
  opacity: number;
  style: NonNullable<React.ComponentProps<typeof Svg>['style']>;
};

function HeroRing({ size, opacity, style }: HeroRingProps) {
  const radius = size / 2 - 0.5;
  const center = size / 2;

  return (
    <Svg style={style} width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <Circle
        cx={center}
        cy={center}
        r={radius}
        stroke="#FFFFFF"
        strokeOpacity={opacity}
        strokeWidth={1}
        fill="none"
      />
    </Svg>
  );
}

export default function ReportHero({
  companyName,
  testRunName,
  reportDate,
}: ReportHeroProps) {
  const fields = [
    { label: 'Model / App Configuration Name', value: companyName },
    { label: 'Test Run Name', value: testRunName },
    { label: 'Test Tool', value: REPORT_METADATA.testTool },
    { label: 'Issued', value: reportDate },
  ];

  return (
    <View style={styles.hero} wrap={false}>
      <HeroGradient />
      <HeroRing size={460} opacity={0.1} style={styles.heroRingOuter} />
      <HeroRing size={340} opacity={0.08} style={styles.heroRingMid} />
      <HeroRing size={220} opacity={0.06} style={styles.heroRingInner} />

      <View style={styles.heroBody}>
        <Text style={styles.heroTitle}>
          AI Verify Baseline Safety Benchmark Testing Report
        </Text>
        <View style={styles.heroDivider} />
        <View style={styles.heroMetaRow}>
          {fields.map((f) => (
            <View key={f.label} style={styles.heroMetaField}>
              <Text style={styles.heroMetaLabel}>{f.label}</Text>
              <Text style={styles.heroMetaValue}>{f.value}</Text>
            </View>
          ))}
        </View>
      </View>
    </View>
  );
}
