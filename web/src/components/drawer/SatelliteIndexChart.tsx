import { useState } from 'react'
import { Bar, CartesianGrid, ComposedChart, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { SatIndex, SatResult } from '@/types/domain'

const INDEX_LABELS: Record<SatIndex, string> = {
  NDVI: 'NDVI',
  MNDWI: 'MNDWI',
  NDMI: 'NDMI',
  water_fraction: 'Water fraction',
}

/**
 * FR5.3 — treated-vs-control satellite index comparison. Renamed from an
 * earlier "time series" design: geospatial-engineer's precompute produces
 * exactly one baseline/latest pair per zone (confirmed live 2026-09-28,
 * Sync Point 1), not a continuous series, so this renders a 2-window
 * grouped comparison instead of a line chart — a straight line drawn
 * through only 2 real points would visually overclaim a trend the data
 * doesn't have.
 */
export function SatelliteIndexChart({ indices, rainfall, defaultIndex }: { indices: SatResult['indices']; rainfall: SatResult['rainfall']; defaultIndex: SatIndex }) {
  const [index, setIndex] = useState<SatIndex>(defaultIndex)

  const hasRainfall = rainfall.baseline_mm !== null && rainfall.latest_mm !== null

  const data = [
    {
      window: 'Baseline',
      treated: indices.treated_before[index],
      control: indices.control_before[index],
      ...(hasRainfall ? { rainfall_mm: rainfall.baseline_mm } : {}),
    },
    {
      window: 'Latest',
      treated: indices.treated_after[index],
      control: indices.control_after[index],
      ...(hasRainfall ? { rainfall_mm: rainfall.latest_mm } : {}),
    },
  ]

  return (
    <div>
      <div className="mb-1 flex flex-wrap justify-end gap-1">
        {(Object.keys(INDEX_LABELS) as SatIndex[]).map((opt) => (
          <button
            key={opt}
            type="button"
            onClick={() => setIndex(opt)}
            className={`rounded px-2 py-0.5 text-xs font-medium ${
              index === opt ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {INDEX_LABELS[opt]}
          </button>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: -12 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="window" tick={{ fontSize: 11 }} />
          <YAxis yAxisId="index" tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
          {hasRainfall && (
            <YAxis
              yAxisId="rainfall"
              orientation="right"
              tick={{ fontSize: 11 }}
              label={{ value: 'mm', fontSize: 10, position: 'insideTopRight' }}
            />
          )}
          <Tooltip />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {hasRainfall && (
            <Bar yAxisId="rainfall" dataKey="rainfall_mm" name="Rainfall (mm)" fill="#93c5fd" opacity={0.6} barSize={18} />
          )}
          <Bar yAxisId="index" dataKey="treated" name={`${INDEX_LABELS[index]} treated`} fill="#16a34a" barSize={18} />
          <Bar yAxisId="index" dataKey="control" name={`${INDEX_LABELS[index]} control`} fill="#94a3b8" barSize={18} />
        </ComposedChart>
      </ResponsiveContainer>
      {!hasRainfall && <p className="text-center text-xs text-slate-400">Rainfall context not available for this asset.</p>}
    </div>
  )
}
