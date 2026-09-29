import { useState } from 'react'
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { ErrorState } from '@/components/layout/ErrorState'
import { SkeletonBlock } from '@/components/shared/Skeleton'
import { ContourMotif } from '@/components/shared/ContourMotif'
import { ProvenanceChip } from '@/components/shared/ProvenanceChip'
import { useWatershedImpact } from '@/hooks/useWatershedImpact'
import { provenanceFromPlaceholderFlag } from '@/utils/provenance'
import type { WatershedImpactSummary } from '@/types/domain'

type Index = 'NDVI' | 'MNDWI'

function effectLabel(effect: WatershedImpactSummary['NDVI']) {
  const sign = effect.effect >= 0 ? '+' : ''
  return `${sign}${effect.effect.toFixed(3)}`
}

/**
 * Beat 4 — treated vs matched-control satellite time series, project-start
 * marker, rainfall bars, effect size + interval, caveats. Data source:
 * `GET /mws/{id}/watershed-impact`. Hard rule #1: the `PLACEHOLDER`/`REAL`
 * chip is driven entirely by `summary.placeholder` — never hardcoded — and
 * flips automatically once GEE credentials land and the backend recomputes
 * with real imagery.
 *
 * Same hero language as CommandStrip (beat 1): the effect size — the
 * headline finding — is a dominant unboxed numeral rather than one of
 * three identical bordered stat cards, the page fills the viewport instead
 * of stacking at the top, and the same contour motif carries the two
 * "summary" beats as one considered system.
 */
export function ImpactCurve({ mwsId }: { mwsId: string }) {
  const { data, isLoading, isError, error, refetch } = useWatershedImpact(mwsId)
  const [index, setIndex] = useState<Index>('NDVI')

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl p-4 sm:p-6">
        <SkeletonBlock lines={6} />
      </div>
    )
  }
  if (isError) {
    return (
      <div className="mx-auto max-w-4xl p-4 sm:p-6">
        <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
      </div>
    )
  }
  if (!data) return null

  const { summary, timeseries } = data
  const effect = index === 'NDVI' ? summary.NDVI : summary.MNDWI

  const years = timeseries.method.years
  const chartData = years.map((year) => {
    const y = String(year)
    return {
      year: y,
      treated: timeseries.treated[index][y] ?? null,
      control: timeseries.control_mean[index][y] ?? null,
      rainfall_mm: timeseries.rainfall_mm_jun_sep[y] ?? null,
    }
  })

  return (
    <div className="relative flex min-h-full flex-col items-center justify-center overflow-hidden px-4 py-10 sm:px-6">
      <ContourMotif className="scale-x-[-1] opacity-90" />

      <div className="relative w-full max-w-4xl">
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-medium text-(--text-muted)">
              Impact curve — treated vs {summary.method_params.n_control_polygons} matched controls
            </h2>
            <div className="mt-2 flex items-baseline gap-3">
              <span className="text-[64px] font-semibold leading-none tracking-tight text-(--text) sm:text-[88px]">
                {effectLabel(effect)}
              </span>
              <span className="text-sm text-(--text-muted)">
                {index} effect, treated − control
                <br />
                post − pre, dry-season median
              </span>
            </div>
            <p className="mt-2 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-(--text-faint)">
              <span>
                {(effect.ci * 100).toFixed(0)}% CI {effect.ci_low.toFixed(3)} to {effect.ci_high.toFixed(3)} (
                {effect.n_bootstrap.toLocaleString()} bootstrap draws)
              </span>
              <span>
                Pre-project gap {effect.pre_mean_gap.toFixed(3)} ({effect.pre_years[0]}–{effect.pre_years[effect.pre_years.length - 1]})
              </span>
              <span>
                Post-project gap {effect.post_mean_gap.toFixed(3)} ({effect.post_years[0]}–{effect.post_years[effect.post_years.length - 1]})
              </span>
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <ProvenanceChip kind={provenanceFromPlaceholderFlag(summary.placeholder)} detail={summary.placeholder ? summary.source : undefined} />
            <div className="flex gap-1">
              {(['NDVI', 'MNDWI'] as const).map((opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => setIndex(opt)}
                  className={`rounded px-2.5 py-1 text-xs font-medium ${
                    index === opt ? 'bg-(--accent) text-(--bg)' : 'bg-(--surface-2) text-(--text-muted) hover:bg-(--surface-3)'
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-(--border) bg-(--surface)/90 p-4 backdrop-blur-sm">
          <ResponsiveContainer width="100%" height={340}>
            <ComposedChart data={chartData} margin={{ top: 8, right: 8, bottom: 4, left: -12 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="year" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
              <YAxis yAxisId="index" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} domain={['auto', 'auto']} />
              <YAxis
                yAxisId="rainfall"
                orientation="right"
                tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
                label={{ value: 'mm (Jun–Sep)', fontSize: 10, position: 'insideTopRight', fill: 'var(--text-faint)' }}
              />
              <Tooltip contentStyle={{ background: 'var(--surface-2)', border: '1px solid var(--border)', color: 'var(--text)' }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <ReferenceLine
                yAxisId="index"
                x={String(summary.method_params.project_start_year)}
                stroke="var(--accent)"
                strokeDasharray="4 3"
                label={{ value: 'Project start', fontSize: 10, fill: 'var(--accent)', position: 'insideTopLeft' }}
              />
              <Bar yAxisId="rainfall" dataKey="rainfall_mm" name="Rainfall (mm, Jun–Sep)" fill="#3b82f6" opacity={0.35} barSize={16} />
              <Line yAxisId="index" type="monotone" dataKey="treated" name={`${index} treated`} stroke="var(--accent)" strokeWidth={2.5} dot={{ r: 3 }} />
              <Line
                yAxisId="index"
                type="monotone"
                dataKey="control"
                name={`${index} control mean`}
                stroke="var(--text-faint)"
                strokeDasharray="4 3"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <ul className="mt-4 space-y-1 text-xs text-(--text-faint)">
          {summary.caveats.map((c) => (
            <li key={c} className="flex gap-1.5">
              <span aria-hidden="true">•</span>
              <span>{c}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
