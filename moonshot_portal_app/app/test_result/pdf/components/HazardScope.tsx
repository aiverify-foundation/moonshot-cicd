import React from 'react';
import { Text, View } from '@react-pdf/renderer';
import { HAZARD_SECTIONS } from '../constants';
import { styles } from '../styles';

export default function HazardScope() {
  return (
    <View style={styles.card}>
      <Text style={styles.sectionTitle}>Benchmarks Covered in Project Moonshot</Text>
      <Text style={styles.muted}>
        The benchmarks are selected from the following:
      </Text>
      {HAZARD_SECTIONS.map((section) => (
        <View key={section.tag} style={styles.hazardCard} wrap={false}>
          <Text style={styles.hazardTag}>{section.tag}</Text>
          {section.items.map((item) => (
            <View key={item.title}>
              <Text style={styles.hazardItemTitle}>{item.title}</Text>
              <Text style={styles.hazardItemDesc}>{item.desc}</Text>
            </View>
          ))}
        </View>
      ))}
    </View>
  );
}
