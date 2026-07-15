import React from 'react';
import { Image, Link, Text, View } from '@react-pdf/renderer';
import { FOOTER_LINKS, FOOTER_LINK_URL } from '../constants';
import { styles } from '../styles';
import logoWhite from '../assets/AIVerifyLogo_White_Cropped.png';

export default function ReportFooter() {
  return (
    <View style={styles.footer} wrap={false}>
      <Image src={logoWhite.src} style={styles.footerLogo} />

      <View style={styles.footerLinksRow}>
        {FOOTER_LINKS.map((label) => (
          <Link key={label} src={FOOTER_LINK_URL} style={styles.footerLink}>
            {label}
          </Link>
        ))}
      </View>

      <Text style={styles.footerCopy}>
        © {new Date().getFullYear()} AI Verify Foundation. All rights reserved.{'\n'}
        AI Verify Foundation is a not-for-profit foundation.
      </Text>
    </View>
  );
}
