import { useState } from 'react'
import { CompareSlider } from '@/components/shared/CompareSlider'
import { NO_SATELLITE_SIGNAL_CATEGORIES } from '@/schemas/domain'
import { NdviTimeSeriesChart } from './NdviTimeSeriesChart'
import type { AssetDetail } from '@/types/domain'

const INTERPRETATION_LABELS: Record<string, string> = {
  strongly_positive: 'Strongly positive change',
  weakly_positive: 'Weakly positive change',
  inconclusive: 'Roughly zero / inconclusive change',
  negative: 'Negative change vs. control',
  neutral_no_signal: 'No reliable satellite signal for this category',
}

/**
 * FR5.3 — satellite before/after chips + NDVI/MNDWI time series. PRD
 * §12.3: this card answers *"did the landscape change"* — kept separate
 * from AiClassifierCard's "is this evidence of the declared work" per
 * §12.2's explicit instruction not to blend the two questions.
 */
export function SatelliteChips({ asset }: { asset: AssetDetail }) {
  const [swipePos, setSwipePos] = useState(50)
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
          {isNoSignalCategory && (
            <p className="rounded bg-slate-50 px-2 py-1 text-xs text-slate-500">
              This activity category has no reliable satellite signal — the score above is a neutral default,
              not a real satellite verdict.
            </p>
          )}
          {sat.interpretation === 'negative' && (
            <p className="rounded bg-amber-50 px-2 py-1 text-xs text-amber-700">
              A negative reading here can also mean the work is too recent to show up in satellite imagery yet —
              it isn&apos;t automatically proof the work failed.
            </p>
          )}

          <p className="text-sm text-slate-600">{INTERPRETATION_LABELS[sat.interpretation]}</p>

          <CompareSlider
            className="aspect-video w-full rounded-md border border-slate-200"
            position={swipePos}
            onPositionChange={setSwipePos}
            beforeLabel="Before"
            afterLabel="After"
            before={<img src={sat.before_image_url} alt="Satellite view before" className="h-full w-full object-cover" />}
            after={<img src={sat.after_image_url} alt="Satellite view after" className="h-full w-full object-cover" />}
          />

          <dl className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs text-slate-500">
            <dt>NDVI DiD</dt>
            <dd className="text-right font-mono">{sat.did.NDVI.toFixed(3)}</dd>
            <dt>MNDWI DiD</dt>
            <dd className="text-right font-mono">{sat.did.MNDWI.toFixed(3)}</dd>
            <dt>Rainfall (baseline → latest)</dt>
            <dd className="text-right font-mono">
              {sat.rainfall_baseline_mm} → {sat.rainfall_latest_mm} mm
            </dd>
          </dl>

          <NdviTimeSeriesChart timeSeries={sat.time_series} />
        </div>
      )}
    </section>
  )
}
