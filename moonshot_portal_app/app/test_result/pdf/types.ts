export type SafetyReportScoreItem = {
  label: string;
  score: number;
  ciLow?: number;
  ciHigh?: number;
};

export type SafetyReportBundle = {
  name: string;
  score: number;
  ciLow?: number;
  ciHigh?: number;
  items: SafetyReportScoreItem[];
};

export type SafetyReportPdfProps = {
  companyName: string;
  testRunName: string;
  reportDate: string;
  bundles: SafetyReportBundle[];
};
