/**
 * Reality-ladder provenance (REAL_DATA_PLAN.md §3) — single source of
 * truth for the REAL/SYNTHETIC/PLACEHOLDER palette, same JS-constant
 * pattern as `utils/band.ts` (kept in sync with `index.css`'s
 * `--real`/`--synthetic`/`--placeholder` custom properties by hand since
 * Tailwind v4 utility classes here read plain hex, not var()).
 */
export type ProvenanceKind = 'real' | 'real-cited' | 'synthetic' | 'placeholder'

export const PROVENANCE_COLORS: Record<ProvenanceKind, string> = {
  real: '#22d3ee',
  'real-cited': '#22d3ee',
  synthetic: '#a78bfa',
  placeholder: '#f59e0b',
}

export const PROVENANCE_LABELS: Record<ProvenanceKind, string> = {
  real: 'REAL',
  'real-cited': 'REAL · CITED',
  synthetic: 'SYNTHETIC',
  placeholder: 'PLACEHOLDER',
}

/**
 * Reality Pass R6, hard rule #1: fully automatic from the `placeholder`
 * boolean every satellite-derived payload carries
 * (`sat_result.placeholder`, thematic-layer `placeholder`,
 * `watershed-impact` summary/timeseries `placeholder`) — never a
 * hardcoded chip. Flips to REAL the instant the field flips to `false`,
 * with zero UI code change.
 */
export function provenanceFromPlaceholderFlag(placeholder: boolean): ProvenanceKind {
  return placeholder ? 'placeholder' : 'real'
}
