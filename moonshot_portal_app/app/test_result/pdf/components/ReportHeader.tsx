import React from 'react';
import { Image, View } from '@react-pdf/renderer';
import { styles } from '../styles';
import logoRgb from '../assets/AIVerifyLogo_RGB_Cropped.png';

export default function ReportHeader() {
  return (
    <View style={styles.header} wrap={false}>
      {/* eslint-disable-next-line jsx-a11y/alt-text -- @react-pdf/renderer Image has no alt prop */}
      <Image src={logoRgb.src} style={styles.headerLogo} />
    </View>
  );
}
