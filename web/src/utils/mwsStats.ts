import type { AssetPinFeatureCollection, MwsStats } from '@/types/domain'

/**
 * `GET /mws/{id}` doesn't serve `stats` yet as of the 2026-09-28 sync
 * (Phase 4 territory, not built even though §9 lists the field under
 * Phase 1). Rather than showing nothing, this computes the same shape
 * client-side from `GET /mws/{id}/assets` — real counts of data actually on
 * screen, not a guess, so it's consistent with CLAUDE.md's "never fabricate
 * a number." Used as a fallback only; `mws.stats` wins when the server does
 * provide it.
 */
export function computeMwsStats(fc: AssetPinFeatureCollection): MwsStats {
  const stats: MwsStats = { total_assets: 0, verified: 0, review: 0, flag: 0, unscored: 0 }
  for (const feature of fc.features) {
    stats.total_assets += 1
    if (feature.properties.band === null) stats.unscored += 1
    else stats[feature.properties.band] += 1
  }
  return stats
}
