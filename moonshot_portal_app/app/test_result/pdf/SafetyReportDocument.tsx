import React from 'react';
import { Document, Page } from '@react-pdf/renderer';
import ReportHeader from './components/ReportHeader';
import ReportHero from './components/ReportHero';
import ScoreBreakdown from './components/ScoreBreakdown';
import InterpretationGuide from './components/InterpretationGuide';
import UseCaseSection from './components/UseCaseSection';
import HazardScope from './components/HazardScope';
import ReportFooter from './components/ReportFooter';
import { paginateScoreBreakdown } from './paginateScoreBreakdown';
import { styles } from './styles';
import type { SafetyReportPdfProps } from './types';

export default function SafetyReportDocument({
  companyName,
  testRunName,
  reportDate,
  bundles,
}: SafetyReportPdfProps) {
  const chunks = paginateScoreBreakdown(bundles);

  return (
    <Document
      title={`AI Verify Safety Report — ${testRunName}`}
      author="AI Verify Foundation"
    >
      <Page size="A4" style={styles.page}>
        <ReportHeader />

        <ReportHero
          companyName={companyName}
          testRunName={testRunName}
          reportDate={reportDate}
        />

        <ScoreBreakdown rows={chunks[0] ?? []} showSectionHeader />
      </Page>

      {chunks.slice(1).map((rows, index) => (
        <Page key={`score-${index}`} size="A4" style={styles.page}>
          <ScoreBreakdown rows={rows} showSectionHeader />
        </Page>
      ))}

      <Page size="A4" style={styles.page}>
        <InterpretationGuide />
        <UseCaseSection />
      </Page>

      <Page size="A4" style={styles.page}>
        <HazardScope />
        <ReportFooter />
      </Page>
    </Document>
  );
}
