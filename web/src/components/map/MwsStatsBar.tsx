import { computeMwsStats } from '@/utils/mwsStats'
import { BAND_COLORS, UNSCORED_COLOR } from '@/utils/band'
import type { AssetPinFeatureCollection, Mws } from '@/types/domain'

/** Small always-visible summary strip — falls back to a client-computed count when `GET /mws/{id}` doesn't serve `stats` (see utils/mwsStats.ts). */
export function MwsStatsBar({ mws, assets }: { mws: Mws; assets: AssetPinFeatureCollection }) {
  const stats = mws.stats ?? computeMwsStats(assets)

  return (
    <div className="absolute left-1/2 top-3 z-10 flex -translate-x-1/2 items-center gap-3 rounded-full border border-slate-200 bg-white/95 px-4 py-1.5 text-xs shadow-sm backdrop-blur">
      <span className="font-semibold text-slate-700">{mws.name ?? mws.id}</span>
      <span className="text-slate-400">|</span>
      <span className="text-slate-500">{stats.total_assets} assets</span>
      <span className="flex items-center gap-1" style={{ color: BAND_COLORS.verified }}>
        <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: BAND_COLORS.verified }} />
        {stats.verified}
      </span>
      <span className="flex items-center gap-1" style={{ color: BAND_COLORS.review }}>
        <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: BAND_COLORS.review }} />
        {stats.review}
      </span>
      <span className="flex items-center gap-1" style={{ color: BAND_COLORS.flag }}>
        <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: BAND_COLORS.flag }} />
        {stats.flag}
      </span>
      <span className="flex items-center gap-1" style={{ color: UNSCORED_COLOR }}>
        <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: UNSCORED_COLOR }} />
        {stats.unscored} pending
      </span>
    </div>
  )
}
