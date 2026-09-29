import type { DistrictCoverage } from '@/types/domain'

export interface StateTotal {
  state: string
  total_works: number
  geotagged_works: number
  pct: number
}

/**
 * Beat 1's NE comparison bars — aggregated client-side from whatever
 * `GET /districts/geotag-coverage` actually returned, so mock and live mode
 * compute this the same way from the same kind of data (no separately
 * hardcoded per-state constant that could drift from the per-district
 * rows). Sorted by geotag % descending (Assam highest, per
 * REAL_DATA_PLAN.md §6's own framing of "Assam 92% vs Tripura 18%").
 */
export function aggregateByState(rows: readonly DistrictCoverage[]): StateTotal[] {
  const byState = new Map<string, { total: number; geo: number }>()
  for (const row of rows) {
    const entry = byState.get(row.state) ?? { total: 0, geo: 0 }
    entry.total += row.total_works
    entry.geo += row.geotagged_works
    byState.set(row.state, entry)
  }
  return [...byState.entries()]
    .map(([state, { total, geo }]) => ({
      state,
      total_works: total,
      geotagged_works: geo,
      pct: total > 0 ? (geo / total) * 100 : 0,
    }))
    .sort((a, b) => b.pct - a.pct)
}
