import { NO_SATELLITE_SIGNAL_CATEGORIES } from '@/schemas/domain'
import { SatelliteIndexChart } from './SatelliteIndexChart'
import type { AssetDetail } from '@/types/domain'

const INTERPRETATION_LABELS: Record<string, string> = {
  strongly_positive: 'Strongly positive change',
  weakly_positive: 'Weakly positive change',
  inconclusive: 'Roughly zero / inconclusive change',
  negative: 'Negative change vs. control',
  neutral_no_signal: 'No reliable satellite signal for this category',
}

/**
 * FR5.3 — satellite response. PRD §12.3: this card answers *"did the
 * landscape change"* — kept separate from AiClassifierCard's "is this
 * evidence of the declared work" per §12.2's explicit instruction not to
 * blend the two questions.
 *
 * No per-asset before/after image swipe here (an earlier version had one):
 * confirmed live at Sync Point 1 (2026-09-28) that `sat_result` carries no
 * image URLs at all — geospatial-engineer's precompute produces one
 * watershed-level composite per thematic layer, not a per-asset image pair.
 * What's real per-asset is the treated-vs-control index comparison below,
 * plus `placeholder`/`low_confidence`/`notes`, all rendered as the backend
 * actually sends them rather than backfilled with invented imagery.
 */
export function SatelliteChips({ asset }: { asset: AssetDetail }) {
  const { sat_result: sat, satellite_score: satelliteScore, category } = asset
  const isNoSignalCategory = NO_SATELLITE_SIGNAL_CATEGORIES.includes(
    category as (typeof NO_SATELLITE_SIGNAL_CATEGORIES)[number],
  )

  return (
    <section>
      <div className="mb-1.5 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">Satellite response — did the landscape change?</h3>
        <span className="text-xs font-medium text-slate-500">
          {satelliteScore === null ? 'Pending' : `${satelliteScore}/30`}
        </span>
      </div>

      {sat === null ? (
        <p className="text-sm text-slate-400">Satellite response not yet attached.</p>
      ) : (
        <div className="space-y-2">
          {sat.placeholder && (
            <p className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">
              Placeholder satellite data ({sat.source}) — not yet a real GEE-derived reading. Treat the numbers
              below as demo scaffolding, not evidence.
            </p>
          )}
          {isNoSignalCategory && (
            <p className="rounded bg-slate-50 px-2 py-1 text-xs text-slate-500">
              This activity category has no reliable satellite signal — the score above is a neutral default,
              not a real satellite verdict.
            </p>
          )}
          {sat.low_confidence && (
            <p className="rounded bg-amber-50 px-2 py-1 text-xs text-amber-700">
              Low-confidence read (thin cloud cover / limited valid pixels) — treat this result cautiously.
            </p>
          )}
          {sat.notes.map((note) => (
            <p key={note} className="rounded bg-amber-50 px-2 py-1 text-xs text-amber-700">
              {note}
            </p>
          ))}

          <p className="text-sm text-slate-600">{INTERPRETATION_LABELS[sat.did_classification]}</p>

          <dl className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs text-slate-500">
            <dt>Primary index for this category</dt>
            <dd className="text-right font-mono">{sat.primary_index_for_category}</dd>
            <dt>DiD ({sat.primary_index_for_category})</dt>
            <dd className="text-right font-mono">{sat.did[sat.primary_index_for_category].toFixed(4)}</dd>
            <dt>Baseline window</dt>
            <dd className="text-right font-mono">
              {sat.baseline_window[0]} → {sat.baseline_window[1]}
            </dd>
            <dt>Latest window</dt>
            <dd className="text-right font-mono">
              {sat.latest_window[0]} → {sat.latest_window[1]}
            </dd>
            <dt>Rainfall change</dt>
            <dd className="text-right font-mono">
              {sat.rainfall.pct_change === null ? 'n/a' : `${sat.rainfall.pct_change > 0 ? '+' : ''}${sat.rainfall.pct_change.toFixed(1)}%`}
            </dd>
          </dl>

          <SatelliteIndexChart indices={sat.indices} rainfall={sat.rainfall} defaultIndex={sat.primary_index_for_category} />
        </div>
      )}
    </section>
  )
}
