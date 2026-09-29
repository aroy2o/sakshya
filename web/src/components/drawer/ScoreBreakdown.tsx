import { BandBadge } from '@/components/badges/BandBadge'
import { bandColor } from '@/utils/band'
import type { AssetDetail, Band } from '@/types/domain'

interface SubScoreRow {
  label: string
  value: number | null
  max: number
}

/**
 * FR5.3 final score. PRD §11: "no single opaque AI score" — always renders
 * all four sub-scores next to the total, never just the 0-100 number.
 * Bar color follows the asset's own band (via `bandColor`), not a
 * per-subscore judgement, so this stays a visual breakdown, not a second
 * scoring opinion.
 */
export function ScoreBreakdown({ asset }: { asset: AssetDetail }) {
  const rows: SubScoreRow[] = [
    { label: 'Geo-integrity', value: asset.geo_score, max: 30 },
    { label: 'Visual match', value: asset.visual_score, max: 30 },
    { label: 'Satellite response', value: asset.satellite_score, max: 30 },
    { label: 'Temporal consistency', value: asset.temporal_score, max: 10 },
  ]
  const barColor = bandColor(asset.band as Band | null)

  return (
    <section>
      <div className="mb-1.5 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-(--text)">Evidence score</h3>
        <span className="text-lg font-bold text-(--text)">
          {asset.evidence_score === null ? '—' : asset.evidence_score}
          <span className="text-xs font-normal text-(--text-faint)">/100</span>
        </span>
      </div>
      <BandBadge band={asset.band} className="mb-2" />

      <div className="space-y-1.5">
        {rows.map((row) => (
          <div key={row.label}>
            <div className="flex justify-between text-xs text-(--text-muted)">
              <span>{row.label}</span>
              <span>{row.value === null ? 'pending' : `${row.value}/${row.max}`}</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-(--surface-2)">
              <div
                className="h-1.5 rounded-full"
                style={{
                  width: row.value === null ? '0%' : `${(row.value / row.max) * 100}%`,
                  backgroundColor: barColor,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
