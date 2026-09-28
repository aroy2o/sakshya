/**
 * Single source of truth for evidence-band color/label mapping. Every place
 * a band shows up (map pins, BandBadge, MapLegend, ScoreBreakdown) imports
 * from here — never re-declares its own palette. Bands and thresholds per
 * PRD §12.5: verified >= 70, review 40-69, flag < 40.
 */
import type { Band } from '@/types/domain'

export const BAND_COLORS: Record<Band, string> = {
  verified: '#16a34a', // green-600
  review: '#d97706', // amber-600
  flag: '#dc2626', // red-600
}

export const BAND_BG_COLORS: Record<Band, string> = {
  verified: '#dcfce7', // green-100
  review: '#fef3c7', // amber-100
  flag: '#fee2e2', // red-100
}

export const BAND_LABELS: Record<Band, string> = {
  verified: 'Verified',
  review: 'Needs review',
  flag: 'Flag for inspection',
}

/** Neutral color for a pin/badge whose asset hasn't been scored yet. */
export const UNSCORED_COLOR = '#94a3b8' // slate-400
export const UNSCORED_BG_COLOR = '#f1f5f9' // slate-100
export const UNSCORED_LABEL = 'Not yet scored'

export function bandColor(band: Band | null): string {
  return band === null ? UNSCORED_COLOR : BAND_COLORS[band]
}

export function bandBgColor(band: Band | null): string {
  return band === null ? UNSCORED_BG_COLOR : BAND_BG_COLORS[band]
}

export function bandLabel(band: Band | null): string {
  return band === null ? UNSCORED_LABEL : BAND_LABELS[band]
}
