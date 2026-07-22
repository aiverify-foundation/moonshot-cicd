import React from 'react';
import { Image, Text, View } from '@react-pdf/renderer';
import { styles } from '../styles';
import logoRgb from '../assets/AIVerifyLogo_RGB_Cropped.png';

export default function ReportHeader() {
  return (
    <View style={styles.header} wrap={false}>
      <Image src={logoRgb.src} style={styles.headerLogo} />
    </View>
  );
}
