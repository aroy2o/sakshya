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
import { KpiNumeral } from '@/components/shared/KpiNumeral'
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
 * `GET /mws/{id}/watershed-impact` (Reality Pass R6, new). Hard rule #1:
 * the `PLACEHOLDER`/`REAL` chip is driven entirely by `summary.placeholder`
 * — never hardcoded — and flips automatically once GEE credentials land
 * and the backend recomputes with real imagery.
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
    <div className="mx-auto max-w-4xl p-4 sm:p-6">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-(--text)">Impact curve</h2>
          <p className="text-xs text-(--text-muted)">
            Treated micro-watershed vs {summary.method_params.n_control_polygons} matched control polygons, dry-season
            median {index}, {years[0]}→{years[years.length - 1]}.
          </p>
        </div>
        <ProvenanceChip kind={provenanceFromPlaceholderFlag(summary.placeholder)} detail={summary.placeholder ? summary.source : undefined} />
      </div>

      <div className="mb-4 flex flex-wrap items-end gap-6 rounded-lg border border-(--border) bg-(--surface) p-4">
        <KpiNumeral
          value={effectLabel(effect)}
          label={`${index} effect (treated − control, post − pre)`}
          sublabel={`${(effect.ci * 100).toFixed(0)}% CI: ${effect.ci_low.toFixed(3)} to ${effect.ci_high.toFixed(3)} (${effect.n_bootstrap.toLocaleString()} bootstrap draws)`}
        />
        <KpiNumeral value={effect.pre_mean_gap.toFixed(3)} label="Pre-project gap" sublabel={effect.pre_years.join(', ')} />
        <KpiNumeral value={effect.post_mean_gap.toFixed(3)} label="Post-project gap" sublabel={effect.post_years.join(', ')} />
        <div className="ml-auto flex gap-1">
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

      <div className="rounded-lg border border-(--border) bg-(--surface) p-4">
        <ResponsiveContainer width="100%" height={320}>
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

      <ul className="mt-3 space-y-1 text-xs text-(--text-faint)">
        {summary.caveats.map((c) => (
          <li key={c} className="flex gap-1.5">
            <span aria-hidden="true">•</span>
            <span>{c}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
