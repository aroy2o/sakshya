/**
 * Builds the asset drawer's "plain-language reason" (FR5.3) from data the
 * API actually returned — geo_flags, ai_result, sat_result, the four
 * sub-scores. It never invents a number or a claim the underlying record
 * doesn't support (CLAUDE.md: "never fabricate a number"): a field that's
 * still null renders as "not yet scored", not as a guessed sentence.
 *
 * Keeps the visual-match and satellite-response explanations in separate
 * sentences on purpose — PRD §12.2 is explicit that "is this evidence of
 * the declared activity" (visual) and "did the intervention work"
 * (satellite) must never blend together, including in UI copy.
 */
import type { AssetDetail, SatInterpretation } from '@/types/domain'

function describeGeo(asset: AssetDetail): string | null {
  if (asset.geo_score === null || asset.geo_flags === null) return null
  const failed = asset.geo_flags.filter((f) => !f.passed)
  if (failed.length === 0) {
    return `Geo-integrity checks all passed (${asset.geo_score}/30).`
  }
  const names = failed.map((f) => f.rule.replace(/_/g, ' ')).join(', ')
  return `Geo-integrity scored ${asset.geo_score}/30 — failed: ${names}.`
}

function describeVisual(asset: AssetDetail): string | null {
  if (asset.visual_score === null || asset.ai_result === null) return null
  const { matches_declared, confidence } = asset.ai_result
  if (matches_declared === 'yes') {
    return `The AI photo check found the image consistent with the declared "${asset.activity}" activity (confidence ${Math.round(confidence * 100)}%).`
  }
  if (matches_declared === 'uncertain') {
    return `The AI photo check was uncertain whether the image matches "${asset.activity}" — routed to human review.`
  }
  return `The AI photo check found the image does not match the declared "${asset.activity}" activity.`
}

// Keyed off `sat_result.did_classification` (PRD §12.3's DiD bands) — trust
// the server's own classification rather than re-deriving it client-side
// from `category`; `neutral_no_signal` already covers the LS/LH/OM case.
const SATELLITE_INTERPRETATION_TEXT: Record<SatInterpretation, (score: number, activity: string) => string> = {
  strongly_positive: (score, activity) =>
    `Satellite imagery shows a strong positive change matching what "${activity}" should produce on the ground (${score}/30).`,
  weakly_positive: (score) => `Satellite imagery shows a weak positive change (${score}/30).`,
  inconclusive: (score) => `Satellite change is close to zero / inconclusive (${score}/30).`,
  negative: (score) => `Satellite imagery shows a decline relative to the control area (${score}/30).`,
  neutral_no_signal: (score) => `No reliable satellite signal is expected for this category, so the satellite score is a neutral ${score}/30.`,
}

function describeSatellite(asset: AssetDetail): string | null {
  if (asset.satellite_score === null || asset.sat_result === null) return null
  const { did_classification, notes, placeholder } = asset.sat_result
  const parts = [SATELLITE_INTERPRETATION_TEXT[did_classification](asset.satellite_score, asset.activity)]
  if (placeholder) {
    parts.push('This reading is placeholder data (no real satellite imagery processed yet), not a real verdict.')
  }
  parts.push(...notes) // server-authored caveats (e.g. PRD §12.3's "too early post-work" note) — rendered verbatim
  return parts.join(' ')
}

function describeTemporal(asset: AssetDetail): string | null {
  if (asset.temporal_score === null) return null
  if (asset.temporal_score === 5) {
    return 'Only one time point of photo evidence is available, so temporal consistency is scored neutral (5/10) rather than penalised.'
  }
  return `Temporal consistency scored ${asset.temporal_score}/10 based on progression across multiple photos.`
}

export function scoreReasonSentences(asset: AssetDetail): string[] {
  const sentences = [describeGeo(asset), describeVisual(asset), describeSatellite(asset), describeTemporal(asset)]
  return sentences.filter((s): s is string => s !== null)
}

export function scoreHeadline(asset: AssetDetail): string {
  if (asset.evidence_score === null || asset.band === null) {
    return 'Not yet scored — some sub-scores are still pending.'
  }
  switch (asset.band) {
    case 'verified':
      return `Verified — evidence score ${asset.evidence_score}/100. This is a triage signal, not a final verdict.`
    case 'review':
      return `Needs review — evidence score ${asset.evidence_score}/100.`
    case 'flag':
      return `Flagged for field inspection — evidence score ${asset.evidence_score}/100.`
  }
}
