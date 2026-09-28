import { useState } from 'react'
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { EmptyState } from '@/components/layout/EmptyState'
import type { SatTimePoint } from '@/types/domain'

type Index = 'NDVI' | 'MNDWI'

/**
 * FR5.3 — treated-vs-control NDVI/MNDWI time series with rainfall bars.
 * Renders only points the API actually returned (`sat_result.time_series`)
 * — an empty array shows EmptyState, never an invented flat line
 * (CLAUDE.md: "never fabricate a number or chart point").
 */
export function NdviTimeSeriesChart({ timeSeries }: { timeSeries: SatTimePoint[] }) {
  const [index, setIndex] = useState<Index>('NDVI')

  if (timeSeries.length === 0) {
    return <EmptyState message="No satellite time-series data available for this asset yet." />
  }

  const treatedKey = index === 'NDVI' ? 'ndvi_treated' : 'mndwi_treated'
  const controlKey = index === 'NDVI' ? 'ndvi_control' : 'mndwi_control'

  return (
    <div>
      <div className="mb-1 flex justify-end gap-1">
        {(['NDVI', 'MNDWI'] as const).map((opt) => (
          <button
            key={opt}
            type="button"
            onClick={() => setIndex(opt)}
            className={`rounded px-2 py-0.5 text-xs font-medium ${
              index === opt ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {opt}
          </button>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <ComposedChart data={timeSeries} margin={{ top: 4, right: 8, bottom: 4, left: -12 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis yAxisId="index" tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
          <YAxis yAxisId="rainfall" orientation="right" tick={{ fontSize: 11 }} label={{ value: 'mm', fontSize: 10, position: 'insideTopRight' }} />
          <Tooltip />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar yAxisId="rainfall" dataKey="rainfall_mm" name="Rainfall (mm)" fill="#93c5fd" opacity={0.6} barSize={14} />
          <Line yAxisId="index" type="monotone" dataKey={treatedKey} name={`${index} treated`} stroke="#16a34a" strokeWidth={2} dot={{ r: 3 }} />
          <Line
            yAxisId="index"
            type="monotone"
            dataKey={controlKey}
            name={`${index} control`}
            stroke="#94a3b8"
            strokeDasharray="4 3"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
