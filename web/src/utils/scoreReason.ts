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
import { NO_SATELLITE_SIGNAL_CATEGORIES } from '@/schemas/domain'
import type { AssetDetail } from '@/types/domain'

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

function describeSatellite(asset: AssetDetail): string | null {
  if (asset.satellite_score === null || asset.sat_result === null) return null
  if (NO_SATELLITE_SIGNAL_CATEGORIES.includes(asset.category as (typeof NO_SATELLITE_SIGNAL_CATEGORIES)[number])) {
    return `This activity category has no reliable satellite signal, so the satellite score is a neutral ${asset.satellite_score}/30 rather than a real verdict.`
  }
  const { interpretation } = asset.sat_result
  switch (interpretation) {
    case 'strongly_positive':
      return `Satellite imagery shows a strong positive change matching what "${asset.activity}" should produce on the ground (${asset.satellite_score}/30).`
    case 'weakly_positive':
      return `Satellite imagery shows a weak positive change (${asset.satellite_score}/30).`
    case 'inconclusive':
      return `Satellite change is close to zero / inconclusive (${asset.satellite_score}/30).`
    case 'negative':
      return `Satellite imagery shows a decline relative to the control area (${asset.satellite_score}/30) — this can also mean the work is too recent to show up yet, not necessarily failure.`
    case 'neutral_no_signal':
      return `No reliable satellite signal is expected for this category, so the satellite score is a neutral ${asset.satellite_score}/30.`
  }
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
