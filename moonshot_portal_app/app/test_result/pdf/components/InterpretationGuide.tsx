import React from 'react';
import { Text, View } from '@react-pdf/renderer';
import { INTERPRETATION_POINTS } from '../constants';
import { styles } from '../styles';

export default function InterpretationGuide() {
  return (
    <View style={styles.card}>
      <Text style={styles.sectionTitle}>How to Interpret the Results</Text>
      {INTERPRETATION_POINTS.map((p, i) => (
        <View
          key={p.label}
          style={
            i === 0
              ? [styles.interpretationRow, { borderTopWidth: 0 }]
              : styles.interpretationRow
          }
        >
          <Text style={styles.interpretationIndex}>{i + 1}</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.interpretationLabel}>{p.label}</Text>
            <Text style={styles.interpretationBody}>{p.body}</Text>
          </View>
        </View>
      ))}
    </View>
  );
}
