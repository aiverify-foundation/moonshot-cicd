import React from 'react';
import { Text, View } from '@react-pdf/renderer';
import { USE_CASE_COPY } from '../constants';
import { styles } from '../styles';

export default function UseCaseSection() {
  return (
    <View style={styles.card}>
      <Text style={styles.sectionTitle}>Use Case</Text>
      <Text style={styles.useCaseBody}>{USE_CASE_COPY}</Text>
    </View>
  );
}
