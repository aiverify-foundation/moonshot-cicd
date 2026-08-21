import React from 'react';
import { Text, View } from '@react-pdf/renderer';
import { styles } from '../styles';
import type { HazardSection } from '../types';

type HazardScopeProps = {
  hazardSections: HazardSection[];
  showSectionHeader: boolean;
};

export default function HazardScope({
  hazardSections,
  showSectionHeader,
}: HazardScopeProps) {
  return (
    <View style={styles.card}>
      {showSectionHeader && (
        <>
          <Text style={styles.sectionTitle}>
            Benchmarks Covered in Project Moonshot
          </Text>
          <Text style={styles.muted}>
            The benchmarks are selected from the following:
          </Text>
        </>
      )}
      {hazardSections.map((section, sectionIndex) => (
        <View key={`${section.tag}-${sectionIndex}`} style={styles.hazardCard}>
          <Text style={styles.hazardTag}>{section.tag}</Text>
          {section.items.map((item) => (
            <View key={item.title} wrap={false}>
              <Text style={styles.hazardItemTitle}>{item.title}</Text>
              <Text style={styles.hazardItemDesc}>{item.desc}</Text>
            </View>
          ))}
        </View>
      ))}
    </View>
  );
}
