import React from 'react';
import { Text, View } from '@react-pdf/renderer';
import { SCORE_BREAKDOWN_SUBTEXT, SCORE_BREAKDOWN_TITLE } from '../constants';
import type { ScoreBreakdownRow } from '../paginateScoreBreakdown';
import { styles } from '../styles';
import ScoreBar from './ScoreBar';

type ScoreBreakdownProps = {
  rows: ScoreBreakdownRow[];
  showSectionHeader: boolean;
};

const BUNDLE_LABEL_MAX_CHARS = 42;
/** Slightly under 2× single-line budget; react-pdf wraps within the label column. */
const ITEM_LABEL_MAX_CHARS = 76;

function truncateBundleLabel(label: string): string {
  if (label.length <= BUNDLE_LABEL_MAX_CHARS) return label;
  return `${label.slice(0, BUNDLE_LABEL_MAX_CHARS - 1)}…`;
}

function formatItemLabel(label: string): string {
  const normalized = label.trim().replace(/\s*\n\s*/g, ' ');
  if (normalized.length <= ITEM_LABEL_MAX_CHARS) return normalized;
  return `${normalized.slice(0, ITEM_LABEL_MAX_CHARS - 1)}…`;
}

function ScoreBreakdownHeader() {
  return (
    <>
      <Text style={styles.sectionTitle}>{SCORE_BREAKDOWN_TITLE}</Text>
      <Text style={styles.muted}>{SCORE_BREAKDOWN_SUBTEXT}</Text>

      <View style={styles.scoreHeaderRow}>
        <Text style={styles.scoreHeaderLabel}>Risk Category</Text>
        <Text style={styles.scoreHeaderBar} />
        <Text style={styles.scoreHeaderValue}>Score</Text>
      </View>
    </>
  );
}

export default function ScoreBreakdown({
  rows,
  showSectionHeader,
}: ScoreBreakdownProps) {
  return (
    <View style={styles.card} wrap={false}>
      {showSectionHeader && <ScoreBreakdownHeader />}

      {rows.map((row, index) => {
        if (row.kind === 'bundle') {
          return (
            <View
              key={`bundle-${row.bundleName}-${index}`}
              style={styles.scoreRow}
              wrap={false}
            >
              <Text style={[styles.scoreLabel, styles.scoreLabelBundle]}>
                {truncateBundleLabel(row.bundleName)}
              </Text>
              <View style={styles.scoreBarWrap} />
              <View style={styles.scoreValueSpacer} />
            </View>
          );
        }

        return (
          <View
            key={`${row.bundleName}-${row.item.label}-${index}`}
            style={styles.scoreRow}
          >
            <Text style={styles.scoreItemLabel}>{formatItemLabel(row.item.label)}</Text>
            <View style={styles.scoreBarWrap}>
              <ScoreBar
                score={row.item.score}
                ciLow={row.item.ciLow}
                ciHigh={row.item.ciHigh}
              />
            </View>
            <View style={styles.scoreValueWrap}>
              <View style={styles.scoreValueBadge}>
                <Text style={styles.scoreValue}>{row.item.score}</Text>
              </View>
            </View>
          </View>
        );
      })}
    </View>
  );
}
