import { AiClassifierCard } from './AiClassifierCard'
import { GeoIntegrityChecklist } from './GeoIntegrityChecklist'
import { PhotoPanel } from './PhotoPanel'
import { SatelliteChips } from './SatelliteChips'
import { ScoreBreakdown } from './ScoreBreakdown'
import { ScoreReasonText } from './ScoreReasonText'
import { ErrorState } from '@/components/layout/ErrorState'
import { LoadingState } from '@/components/layout/LoadingState'
import { useAssetDetail } from '@/hooks/useAssetDetail'

/**
 * FR5.3 — slide-over asset drawer, opened by clicking a pin
 * (`AssetPinsLayer` → `MapUiContext.selectedAssetId` → this component).
 * Section order: photos → geo-integrity → AI photo check → satellite
 * response → score. The AI-check/satellite split into two separate cards
 * is deliberate (PRD §12.2) — never merge "is this evidence" with "did it
 * work" into one verdict.
 */
export function AssetDrawer({ assetId, onClose }: { assetId: number; onClose: () => void }) {
  const { data: asset, isLoading, isError, error, refetch } = useAssetDetail(assetId)

  return (
    <>
      <div className="fixed inset-0 z-30 bg-black/20" onClick={onClose} aria-hidden="true" />
      <aside className="fixed right-0 top-0 z-40 h-full w-full max-w-md overflow-y-auto border-l border-slate-200 bg-white p-4 shadow-xl">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-800">
            {asset ? `${asset.activity} (${asset.category})` : `Asset #${assetId}`}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            aria-label="Close asset details"
          >
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5" aria-hidden="true">
              <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
            </svg>
          </button>
        </div>

        {isLoading && <LoadingState label="Loading asset details…" />}
        {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}

        {asset && (
          <div className="space-y-5">
            {asset.work_code && <p className="text-xs text-slate-400">Work code: {asset.work_code}</p>}
            <PhotoPanel asset={asset} />
            <GeoIntegrityChecklist flags={asset.geo_flags} geoScore={asset.geo_score} />
            <AiClassifierCard result={asset.ai_result} visualScore={asset.visual_score} />
            <SatelliteChips asset={asset} />
            <ScoreBreakdown asset={asset} />
            <ScoreReasonText asset={asset} />
          </div>
        )}
      </aside>
    </>
  )
}
