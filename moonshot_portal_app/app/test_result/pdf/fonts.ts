import { Font } from '@react-pdf/renderer';

let fontsRegistered = false;

/** TTF URLs from fonts.googleapis.com (woff2 URLs 404 and break react-pdf). */
const MONTSERRAT_TTF = {
  400: 'https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCtr6Ew-.ttf',
  600: 'https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCu170w-.ttf',
  700: 'https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCuM70w-.ttf',
  900: 'https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCvC70w-.ttf',
} as const;

const INTER_TTF = {
  400: 'https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuLyfMZg.ttf',
  600: 'https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuGKYMZg.ttf',
} as const;

/**
 * Register Montserrat + Inter before rendering. Call from client PDF generation only.
 */
export function registerReportFonts(): void {
  if (fontsRegistered) return;

  Font.register({
    family: 'Montserrat',
    fonts: [
      { src: MONTSERRAT_TTF[400], fontWeight: 400 },
      { src: MONTSERRAT_TTF[600], fontWeight: 600 },
      { src: MONTSERRAT_TTF[700], fontWeight: 700 },
      { src: MONTSERRAT_TTF[900], fontWeight: 900 },
    ],
  });

  Font.register({
    family: 'Inter',
    fonts: [
      { src: INTER_TTF[400], fontWeight: 400 },
      { src: INTER_TTF[600], fontWeight: 600 },
    ],
  });

  fontsRegistered = true;
}
