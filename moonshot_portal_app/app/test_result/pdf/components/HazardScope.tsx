import React from 'react';
import { Text, View } from '@react-pdf/renderer';
import { HAZARD_SECTIONS } from '../constants';
import { styles } from '../styles';

export default function HazardScope() {
  return (
    <View style={styles.card}>
      <Text style={styles.sectionTitle}>Risk Scope Covered</Text>
      <Text style={styles.muted}>
        The benchmark covers two test bundles: Singapore Undesirable Content and
        AILuminate.
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
